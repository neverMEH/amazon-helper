import { useQuery } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { amcExecutionService } from '../../services/amcExecutionService';
import EnhancedResultsTable from './EnhancedResultsTable';

interface Props {
  instanceId: string;
  executionId: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function AMCExecutionDetail({ instanceId, executionId, isOpen, onClose }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['amc-execution-detail', instanceId, executionId],
    queryFn: () => amcExecutionService.getExecutionDetails(instanceId, executionId),
    enabled: isOpen && !!executionId,
    // Poll every 5 seconds while modal is open
    refetchInterval: isOpen ? 5000 : false,
  });

  const execution = data?.execution;

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
              <button
                type="button"
                className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                onClick={onClose}
              >
                <span className="sr-only">Close</span>
                <X className="h-6 w-6" aria-hidden="true" />
              </button>
            </div>

            <div className="sm:flex sm:items-start">
              <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                <h3 className="text-lg font-semibold leading-6 text-gray-900">
                  Execution Details
                </h3>

                {isLoading && (
                  <div className="mt-4 flex justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                  </div>
                )}

                {error && (
                  <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
                    <p className="text-sm text-red-600">Failed to load execution details</p>
                  </div>
                )}

                {execution && (
                  <div className="mt-4 space-y-4">
                    <div className="bg-gray-50 px-4 py-3 sm:px-6 rounded-lg">
                      <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                            <div>
                              <dt className="text-sm font-medium text-gray-500">Execution ID</dt>
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
                            {execution.startTime && (
                              <div>
                                <dt className="text-sm font-medium text-gray-500">Start Time</dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                  {new Date(execution.startTime).toLocaleString()}
                                </dd>
                              </div>
                            )}
                            {execution.endTime && (
                              <div>
                                <dt className="text-sm font-medium text-gray-500">End Time</dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                  {new Date(execution.endTime).toLocaleString()}
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

                        {execution.error && (
                          <div className="bg-red-50 border border-red-200 rounded-md p-4">
                            <h4 className="text-sm font-medium text-red-800">Error</h4>
                            <p className="mt-1 text-sm text-red-700">{execution.error}</p>
                          </div>
                        )}

                        {execution.resultData && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 mb-2">Results</h4>
                            <EnhancedResultsTable 
                              data={execution.resultData}
                              instanceInfo={execution.instanceInfo}
                              brands={execution.brands}
                            />
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
    </>
  );
}