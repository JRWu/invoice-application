import React from 'react';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';

export const createMockLocalStorage = () => {
  const store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
    get store() {
      return { ...store };
    },
  };
};

export const renderWithProviders = (ui, options = {}) => {
  const {
    initialAuthState = {},
    routerProps = {},
    ...renderOptions
  } = options;

  if (!global.localStorage) {
    global.localStorage = createMockLocalStorage();
  }

  if (initialAuthState.token) {
    global.localStorage.setItem('token', initialAuthState.token);
  }
  if (initialAuthState.user) {
    global.localStorage.setItem('user', JSON.stringify(initialAuthState.user));
  }

  const Wrapper = ({ children }) => (
    <BrowserRouter {...routerProps}>
      <AuthProvider>
        {children}
      </AuthProvider>
    </BrowserRouter>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

export const mockApiResponses = {
  auth: {
    loginSuccess: (user = { id: 1, username: 'testuser', email: 'test@example.com' }) => ({
      data: {
        access_token: 'mock-jwt-token',
        user,
        message: 'Login successful',
      },
    }),
    
    loginError: (error = 'Invalid credentials') => ({
      response: {
        data: { error },
        status: 401,
      },
    }),
    
    registerSuccess: (user = { id: 1, username: 'newuser', email: 'new@example.com' }) => ({
      data: {
        access_token: 'mock-jwt-token',
        user,
        message: 'User created successfully',
      },
    }),
    
    registerError: (error = 'Username already exists') => ({
      response: {
        data: { error },
        status: 400,
      },
    }),
    
    profileSuccess: (user = { id: 1, username: 'testuser', email: 'test@example.com' }) => ({
      data: { user },
    }),
    
    profileError: (error = 'Unauthorized') => ({
      response: {
        data: { error },
        status: 401,
      },
    }),
  },
  
  invoices: {
    getAllSuccess: (invoices = []) => ({
      data: { invoices },
    }),
    
    getByIdSuccess: (invoice = { id: 1, invoice_number: 'INV-001' }) => ({
      data: { invoice },
    }),
    
    createSuccess: (invoice = { id: 1, invoice_number: 'INV-001' }) => ({
      data: { invoice, message: 'Invoice created successfully' },
    }),
    
    updateSuccess: (invoice = { id: 1, invoice_number: 'INV-001' }) => ({
      data: { invoice, message: 'Invoice updated successfully' },
    }),
    
    deleteSuccess: () => ({
      data: { message: 'Invoice deleted successfully' },
    }),
    
    error: (error = 'Operation failed', status = 400) => ({
      response: {
        data: { error },
        status,
      },
    }),
  },
  
  reports: {
    getAllSuccess: (reports = []) => ({
      data: { reports },
    }),
    
    generateSuccess: (report = { id: 1, report_type: 'monthly' }) => ({
      data: { report, message: 'Report generated successfully' },
    }),
    
    getDashboardSuccess: (data = { total_revenue: 1000, invoice_count: 5 }) => ({
      data,
    }),
    
    error: (error = 'Operation failed', status = 400) => ({
      response: {
        data: { error },
        status,
      },
    }),
  },
};

export const createTestUser = (overrides = {}) => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  company_name: 'Test Company',
  created_at: '2023-01-01T00:00:00.000Z',
  ...overrides,
});

export const createTestInvoice = (overrides = {}) => ({
  id: 1,
  invoice_number: 'INV-20230101-001',
  customer_name: 'Test Customer',
  customer_email: 'customer@example.com',
  customer_address: '123 Test St',
  issue_date: '2023-01-01',
  due_date: '2023-01-31',
  status: 'draft',
  subtotal: 100.00,
  tax_rate: 10.0,
  tax_amount: 10.00,
  total_amount: 110.00,
  notes: 'Test invoice',
  created_at: '2023-01-01T00:00:00.000Z',
  updated_at: '2023-01-01T00:00:00.000Z',
  items: [],
  ...overrides,
});

export const createTestInvoiceItem = (overrides = {}) => ({
  id: 1,
  description: 'Test Item',
  quantity: 1.0,
  unit_price: 100.00,
  total: 100.00,
  ...overrides,
});

export const createTestReport = (overrides = {}) => ({
  id: 1,
  report_type: 'monthly',
  start_date: '2023-01-01',
  end_date: '2023-01-31',
  data: {
    total_revenue: 1000.00,
    invoice_count: 5,
    paid_invoices: 3,
    pending_invoices: 2,
  },
  created_at: '2023-01-01T00:00:00.000Z',
  ...overrides,
});

export const createAuthenticatedUser = (userOverrides = {}) => {
  const user = createTestUser(userOverrides);
  const token = 'mock-jwt-token';
  
  return { user, token };
};

export const setupAuthenticatedTest = (userOverrides = {}) => {
  const { user, token } = createAuthenticatedUser(userOverrides);
  
  const mockLocalStorage = createMockLocalStorage();
  mockLocalStorage.setItem('token', token);
  mockLocalStorage.setItem('user', JSON.stringify(user));
  global.localStorage = mockLocalStorage;
  
  return { user, token, mockLocalStorage };
};

export const getValidationErrors = (container) => {
  const errorElements = container.querySelectorAll('[role="alert"], .error, .invalid');
  return Array.from(errorElements).map(el => el.textContent);
};

export const fillForm = async (user, formData) => {
  for (const [fieldName, value] of Object.entries(formData)) {
    const field = document.querySelector(`[name="${fieldName}"], #${fieldName}`);
    if (field) {
      await user.clear(field);
      await user.type(field, value);
    }
  }
};

export const waitForAuthState = async (expectedState) => {
  const { waitFor } = await import('@testing-library/react');
  
  await waitFor(() => {
    const authState = {
      isAuthenticated: !!localStorage.getItem('token'),
      user: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null,
      token: localStorage.getItem('token'),
    };
    
    expect(authState).toMatchObject(expectedState);
  });
};

export const createNetworkError = (message = 'Network Error') => {
  const error = new Error(message);
  error.code = 'NETWORK_ERROR';
  return error;
};

export const createTimeoutError = (message = 'Request Timeout') => {
  const error = new Error(message);
  error.code = 'ECONNABORTED';
  return error;
};

export const expectAuthenticatedState = (container) => {
  expect(container.querySelector('[data-testid="authenticated"]')).toHaveTextContent('true');
  expect(container.querySelector('[data-testid="user"]')).not.toHaveTextContent('null');
  expect(container.querySelector('[data-testid="token"]')).not.toHaveTextContent('null');
};

export const expectUnauthenticatedState = (container) => {
  expect(container.querySelector('[data-testid="authenticated"]')).toHaveTextContent('false');
  expect(container.querySelector('[data-testid="user"]')).toHaveTextContent('null');
  expect(container.querySelector('[data-testid="token"]')).toHaveTextContent('null');
};

export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
