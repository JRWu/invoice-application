import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { toast } from 'react-toastify';
import Login from '../Login';
import { useAuth } from '../../../contexts/AuthContext';

const mockLogin = jest.fn();
const mockNavigate = jest.fn();

jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

jest.mock('react-toastify', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
}));

const renderLogin = () => {
  return render(
    <BrowserRouter>
      <Login />
    </BrowserRouter>
  );
};

describe('Login Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLogin.mockClear();
    mockNavigate.mockClear();
    
    useAuth.mockReturnValue({
      login: mockLogin,
      user: null,
      token: null,
      loading: false,
      register: jest.fn(),
      logout: jest.fn(),
      isAuthenticated: false,
    });
  });

  describe('Component Rendering', () => {
    test('renders login form with all required elements', () => {
      renderLogin();
      
      expect(screen.getByText('Welcome Back')).toBeInTheDocument();
      expect(screen.getByText('Sign in to Invoice Application')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your username')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
      expect(screen.getByText("Don't have an account?")).toBeInTheDocument();
      expect(screen.getByText('Create one here')).toBeInTheDocument();
    });

    test('renders input fields with correct attributes', () => {
      renderLogin();
      
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
  });

  describe('Form Input Handling', () => {
    test('updates username field on input change', () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      fireEvent.change(usernameInput, { target: { value: 'testuser@example.com' } });
      
      expect(usernameInput).toHaveValue('testuser@example.com');
    });

    test('updates password field on input change', () => {
      renderLogin();
      
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      
      expect(passwordInput).toHaveValue('password123');
    });

    test('handles multiple input changes correctly', () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      
      fireEvent.change(usernameInput, { target: { value: 'user@test.com' } });
      fireEvent.change(passwordInput, { target: { value: 'mypassword' } });
      
      expect(usernameInput).toHaveValue('user@test.com');
      expect(passwordInput).toHaveValue('mypassword');
    });
  });

  describe('Email Format Validation', () => {
    test('accepts valid email formats in username field', async () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      mockLogin.mockResolvedValueOnce({ success: true });
      
      fireEvent.change(usernameInput, { target: { value: 'user@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'user@example.com',
          password: 'password123'
        });
      });
    });

    test('accepts complex email formats in username field', async () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      mockLogin.mockResolvedValueOnce({ success: true });
      
      fireEvent.change(usernameInput, { target: { value: 'test.email+tag@domain.co.uk' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'test.email+tag@domain.co.uk',
          password: 'password123'
        });
      });
    });

    test('handles malformed email formats gracefully', async () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      const malformedEmails = [
        'invalid-email',
        '@domain.com',
        'user@',
        'user..double.dot@example.com',
        'user@domain',
        'user name@example.com',
        'user@domain..com',
        ''
      ];
      
      for (const email of malformedEmails) {
        mockLogin.mockResolvedValueOnce({ 
          success: false, 
          error: 'Invalid email format' 
        });
        
        fireEvent.change(usernameInput, { target: { value: email } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
        
        await waitFor(() => {
          expect(mockLogin).toHaveBeenCalledWith({
            username: email,
            password: 'password123'
          });
        });
        
        await waitFor(() => {
          expect(toast.error).toHaveBeenCalledWith('Invalid email format');
        });
        
        jest.clearAllMocks();
      }
    });

    test('accepts non-email usernames (backward compatibility)', async () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      mockLogin.mockResolvedValueOnce({ success: true });
      
      fireEvent.change(usernameInput, { target: { value: 'regularusername' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'regularusername',
          password: 'password123'
        });
      });
    });
  });

  describe('Form Submission', () => {
    test('submits form with empty fields (backend validation)', async () => {
      renderLogin();
      
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      mockLogin.mockResolvedValueOnce({ success: false, error: 'Username and password are required' });
      
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: '',
          password: ''
        });
      });
    });

    test('submits form with empty username (backend validation)', async () => {
      renderLogin();
      
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      mockLogin.mockResolvedValueOnce({ success: false, error: 'Username is required' });
      
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: '',
          password: 'password123'
        });
      });
    });

    test('submits form with empty password (backend validation)', async () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      mockLogin.mockResolvedValueOnce({ success: false, error: 'Password is required' });
      
      fireEvent.change(usernameInput, { target: { value: 'user@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'user@example.com',
          password: ''
        });
      });
    });

    test('submits form with valid credentials', async () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      mockLogin.mockResolvedValueOnce({ success: true });
      
      fireEvent.change(usernameInput, { target: { value: 'user@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'user@example.com',
          password: 'password123'
        });
      });
    });
  });

  describe('Loading States', () => {
    test('shows loading state during form submission', async () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      mockLogin.mockImplementation(() => new Promise(resolve => 
        setTimeout(() => resolve({ success: true }), 100)
      ));
      
      fireEvent.change(usernameInput, { target: { value: 'user@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      expect(submitButton).toBeDisabled();
      expect(screen.getByRole('button')).toHaveClass('btn btn-primary');
      
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });

    test('disables form during loading', async () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      mockLogin.mockImplementation(() => new Promise(resolve => 
        setTimeout(() => resolve({ success: true }), 100)
      ));
      
      fireEvent.change(usernameInput, { target: { value: 'user@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      expect(submitButton).toBeDisabled();
      
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });
  });

  describe('Authentication Flow', () => {
    test('handles successful login', async () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      mockLogin.mockResolvedValueOnce({ success: true });
      
      fireEvent.change(usernameInput, { target: { value: 'user@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Login successful!');
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });

    test('handles login failure with error message', async () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      mockLogin.mockResolvedValueOnce({ 
        success: false, 
        error: 'Invalid credentials' 
      });
      
      fireEvent.change(usernameInput, { target: { value: 'user@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Invalid credentials');
        expect(mockNavigate).not.toHaveBeenCalled();
      });
    });

    test('handles login exception', async () => {
      renderLogin();
      
      const usernameInput = screen.getByPlaceholderText('Enter your username');
      const passwordInput = screen.getByPlaceholderText('Enter your password');
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      
      mockLogin.mockRejectedValueOnce(new Error('Network error'));
      
      fireEvent.change(usernameInput, { target: { value: 'user@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('An error occurred during login');
        expect(mockNavigate).not.toHaveBeenCalled();
      });
    });
  });

  describe('Navigation Links', () => {
    test('renders registration link', () => {
      renderLogin();
      
      const registerLink = screen.getByText('Create one here');
      expect(registerLink).toBeInTheDocument();
      expect(registerLink.closest('a')).toHaveAttribute('href', '/register');
    });
  });

  describe('Accessibility', () => {
    test('has proper form labels', () => {
      renderLogin();
      
      expect(screen.getByText('Username')).toBeInTheDocument();
      expect(screen.getByText('Password')).toBeInTheDocument();
    });

    test('has proper button roles', () => {
      renderLogin();
      
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    test('has proper form structure', () => {
      renderLogin();
      
      const form = document.querySelector('form');
      expect(form).toBeInTheDocument();
      expect(form.tagName.toLowerCase()).toBe('form');
    });
  });
});
