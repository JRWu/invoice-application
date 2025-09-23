import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

jest.mock('../../utils/api', () => ({
  authAPI: {
    login: jest.fn(),
    register: jest.fn(),
    getProfile: jest.fn(),
  },
}));

import { AuthProvider, useAuth } from '../AuthContext';
import { authAPI } from '../../utils/api';

const TestComponent = () => {
  const { user, token, loading, login, register, logout, isAuthenticated } = useAuth();
  
  return (
    <div>
      <div data-testid="user">{user ? JSON.stringify(user) : 'null'}</div>
      <div data-testid="token">{token || 'null'}</div>
      <div data-testid="loading">{loading.toString()}</div>
      <div data-testid="authenticated">{isAuthenticated.toString()}</div>
      <button 
        onClick={() => login({ username: 'testuser', password: 'testpass' })}
        data-testid="login-button"
      >
        Login
      </button>
      <button 
        onClick={() => register({ 
          username: 'newuser', 
          email: 'new@example.com', 
          password: 'newpass',
          company_name: 'New Company'
        })}
        data-testid="register-button"
      >
        Register
      </button>
      <button onClick={logout} data-testid="logout-button">
        Logout
      </button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    localStorageMock.clear.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('AuthProvider initialization', () => {
    it('should initialize with no user when localStorage is empty', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
      });

      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(screen.getByTestId('token')).toHaveTextContent('null');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    });

    it('should initialize with user data from localStorage', async () => {
      const mockToken = 'mock-jwt-token';
      const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' };
      
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'token') return mockToken;
        if (key === 'user') return JSON.stringify(mockUser);
        return null;
      });

      await act(async () => {
        render(
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
      });

      expect(screen.getByTestId('user')).toHaveTextContent(JSON.stringify(mockUser));
      expect(screen.getByTestId('token')).toHaveTextContent(mockToken);
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    });

    it('should handle corrupted user data in localStorage', async () => {
      const mockToken = 'mock-jwt-token';
      
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'token') return mockToken;
        if (key === 'user') return 'invalid-json';
        return null;
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
      });

      expect(screen.getByTestId('user')).toHaveTextContent('null');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    });
  });

  describe('login function', () => {
    it('should handle successful login', async () => {
      const user = userEvent;
      const mockToken = 'mock-jwt-token';
      const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' };
      
      authAPI.login.mockResolvedValue({
        data: {
          access_token: mockToken,
          user: mockUser,
        },
      });

      await act(async () => {
        render(
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
      });

      await act(async () => {
        await user.click(screen.getByTestId('login-button'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent(JSON.stringify(mockUser));
        expect(screen.getByTestId('token')).toHaveTextContent(mockToken);
        expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', mockToken);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockUser));
      expect(authAPI.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'testpass',
      });
    });

    it('should handle login failure', async () => {
      const user = userEvent;
      const mockError = {
        response: {
          data: {
            error: 'Invalid credentials',
          },
        },
      };
      
      authAPI.login.mockRejectedValue(mockError);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
      });

      await user.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('null');
        expect(screen.getByTestId('token')).toHaveTextContent('null');
        expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      });

      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });

    it('should handle network error during login', async () => {
      const user = userEvent;
      
      authAPI.login.mockRejectedValue(new Error('Network error'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
      });

      await user.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('null');
        expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      });
    });
  });

  describe('register function', () => {
    it('should handle successful registration', async () => {
      const user = userEvent;
      const mockToken = 'mock-jwt-token';
      const mockUser = { id: 1, username: 'newuser', email: 'new@example.com' };
      
      authAPI.register.mockResolvedValue({
        data: {
          access_token: mockToken,
          user: mockUser,
        },
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
      });

      await user.click(screen.getByTestId('register-button'));

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent(JSON.stringify(mockUser));
        expect(screen.getByTestId('token')).toHaveTextContent(mockToken);
        expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', mockToken);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockUser));
      expect(authAPI.register).toHaveBeenCalledWith({
        username: 'newuser',
        email: 'new@example.com',
        password: 'newpass',
        company_name: 'New Company',
      });
    });

    it('should handle registration failure', async () => {
      const user = userEvent;
      const mockError = {
        response: {
          data: {
            error: 'Username already exists',
          },
        },
      };
      
      authAPI.register.mockRejectedValue(mockError);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
      });

      await user.click(screen.getByTestId('register-button'));

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('null');
        expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      });

      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });
  });

  describe('logout function', () => {
    it('should clear user data and localStorage on logout', async () => {
      const user = userEvent;
      const mockToken = 'mock-jwt-token';
      const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' };
      
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'token') return mockToken;
        if (key === 'user') return JSON.stringify(mockUser);
        return null;
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
      });

      await user.click(screen.getByTestId('logout-button'));

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('null');
        expect(screen.getByTestId('token')).toHaveTextContent('null');
        expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user');
    });
  });

  describe('useAuth hook', () => {
    it('should throw error when used outside AuthProvider', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      expect(() => {
        render(<TestComponent />);
      }).toThrow('useAuth must be used within an AuthProvider');
      
      consoleSpy.mockRestore();
    });
  });

  describe('isAuthenticated computed property', () => {
    it('should return true when token exists', async () => {
      const mockToken = 'mock-jwt-token';
      
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'token') return mockToken;
        return null;
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
      });
    });

    it('should return false when token is null', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      });
    });

    it('should return false when token is empty string', async () => {
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'token') return '';
        return null;
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      });
    });
  });

  describe('loading state', () => {
    it('should start with loading true and set to false after initialization', async () => {
      let initialLoadingState;
      
      const TestComponentWithCapture = () => {
        const { loading } = useAuth();
        if (initialLoadingState === undefined) {
          initialLoadingState = loading;
        }
        return <div data-testid="loading">{loading.toString()}</div>;
      };

      render(
        <AuthProvider>
          <TestComponentWithCapture />
        </AuthProvider>
      );

      expect(initialLoadingState).toBe(true);

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
      });
    });
  });

  describe('error handling', () => {
    it('should handle missing access_token in login response', async () => {
      const user = userEvent;
      
      authAPI.login.mockResolvedValue({
        data: {
          user: { id: 1, username: 'testuser' },
        },
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
      });

      await user.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      });
    });

    it('should handle missing user data in login response', async () => {
      const user = userEvent;
      
      authAPI.login.mockResolvedValue({
        data: {
          access_token: 'mock-token',
        },
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
      });

      await user.click(screen.getByTestId('login-button'));

      await waitFor(() => {
        expect(screen.getByTestId('token')).toHaveTextContent('mock-token');
        expect(screen.getByTestId('user')).toHaveTextContent('null');
      });
    });
  });
});
