#!/usr/bin/env python3
"""
Authentication Security Tests

Tests for security aspects of authentication including password validation,
token security, and protection against common attacks.
"""

import sys
import os
import unittest
import json
import time
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, User
from config import Config
from flask_jwt_extended import create_access_token, decode_token


class TestAuthSecurity(unittest.TestCase):
    """Security tests for authentication functionality."""
    
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
    
    def test_password_hashing_security(self):
        """Test that password hashing is secure and consistent."""
        with self.app.app_context():
            user = User(username='sectest', email='sec@example.com')
            password = 'testsecurepassword123'
            
            user.set_password(password)
            
            self.assertNotEqual(user.password_hash, password)
            self.assertTrue(user.password_hash.startswith('pbkdf2:sha256:'))
            
            self.assertTrue(user.check_password(password))
            
            self.assertFalse(user.check_password('wrongpassword'))
            self.assertFalse(user.check_password(''))
            try:
                result = user.check_password(None)
                self.assertFalse(result)
            except (AttributeError, TypeError):
                pass
            
            user2 = User(username='sectest2', email='sec2@example.com')
            user2.set_password(password)
            self.assertNotEqual(user.password_hash, user2.password_hash)
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks."""
        user_data = {
            'username': 'legitimate',
            'email': 'legit@example.com',
            'password': 'legitpassword123'
        }
        self.client.post('/api/auth/register', 
                        data=json.dumps(user_data),
                        content_type='application/json')
        
        injection_attempts = [
            "admin'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "admin' OR '1'='1' --",
            "admin' OR '1'='1' /*",
            "'; SELECT * FROM users WHERE 't'='t",
            "admin'/**/OR/**/1=1--",
        ]
        
        for injection in injection_attempts:
            with self.subTest(injection=injection):
                login_data = {
                    'username': injection,
                    'password': 'anypassword'
                }
                
                response = self.client.post('/api/auth/login', 
                                          data=json.dumps(login_data),
                                          content_type='application/json')
                
                self.assertEqual(response.status_code, 401)
                data = json.loads(response.data)
                self.assertEqual(data['error'], 'Invalid credentials')
        
        login_data = {
            'username': 'legitimate',
            'password': 'legitpassword123'
        }
        response = self.client.post('/api/auth/login', 
                                  data=json.dumps(login_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
    
    def test_token_expiration_handling(self):
        """Test JWT token expiration behavior."""
        with self.app.app_context():
            user_id = "123"
            
            with patch('flask_jwt_extended.create_access_token') as mock_create:
                from datetime import timedelta
                mock_create.return_value = create_access_token(
                    identity=user_id, 
                    expires_delta=timedelta(seconds=1)
                )
                token = mock_create.return_value
            
            decoded = decode_token(token)
            self.assertEqual(decoded['sub'], user_id)
            
            time.sleep(2)
            
            with self.assertRaises(Exception):
                decode_token(token)
    
    def test_token_tampering_protection(self):
        """Test protection against token tampering."""
        user_data = {
            'username': 'tokentest',
            'email': 'token@example.com',
            'password': 'tokenpassword123'
        }
        register_response = self.client.post('/api/auth/register', 
                                           data=json.dumps(user_data),
                                           content_type='application/json')
        
        valid_token = json.loads(register_response.data)['access_token']
        
        tampered_tokens = [
            valid_token[:-5] + "XXXXX",  # Change last 5 characters
            valid_token.replace('.', 'X', 1),  # Replace first dot
            valid_token + "extra",  # Add extra characters
            valid_token[10:],  # Remove first 10 characters
            "Bearer " + valid_token,  # Add Bearer prefix (should be in header)
            "",  # Empty token
            "invalid.token.format",  # Invalid format
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",  # Invalid signature
        ]
        
        for tampered_token in tampered_tokens:
            with self.subTest(tampered_token=tampered_token[:20] + "..."):
                headers = {'Authorization': f'Bearer {tampered_token}'}
                response = self.client.get('/api/auth/profile', headers=headers)
                
                self.assertIn(response.status_code, [401, 422])
    
    def test_empty_and_malformed_requests(self):
        """Test handling of empty and malformed requests."""
        response = self.client.post('/api/auth/register', 
                                  data='{}',
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        response = self.client.post('/api/auth/register', 
                                  data='{"username": "test", "email":}',
                                  content_type='application/json')
        self.assertIn(response.status_code, [400, 500])
        
        response = self.client.post('/api/auth/register', 
                                  data='username=test&email=test@example.com',
                                  content_type='application/x-www-form-urlencoded')
        self.assertIn(response.status_code, [400, 415, 500])
        
        response = self.client.post('/api/auth/register')
        self.assertIn(response.status_code, [400, 500])
    
    def test_case_sensitivity(self):
        """Test case sensitivity in usernames and emails."""
        user_data = {
            'username': 'TestUser',
            'email': 'Test@Example.Com',
            'password': 'password123'
        }
        response = self.client.post('/api/auth/register', 
                                  data=json.dumps(user_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        user_data2 = {
            'username': 'testuser',  # lowercase
            'email': 'test@example.com',  # lowercase
            'password': 'password123'
        }
        response = self.client.post('/api/auth/register', 
                                  data=json.dumps(user_data2),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        login_data = {
            'username': 'testuser',  # Different case
            'password': 'password123'
        }
        response = self.client.post('/api/auth/login', 
                                  data=json.dumps(login_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        login_data = {
            'username': 'TESTUSER',  # Wrong case
            'password': 'password123'
        }
        response = self.client.post('/api/auth/login', 
                                  data=json.dumps(login_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 401)
    
    def test_special_characters_in_credentials(self):
        """Test handling of special characters in usernames and passwords."""
        special_cases = [
            {
                'username': 'user@domain.com',
                'email': 'user@domain.com',
                'password': 'pass!@#$%^&*()_+-=[]{}|;:,.<>?'
            },
            {
                'username': 'user_with_underscores',
                'email': 'user_with_underscores@example.com',
                'password': 'пароль123'  # Cyrillic characters
            },
            {
                'username': 'user-with-dashes',
                'email': 'user-with-dashes@example.com',
                'password': '密码123'  # Chinese characters
            },
            {
                'username': 'user.with.dots',
                'email': 'user.with.dots@example.com',
                'password': 'contraseña123'  # Spanish characters
            }
        ]
        
        for i, user_data in enumerate(special_cases):
            with self.subTest(case=i, username=user_data['username']):
                response = self.client.post('/api/auth/register', 
                                          data=json.dumps(user_data),
                                          content_type='application/json')
                self.assertEqual(response.status_code, 201)
                
                login_data = {
                    'username': user_data['username'],
                    'password': user_data['password']
                }
                response = self.client.post('/api/auth/login', 
                                          data=json.dumps(login_data),
                                          content_type='application/json')
                self.assertEqual(response.status_code, 200)
    
    def test_long_input_handling(self):
        """Test handling of very long inputs."""
        long_username = 'a' * 1000
        user_data = {
            'username': long_username,
            'email': 'long@example.com',
            'password': 'password123'
        }
        response = self.client.post('/api/auth/register', 
                                  data=json.dumps(user_data),
                                  content_type='application/json')
        self.assertIn(response.status_code, [201, 400])
        
        long_password = 'p' * 1000
        user_data = {
            'username': 'longpassuser',
            'email': 'longpass@example.com',
            'password': long_password
        }
        response = self.client.post('/api/auth/register', 
                                  data=json.dumps(user_data),
                                  content_type='application/json')
        self.assertIn(response.status_code, [201, 400])
        
        if response.status_code == 201:
            login_data = {
                'username': 'longpassuser',
                'password': long_password
            }
            response = self.client.post('/api/auth/login', 
                                      data=json.dumps(login_data),
                                      content_type='application/json')
            self.assertEqual(response.status_code, 200)
    
    def test_concurrent_registration_attempts(self):
        """Test handling of concurrent registration attempts with same credentials."""
        user_data = {
            'username': 'concurrent',
            'email': 'concurrent@example.com',
            'password': 'password123'
        }
        
        response = self.client.post('/api/auth/register', 
                                  data=json.dumps(user_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        response2 = self.client.post('/api/auth/register', 
                                   data=json.dumps(user_data),
                                   content_type='application/json')
        self.assertEqual(response2.status_code, 400)
        
        user_data2 = {
            'username': 'concurrent2',
            'email': 'concurrent@example.com',  # Same email
            'password': 'password123'
        }
        response3 = self.client.post('/api/auth/register', 
                                   data=json.dumps(user_data2),
                                   content_type='application/json')
        self.assertEqual(response3.status_code, 400)


def run_auth_security_tests():
    """Run all authentication security tests and return results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAuthSecurity)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_auth_security_tests()
    if success:
        print("\n✅ All authentication security tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some authentication security tests failed!")
        sys.exit(1)
