import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  Loader2, CheckCircle, XCircle, AlertCircle,
  Send, ArrowLeft, ExternalLink, BarChart3, Clock
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { reportBuilderService } from '../../services/reportBuilderService';
import toast from 'react-hot-toast';

interface BackfillProgress {
  totalPeriods: number;
  completedPeriods: number;
  failedPeriods: number;
  inProgressPeriods: number;
  estimatedTimeRemaining: string;
  currentBatch: number;
  totalBatches: number;
}

interface SubmissionResult {
  success: boolean;
  reportId?: string;
  scheduleId?: string;
  collectionId?: string;
  backfillProgress?: BackfillProgress;
  error?: string;
  details?: {
    workflowId: string;
    instanceId: string;
    nextRun?: string;
  };
}

interface ReportSubmissionProps {
  workflowId: string;
  workflowName: string;
  instanceId: string;
  parameters: Record<string, any>;
  lookbackConfig: any;
  scheduleConfig: any;
  onBack: () => void;
}

export default function ReportSubmission({
  workflowId,
  workflowName,
  instanceId,
  parameters,
  lookbackConfig,
  scheduleConfig,
  onBack,
}: ReportSubmissionProps) {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState<SubmissionResult | null>(null);
  const [backfillProgress, setBackfillProgress] = useState<BackfillProgress | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: async () => {
      setIsSubmitting(true);

      // Prepare submission data
      const submitData = {
        workflow_id: workflowId,
        instance_id: instanceId,
        parameters,
        lookback_config: lookbackConfig,
        schedule_config: scheduleConfig,
      };

      // Call the submission endpoint
      const response = await reportBuilderService.submit(submitData);
      return response;
    },
    onSuccess: (data) => {
      setIsSubmitting(false);
      setSubmissionResult({
        success: true,
        reportId: data.report_id,
        scheduleId: data.schedule_id,
        collectionId: data.collection_id,
        details: {
          workflowId,
          instanceId,
          nextRun: data.next_run,
        },
      });

      // If it's a backfill, start polling for progress
      if (scheduleConfig.type === 'backfill_with_schedule' && data.collection_id) {
        startBackfillPolling(data.collection_id);
      }

      toast.success('Report configuration submitted successfully!');
    },
    onError: (error: any) => {
      setIsSubmitting(false);
      setSubmissionResult({
        success: false,
        error: error.message || 'Failed to submit report configuration',
      });
      toast.error(error.message || 'Submission failed');
    },
  });

  // Poll for backfill progress
  const startBackfillPolling = (collectionId: string) => {
    const pollProgress = async () => {
      try {
        const progress = await reportBuilderService.getBackfillProgress(collectionId);
        setBackfillProgress(progress);

        // Stop polling if complete
        if (progress.completedPeriods + progress.failedPeriods >= progress.totalPeriods) {
          if (pollingInterval) {
            clearInterval(pollingInterval);
            setPollingInterval(null);
          }
        }
      } catch (error) {
        console.error('Error polling backfill progress:', error);
      }
    };

    // Poll immediately
    pollProgress();

    // Then poll every 5 seconds
    const interval = setInterval(pollProgress, 5000);
    setPollingInterval(interval);
  };

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // Auto-submit on mount
  useEffect(() => {
    if (!submissionResult && !isSubmitting) {
      submitMutation.mutate();
    }
  }, []);

  const handleViewDashboard = () => {
    navigate('/dashboards');
  };

  const handleViewSchedules = () => {
    navigate('/schedules');
  };

  const handleViewCollection = () => {
    if (submissionResult?.collectionId) {
      navigate(`/data-collections/${submissionResult.collectionId}`);
    }
  };

  const handleCreateAnother = () => {
    window.location.reload(); // Reset the entire flow
  };

  // Calculate progress percentage for backfill
  const getProgressPercentage = () => {
    if (!backfillProgress) return 0;
    return Math.round(
      ((backfillProgress.completedPeriods + backfillProgress.failedPeriods) /
        backfillProgress.totalPeriods) * 100
    );
  };

  return (
    <div className="space-y-6">
      {/* Submitting State */}
      {isSubmitting && (
        <div className="text-center py-12">
          <Loader2 className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Submitting Report Configuration</h3>
          <p className="text-sm text-gray-500">Please wait while we process your request...</p>
        </div>
      )}

      {/* Success State */}
      {submissionResult?.success && (
        <div className="text-center py-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>

          <h3 className="text-xl font-medium text-gray-900 mb-2">Report Successfully Configured!</h3>
          <p className="text-gray-600 mb-6">
            Your report "{workflowName}" has been configured and{' '}
            {scheduleConfig.type === 'once' ? 'is running now' : 'scheduled'}.
          </p>

          {/* Success Details */}
          <div className="bg-gray-50 rounded-lg p-6 max-w-2xl mx-auto mb-6">
            <div className="grid grid-cols-2 gap-4 text-sm">
              {submissionResult.reportId && (
                <div>
                  <p className="text-gray-600">Report ID</p>
                  <p className="font-mono text-gray-900">{submissionResult.reportId}</p>
                </div>
              )}
              {submissionResult.scheduleId && (
                <div>
                  <p className="text-gray-600">Schedule ID</p>
                  <p className="font-mono text-gray-900">{submissionResult.scheduleId}</p>
                </div>
              )}
              {submissionResult.details?.nextRun && (
                <div>
                  <p className="text-gray-600">Next Run</p>
                  <p className="text-gray-900">{submissionResult.details.nextRun}</p>
                </div>
              )}
              {scheduleConfig.type !== 'once' && (
                <div>
                  <p className="text-gray-600">Schedule</p>
                  <p className="text-gray-900">
                    {scheduleConfig.frequency} at {scheduleConfig.time}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Backfill Progress */}
          {backfillProgress && (
            <div className="bg-blue-50 rounded-lg p-6 max-w-2xl mx-auto mb-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-gray-900 flex items-center">
                  <Clock className="h-4 w-4 mr-2" />
                  Backfill Progress
                </h4>
                <span className="text-sm text-gray-600">
                  Batch {backfillProgress.currentBatch} of {backfillProgress.totalBatches}
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${getProgressPercentage()}%` }}
                />
              </div>

              <div className="grid grid-cols-4 gap-2 text-xs">
                <div className="text-center">
                  <p className="text-gray-600">Completed</p>
                  <p className="font-medium text-green-600">{backfillProgress.completedPeriods}</p>
                </div>
                <div className="text-center">
                  <p className="text-gray-600">In Progress</p>
                  <p className="font-medium text-blue-600">{backfillProgress.inProgressPeriods}</p>
                </div>
                <div className="text-center">
                  <p className="text-gray-600">Failed</p>
                  <p className="font-medium text-red-600">{backfillProgress.failedPeriods}</p>
                </div>
                <div className="text-center">
                  <p className="text-gray-600">Remaining</p>
                  <p className="font-medium text-gray-900">
                    {backfillProgress.totalPeriods -
                     backfillProgress.completedPeriods -
                     backfillProgress.failedPeriods -
                     backfillProgress.inProgressPeriods}
                  </p>
                </div>
              </div>

              {backfillProgress.estimatedTimeRemaining && (
                <p className="text-center text-sm text-gray-600 mt-3">
                  Estimated time remaining: {backfillProgress.estimatedTimeRemaining}
                </p>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            {scheduleConfig.type === 'backfill_with_schedule' && submissionResult.collectionId && (
              <button
                onClick={handleViewCollection}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md
                         shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2
                         focus:ring-offset-2 focus:ring-blue-500"
              >
                <BarChart3 className="h-4 w-4 mr-2" />
                View Collection Progress
              </button>
            )}

            {scheduleConfig.type !== 'once' && (
              <button
                onClick={handleViewSchedules}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md
                         text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2
                         focus:ring-offset-2 focus:ring-blue-500"
              >
                <Clock className="h-4 w-4 mr-2" />
                View Schedules
              </button>
            )}

            <button
              onClick={handleViewDashboard}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md
                       text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2
                       focus:ring-offset-2 focus:ring-blue-500"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Go to Dashboard
            </button>

            <button
              onClick={handleCreateAnother}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md
                       text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2
                       focus:ring-offset-2 focus:ring-blue-500"
            >
              Create Another Report
            </button>
          </div>
        </div>
      )}

      {/* Error State */}
      {submissionResult?.success === false && (
        <div className="text-center py-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
            <XCircle className="h-8 w-8 text-red-600" />
          </div>

          <h3 className="text-xl font-medium text-gray-900 mb-2">Submission Failed</h3>
          <p className="text-gray-600 mb-4">
            We encountered an error while submitting your report configuration.
          </p>

          {submissionResult.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-2xl mx-auto mb-6">
              <div className="flex items-start">
                <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
                <p className="text-sm text-red-800">{submissionResult.error}</p>
              </div>
            </div>
          )}

          {/* Error Actions */}
          <div className="flex gap-3 justify-center">
            <button
              onClick={onBack}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md
                       text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2
                       focus:ring-offset-2 focus:ring-blue-500"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </button>

            <button
              onClick={() => submitMutation.mutate()}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md
                       shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2
                       focus:ring-offset-2 focus:ring-blue-500"
            >
              <Send className="h-4 w-4 mr-2" />
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Footer Note */}
      {submissionResult && (
        <div className="text-center text-sm text-gray-500 border-t pt-4">
          {scheduleConfig.type === 'once' ? (
            <p>Your report is being executed. Results will be available in the dashboard shortly.</p>
          ) : scheduleConfig.type === 'backfill_with_schedule' ? (
            <p>Historical data is being processed. You can close this window and check progress later.</p>
          ) : (
            <p>Your report has been scheduled and will run automatically at the specified times.</p>
          )}
        </div>
      )}
    </div>
  );
}