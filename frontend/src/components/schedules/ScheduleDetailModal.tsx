import React, { useState } from 'react';
import {
  X,
  Save,
  Edit2,
  Power,
  Play,
  Trash2,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  ExternalLink,
  AlertCircle,
  TrendingUp,
  BarChart3
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { formatInTimeZone } from 'date-fns-tz';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { scheduleService } from '../../services/scheduleService';
import type { Schedule, ScheduleRun } from '../../types/schedule';
import AMCExecutionDetail from '../executions/AMCExecutionDetail';

interface ScheduleDetailModalProps {
  schedule: Schedule;
  onClose: () => void;
  onUpdate?: (schedule: Schedule) => void;
  onDelete?: (scheduleId: string) => void;
}

const ScheduleDetailModal: React.FC<ScheduleDetailModalProps> = ({
  schedule,
  onClose,
  onUpdate,
  onDelete
}) => {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState<'details' | 'history' | 'settings'>('details');
  const [selectedRun, setSelectedRun] = useState<ScheduleRun | null>(null);
  const [showExecutionDetail, setShowExecutionDetail] = useState(false);
  const [editData, setEditData] = useState({
    name: schedule.name || schedule.workflows?.name || '',
    description: schedule.description || '',
    cron_expression: schedule.cron_expression,
    timezone: schedule.timezone,
    default_parameters: schedule.default_parameters || {},
    notification_config: schedule.notification_config || {
      on_success: false,
      on_failure: true,
      email: ''
    },
    is_active: schedule.is_active,
    auto_pause_on_failure: schedule.auto_pause_on_failure || false,
    failure_threshold: schedule.failure_threshold || 3,
    cost_limit: schedule.cost_limit || undefined
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async () => {
      return await scheduleService.updateSchedule(schedule.schedule_id, editData);
    },
    onSuccess: (updatedSchedule) => {
      toast.success('Schedule updated successfully');
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      setIsEditing(false);
      if (onUpdate) {
        onUpdate(updatedSchedule);
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update schedule');
    }
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      return await scheduleService.deleteSchedule(schedule.schedule_id);
    },
    onSuccess: () => {
      toast.success('Schedule deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      if (onDelete) {
        onDelete(schedule.schedule_id);
      }
      onClose();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete schedule');
    }
  });

  // Fetch schedule runs
  const { data: runs, isLoading: runsLoading } = useQuery({
    queryKey: ['schedule-runs', schedule.schedule_id],
    queryFn: () => scheduleService.getScheduleRuns(schedule.schedule_id, { limit: 30 }),
    enabled: activeTab === 'history',
  });

  // Fetch schedule metrics
  const { data: metrics } = useQuery({
    queryKey: ['schedule-metrics', schedule.schedule_id],
    queryFn: () => scheduleService.getScheduleMetrics(schedule.schedule_id, 30),
    enabled: activeTab === 'history',
  });

  // Test run mutation
  const testRunMutation = useMutation({
    mutationFn: async () => {
      return await scheduleService.testRun(schedule.schedule_id, editData.default_parameters);
    },
    onSuccess: () => {
      toast.success('Test run initiated successfully');
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      queryClient.invalidateQueries({ queryKey: ['schedule-runs', schedule.schedule_id] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to initiate test run');
    }
  });

  // Toggle active status
  const toggleActiveMutation = useMutation({
    mutationFn: async () => {
      if (schedule.is_active) {
        return await scheduleService.disableSchedule(schedule.schedule_id);
      } else {
        return await scheduleService.enableSchedule(schedule.schedule_id);
      }
    },
    onSuccess: () => {
      toast.success(schedule.is_active ? 'Schedule disabled' : 'Schedule enabled');
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      schedule.is_active = !schedule.is_active;
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to toggle schedule status');
    }
  });

  const handleSave = () => {
    updateMutation.mutate();
  };

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this schedule? This action cannot be undone.')) {
      deleteMutation.mutate();
    }
  };

  const getScheduleTypeLabel = () => {
    switch (schedule.schedule_type) {
      case 'daily':
        return 'Daily';
      case 'interval':
        return `Every ${schedule.interval_days} days`;
      case 'weekly':
        return 'Weekly';
      case 'monthly':
        return 'Monthly';
      case 'custom':
        return 'Custom';
      default:
        return schedule.schedule_type;
    }
  };

  const parseParameters = (params: any) => {
    if (typeof params === 'string') {
      try {
        return JSON.parse(params);
      } catch {
        return {};
      }
    }
    return params || {};
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold">
              {schedule.name || schedule.workflows?.name || 'Schedule Details'}
            </h2>
            <div className="flex items-center space-x-2">
              {schedule.is_active ? (
                <span className="flex items-center text-green-600 text-sm">
                  <CheckCircle className="w-4 h-4 mr-1" />
                  Active
                </span>
              ) : (
                <span className="flex items-center text-gray-500 text-sm">
                  <XCircle className="w-4 h-4 mr-1" />
                  Inactive
                </span>
              )}
              <span className="text-sm text-gray-500">
                ID: {schedule.schedule_id}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <div className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('details')}
              className={`py-3 border-b-2 transition-colors ${
                activeTab === 'details'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Details
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`py-3 border-b-2 transition-colors ${
                activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Execution History
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`py-3 border-b-2 transition-colors ${
                activeTab === 'settings'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Settings
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'details' && (
            <div className="space-y-6">
              {/* Schedule Name and Description */}
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Schedule Name
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={editData.name}
                      onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="Enter a name for this schedule"
                    />
                  ) : (
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="font-medium">
                        {schedule.name || schedule.workflows?.name + ' Schedule' || 'Unnamed Schedule'}
                      </div>
                    </div>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description / Notes
                  </label>
                  {isEditing ? (
                    <textarea
                      value={editData.description}
                      onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      rows={3}
                      placeholder="Add any notes or description about this schedule..."
                    />
                  ) : (
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-gray-600">
                        {schedule.description || 'No description provided'}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Brand Associations */}
              <div>
                <h3 className="text-lg font-medium mb-3">Associated Brands</h3>
                <div className="flex flex-wrap gap-2">
                  {schedule.workflows?.amc_instances?.brands && schedule.workflows.amc_instances.brands.length > 0 ? (
                    schedule.workflows.amc_instances.brands.map((brand) => (
                      <span
                        key={brand}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                      >
                        {brand}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-500 text-sm">No brands associated</span>
                  )}
                </div>
              </div>

              {/* Workflow Info */}
              <div>
                <h3 className="text-lg font-medium mb-3">Workflow</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="font-medium">{schedule.workflows?.name || 'Unknown Workflow'}</div>
                  <div className="text-sm text-gray-500 mt-1">
                    ID: {schedule.workflows?.workflow_id || schedule.workflow_id}
                  </div>
                  {schedule.workflows?.amc_instances && (
                    <div className="text-sm text-gray-500 mt-1">
                      Instance: {schedule.workflows.amc_instances.instance_name || schedule.workflows.amc_instances.instance_id}
                    </div>
                  )}
                </div>
              </div>

              {/* Schedule Configuration */}
              <div>
                <h3 className="text-lg font-medium mb-3">Schedule Configuration</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Schedule Type
                    </label>
                    <div className="bg-gray-50 rounded-lg p-3">
                      {getScheduleTypeLabel()}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Timezone
                    </label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editData.timezone}
                        onChange={(e) => setEditData({ ...editData, timezone: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    ) : (
                      <div className="bg-gray-50 rounded-lg p-3">
                        {schedule.timezone}
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      CRON Expression
                    </label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editData.cron_expression}
                        onChange={(e) => setEditData({ ...editData, cron_expression: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"
                      />
                    ) : (
                      <div className="bg-gray-50 rounded-lg p-3 font-mono text-sm">
                        {schedule.cron_expression}
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Next Run
                    </label>
                    <div className="bg-gray-50 rounded-lg p-3">
                      {schedule.next_run_at ? (
                        <div>
                          <div>{format(parseISO(schedule.next_run_at), 'PPpp')}</div>
                          <div className="text-xs text-gray-500">
                            {formatInTimeZone(parseISO(schedule.next_run_at), schedule.timezone, 'PPpp')} ({schedule.timezone})
                          </div>
                        </div>
                      ) : (
                        'Not scheduled'
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Parameters */}
              <div>
                <h3 className="text-lg font-medium mb-3">Default Parameters</h3>
                {isEditing ? (
                  <textarea
                    value={JSON.stringify(editData.default_parameters, null, 2)}
                    onChange={(e) => {
                      try {
                        const params = JSON.parse(e.target.value);
                        setEditData({ ...editData, default_parameters: params });
                      } catch {
                        // Invalid JSON, don't update
                      }
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"
                    rows={6}
                  />
                ) : (
                  <pre className="bg-gray-50 rounded-lg p-4 text-sm overflow-x-auto">
                    {JSON.stringify(parseParameters(schedule.default_parameters), null, 2)}
                  </pre>
                )}
              </div>

              {/* Statistics */}
              <div>
                <h3 className="text-lg font-medium mb-3">Statistics</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-500">Last Run</div>
                    <div className="font-medium mt-1">
                      {schedule.last_run_at
                        ? format(parseISO(schedule.last_run_at), 'PPp')
                        : 'Never'
                      }
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-500">Consecutive Failures</div>
                    <div className="font-medium mt-1">
                      {schedule.consecutive_failures || 0}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-500">Created</div>
                    <div className="font-medium mt-1">
                      {format(parseISO(schedule.created_at), 'PP')}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="space-y-6">
              {/* Metrics Summary */}
              {metrics && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
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
              )}

              {/* Execution History Table */}
              <div>
                <h3 className="text-lg font-medium mb-3">Recent Executions</h3>
                {runsLoading ? (
                  <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                ) : runs && runs.length > 0 ? (
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
                        {runs.map((run: ScheduleRun) => (
                          <tr key={run.id} className="hover:bg-gray-50">
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
                                  className="text-blue-600 hover:text-blue-800 flex items-center"
                                  title="View execution details"
                                >
                                  <ExternalLink className="w-4 h-4" />
                                  <span className="ml-1 text-sm">View</span>
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-8 bg-gray-50 rounded-lg">
                    <Clock className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600">No execution history yet</p>
                    <p className="text-sm text-gray-500 mt-1">This schedule hasn't run yet</p>
                  </div>
                )}
              </div>

              {/* Error Summary if there are recent failures */}
              {runs && runs.filter((r: ScheduleRun) => r.status === 'failed' && r.error_summary).length > 0 && (
                <div>
                  <h3 className="text-lg font-medium mb-3">Recent Errors</h3>
                  <div className="space-y-2">
                    {runs
                      .filter((r: ScheduleRun) => r.status === 'failed' && r.error_summary)
                      .slice(0, 3)
                      .map((run: ScheduleRun) => (
                        <div key={run.id} className="bg-red-50 border border-red-200 rounded-lg p-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="text-sm font-medium text-red-900">
                                Run #{run.run_number} - {format(parseISO(run.scheduled_at), 'MMM d, h:mm a')}
                              </div>
                              <div className="text-sm text-red-700 mt-1">
                                {run.error_summary}
                              </div>
                            </div>
                            {run.workflow_execution_id && (
                              <button
                                onClick={() => {
                                  setSelectedRun(run);
                                  setShowExecutionDetail(true);
                                }}
                                className="ml-3 text-red-600 hover:text-red-800"
                              >
                                <ExternalLink className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              {/* Notifications */}
              <div>
                <h3 className="text-lg font-medium mb-3">Notifications</h3>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editData.notification_config.on_success}
                      onChange={(e) => setEditData({
                        ...editData,
                        notification_config: {
                          ...editData.notification_config,
                          on_success: e.target.checked
                        }
                      })}
                      disabled={!isEditing}
                      className="mr-3"
                    />
                    <span>Notify on successful execution</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editData.notification_config.on_failure}
                      onChange={(e) => setEditData({
                        ...editData,
                        notification_config: {
                          ...editData.notification_config,
                          on_failure: e.target.checked
                        }
                      })}
                      disabled={!isEditing}
                      className="mr-3"
                    />
                    <span>Notify on failed execution</span>
                  </label>
                  {(editData.notification_config.on_success || editData.notification_config.on_failure) && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Email Address
                      </label>
                      <input
                        type="email"
                        value={editData.notification_config.email || ''}
                        onChange={(e) => setEditData({
                          ...editData,
                          notification_config: {
                            ...editData.notification_config,
                            email: e.target.value
                          }
                        })}
                        disabled={!isEditing}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        placeholder="email@example.com"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Failure Handling */}
              <div>
                <h3 className="text-lg font-medium mb-3">Failure Handling</h3>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editData.auto_pause_on_failure}
                      onChange={(e) => setEditData({
                        ...editData,
                        auto_pause_on_failure: e.target.checked
                      })}
                      disabled={!isEditing}
                      className="mr-3"
                    />
                    <span>Auto-pause after consecutive failures</span>
                  </label>
                  {editData.auto_pause_on_failure && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Failure Threshold
                      </label>
                      <input
                        type="number"
                        value={editData.failure_threshold}
                        onChange={(e) => setEditData({
                          ...editData,
                          failure_threshold: parseInt(e.target.value) || 3
                        })}
                        disabled={!isEditing}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        min="1"
                        max="10"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Cost Limit */}
              <div>
                <h3 className="text-lg font-medium mb-3">Cost Management</h3>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cost Limit (USD)
                  </label>
                  <input
                    type="number"
                    value={editData.cost_limit || ''}
                    onChange={(e) => setEditData({
                      ...editData,
                      cost_limit: e.target.value ? parseFloat(e.target.value) : undefined
                    })}
                    disabled={!isEditing}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="No limit"
                    step="0.01"
                    min="0"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Schedule will pause if execution cost exceeds this limit
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => toggleActiveMutation.mutate()}
              disabled={toggleActiveMutation.isPending}
              className={`px-4 py-2 rounded-lg flex items-center space-x-2 ${
                schedule.is_active
                  ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                  : 'bg-green-100 text-green-700 hover:bg-green-200'
              }`}
            >
              <Power className="w-4 h-4" />
              <span>{schedule.is_active ? 'Disable' : 'Enable'}</span>
            </button>
            <button
              onClick={() => testRunMutation.mutate()}
              disabled={testRunMutation.isPending}
              className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 flex items-center space-x-2"
            >
              <Play className="w-4 h-4" />
              <span>Test Run</span>
            </button>
            <button
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 flex items-center space-x-2"
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete</span>
            </button>
          </div>
          <div className="flex items-center space-x-2">
            {isEditing ? (
              <>
                <button
                  onClick={() => {
                    setIsEditing(false);
                    // Reset edit data
                    setEditData({
                      name: schedule.name || schedule.workflows?.name || '',
                      description: schedule.description || '',
                      cron_expression: schedule.cron_expression,
                      timezone: schedule.timezone,
                      default_parameters: schedule.default_parameters || {},
                      notification_config: schedule.notification_config || {
                        on_success: false,
                        on_failure: true,
                        email: ''
                      },
                      is_active: schedule.is_active,
                      auto_pause_on_failure: schedule.auto_pause_on_failure || false,
                      failure_threshold: schedule.failure_threshold || 3,
                      cost_limit: schedule.cost_limit || undefined
                    });
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={updateMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
                >
                  <Save className="w-4 h-4" />
                  <span>Save Changes</span>
                </button>
              </>
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
              >
                <Edit2 className="w-4 h-4" />
                <span>Edit</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Execution Detail Modal */}
      {showExecutionDetail && selectedRun?.workflow_execution_id && (() => {
        // Get instance_id from the workflow's amc_instances relation
        const instanceId = schedule.workflows?.amc_instances?.instance_id;
        
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
          // Fallback if instance ID is not available
          return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60">
              <div className="bg-white rounded-lg p-6 max-w-md">
                <h3 className="text-lg font-semibold mb-2">Unable to Load Execution Details</h3>
                <p className="text-gray-600 mb-4">
                  The AMC instance information is not available. Please try refreshing the page.
                </p>
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

export default ScheduleDetailModal;