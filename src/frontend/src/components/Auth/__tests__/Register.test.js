import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders, mockApiResponses, createTestUser } from '../../../test-utils';
import Register from '../Register';
import { authAPI } from '../../../utils/api';

jest.mock('../../../utils/api');

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
}));

describe('Register Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
  });

  it('should render registration form with all required fields', () => {
    renderWithProviders(<Register />);

    expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/company name/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByText(/already have an account/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument();
  });

  it('should handle successful registration', async () => {
    const testUser = createTestUser({
      username: 'newuser',
      email: 'new@example.com',
      company_name: 'New Company',
    });
    
    authAPI.register.mockResolvedValue(mockApiResponses.auth.registerSuccess(testUser));

    renderWithProviders(<Register />);

    await userEvent.type(screen.getByLabelText(/username/i), 'newuser');
    await userEvent.type(screen.getByLabelText(/email/i), 'new@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'password123');
    await userEvent.type(screen.getByLabelText(/company name/i), 'New Company');
    
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(authAPI.register).toHaveBeenCalledWith({
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123',
        company_name: 'New Company',
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should handle registration without company name', async () => {
    const testUser = createTestUser({
      username: 'newuser',
      email: 'new@example.com',
    });
    
    authAPI.register.mockResolvedValue(mockApiResponses.auth.registerSuccess(testUser));

    renderWithProviders(<Register />);

    await userEvent.type(screen.getByLabelText(/username/i), 'newuser');
    await userEvent.type(screen.getByLabelText(/email/i), 'new@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'password123');
    
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(authAPI.register).toHaveBeenCalledWith({
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123',
        company_name: '',
      });
    });
  });

  it('should display error message on registration failure', async () => {
    authAPI.register.mockRejectedValue(mockApiResponses.auth.registerError('Username already exists'));

    renderWithProviders(<Register />);

    await userEvent.type(screen.getByLabelText(/username/i), 'existinguser');
    await userEvent.type(screen.getByLabelText(/email/i), 'existing@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(authAPI.register).toHaveBeenCalledWith({
        username: 'existinguser',
        email: 'existing@example.com',
        password: 'password123',
        company_name: '',
      });
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should handle network error during registration', async () => {
    authAPI.register.mockRejectedValue(new Error('Network error'));

    renderWithProviders(<Register />);

    await userEvent.type(screen.getByLabelText(/username/i), 'newuser');
    await userEvent.type(screen.getByLabelText(/email/i), 'new@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(authAPI.register).toHaveBeenCalledWith({
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123',
        company_name: '',
      });
    });
  });

  it('should validate all required fields', async () => {
    renderWithProviders(<Register />);

    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(authAPI.register).not.toHaveBeenCalled();
  });

  it('should handle email input validation', async () => {
    renderWithProviders(<Register />);

    const emailInput = screen.getByLabelText(/email/i);
    await userEvent.type(emailInput, 'test@example.com');
    expect(emailInput).toHaveValue('test@example.com');
    expect(emailInput.validity.valid).toBe(true);

    await userEvent.clear(emailInput);
    await userEvent.type(emailInput, 'invalid-email');
    expect(emailInput).toHaveValue('invalid-email');
  });

  it('should validate password strength', async () => {
    renderWithProviders(<Register />);

    await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), '123');
    await userEvent.type(screen.getByLabelText(/confirm password/i), '123');
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(authAPI.register).not.toHaveBeenCalled();
    });
  });

  it('should maintain form state during API call', async () => {
    let resolveRegister;
    const registerPromise = new Promise((resolve) => {
      resolveRegister = resolve;
    });
    
    authAPI.register.mockReturnValue(registerPromise);

    renderWithProviders(<Register />);

    const usernameInput = screen.getByLabelText(/username/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/^password$/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

    await userEvent.type(usernameInput, 'testuser');
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password123');
    await userEvent.type(confirmPasswordInput, 'password123');
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(usernameInput).toHaveValue('testuser');
    expect(emailInput).toHaveValue('test@example.com');
    expect(passwordInput).toHaveValue('password123');
    expect(confirmPasswordInput).toHaveValue('password123');

    resolveRegister(mockApiResponses.auth.registerSuccess());

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should disable submit button while loading', async () => {
    
    let resolveRegister;
    const registerPromise = new Promise((resolve) => {
      resolveRegister = resolve;
    });
    
    authAPI.register.mockReturnValue(registerPromise);

    renderWithProviders(<Register />);

    await userEvent.type(screen.getByLabelText(/username/i), 'newuser');
    await userEvent.type(screen.getByLabelText(/email/i), 'new@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'password123');
    
    const submitButton = screen.getByRole('button', { name: /create account/i });
    await userEvent.click(submitButton);

    expect(submitButton).toBeDisabled();

    resolveRegister(mockApiResponses.auth.registerSuccess());

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });
  });

  it('should handle form submission with Enter key', async () => {
    const testUser = createTestUser();
    
    authAPI.register.mockResolvedValue(mockApiResponses.auth.registerSuccess(testUser));

    renderWithProviders(<Register />);

    await userEvent.type(screen.getByLabelText(/username/i), 'newuser');
    await userEvent.type(screen.getByLabelText(/email/i), 'new@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'password123');
    
    await userEvent.keyboard('{Enter}');

    await waitFor(() => {
      expect(authAPI.register).toHaveBeenCalledWith({
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123',
        company_name: '',
      });
    });
  });

  it('should render form even if already authenticated', () => {
    const authenticatedUser = createTestUser();
    
    renderWithProviders(<Register />, {
      initialAuthState: {
        token: 'existing-token',
        user: authenticatedUser,
      },
    });

    expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
  });

  it('should handle special characters in form fields', async () => {
    const testUser = createTestUser({
      username: 'user@domain.com',
      email: 'user@domain.com',
      company_name: 'Company & Co.',
    });
    
    authAPI.register.mockResolvedValue(mockApiResponses.auth.registerSuccess(testUser));

    renderWithProviders(<Register />);

    await userEvent.type(screen.getByLabelText(/username/i), 'user@domain.com');
    await userEvent.type(screen.getByLabelText(/email/i), 'user@domain.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'pass!@#$%^&*()');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'pass!@#$%^&*()');
    await userEvent.type(screen.getByLabelText(/company name/i), 'Company & Co.');
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(authAPI.register).toHaveBeenCalledWith({
        username: 'user@domain.com',
        email: 'user@domain.com',
        password: 'pass!@#$%^&*()',
        company_name: 'Company & Co.',
      });
    });
  });

  it('should handle email input correctly', async () => {
    renderWithProviders(<Register />);

    const emailInput = screen.getByLabelText(/email/i);
    
    await userEvent.type(emailInput, 'test@example.com');
    expect(emailInput).toHaveValue('test@example.com');

    await userEvent.clear(emailInput);
    await userEvent.type(emailInput, 'another@domain.org');
    expect(emailInput).toHaveValue('another@domain.org');
  });

  it('should handle password confirmation mismatch', async () => {
    renderWithProviders(<Register />);

    await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'different123');
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(authAPI.register).not.toHaveBeenCalled();
  });

  it('should handle different error types from server', async () => {
    authAPI.register.mockRejectedValue(mockApiResponses.auth.registerError('Username already exists'));

    renderWithProviders(<Register />);

    await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(authAPI.register).toHaveBeenCalledWith({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        company_name: '',
      });
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
