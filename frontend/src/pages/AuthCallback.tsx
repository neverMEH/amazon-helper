import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Box, CircularProgress, Alert } from '@mui/material';
import { useAuth } from '../hooks/useAuth';

export const AuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      const token = searchParams.get('token');
      const redirect = searchParams.get('redirect') || '/';
      const errorMessage = searchParams.get('message');

      if (errorMessage) {
        setError(errorMessage);
        return;
      }

      if (token) {
        try {
          // Store the token
          await login(token);
          
          // Redirect to the intended page
          navigate(redirect);
        } catch (err) {
          setError('Failed to complete authentication');
        }
      } else {
        setError('No authentication token received');
      }
    };

    handleCallback();
  }, [searchParams, login, navigate]);

  if (error) {
    return (
      <Box 
        display="flex" 
        flexDirection="column" 
        alignItems="center" 
        justifyContent="center" 
        minHeight="50vh"
        gap={2}
      >
        <Alert severity="error">{error}</Alert>
        <a href="/">Return to Home</a>
      </Box>
    );
  }

  return (
    <Box 
      display="flex" 
      flexDirection="column" 
      alignItems="center" 
      justifyContent="center" 
      minHeight="50vh"
      gap={2}
    >
      <CircularProgress />
      <span>Completing authentication...</span>
    </Box>
  );
};