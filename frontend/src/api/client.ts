import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = '/api';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
client.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle auth errors and extract error messages
client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error?: string; message?: string }>) => {
    // Extract error message from response body
    const errorMessage = error.response?.data?.error || error.response?.data?.message;

    if (error.response?.status === 401) {
      // Only redirect for non-login requests (login 401 should show error message)
      const isLoginRequest = error.config?.url?.includes('/auth/login');
      if (!isLoginRequest) {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }

    // Create a new error with the server's message if available
    if (errorMessage) {
      const customError = new Error(errorMessage);
      (customError as Error & { status?: number }).status = error.response?.status;
      return Promise.reject(customError);
    }

    return Promise.reject(error);
  }
);

export default client;
