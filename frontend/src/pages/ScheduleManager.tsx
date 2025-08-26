import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Plus, 
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
  CalendarDays
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { format, parseISO } from 'date-fns';
import { scheduleService } from '../services/scheduleService';
import type { Schedule } from '../types/schedule';
import ScheduleWizard from '../components/schedules/ScheduleWizard';
import ScheduleDetailModal from '../components/schedules/ScheduleDetailModal';

type ViewMode = 'grid' | 'list' | 'calendar';

const ScheduleManager: React.FC = () => {
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [showCreateWizard, setShowCreateWizard] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [filterActive, setFilterActive] = useState<boolean | null>(null);

  // Fetch schedules
  const { data: schedules, isLoading } = useQuery({
    queryKey: ['schedules', filterActive],
    queryFn: () => scheduleService.listAllSchedules({ is_active: filterActive ?? undefined }),
  });

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
      // Refresh schedules after 65 seconds to show updated next_run_at
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['schedules'] });
      }, 65000);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to schedule test run');
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
      {schedules?.map((schedule) => (
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
              >
                <Power className="w-4 h-4 text-gray-600" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  testRunMutation.mutate(schedule.schedule_id);
                }}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <Play className="w-4 h-4 text-gray-600" />
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
          
          {/* Brands display temporarily disabled - brands field not yet in database
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
          )} */}

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
          {schedules?.map((schedule) => (
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
                  {/* Brands display temporarily disabled - brands field not yet in database
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
                  )} */}
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
                  >
                    <Power className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => testRunMutation.mutate(schedule.schedule_id)}
                    className="text-gray-600 hover:text-gray-900"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Are you sure you want to delete this schedule?')) {
                        deleteScheduleMutation.mutate(schedule.schedule_id);
                      }
                    }}
                    className="text-red-600 hover:text-red-900"
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
        <button
          onClick={() => setShowCreateWizard(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Schedule
        </button>
      </div>

      {/* Filters and View Mode */}
      <div className="mb-6 flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setFilterActive(null)}
            className={`px-3 py-1 rounded-lg text-sm font-medium ${
              filterActive === null
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilterActive(true)}
            className={`px-3 py-1 rounded-lg text-sm font-medium ${
              filterActive === true
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Active
          </button>
          <button
            onClick={() => setFilterActive(false)}
            className={`px-3 py-1 rounded-lg text-sm font-medium ${
              filterActive === false
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Inactive
          </button>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded ${viewMode === 'grid' ? 'bg-gray-200' : 'hover:bg-gray-100'}`}
          >
            <Grid3x3 className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded ${viewMode === 'list' ? 'bg-gray-200' : 'hover:bg-gray-100'}`}
          >
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : schedules && schedules.length > 0 ? (
        viewMode === 'grid' ? renderGridView() : renderListView()
      ) : (
        <div className="text-center py-12">
          <CalendarDays className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No schedules yet</h3>
          <p className="text-gray-600 mb-4">Create your first schedule to automate workflow execution</p>
          <button
            onClick={() => setShowCreateWizard(true)}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Schedule
          </button>
        </div>
      )}

      {/* Create Wizard Modal */}
      {showCreateWizard && (
        <ScheduleWizard
          workflowId="" // This will need to be handled differently
          workflowName=""
          onComplete={() => setShowCreateWizard(false)}
          onCancel={() => setShowCreateWizard(false)}
        />
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

    </div>
  );
};

export default ScheduleManager;