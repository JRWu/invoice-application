# Backend Tests

This directory contains all backend tests for the Invoice Application.

## Structure

```
tests/
├── __init__.py                 # Makes tests a Python package
├── README.md                  # This file
├── run_tests.py               # Test runner script
├── test_jwt.py                # JWT authentication tests
├── test_auth_integration.py   # Authentication integration tests
├── test_auth_security.py      # Authentication security tests
└── test_utils.py              # Test utilities and helpers
```

## Running Tests

### Run All Tests
```bash
# From the backend directory
python3 tests/run_tests.py
```

### Run Specific Test File
```bash
# From the backend directory
python3 tests/test_jwt.py
python3 tests/test_auth_integration.py
python3 tests/test_auth_security.py
```

### Run Tests with Python's unittest module
```bash
# From the backend directory
python3 -m unittest discover tests -v
```

### Run Individual Test Classes
```bash
# From the backend directory
python3 -m unittest tests.test_auth_integration.TestAuthIntegration -v
python3 -m unittest tests.test_auth_security.TestAuthSecurity -v
```

## Test Categories

### JWT Authentication Tests (`test_jwt.py`)
- Token creation with string identities
- Token creation with integer IDs (converted to strings)
- Token decoding and validation
- Token identity consistency
- Required JWT claims verification
- Invalid token handling

### Authentication Integration Tests (`test_auth_integration.py`)
- Complete authentication flow testing (register → login → profile)
- Registration endpoint validation (success, duplicate users, missing fields)
- Login endpoint validation (success, invalid credentials, missing fields)
- Profile endpoint validation (valid token, invalid token, missing token)
- Password hashing verification
- End-to-end authentication scenarios

### Authentication Security Tests (`test_auth_security.py`)
- Password hashing security and consistency
- SQL injection protection
- Token tampering protection
- Token expiration handling
- Malformed request handling
- Case sensitivity in credentials
- Special characters in usernames and passwords
- Long input handling
- Concurrent registration attempts

### Test Utilities (`test_utils.py`)
- `TestDataFactory`: Factory for creating test data
- `AuthTestHelper`: Helper methods for authentication testing
- `DatabaseTestHelper`: Database operations for tests
- Common test data constants and patterns
- SQL injection and token tampering test cases

## Using Test Utilities

The `test_utils.py` module provides helpful utilities for writing tests:

```python
from test_utils import TestDataFactory, AuthTestHelper, DatabaseTestHelper

# Create test data
user_data = TestDataFactory.create_user_data(username="testuser")
login_data = TestDataFactory.create_login_data()

# Use authentication helper
auth_helper = AuthTestHelper(self.client, self.app)
response, data = auth_helper.register_and_login(user_data)
auth_helper.assert_successful_auth_response(response, "testuser")

# Use database helper
db_helper = DatabaseTestHelper(self.app)
user_count = db_helper.get_user_count()
```

## Security Testing

The security tests cover important attack vectors:

- **SQL Injection**: Tests various SQL injection attempts in login/registration
- **Token Tampering**: Tests protection against modified JWT tokens
- **Password Security**: Verifies proper hashing and salt usage
- **Input Validation**: Tests handling of malformed and oversized inputs
- **Concurrent Access**: Tests race conditions in user registration

## Integration Testing

Integration tests verify the complete authentication flow:

1. **Registration Flow**: User registration with validation
2. **Login Flow**: Authentication with registered credentials
3. **Profile Access**: Protected route access with JWT tokens
4. **Error Handling**: Proper error responses for invalid scenarios

## Adding New Tests

1. Create a new test file following the naming convention `test_*.py`
2. Import the `unittest` module and create a test class inheriting from `unittest.TestCase`
3. Add the parent directory to the Python path to import backend modules:
   ```python
   import sys
   import os
   sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   ```
4. Use test utilities from `test_utils.py` for common operations
5. Write test methods starting with `test_`
6. Use `setUp()` and `tearDown()` methods for test fixtures if needed

## Example Test Structure

```python
import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from test_utils import TestDataFactory, AuthTestHelper

class TestYourFeature(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.auth_helper = AuthTestHelper(self.client, self.app)
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_your_feature(self):
        user_data = TestDataFactory.create_user_data()
        response, data = self.auth_helper.register_user(user_data)
        self.auth_helper.assert_successful_auth_response(response, user_data['username'])

if __name__ == "__main__":
    unittest.main()
```

## Best Practices

- **Independence**: All tests should be independent and not rely on external state
- **Descriptive Names**: Use descriptive test method names that explain what is being tested
- **Documentation**: Include docstrings for test classes and methods
- **Mocking**: Mock external dependencies when necessary
- **AAA Pattern**: Follow the Arrange, Act, Assert pattern
- **Test Data**: Use `TestDataFactory` for consistent test data creation
- **Helpers**: Leverage `AuthTestHelper` and `DatabaseTestHelper` for common operations
- **Security**: Include security tests for any authentication-related features
- **Edge Cases**: Test edge cases, error conditions, and boundary values

## Performance Considerations

- Use in-memory SQLite database for fast test execution
- Clean up database state between tests
- Use test utilities to reduce code duplication
- Group related tests in the same test class for better organization
