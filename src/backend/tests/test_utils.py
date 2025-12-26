#!/usr/bin/env python3
"""
Test Utilities

Common utilities and helpers for authentication testing.
"""

import sys
import os
import json
from typing import Dict, Any, Optional

# Add the parent directory to the path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User
from flask_jwt_extended import create_access_token


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_user_data(
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "testpassword123",
        company_name: str = "Test Company"
    ) -> Dict[str, str]:
        """Create user registration data."""
        return {
            'username': username,
            'email': email,
            'password': password,
            'company_name': company_name
        }
    
    @staticmethod
    def create_login_data(
        username: str = "testuser",
        password: str = "testpassword123"
    ) -> Dict[str, str]:
        """Create login data."""
        return {
            'username': username,
            'password': password
        }
    
    @staticmethod
    def create_multiple_users(count: int = 3) -> list:
        """Create multiple unique user data sets."""
        users = []
        for i in range(count):
            users.append({
                'username': f'testuser{i}',
                'email': f'test{i}@example.com',
                'password': f'testpassword{i}123',
                'company_name': f'Test Company {i}'
            })
        return users


class AuthTestHelper:
    """Helper class for authentication testing."""
    
    def __init__(self, test_client, app):
        self.client = test_client
        self.app = app
    
    def register_user(self, user_data: Optional[Dict[str, str]] = None) -> tuple:
        """Register a user and return response and data."""
        if user_data is None:
            user_data = TestDataFactory.create_user_data()
        
        response = self.client.post('/api/auth/register', 
                                  data=json.dumps(user_data),
                                  content_type='application/json')
        
        data = json.loads(response.data) if response.data else {}
        return response, data
    
    def login_user(self, login_data: Optional[Dict[str, str]] = None) -> tuple:
        """Login a user and return response and data."""
        if login_data is None:
            login_data = TestDataFactory.create_login_data()
        
        response = self.client.post('/api/auth/login', 
                                  data=json.dumps(login_data),
                                  content_type='application/json')
        
        data = json.loads(response.data) if response.data else {}
        return response, data
    
    def get_profile(self, token: str) -> tuple:
        """Get user profile with token and return response and data."""
        headers = {'Authorization': f'Bearer {token}'}
        response = self.client.get('/api/auth/profile', headers=headers)
        
        data = json.loads(response.data) if response.data else {}
        return response, data
    
    def register_and_login(self, user_data: Optional[Dict[str, str]] = None) -> tuple:
        """Register a user and then login, return login response and data."""
        if user_data is None:
            user_data = TestDataFactory.create_user_data()
        
        self.register_user(user_data)
        
        login_data = {
            'username': user_data['username'],
            'password': user_data['password']
        }
        return self.login_user(login_data)
    
    def create_authenticated_headers(self, token: str) -> Dict[str, str]:
        """Create headers with authentication token."""
        return {'Authorization': f'Bearer {token}'}
    
    def create_user_in_db(self, user_data: Optional[Dict[str, str]] = None) -> User:
        """Create a user directly in the database (bypassing API)."""
        if user_data is None:
            user_data = TestDataFactory.create_user_data()
        
        with self.app.app_context():
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                company_name=user_data.get('company_name', '')
            )
            user.set_password(user_data['password'])
            
            db.session.add(user)
            db.session.commit()
            
            return user
    
    def create_token_for_user(self, user_id: int) -> str:
        """Create a JWT token for a user ID."""
        with self.app.app_context():
            return create_access_token(identity=str(user_id))
    
    def assert_successful_auth_response(self, response, expected_username: str):
        """Assert that an auth response is successful and contains expected data."""
        assert response.status_code in [200, 201], f"Expected success status, got {response.status_code}"
        
        data = json.loads(response.data)
        assert 'access_token' in data, "Response should contain access_token"
        assert 'user' in data, "Response should contain user data"
        assert data['user']['username'] == expected_username, f"Expected username {expected_username}"
        
        return data
    
    def assert_error_response(self, response, expected_status: int, expected_error: str = None):
        """Assert that a response contains an error."""
        assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}"
        
        data = json.loads(response.data)
        assert 'error' in data, "Error response should contain error field"
        
        if expected_error:
            assert data['error'] == expected_error, f"Expected error '{expected_error}', got '{data['error']}'"
        
        return data


class DatabaseTestHelper:
    """Helper for database operations in tests."""
    
    def __init__(self, app):
        self.app = app
    
    def clean_database(self):
        """Clean all data from test database."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()
    
    def get_user_count(self) -> int:
        """Get total number of users in database."""
        with self.app.app_context():
            return User.query.count()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username from database."""
        with self.app.app_context():
            return User.query.filter_by(username=username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email from database."""
        with self.app.app_context():
            return User.query.filter_by(email=email).first()
    
    def verify_password_hashed(self, username: str, original_password: str) -> bool:
        """Verify that a user's password is properly hashed."""
        user = self.get_user_by_username(username)
        if not user:
            return False
        
        if user.password_hash == original_password:
            return False
        
        if not user.password_hash.startswith('pbkdf2:sha256:'):
            return False
        
        return user.check_password(original_password)


VALID_USER_DATA = TestDataFactory.create_user_data()
VALID_LOGIN_DATA = TestDataFactory.create_login_data()

INVALID_USER_DATA_CASES = [
    ({}, 'username is required'),
    ({'username': 'test'}, 'email is required'),
    ({'username': 'test', 'email': 'test@example.com'}, 'password is required'),
    ({'username': '', 'email': 'test@example.com', 'password': 'test123'}, 'username is required'),
    ({'username': 'test', 'email': '', 'password': 'test123'}, 'email is required'),
    ({'username': 'test', 'email': 'test@example.com', 'password': ''}, 'password is required'),
]

INVALID_LOGIN_DATA_CASES = [
    ({}, 'Username and password are required'),
    ({'username': 'test'}, 'Username and password are required'),
    ({'password': 'test'}, 'Username and password are required'),
    ({'username': '', 'password': 'test'}, 'Username and password are required'),
    ({'username': 'test', 'password': ''}, 'Username and password are required'),
]

SQL_INJECTION_ATTEMPTS = [
    "admin'; DROP TABLE users; --",
    "admin' OR '1'='1",
    "admin' OR '1'='1' --",
    "admin' OR '1'='1' /*",
    "'; SELECT * FROM users WHERE 't'='t",
    "admin'/**/OR/**/1=1--",
    "1' OR '1'='1",
    "' OR 1=1--",
    "' OR 'a'='a",
    "') OR ('1'='1",
]

def get_token_tampering_cases(valid_token: str) -> list:
    """Get list of tampered tokens for testing."""
    return [
        valid_token[:-5] + "XXXXX",  # Change last 5 characters
        valid_token.replace('.', 'X', 1),  # Replace first dot
        valid_token + "extra",  # Add extra characters
        valid_token[10:],  # Remove first 10 characters
        "Bearer " + valid_token,  # Add Bearer prefix (should be in header)
        "",  # Empty token
        "invalid.token.format",  # Invalid format
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",  # Invalid signature
        "null",  # String null
        "undefined",  # String undefined
    ]
