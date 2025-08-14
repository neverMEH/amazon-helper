import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Track if we're currently refreshing the token
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (error?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle auth errors with token refresh
let logoutTimer: ReturnType<typeof setTimeout> | null = null;
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Check if this is a 401 error and we haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If we're already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => {
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Try to refresh the token
        const refreshResponse = await api.post('/auth/refresh');
        
        if (refreshResponse.data?.access_token) {
          const newToken = refreshResponse.data.access_token;
          localStorage.setItem('access_token', newToken);
          
          // Update the authorization header for the original request
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          
          // Process any queued requests
          processQueue(null, newToken);
          
          // Retry the original request
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Token refresh failed, process queue with error
        processQueue(refreshError, null);
        
        // Clear local storage and redirect to login
        if (!logoutTimer) {
          logoutTimer = setTimeout(() => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
            logoutTimer = null;
          }, 100);
        }
        
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // For non-401 errors or if refresh failed, just reject
    return Promise.reject(error);
  }
);

export default api;