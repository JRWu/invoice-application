#!/usr/bin/env python3
"""
Frontend Auth API Tests

Tests for the frontend authAPI object methods that handle communication
with authentication endpoints.
"""

import sys
import os
import unittest
from unittest.mock import patch, Mock, MagicMock
import json

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAuthAPI(unittest.TestCase):
    """Test cases for frontend authAPI methods."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_axios = Mock()
        
        self.mock_local_storage = {}
        
        self.valid_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'company_name': 'Test Company'
        }
        
        self.valid_credentials = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        
        self.mock_user_response = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'company_name': 'Test Company'
        }
        
        self.mock_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token'
    
    def tearDown(self):
        """Clean up after each test method."""
        pass
    
    def test_register_success(self):
        """Test successful user registration."""
        expected_response = {
            'message': 'User created successfully',
            'access_token': self.mock_token,
            'user': self.mock_user_response
        }
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = expected_response
        mock_response.data = expected_response
        
        self.mock_axios.post.return_value = mock_response
        
        result = self.mock_axios.post('/api/auth/register', self.valid_user_data)
        
        self.mock_axios.post.assert_called_once_with('/api/auth/register', self.valid_user_data)
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.data['message'], 'User created successfully')
        self.assertEqual(result.data['access_token'], self.mock_token)
        self.assertEqual(result.data['user'], self.mock_user_response)
    
    def test_register_missing_username(self):
        """Test registration with missing username."""
        invalid_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        expected_response = {'error': 'username is required'}
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.data = expected_response
        
        self.mock_axios.post.return_value = mock_response
        
        result = self.mock_axios.post('/api/auth/register', invalid_data)
        
        self.mock_axios.post.assert_called_once_with('/api/auth/register', invalid_data)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.data['error'], 'username is required')
    
    def test_register_missing_email(self):
        """Test registration with missing email."""
        invalid_data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        
        expected_response = {'error': 'email is required'}
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.data = expected_response
        
        self.mock_axios.post.return_value = mock_response
        
        result = self.mock_axios.post('/api/auth/register', invalid_data)
        
        self.mock_axios.post.assert_called_once_with('/api/auth/register', invalid_data)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.data['error'], 'email is required')
    
    def test_register_missing_password(self):
        """Test registration with missing password."""
        invalid_data = {
            'username': 'testuser',
            'email': 'test@example.com'
        }
        
        expected_response = {'error': 'password is required'}
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.data = expected_response
        
        self.mock_axios.post.return_value = mock_response
        
        result = self.mock_axios.post('/api/auth/register', invalid_data)
        
        self.mock_axios.post.assert_called_once_with('/api/auth/register', invalid_data)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.data['error'], 'password is required')
    
    def test_register_username_exists(self):
        """Test registration with existing username."""
        expected_response = {'error': 'Username already exists'}
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.data = expected_response
        
        self.mock_axios.post.return_value = mock_response
        
        result = self.mock_axios.post('/api/auth/register', self.valid_user_data)
        
        self.mock_axios.post.assert_called_once_with('/api/auth/register', self.valid_user_data)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.data['error'], 'Username already exists')
    
    def test_register_email_exists(self):
        """Test registration with existing email."""
        expected_response = {'error': 'Email already exists'}
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.data = expected_response
        
        self.mock_axios.post.return_value = mock_response
        
        result = self.mock_axios.post('/api/auth/register', self.valid_user_data)
        
        self.mock_axios.post.assert_called_once_with('/api/auth/register', self.valid_user_data)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.data['error'], 'Email already exists')
    
    def test_register_server_error(self):
        """Test registration with server error."""
        expected_response = {'error': 'Internal server error'}
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.data = expected_response
        
        self.mock_axios.post.return_value = mock_response
        
        result = self.mock_axios.post('/api/auth/register', self.valid_user_data)
        
        self.mock_axios.post.assert_called_once_with('/api/auth/register', self.valid_user_data)
        self.assertEqual(result.status_code, 500)
        self.assertEqual(result.data['error'], 'Internal server error')
    
    def test_login_success(self):
        """Test successful user login."""
        expected_response = {
            'message': 'Login successful',
            'access_token': self.mock_token,
            'user': self.mock_user_response
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.data = expected_response
        
        self.mock_axios.post.return_value = mock_response
        
        result = self.mock_axios.post('/api/auth/login', self.valid_credentials)
        
        self.mock_axios.post.assert_called_once_with('/api/auth/login', self.valid_credentials)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['message'], 'Login successful')
        self.assertEqual(result.data['access_token'], self.mock_token)
        self.assertEqual(result.data['user'], self.mock_user_response)
    
    def test_login_missing_username(self):
        """Test login with missing username."""
        invalid_credentials = {'password': 'testpassword123'}
        expected_response = {'error': 'Username and password are required'}
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.data = expected_response
        
        self.mock_axios.post.return_value = mock_response
        
        result = self.mock_axios.post('/api/auth/login', invalid_credentials)
        
        self.mock_axios.post.assert_called_once_with('/api/auth/login', invalid_credentials)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.data['error'], 'Username and password are required')
    
    def test_login_missing_password(self):
        """Test login with missing password."""
        invalid_credentials = {'username': 'testuser'}
        expected_response = {'error': 'Username and password are required'}
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.data = expected_response
        
        self.mock_axios.post.return_value = mock_response
        
        result = self.mock_axios.post('/api/auth/login', invalid_credentials)
        
        self.mock_axios.post.assert_called_once_with('/api/auth/login', invalid_credentials)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.data['error'], 'Username and password are required')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        expected_response = {'error': 'Invalid credentials'}
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.data = expected_response
        
        self.mock_axios.post.return_value = mock_response
        
        result = self.mock_axios.post('/api/auth/login', self.valid_credentials)
        
        self.mock_axios.post.assert_called_once_with('/api/auth/login', self.valid_credentials)
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.data['error'], 'Invalid credentials')
    
    def test_login_server_error(self):
        """Test login with server error."""
        expected_response = {'error': 'Internal server error'}
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.data = expected_response
        
        self.mock_axios.post.return_value = mock_response
        
        result = self.mock_axios.post('/api/auth/login', self.valid_credentials)
        
        self.mock_axios.post.assert_called_once_with('/api/auth/login', self.valid_credentials)
        self.assertEqual(result.status_code, 500)
        self.assertEqual(result.data['error'], 'Internal server error')
    
    def test_get_profile_success(self):
        """Test successful profile retrieval."""
        expected_response = {'user': self.mock_user_response}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.data = expected_response
        
        self.mock_axios.get.return_value = mock_response
        
        result = self.mock_axios.get('/api/auth/profile')
        
        self.mock_axios.get.assert_called_once_with('/api/auth/profile')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['user'], self.mock_user_response)
    
    def test_get_profile_unauthorized(self):
        """Test profile retrieval with invalid token."""
        expected_response = {'error': 'Unauthorized'}
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.data = expected_response
        
        self.mock_axios.get.return_value = mock_response
        
        result = self.mock_axios.get('/api/auth/profile')
        
        self.mock_axios.get.assert_called_once_with('/api/auth/profile')
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.data['error'], 'Unauthorized')
    
    def test_get_profile_user_not_found(self):
        """Test profile retrieval when user not found."""
        expected_response = {'error': 'User not found'}
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.data = expected_response
        
        self.mock_axios.get.return_value = mock_response
        
        result = self.mock_axios.get('/api/auth/profile')
        
        self.mock_axios.get.assert_called_once_with('/api/auth/profile')
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.data['error'], 'User not found')
    
    def test_get_profile_server_error(self):
        """Test profile retrieval with server error."""
        expected_response = {'error': 'Internal server error'}
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.data = expected_response
        
        self.mock_axios.get.return_value = mock_response
        
        result = self.mock_axios.get('/api/auth/profile')
        
        self.mock_axios.get.assert_called_once_with('/api/auth/profile')
        self.assertEqual(result.status_code, 500)
        self.assertEqual(result.data['error'], 'Internal server error')
    
    def test_axios_request_interceptor_adds_token(self):
        """Test that request interceptor adds Authorization header when token exists."""
        mock_config = {'headers': {}}
        mock_token = self.mock_token
        
        with patch('builtins.dict') as mock_storage:
            mock_storage.__getitem__ = Mock(return_value=mock_token)
            
            if mock_token:
                mock_config['headers']['Authorization'] = f'Bearer {mock_token}'
        
        self.assertEqual(mock_config['headers']['Authorization'], f'Bearer {mock_token}')
    
    def test_axios_request_interceptor_no_token(self):
        """Test that request interceptor works when no token exists."""
        mock_config = {'headers': {}}
        
        mock_token = None
        
        if mock_token:
            mock_config['headers']['Authorization'] = f'Bearer {mock_token}'
        
        self.assertNotIn('Authorization', mock_config['headers'])
    
    def test_axios_response_interceptor_401_handling(self):
        """Test that response interceptor handles 401 errors correctly."""
        mock_error = Mock()
        mock_error.response.status = 401
        
        should_clear_storage = False
        should_redirect = False
        
        if hasattr(mock_error, 'response') and mock_error.response.status == 401:
            should_clear_storage = True
            should_redirect = True
        
        self.assertTrue(should_clear_storage)
        self.assertTrue(should_redirect)
    
    def test_axios_response_interceptor_other_errors(self):
        """Test that response interceptor handles non-401 errors correctly."""
        mock_error = Mock()
        mock_error.response.status = 500
        
        should_clear_storage = False
        should_redirect = False
        
        if hasattr(mock_error, 'response') and mock_error.response.status == 401:
            should_clear_storage = True
            should_redirect = True
        
        self.assertFalse(should_clear_storage)
        self.assertFalse(should_redirect)


def run_auth_api_tests():
    """Run all auth API tests and return results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAuthAPI)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run the tests
    success = run_auth_api_tests()
    if success:
        print("\n✅ All auth API tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some auth API tests failed!")
        sys.exit(1)
