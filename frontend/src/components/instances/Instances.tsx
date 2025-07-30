import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Database, CheckCircle, XCircle, ChevronRight } from 'lucide-react';
import api from '../../services/api';

interface AMCInstance {
  id: string;
  instanceId: string;
  instanceName: string;
  region: string;
  accountId: string;
  accountName: string;
  isActive: boolean;
  type: string;
  createdAt: string;
  brands: string[];
  stats: {
    totalCampaigns: number;
    totalWorkflows: number;
    activeWorkflows: number;
  };
}

export default function Instances() {
  const navigate = useNavigate();
  const { data: instances, isLoading } = useQuery<AMCInstance[]>({
    queryKey: ['instances'],
    queryFn: async () => {
      const response = await api.get('/instances/');
      return response.data;
    },
  });

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">AMC Instances</h1>
        <p className="mt-1 text-sm text-gray-600">
          Manage your Amazon Marketing Cloud instances
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading instances...</div>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Instance Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Instance ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Account
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Brands
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Workflows
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="relative px-6 py-3">
                  <span className="sr-only">View</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {instances?.map((instance) => (
                <tr
                  key={instance.id}
                  onClick={() => navigate(`/instances/${instance.instanceId}`)}
                  className="hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Database className="h-8 w-8 text-gray-400 mr-3" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {instance.instanceName}
                        </div>
                        <div className="text-sm text-gray-500">
                          {instance.region}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{instance.instanceId}</div>
                    <div className="text-sm text-gray-500">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        instance.type === 'SANDBOX' 
                          ? 'bg-yellow-100 text-yellow-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {instance.type}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{instance.accountName}</div>
                    <div className="text-sm text-gray-500">{instance.accountId}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {instance.brands.length > 0 ? (
                        instance.brands.map((brand, idx) => (
                          <span
                            key={idx}
                            className="inline-flex px-2 py-1 text-xs font-medium bg-indigo-100 text-indigo-800 rounded-full"
                          >
                            {brand}
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-gray-500">No brands</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {instance.stats.activeWorkflows} active
                    </div>
                    <div className="text-sm text-gray-500">
                      {instance.stats.totalWorkflows} total
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    {instance.isActive ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        <XCircle className="h-4 w-4 mr-1" />
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}