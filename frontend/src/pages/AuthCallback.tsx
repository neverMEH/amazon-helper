import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2, AlertCircle } from 'lucide-react';
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
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
        <div className="flex items-center p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
          <span className="text-red-800">{error}</span>
        </div>
        <a href="/" className="text-blue-600 hover:text-blue-800 underline">
          Return to Home
        </a>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
      <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      <span className="text-gray-600">Completing authentication...</span>
    </div>
  );
};