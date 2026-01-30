#!/usr/bin/env python3
"""
Data Validation Tests

Tests for data validation functionality and error handling.
"""

import sys
import os
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation import (
    validate_required_fields, validate_email, validate_password, validate_username,
    validate_user_data, validate_date_string, validate_numeric_field,
    validate_invoice_data, validate_invoice_item
)
from error_handlers import (
    ValidationError, AuthenticationError, AuthorizationError, NotFoundError,
    DatabaseError, validate_and_raise, create_error_response, create_success_response
)

class TestDataValidation(unittest.TestCase):
    """Test cases for data validation functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.valid_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'company_name': 'Test Company'
        }
        
        self.valid_invoice_data = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'due_date': '2024-12-31',
            'tax_rate': 10.0,
            'status': 'draft',
            'items': [
                {
                    'description': 'Test item',
                    'quantity': 2.0,
                    'unit_price': 50.0
                }
            ]
        }
    
    def tearDown(self):
        """Clean up after each test method."""
        pass
    
    def test_validate_required_fields_success(self):
        """Test that validation passes when all required fields are present."""
        data = {'field1': 'value1', 'field2': 'value2'}
        result = validate_required_fields(data, ['field1', 'field2'])
        self.assertIsNone(result)
    
    def test_validate_required_fields_missing(self):
        """Test that validation fails when required fields are missing."""
        data = {'field1': 'value1'}
        result = validate_required_fields(data, ['field1', 'field2'])
        self.assertEqual(result, 'field2 is required')
    
    def test_validate_required_fields_empty(self):
        """Test that validation fails when required fields are empty."""
        data = {'field1': 'value1', 'field2': ''}
        result = validate_required_fields(data, ['field1', 'field2'])
        self.assertEqual(result, 'field2 is required')
    
    def test_validate_email_success(self):
        """Test that valid email addresses pass validation."""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org'
        ]
        for email in valid_emails:
            result = validate_email(email)
            self.assertIsNone(result, f'Email {email} should be valid')
    
    def test_validate_email_invalid_format(self):
        """Test that invalid email formats fail validation."""
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user@domain',
            'user.domain.com'
        ]
        for email in invalid_emails:
            result = validate_email(email)
            self.assertIsNotNone(result, f'Email {email} should be invalid')
            self.assertIn('Invalid email format', result)
    
    def test_validate_email_empty(self):
        """Test that empty email fails validation."""
        result = validate_email('')
        self.assertEqual(result, 'Email is required')
    
    def test_validate_password_success(self):
        """Test that valid passwords pass validation."""
        valid_passwords = ['password123', 'mySecurePass', 'test1234']
        for password in valid_passwords:
            result = validate_password(password)
            self.assertIsNone(result, f'Password {password} should be valid')
    
    def test_validate_password_too_short(self):
        """Test that short passwords fail validation."""
        result = validate_password('short')
        self.assertIn('must be at least 8 characters', result)
    
    def test_validate_password_empty(self):
        """Test that empty password fails validation."""
        result = validate_password('')
        self.assertEqual(result, 'Password is required')
    
    def test_validate_username_success(self):
        """Test that valid usernames pass validation."""
        valid_usernames = ['testuser', 'user123', 'test_user', 'user-name']
        for username in valid_usernames:
            result = validate_username(username)
            self.assertIsNone(result, f'Username {username} should be valid')
    
    def test_validate_username_invalid_characters(self):
        """Test that usernames with invalid characters fail validation."""
        invalid_usernames = ['user@name', 'user.name', 'user name', 'user#name']
        for username in invalid_usernames:
            result = validate_username(username)
            self.assertIsNotNone(result, f'Username {username} should be invalid')
    
    def test_validate_user_data_success(self):
        """Test that valid user data passes validation."""
        result = validate_user_data(self.valid_user_data)
        self.assertIsNone(result)
    
    def test_validate_user_data_missing_fields(self):
        """Test that user data with missing required fields fails validation."""
        invalid_data = {'username': 'testuser', 'email': 'test@example.com'}
        result = validate_user_data(invalid_data)
        self.assertEqual(result, 'password is required')
    
    def test_validate_date_string_success(self):
        """Test that valid date strings pass validation."""
        result = validate_date_string('2024-12-31', 'Test date')
        self.assertIsNone(result)
    
    def test_validate_date_string_invalid_format(self):
        """Test that invalid date formats fail validation."""
        result = validate_date_string('31-12-2024', 'Test date')
        self.assertIn('must be in YYYY-MM-DD format', result)
    
    def test_validate_numeric_field_success(self):
        """Test that valid numeric values pass validation."""
        result = validate_numeric_field(10.5, 'Test field')
        self.assertIsNone(result)
    
    def test_validate_numeric_field_invalid(self):
        """Test that non-numeric values fail validation."""
        result = validate_numeric_field('not_a_number', 'Test field')
        self.assertIn('must be a valid number', result)
    
    def test_validate_numeric_field_negative(self):
        """Test that negative values fail validation when min_value is set."""
        result = validate_numeric_field(-5, 'Test field', 0)
        self.assertIn('must be 0 or greater', result)
    
    def test_validate_invoice_data_success(self):
        """Test that valid invoice data passes validation."""
        result = validate_invoice_data(self.valid_invoice_data)
        self.assertIsNone(result)
    
    def test_validate_invoice_data_missing_items(self):
        """Test that invoice data without items fails validation."""
        invalid_data = self.valid_invoice_data.copy()
        invalid_data['items'] = []
        result = validate_invoice_data(invalid_data)
        self.assertEqual(result, 'At least one item is required')
    
    def test_validate_invoice_data_no_items_field(self):
        """Test that invoice data without items field fails validation."""
        invalid_data = self.valid_invoice_data.copy()
        del invalid_data['items']
        result = validate_invoice_data(invalid_data)
        self.assertEqual(result, 'items is required')
    
    def test_validate_invoice_data_invalid_status(self):
        """Test that invoice data with invalid status fails validation."""
        invalid_data = self.valid_invoice_data.copy()
        invalid_data['status'] = 'invalid_status'
        result = validate_invoice_data(invalid_data)
        self.assertIn('Status must be one of', result)
    
    def test_validate_invoice_item_success(self):
        """Test that valid invoice item passes validation."""
        item = {
            'description': 'Test item',
            'quantity': 2.0,
            'unit_price': 50.0
        }
        result = validate_invoice_item(item)
        self.assertIsNone(result)
    
    def test_validate_invoice_item_missing_fields(self):
        """Test that invoice item with missing fields fails validation."""
        item = {'description': 'Test item', 'quantity': 2.0}
        result = validate_invoice_item(item)
        self.assertEqual(result, 'unit_price is required')

class TestErrorHandlers(unittest.TestCase):
    """Test cases for error handling functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        pass
    
    def tearDown(self):
        """Clean up after each test method."""
        pass
    
    def test_validation_error_creation(self):
        """Test that ValidationError is created correctly."""
        error = ValidationError('Test error message')
        self.assertEqual(error.message, 'Test error message')
        self.assertEqual(error.status_code, 400)
    
    def test_validation_error_custom_status(self):
        """Test that ValidationError accepts custom status code."""
        error = ValidationError('Test error', 422)
        self.assertEqual(error.status_code, 422)
    
    def test_authentication_error_creation(self):
        """Test that AuthenticationError is created correctly."""
        error = AuthenticationError('Auth failed')
        self.assertEqual(error.message, 'Auth failed')
        self.assertEqual(error.status_code, 401)
    
    def test_validate_and_raise_success(self):
        """Test that validate_and_raise doesn't raise when validation passes."""
        def always_valid(data):
            return None
        
        try:
            validate_and_raise(always_valid, {})
        except Exception:
            self.fail('validate_and_raise should not raise when validation passes')
    
    def test_validate_and_raise_failure(self):
        """Test that validate_and_raise raises ValidationError when validation fails."""
        def always_invalid(data):
            return 'Validation failed'
        
        with self.assertRaises(ValidationError) as context:
            validate_and_raise(always_invalid, {})
        
        self.assertEqual(str(context.exception), 'Validation failed')
    
    def test_create_error_response(self):
        """Test that error responses are created correctly."""
        from flask import Flask
        app = Flask(__name__)
        with app.app_context():
            response, status_code = create_error_response('Test error', 400)
            self.assertEqual(status_code, 400)
    
    def test_create_success_response(self):
        """Test that success responses are created correctly."""
        from flask import Flask
        app = Flask(__name__)
        with app.app_context():
            response, status_code = create_success_response('Success', {'data': 'test'})
            self.assertEqual(status_code, 200)

def run_validation_tests():
    """Run all validation tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandlers))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_validation_tests()
    if success:
        print("\n✅ All validation tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some validation tests failed!")
        sys.exit(1)
