#!/usr/bin/env python3
"""
Invoice Management Tests

Tests for invoice CRUD operations, authentication, business logic, and validation.
"""

import sys
import os
import unittest
from datetime import datetime, date

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from config import Config
from models import db, User, Invoice, InvoiceItem


class TestInvoiceEndpoints(unittest.TestCase):
    """Test cases for invoice management endpoints."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = Flask(__name__)
        self.app.config.from_object(Config)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        
        db.init_app(self.app)
        self.jwt = JWTManager(self.app)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Create tables
        db.create_all()
        
        from routes.invoices import invoices_bp
        self.app.register_blueprint(invoices_bp, url_prefix='/api/invoices')
    
    def tearDown(self):
        """Clean up after each test method."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_test_user(self, username="testuser", email="test@example.com", password="testpass"):
        """Create a test user and return the user object."""
        user = User(username=username, email=email, company_name="Test Company")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    
    def get_auth_headers(self, user_id):
        """Get authorization headers with JWT token for a user."""
        token = create_access_token(identity=str(user_id))
        return {'Authorization': f'Bearer {token}'}
    
    def create_test_invoice(self, user_id, customer_name="Test Customer", status="draft"):
        """Create a test invoice and return the invoice object."""
        invoice = Invoice(
            invoice_number=f"INV-{datetime.now().strftime('%Y%m%d')}-TEST123",
            user_id=user_id,
            customer_name=customer_name,
            customer_email="customer@example.com",
            due_date=date(2024, 12, 31),
            status=status,
            tax_rate=10.0
        )
        db.session.add(invoice)
        db.session.flush()
        
        item1 = InvoiceItem(
            invoice_id=invoice.id,
            description="Test Item 1",
            quantity=2.0,
            unit_price=50.0
        )
        item1.calculate_total()
        
        item2 = InvoiceItem(
            invoice_id=invoice.id,
            description="Test Item 2",
            quantity=1.0,
            unit_price=100.0
        )
        item2.calculate_total()
        
        db.session.add(item1)
        db.session.add(item2)
        
        # Calculate invoice totals
        invoice.calculate_totals()
        db.session.commit()
        
        return invoice

    def test_get_invoices_success_with_data(self):
        """Test successful retrieval of invoices for authenticated user with data."""
        user = self.create_test_user()
        invoice = self.create_test_invoice(user.id)
        headers = self.get_auth_headers(user.id)
        
        response = self.client.get('/api/invoices/', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('invoices', data)
        self.assertEqual(len(data['invoices']), 1)
        self.assertEqual(data['invoices'][0]['customer_name'], 'Test Customer')
        self.assertEqual(data['invoices'][0]['total_amount'], 220.0)  # (100 + 200) * 1.1 tax
    
    def test_get_invoices_empty_list(self):
        """Test successful retrieval of empty invoice list for new user."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        response = self.client.get('/api/invoices/', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('invoices', data)
        self.assertEqual(len(data['invoices']), 0)
    
    def test_get_invoices_unauthorized(self):
        """Test unauthorized access without JWT token."""
        response = self.client.get('/api/invoices/')
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertTrue('error' in data or 'msg' in data)
    
    def test_get_invoices_user_isolation(self):
        """Test that users only see their own invoices."""
        user1 = self.create_test_user(username="user1", email="user1@example.com")
        user2 = self.create_test_user(username="user2", email="user2@example.com")
        
        self.create_test_invoice(user1.id, customer_name="User1 Customer")
        
        headers = self.get_auth_headers(user2.id)
        response = self.client.get('/api/invoices/', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['invoices']), 0)

    def test_create_invoice_success_required_fields(self):
        """Test successful invoice creation with required fields only."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        invoice_data = {
            'customer_name': 'New Customer',
            'due_date': '2024-12-31',
            'items': [
                {
                    'description': 'Service 1',
                    'quantity': 1,
                    'unit_price': 100.0
                }
            ]
        }
        
        response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('invoice', data)
        self.assertEqual(data['invoice']['customer_name'], 'New Customer')
        self.assertEqual(data['invoice']['status'], 'draft')
        self.assertTrue(data['invoice']['invoice_number'].startswith('INV-'))
    
    def test_create_invoice_success_all_fields(self):
        """Test successful invoice creation with all optional fields."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        invoice_data = {
            'customer_name': 'Complete Customer',
            'customer_email': 'complete@example.com',
            'customer_address': '123 Main St',
            'due_date': '2024-12-31',
            'tax_rate': 8.5,
            'notes': 'Test notes',
            'status': 'sent',
            'items': [
                {
                    'description': 'Premium Service',
                    'quantity': 2,
                    'unit_price': 150.0
                }
            ]
        }
        
        response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        invoice = data['invoice']
        self.assertEqual(invoice['customer_email'], 'complete@example.com')
        self.assertEqual(invoice['customer_address'], '123 Main St')
        self.assertEqual(invoice['tax_rate'], 8.5)
        self.assertEqual(invoice['notes'], 'Test notes')
        self.assertEqual(invoice['status'], 'sent')
        self.assertEqual(invoice['total_amount'], 325.5)  # 300 * 1.085
    
    def test_create_invoice_missing_customer_name(self):
        """Test validation error for missing customer_name."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        invoice_data = {
            'due_date': '2024-12-31',
            'items': [{'description': 'Service', 'quantity': 1, 'unit_price': 100}]
        }
        
        response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('customer_name is required', data['error'])
    
    def test_create_invoice_missing_due_date(self):
        """Test validation error for missing due_date."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        invoice_data = {
            'customer_name': 'Customer',
            'items': [{'description': 'Service', 'quantity': 1, 'unit_price': 100}]
        }
        
        response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('due_date is required', data['error'])
    
    def test_create_invoice_missing_items(self):
        """Test validation error for missing items."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        invoice_data = {
            'customer_name': 'Customer',
            'due_date': '2024-12-31'
        }
        
        response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('items is required', data['error'])
    
    def test_create_invoice_invalid_date_format(self):
        """Test error for invalid date format."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        invoice_data = {
            'customer_name': 'Customer',
            'due_date': 'invalid-date',
            'items': [{'description': 'Service', 'quantity': 1, 'unit_price': 100}]
        }
        
        response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        
        self.assertEqual(response.status_code, 500)
    
    def test_create_invoice_invalid_items_structure(self):
        """Test validation error for invalid item structure."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        invoice_data = {
            'customer_name': 'Customer',
            'due_date': '2024-12-31',
            'items': [{'description': 'Service'}]  # Missing quantity and unit_price
        }
        
        response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Each item must have description, quantity, and unit_price', data['error'])
    
    def test_create_invoice_unauthorized(self):
        """Test unauthorized invoice creation without JWT token."""
        invoice_data = {
            'customer_name': 'Customer',
            'due_date': '2024-12-31',
            'items': [{'description': 'Service', 'quantity': 1, 'unit_price': 100}]
        }
        
        response = self.client.post('/api/invoices/', json=invoice_data)
        
        self.assertEqual(response.status_code, 401)
    
    def test_invoice_number_generation_uniqueness(self):
        """Test that invoice numbers are unique and follow UUID pattern."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        invoice_data = {
            'customer_name': 'Customer',
            'due_date': '2024-12-31',
            'items': [{'description': 'Service', 'quantity': 1, 'unit_price': 100}]
        }
        
        response1 = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        response2 = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response2.status_code, 201)
        
        invoice1 = response1.get_json()['invoice']
        invoice2 = response2.get_json()['invoice']
        
        self.assertTrue(invoice1['invoice_number'].startswith('INV-'))
        self.assertTrue(invoice2['invoice_number'].startswith('INV-'))
        self.assertNotEqual(invoice1['invoice_number'], invoice2['invoice_number'])

    def test_get_invoice_success(self):
        """Test successful retrieval of specific invoice."""
        user = self.create_test_user()
        invoice = self.create_test_invoice(user.id)
        headers = self.get_auth_headers(user.id)
        
        response = self.client.get(f'/api/invoices/{invoice.id}', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('invoice', data)
        self.assertEqual(data['invoice']['id'], invoice.id)
        self.assertEqual(data['invoice']['customer_name'], 'Test Customer')
    
    def test_get_invoice_not_found(self):
        """Test retrieval of non-existent invoice."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        response = self.client.get('/api/invoices/99999', headers=headers)
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('Invoice not found', data['error'])
    
    def test_get_invoice_user_isolation(self):
        """Test that users cannot access other users' invoices."""
        user1 = self.create_test_user(username="user1", email="user1@example.com")
        user2 = self.create_test_user(username="user2", email="user2@example.com")
        
        invoice = self.create_test_invoice(user1.id)
        headers = self.get_auth_headers(user2.id)
        
        response = self.client.get(f'/api/invoices/{invoice.id}', headers=headers)
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('Invoice not found', data['error'])
    
    def test_get_invoice_unauthorized(self):
        """Test unauthorized access to specific invoice."""
        user = self.create_test_user()
        invoice = self.create_test_invoice(user.id)
        
        response = self.client.get(f'/api/invoices/{invoice.id}')
        
        self.assertEqual(response.status_code, 401)

    def test_update_invoice_success_partial(self):
        """Test successful partial update of invoice."""
        user = self.create_test_user()
        invoice = self.create_test_invoice(user.id)
        headers = self.get_auth_headers(user.id)
        
        update_data = {
            'customer_name': 'Updated Customer',
            'status': 'sent'
        }
        
        response = self.client.put(f'/api/invoices/{invoice.id}', json=update_data, headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['invoice']['customer_name'], 'Updated Customer')
        self.assertEqual(data['invoice']['status'], 'sent')
    
    def test_update_invoice_success_all_fields(self):
        """Test successful update of all invoice fields."""
        user = self.create_test_user()
        invoice = self.create_test_invoice(user.id)
        headers = self.get_auth_headers(user.id)
        
        update_data = {
            'customer_name': 'Fully Updated Customer',
            'customer_email': 'updated@example.com',
            'customer_address': '456 Updated St',
            'due_date': '2025-01-31',
            'tax_rate': 15.0,
            'notes': 'Updated notes',
            'status': 'paid'
        }
        
        response = self.client.put(f'/api/invoices/{invoice.id}', json=update_data, headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        invoice_data = data['invoice']
        self.assertEqual(invoice_data['customer_name'], 'Fully Updated Customer')
        self.assertEqual(invoice_data['customer_email'], 'updated@example.com')
        self.assertEqual(invoice_data['tax_rate'], 15.0)
        self.assertEqual(invoice_data['status'], 'paid')
    
    def test_update_invoice_with_new_items(self):
        """Test updating invoice with new items array."""
        user = self.create_test_user()
        invoice = self.create_test_invoice(user.id)
        headers = self.get_auth_headers(user.id)
        
        update_data = {
            'items': [
                {
                    'description': 'New Item 1',
                    'quantity': 3,
                    'unit_price': 75.0
                },
                {
                    'description': 'New Item 2',
                    'quantity': 1,
                    'unit_price': 200.0
                }
            ]
        }
        
        response = self.client.put(f'/api/invoices/{invoice.id}', json=update_data, headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        items = data['invoice']['items']
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['description'], 'New Item 1')
        self.assertEqual(items[1]['description'], 'New Item 2')
    
    def test_update_invoice_totals_recalculation(self):
        """Test that totals are recalculated after update."""
        user = self.create_test_user()
        invoice = self.create_test_invoice(user.id)
        headers = self.get_auth_headers(user.id)
        
        update_data = {
            'tax_rate': 20.0,
            'items': [
                {
                    'description': 'Updated Item',
                    'quantity': 1,
                    'unit_price': 500.0
                }
            ]
        }
        
        response = self.client.put(f'/api/invoices/{invoice.id}', json=update_data, headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        invoice_data = data['invoice']
        self.assertEqual(invoice_data['subtotal'], 500.0)
        self.assertEqual(invoice_data['tax_amount'], 100.0)  # 500 * 0.20
        self.assertEqual(invoice_data['total_amount'], 600.0)
    
    def test_update_invoice_not_found(self):
        """Test update of non-existent invoice."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        update_data = {'customer_name': 'Updated'}
        
        response = self.client.put('/api/invoices/99999', json=update_data, headers=headers)
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('Invoice not found', data['error'])
    
    def test_update_invoice_user_isolation(self):
        """Test that users cannot update other users' invoices."""
        user1 = self.create_test_user(username="user1", email="user1@example.com")
        user2 = self.create_test_user(username="user2", email="user2@example.com")
        
        invoice = self.create_test_invoice(user1.id)
        headers = self.get_auth_headers(user2.id)
        
        update_data = {'customer_name': 'Hacked'}
        
        response = self.client.put(f'/api/invoices/{invoice.id}', json=update_data, headers=headers)
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('Invoice not found', data['error'])
    
    def test_update_invoice_unauthorized(self):
        """Test unauthorized invoice update."""
        user = self.create_test_user()
        invoice = self.create_test_invoice(user.id)
        
        update_data = {'customer_name': 'Updated'}
        
        response = self.client.put(f'/api/invoices/{invoice.id}', json=update_data)
        
        self.assertEqual(response.status_code, 401)

    def test_delete_invoice_success(self):
        """Test successful invoice deletion."""
        user = self.create_test_user()
        invoice = self.create_test_invoice(user.id)
        headers = self.get_auth_headers(user.id)
        
        response = self.client.delete(f'/api/invoices/{invoice.id}', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('Invoice deleted successfully', data['message'])
        
        get_response = self.client.get(f'/api/invoices/{invoice.id}', headers=headers)
        self.assertEqual(get_response.status_code, 404)
    
    def test_delete_invoice_not_found(self):
        """Test deletion of non-existent invoice."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        response = self.client.delete('/api/invoices/99999', headers=headers)
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('Invoice not found', data['error'])
    
    def test_delete_invoice_user_isolation(self):
        """Test that users cannot delete other users' invoices."""
        user1 = self.create_test_user(username="user1", email="user1@example.com")
        user2 = self.create_test_user(username="user2", email="user2@example.com")
        
        invoice = self.create_test_invoice(user1.id)
        headers = self.get_auth_headers(user2.id)
        
        response = self.client.delete(f'/api/invoices/{invoice.id}', headers=headers)
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('Invoice not found', data['error'])
    
    def test_delete_invoice_unauthorized(self):
        """Test unauthorized invoice deletion."""
        user = self.create_test_user()
        invoice = self.create_test_invoice(user.id)
        
        response = self.client.delete(f'/api/invoices/{invoice.id}')
        
        self.assertEqual(response.status_code, 401)
    
    def test_delete_invoice_cascade_items(self):
        """Test that invoice items are deleted when invoice is deleted."""
        user = self.create_test_user()
        invoice = self.create_test_invoice(user.id)
        headers = self.get_auth_headers(user.id)
        
        items_before = InvoiceItem.query.filter_by(invoice_id=invoice.id).all()
        self.assertEqual(len(items_before), 2)
        
        response = self.client.delete(f'/api/invoices/{invoice.id}', headers=headers)
        self.assertEqual(response.status_code, 200)
        
        items_after = InvoiceItem.query.filter_by(invoice_id=invoice.id).all()
        self.assertEqual(len(items_after), 0)

    def test_invoice_item_calculate_total(self):
        """Test InvoiceItem calculate_total method."""
        item = InvoiceItem(
            description="Test Item",
            quantity=3.5,
            unit_price=25.0
        )
        item.calculate_total()
        
        self.assertEqual(item.total, 87.5)  # 3.5 * 25.0
    
    def test_invoice_calculate_totals(self):
        """Test Invoice calculate_totals method."""
        user = self.create_test_user()
        
        invoice = Invoice(
            invoice_number="TEST-001",
            user_id=user.id,
            customer_name="Test Customer",
            due_date=date(2024, 12, 31),
            tax_rate=12.5
        )
        db.session.add(invoice)
        db.session.flush()
        
        item1 = InvoiceItem(invoice_id=invoice.id, description="Item 1", quantity=2, unit_price=100)
        item1.calculate_total()
        item2 = InvoiceItem(invoice_id=invoice.id, description="Item 2", quantity=1, unit_price=50)
        item2.calculate_total()
        
        db.session.add(item1)
        db.session.add(item2)
        
        invoice.calculate_totals()
        
        self.assertEqual(invoice.subtotal, 250.0)  # 200 + 50
        self.assertEqual(invoice.tax_amount, 31.25)  # 250 * 0.125
        self.assertEqual(invoice.total_amount, 281.25)  # 250 + 31.25
    
    def test_financial_calculations_accuracy(self):
        """Test accuracy of financial calculations with decimal precision."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        invoice_data = {
            'customer_name': 'Precision Customer',
            'due_date': '2024-12-31',
            'tax_rate': 8.75,
            'items': [
                {
                    'description': 'Precise Item',
                    'quantity': 3.33,
                    'unit_price': 33.33
                }
            ]
        }
        
        response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        invoice = data['invoice']
        
        expected_subtotal = 3.33 * 33.33  # 110.9889
        expected_tax = expected_subtotal * 0.0875
        expected_total = expected_subtotal + expected_tax
        
        self.assertAlmostEqual(invoice['subtotal'], expected_subtotal, places=2)
        self.assertAlmostEqual(invoice['tax_amount'], expected_tax, places=2)
        self.assertAlmostEqual(invoice['total_amount'], expected_total, places=2)

    def test_invoice_status_validation(self):
        """Test that valid status values are accepted."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        valid_statuses = ['draft', 'sent', 'paid', 'overdue']
        
        for status in valid_statuses:
            invoice_data = {
                'customer_name': f'Customer {status}',
                'due_date': '2024-12-31',
                'status': status,
                'items': [{'description': 'Service', 'quantity': 1, 'unit_price': 100}]
            }
            
            response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
            
            self.assertEqual(response.status_code, 201)
            data = response.get_json()
            self.assertEqual(data['invoice']['status'], status)
    
    def test_item_required_fields(self):
        """Test validation of required fields for invoice items."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        invoice_data = {
            'customer_name': 'Customer',
            'due_date': '2024-12-31',
            'items': [{'quantity': 1, 'unit_price': 100}]
        }
        
        response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        self.assertEqual(response.status_code, 400)
        
        invoice_data['items'] = [{'description': 'Service', 'unit_price': 100}]
        response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        self.assertEqual(response.status_code, 400)
        
        invoice_data['items'] = [{'description': 'Service', 'quantity': 1}]
        response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        self.assertEqual(response.status_code, 400)
    
    def test_date_format_validation(self):
        """Test validation of due_date format requirements."""
        user = self.create_test_user()
        headers = self.get_auth_headers(user.id)
        
        invoice_data = {
            'customer_name': 'Customer',
            'due_date': '2024-12-31',
            'items': [{'description': 'Service', 'quantity': 1, 'unit_price': 100}]
        }
        
        response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
        self.assertEqual(response.status_code, 201)
        
        invalid_dates = ['12/31/2024', '2024-13-01', '2024-02-30', 'not-a-date']
        
        for invalid_date in invalid_dates:
            invoice_data['due_date'] = invalid_date
            response = self.client.post('/api/invoices/', json=invoice_data, headers=headers)
            self.assertNotEqual(response.status_code, 201)


def run_invoice_tests():
    """Run all invoice tests and return results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestInvoiceEndpoints)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run the tests
    success = run_invoice_tests()
    if success:
        print("\n✅ All invoice tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some invoice tests failed!")
        sys.exit(1)
