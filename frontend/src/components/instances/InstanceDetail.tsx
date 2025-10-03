import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Database, Activity, FileText, History, Settings, Package } from 'lucide-react';
import api from '../../services/api';
import InstanceOverview from './InstanceOverview';
import InstanceCampaigns from './InstanceCampaigns';
import InstanceASINs from './InstanceASINs';
import InstanceWorkflows from './InstanceWorkflows';
import InstanceExecutions from './InstanceExecutions';
import InstanceMappingTab from './InstanceMappingTab';

interface InstanceDetail {
  id: string;
  instanceId: string;
  instanceName: string;
  type: string;
  region: string;
  status: string;
  isActive: boolean;
  account: {
    accountId: string;
    accountName: string;
    marketplaceId: string;
  };
  endpointUrl: string;
  dataUploadAccountId: string;
  capabilities: Record<string, any>;
  createdAt: string;
  updatedAt: string;
  brands: string[];
  stats: {
    totalCampaigns: number;
    totalWorkflows: number;
    activeWorkflows: number;
  };
}

type TabType = 'overview' | 'campaigns' | 'asins' | 'queries' | 'executions' | 'mappings';

export default function InstanceDetail() {
  const { instanceId } = useParams<{ instanceId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  const { data: instance, isLoading, error } = useQuery<InstanceDetail>({
    queryKey: ['instance', instanceId],
    queryFn: async () => {
      const response = await api.get(`/instances/${instanceId}`);
      return response.data;
    },
    enabled: !!instanceId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading instance details...</div>
      </div>
    );
  }

  if (error || !instance) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">Failed to load instance details</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview' as TabType, name: 'Overview', icon: Database },
    { id: 'campaigns' as TabType, name: 'Campaigns', icon: Activity },
    { id: 'asins' as TabType, name: 'ASINs', icon: Package },
    { id: 'queries' as TabType, name: 'Workflows', icon: FileText },
    { id: 'executions' as TabType, name: 'Executions', icon: History },
    { id: 'mappings' as TabType, name: 'Mapping', icon: Settings },
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/instances')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Instances
        </button>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{instance.instanceName}</h1>
            <p className="mt-1 text-sm text-gray-600">
              {instance.instanceId} • {instance.account.accountName} • {instance.region}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <span className={`px-3 py-1 text-sm font-medium rounded-full ${
              instance.type === 'SANDBOX' 
                ? 'bg-yellow-100 text-yellow-800' 
                : 'bg-blue-100 text-blue-800'
            }`}>
              {instance.type}
            </span>
            <span className={`px-3 py-1 text-sm font-medium rounded-full ${
              instance.isActive
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {instance.isActive ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center py-2 px-1 border-b-2 font-medium text-sm
                  ${activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="h-4 w-4 mr-2" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white shadow rounded-lg">
        {activeTab === 'overview' && <InstanceOverview instance={instance} />}
        {activeTab === 'campaigns' && <InstanceCampaigns instanceId={instance.instanceId} />}
        {activeTab === 'asins' && <InstanceASINs instanceId={instance.id} />}
        {activeTab === 'queries' && <InstanceWorkflows instanceId={instance.instanceId} />}
        {activeTab === 'executions' && <InstanceExecutions instanceId={instance.instanceId} />}
        {activeTab === 'mappings' && <InstanceMappingTab instanceId={instance.id} />}
      </div>
    </div>
  );
}