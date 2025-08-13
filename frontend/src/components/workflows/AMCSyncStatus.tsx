import { Cloud, CloudOff, Loader, AlertCircle, Check, Info, Zap, Calendar, Shield } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { useState } from 'react';
import api from '../../services/api';

interface AMCSyncStatusProps {
  workflowId: string;
  initialStatus?: {
    amcWorkflowId?: string;
    isSyncedToAmc?: boolean;
    amcSyncStatus?: string;
    lastSyncedAt?: string;
  };
}

export default function AMCSyncStatus({ workflowId, initialStatus }: AMCSyncStatusProps) {
  const queryClient = useQueryClient();
  const [showExplanation, setShowExplanation] = useState(false);

  // Query for current sync status
  const { data: syncStatus, isLoading } = useQuery({
    queryKey: ['workflow-amc-status', workflowId],
    queryFn: async () => {
      const response = await api.get(`/workflows/${workflowId}/amc-status`);
      return response.data;
    },
    initialData: initialStatus,
    refetchInterval: (query) => {
      // Poll while syncing
      return query.state.data?.amc_sync_status === 'syncing' ? 2000 : false;
    },
  });

  // Sync to AMC mutation
  const syncMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/workflows/${workflowId}/sync-to-amc`);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Workflow synced to AMC successfully');
      queryClient.invalidateQueries({ queryKey: ['workflow-amc-status', workflowId] });
      queryClient.invalidateQueries({ queryKey: ['workflow', workflowId] });
    },
    onError: (error: any) => {
      toast.error(`Failed to sync: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Remove from AMC mutation
  const removeMutation = useMutation({
    mutationFn: async () => {
      const response = await api.delete(`/workflows/${workflowId}/amc-sync`);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Workflow removed from AMC');
      queryClient.invalidateQueries({ queryKey: ['workflow-amc-status', workflowId] });
      queryClient.invalidateQueries({ queryKey: ['workflow', workflowId] });
    },
    onError: (error: any) => {
      toast.error(`Failed to remove: ${error.response?.data?.detail || error.message}`);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 text-gray-500">
        <Loader className="h-4 w-4 animate-spin" />
        <span className="text-sm">Loading sync status...</span>
      </div>
    );
  }

  const isSynced = syncStatus?.is_synced_to_amc;
  const syncStatusText = syncStatus?.amc_sync_status || 'not_synced';
  const amcWorkflowId = syncStatus?.amc_workflow_id;
  const lastSyncedAt = syncStatus?.last_synced_at;

  const getStatusIcon = () => {
    switch (syncStatusText) {
      case 'synced':
        return <Check className="h-5 w-5 text-green-500" />;
      case 'syncing':
        return <Loader className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'sync_failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <CloudOff className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    switch (syncStatusText) {
      case 'synced':
        return 'Synced to AMC';
      case 'syncing':
        return 'Syncing...';
      case 'sync_failed':
        return 'Sync failed';
      default:
        return 'Not synced';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-gray-900">AMC Sync Status</h3>
              <button
                onClick={() => setShowExplanation(!showExplanation)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
                title="Learn more about AMC sync"
              >
                <Info className="h-4 w-4" />
              </button>
            </div>
            <p className="text-sm text-gray-500">{getStatusText()}</p>
            {amcWorkflowId && (
              <p className="text-xs text-gray-400 mt-1">AMC ID: {amcWorkflowId}</p>
            )}
            {lastSyncedAt && (
              <p className="text-xs text-gray-400">
                Last synced: {new Date(lastSyncedAt).toLocaleString()}
              </p>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {!isSynced ? (
            <button
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending || syncStatusText === 'syncing'}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {syncMutation.isPending ? (
                <>
                  <Loader className="h-4 w-4 mr-2 animate-spin" />
                  Syncing...
                </>
              ) : (
                <>
                  <Cloud className="h-4 w-4 mr-2" />
                  Sync to AMC (Optional)
                </>
              )}
            </button>
          ) : (
            <>
              <button
                onClick={() => syncMutation.mutate()}
                disabled={syncMutation.isPending}
                className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Cloud className="h-4 w-4 mr-2" />
                Re-sync
              </button>
              <button
                onClick={() => {
                  if (confirm('Are you sure you want to remove this workflow from AMC?')) {
                    removeMutation.mutate();
                  }
                }}
                disabled={removeMutation.isPending}
                className="inline-flex items-center px-3 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {removeMutation.isPending ? (
                  <>
                    <Loader className="h-4 w-4 mr-2 animate-spin" />
                    Removing...
                  </>
                ) : (
                  <>
                    <CloudOff className="h-4 w-4 mr-2" />
                    Remove
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>
      
      {/* Explanation section */}
      {showExplanation && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">Why sync to AMC?</h4>
          <div className="space-y-2 text-sm text-blue-800">
            <div className="flex items-start gap-2">
              <Zap className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-medium">Better Performance:</span> Synced queries run faster as AMC can optimize and cache them
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Calendar className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-medium">Native Scheduling:</span> Use AMC's built-in scheduling features for automated runs
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Shield className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-medium">Version Control:</span> AMC tracks query versions and execution history
              </div>
            </div>
          </div>
          <p className="mt-3 text-xs text-blue-700 italic">
            Note: Queries work perfectly fine without syncing. Sync is optional for enhanced features.
          </p>
        </div>
      )}
      
      {syncStatusText === 'sync_failed' && (
        <div className="mt-3 p-3 bg-red-50 rounded-md">
          <p className="text-sm text-red-700">
            Failed to sync workflow to AMC. Please check your authentication and try again.
          </p>
        </div>
      )}
      
      {isSynced && !showExplanation && (
        <div className="mt-3 p-3 bg-green-50 rounded-md">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm text-green-700">
                ✓ Synced to AMC for optimized performance
              </p>
              <p className="text-xs text-green-600 mt-1">
                This query runs faster and can use AMC's native scheduling
              </p>
            </div>
          </div>
        </div>
      )}
      
      {!isSynced && !syncStatusText.includes('fail') && !showExplanation && (
        <div className="mt-3 p-3 bg-gray-50 rounded-md">
          <p className="text-xs text-gray-600">
            <span className="font-medium">Optional:</span> Sync to AMC for faster execution and scheduling features.
            Your query works fine without syncing.
          </p>
        </div>
      )}
    </div>
  );
}