import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { User, Mail, Calendar, Shield, RefreshCw, AlertCircle, CheckCircle, Key, Building } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';

interface UserProfile {
  id: string;
  email: string;
  name?: string;
  created_at: string;
  last_login?: string;
  amazon_connected: boolean;
  token_expires_at?: string;
  refresh_token_valid?: boolean;
  accounts?: {
    account_id: string;
    account_name: string;
    marketplace_id: string;
  }[];
}

export default function Profile() {
  const queryClient = useQueryClient();
  const [isReAuthenticating, setIsReAuthenticating] = useState(false);

  // Fetch user profile
  const { data: profile, isLoading, error } = useQuery<UserProfile>({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const response = await api.get('/profile');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Re-authenticate with Amazon
  const reAuthMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/auth/amazon/reauth');
      return response.data;
    },
    onSuccess: (data) => {
      if (data.authUrl) {
        // Redirect to Amazon auth
        window.location.href = data.authUrl;
      } else {
        toast.success('Re-authentication initiated');
        queryClient.invalidateQueries({ queryKey: ['user-profile'] });
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to re-authenticate');
    },
  });

  // Disconnect Amazon account
  const disconnectMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/auth/amazon/disconnect');
      return response.data;
    },
    onSuccess: () => {
      toast.success('Amazon account disconnected');
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to disconnect');
    },
  });

  const handleReAuth = () => {
    setIsReAuthenticating(true);
    reAuthMutation.mutate();
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTokenStatus = () => {
    if (!profile?.token_expires_at) return null;
    
    const expiresAt = new Date(profile.token_expires_at);
    const now = new Date();
    const hoursUntilExpiry = (expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60);
    
    if (hoursUntilExpiry < 0) {
      return { status: 'expired', message: 'Token expired', color: 'red' };
    } else if (hoursUntilExpiry < 24) {
      return { status: 'expiring', message: `Expires in ${Math.round(hoursUntilExpiry)} hours`, color: 'yellow' };
    } else {
      const daysUntilExpiry = Math.round(hoursUntilExpiry / 24);
      return { status: 'valid', message: `Valid for ${daysUntilExpiry} days`, color: 'green' };
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-600">Failed to load profile information</p>
      </div>
    );
  }

  const tokenStatus = getTokenStatus();

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Profile Settings</h1>

      {/* User Information Section */}
      <div className="bg-white shadow rounded-lg mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 flex items-center gap-2">
            <User className="h-5 w-5" />
            User Information
          </h2>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <div className="mt-1 flex items-center gap-2">
                <Mail className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-900">{profile?.email}</span>
              </div>
            </div>
          </div>

          {profile?.name && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <p className="mt-1 text-sm text-gray-900">{profile.name}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Member Since</label>
              <div className="mt-1 flex items-center gap-2">
                <Calendar className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-900">{formatDate(profile?.created_at)}</span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Last Login</label>
              <div className="mt-1 flex items-center gap-2">
                <Calendar className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-900">{formatDate(profile?.last_login)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Amazon Integration Section */}
      <div className="bg-white shadow rounded-lg mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Amazon Advertising Integration
          </h2>
        </div>
        <div className="px-6 py-4 space-y-4">
          {/* Connection Status */}
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Connection Status</label>
              <div className="flex items-center gap-2">
                {profile?.amazon_connected ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="text-sm font-medium text-green-700">Connected</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-5 w-5 text-red-500" />
                    <span className="text-sm font-medium text-red-700">Not Connected</span>
                  </>
                )}
              </div>
            </div>

            {profile?.amazon_connected && (
              <button
                onClick={() => disconnectMutation.mutate()}
                disabled={disconnectMutation.isPending}
                className="px-3 py-1 text-sm text-red-600 hover:text-red-700 border border-red-300 rounded-md hover:bg-red-50"
              >
                Disconnect
              </button>
            )}
          </div>

          {/* Token Status */}
          {profile?.amazon_connected && tokenStatus && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Token Status</label>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Key className="h-4 w-4 text-gray-400" />
                  <span className={`text-sm font-medium text-${tokenStatus.color}-700`}>
                    {tokenStatus.message}
                  </span>
                </div>
                {tokenStatus.status !== 'valid' && (
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${tokenStatus.color}-100 text-${tokenStatus.color}-800`}>
                    Action Required
                  </span>
                )}
              </div>
              {profile.token_expires_at && (
                <p className="mt-1 text-xs text-gray-500">
                  Expires: {formatDate(profile.token_expires_at)}
                </p>
              )}
            </div>
          )}

          {/* Re-authentication Button */}
          <div className="pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-900">Re-authenticate with Amazon</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {profile?.amazon_connected 
                    ? 'Refresh your Amazon Advertising API credentials'
                    : 'Connect your Amazon Advertising account to get started'}
                </p>
              </div>
              <button
                onClick={handleReAuth}
                disabled={reAuthMutation.isPending || isReAuthenticating}
                className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
                  tokenStatus?.status === 'expired' || !profile?.amazon_connected
                    ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                    : 'bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500'
                } focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${(reAuthMutation.isPending || isReAuthenticating) ? 'animate-spin' : ''}`} />
                {profile?.amazon_connected ? 'Re-authenticate' : 'Connect Amazon Account'}
              </button>
            </div>

            {/* Warning for expired tokens */}
            {tokenStatus?.status === 'expired' && (
              <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-3">
                <div className="flex">
                  <AlertCircle className="h-5 w-5 text-red-400 mt-0.5" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Authentication Required</h3>
                    <p className="mt-1 text-sm text-red-700">
                      Your Amazon authentication has expired. Please re-authenticate to continue using AMC features.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Warning for expiring tokens */}
            {tokenStatus?.status === 'expiring' && (
              <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-md p-3">
                <div className="flex">
                  <AlertCircle className="h-5 w-5 text-yellow-400 mt-0.5" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-yellow-800">Token Expiring Soon</h3>
                    <p className="mt-1 text-sm text-yellow-700">
                      Your authentication will expire soon. Re-authenticate to avoid service interruption.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Connected Accounts Section */}
      {profile?.accounts && profile.accounts.length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900 flex items-center gap-2">
              <Building className="h-5 w-5" />
              Connected AMC Accounts
            </h2>
          </div>
          <div className="px-6 py-4">
            <div className="space-y-3">
              {profile.accounts.map((account, index) => (
                <div key={index} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{account.account_name}</p>
                    <p className="text-xs text-gray-500">
                      ID: {account.account_id} • Marketplace: {account.marketplace_id}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}