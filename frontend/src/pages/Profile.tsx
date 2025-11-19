import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { User, Mail, Calendar, Shield, RefreshCw, AlertCircle, CheckCircle, Key, Building, Database, Eye, EyeOff, TestTube } from 'lucide-react';
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

interface SnowflakeConfig {
  account: string;
  username: string;
  password: string;
  warehouse: string;
  database: string;
  schema?: string;
  role?: string;
}

export default function Profile() {
  const queryClient = useQueryClient();
  const [isReAuthenticating, setIsReAuthenticating] = useState(false);

  // Snowflake configuration state
  const [showPassword, setShowPassword] = useState(false);
  const [snowflakeConfig, setSnowflakeConfig] = useState<SnowflakeConfig>({
    account: '',
    username: '',
    password: '',
    warehouse: '',
    database: '',
    schema: '',
    role: '',
  });
  const [isEditingSnowflake, setIsEditingSnowflake] = useState(false);

  // Check for reauth success on component mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('reauth') === 'success') {
      toast.success('Amazon account re-connected successfully!');
      // Clear the query parameter
      window.history.replaceState({}, '', window.location.pathname);
      // Refetch profile data
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
    }
  }, [queryClient]);

  // Fetch user profile
  const { data: profile, isLoading, error } = useQuery<UserProfile>({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const response = await api.get('/profile');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch Snowflake configuration
  const { data: snowflakeConfigData, isLoading: snowflakeLoading } = useQuery({
    queryKey: ['snowflake-config'],
    queryFn: async () => {
      try {
        const response = await api.get('/snowflake/config');
        return response.data;
      } catch (error: any) {
        if (error.response?.status === 404) {
          return null; // No config exists yet
        }
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000,
  });

  // Load Snowflake config into state when fetched
  useEffect(() => {
    if (snowflakeConfigData && !isEditingSnowflake) {
      setSnowflakeConfig({
        account: snowflakeConfigData.account || '',
        username: snowflakeConfigData.username || '',
        password: '', // Never populate password from server
        warehouse: snowflakeConfigData.warehouse || '',
        database: snowflakeConfigData.database || '',
        schema: snowflakeConfigData.schema || '',
        role: snowflakeConfigData.role || '',
      });
    }
  }, [snowflakeConfigData, isEditingSnowflake]);

  // Save Snowflake configuration
  const saveSnowflakeMutation = useMutation({
    mutationFn: async (config: SnowflakeConfig) => {
      const response = await api.post('/snowflake/config', config);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Snowflake configuration saved successfully');
      setIsEditingSnowflake(false);
      queryClient.invalidateQueries({ queryKey: ['snowflake-config'] });
      queryClient.invalidateQueries({ queryKey: ['snowflake-config-check'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to save Snowflake configuration');
    },
  });

  // Test Snowflake connection
  const testSnowflakeMutation = useMutation({
    mutationFn: async (config: SnowflakeConfig) => {
      const response = await api.post('/snowflake/config/test', config);
      return response.data;
    },
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Snowflake connection test successful!');
      } else {
        toast.error(data.error || 'Connection test failed');
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to test connection');
    },
  });

  // Delete Snowflake configuration
  const deleteSnowflakeMutation = useMutation({
    mutationFn: async () => {
      const response = await api.delete('/snowflake/config');
      return response.data;
    },
    onSuccess: () => {
      toast.success('Snowflake configuration deleted');
      setSnowflakeConfig({
        account: '',
        username: '',
        password: '',
        warehouse: '',
        database: '',
        schema: '',
        role: '',
      });
      setIsEditingSnowflake(false);
      queryClient.invalidateQueries({ queryKey: ['snowflake-config'] });
      queryClient.invalidateQueries({ queryKey: ['snowflake-config-check'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete configuration');
    },
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

      {/* Snowflake Configuration Section */}
      <div className="bg-white shadow rounded-lg mb-6" id="snowflake">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 flex items-center gap-2">
            <Database className="h-5 w-5" />
            Snowflake Configuration
          </h2>
        </div>
        <div className="px-6 py-4 space-y-4">
          {/* Status Banner */}
          {snowflakeConfigData ? (
            <div className="bg-green-50 border border-green-200 rounded-md p-3">
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                <div>
                  <p className="text-sm font-medium text-green-800">Snowflake Connected</p>
                  <p className="text-xs text-green-700 mt-1">
                    {snowflakeConfigData.account} • {snowflakeConfigData.database}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-blue-500 mr-2" />
                <div>
                  <p className="text-sm font-medium text-blue-800">No Snowflake Configuration</p>
                  <p className="text-xs text-blue-700 mt-1">
                    Configure Snowflake to enable automatic upload of execution results to your data warehouse.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Configuration Form */}
          {(isEditingSnowflake || !snowflakeConfigData) && (
            <div className="space-y-4 pt-4 border-t">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="sf-account" className="block text-sm font-medium text-gray-700">
                    Account <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="sf-account"
                    value={snowflakeConfig.account}
                    onChange={(e) => setSnowflakeConfig({...snowflakeConfig, account: e.target.value})}
                    placeholder="myorg-account123"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                  <p className="mt-1 text-xs text-gray-500">Your Snowflake account identifier</p>
                </div>

                <div>
                  <label htmlFor="sf-username" className="block text-sm font-medium text-gray-700">
                    Username <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="sf-username"
                    value={snowflakeConfig.username}
                    onChange={(e) => setSnowflakeConfig({...snowflakeConfig, username: e.target.value})}
                    placeholder="username"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="sf-password" className="block text-sm font-medium text-gray-700">
                  Password <span className="text-red-500">*</span>
                </label>
                <div className="mt-1 relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="sf-password"
                    value={snowflakeConfig.password}
                    onChange={(e) => setSnowflakeConfig({...snowflakeConfig, password: e.target.value})}
                    placeholder={snowflakeConfigData ? 'Enter new password to update' : 'Password'}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
                {snowflakeConfigData && !snowflakeConfig.password && (
                  <p className="mt-1 text-xs text-gray-500">Leave blank to keep existing password</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="sf-warehouse" className="block text-sm font-medium text-gray-700">
                    Warehouse <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="sf-warehouse"
                    value={snowflakeConfig.warehouse}
                    onChange={(e) => setSnowflakeConfig({...snowflakeConfig, warehouse: e.target.value})}
                    placeholder="COMPUTE_WH"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label htmlFor="sf-database" className="block text-sm font-medium text-gray-700">
                    Database <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="sf-database"
                    value={snowflakeConfig.database}
                    onChange={(e) => setSnowflakeConfig({...snowflakeConfig, database: e.target.value})}
                    placeholder="ANALYTICS"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="sf-schema" className="block text-sm font-medium text-gray-700">
                    Schema (optional)
                  </label>
                  <input
                    type="text"
                    id="sf-schema"
                    value={snowflakeConfig.schema}
                    onChange={(e) => setSnowflakeConfig({...snowflakeConfig, schema: e.target.value})}
                    placeholder="PUBLIC"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                  <p className="mt-1 text-xs text-gray-500">Defaults to PUBLIC if not specified</p>
                </div>

                <div>
                  <label htmlFor="sf-role" className="block text-sm font-medium text-gray-700">
                    Role (optional)
                  </label>
                  <input
                    type="text"
                    id="sf-role"
                    value={snowflakeConfig.role}
                    onChange={(e) => setSnowflakeConfig({...snowflakeConfig, role: e.target.value})}
                    placeholder="ACCOUNTADMIN"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t">
                <button
                  type="button"
                  onClick={() => testSnowflakeMutation.mutate(snowflakeConfig)}
                  disabled={testSnowflakeMutation.isPending || !snowflakeConfig.account || !snowflakeConfig.username || !snowflakeConfig.password}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {testSnowflakeMutation.isPending ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Testing...
                    </>
                  ) : (
                    <>
                      <TestTube className="h-4 w-4 mr-2" />
                      Test Connection
                    </>
                  )}
                </button>

                <div className="flex items-center space-x-2">
                  {snowflakeConfigData && (
                    <button
                      type="button"
                      onClick={() => {
                        setIsEditingSnowflake(false);
                        setSnowflakeConfig({
                          account: snowflakeConfigData.account || '',
                          username: snowflakeConfigData.username || '',
                          password: '',
                          warehouse: snowflakeConfigData.warehouse || '',
                          database: snowflakeConfigData.database || '',
                          schema: snowflakeConfigData.schema || '',
                          role: snowflakeConfigData.role || '',
                        });
                      }}
                      className="px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => saveSnowflakeMutation.mutate(snowflakeConfig)}
                    disabled={saveSnowflakeMutation.isPending || !snowflakeConfig.account || !snowflakeConfig.username || !snowflakeConfig.warehouse || !snowflakeConfig.database}
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {saveSnowflakeMutation.isPending ? 'Saving...' : 'Save Configuration'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* View Mode Actions */}
          {!isEditingSnowflake && snowflakeConfigData && (
            <div className="flex items-center justify-between pt-4 border-t">
              <button
                type="button"
                onClick={() => setIsEditingSnowflake(true)}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Edit Configuration
              </button>
              <button
                type="button"
                onClick={() => {
                  if (window.confirm('Are you sure you want to delete your Snowflake configuration? This will disable automatic uploads.')) {
                    deleteSnowflakeMutation.mutate();
                  }
                }}
                disabled={deleteSnowflakeMutation.isPending}
                className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleteSnowflakeMutation.isPending ? 'Deleting...' : 'Delete Configuration'}
              </button>
            </div>
          )}
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