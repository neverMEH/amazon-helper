import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { X, Calendar, AlertCircle } from 'lucide-react';
import { dataCollectionService } from '../../services/dataCollectionService';
import { workflowService } from '../../services/workflowService';
import { instanceService } from '../../services/instanceService';
import type { CollectionCreate } from '../../types/dataCollection';

interface StartCollectionModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

const StartCollectionModal: React.FC<StartCollectionModalProps> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState<CollectionCreate>({
    workflow_id: '',
    instance_id: '',
    target_weeks: 52,
    collection_type: 'backfill',
  });
  const [error, setError] = useState<string | null>(null);

  // Fetch workflows
  const { data: workflows = [] } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => workflowService.getWorkflows(),
  });

  // Fetch instances
  const { data: instances = [] } = useQuery({
    queryKey: ['instances'],
    queryFn: () => instanceService.list(),
  });

  // Create collection mutation
  const createMutation = useMutation({
    mutationFn: (data: CollectionCreate) => dataCollectionService.createCollection(data),
    onSuccess: () => {
      onSuccess();
    },
    onError: (error) => {
      setError((error as Error).message);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.workflow_id) {
      setError('Please select a workflow');
      return;
    }
    if (!formData.instance_id) {
      setError('Please select an instance');
      return;
    }

    createMutation.mutate(formData);
  };

  // Calculate date range based on target weeks
  const calculateDateRange = () => {
    const endDate = new Date();
    endDate.setDate(endDate.getDate() - 14); // 14 days ago for AMC data lag
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - (formData.target_weeks * 7));
    
    return {
      start: startDate.toLocaleDateString(),
      end: endDate.toLocaleDateString()
    };
  };

  const dateRange = calculateDateRange();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-semibold">Start Data Collection</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Workflow Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Workflow *
            </label>
            <select
              value={formData.workflow_id}
              onChange={(e) => setFormData({ ...formData, workflow_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select a workflow</option>
              {workflows.map((workflow: any) => (
                <option key={workflow.id} value={workflow.id}>
                  {workflow.name} ({workflow.workflow_id})
                </option>
              ))}
            </select>
            <p className="mt-1 text-sm text-gray-500">
              Select the workflow to execute for data collection
            </p>
          </div>

          {/* Instance Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AMC Instance *
            </label>
            <select
              value={formData.instance_id}
              onChange={(e) => setFormData({ ...formData, instance_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select an instance</option>
              {instances.map((instance: any) => (
                <option key={instance.id} value={instance.id}>
                  {instance.instance_name} ({instance.instance_id})
                </option>
              ))}
            </select>
            <p className="mt-1 text-sm text-gray-500">
              Select the AMC instance to run the collection on
            </p>
          </div>

          {/* Collection Type */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Collection Type
            </label>
            <div className="space-y-2">
              <label className="flex items-start gap-3">
                <input
                  type="radio"
                  value="backfill"
                  checked={formData.collection_type === 'backfill'}
                  onChange={(e) => setFormData({ ...formData, collection_type: e.target.value as 'backfill' | 'weekly_update' })}
                  className="mt-1"
                />
                <div>
                  <div className="font-medium">Historical Backfill</div>
                  <div className="text-sm text-gray-600">
                    Collect historical data for the specified number of weeks
                  </div>
                </div>
              </label>
              <label className="flex items-start gap-3">
                <input
                  type="radio"
                  value="weekly_update"
                  checked={formData.collection_type === 'weekly_update'}
                  onChange={(e) => setFormData({ ...formData, collection_type: e.target.value as 'backfill' | 'weekly_update' })}
                  className="mt-1"
                />
                <div>
                  <div className="font-medium">Weekly Update</div>
                  <div className="text-sm text-gray-600">
                    Continuously update with new weekly data as it becomes available
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* Target Weeks */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Number of Weeks
            </label>
            <div className="flex items-center gap-4">
              <input
                type="number"
                min="1"
                max="52"
                value={formData.target_weeks}
                onChange={(e) => setFormData({ ...formData, target_weeks: parseInt(e.target.value) || 1 })}
                className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
              <div className="flex-1">
                <div className="text-sm text-gray-600">
                  Date Range: {dateRange.start} to {dateRange.end}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  AMC data has a 14-day processing lag
                </div>
              </div>
            </div>
          </div>

          {/* Info Box */}
          <div className="mb-6 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-start gap-2">
              <Calendar className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-900">
                <p className="font-medium mb-1">How Collection Works</p>
                <ul className="list-disc list-inside space-y-1 text-blue-800">
                  <li>The workflow will be executed once for each week in the date range</li>
                  <li>Date parameters in the workflow will be automatically substituted</li>
                  <li>Collections run in the background and can be paused/resumed</li>
                  <li>You'll receive notifications when the collection completes</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              disabled={createMutation.isPending}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? 'Starting...' : 'Start Collection'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StartCollectionModal;