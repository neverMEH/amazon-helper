import React, { useEffect, useState } from 'react';
import { Button, Alert, Box, CircularProgress } from '@mui/material';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';

interface AuthStatus {
  authenticated: boolean;
  message: string;
}

export const AmazonAuthStatus: React.FC = () => {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [authorizing, setAuthorizing] = useState(false);
  const { token } = useAuth();

  useEffect(() => {
    checkAuthStatus();
  }, [token]);

  const checkAuthStatus = async () => {
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await api.get('/auth/amazon/status');
      setAuthStatus(response.data);
    } catch (error) {
      console.error('Failed to check Amazon auth status:', error);
      setAuthStatus({
        authenticated: false,
        message: 'Failed to check authentication status'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAmazonLogin = async () => {
    setAuthorizing(true);
    try {
      const response = await api.get('/auth/amazon/login');
      if (response.data.auth_url) {
        // Redirect to Amazon OAuth
        window.location.href = response.data.auth_url;
      }
    } catch (error) {
      console.error('Failed to initiate Amazon login:', error);
      setAuthorizing(false);
    }
  };

  const handleRefreshToken = async () => {
    setLoading(true);
    try {
      await api.post('/auth/amazon/refresh');
      await checkAuthStatus();
    } catch (error) {
      console.error('Failed to refresh token:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" alignItems="center" gap={2}>
        <CircularProgress size={20} />
        <span>Checking Amazon authentication...</span>
      </Box>
    );
  }

  if (!token) {
    return null;
  }

  if (!authStatus?.authenticated) {
    return (
      <Alert 
        severity="warning" 
        action={
          <Button 
            color="inherit" 
            size="small" 
            onClick={handleAmazonLogin}
            disabled={authorizing}
          >
            {authorizing ? 'Redirecting...' : 'Connect Amazon Account'}
          </Button>
        }
      >
        {authStatus?.message || 'Amazon account not connected. Connect your account to execute workflows.'}
      </Alert>
    );
  }

  return (
    <Alert 
      severity="success"
      action={
        <Button 
          color="inherit" 
          size="small" 
          onClick={handleRefreshToken}
        >
          Refresh Token
        </Button>
      }
    >
      Amazon account connected
    </Alert>
  );
};