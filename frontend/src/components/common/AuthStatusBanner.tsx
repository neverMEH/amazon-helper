import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

export default function AuthStatusBanner() {
  const [isDismissed, setIsDismissed] = useState(false);
  const [hasShownOnce, setHasShownOnce] = useState(false);

  // Check token status
  const { data: tokenStatus } = useQuery({
    queryKey: ['token-status'],
    queryFn: async () => {
      try {
        const response = await api.get('/auth/token-status');
        return response.data;
      } catch (error) {
        console.error('Failed to check token status:', error);
        return { hasValidToken: false, message: 'Failed to check authentication status' };
      }
    },
    refetchInterval: 60000, // Check every minute
    staleTime: 30000, // Consider data stale after 30 seconds
  });

  // Reset dismissed state when auth status changes from invalid to valid
  useEffect(() => {
    if (tokenStatus?.hasValidToken && hasShownOnce) {
      setIsDismissed(false);
      setHasShownOnce(false);
    } else if (!tokenStatus?.hasValidToken && !hasShownOnce) {
      setHasShownOnce(true);
      setIsDismissed(false);
    }
  }, [tokenStatus?.hasValidToken, hasShownOnce]);

  // Don't show if authenticated or dismissed
  if (tokenStatus?.hasValidToken || isDismissed) {
    return null;
  }

  // Don't show while loading initial status
  if (tokenStatus === undefined) {
    return null;
  }

  return (
    <div className="bg-red-600 text-white shadow-lg relative sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-3">
          <div className="flex items-center flex-1">
            <AlertTriangle className="h-5 w-5 mr-3 flex-shrink-0" />
            <p className="font-medium text-sm sm:text-base">
              Amazon Advertising API authentication required
            </p>
            <span className="hidden sm:inline-block mx-2">•</span>
            <p className="hidden sm:inline-block text-sm">
              {tokenStatus?.message || 'Your authentication has expired or is invalid'}
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <Link
              to="/profile"
              className="bg-white text-red-600 px-4 py-1.5 rounded-md text-sm font-medium hover:bg-red-50 transition-colors"
            >
              Re-authenticate
            </Link>
            
            <button
              onClick={() => setIsDismissed(true)}
              className="text-white hover:text-red-200 transition-colors"
              aria-label="Dismiss banner"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
        
        {/* Mobile-only extended message */}
        <p className="sm:hidden text-sm pb-3">
          {tokenStatus?.message || 'Your authentication has expired or is invalid'}
        </p>
      </div>
    </div>
  );
}