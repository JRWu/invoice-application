import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { toast } from 'react-toastify';
import Login from './Login';
import { useAuth } from '../../contexts/AuthContext';

jest.mock('axios');

jest.mock('../../utils/api', () => ({
  authAPI: {
    login: jest.fn(),
    register: jest.fn(),
    getProfile: jest.fn(),
  },
}));

jest.mock('react-toastify', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
}));

const renderLoginWithAuth = (mockAuthValue = {}) => {
  const defaultAuthValue = {
    user: null,
    token: null,
    loading: false,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    isAuthenticated: false,
    ...mockAuthValue,
  };

  useAuth.mockReturnValue(defaultAuthValue);

  return render(
    <BrowserRouter>
      <Login />
    </BrowserRouter>
  );
};

describe('Login Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
    toast.success.mockClear();
    toast.error.mockClear();
  });

  describe('Form Rendering', () => {
    test('renders login form with all required elements', () => {
      renderLoginWithAuth();

      expect(screen.getByText('Welcome Back')).toBeInTheDocument();
      expect(screen.getByText('Sign in to your invoice account')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your username')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
      expect(screen.getByText(/don't have an account/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /create one here/i })).toBeInTheDocument();
    });

    test('renders form inputs with correct attributes', () => {
      renderLoginWithAuth();

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');

      expect(usernameInput).toHaveAttribute('type', 'text');
      expect(usernameInput).toHaveAttribute('name', 'username');
      expect(usernameInput).toHaveAttribute('placeholder', 'Enter your username');
      expect(usernameInput).toBeRequired();

      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('name', 'password');
      expect(passwordInput).toHaveAttribute('placeholder', 'Enter your password');
      expect(passwordInput).toBeRequired();
    });

    test('renders registration link with correct href', () => {
      renderLoginWithAuth();

      const registerLink = screen.getByRole('link', { name: /create one here/i });
      expect(registerLink).toHaveAttribute('href', '/register');
    });
  });

  describe('Form Interactions', () => {
    test('updates username input value on change', () => {
      renderLoginWithAuth();

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      fireEvent.change(usernameInput, { target: { value: 'testuser' } });

      expect(usernameInput.value).toBe('testuser');
    });

    test('updates password input value on change', () => {
      renderLoginWithAuth();

      const passwordInput = screen.getByPlaceholderText('Enter your password');
      fireEvent.change(passwordInput, { target: { value: 'testpassword' } });

      expect(passwordInput.value).toBe('testpassword');
    });

    test('updates both input values independently', () => {
      renderLoginWithAuth();

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'testpassword' } });

      expect(usernameInput.value).toBe('testuser');
      expect(passwordInput.value).toBe('testpassword');
    });
  });

  describe('Form Submission', () => {
    test('calls login function with correct credentials on form submission', async () => {
      const mockLogin = jest.fn().mockResolvedValue({ success: true });
      renderLoginWithAuth({ login: mockLogin });

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'testpassword' } });
      fireEvent.click(submitButton);

      expect(mockLogin).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'testpassword',
      });
    });

    test('prevents default form submission behavior', async () => {
      const mockLogin = jest.fn().mockResolvedValue({ success: true });
      renderLoginWithAuth({ login: mockLogin });

      const form = screen.getByRole('button', { name: /sign in/i }).closest('form');
      const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
      const preventDefaultSpy = jest.spyOn(submitEvent, 'preventDefault');

      fireEvent(form, submitEvent);

      expect(preventDefaultSpy).toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    test('shows loading spinner and disables button during login', async () => {
      const mockLogin = jest.fn(() => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100)));
      renderLoginWithAuth({ login: mockLogin });

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'testpassword' } });
      fireEvent.click(submitButton);

      expect(submitButton).toBeDisabled();
      expect(screen.getByRole('button')).toContainHTML('<div class="spinner"');

      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });

    test('restores button state after login completes', async () => {
      const mockLogin = jest.fn().mockResolvedValue({ success: true });
      renderLoginWithAuth({ login: mockLogin });

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'testpassword' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
        expect(screen.getByText('Sign In')).toBeInTheDocument();
      });
    });
  });

  describe('Successful Login', () => {
    test('shows success toast and navigates to dashboard on successful login', async () => {
      const mockLogin = jest.fn().mockResolvedValue({ success: true });
      renderLoginWithAuth({ login: mockLogin });

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'testpassword' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Login successful!');
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });
  });

  describe('Login Errors', () => {
    test('shows error toast when login fails with error message', async () => {
      const mockLogin = jest.fn().mockResolvedValue({ 
        success: false, 
        error: 'Invalid credentials' 
      });
      renderLoginWithAuth({ login: mockLogin });

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      fireEvent.change(usernameInput, { target: { value: 'wronguser' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Invalid credentials');
        expect(mockNavigate).not.toHaveBeenCalled();
      });
    });

    test('shows generic error toast when login throws exception', async () => {
      const mockLogin = jest.fn().mockRejectedValue(new Error('Network error'));
      renderLoginWithAuth({ login: mockLogin });

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'testpassword' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('An error occurred during login');
        expect(mockNavigate).not.toHaveBeenCalled();
      });
    });

    test('restores button state after login error', async () => {
      const mockLogin = jest.fn().mockResolvedValue({ 
        success: false, 
        error: 'Invalid credentials' 
      });
      renderLoginWithAuth({ login: mockLogin });

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      fireEvent.change(usernameInput, { target: { value: 'wronguser' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
        expect(screen.getByText('Sign In')).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation', () => {
    test('form requires username field', () => {
      renderLoginWithAuth();

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      expect(usernameInput).toBeRequired();
    });

    test('form requires password field', () => {
      renderLoginWithAuth();

      const passwordInput = screen.getByPlaceholderText('Enter your password');
      expect(passwordInput).toBeRequired();
    });

    test('can submit form with valid inputs', async () => {
      const mockLogin = jest.fn().mockResolvedValue({ success: true });
      renderLoginWithAuth({ login: mockLogin });

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      fireEvent.change(usernameInput, { target: { value: 'validuser' } });
      fireEvent.change(passwordInput, { target: { value: 'validpassword' } });
      fireEvent.click(submitButton);

      expect(mockLogin).toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    test('handles multiple rapid form submissions', async () => {
      const mockLogin = jest.fn(() => new Promise(resolve => setTimeout(() => resolve({ success: true }), 50)));
      renderLoginWithAuth({ login: mockLogin });

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'testpassword' } });
      
      fireEvent.click(submitButton);
      fireEvent.click(submitButton);
      fireEvent.click(submitButton);

      expect(mockLogin).toHaveBeenCalledTimes(1);
    });

    test('handles empty form submission', async () => {
      const mockLogin = jest.fn().mockResolvedValue({ success: true });
      renderLoginWithAuth({ login: mockLogin });

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      fireEvent.click(submitButton);

      expect(mockLogin).toHaveBeenCalledWith({
        username: '',
        password: '',
      });
    });

    test('clears form state between renders', () => {
      const { unmount } = renderLoginWithAuth();
      unmount();

      renderLoginWithAuth();

      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');

      expect(usernameInput.value).toBe('');
      expect(passwordInput.value).toBe('');
    });
  });
});
