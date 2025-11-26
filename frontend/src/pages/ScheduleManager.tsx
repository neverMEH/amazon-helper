import React, { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Calendar,
  Clock,
  Power,
  PowerOff,
  Play,
  Trash2,
  ChevronRight,
  CheckCircle,
  XCircle,
  Grid3x3,
  List,
  CalendarDays,
  RefreshCw,
  Loader,
  Activity,
  Timer,
  Search,
  X,
  Database
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { format, parseISO } from 'date-fns';
import { scheduleService } from '../services/scheduleService';
import type { Schedule } from '../types/schedule';
import ScheduleDetailModal from '../components/schedules/ScheduleDetailModal';
import ScheduleRunModal from '../components/schedules/ScheduleRunModal';

type ViewMode = 'grid' | 'list' | 'calendar';

const ScheduleManager: React.FC = () => {
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showScheduleRunModal, setShowScheduleRunModal] = useState(false);
  const [filterActive, setFilterActive] = useState<boolean | null>(null);
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);
  const [hasRecentActivity, setHasRecentActivity] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedInstance, setSelectedInstance] = useState<string | null>(null);

  // Fetch schedules with auto-refresh
  const { data: schedules, isLoading, refetch } = useQuery({
    queryKey: ['schedules', filterActive],
    queryFn: () => scheduleService.listAllSchedules({ is_active: filterActive ?? undefined }),
    // Auto-refresh every 10 seconds if there's recent activity
    refetchInterval: hasRecentActivity ? 10000 : false,
    refetchIntervalInBackground: false,
  });

  // Check for recent activity (test runs or executions in last 5 minutes)
  useEffect(() => {
    if (!schedules) return;
    
    const hasRecent = schedules.some((schedule: Schedule) => {
      // Check if there's a next_run_at in the near future (test run)
      if (schedule.next_run_at) {
        const nextRun = new Date(schedule.next_run_at).getTime();
        const fiveMinutesFromNow = Date.now() + (5 * 60 * 1000);
        if (nextRun <= fiveMinutesFromNow && nextRun > Date.now()) {
          return true;
        }
      }
      
      // Check if last run was recent
      if (schedule.last_run_at) {
        const lastRun = new Date(schedule.last_run_at).getTime();
        const fiveMinutesAgo = Date.now() - (5 * 60 * 1000);
        return lastRun > fiveMinutesAgo;
      }
      
      return false;
    });
    
    setHasRecentActivity(hasRecent);
  }, [schedules]);

  // Extract unique instances from schedules for filtering tabs
  const uniqueInstances = useMemo(() => {
    if (!schedules) return [];
    const instanceMap = new Map<string, { instanceId: string; instanceName: string; brands: string[] }>();

    schedules.forEach((schedule: Schedule) => {
      const instance = schedule.workflows?.amc_instances;
      if (instance?.instance_id) {
        if (!instanceMap.has(instance.instance_id)) {
          instanceMap.set(instance.instance_id, {
            instanceId: instance.instance_id,
            instanceName: instance.instance_name || instance.instance_id,
            brands: instance.brands || [],
          });
        }
      }
    });

    return Array.from(instanceMap.values()).sort((a, b) =>
      a.instanceName.localeCompare(b.instanceName)
    );
  }, [schedules]);

  // Filter schedules based on search query and selected instance
  const filteredSchedules = useMemo(() => {
    if (!schedules) return [];

    return schedules.filter((schedule: Schedule) => {
      // Filter by search query
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const name = (schedule.name || schedule.workflows?.name || '').toLowerCase();
        const description = (schedule.description || '').toLowerCase();
        const instanceName = (schedule.workflows?.amc_instances?.instance_name || '').toLowerCase();
        const brands = (schedule.workflows?.amc_instances?.brands || []).join(' ').toLowerCase();

        if (!name.includes(query) &&
            !description.includes(query) &&
            !instanceName.includes(query) &&
            !brands.includes(query)) {
          return false;
        }
      }

      // Filter by selected instance
      if (selectedInstance) {
        const instanceId = schedule.workflows?.amc_instances?.instance_id;
        if (instanceId !== selectedInstance) {
          return false;
        }
      }

      return true;
    });
  }, [schedules, searchQuery, selectedInstance]);

  // Manual refresh function
  const handleManualRefresh = async () => {
    setIsManualRefreshing(true);
    try {
      await queryClient.invalidateQueries({ queryKey: ['schedules'] });
      await refetch();
    } finally {
      setIsManualRefreshing(false);
    }
  };

  // Enable/disable mutation
  const toggleScheduleMutation = useMutation({
    mutationFn: async ({ scheduleId, enable }: { scheduleId: string; enable: boolean }) => {
      if (enable) {
        await scheduleService.enableSchedule(scheduleId);
      } else {
        await scheduleService.disableSchedule(scheduleId);
      }
    },
    onSuccess: (_, { enable }) => {
      toast.success(`Schedule ${enable ? 'enabled' : 'disabled'} successfully`);
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update schedule');
    },
  });

  // Delete mutation
  const deleteScheduleMutation = useMutation({
    mutationFn: scheduleService.deleteSchedule,
    onSuccess: () => {
      toast.success('Schedule deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      setSelectedSchedule(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete schedule');
    },
  });

  // Test run mutation
  const testRunMutation = useMutation({
    mutationFn: (scheduleId: string) => scheduleService.testRun(scheduleId),
    onSuccess: (data) => {
      const scheduledTime = new Date(data.scheduled_at);
      toast.success(
        `Test run scheduled for ${format(scheduledTime, 'h:mm:ss a')} (in about 1 minute)`,
        { duration: 5000 }
      );
      // Set recent activity flag to enable auto-refresh
      setHasRecentActivity(true);
      // Also refresh immediately to show the pending test run
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      // Refresh schedules after 65 seconds to show updated next_run_at
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['schedules'] });
      }, 65000);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to schedule test run');
    },
  });

  // Schedule run mutation
  const scheduleRunMutation = useMutation({
    mutationFn: ({ scheduleId, scheduledTime }: { scheduleId: string; scheduledTime: Date }) => 
      scheduleService.scheduleRunAtTime(scheduleId, scheduledTime),
    onSuccess: (data) => {
      const scheduledTime = new Date(data.scheduled_at);
      toast.success(
        `Run scheduled for ${format(scheduledTime, 'MMM d, h:mm a')}`,
        { duration: 5000 }
      );
      // Set recent activity flag to enable auto-refresh
      setHasRecentActivity(true);
      // Refresh schedules to show the pending run
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      setShowScheduleRunModal(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to schedule run');
    },
  });

  const getStatusIcon = (schedule: Schedule) => {
    if (!schedule.is_active) {
      return <PowerOff className="w-4 h-4 text-gray-400" />;
    }
    if (schedule.consecutive_failures >= 3) {
      return <XCircle className="w-4 h-4 text-red-500" />;
    }
    return <CheckCircle className="w-4 h-4 text-green-500" />;
  };

  const getStatusText = (schedule: Schedule) => {
    if (!schedule.is_active) return 'Disabled';
    if (schedule.consecutive_failures >= 3) return 'Failed';
    return 'Active';
  };

  const renderGridView = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {filteredSchedules.map((schedule) => (
        <div
          key={schedule.id}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
          onClick={() => {
            setSelectedSchedule(schedule);
            setShowDetailModal(true);
          }}
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center">
              {getStatusIcon(schedule)}
              <span className={`ml-2 text-sm font-medium ${
                schedule.is_active ? 'text-gray-900' : 'text-gray-500'
              }`}>
                {getStatusText(schedule)}
              </span>
            </div>
            <div className="flex space-x-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleScheduleMutation.mutate({
                    scheduleId: schedule.schedule_id,
                    enable: !schedule.is_active,
                  });
                }}
                className="p-1 hover:bg-gray-100 rounded"
                title={schedule.is_active ? 'Disable schedule' : 'Enable schedule'}
              >
                <Power className="w-4 h-4 text-gray-600" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  testRunMutation.mutate(schedule.schedule_id);
                }}
                className="p-1 hover:bg-gray-100 rounded"
                title="Quick test (runs in 1 minute)"
              >
                <Play className="w-4 h-4 text-gray-600" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedSchedule(schedule);
                  setShowScheduleRunModal(true);
                }}
                className="p-1 hover:bg-gray-100 rounded"
                title="Schedule run today"
              >
                <Timer className="w-4 h-4 text-gray-600" />
              </button>
            </div>
          </div>

          <h3 className="font-medium text-gray-900 mb-1">
            {schedule.name || schedule.workflows?.name || 'Unnamed Schedule'}
          </h3>
          
          {schedule.description && (
            <p className="text-xs text-gray-500 mb-2 line-clamp-2">
              {schedule.description}
            </p>
          )}
          
          {schedule.workflows?.amc_instances?.brands && schedule.workflows.amc_instances.brands.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {schedule.workflows.amc_instances.brands.slice(0, 2).map((brand) => (
                <span
                  key={brand}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700"
                >
                  {brand}
                </span>
              ))}
              {schedule.workflows.amc_instances.brands.length > 2 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                  +{schedule.workflows.amc_instances.brands.length - 2}
                </span>
              )}
            </div>
          )}

          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex items-center">
              <Calendar className="w-4 h-4 mr-2" />
              {scheduleService.parseCronExpression(schedule.cron_expression)}
            </div>
            <div className="flex items-center">
              <Clock className="w-4 h-4 mr-2" />
              {schedule.timezone}
            </div>
            {schedule.next_run_at && (
              <div className="flex items-center text-blue-600">
                <ChevronRight className="w-4 h-4 mr-2" />
                Next: {format(parseISO(schedule.next_run_at), 'MMM d, h:mm a')}
              </div>
            )}
          </div>

          {schedule.last_run_at && (
            <div className="mt-3 pt-3 border-t text-xs text-gray-500">
              Last run: {format(parseISO(schedule.last_run_at), 'MMM d, h:mm a')}
            </div>
          )}
        </div>
      ))}
    </div>
  );

  const renderListView = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Workflow
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Schedule
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Next Run
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Last Run
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {filteredSchedules.map((schedule) => (
            <tr
              key={schedule.id}
              className="hover:bg-gray-50 cursor-pointer"
              onClick={() => {
                setSelectedSchedule(schedule);
                setShowDetailModal(true);
              }}
            >
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  {getStatusIcon(schedule)}
                  <span className="ml-2 text-sm text-gray-900">{getStatusText(schedule)}</span>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {schedule.name || schedule.workflows?.name || 'Unnamed Schedule'}
                  </div>
                  {schedule.description && (
                    <div className="text-xs text-gray-500 truncate max-w-xs">
                      {schedule.description}
                    </div>
                  )}
                  {schedule.workflows?.amc_instances?.brands && schedule.workflows.amc_instances.brands.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {schedule.workflows.amc_instances.brands.slice(0, 3).map((brand) => (
                        <span
                          key={brand}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700"
                        >
                          {brand}
                        </span>
                      ))}
                      {schedule.workflows.amc_instances.brands.length > 3 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                          +{schedule.workflows.amc_instances.brands.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                {scheduleService.parseCronExpression(schedule.cron_expression)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                {schedule.next_run_at
                  ? format(parseISO(schedule.next_run_at), 'MMM d, h:mm a')
                  : '-'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                {schedule.last_run_at
                  ? format(parseISO(schedule.last_run_at), 'MMM d, h:mm a')
                  : 'Never'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <div className="flex space-x-2" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => toggleScheduleMutation.mutate({
                      scheduleId: schedule.schedule_id,
                      enable: !schedule.is_active,
                    })}
                    className="text-gray-600 hover:text-gray-900"
                    title={schedule.is_active ? 'Disable' : 'Enable'}
                  >
                    <Power className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => testRunMutation.mutate(schedule.schedule_id)}
                    className="text-gray-600 hover:text-gray-900"
                    title="Quick test"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      setSelectedSchedule(schedule);
                      setShowScheduleRunModal(true);
                    }}
                    className="text-gray-600 hover:text-gray-900"
                    title="Schedule run"
                  >
                    <Timer className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Are you sure you want to delete this schedule?')) {
                        deleteScheduleMutation.mutate(schedule.schedule_id);
                      }
                    }}
                    className="text-red-600 hover:text-red-900"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Schedule Manager</h1>
          <p className="text-gray-600 mt-1">Manage your workflow schedules and execution history</p>
        </div>
        <div className="flex items-center gap-3">
          {hasRecentActivity && (
            <span className="flex items-center text-xs text-green-600 bg-green-50 px-2 py-1 rounded-md">
              <Activity className="w-3 h-3 mr-1 animate-pulse" />
              Auto-refreshing
            </span>
          )}
          <button
            onClick={handleManualRefresh}
            disabled={isManualRefreshing}
            className="flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Refresh schedules"
          >
            {isManualRefreshing ? (
              <Loader className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-4 flex flex-col sm:flex-row gap-4">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search schedules..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Status Filters and View Mode */}
        <div className="flex items-center justify-between sm:justify-end gap-4 flex-wrap">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setFilterActive(null)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                filterActive === null
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterActive(true)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                filterActive === true
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Active
            </button>
            <button
              onClick={() => setFilterActive(false)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                filterActive === false
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Inactive
            </button>
          </div>

          <div className="flex items-center space-x-1 border-l pl-4">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-gray-200' : 'hover:bg-gray-100'}`}
              title="Grid view"
            >
              <Grid3x3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${viewMode === 'list' ? 'bg-gray-200' : 'hover:bg-gray-100'}`}
              title="List view"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Instance Tabs */}
      {uniqueInstances.length > 0 && (
        <div className="mb-6 overflow-x-auto">
          <div className="flex items-center space-x-2 pb-2">
            <button
              onClick={() => setSelectedInstance(null)}
              className={`flex items-center px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                selectedInstance === null
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Database className="w-3.5 h-3.5 mr-1.5" />
              All Instances
              <span className="ml-1.5 px-1.5 py-0.5 rounded text-xs bg-opacity-20 bg-white">
                {schedules?.length || 0}
              </span>
            </button>
            {uniqueInstances.map((instance) => {
              const instanceScheduleCount = schedules?.filter(
                (s) => s.workflows?.amc_instances?.instance_id === instance.instanceId
              ).length || 0;

              return (
                <button
                  key={instance.instanceId}
                  onClick={() => setSelectedInstance(instance.instanceId)}
                  className={`flex items-center px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                    selectedInstance === instance.instanceId
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {instance.instanceName}
                  {instance.brands.length > 0 && (
                    <span className={`ml-1.5 text-xs ${
                      selectedInstance === instance.instanceId ? 'text-blue-200' : 'text-gray-500'
                    }`}>
                      ({instance.brands.slice(0, 2).join(', ')}{instance.brands.length > 2 ? '...' : ''})
                    </span>
                  )}
                  <span className={`ml-1.5 px-1.5 py-0.5 rounded text-xs ${
                    selectedInstance === instance.instanceId
                      ? 'bg-blue-500'
                      : 'bg-gray-200'
                  }`}>
                    {instanceScheduleCount}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : filteredSchedules.length > 0 ? (
        viewMode === 'grid' ? renderGridView() : renderListView()
      ) : schedules && schedules.length > 0 ? (
        <div className="text-center py-12">
          <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No matching schedules</h3>
          <p className="text-gray-600 mb-4">Try adjusting your search or filter criteria</p>
          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedInstance(null);
            }}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            <X className="w-4 h-4 mr-2" />
            Clear Filters
          </button>
        </div>
      ) : (
        <div className="text-center py-12">
          <CalendarDays className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No schedules yet</h3>
          <p className="text-gray-600 mb-4">
            To create a schedule, first run a template from an instance, then create a schedule from the successful execution.
          </p>
        </div>
      )}

      {/* Schedule Detail Modal */}
      {selectedSchedule && showDetailModal && (
        <ScheduleDetailModal
          schedule={selectedSchedule}
          onClose={() => {
            setShowDetailModal(false);
            setSelectedSchedule(null);
          }}
          onUpdate={() => {
            queryClient.invalidateQueries({ queryKey: ['schedules'] });
          }}
          onDelete={() => {
            setShowDetailModal(false);
            setSelectedSchedule(null);
            queryClient.invalidateQueries({ queryKey: ['schedules'] });
          }}
        />
      )}

      {/* Schedule Run Modal */}
      {selectedSchedule && showScheduleRunModal && (
        <ScheduleRunModal
          schedule={selectedSchedule}
          onSchedule={async (scheduledTime) => {
            await scheduleRunMutation.mutateAsync({
              scheduleId: selectedSchedule.schedule_id,
              scheduledTime
            });
          }}
          onClose={() => {
            setShowScheduleRunModal(false);
            setSelectedSchedule(null);
          }}
        />
      )}

    </div>
  );
};

export default ScheduleManager;