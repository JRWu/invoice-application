#!/usr/bin/env python3
"""
Invoice API Tests

Tests for invoice CRUD operations and API endpoints.
"""

import sys
import os
import unittest
import json
from datetime import datetime, date

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from config import Config
from models import db, User, Invoice, InvoiceItem
from routes.invoices import invoices_bp


class TestInvoicesAPI(unittest.TestCase):
    """Test cases for invoice API endpoints."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = Flask(__name__)
        self.app.config.from_object(Config)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        
        self.jwt = JWTManager(self.app)
        db.init_app(self.app)
        self.app.register_blueprint(invoices_bp, url_prefix='/api/invoices')
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        db.create_all()
        
        self.test_user = User(username='testuser', email='test@example.com')
        self.test_user.set_password('testpass')
        db.session.add(self.test_user)
        db.session.commit()
        
        self.other_user = User(username='otheruser', email='other@example.com')
        self.other_user.set_password('otherpass')
        db.session.add(self.other_user)
        db.session.commit()
        
        self.auth_token = create_access_token(identity=str(self.test_user.id))
        self.auth_headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        self.other_auth_token = create_access_token(identity=str(self.other_user.id))
        self.other_auth_headers = {'Authorization': f'Bearer {self.other_auth_token}'}
    
    def tearDown(self):
        """Clean up after each test method."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_sample_invoice_data(self):
        """Create sample invoice data for testing."""
        return {
            'customer_name': 'Test Customer',
            'customer_email': 'customer@example.com',
            'customer_address': '123 Test St, Test City, TC 12345',
            'due_date': '2024-12-31',
            'tax_rate': 10.0,
            'notes': 'Test invoice notes',
            'status': 'draft',
            'items': [
                {
                    'description': 'Test Item 1',
                    'quantity': 2.0,
                    'unit_price': 50.0
                },
                {
                    'description': 'Test Item 2',
                    'quantity': 1.0,
                    'unit_price': 100.0
                }
            ]
        }
    
    def create_test_invoice(self, user_id=None):
        """Create a test invoice in the database."""
        if user_id is None:
            user_id = self.test_user.id
        
        import uuid
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        invoice = Invoice(
            invoice_number=invoice_number,
            user_id=user_id,
            customer_name='Test Customer',
            customer_email='customer@example.com',
            due_date=date(2024, 12, 31),
            tax_rate=10.0,
            status='draft'
        )
        db.session.add(invoice)
        db.session.flush()
        
        item1 = InvoiceItem(
            invoice_id=invoice.id,
            description='Test Item 1',
            quantity=2.0,
            unit_price=50.0
        )
        item1.calculate_total()
        db.session.add(item1)
        
        item2 = InvoiceItem(
            invoice_id=invoice.id,
            description='Test Item 2',
            quantity=1.0,
            unit_price=100.0
        )
        item2.calculate_total()
        db.session.add(item2)
        
        invoice.calculate_totals()
        db.session.commit()
        
        return invoice

    def test_get_invoices_success(self):
        """Test successful retrieval of user invoices."""
        invoice1 = self.create_test_invoice()
        invoice2 = self.create_test_invoice()
        
        response = self.client.get('/api/invoices/', headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('invoices', data)
        self.assertEqual(len(data['invoices']), 2)
        
        invoice_ids = [inv['id'] for inv in data['invoices']]
        self.assertIn(invoice1.id, invoice_ids)
        self.assertIn(invoice2.id, invoice_ids)
    
    def test_get_invoices_empty_list(self):
        """Test retrieval when user has no invoices."""
        response = self.client.get('/api/invoices/', headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('invoices', data)
        self.assertEqual(len(data['invoices']), 0)
    
    def test_get_invoices_user_isolation(self):
        """Test that users only see their own invoices."""
        test_invoice = self.create_test_invoice(self.test_user.id)
        
        other_invoice = self.create_test_invoice(self.other_user.id)
        
        response = self.client.get('/api/invoices/', headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['invoices']), 1)
        self.assertEqual(data['invoices'][0]['id'], test_invoice.id)
        
        response = self.client.get('/api/invoices/', headers=self.other_auth_headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['invoices']), 1)
        self.assertEqual(data['invoices'][0]['id'], other_invoice.id)
    
    def test_get_invoices_no_auth(self):
        """Test that unauthenticated requests are rejected."""
        response = self.client.get('/api/invoices/')
        self.assertEqual(response.status_code, 401)

    def test_get_invoice_by_id_success(self):
        """Test successful retrieval of specific invoice."""
        invoice = self.create_test_invoice()
        
        response = self.client.get(f'/api/invoices/{invoice.id}', headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('invoice', data)
        self.assertEqual(data['invoice']['id'], invoice.id)
        self.assertEqual(data['invoice']['customer_name'], 'Test Customer')
        self.assertEqual(len(data['invoice']['items']), 2)
    
    def test_get_invoice_not_found(self):
        """Test retrieval of non-existent invoice."""
        response = self.client.get('/api/invoices/99999', headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invoice not found')
    
    def test_get_invoice_other_user(self):
        """Test that users cannot access other users' invoices."""
        other_invoice = self.create_test_invoice(self.other_user.id)
        
        response = self.client.get(f'/api/invoices/{other_invoice.id}', headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invoice not found')
    
    def test_get_invoice_no_auth(self):
        """Test that unauthenticated requests are rejected."""
        invoice = self.create_test_invoice()
        response = self.client.get(f'/api/invoices/{invoice.id}')
        self.assertEqual(response.status_code, 401)

    def test_create_invoice_success(self):
        """Test successful invoice creation."""
        invoice_data = self.create_sample_invoice_data()
        
        response = self.client.post('/api/invoices/', 
                                  data=json.dumps(invoice_data),
                                  content_type='application/json',
                                  headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('invoice', data)
        self.assertEqual(data['message'], 'Invoice created successfully')
        
        invoice = data['invoice']
        self.assertEqual(invoice['customer_name'], 'Test Customer')
        self.assertEqual(invoice['customer_email'], 'customer@example.com')
        self.assertEqual(len(invoice['items']), 2)
        self.assertEqual(invoice['subtotal'], 200.0)  # (2*50) + (1*100)
        self.assertEqual(invoice['tax_amount'], 20.0)  # 10% of 200
        self.assertEqual(invoice['total_amount'], 220.0)  # 200 + 20
        
        self.assertTrue(invoice['invoice_number'].startswith('INV-'))
    
    def test_create_invoice_missing_customer_name(self):
        """Test invoice creation with missing customer_name."""
        invoice_data = self.create_sample_invoice_data()
        del invoice_data['customer_name']
        
        response = self.client.post('/api/invoices/', 
                                  data=json.dumps(invoice_data),
                                  content_type='application/json',
                                  headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'customer_name is required')
    
    def test_create_invoice_missing_due_date(self):
        """Test invoice creation with missing due_date."""
        invoice_data = self.create_sample_invoice_data()
        del invoice_data['due_date']
        
        response = self.client.post('/api/invoices/', 
                                  data=json.dumps(invoice_data),
                                  content_type='application/json',
                                  headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'due_date is required')
    
    def test_create_invoice_missing_items(self):
        """Test invoice creation with missing items."""
        invoice_data = self.create_sample_invoice_data()
        del invoice_data['items']
        
        response = self.client.post('/api/invoices/', 
                                  data=json.dumps(invoice_data),
                                  content_type='application/json',
                                  headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'items is required')
    
    def test_create_invoice_invalid_date_format(self):
        """Test invoice creation with invalid date format."""
        invoice_data = self.create_sample_invoice_data()
        invoice_data['due_date'] = 'invalid-date'
        
        response = self.client.post('/api/invoices/', 
                                  data=json.dumps(invoice_data),
                                  content_type='application/json',
                                  headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_create_invoice_missing_item_fields(self):
        """Test invoice creation with missing item fields."""
        invoice_data = self.create_sample_invoice_data()
        invoice_data['items'][0] = {'description': 'Test Item'}  # Missing quantity and unit_price
        
        response = self.client.post('/api/invoices/', 
                                  data=json.dumps(invoice_data),
                                  content_type='application/json',
                                  headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Each item must have description, quantity, and unit_price')
    
    def test_create_invoice_no_auth(self):
        """Test that unauthenticated requests are rejected."""
        invoice_data = self.create_sample_invoice_data()
        
        response = self.client.post('/api/invoices/', 
                                  data=json.dumps(invoice_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 401)

    def test_update_invoice_success(self):
        """Test successful invoice update."""
        invoice = self.create_test_invoice()
        
        update_data = {
            'customer_name': 'Updated Customer',
            'customer_email': 'updated@example.com',
            'status': 'sent',
            'notes': 'Updated notes'
        }
        
        response = self.client.put(f'/api/invoices/{invoice.id}',
                                 data=json.dumps(update_data),
                                 content_type='application/json',
                                 headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Invoice updated successfully')
        
        updated_invoice = data['invoice']
        self.assertEqual(updated_invoice['customer_name'], 'Updated Customer')
        self.assertEqual(updated_invoice['customer_email'], 'updated@example.com')
        self.assertEqual(updated_invoice['status'], 'sent')
        self.assertEqual(updated_invoice['notes'], 'Updated notes')
    
    def test_update_invoice_with_items(self):
        """Test invoice update with new items."""
        invoice = self.create_test_invoice()
        
        update_data = {
            'items': [
                {
                    'description': 'New Item 1',
                    'quantity': 3.0,
                    'unit_price': 75.0
                }
            ]
        }
        
        response = self.client.put(f'/api/invoices/{invoice.id}',
                                 data=json.dumps(update_data),
                                 content_type='application/json',
                                 headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        updated_invoice = data['invoice']
        self.assertEqual(len(updated_invoice['items']), 1)
        self.assertEqual(updated_invoice['items'][0]['description'], 'New Item 1')
        self.assertEqual(updated_invoice['subtotal'], 225.0)  # 3 * 75
    
    def test_update_invoice_not_found(self):
        """Test update of non-existent invoice."""
        update_data = {'customer_name': 'Updated Customer'}
        
        response = self.client.put('/api/invoices/99999',
                                 data=json.dumps(update_data),
                                 content_type='application/json',
                                 headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invoice not found')
    
    def test_update_invoice_other_user(self):
        """Test that users cannot update other users' invoices."""
        other_invoice = self.create_test_invoice(self.other_user.id)
        update_data = {'customer_name': 'Updated Customer'}
        
        response = self.client.put(f'/api/invoices/{other_invoice.id}',
                                 data=json.dumps(update_data),
                                 content_type='application/json',
                                 headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invoice not found')
    
    def test_update_invoice_no_auth(self):
        """Test that unauthenticated requests are rejected."""
        invoice = self.create_test_invoice()
        update_data = {'customer_name': 'Updated Customer'}
        
        response = self.client.put(f'/api/invoices/{invoice.id}',
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 401)

    def test_delete_invoice_success(self):
        """Test successful invoice deletion."""
        invoice = self.create_test_invoice()
        
        response = self.client.delete(f'/api/invoices/{invoice.id}', headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Invoice deleted successfully')
        
        deleted_invoice = db.session.get(Invoice, invoice.id)
        self.assertIsNone(deleted_invoice)
    
    def test_delete_invoice_not_found(self):
        """Test deletion of non-existent invoice."""
        response = self.client.delete('/api/invoices/99999', headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invoice not found')
    
    def test_delete_invoice_other_user(self):
        """Test that users cannot delete other users' invoices."""
        other_invoice = self.create_test_invoice(self.other_user.id)
        
        response = self.client.delete(f'/api/invoices/{other_invoice.id}', headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invoice not found')
        
        existing_invoice = db.session.get(Invoice, other_invoice.id)
        self.assertIsNotNone(existing_invoice)
    
    def test_delete_invoice_no_auth(self):
        """Test that unauthenticated requests are rejected."""
        invoice = self.create_test_invoice()
        response = self.client.delete(f'/api/invoices/{invoice.id}')
        self.assertEqual(response.status_code, 401)


def run_invoice_api_tests():
    """Run all invoice API tests and return results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestInvoicesAPI)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run the tests
    success = run_invoice_api_tests()
    if success:
        print("\n✅ All invoice API tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some invoice API tests failed!")
        sys.exit(1)
