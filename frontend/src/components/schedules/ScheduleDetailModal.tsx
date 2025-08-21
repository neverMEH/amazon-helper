import React, { useState } from 'react';
import {
  X,
  Save,
  Edit2,
  Power,
  Play,
  Trash2,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { formatInTimeZone } from 'date-fns-tz';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { scheduleService } from '../../services/scheduleService';
import type { Schedule } from '../../types/schedule';
import ScheduleHistory from './ScheduleHistory';

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
  const [showHistory, setShowHistory] = useState(false);
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
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-lg font-medium mb-2">Execution History</h3>
                <p className="text-sm text-gray-600 mb-4">
                  View detailed execution history and metrics for this schedule.
                </p>
                <button
                  onClick={() => setShowHistory(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  View Full History
                </button>
              </div>
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

      {/* Schedule History Modal - separate overlay */}
      {showHistory && (
        <ScheduleHistory
          schedule={schedule}
          onClose={() => setShowHistory(false)}
        />
      )}
    </div>
  );
};

export default ScheduleDetailModal;