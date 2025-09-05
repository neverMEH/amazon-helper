import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Calendar, CheckCircle, AlertCircle, Clock, RefreshCw } from 'lucide-react';
import { dataCollectionService } from '../../services/dataCollectionService';
import type { CollectionProgress as CollectionProgressType } from '../../types/dataCollection';

interface CollectionProgressProps {
  collectionId: string;
  onBack: () => void;
}

const CollectionProgress: React.FC<CollectionProgressProps> = ({ collectionId, onBack }) => {
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

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Collection Progress</h1>
        <p className="text-gray-600">
          Collection ID: {progress.collection_id}
        </p>
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
                className={`px-6 py-4 ${getWeekStatusClass(week.status)}`}
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
                      <div className="text-xs text-gray-500 mt-1">
                        ID: {week.execution_id}
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
    </div>
  );
};

export default CollectionProgress;