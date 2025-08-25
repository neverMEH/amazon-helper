import React, { useState, useMemo } from 'react';
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
  Table,
  ExternalLink,
  Filter,
  Search,
  ChevronDown,
  XCircle as ClearIcon,
  ArrowUpDown,
  ArrowUp,
  ArrowDown
} from 'lucide-react';
import { format, parseISO, subDays, isAfter } from 'date-fns';
import { scheduleService } from '../../services/scheduleService';
import type { Schedule, ScheduleRun } from '../../types/schedule';
import AMCExecutionDetail from '../executions/AMCExecutionDetail';

interface ScheduleHistoryProps {
  schedule: Schedule;
  onClose: () => void;
}

type ViewMode = 'timeline' | 'table' | 'metrics';
type StatusFilter = 'all' | 'completed' | 'failed' | 'running' | 'pending';
type DateRangeFilter = 'all' | '7days' | '30days' | '90days';
type SortBy = 'lastRun' | 'scheduled' | 'runNumber' | 'duration' | 'cost' | 'status';
type SortOrder = 'asc' | 'desc';

const ScheduleHistory: React.FC<ScheduleHistoryProps> = ({ schedule: initialSchedule, onClose }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('timeline');
  const [selectedRun, setSelectedRun] = useState<ScheduleRun | null>(null);
  const [showExecutionDetail, setShowExecutionDetail] = useState(false);
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [dateRangeFilter, setDateRangeFilter] = useState<DateRangeFilter>('30days');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<SortBy>('lastRun');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // Fetch complete schedule data with all relations
  const { data: scheduleData } = useQuery({
    queryKey: ['schedule-detail', initialSchedule.schedule_id],
    queryFn: () => scheduleService.getSchedule(initialSchedule.schedule_id),
    initialData: initialSchedule,
  });

  // Use the fetched schedule data or fall back to initial
  const schedule = scheduleData || initialSchedule;

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

  // Filter and sort runs
  const filteredAndSortedRuns = useMemo(() => {
    if (!runs || !Array.isArray(runs)) return [];
    
    let filtered = [...runs];
    
    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(run => run.status === statusFilter);
    }
    
    // Apply date range filter
    if (dateRangeFilter !== 'all') {
      const now = new Date();
      let cutoffDate: Date;
      
      switch (dateRangeFilter) {
        case '7days':
          cutoffDate = subDays(now, 7);
          break;
        case '30days':
          cutoffDate = subDays(now, 30);
          break;
        case '90days':
          cutoffDate = subDays(now, 90);
          break;
        default:
          cutoffDate = new Date(0);
      }
      
      filtered = filtered.filter(run => {
        const runDate = run.started_at ? parseISO(run.started_at) : parseISO(run.scheduled_at);
        return isAfter(runDate, cutoffDate);
      });
    }
    
    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(run => 
        run.error_summary?.toLowerCase().includes(search) ||
        run.workflow_execution_id?.toLowerCase().includes(search) ||
        run.id.toLowerCase().includes(search)
      );
    }
    
    // Sort runs
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'lastRun': {
          // Use started_at if available, otherwise scheduled_at
          const dateA = a.started_at ? new Date(a.started_at).getTime() : new Date(a.scheduled_at).getTime();
          const dateB = b.started_at ? new Date(b.started_at).getTime() : new Date(b.scheduled_at).getTime();
          comparison = dateB - dateA;
          break;
        }
        case 'scheduled': {
          const dateA = new Date(a.scheduled_at).getTime();
          const dateB = new Date(b.scheduled_at).getTime();
          comparison = dateB - dateA;
          break;
        }
        case 'runNumber':
          comparison = b.run_number - a.run_number;
          break;
        case 'duration': {
          const durationA = a.started_at && a.completed_at ? 
            new Date(a.completed_at).getTime() - new Date(a.started_at).getTime() : 0;
          const durationB = b.started_at && b.completed_at ? 
            new Date(b.completed_at).getTime() - new Date(b.started_at).getTime() : 0;
          comparison = durationB - durationA;
          break;
        }
        case 'cost':
          comparison = b.total_cost - a.total_cost;
          break;
        case 'status': {
          const statusOrder = { completed: 0, running: 1, pending: 2, failed: 3, cancelled: 4 };
          comparison = (statusOrder[a.status] || 5) - (statusOrder[b.status] || 5);
          break;
        }
      }
      
      // Apply sort order
      return sortOrder === 'asc' ? -comparison : comparison;
    });
    
    return filtered;
  }, [runs, statusFilter, dateRangeFilter, searchTerm, sortBy, sortOrder]);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (statusFilter !== 'all') count++;
    if (dateRangeFilter !== '30days') count++;
    if (searchTerm) count++;
    if (sortBy !== 'lastRun' || sortOrder !== 'desc') count++;
    return count;
  }, [statusFilter, dateRangeFilter, searchTerm, sortBy, sortOrder]);

  const clearAllFilters = () => {
    setStatusFilter('all');
    setDateRangeFilter('30days');
    setSearchTerm('');
    setSortBy('lastRun');
    setSortOrder('desc');
  };

  const toggleSortOrder = () => {
    setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
  };

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

  const renderTimeline = () => {
    return (
      <div className="space-y-4">
        {filteredAndSortedRuns.map((run, index) => (
        <div key={run.id} className="relative">
          {index < filteredAndSortedRuns.length - 1 && (
            <div className="absolute top-10 left-6 w-0.5 h-full bg-gray-200" />
          )}
          <div className="flex items-start">
            <div className="flex-shrink-0 w-12 flex justify-center">
              {getStatusIcon(run.status)}
            </div>
            <div className="flex-1 ml-4 bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
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
              {run.workflow_execution_id && (
                <div className="mt-3 pt-3 border-t">
                  <button
                    onClick={() => {
                      setSelectedRun(run);
                      setShowExecutionDetail(true);
                    }}
                    className="flex items-center text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    <ExternalLink className="w-4 h-4 mr-1" />
                    View Execution Details
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
    );
  };

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
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {filteredAndSortedRuns.map((run) => (
            <tr
              key={run.id}
              className="hover:bg-gray-50"
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
              <td className="px-4 py-3 whitespace-nowrap">
                {run.workflow_execution_id && (
                  <button
                    onClick={() => {
                      setSelectedRun(run);
                      setShowExecutionDetail(true);
                    }}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </button>
                )}
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

        {/* Filters */}
        <div className="px-6 py-3 border-b bg-gray-50">
          <div className="flex flex-wrap items-center gap-3">
            {/* Status Filter */}
            <div className="relative">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="running">Running</option>
                <option value="pending">Pending</option>
              </select>
              <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>

            {/* Date Range Filter */}
            <div className="relative">
              <select
                value={dateRangeFilter}
                onChange={(e) => setDateRangeFilter(e.target.value as DateRangeFilter)}
                className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Time</option>
                <option value="7days">Last 7 Days</option>
                <option value="30days">Last 30 Days</option>
                <option value="90days">Last 90 Days</option>
              </select>
              <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>

            {/* Sort Options */}
            <div className="flex items-center gap-2">
              <div className="relative">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortBy)}
                  className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="lastRun">Last Run</option>
                  <option value="scheduled">Scheduled Date</option>
                  <option value="runNumber">Run Number</option>
                  <option value="duration">Duration</option>
                  <option value="cost">Cost</option>
                  <option value="status">Status</option>
                </select>
                <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
              <button
                onClick={toggleSortOrder}
                className="p-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                title={sortOrder === 'desc' ? 'Sort Ascending' : 'Sort Descending'}
              >
                {sortOrder === 'desc' ? (
                  <ArrowDown className="w-4 h-4 text-gray-600" />
                ) : (
                  <ArrowUp className="w-4 h-4 text-gray-600" />
                )}
              </button>
            </div>

            {/* Search */}
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search errors, IDs..."
                className="w-full pl-10 pr-4 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Clear Filters */}
            {activeFilterCount > 0 && (
              <button
                onClick={clearAllFilters}
                className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <ClearIcon className="w-4 h-4" />
                Clear Filters
                {activeFilterCount > 0 && (
                  <span className="ml-1 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
                    {activeFilterCount}
                  </span>
                )}
              </button>
            )}
          </div>
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

          {!runsLoading && filteredAndSortedRuns.length === 0 && viewMode !== 'metrics' && (
            <div className="text-center py-12">
              <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {runs && runs.length > 0 ? 'No matching runs' : 'No execution history'}
              </h3>
              <p className="text-gray-600">
                {runs && runs.length > 0 
                  ? 'Try adjusting your filters to see more results' 
                  : "This schedule hasn't run yet"}
              </p>
              {activeFilterCount > 0 && runs && runs.length > 0 && (
                <button
                  onClick={clearAllFilters}
                  className="mt-4 px-4 py-2 text-sm text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100"
                >
                  Clear all filters
                </button>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Execution Detail Modal */}
      {showExecutionDetail && selectedRun?.workflow_execution_id && (() => {
        // Try multiple ways to get the instance_id
        let instanceId = null;
        
        // Method 1: From nested amc_instances relation
        if (schedule.workflows?.amc_instances?.instance_id) {
          instanceId = schedule.workflows.amc_instances.instance_id;
        }
        // Method 2: If workflows has instance_id directly (though this would be a UUID)
        // We might need to fetch the actual instance_id from somewhere else
        
        // Debug logging
        console.log('Schedule data:', schedule);
        console.log('Workflow data:', schedule.workflows);
        console.log('Instance ID found:', instanceId);
        
        if (instanceId) {
          return (
            <AMCExecutionDetail
              instanceId={instanceId}
              executionId={selectedRun.workflow_execution_id}
              isOpen={showExecutionDetail}
              onClose={() => {
                setShowExecutionDetail(false);
                setSelectedRun(null);
              }}
            />
          );
        } else {
          // Fallback: If we can't find the instance ID
          return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg p-6 max-w-md">
                <h3 className="text-lg font-semibold mb-2">Unable to Load Execution Details</h3>
                <p className="text-gray-600 mb-4">
                  The AMC instance information is not available. Please try refreshing the page or contact support if the issue persists.
                </p>
                <div className="text-xs text-gray-500 mb-4">
                  Debug: workflow_id={schedule.workflows?.workflow_id || 'N/A'}, 
                  has_instance={!!schedule.workflows?.amc_instances ? 'yes' : 'no'}
                </div>
                <button
                  onClick={() => {
                    setShowExecutionDetail(false);
                    setSelectedRun(null);
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Close
                </button>
              </div>
            </div>
          );
        }
      })()}
    </div>
  );
};

export default ScheduleHistory;