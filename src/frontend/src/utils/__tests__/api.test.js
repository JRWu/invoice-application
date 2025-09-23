import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios;

const mockAxiosInstance = {
  interceptors: {
    request: {
      use: jest.fn(),
    },
    response: {
      use: jest.fn(),
    },
  },
  post: jest.fn(),
  get: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
};

mockedAxios.create.mockReturnValue(mockAxiosInstance);

import api, { authAPI, invoicesAPI, reportsAPI } from '../api';

const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

delete window.location;
window.location = { href: '' };

describe('API Configuration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('axios instance creation', () => {
    it('should create axios instance with correct base URL', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: 'http://localhost:5001/api',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    it('should use environment variable for API URL when available', () => {
      const originalEnv = process.env.REACT_APP_API_URL;
      process.env.REACT_APP_API_URL = 'https://api.example.com';

      jest.resetModules();
      require('../api');

      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: 'https://api.example.com',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      process.env.REACT_APP_API_URL = originalEnv;
    });
  });

  describe('request interceptor', () => {
    let mockAxiosInstance;
    let requestInterceptor;

    beforeEach(() => {
      mockAxiosInstance = {
        interceptors: {
          request: {
            use: jest.fn(),
          },
          response: {
            use: jest.fn(),
          },
        },
        post: jest.fn(),
        get: jest.fn(),
        put: jest.fn(),
        delete: jest.fn(),
      };

      mockedAxios.create.mockReturnValue(mockAxiosInstance);

      jest.resetModules();
      require('../api');

      requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
    });

    it('should add Authorization header when token exists', () => {
      const mockToken = 'mock-jwt-token';
      localStorageMock.getItem.mockReturnValue(mockToken);

      const config = { headers: {} };
      const result = requestInterceptor(config);

      expect(localStorageMock.getItem).toHaveBeenCalledWith('token');
      expect(result.headers.Authorization).toBe(`Bearer ${mockToken}`);
    });

    it('should not add Authorization header when token does not exist', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const config = { headers: {} };
      const result = requestInterceptor(config);

      expect(localStorageMock.getItem).toHaveBeenCalledWith('token');
      expect(result.headers.Authorization).toBeUndefined();
    });

    it('should not add Authorization header when token is empty string', () => {
      localStorageMock.getItem.mockReturnValue('');

      const config = { headers: {} };
      const result = requestInterceptor(config);

      expect(result.headers.Authorization).toBeUndefined();
    });

    it('should preserve existing headers', () => {
      const mockToken = 'mock-jwt-token';
      localStorageMock.getItem.mockReturnValue(mockToken);

      const config = {
        headers: {
          'Custom-Header': 'custom-value',
          'Content-Type': 'application/json',
        },
      };
      const result = requestInterceptor(config);

      expect(result.headers['Custom-Header']).toBe('custom-value');
      expect(result.headers['Content-Type']).toBe('application/json');
      expect(result.headers.Authorization).toBe(`Bearer ${mockToken}`);
    });

    it('should handle request interceptor error', () => {
      const requestErrorHandler = mockAxiosInstance.interceptors.request.use.mock.calls[0][1];
      const mockError = new Error('Request error');

      expect(() => requestErrorHandler(mockError)).rejects.toBe(mockError);
    });
  });

  describe('response interceptor', () => {
    let mockAxiosInstance;
    let responseSuccessHandler;
    let responseErrorHandler;

    beforeEach(() => {
      mockAxiosInstance = {
        interceptors: {
          request: {
            use: jest.fn(),
          },
          response: {
            use: jest.fn(),
          },
        },
        post: jest.fn(),
        get: jest.fn(),
        put: jest.fn(),
        delete: jest.fn(),
      };

      mockedAxios.create.mockReturnValue(mockAxiosInstance);

      jest.resetModules();
      require('../api');

      responseSuccessHandler = mockAxiosInstance.interceptors.response.use.mock.calls[0][0];
      responseErrorHandler = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
    });

    it('should pass through successful responses', () => {
      const mockResponse = { data: { message: 'success' }, status: 200 };
      const result = responseSuccessHandler(mockResponse);

      expect(result).toBe(mockResponse);
    });

    it('should handle 401 errors by clearing localStorage and redirecting', () => {
      const mockError = {
        response: {
          status: 401,
          data: { error: 'Unauthorized' },
        },
      };

      expect(() => responseErrorHandler(mockError)).rejects.toBe(mockError);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user');
      expect(window.location.href).toBe('/login');
    });

    it('should not clear localStorage for non-401 errors', () => {
      const mockError = {
        response: {
          status: 500,
          data: { error: 'Server error' },
        },
      };

      expect(() => responseErrorHandler(mockError)).rejects.toBe(mockError);
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
      expect(window.location.href).toBe('');
    });

    it('should handle errors without response object', () => {
      const mockError = new Error('Network error');

      expect(() => responseErrorHandler(mockError)).rejects.toBe(mockError);
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
    });

    it('should handle 401 errors without response.status', () => {
      const mockError = {
        response: {
          data: { error: 'Unauthorized' },
        },
      };

      expect(() => responseErrorHandler(mockError)).rejects.toBe(mockError);
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
    });
  });
});

describe('Auth API', () => {
  let mockAxiosInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockAxiosInstance = {
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
      post: jest.fn(),
      get: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
    };

    mockedAxios.create.mockReturnValue(mockAxiosInstance);

    jest.resetModules();
  });

  describe('authAPI.register', () => {
    it('should call POST /auth/register with user data', async () => {
      const { authAPI } = require('../api');
      const userData = {
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        company_name: 'Test Company',
      };

      const mockResponse = { data: { message: 'User created' } };
      mockAxiosInstance.post.mockResolvedValue(mockResponse);

      const result = await authAPI.register(userData);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/register', userData);
      expect(result).toBe(mockResponse);
    });

    it('should handle registration errors', async () => {
      const { authAPI } = require('../api');
      const userData = { username: 'testuser' };
      const mockError = new Error('Registration failed');

      mockAxiosInstance.post.mockRejectedValue(mockError);

      await expect(authAPI.register(userData)).rejects.toBe(mockError);
    });
  });

  describe('authAPI.login', () => {
    it('should call POST /auth/login with credentials', async () => {
      const { authAPI } = require('../api');
      const credentials = {
        username: 'testuser',
        password: 'password123',
      };

      const mockResponse = { data: { access_token: 'token', user: {} } };
      mockAxiosInstance.post.mockResolvedValue(mockResponse);

      const result = await authAPI.login(credentials);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/login', credentials);
      expect(result).toBe(mockResponse);
    });

    it('should handle login errors', async () => {
      const { authAPI } = require('../api');
      const credentials = { username: 'testuser', password: 'wrong' };
      const mockError = new Error('Invalid credentials');

      mockAxiosInstance.post.mockRejectedValue(mockError);

      await expect(authAPI.login(credentials)).rejects.toBe(mockError);
    });
  });

  describe('authAPI.getProfile', () => {
    it('should call GET /auth/profile', async () => {
      const { authAPI } = require('../api');
      const mockResponse = { data: { user: { id: 1, username: 'testuser' } } };
      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await authAPI.getProfile();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/auth/profile');
      expect(result).toBe(mockResponse);
    });

    it('should handle profile fetch errors', async () => {
      const { authAPI } = require('../api');
      const mockError = new Error('Unauthorized');

      mockAxiosInstance.get.mockRejectedValue(mockError);

      await expect(authAPI.getProfile()).rejects.toBe(mockError);
    });
  });
});

describe('Invoices API', () => {
  let mockAxiosInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockAxiosInstance = {
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
      post: jest.fn(),
      get: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
    };

    mockedAxios.create.mockReturnValue(mockAxiosInstance);
    jest.resetModules();
  });

  describe('invoicesAPI methods', () => {
    it('should call correct endpoints for all invoice operations', async () => {
      const { invoicesAPI } = require('../api');

      await invoicesAPI.getAll();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/invoices/');

      await invoicesAPI.getById(123);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/invoices/123');

      const invoiceData = { customer_name: 'Test Customer' };
      await invoicesAPI.create(invoiceData);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/invoices/', invoiceData);

      await invoicesAPI.update(123, invoiceData);
      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/invoices/123', invoiceData);

      await invoicesAPI.delete(123);
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/invoices/123');
    });
  });
});

describe('Reports API', () => {
  let mockAxiosInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockAxiosInstance = {
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
      post: jest.fn(),
      get: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
    };

    mockedAxios.create.mockReturnValue(mockAxiosInstance);
    jest.resetModules();
  });

  describe('reportsAPI methods', () => {
    it('should call correct endpoints for all report operations', async () => {
      const { reportsAPI } = require('../api');

      await reportsAPI.getAll();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/reports/');

      const reportData = { type: 'monthly' };
      await reportsAPI.generate(reportData);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/reports/generate', reportData);

      await reportsAPI.getDashboard();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/reports/dashboard');

      await reportsAPI.delete(123);
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/reports/123');
    });
  });
});

describe('Integration Tests', () => {
  let mockAxiosInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    
    mockAxiosInstance = {
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
      post: jest.fn(),
      get: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
    };

    mockedAxios.create.mockReturnValue(mockAxiosInstance);
    jest.resetModules();
  });

  it('should add token to authenticated requests', async () => {
    const mockToken = 'mock-jwt-token';
    localStorageMock.getItem.mockReturnValue(mockToken);

    const { authAPI } = require('../api');
    
    const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
    
    const config = { headers: {} };
    requestInterceptor(config);

    await authAPI.getProfile();

    expect(mockAxiosInstance.get).toHaveBeenCalledWith('/auth/profile');
    expect(config.headers.Authorization).toBe(`Bearer ${mockToken}`);
  });

  it('should handle authentication flow with interceptors', async () => {
    const { authAPI } = require('../api');
    
    const responseErrorHandler = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
    
    const mockError = {
      response: { status: 401 },
    };

    expect(() => responseErrorHandler(mockError)).rejects.toBe(mockError);
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('user');
    expect(window.location.href).toBe('/login');
  });
});
