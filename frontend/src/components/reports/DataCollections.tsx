import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Calendar, Play, Pause, RefreshCw, X, AlertCircle, CheckCircle, Clock, ChevronRight } from 'lucide-react';
import { dataCollectionService } from '../../services/dataCollectionService';
import type { CollectionResponse, CollectionCreate } from '../../types/dataCollection';
import { workflowService } from '../../services/workflowService';
import { instanceService } from '../../services/instanceService';
import CollectionProgress from './CollectionProgress';
import StartCollectionModal from './StartCollectionModal';

const DataCollections: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [showStartModal, setShowStartModal] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Fetch collections
  const { data: collections = [], isLoading, error, refetch } = useQuery({
    queryKey: ['dataCollections', statusFilter],
    queryFn: () => dataCollectionService.listCollections(
      statusFilter !== 'all' ? { status: statusFilter } : undefined
    ),
    refetchInterval: 5000, // Poll every 5 seconds for updates
  });

  // Pause collection mutation
  const pauseMutation = useMutation({
    mutationFn: (collectionId: string) => dataCollectionService.pauseCollection(collectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataCollections'] });
    },
  });

  // Resume collection mutation
  const resumeMutation = useMutation({
    mutationFn: (collectionId: string) => dataCollectionService.resumeCollection(collectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataCollections'] });
    },
  });

  // Cancel collection mutation
  const cancelMutation = useMutation({
    mutationFn: (collectionId: string) => dataCollectionService.cancelCollection(collectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataCollections'] });
    },
  });

  // Retry failed weeks mutation
  const retryMutation = useMutation({
    mutationFn: (collectionId: string) => dataCollectionService.retryFailedWeeks(collectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataCollections'] });
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'running':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'paused':
        return <Pause className="w-5 h-5 text-yellow-500" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-gray-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-600';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  if (selectedCollection) {
    return (
      <CollectionProgress
        collectionId={selectedCollection}
        onBack={() => setSelectedCollection(null)}
      />
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Data Collections</h1>
          <p className="text-gray-600 mt-1">
            Manage historical data backfill and weekly update collections
          </p>
        </div>
        <button
          onClick={() => setShowStartModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Play className="w-4 h-4" />
          Start Collection
        </button>
      </div>

      {/* Filters */}
      <div className="mb-6 flex gap-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="paused">Paused</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Collections List */}
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 text-gray-400 animate-spin" />
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading collections: {(error as Error).message}</p>
        </div>
      ) : collections.length === 0 ? (
        <div className="bg-gray-50 rounded-lg p-12 text-center">
          <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Collections Found</h3>
          <p className="text-gray-600 mb-4">
            Start a new data collection to backfill historical data for your workflows
          </p>
          <button
            onClick={() => setShowStartModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Start Your First Collection
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collection
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Progress
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date Range
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {collections.map((collection) => (
                <tr
                  key={collection.collection_id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => setSelectedCollection(collection.collection_id)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {collection.workflow_name || collection.collection_id}
                      </div>
                      <div className="text-sm text-gray-500">
                        {collection.instance_name || 'Instance'}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(collection.status)}
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeClass(collection.status)}`}>
                        {collection.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="flex items-center">
                        <div className="flex-1 bg-gray-200 rounded-full h-2 mr-3">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${collection.progress_percentage || 0}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600">
                          {collection.progress_percentage || 0}%
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {collection.weeks_completed || 0} of {collection.target_weeks} weeks
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div>
                      <div>{new Date(collection.start_date).toLocaleDateString()}</div>
                      <div className="text-xs">to {new Date(collection.end_date).toLocaleDateString()}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      {collection.status === 'running' && (
                        <button
                          onClick={() => pauseMutation.mutate(collection.collection_id)}
                          className="text-yellow-600 hover:text-yellow-800"
                          title="Pause"
                        >
                          <Pause className="w-4 h-4" />
                        </button>
                      )}
                      {collection.status === 'paused' && (
                        <button
                          onClick={() => resumeMutation.mutate(collection.collection_id)}
                          className="text-green-600 hover:text-green-800"
                          title="Resume"
                        >
                          <Play className="w-4 h-4" />
                        </button>
                      )}
                      {collection.status === 'failed' && (
                        <button
                          onClick={() => retryMutation.mutate(collection.collection_id)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Retry Failed"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      )}
                      {['pending', 'running', 'paused'].includes(collection.status) && (
                        <button
                          onClick={() => {
                            if (confirm('Are you sure you want to cancel this collection?')) {
                              cancelMutation.mutate(collection.collection_id);
                            }
                          }}
                          className="text-red-600 hover:text-red-800"
                          title="Cancel"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => setSelectedCollection(collection.collection_id)}
                        className="text-gray-600 hover:text-gray-800"
                        title="View Details"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Start Collection Modal */}
      {showStartModal && (
        <StartCollectionModal
          onClose={() => setShowStartModal(false)}
          onSuccess={() => {
            setShowStartModal(false);
            queryClient.invalidateQueries({ queryKey: ['dataCollections'] });
          }}
        />
      )}
    </div>
  );
};

export default DataCollections;