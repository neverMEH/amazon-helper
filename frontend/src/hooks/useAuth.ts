import { useCallback } from 'react';

export const useAuth = () => {
  const token = localStorage.getItem('access_token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const login = useCallback(async (token: string) => {
    localStorage.setItem('access_token', token);
    // Optionally fetch user info here
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }, []);

  return {
    token,
    user,
    login,
    logout,
    isAuthenticated: !!token,
  };
};