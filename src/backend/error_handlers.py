from flask import jsonify
from typing import Tuple, Dict, Any

class ValidationError(Exception):
    """Custom exception for validation errors."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class AuthorizationError(Exception):
    """Custom exception for authorization errors."""
    def __init__(self, message: str, status_code: int = 403):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class NotFoundError(Exception):
    """Custom exception for resource not found errors."""
    def __init__(self, message: str, status_code: int = 404):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class DatabaseError(Exception):
    """Custom exception for database operation errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def handle_validation_error(error: ValidationError) -> Tuple[Dict[str, Any], int]:
    """Handle validation errors and return JSON response."""
    return jsonify({'error': error.message}), error.status_code

def handle_authentication_error(error: AuthenticationError) -> Tuple[Dict[str, Any], int]:
    """Handle authentication errors and return JSON response."""
    return jsonify({'error': error.message}), error.status_code

def handle_authorization_error(error: AuthorizationError) -> Tuple[Dict[str, Any], int]:
    """Handle authorization errors and return JSON response."""
    return jsonify({'error': error.message}), error.status_code

def handle_not_found_error(error: NotFoundError) -> Tuple[Dict[str, Any], int]:
    """Handle not found errors and return JSON response."""
    return jsonify({'error': error.message}), error.status_code

def handle_database_error(error: DatabaseError) -> Tuple[Dict[str, Any], int]:
    """Handle database errors and return JSON response."""
    return jsonify({'error': error.message}), error.status_code

def handle_generic_error(error: Exception) -> Tuple[Dict[str, Any], int]:
    """Handle generic exceptions and return JSON response."""
    return jsonify({'error': 'An unexpected error occurred'}), 500

def create_error_response(message: str, status_code: int = 400) -> Tuple[Dict[str, Any], int]:
    """Create a standardized error response."""
    return jsonify({'error': message}), status_code

def create_success_response(message: str, data: Dict[str, Any] = None, status_code: int = 200) -> Tuple[Dict[str, Any], int]:
    """Create a standardized success response."""
    response = {'message': message}
    if data:
        response.update(data)
    return jsonify(response), status_code

def validate_and_raise(validation_func, data: Dict[str, Any], error_class=ValidationError):
    """Helper function to validate data and raise custom exception if invalid."""
    error_message = validation_func(data)
    if error_message:
        raise error_class(error_message)
