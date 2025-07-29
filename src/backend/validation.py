import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
MIN_PASSWORD_LENGTH = 8
MAX_USERNAME_LENGTH = 80
MAX_EMAIL_LENGTH = 120
MAX_COMPANY_NAME_LENGTH = 200
MAX_CUSTOMER_NAME_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 500

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Optional[str]:
    """Validate that all required fields are present and not empty."""
    for field in required_fields:
        if not data.get(field):
            return f'{field} is required'
    return None

def validate_email(email: str) -> Optional[str]:
    """Validate email format."""
    if not email:
        return 'Email is required'
    if len(email) > MAX_EMAIL_LENGTH:
        return f'Email must be {MAX_EMAIL_LENGTH} characters or less'
    if not re.match(EMAIL_REGEX, email):
        return 'Invalid email format'
    return None

def validate_password(password: str) -> Optional[str]:
    """Validate password strength."""
    if not password:
        return 'Password is required'
    if len(password) < MIN_PASSWORD_LENGTH:
        return f'Password must be at least {MIN_PASSWORD_LENGTH} characters long'
    return None

def validate_username(username: str) -> Optional[str]:
    """Validate username format and length."""
    if not username:
        return 'Username is required'
    if len(username) > MAX_USERNAME_LENGTH:
        return f'Username must be {MAX_USERNAME_LENGTH} characters or less'
    if not username.replace('_', '').replace('-', '').isalnum():
        return 'Username can only contain letters, numbers, hyphens, and underscores'
    return None

def validate_user_data(data: Dict[str, Any]) -> Optional[str]:
    """Validate user registration/update data."""
    required_fields = ['username', 'email', 'password']
    error = validate_required_fields(data, required_fields)
    if error:
        return error
    
    error = validate_username(data['username'])
    if error:
        return error
    
    error = validate_email(data['email'])
    if error:
        return error
    
    error = validate_password(data['password'])
    if error:
        return error
    
    if data.get('company_name') and len(data['company_name']) > MAX_COMPANY_NAME_LENGTH:
        return f'Company name must be {MAX_COMPANY_NAME_LENGTH} characters or less'
    
    return None

def validate_date_string(date_str: str, field_name: str) -> Optional[str]:
    """Validate date string format (YYYY-MM-DD)."""
    if not date_str:
        return f'{field_name} is required'
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return None
    except ValueError:
        return f'{field_name} must be in YYYY-MM-DD format'

def validate_numeric_field(value: Any, field_name: str, min_value: float = 0) -> Optional[str]:
    """Validate numeric fields."""
    if value is None:
        return f'{field_name} is required'
    try:
        num_value = float(value)
        if num_value < min_value:
            return f'{field_name} must be {min_value} or greater'
        return None
    except (ValueError, TypeError):
        return f'{field_name} must be a valid number'

def validate_invoice_data(data: Dict[str, Any]) -> Optional[str]:
    """Validate invoice creation/update data."""
    required_fields = ['customer_name', 'due_date']
    error = validate_required_fields(data, required_fields)
    if error:
        return error
    
    if len(data['customer_name']) > MAX_CUSTOMER_NAME_LENGTH:
        return f'Customer name must be {MAX_CUSTOMER_NAME_LENGTH} characters or less'
    
    error = validate_date_string(data['due_date'], 'Due date')
    if error:
        return error
    
    if 'tax_rate' in data:
        error = validate_numeric_field(data['tax_rate'], 'Tax rate', 0)
        if error:
            return error
        if float(data['tax_rate']) > 100:
            return 'Tax rate cannot exceed 100%'
    
    valid_statuses = ['draft', 'sent', 'paid', 'overdue']
    if 'status' in data and data['status'] not in valid_statuses:
        return f'Status must be one of: {", ".join(valid_statuses)}'
    
    if 'items' not in data:
        return 'items is required'
    if not isinstance(data['items'], list):
        return 'items must be a list'
    if len(data['items']) == 0:
        return 'At least one item is required'
    
    for i, item in enumerate(data['items']):
        error = validate_invoice_item(item, i + 1)
        if error:
            return error
    
    return None

def validate_invoice_item(item: Dict[str, Any], item_number: int = None) -> Optional[str]:
    """Validate individual invoice item data."""
    prefix = f'Item {item_number}: ' if item_number else ''
    
    required_fields = ['description', 'quantity', 'unit_price']
    for field in required_fields:
        if not item.get(field):
            return f'{prefix}{field} is required'
    
    if len(item['description']) > MAX_DESCRIPTION_LENGTH:
        return f'{prefix}Description must be {MAX_DESCRIPTION_LENGTH} characters or less'
    
    error = validate_numeric_field(item['quantity'], f'{prefix}Quantity', 0.01)
    if error:
        return error
    
    error = validate_numeric_field(item['unit_price'], f'{prefix}Unit price', 0)
    if error:
        return error
    
    return None
