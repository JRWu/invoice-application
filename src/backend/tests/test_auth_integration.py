#!/usr/bin/env python3
"""
Authentication Integration Tests

Tests for the complete authentication flow including registration, login, and profile access.
"""

import sys
import os
import unittest
import json
from unittest.mock import patch

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, User
from config import Config


class TestAuthIntegration(unittest.TestCase):
    """Integration tests for authentication endpoints."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after each test method."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_register_success(self):
        """Test successful user registration."""
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword123',
            'company_name': 'Test Company'
        }
        
        response = self.client.post('/api/auth/register', 
                                  data=json.dumps(user_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'testuser')
        self.assertEqual(data['user']['email'], 'test@example.com')
        self.assertEqual(data['message'], 'User created successfully')
    
    def test_register_duplicate_username(self):
        """Test registration with duplicate username."""
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword123'
        }
        
        self.client.post('/api/auth/register', 
                        data=json.dumps(user_data),
                        content_type='application/json')
        
        duplicate_data = {
            'username': 'testuser',
            'email': 'different@example.com',
            'password': 'anotherpassword123'
        }
        
        response = self.client.post('/api/auth/register', 
                                  data=json.dumps(duplicate_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Username already exists')
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword123'
        }
        
        self.client.post('/api/auth/register', 
                        data=json.dumps(user_data),
                        content_type='application/json')
        
        duplicate_data = {
            'username': 'differentuser',
            'email': 'test@example.com',
            'password': 'anotherpassword123'
        }
        
        response = self.client.post('/api/auth/register', 
                                  data=json.dumps(duplicate_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Email already exists')
    
    def test_register_missing_required_fields(self):
        """Test registration with missing required fields."""
        test_cases = [
            ({}, 'username is required'),
            ({'username': 'test'}, 'email is required'),
            ({'username': 'test', 'email': 'test@example.com'}, 'password is required'),
        ]
        
        for user_data, expected_error in test_cases:
            with self.subTest(user_data=user_data):
                response = self.client.post('/api/auth/register', 
                                          data=json.dumps(user_data),
                                          content_type='application/json')
                
                self.assertEqual(response.status_code, 400)
                data = json.loads(response.data)
                self.assertIn('error', data)
                self.assertEqual(data['error'], expected_error)
    
    def test_login_success(self):
        """Test successful user login."""
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword123'
        }
        self.client.post('/api/auth/register', 
                        data=json.dumps(user_data),
                        content_type='application/json')
        
        login_data = {
            'username': 'testuser',
            'password': 'securepassword123'
        }
        
        response = self.client.post('/api/auth/login', 
                                  data=json.dumps(login_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'testuser')
        self.assertEqual(data['message'], 'Login successful')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword123'
        }
        self.client.post('/api/auth/register', 
                        data=json.dumps(user_data),
                        content_type='application/json')
        
        login_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post('/api/auth/login', 
                                  data=json.dumps(login_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid credentials')
    
    def test_login_nonexistent_user(self):
        """Test login with nonexistent user."""
        login_data = {
            'username': 'nonexistent',
            'password': 'somepassword'
        }
        
        response = self.client.post('/api/auth/login', 
                                  data=json.dumps(login_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid credentials')
    
    def test_login_missing_fields(self):
        """Test login with missing required fields."""
        test_cases = [
            ({}, 'Username and password are required'),
            ({'username': 'test'}, 'Username and password are required'),
            ({'password': 'test'}, 'Username and password are required'),
        ]
        
        for login_data, expected_error in test_cases:
            with self.subTest(login_data=login_data):
                response = self.client.post('/api/auth/login', 
                                          data=json.dumps(login_data),
                                          content_type='application/json')
                
                self.assertEqual(response.status_code, 400)
                data = json.loads(response.data)
                self.assertIn('error', data)
                self.assertEqual(data['error'], expected_error)
    
    def test_profile_success(self):
        """Test successful profile access with valid token."""
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword123'
        }
        register_response = self.client.post('/api/auth/register', 
                                           data=json.dumps(user_data),
                                           content_type='application/json')
        
        token = json.loads(register_response.data)['access_token']
        
        headers = {'Authorization': f'Bearer {token}'}
        response = self.client.get('/api/auth/profile', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'testuser')
        self.assertEqual(data['user']['email'], 'test@example.com')
    
    def test_profile_missing_token(self):
        """Test profile access without token."""
        response = self.client.get('/api/auth/profile')
        
        self.assertEqual(response.status_code, 401)
    
    def test_profile_invalid_token(self):
        """Test profile access with invalid token."""
        headers = {'Authorization': 'Bearer invalid.token.here'}
        response = self.client.get('/api/auth/profile', headers=headers)
        
        self.assertIn(response.status_code, [401, 422])
    
    def test_complete_auth_flow(self):
        """Test complete authentication flow: register -> login -> profile."""
        user_data = {
            'username': 'flowtest',
            'email': 'flow@example.com',
            'password': 'flowpassword123',
            'company_name': 'Flow Company'
        }
        
        register_response = self.client.post('/api/auth/register', 
                                           data=json.dumps(user_data),
                                           content_type='application/json')
        
        self.assertEqual(register_response.status_code, 201)
        register_data = json.loads(register_response.data)
        register_token = register_data['access_token']
        
        login_data = {
            'username': 'flowtest',
            'password': 'flowpassword123'
        }
        
        login_response = self.client.post('/api/auth/login', 
                                        data=json.dumps(login_data),
                                        content_type='application/json')
        
        self.assertEqual(login_response.status_code, 200)
        login_data = json.loads(login_response.data)
        login_token = login_data['access_token']
        
        for token in [register_token, login_token]:
            with self.subTest(token_source='register' if token == register_token else 'login'):
                headers = {'Authorization': f'Bearer {token}'}
                profile_response = self.client.get('/api/auth/profile', headers=headers)
                
                self.assertEqual(profile_response.status_code, 200)
                profile_data = json.loads(profile_response.data)
                self.assertEqual(profile_data['user']['username'], 'flowtest')
                self.assertEqual(profile_data['user']['email'], 'flow@example.com')
                self.assertEqual(profile_data['user']['company_name'], 'Flow Company')
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed and not stored in plain text."""
        user_data = {
            'username': 'hashtest',
            'email': 'hash@example.com',
            'password': 'plaintextpassword'
        }
        
        self.client.post('/api/auth/register', 
                        data=json.dumps(user_data),
                        content_type='application/json')
        
        with self.app.app_context():
            user = User.query.filter_by(username='hashtest').first()
            self.assertIsNotNone(user)
            self.assertNotEqual(user.password_hash, 'plaintextpassword')
            self.assertTrue(user.password_hash.startswith('pbkdf2:sha256:'))
            self.assertTrue(user.check_password('plaintextpassword'))
            self.assertFalse(user.check_password('wrongpassword'))


def run_auth_integration_tests():
    """Run all authentication integration tests and return results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAuthIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_auth_integration_tests()
    if success:
        print("\n✅ All authentication integration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some authentication integration tests failed!")
        sys.exit(1)
