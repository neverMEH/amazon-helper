import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  X,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Calendar,
  TrendingUp,
  Activity,
  BarChart3,
  Table
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { scheduleService } from '../../services/scheduleService';
import type { Schedule, ScheduleRun, ScheduleMetrics } from '../../types/schedule';

interface ScheduleHistoryProps {
  schedule: Schedule;
  onClose: () => void;
}

type ViewMode = 'timeline' | 'table' | 'metrics';

const ScheduleHistory: React.FC<ScheduleHistoryProps> = ({ schedule, onClose }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('timeline');
  const [selectedRun, setSelectedRun] = useState<ScheduleRun | null>(null);

  // Fetch schedule runs
  const { data: runs, isLoading: runsLoading } = useQuery({
    queryKey: ['schedule-runs', schedule.schedule_id],
    queryFn: () => scheduleService.getScheduleRuns(schedule.schedule_id, { limit: 30 }),
  });

  // Fetch schedule metrics
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['schedule-metrics', schedule.schedule_id],
    queryFn: () => scheduleService.getScheduleMetrics(schedule.schedule_id, 30),
    enabled: viewMode === 'metrics',
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'running':
        return <Activity className="w-4 h-4 text-blue-500 animate-pulse" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-gray-400" />;
      default:
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-50';
      case 'failed':
        return 'text-red-700 bg-red-50';
      case 'running':
        return 'text-blue-700 bg-blue-50';
      case 'pending':
        return 'text-gray-700 bg-gray-50';
      default:
        return 'text-yellow-700 bg-yellow-50';
    }
  };

  const calculateDuration = (run: ScheduleRun) => {
    if (!run.started_at || !run.completed_at) return null;
    const start = parseISO(run.started_at);
    const end = parseISO(run.completed_at);
    const seconds = Math.floor((end.getTime() - start.getTime()) / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const renderTimeline = () => (
    <div className="space-y-4">
      {runs?.map((run, index) => (
        <div key={run.id} className="relative">
          {index < (runs?.length || 0) - 1 && (
            <div className="absolute top-10 left-6 w-0.5 h-full bg-gray-200" />
          )}
          <div className="flex items-start">
            <div className="flex-shrink-0 w-12 flex justify-center">
              {getStatusIcon(run.status)}
            </div>
            <div
              className="flex-1 ml-4 bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setSelectedRun(run)}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-900">
                      Run #{run.run_number}
                    </span>
                    <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(run.status)}`}>
                      {run.status}
                    </span>
                  </div>
                  <div className="mt-1 text-sm text-gray-600">
                    Scheduled: {format(parseISO(run.scheduled_at), 'MMM d, yyyy h:mm a')}
                  </div>
                  {run.started_at && (
                    <div className="mt-1 text-sm text-gray-600">
                      Started: {format(parseISO(run.started_at), 'h:mm:ss a')}
                      {run.completed_at && ` • Duration: ${calculateDuration(run)}`}
                    </div>
                  )}
                </div>
                <div className="text-right">
                  {run.total_rows > 0 && (
                    <div className="text-sm text-gray-600">{run.total_rows.toLocaleString()} rows</div>
                  )}
                  {run.total_cost > 0 && (
                    <div className="text-sm text-gray-600">${run.total_cost.toFixed(2)}</div>
                  )}
                </div>
              </div>
              {run.error_summary && (
                <div className="mt-2 text-sm text-red-600 bg-red-50 rounded p-2">
                  {run.error_summary}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  const renderTable = () => (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Run #
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Scheduled
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Duration
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Rows
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Cost
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {runs?.map((run) => (
            <tr
              key={run.id}
              className="hover:bg-gray-50 cursor-pointer"
              onClick={() => setSelectedRun(run)}
            >
              <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                #{run.run_number}
              </td>
              <td className="px-4 py-3 whitespace-nowrap">
                <div className="flex items-center">
                  {getStatusIcon(run.status)}
                  <span className="ml-2 text-sm text-gray-900">{run.status}</span>
                </div>
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                {format(parseISO(run.scheduled_at), 'MMM d, h:mm a')}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                {calculateDuration(run) || '-'}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                {run.total_rows > 0 ? run.total_rows.toLocaleString() : '-'}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                {run.total_cost > 0 ? `$${run.total_cost.toFixed(2)}` : '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const renderMetrics = () => {
    if (metricsLoading) {
      return (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!metrics) return null;

    return (
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Runs</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.total_runs}</p>
              </div>
              <Activity className="w-8 h-8 text-gray-400" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">{metrics.success_rate}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-400" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Runtime</p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.avg_runtime_seconds
                    ? `${Math.round(metrics.avg_runtime_seconds / 60)}m`
                    : '-'}
                </p>
              </div>
              <Clock className="w-8 h-8 text-gray-400" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Cost</p>
                <p className="text-2xl font-bold text-gray-900">${metrics.total_cost.toFixed(2)}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-gray-400" />
            </div>
          </div>
        </div>

        {/* Detailed Stats */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h4 className="font-medium text-gray-900 mb-4">Execution Statistics</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-sm text-gray-600">Successful Runs</span>
              <span className="text-sm font-medium text-green-600">{metrics.successful_runs}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-sm text-gray-600">Failed Runs</span>
              <span className="text-sm font-medium text-red-600">{metrics.failed_runs}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-sm text-gray-600">Pending Runs</span>
              <span className="text-sm font-medium text-gray-600">{metrics.pending_runs}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-sm text-gray-600">Total Rows Processed</span>
              <span className="text-sm font-medium text-gray-900">
                {metrics.total_rows_processed.toLocaleString()}
              </span>
            </div>
            {metrics.next_run && (
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-sm text-gray-600">Next Run</span>
                <span className="text-sm font-medium text-blue-600">
                  {format(parseISO(metrics.next_run), 'MMM d, h:mm a')}
                </span>
              </div>
            )}
            {metrics.last_run && (
              <div className="flex justify-between items-center py-2">
                <span className="text-sm text-gray-600">Last Run</span>
                <span className="text-sm font-medium text-gray-900">
                  {format(parseISO(metrics.last_run), 'MMM d, h:mm a')}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Schedule History</h2>
            <p className="text-sm text-gray-600 mt-1">{schedule.workflows?.name}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* View Mode Tabs */}
        <div className="px-6 py-3 border-b flex space-x-4">
          <button
            onClick={() => setViewMode('timeline')}
            className={`px-3 py-1 rounded-lg text-sm font-medium ${
              viewMode === 'timeline'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Clock className="w-4 h-4 inline mr-2" />
            Timeline
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`px-3 py-1 rounded-lg text-sm font-medium ${
              viewMode === 'table'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Table className="w-4 h-4 inline mr-2" />
            Table
          </button>
          <button
            onClick={() => setViewMode('metrics')}
            className={`px-3 py-1 rounded-lg text-sm font-medium ${
              viewMode === 'metrics'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <BarChart3 className="w-4 h-4 inline mr-2" />
            Metrics
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {runsLoading && viewMode !== 'metrics' ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {viewMode === 'timeline' && renderTimeline()}
              {viewMode === 'table' && renderTable()}
              {viewMode === 'metrics' && renderMetrics()}
            </>
          )}

          {!runsLoading && runs?.length === 0 && viewMode !== 'metrics' && (
            <div className="text-center py-12">
              <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No execution history</h3>
              <p className="text-gray-600">This schedule hasn't run yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScheduleHistory;