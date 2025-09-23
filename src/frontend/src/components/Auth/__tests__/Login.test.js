import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders, mockApiResponses, createTestUser } from '../../../test-utils';
import Login from '../Login';
import { authAPI } from '../../../utils/api';

jest.mock('../../../utils/api');

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
}));

describe('Login Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
  });

  it('should render login form with all required fields', () => {
    renderWithProviders(<Login />);

    expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByText(/don't have an account/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /create one here/i })).toBeInTheDocument();
  });

  it('should handle successful login', async () => {
    const testUser = createTestUser({ username: 'testuser' });
    
    authAPI.login.mockResolvedValue(mockApiResponses.auth.loginSuccess(testUser));

    renderWithProviders(<Login />);

    await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(authAPI.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should display error message on login failure', async () => {
    authAPI.login.mockRejectedValue(mockApiResponses.auth.loginError('Invalid credentials'));

    renderWithProviders(<Login />);

    await userEvent.type(screen.getByLabelText(/username/i), 'wronguser');
    await userEvent.type(screen.getByLabelText(/password/i), 'wrongpassword');
    
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(authAPI.login).toHaveBeenCalledWith({
        username: 'wronguser',
        password: 'wrongpassword',
      });
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should handle network error during login', async () => {
    authAPI.login.mockRejectedValue(new Error('Network error'));

    renderWithProviders(<Login />);

    await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(authAPI.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });
  });

  it('should handle empty form submission', async () => {
    renderWithProviders(<Login />);

    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(authAPI.login).toHaveBeenCalledWith({
        username: '',
        password: '',
      });
    });
  });

  it('should handle partial form submission', async () => {
    renderWithProviders(<Login />);

    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(authAPI.login).toHaveBeenCalledWith({
        username: '',
        password: 'password123',
      });
    });
  });

  it('should handle username only submission', async () => {
    renderWithProviders(<Login />);

    await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(authAPI.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: '',
      });
    });
  });

  it('should handle form input changes', async () => {
    renderWithProviders(<Login />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await userEvent.type(usernameInput, 'testuser');
    await userEvent.type(passwordInput, 'password123');

    expect(usernameInput).toHaveValue('testuser');
    expect(passwordInput).toHaveValue('password123');

    await userEvent.clear(usernameInput);
    await userEvent.type(usernameInput, 'newuser');

    expect(usernameInput).toHaveValue('newuser');
  });

  it('should disable submit button while loading', async () => {
    let resolveLogin;
    const loginPromise = new Promise((resolve) => {
      resolveLogin = resolve;
    });
    
    authAPI.login.mockReturnValue(loginPromise);

    renderWithProviders(<Login />);

    await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await userEvent.click(submitButton);

    expect(submitButton).toBeDisabled();

    resolveLogin(mockApiResponses.auth.loginSuccess());

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });
  });

  it('should handle form submission with Enter key', async () => {
    const testUser = createTestUser();
    
    authAPI.login.mockResolvedValue(mockApiResponses.auth.loginSuccess(testUser));

    renderWithProviders(<Login />);

    await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    
    await userEvent.keyboard('{Enter}');

    await waitFor(() => {
      expect(authAPI.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });
  });

  it('should render form even if already authenticated', () => {
    const authenticatedUser = createTestUser();
    
    renderWithProviders(<Login />, {
      initialAuthState: {
        token: 'existing-token',
        user: authenticatedUser,
      },
    });

    expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
  });

  it('should handle special characters in credentials', async () => {
    const testUser = createTestUser({ username: 'user@domain.com' });
    
    authAPI.login.mockResolvedValue(mockApiResponses.auth.loginSuccess(testUser));

    renderWithProviders(<Login />);

    const specialUsername = 'user@domain.com';
    const specialPassword = 'pass!@#$%^&*()';

    await userEvent.type(screen.getByLabelText(/username/i), specialUsername);
    await userEvent.type(screen.getByLabelText(/password/i), specialPassword);
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(authAPI.login).toHaveBeenCalledWith({
        username: specialUsername,
        password: specialPassword,
      });
    });
  });

  it('should handle very long credentials', async () => {
    authAPI.login.mockResolvedValue(mockApiResponses.auth.loginSuccess());

    renderWithProviders(<Login />);

    const longUsername = 'a'.repeat(100);
    const longPassword = 'p'.repeat(200);

    await userEvent.type(screen.getByLabelText(/username/i), longUsername);
    await userEvent.type(screen.getByLabelText(/password/i), longPassword);
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(authAPI.login).toHaveBeenCalledWith({
        username: longUsername,
        password: longPassword,
      });
    });
  });

  it('should maintain form state during API call', async () => {
    let resolveLogin;
    const loginPromise = new Promise((resolve) => {
      resolveLogin = resolve;
    });
    
    authAPI.login.mockReturnValue(loginPromise);

    renderWithProviders(<Login />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await userEvent.type(usernameInput, 'testuser');
    await userEvent.type(passwordInput, 'password123');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(usernameInput).toHaveValue('testuser');
    expect(passwordInput).toHaveValue('password123');

    resolveLogin(mockApiResponses.auth.loginSuccess());

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });
});
