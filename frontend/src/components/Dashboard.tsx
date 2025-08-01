import { useQuery } from '@tanstack/react-query';
import { BarChart3, Database, GitBranch, Tag } from 'lucide-react';
import api from '../services/api';

interface DashboardStats {
  totalInstances: number;
  totalWorkflows: number;
  totalCampaigns: number;
  recentExecutions: number;
}

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      // For now, we'll use placeholder data
      // TODO: Create a dedicated stats endpoint
      const [instances, workflows, campaigns] = await Promise.all([
        api.get('/instances'),
        api.get('/workflows'),
        api.get('/campaigns'),
      ]);
      
      return {
        totalInstances: instances.data.length || 0,
        totalWorkflows: workflows.data.length || 0,
        totalCampaigns: campaigns.data.length || 0,
        recentExecutions: 0,
      };
    },
  });

  const cards = [
    {
      title: 'AMC Instances',
      value: stats?.totalInstances || 0,
      icon: Database,
      color: 'bg-blue-500',
    },
    {
      title: 'Workflows',
      value: stats?.totalWorkflows || 0,
      icon: GitBranch,
      color: 'bg-green-500',
    },
    {
      title: 'Campaigns',
      value: stats?.totalCampaigns || 0,
      icon: Tag,
      color: 'bg-purple-500',
    },
    {
      title: 'Recent Executions',
      value: stats?.recentExecutions || 0,
      icon: BarChart3,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          Overview of your Amazon Marketing Cloud resources
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading...</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {cards.map((card) => (
            <div
              key={card.title}
              className="bg-white overflow-hidden shadow rounded-lg"
            >
              <div className="p-5">
                <div className="flex items-center">
                  <div className={`flex-shrink-0 ${card.color} rounded-md p-3`}>
                    <card.icon className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        {card.title}
                      </dt>
                      <dd className="text-2xl font-semibold text-gray-900">
                        {card.value}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}