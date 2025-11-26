import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Database,
  Activity,
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  TrendingUp,
  Play,
  ArrowRight,
  RefreshCw,
  Loader,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import api from '../services/api';

interface DashboardStats {
  totalInstances: number;
  activeInstances: number;
  totalWorkflows: number;
  executions: {
    total7d: number;
    total24h: number;
    successRate: number;
    statusBreakdown: {
      succeeded: number;
      failed: number;
      running: number;
      pending: number;
    };
  };
  schedules: {
    total: number;
    active: number;
    failing: number;
    upcoming24h: number;
  };
  recentActivity: Array<{
    executionId: string;
    workflowName: string;
    instanceName: string;
    status: string;
    startedAt: string;
    completedAt?: string;
  }>;
}

const getStatusColor = (status: string) => {
  switch (status.toUpperCase()) {
    case 'SUCCEEDED':
    case 'COMPLETED':
      return 'text-green-600 bg-green-100';
    case 'FAILED':
      return 'text-red-600 bg-red-100';
    case 'RUNNING':
      return 'text-blue-600 bg-blue-100';
    case 'PENDING':
      return 'text-yellow-600 bg-yellow-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
};

const getStatusIcon = (status: string) => {
  switch (status.toUpperCase()) {
    case 'SUCCEEDED':
    case 'COMPLETED':
      return <CheckCircle className="w-4 h-4" />;
    case 'FAILED':
      return <XCircle className="w-4 h-4" />;
    case 'RUNNING':
      return <Loader className="w-4 h-4 animate-spin" />;
    case 'PENDING':
      return <Clock className="w-4 h-4" />;
    default:
      return <Activity className="w-4 h-4" />;
  }
};

export default function Dashboard() {
  const navigate = useNavigate();

  const { data: stats, isLoading, refetch, isFetching } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get('/stats');
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 60 * 1000, // Auto-refresh every minute
  });

  const hasRunningExecutions = stats?.executions?.statusBreakdown?.running && stats.executions.statusBreakdown.running > 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600">
            Overview of your Amazon Marketing Cloud resources
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center gap-3 text-gray-500">
            <Loader className="w-5 h-5 animate-spin" />
            Loading dashboard...
          </div>
        </div>
      ) : (
        <>
          {/* Primary Metrics Row */}
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {/* Active Instances */}
            <div
              onClick={() => navigate('/instances')}
              className="bg-white overflow-hidden shadow rounded-lg cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
                    <Database className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        AMC Instances
                      </dt>
                      <dd className="flex items-baseline">
                        <span className="text-2xl font-semibold text-gray-900">
                          {stats?.activeInstances || 0}
                        </span>
                        <span className="ml-2 text-sm text-gray-500">
                          / {stats?.totalInstances || 0} total
                        </span>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            {/* Executions Today */}
            <div
              onClick={() => navigate('/executions')}
              className="bg-white overflow-hidden shadow rounded-lg cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
                    <Activity className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Executions (24h)
                      </dt>
                      <dd className="flex items-baseline">
                        <span className="text-2xl font-semibold text-gray-900">
                          {stats?.executions?.total24h || 0}
                        </span>
                        {hasRunningExecutions && (
                          <span className="ml-2 flex items-center text-sm text-blue-600">
                            <Loader className="w-3 h-3 mr-1 animate-spin" />
                            {stats?.executions?.statusBreakdown?.running} running
                          </span>
                        )}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            {/* Success Rate */}
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className={`flex-shrink-0 rounded-md p-3 ${
                    (stats?.executions?.successRate || 0) >= 90 ? 'bg-green-500' :
                    (stats?.executions?.successRate || 0) >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}>
                    <TrendingUp className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Success Rate (7d)
                      </dt>
                      <dd className="flex items-baseline">
                        <span className="text-2xl font-semibold text-gray-900">
                          {stats?.executions?.successRate || 0}%
                        </span>
                        <span className="ml-2 text-sm text-gray-500">
                          of {stats?.executions?.total7d || 0} runs
                        </span>
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            {/* Active Schedules */}
            <div
              onClick={() => navigate('/schedules')}
              className="bg-white overflow-hidden shadow rounded-lg cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0 bg-purple-500 rounded-md p-3">
                    <Calendar className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Active Schedules
                      </dt>
                      <dd className="flex items-baseline">
                        <span className="text-2xl font-semibold text-gray-900">
                          {stats?.schedules?.active || 0}
                        </span>
                        {(stats?.schedules?.failing || 0) > 0 && (
                          <span className="ml-2 flex items-center text-sm text-red-600">
                            <AlertTriangle className="w-3 h-3 mr-1" />
                            {stats?.schedules?.failing} failing
                          </span>
                        )}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Secondary Row: Execution Status Breakdown + Upcoming Schedules */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Execution Status Breakdown */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium text-gray-900">Execution Status (7 days)</h2>
                <button
                  onClick={() => navigate('/executions')}
                  className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                >
                  View all <ArrowRight className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Succeeded */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-green-100">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700">Succeeded</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats?.executions?.statusBreakdown?.succeeded || 0}
                  </span>
                </div>

                {/* Failed */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-red-100">
                      <XCircle className="w-5 h-5 text-red-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700">Failed</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats?.executions?.statusBreakdown?.failed || 0}
                  </span>
                </div>

                {/* Running */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-blue-100">
                      <Loader className="w-5 h-5 text-blue-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700">Running</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats?.executions?.statusBreakdown?.running || 0}
                  </span>
                </div>

                {/* Pending */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-yellow-100">
                      <Clock className="w-5 h-5 text-yellow-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700">Pending</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats?.executions?.statusBreakdown?.pending || 0}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Actions / Schedule Summary */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium text-gray-900">Schedule Summary</h2>
                <button
                  onClick={() => navigate('/schedules')}
                  className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                >
                  Manage <ArrowRight className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-3xl font-bold text-gray-900">
                    {stats?.schedules?.total || 0}
                  </div>
                  <div className="text-sm text-gray-500">Total Schedules</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-3xl font-bold text-indigo-600">
                    {stats?.schedules?.upcoming24h || 0}
                  </div>
                  <div className="text-sm text-gray-500">Running in 24h</div>
                </div>
              </div>

              {/* Quick Navigation */}
              <div className="space-y-3">
                <button
                  onClick={() => navigate('/instances')}
                  className="w-full flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Play className="w-5 h-5 text-indigo-600" />
                    <span className="text-sm font-medium text-gray-700">Run a Template</span>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-400" />
                </button>

                <button
                  onClick={() => navigate('/executions')}
                  className="w-full flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Activity className="w-5 h-5 text-indigo-600" />
                    <span className="text-sm font-medium text-gray-700">View All Executions</span>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900">Recent Activity</h2>
              <button
                onClick={() => navigate('/executions')}
                className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
              >
                View all <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {stats?.recentActivity && stats.recentActivity.length > 0 ? (
              <div className="overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead>
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Workflow
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Instance
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Started
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {stats.recentActivity.map((activity, index) => (
                      <tr key={activity.executionId || index} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="text-sm font-medium text-gray-900">
                            {activity.workflowName}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="text-sm text-gray-500">
                            {activity.instanceName}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(activity.status)}`}>
                            {getStatusIcon(activity.status)}
                            {activity.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {activity.startedAt
                            ? formatDistanceToNow(new Date(activity.startedAt), { addSuffix: true })
                            : 'Unknown'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8">
                <Activity className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-500">No recent activity</p>
                <button
                  onClick={() => navigate('/instances')}
                  className="mt-3 text-sm text-indigo-600 hover:text-indigo-700"
                >
                  Run your first template
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
