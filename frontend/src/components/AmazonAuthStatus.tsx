import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, Loader2, RefreshCw } from 'lucide-react';
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
      <div className="flex items-center gap-2 text-gray-600">
        <Loader2 className="w-5 h-5 animate-spin" />
        <span>Checking Amazon authentication...</span>
      </div>
    );
  }

  if (!token) {
    return null;
  }

  if (!authStatus?.authenticated) {
    return (
      <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-yellow-600 mr-2" />
            <span className="text-yellow-800">
              {authStatus?.message || 'Amazon account not connected. Connect your account to execute workflows.'}
            </span>
          </div>
          <button
            onClick={handleAmazonLogin}
            disabled={authorizing}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {authorizing ? 'Redirecting...' : 'Connect Amazon Account'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
          <span className="text-green-800">Amazon account connected</span>
        </div>
        <button
          onClick={handleRefreshToken}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm font-medium flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh Token
        </button>
      </div>
    </div>
  );
};