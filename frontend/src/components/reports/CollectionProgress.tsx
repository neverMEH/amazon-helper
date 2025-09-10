import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Calendar, CheckCircle, AlertCircle, Clock, RefreshCw, Eye, BarChart3 } from 'lucide-react';
import { dataCollectionService } from '../../services/dataCollectionService';
import AMCExecutionDetail from '../executions/AMCExecutionDetail';
import CollectionReportDashboard from '../collections/CollectionReportDashboard';

interface CollectionProgressProps {
  collectionId: string;
  onBack: () => void;
  instanceId?: string;
}

const CollectionProgress: React.FC<CollectionProgressProps> = ({ collectionId, onBack, instanceId }) => {
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [showExecutionDetail, setShowExecutionDetail] = useState(false);
  const [showDashboard, setShowDashboard] = useState(false);

  // Fetch collection progress
  const { data: progress, isLoading, error } = useQuery({
    queryKey: ['collectionProgress', collectionId],
    queryFn: () => dataCollectionService.getCollectionProgress(collectionId),
    refetchInterval: 3000, // Poll every 3 seconds for updates
  });

  const getWeekStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'running':
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-gray-400" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getWeekStatusClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'running':
        return 'bg-blue-50 border-blue-200 animate-pulse';
      case 'failed':
        return 'bg-red-50 border-red-200';
      case 'pending':
        return 'bg-gray-50 border-gray-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const handleWeekClick = (executionId: string | null | undefined) => {
    if (executionId) {
      console.log('Week clicked - Execution ID:', executionId);
      console.log('Instance ID from prop:', instanceId);
      console.log('Instance ID from progress:', progress?.instance_id);
      console.log('Final instance ID:', instanceId || progress?.instance_id || '');
      setSelectedExecutionId(executionId);
      setShowExecutionDetail(true);
    }
  };

  const handleCloseExecutionDetail = () => {
    setShowExecutionDetail(false);
    setSelectedExecutionId(null);
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <button
          onClick={onBack}
          className="mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Collections
        </button>
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 text-gray-400 animate-spin" />
        </div>
      </div>
    );
  }

  if (error || !progress) {
    return (
      <div className="p-6">
        <button
          onClick={onBack}
          className="mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Collections
        </button>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">
            Error loading collection progress: {error ? (error as Error).message : 'Unknown error'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <button
        onClick={onBack}
        className="mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Collections
      </button>

      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Collection Progress</h1>
          <p className="text-gray-600">
            Collection ID: {progress.collection_id}
          </p>
        </div>
        <button
          onClick={() => setShowDashboard(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          data-testid="view-dashboard-button"
        >
          <BarChart3 className="w-4 h-4" />
          View Dashboard
        </button>
      </div>

      {/* Progress Overview */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Overall Progress</h2>
        
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Completion</span>
            <span className="text-sm text-gray-600">{progress.progress_percentage}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${progress.progress_percentage}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {progress.statistics.total_weeks}
            </div>
            <div className="text-sm text-gray-600">Total Weeks</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {progress.statistics.completed}
            </div>
            <div className="text-sm text-gray-600">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {progress.statistics.running}
            </div>
            <div className="text-sm text-gray-600">Running</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">
              {progress.statistics.pending}
            </div>
            <div className="text-sm text-gray-600">Pending</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {progress.statistics.failed}
            </div>
            <div className="text-sm text-gray-600">Failed</div>
          </div>
        </div>

        {progress.next_week && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="text-sm font-medium text-blue-900 mb-1">Next Week to Process</h3>
            <div className="flex items-center gap-2 text-sm text-blue-700">
              <Calendar className="w-4 h-4" />
              <span>
                {formatDate(progress.next_week.week_start)} - {formatDate(progress.next_week.week_end)}
              </span>
              {progress.next_week.scheduled_for && (
                <span className="ml-2 text-xs">
                  (Scheduled for {new Date(progress.next_week.scheduled_for).toLocaleTimeString()})
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Week-by-Week Progress */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Week-by-Week Progress</h2>
        </div>
        <div className="max-h-[600px] overflow-y-auto">
          <div className="divide-y divide-gray-200">
            {progress.weeks.map((week) => (
              <div
                key={week.id}
                data-testid="week-row"
                data-clickable={!!week.execution_id}
                className={`px-6 py-4 ${getWeekStatusClass(week.status)} ${
                  week.execution_id ? 'cursor-pointer hover:bg-opacity-80 transition-colors' : ''
                }`}
                onClick={() => handleWeekClick(week.execution_id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    {getWeekStatusIcon(week.status)}
                    <div>
                      <div className="font-medium text-gray-900">
                        {formatDate(week.week_start_date)} - {formatDate(week.week_end_date)}
                      </div>
                      {week.error_message && (
                        <div className="text-sm text-red-600 mt-1">
                          Error: {week.error_message}
                        </div>
                      )}
                      <div className="flex gap-4 text-xs text-gray-500 mt-1">
                        {week.started_at && (
                          <span>Started: {new Date(week.started_at).toLocaleTimeString()}</span>
                        )}
                        {week.completed_at && (
                          <span>Completed: {new Date(week.completed_at).toLocaleTimeString()}</span>
                        )}
                        {week.execution_time_seconds && (
                          <span>Duration: {formatDuration(week.execution_time_seconds)}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    {week.record_count !== undefined && week.record_count !== null && (
                      <div className="text-sm text-gray-600">
                        {week.record_count.toLocaleString()} records
                      </div>
                    )}
                    {week.execution_id && (
                      <div className="flex items-center gap-2 mt-1">
                        <div className="text-xs text-gray-500">
                          ID: {week.execution_id}
                        </div>
                        <button
                          data-testid="view-execution-button"
                          className="inline-flex items-center text-xs text-blue-600 hover:text-blue-800"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleWeekClick(week.execution_id);
                          }}
                        >
                          <Eye className="w-3 h-3 mr-1" />
                          View
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Timeline Info */}
      <div className="mt-6 text-sm text-gray-600">
        <div className="flex justify-between">
          <span>Started: {new Date(progress.started_at).toLocaleString()}</span>
          <span>Last Updated: {new Date(progress.updated_at).toLocaleString()}</span>
        </div>
      </div>

      {/* AMC Execution Detail Modal */}
      {showExecutionDetail && selectedExecutionId && (
        <AMCExecutionDetail
          instanceId={instanceId || progress.instance_id || ''}
          executionId={selectedExecutionId}
          isOpen={showExecutionDetail}
          onClose={handleCloseExecutionDetail}
        />
      )}

      {/* Collection Report Dashboard Modal */}
      {showDashboard && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-7xl h-[90vh] overflow-hidden" data-testid="dashboard-container">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">Report Dashboard</h3>
              <button
                onClick={() => setShowDashboard(false)}
                className="text-gray-400 hover:text-gray-600"
                aria-label="Close dashboard"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-4 h-full overflow-auto">
              <CollectionReportDashboard
                collectionId={collectionId}
                onClose={() => setShowDashboard(false)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CollectionProgress;