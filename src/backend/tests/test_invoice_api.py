#!/usr/bin/env python3
"""
Invoice API Tests

Tests for Invoice API endpoints including CRUD operations and authentication.
"""

import sys
import os
import unittest
from datetime import datetime, date

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from app import create_app
from models import db, Invoice, InvoiceItem, User


class TestInvoiceAPI(unittest.TestCase):
    """Test cases for Invoice API endpoints."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        with self.app.app_context():
            db.create_all()
            self.test_user = User(username='testuser', email='test@example.com')
            self.test_user.set_password('testpass')
            db.session.add(self.test_user)
            db.session.commit()
            self.user_id = self.test_user.id
    
    def tearDown(self):
        """Clean up after each test method."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_auth_headers(self):
        """Create authorization headers with valid JWT token."""
        with self.app.app_context():
            token = create_access_token(identity=str(self.user_id))
            return {'Authorization': f'Bearer {token}'}
    
    def get_sample_invoice_data(self):
        """Get sample invoice data for testing."""
        return {
            'customer_name': 'Test Customer',
            'customer_email': 'customer@test.com',
            'customer_address': '123 Test St, Test City, TC 12345',
            'due_date': '2024-12-31',
            'tax_rate': 8.5,
            'notes': 'Test invoice notes',
            'status': 'draft',
            'items': [
                {
                    'description': 'Test Service 1',
                    'quantity': 2.0,
                    'unit_price': 50.0
                },
                {
                    'description': 'Test Service 2',
                    'quantity': 1.0,
                    'unit_price': 100.0
                }
            ]
        }
    
    def test_get_invoices_success(self):
        """Test successful retrieval of all invoices."""
        headers = self.create_auth_headers()
        response = self.client.get('/api/invoices/', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('invoices', data)
        self.assertIsInstance(data['invoices'], list)
    
    def test_get_invoices_unauthorized(self):
        """Test unauthorized access to invoices."""
        response = self.client.get('/api/invoices/')
        self.assertEqual(response.status_code, 401)
    
    def test_get_invoices_invalid_token(self):
        """Test invalid token access to invoices."""
        headers = {'Authorization': 'Bearer invalid_token'}
        response = self.client.get('/api/invoices/', headers=headers)
        self.assertEqual(response.status_code, 401)
    
    def test_create_invoice_success(self):
        """Test successful invoice creation."""
        headers = self.create_auth_headers()
        data = self.get_sample_invoice_data()
        
        response = self.client.post('/api/invoices/', 
                                  json=data, 
                                  headers=headers)
        
        self.assertEqual(response.status_code, 201)
        response_data = response.get_json()
        self.assertIn('message', response_data)
        self.assertIn('invoice', response_data)
        self.assertEqual(response_data['invoice']['customer_name'], 'Test Customer')
        self.assertEqual(len(response_data['invoice']['items']), 2)
    
    def test_create_invoice_missing_customer_name(self):
        """Test invoice creation with missing customer_name."""
        headers = self.create_auth_headers()
        data = self.get_sample_invoice_data()
        del data['customer_name']
        
        response = self.client.post('/api/invoices/', json=data, headers=headers)
        self.assertEqual(response.status_code, 400)
        response_data = response.get_json()
        self.assertIn('error', response_data)
    
    def test_create_invoice_missing_due_date(self):
        """Test invoice creation with missing due_date."""
        headers = self.create_auth_headers()
        data = self.get_sample_invoice_data()
        del data['due_date']
        
        response = self.client.post('/api/invoices/', json=data, headers=headers)
        self.assertEqual(response.status_code, 400)
        response_data = response.get_json()
        self.assertIn('error', response_data)
    
    def test_create_invoice_missing_items(self):
        """Test invoice creation with missing items."""
        headers = self.create_auth_headers()
        data = self.get_sample_invoice_data()
        del data['items']
        
        response = self.client.post('/api/invoices/', json=data, headers=headers)
        self.assertEqual(response.status_code, 400)
        response_data = response.get_json()
        self.assertIn('error', response_data)
    
    def test_create_invoice_invalid_item_data(self):
        """Test invoice creation with invalid item data."""
        headers = self.create_auth_headers()
        data = self.get_sample_invoice_data()
        data['items'] = [{'description': 'Test', 'quantity': 1.0}]  # Missing unit_price
        
        response = self.client.post('/api/invoices/', json=data, headers=headers)
        self.assertEqual(response.status_code, 400)
        response_data = response.get_json()
        self.assertIn('error', response_data)
    
    def test_create_invoice_unauthorized(self):
        """Test unauthorized invoice creation."""
        data = self.get_sample_invoice_data()
        response = self.client.post('/api/invoices/', json=data)
        self.assertEqual(response.status_code, 401)
    
    def test_get_invoice_success(self):
        """Test successful retrieval of specific invoice."""
        headers = self.create_auth_headers()
        data = self.get_sample_invoice_data()
        create_response = self.client.post('/api/invoices/', json=data, headers=headers)
        invoice_id = create_response.get_json()['invoice']['id']
        
        response = self.client.get(f'/api/invoices/{invoice_id}', headers=headers)
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn('invoice', response_data)
        self.assertEqual(response_data['invoice']['id'], invoice_id)
        self.assertEqual(response_data['invoice']['customer_name'], 'Test Customer')
    
    def test_get_invoice_not_found(self):
        """Test retrieval of non-existent invoice."""
        headers = self.create_auth_headers()
        response = self.client.get('/api/invoices/99999', headers=headers)
        self.assertEqual(response.status_code, 404)
        response_data = response.get_json()
        self.assertIn('error', response_data)
    
    def test_get_invoice_unauthorized(self):
        """Test unauthorized access to specific invoice."""
        response = self.client.get('/api/invoices/1')
        self.assertEqual(response.status_code, 401)
    
    def test_update_invoice_success(self):
        """Test successful invoice update."""
        headers = self.create_auth_headers()
        data = self.get_sample_invoice_data()
        create_response = self.client.post('/api/invoices/', json=data, headers=headers)
        invoice_id = create_response.get_json()['invoice']['id']
        
        update_data = {
            'customer_name': 'Updated Customer',
            'status': 'sent',
            'notes': 'Updated notes'
        }
        response = self.client.put(f'/api/invoices/{invoice_id}', 
                                 json=update_data, 
                                 headers=headers)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn('message', response_data)
        self.assertEqual(response_data['invoice']['customer_name'], 'Updated Customer')
        self.assertEqual(response_data['invoice']['status'], 'sent')
        self.assertEqual(response_data['invoice']['notes'], 'Updated notes')
    
    def test_update_invoice_with_items(self):
        """Test invoice update with new items."""
        headers = self.create_auth_headers()
        data = self.get_sample_invoice_data()
        create_response = self.client.post('/api/invoices/', json=data, headers=headers)
        invoice_id = create_response.get_json()['invoice']['id']
        
        update_data = {
            'customer_name': 'Updated Customer',
            'items': [
                {
                    'description': 'New Service',
                    'quantity': 3.0,
                    'unit_price': 75.0
                }
            ]
        }
        response = self.client.put(f'/api/invoices/{invoice_id}', 
                                 json=update_data, 
                                 headers=headers)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(len(response_data['invoice']['items']), 1)
        self.assertEqual(response_data['invoice']['items'][0]['description'], 'New Service')
    
    def test_update_invoice_not_found(self):
        """Test update of non-existent invoice."""
        headers = self.create_auth_headers()
        update_data = {'customer_name': 'Updated Customer'}
        response = self.client.put('/api/invoices/99999', json=update_data, headers=headers)
        self.assertEqual(response.status_code, 404)
        response_data = response.get_json()
        self.assertIn('error', response_data)
    
    def test_update_invoice_unauthorized(self):
        """Test unauthorized invoice update."""
        update_data = {'customer_name': 'Updated Customer'}
        response = self.client.put('/api/invoices/1', json=update_data)
        self.assertEqual(response.status_code, 401)
    
    def test_delete_invoice_success(self):
        """Test successful invoice deletion."""
        headers = self.create_auth_headers()
        data = self.get_sample_invoice_data()
        create_response = self.client.post('/api/invoices/', json=data, headers=headers)
        invoice_id = create_response.get_json()['invoice']['id']
        
        response = self.client.delete(f'/api/invoices/{invoice_id}', headers=headers)
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn('message', response_data)
        
        get_response = self.client.get(f'/api/invoices/{invoice_id}', headers=headers)
        self.assertEqual(get_response.status_code, 404)
    
    def test_delete_invoice_not_found(self):
        """Test deletion of non-existent invoice."""
        headers = self.create_auth_headers()
        response = self.client.delete('/api/invoices/99999', headers=headers)
        self.assertEqual(response.status_code, 404)
        response_data = response.get_json()
        self.assertIn('error', response_data)
    
    def test_delete_invoice_unauthorized(self):
        """Test unauthorized invoice deletion."""
        response = self.client.delete('/api/invoices/1')
        self.assertEqual(response.status_code, 401)
    
    def test_invoice_totals_calculation(self):
        """Test that invoice totals are calculated correctly."""
        headers = self.create_auth_headers()
        data = self.get_sample_invoice_data()
        
        response = self.client.post('/api/invoices/', json=data, headers=headers)
        self.assertEqual(response.status_code, 201)
        
        invoice_data = response.get_json()['invoice']
        self.assertEqual(invoice_data['subtotal'], 200.0)
        self.assertEqual(invoice_data['tax_amount'], 17.0)
        self.assertEqual(invoice_data['total_amount'], 217.0)
    
    def test_user_isolation(self):
        """Test that users can only access their own invoices."""
        headers1 = self.create_auth_headers()
        data = self.get_sample_invoice_data()
        create_response = self.client.post('/api/invoices/', json=data, headers=headers1)
        invoice_id = create_response.get_json()['invoice']['id']
        
        with self.app.app_context():
            user2 = User(username='testuser2', email='test2@example.com')
            user2.set_password('testpass2')
            db.session.add(user2)
            db.session.commit()
            user2_id = user2.id
        
        with self.app.app_context():
            token2 = create_access_token(identity=str(user2_id))
            headers2 = {'Authorization': f'Bearer {token2}'}
        
        response = self.client.get(f'/api/invoices/{invoice_id}', headers=headers2)
        self.assertEqual(response.status_code, 404)


def run_invoice_tests():
    """Run all Invoice API tests and return results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestInvoiceAPI)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run the tests
    success = run_invoice_tests()
    if success:
        print("\n✅ All Invoice API tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some Invoice API tests failed!")
        sys.exit(1)
