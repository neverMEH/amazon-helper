import React, { useState, useEffect } from 'react';
import { SnowflakeConfiguration } from '../../types/report';

interface SnowflakeConfigProps {
  onConfigSaved?: () => void;
}

const SnowflakeConfig: React.FC<SnowflakeConfigProps> = ({ onConfigSaved }) => {
  const [config, setConfig] = useState<Partial<SnowflakeConfiguration>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [authMethod, setAuthMethod] = useState<'password' | 'keypair'>('password');

  useEffect(() => {
    loadExistingConfig();
  }, []);

  const loadExistingConfig = async () => {
    try {
      const response = await fetch('/api/snowflake/configurations', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const configs = await response.json();
        if (configs.length > 0) {
          setConfig(configs[0]);
          setAuthMethod(configs[0].username ? 'password' : 'keypair');
        }
      }
    } catch (err) {
      console.error('Failed to load Snowflake config:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const configData = {
        account_identifier: config.account_identifier,
        warehouse: config.warehouse,
        database: config.database,
        schema: config.schema,
        role: config.role,
        ...(authMethod === 'password' 
          ? { username: config.username, password: config.password }
          : { private_key: config.private_key }
        )
      };

      const url = config.id 
        ? `/api/snowflake/configurations/${config.id}`
        : '/api/snowflake/configurations';
      
      const method = config.id ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(configData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save configuration');
      }

      setSuccess('Snowflake configuration saved successfully!');
      onConfigSaved?.();
      
      // Test connection
      const savedConfig = await response.json();
      await testConnection(savedConfig.id);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (configId: string) => {
    try {
      const response = await fetch(`/api/snowflake/configurations/${configId}/test-connection`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        setSuccess(prev => prev + ' Connection test successful!');
      } else {
        const errorData = await response.json();
        setError(`Connection test failed: ${errorData.detail}`);
      }
    } catch (err) {
      setError(`Connection test failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Snowflake Configuration</h2>
      
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">Success</h3>
              <div className="mt-2 text-sm text-green-700">{success}</div>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Authentication Method */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Authentication Method
          </label>
          <div className="flex space-x-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="password"
                checked={authMethod === 'password'}
                onChange={(e) => setAuthMethod(e.target.value as 'password')}
                className="mr-2"
              />
              Username/Password
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="keypair"
                checked={authMethod === 'keypair'}
                onChange={(e) => setAuthMethod(e.target.value as 'keypair')}
                className="mr-2"
              />
              Key-Pair Authentication
            </label>
          </div>
        </div>

        {/* Basic Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Account Identifier *
            </label>
            <input
              type="text"
              value={config.account_identifier || ''}
              onChange={(e) => setConfig({...config, account_identifier: e.target.value})}
              placeholder="your-account.snowflakecomputing.com"
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Warehouse *
            </label>
            <input
              type="text"
              value={config.warehouse || ''}
              onChange={(e) => setConfig({...config, warehouse: e.target.value})}
              placeholder="COMPUTE_WH"
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Database *
            </label>
            <input
              type="text"
              value={config.database || ''}
              onChange={(e) => setConfig({...config, database: e.target.value})}
              placeholder="YOUR_DATABASE"
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Schema *
            </label>
            <input
              type="text"
              value={config.schema || ''}
              onChange={(e) => setConfig({...config, schema: e.target.value})}
              placeholder="PUBLIC"
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Role (Optional)
            </label>
            <input
              type="text"
              value={config.role || ''}
              onChange={(e) => setConfig({...config, role: e.target.value})}
              placeholder="ACCOUNTADMIN"
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Authentication Fields */}
        {authMethod === 'password' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Username *
              </label>
              <input
                type="text"
                value={config.username || ''}
                onChange={(e) => setConfig({...config, username: e.target.value})}
                placeholder="your_username"
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Password *
              </label>
              <input
                type="password"
                value={config.password || ''}
                onChange={(e) => setConfig({...config, password: e.target.value})}
                placeholder="your_password"
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Private Key *
            </label>
            <textarea
              value={config.private_key || ''}
              onChange={(e) => setConfig({...config, private_key: e.target.value})}
              placeholder="-----BEGIN PRIVATE KEY-----&#10;...&#10;-----END PRIVATE KEY-----"
              rows={6}
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
              required
            />
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => setConfig({})}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            Clear
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </form>

      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
        <h3 className="text-sm font-medium text-blue-800 mb-2">Getting Started</h3>
        <div className="text-sm text-blue-700 space-y-1">
          <p>1. Get your Snowflake account details from your Snowflake console</p>
          <p>2. Choose your preferred authentication method</p>
          <p>3. Fill in the required connection details</p>
          <p>4. Test the connection to ensure everything works</p>
          <p>5. Enable Snowflake storage when creating reports</p>
        </div>
      </div>
    </div>
  );
};

export default SnowflakeConfig;
