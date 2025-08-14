import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Code, Database, Calendar, User, Hash, ChevronDown, ChevronRight, RefreshCw, Play, Loader, Table, BarChart3, Maximize2, Edit2 } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { amcExecutionService } from '../../services/amcExecutionService';
import EnhancedResultsTable from './EnhancedResultsTable';
import DataVisualization from './DataVisualization';
import SQLEditor from '../common/SQLEditor';
import ExecutionErrorDetails from './ExecutionErrorDetails';

interface Props {
  instanceId: string;
  executionId: string;
  isOpen: boolean;
  onClose: () => void;
  onRerunSuccess?: (newExecutionId: string) => void;
}

export default function AMCExecutionDetail({ instanceId, executionId, isOpen, onClose, onRerunSuccess }: Props) {
  const [showQuery, setShowQuery] = useState(false);
  const [showParameters, setShowParameters] = useState(false);
  const [isRerunning, setIsRerunning] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'charts'>('table');
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isExpandedSQL, setIsExpandedSQL] = useState(false);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['amc-execution-detail', instanceId, executionId],
    queryFn: () => amcExecutionService.getExecutionDetails(instanceId, executionId),
    enabled: isOpen && !!executionId,
    // Poll every 5 seconds while modal is open
    refetchInterval: isOpen ? 5000 : false,
  });

  const execution = data?.execution;

  // Rerun mutation
  const rerunMutation = useMutation({
    mutationFn: async () => {
      // Check for workflow ID in multiple possible locations
      const workflowId = execution?.workflowId || execution?.workflowInfo?.id;
      if (!workflowId) {
        throw new Error('Workflow ID not found');
      }
      
      // Import api service
      const { default: api } = await import('../../services/api');
      
      // Execute with the same parameters
      const response = await api.post(`/workflows/${workflowId}/execute`, {
        parameters: execution.executionParameters || {},
        instance_id: instanceId
      });
      
      return response.data;
    },
    onSuccess: (data) => {
      toast.success('Workflow rerun initiated');
      setIsRerunning(false);
      
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['amc-execution-detail'] });
      queryClient.invalidateQueries({ queryKey: ['amc-executions'] });
      
      // If we get a new execution ID, navigate to it
      if (data.execution_id) {
        toast.success(`Opening new execution: ${data.execution_id}`);
        
        // Show transition state
        setIsTransitioning(true);
        
        // If callback is provided, use it to navigate to new execution
        if (onRerunSuccess) {
          // Small delay for smooth transition
          setTimeout(() => {
            onRerunSuccess(data.execution_id);
            setIsTransitioning(false);
          }, 400);
        } else {
          // Fallback: close current modal and let parent handle
          // This gives time for the list to refresh
          setTimeout(() => {
            onClose();
            setIsTransitioning(false);
          }, 500);
        }
      }
    },
    onError: (error: unknown) => {
      const errorMessage = error && typeof error === 'object' && 'response' in error 
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail 
        : 'Failed to rerun workflow';
      toast.error(errorMessage);
      setIsRerunning(false);
    }
  });

  const handleRerun = () => {
    setIsRerunning(true);
    rerunMutation.mutate();
  };

  const handleRefresh = () => {
    refetch();
    toast.success('Refreshing execution data...');
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-40"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <div className="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-6xl sm:p-6">
            <div className="absolute right-0 top-0 hidden pr-4 pt-4 sm:block">
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={handleRefresh}
                  className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  title="Refresh execution data"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={handleRerun}
                  disabled={isRerunning || (!execution?.workflowId && !execution?.workflowInfo?.id)}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  title="Rerun with same parameters"
                >
                  {isRerunning ? (
                    <>
                      <Loader className="h-4 w-4 mr-1 animate-spin" />
                      Rerunning...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-1" />
                      Rerun
                    </>
                  )}
                </button>
                <button
                  type="button"
                  className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                  onClick={onClose}
                >
                  <span className="sr-only">Close</span>
                  <X className="h-6 w-6" aria-hidden="true" />
                </button>
              </div>
            </div>

            <div className="sm:flex sm:items-start">
              <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                <h3 className="text-lg font-semibold leading-6 text-gray-900">
                  Execution Details
                </h3>
                
                {/* Display Instance and Workflow Name */}
                {execution && (
                  <div className="mt-2 space-y-1">
                    {execution.instanceInfo && (
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">Instance:</span> {execution.instanceInfo.instanceName} ({execution.instanceInfo.region})
                      </p>
                    )}
                    {(execution.workflowInfo?.name || execution.workflowName) && (
                      <p className="text-sm text-gray-600">
                        <span className="font-medium">Query:</span> {execution.workflowInfo?.name || execution.workflowName}
                      </p>
                    )}
                  </div>
                )}

                {(isLoading || isTransitioning) && (
                  <div className="mt-4 flex flex-col items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                    {isTransitioning && (
                      <p className="mt-2 text-sm text-gray-600">Loading new execution...</p>
                    )}
                  </div>
                )}

                {error && !isTransitioning && (
                  <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
                    <p className="text-sm text-red-600">Failed to load execution details</p>
                  </div>
                )}

                {execution && !isTransitioning && (
                  <div className="mt-4 space-y-4">
                    {/* Query Details Section */}
                    {(execution.sqlQuery || execution.workflowInfo?.sqlQuery) && (
                      <div className="border border-gray-200 rounded-lg">
                        <button
                          onClick={() => setShowQuery(!showQuery)}
                          className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center">
                            <Code className="h-5 w-5 text-gray-400 mr-2" />
                            <span className="text-sm font-medium text-gray-900">SQL Query</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            {showQuery && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setIsExpandedSQL(true);
                                }}
                                className="p-1 hover:bg-gray-200 rounded transition-colors"
                                title="Expand SQL editor"
                              >
                                <Maximize2 className="h-4 w-4 text-gray-500" />
                              </button>
                            )}
                            {showQuery ? (
                              <ChevronDown className="h-5 w-5 text-gray-400" />
                            ) : (
                              <ChevronRight className="h-5 w-5 text-gray-400" />
                            )}
                          </div>
                        </button>
                        {showQuery && (
                          <div className="px-4 pb-4">
                            <SQLEditor 
                              value={execution.sqlQuery || execution.workflowInfo?.sqlQuery || ''} 
                              onChange={() => {}} // Read-only, no changes needed
                              height="300px"
                              readOnly={true}
                            />
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Execution Parameters Section */}
                    {execution.executionParameters && Object.keys(execution.executionParameters).length > 0 && (
                      <div className="border border-gray-200 rounded-lg">
                        <button
                          onClick={() => setShowParameters(!showParameters)}
                          className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center">
                            <Database className="h-5 w-5 text-gray-400 mr-2" />
                            <span className="text-sm font-medium text-gray-900">Execution Parameters</span>
                            <span className="ml-2 text-xs text-gray-500">({Object.keys(execution.executionParameters).length})</span>
                          </div>
                          {showParameters ? (
                            <ChevronDown className="h-5 w-5 text-gray-400" />
                          ) : (
                            <ChevronRight className="h-5 w-5 text-gray-400" />
                          )}
                        </button>
                        {showParameters && (
                          <div className="px-4 pb-4">
                            <div className="bg-gray-50 rounded-md p-3">
                              {Object.entries(execution.executionParameters).map(([key, value]) => (
                                <div key={key} className="flex justify-between py-1 text-sm">
                                  <span className="font-medium text-gray-600">{key}:</span>
                                  <span className="text-gray-900">{JSON.stringify(value)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Execution Metadata */}
                    <div className="bg-gray-50 px-4 py-3 sm:px-6 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Execution Details</h4>
                      <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
                            <div>
                              <dt className="text-sm font-medium text-gray-500 flex items-center">
                                <Hash className="h-4 w-4 mr-1" />
                                Execution ID
                              </dt>
                              <dd className="mt-1 text-sm text-gray-900 font-mono">
                                {execution.executionId}
                              </dd>
                            </div>
                            <div>
                              <dt className="text-sm font-medium text-gray-500">Status</dt>
                              <dd className="mt-1 text-sm">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                                  ${execution.status === 'SUCCEEDED' ? 'bg-green-100 text-green-800' :
                                    execution.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                                    execution.status === 'RUNNING' ? 'bg-blue-100 text-blue-800' :
                                    'bg-yellow-100 text-yellow-800'}`}>
                                  {execution.amcStatus || execution.status}
                                </span>
                              </dd>
                            </div>
                            {execution.triggeredBy && (
                              <div>
                                <dt className="text-sm font-medium text-gray-500 flex items-center">
                                  <User className="h-4 w-4 mr-1" />
                                  Triggered By
                                </dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                  {execution.triggeredBy}
                                </dd>
                              </div>
                            )}
                            {(execution.createdAt || execution.startTime) && (
                              <div>
                                <dt className="text-sm font-medium text-gray-500 flex items-center">
                                  <Calendar className="h-4 w-4 mr-1" />
                                  Created
                                </dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                  {new Date(execution.createdAt || execution.startTime!).toLocaleString()}
                                </dd>
                              </div>
                            )}
                            {execution.startedAt && (
                              <div>
                                <dt className="text-sm font-medium text-gray-500">Started</dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                  {new Date(execution.startedAt).toLocaleString()}
                                </dd>
                              </div>
                            )}
                            {(execution.completedAt || execution.endTime) && (
                              <div>
                                <dt className="text-sm font-medium text-gray-500">Completed</dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                  {new Date(execution.completedAt || execution.endTime!).toLocaleString()}
                                </dd>
                              </div>
                            )}
                            {execution.durationSeconds && (
                              <div>
                                <dt className="text-sm font-medium text-gray-500">Duration</dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                  {execution.durationSeconds < 60 
                                    ? `${execution.durationSeconds}s`
                                    : `${Math.floor(execution.durationSeconds / 60)}m ${execution.durationSeconds % 60}s`
                                  }
                                </dd>
                              </div>
                            )}
                            {execution.rowCount !== undefined && execution.rowCount !== null && (
                              <div>
                                <dt className="text-sm font-medium text-gray-500">Rows Returned</dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                  {execution.rowCount.toLocaleString()}
                                </dd>
                              </div>
                            )}
                            <div>
                              <dt className="text-sm font-medium text-gray-500">Progress</dt>
                              <dd className="mt-1">
                                <div className="flex items-center">
                                  <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                                    <div
                                      className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                                      style={{ width: `${execution.progress}%` }}
                                    />
                                  </div>
                                  <span className="text-sm text-gray-600">{execution.progress}%</span>
                                </div>
                              </dd>
                            </div>
                          </dl>
                        </div>

                        {/* Display detailed error information for failed executions */}
                        <ExecutionErrorDetails 
                          errorMessage={execution.error || execution.errorMessage}
                          errorDetails={execution.errorDetails}
                          status={execution.status}
                          sqlQuery={execution.sqlQuery || execution.workflowInfo?.sqlQuery}
                          executionId={executionId}
                          instanceName={execution.instanceInfo?.instanceName}
                        />

                        {/* Edit & Retry button for failed executions */}
                        {(execution.status === 'FAILED' || execution.status === 'failed') && 
                         (execution.workflowId || execution.workflowInfo?.id) && (
                          <div className="mt-4 flex justify-center">
                            <button
                              onClick={() => {
                                const workflowId = execution.workflowId || execution.workflowInfo?.id;
                                navigate(`/query-builder/edit/${workflowId}`, {
                                  state: { 
                                    fromFailure: true,
                                    errorMessage: execution.error || execution.errorMessage,
                                    executionParameters: execution.executionParameters,
                                    instanceId: instanceId
                                  }
                                });
                                onClose();
                              }}
                              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                            >
                              <Edit2 className="h-4 w-4 mr-2" />
                              Edit Query & Retry
                            </button>
                          </div>
                        )}

                        {execution.resultData && (
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <h4 className="text-sm font-medium text-gray-900">Results</h4>
                              
                              {/* View Mode Toggle */}
                              <div className="flex rounded-md shadow-sm" role="group">
                                <button
                                  type="button"
                                  onClick={() => setViewMode('table')}
                                  className={`px-4 py-2 text-sm font-medium rounded-l-lg border ${
                                    viewMode === 'table'
                                      ? 'bg-indigo-600 text-white border-indigo-600 z-10'
                                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                                  }`}
                                >
                                  <Table className="h-4 w-4 inline-block mr-1" />
                                  Table
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setViewMode('charts')}
                                  className={`px-4 py-2 text-sm font-medium rounded-r-lg border-t border-r border-b ${
                                    viewMode === 'charts'
                                      ? 'bg-indigo-600 text-white border-indigo-600 z-10'
                                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                                  }`}
                                >
                                  <BarChart3 className="h-4 w-4 inline-block mr-1" />
                                  Charts
                                </button>
                              </div>
                            </div>

                            {/* Conditional Rendering based on View Mode */}
                            {viewMode === 'table' ? (
                              <EnhancedResultsTable 
                                data={execution.resultData}
                                instanceInfo={execution.instanceInfo}
                                brands={execution.brands}
                                executionContext={{
                                  workflowName: execution.workflowInfo?.name || execution.workflowName || 'query',
                                  executionId: execution.executionId,
                                  startTime: execution.startTime,
                                  endTime: execution.endTime || new Date().toISOString()
                                }}
                              />
                            ) : (
                              <DataVisualization
                                data={execution.resultData}
                                columns={execution.resultData && execution.resultData.length > 0 
                                  ? Object.keys(execution.resultData[0])
                                  : []
                                }
                                title="Query Results Visualization"
                                brands={execution.brands}
                              />
                            )}
                          </div>
                        )}

                    {execution.status === 'SUCCEEDED' && !execution.resultData && (
                      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                        <p className="text-sm text-blue-700">
                          Execution completed successfully. Results may take a moment to load.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-5 sm:mt-6">
              <button
                type="button"
                className="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                onClick={onClose}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Expanded SQL Modal */}
      {isExpandedSQL && (
        <>
          <div 
            className="fixed inset-0 bg-gray-900 bg-opacity-50 transition-opacity z-[60]"
            onClick={() => setIsExpandedSQL(false)}
          />
          <div className="fixed inset-0 z-[70] overflow-y-auto p-4">
            <div className="flex min-h-full items-center justify-center">
              <div className="relative transform overflow-hidden rounded-lg bg-white shadow-2xl transition-all w-full max-w-7xl">
                <div className="bg-white px-4 pb-4 pt-5 sm:p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                      <Code className="h-5 w-5 mr-2 text-gray-500" />
                      SQL Query - Expanded View
                    </h3>
                    <button
                      onClick={() => setIsExpandedSQL(false)}
                      className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                    >
                      <span className="sr-only">Close</span>
                      <X className="h-6 w-6" aria-hidden="true" />
                    </button>
                  </div>
                  
                  {/* Instance and Query Name Info */}
                  {execution && (
                    <div className="mb-4 text-sm text-gray-600 space-y-1">
                      {execution.instanceInfo && (
                        <p>
                          <span className="font-medium">Instance:</span> {execution.instanceInfo.instanceName} ({execution.instanceInfo.region})
                        </p>
                      )}
                      {(execution.workflowInfo?.name || execution.workflowName) && (
                        <p>
                          <span className="font-medium">Query:</span> {execution.workflowInfo?.name || execution.workflowName}
                        </p>
                      )}
                    </div>
                  )}
                  
                  <div className="border rounded-lg overflow-hidden">
                    <SQLEditor 
                      value={execution?.sqlQuery || execution?.workflowInfo?.sqlQuery || ''} 
                      onChange={() => {}}
                      height="calc(80vh - 200px)"
                      readOnly={true}
                    />
                  </div>
                  
                  <div className="mt-4 flex justify-end">
                    <button
                      type="button"
                      onClick={() => setIsExpandedSQL(false)}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}