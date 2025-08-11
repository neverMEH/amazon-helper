import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

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

// Handle auth errors with debouncing to prevent logout cascade
let logoutTimer: ReturnType<typeof setTimeout> | null = null;
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Debounce logout to prevent multiple redirects
      if (!logoutTimer) {
        logoutTimer = setTimeout(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
          logoutTimer = null;
        }, 100); // Small delay to batch multiple 401s
      }
    }
    return Promise.reject(error);
  }
);

export default api;