# Frontend Testing Documentation

This document outlines the testing setup and practices for the Invoice Application frontend.

## Testing Framework

The frontend uses the following testing tools:
- **Jest**: JavaScript testing framework
- **React Testing Library**: Testing utilities for React components
- **@testing-library/user-event**: User interaction simulation
- **@testing-library/jest-dom**: Custom Jest matchers for DOM elements

## Test Structure

```
src/
├── test-utils.js                           # Custom testing utilities
├── contexts/
│   └── __tests__/
│       └── AuthContext.test.js            # Authentication context tests
├── utils/
│   └── __tests__/
│       └── api.test.js                     # API utilities tests
└── components/
    └── Auth/
        └── __tests__/
            ├── Login.test.js               # Login component tests
            └── Register.test.js            # Register component tests
```

## Running Tests

### Run All Tests
```bash
cd src/frontend
npm test
```

### Run Tests in Watch Mode
```bash
cd src/frontend
npm test -- --watch
```

### Run Tests with Coverage
```bash
cd src/frontend
npm test -- --coverage
```

### Run Specific Test File
```bash
cd src/frontend
npm test AuthContext.test.js
npm test Login.test.js
```

## Test Categories

### Authentication Context Tests (`AuthContext.test.js`)
- AuthProvider initialization with and without localStorage data
- Login function success and failure scenarios
- Register function success and failure scenarios
- Logout function and state cleanup
- Token persistence and loading states
- Error handling for corrupted localStorage data
- useAuth hook validation

### API Utilities Tests (`api.test.js`)
- Axios instance configuration
- Request interceptor token attachment
- Response interceptor 401 handling
- Auth API methods (login, register, getProfile)
- Invoices API methods
- Reports API methods
- Error handling and network failures

### Login Component Tests (`Login.test.js`)
- Form rendering and field validation
- Successful login flow
- Error handling and display
- Loading states and button disabling
- Form validation (required fields, special characters)
- Navigation and redirection
- Integration with AuthContext

### Register Component Tests (`Register.test.js`)
- Form rendering with all fields
- Successful registration flow
- Email validation and password strength
- Error handling and display
- Loading states and form validation
- Integration with AuthContext
- Password strength indicator

## Test Utilities

The `test-utils.js` file provides helpful utilities:

### Custom Render Function
```javascript
import { renderWithProviders } from '../test-utils';

// Render component with AuthProvider and Router
renderWithProviders(<MyComponent />, {
  initialAuthState: { token: 'mock-token', user: mockUser }
});
```

### Mock API Responses
```javascript
import { mockApiResponses } from '../test-utils';

// Mock successful login
authAPI.login.mockResolvedValue(mockApiResponses.auth.loginSuccess());

// Mock login error
authAPI.login.mockRejectedValue(mockApiResponses.auth.loginError('Invalid credentials'));
```

### Test Data Factories
```javascript
import { createTestUser, createTestInvoice } from '../test-utils';

const user = createTestUser({ username: 'testuser' });
const invoice = createTestInvoice({ customer_name: 'Test Customer' });
```

### Authentication Helpers
```javascript
import { setupAuthenticatedTest, expectAuthenticatedState } from '../test-utils';

// Set up authenticated user state
const { user, token } = setupAuthenticatedTest();

// Assert authentication state
expectAuthenticatedState(container);
```

## Best Practices

### Test Organization
- Group related tests using `describe` blocks
- Use descriptive test names that explain the scenario
- Follow the AAA pattern: Arrange, Act, Assert
- Use `beforeEach` and `afterEach` for setup and cleanup

### Mocking
- Mock external dependencies (API calls, localStorage)
- Use `jest.mock()` for module mocking
- Clear mocks between tests with `jest.clearAllMocks()`

### User Interactions
- Use `userEvent` for realistic user interactions
- Wait for async operations with `waitFor`
- Test both success and failure scenarios

### Assertions
- Use semantic queries (`getByRole`, `getByLabelText`)
- Test accessibility with ARIA attributes
- Verify error messages and loading states
- Check form validation and submission

### Example Test Structure
```javascript
describe('ComponentName', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('rendering', () => {
    it('should render all required elements', () => {
      // Test rendering
    });
  });

  describe('user interactions', () => {
    it('should handle form submission', async () => {
      // Test interactions
    });
  });

  describe('error handling', () => {
    it('should display error messages', async () => {
      // Test error scenarios
    });
  });
});
```

## Common Testing Patterns

### Testing Form Validation
```javascript
it('should validate required fields', async () => {
  const user = userEvent.setup();
  renderWithProviders(<LoginForm />);

  await user.click(screen.getByRole('button', { name: /login/i }));

  expect(screen.getByText(/username is required/i)).toBeInTheDocument();
  expect(screen.getByText(/password is required/i)).toBeInTheDocument();
});
```

### Testing API Integration
```javascript
it('should handle successful login', async () => {
  const user = userEvent.setup();
  authAPI.login.mockResolvedValue(mockApiResponses.auth.loginSuccess());

  renderWithProviders(<Login />);

  await user.type(screen.getByLabelText(/username/i), 'testuser');
  await user.type(screen.getByLabelText(/password/i), 'password123');
  await user.click(screen.getByRole('button', { name: /login/i }));

  await waitFor(() => {
    expect(authAPI.login).toHaveBeenCalledWith({
      username: 'testuser',
      password: 'password123',
    });
  });
});
```

### Testing Loading States
```javascript
it('should show loading state during API call', async () => {
  const user = userEvent.setup();
  
  let resolveLogin;
  const loginPromise = new Promise((resolve) => {
    resolveLogin = resolve;
  });
  
  authAPI.login.mockReturnValue(loginPromise);

  renderWithProviders(<Login />);

  await user.click(screen.getByRole('button', { name: /login/i }));

  expect(screen.getByText(/logging in/i)).toBeInTheDocument();
  expect(screen.getByRole('button')).toBeDisabled();

  resolveLogin(mockApiResponses.auth.loginSuccess());
});
```

## Debugging Tests

### Debug Rendered Output
```javascript
import { screen } from '@testing-library/react';

// Print the current DOM
screen.debug();

// Print specific element
screen.debug(screen.getByRole('button'));
```

### Query Debugging
```javascript
// Find all available roles
screen.logTestingPlaygroundURL();

// Get suggestions for queries
screen.getByRole('button', { name: /submit/i });
```

### Async Debugging
```javascript
// Wait for element to appear
await waitFor(() => {
  expect(screen.getByText(/success/i)).toBeInTheDocument();
});

// Wait with custom timeout
await waitFor(() => {
  expect(mockFunction).toHaveBeenCalled();
}, { timeout: 3000 });
```

## Performance Considerations

- Use `screen.getBy*` queries for elements that should exist
- Use `screen.queryBy*` queries for elements that might not exist
- Use `screen.findBy*` queries for async elements
- Avoid using `container.querySelector` when possible
- Mock heavy dependencies to keep tests fast
- Use `act()` wrapper for state updates outside of user events

## Integration with Backend Tests

The frontend tests complement the backend authentication tests by:
- Testing the complete user experience flow
- Validating API integration and error handling
- Ensuring proper state management and persistence
- Verifying accessibility and user interaction patterns

Together, the frontend and backend tests provide comprehensive coverage of the authentication system from API endpoints to user interface.
