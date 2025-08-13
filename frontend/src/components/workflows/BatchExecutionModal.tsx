import { useState, useEffect, useRef } from 'react';
import { X, Play, CheckCircle, AlertCircle, Clock, Loader2, Database, Download } from 'lucide-react';
import { workflowService, type BatchStatus, type BatchResults } from '../../services/workflowService';
import ParameterEditor from './ParameterEditor';
import MultiInstanceSelector from '../query-builder/MultiInstanceSelector';

interface BatchExecutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflow: {
    id: string;
    name: string;
    description?: string;
    parameters?: Record<string, any>;
    sql_query: string;
    instance_id?: string;
  };
  instances: any[];
  onExecutionComplete?: () => void;
}

type ViewMode = 'table' | 'chart' | 'raw';

export default function BatchExecutionModal({
  isOpen,
  onClose,
  workflow,
  instances,
  onExecutionComplete
}: BatchExecutionModalProps) {
  const [selectedInstances, setSelectedInstances] = useState<string[]>([]);
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [batchName, setBatchName] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null);
  const [batchResults, setBatchResults] = useState<BatchResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const batchNameInputRef = useRef<HTMLInputElement>(null);
  const pollCountRef = useRef<number>(0);
  const lastPollTimeRef = useRef<number>(Date.now());

  // Initialize parameters from workflow
  useEffect(() => {
    if (workflow.parameters) {
      setParameters(workflow.parameters);
    }
    // Generate default batch name
    const now = new Date();
    setBatchName(`${workflow.name} - Batch ${now.toLocaleString()}`);
  }, [workflow]);

  // Focus management and keyboard navigation
  useEffect(() => {
    if (isOpen) {
      // Store current focus
      previousFocusRef.current = document.activeElement as HTMLElement;
      
      // Focus the batch name input after a short delay
      setTimeout(() => {
        batchNameInputRef.current?.focus();
      }, 100);
      
      // Add keyboard handlers
      const handleKeyDown = (e: KeyboardEvent) => {
        // Escape key to close
        if (e.key === 'Escape') {
          onClose();
          return;
        }
        
        // Tab key for focus trap
        if (e.key === 'Tab' && modalRef.current) {
          const focusableElements = modalRef.current.querySelectorAll(
            'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
          );
          
          if (focusableElements.length === 0) return;
          
          const firstElement = focusableElements[0] as HTMLElement;
          const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
          
          if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      };
      
      document.addEventListener('keydown', handleKeyDown);
      
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
      };
    } else {
      // Restore focus when modal closes
      previousFocusRef.current?.focus();
    }
  }, [isOpen, onClose]);

  // Poll for batch status with exponential backoff
  useEffect(() => {
    // Clear any existing timeout
    if (pollingIntervalRef.current) {
      clearTimeout(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    if (batchId && isExecuting) {
      const pollStatus = async () => {
        try {
          const status = await workflowService.getBatchStatus(batchId);
          setBatchStatus(status);

          // Check if batch is complete
          if (status.status === 'completed' || status.status === 'failed' || status.status === 'partial') {
            setIsExecuting(false);
            
            // Clear timeout
            if (pollingIntervalRef.current) {
              clearTimeout(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
            
            // Reset poll counter
            pollCountRef.current = 0;
            
            // Fetch results if completed
            if (status.status === 'completed' || status.status === 'partial') {
              const results = await workflowService.getBatchResults(batchId);
              setBatchResults(results);
            }
            
            if (onExecutionComplete) {
              onExecutionComplete();
            }
          } else {
            // Schedule next poll with exponential backoff
            scheduleNextPoll();
          }
        } catch (err) {
          console.error('Error polling batch status:', err);
          // Continue polling with backoff on error
          scheduleNextPoll();
        }
      };

      const scheduleNextPoll = () => {
        // Calculate delay with exponential backoff
        // Start at 2 seconds, max at 30 seconds
        const baseDelay = 2000; // 2 seconds
        const maxDelay = 30000; // 30 seconds
        const backoffFactor = 1.5;
        
        // Calculate delay based on poll count
        let delay = Math.min(baseDelay * Math.pow(backoffFactor, pollCountRef.current), maxDelay);
        
        // If status shows active progress, poll more frequently
        if (batchStatus && batchStatus.runningInstances > 0) {
          delay = Math.min(delay, 5000); // Poll every 5 seconds when actively running
        }
        
        // Clear existing timeout
        if (pollingIntervalRef.current) {
          clearTimeout(pollingIntervalRef.current);
        }
        
        // Schedule next poll
        pollingIntervalRef.current = setTimeout(() => {
          pollCountRef.current++;
          lastPollTimeRef.current = Date.now();
          pollStatus();
        }, delay) as any;
      };

      // Initial poll
      pollStatus();
    }

    // Cleanup function
    return () => {
      if (pollingIntervalRef.current) {
        clearTimeout(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      // Reset poll counter on cleanup
      pollCountRef.current = 0;
    };
  }, [batchId, isExecuting, onExecutionComplete, batchStatus?.runningInstances]);

  const handleExecute = async () => {
    if (selectedInstances.length === 0) {
      setError('Please select at least one instance');
      return;
    }

    setError(null);
    setIsExecuting(true);
    setBatchStatus(null);
    setBatchResults(null);

    try {
      const result = await workflowService.batchExecuteWorkflow(workflow.id, {
        instanceIds: selectedInstances,
        parameters,
        name: batchName,
        description: `Batch execution of ${workflow.name} across ${selectedInstances.length} instances`
      });

      setBatchId(result.batchId);
      
      // Set initial status
      setBatchStatus({
        batchId: result.batchId,
        workflowId: workflow.id,
        name: batchName,
        status: 'running',
        totalInstances: result.totalInstances,
        completedInstances: 0,
        failedInstances: 0,
        runningInstances: result.totalInstances,
        pendingInstances: 0,
        executions: result.executions,
        statusCounts: { running: result.totalInstances }
      } as BatchStatus);
    } catch (err: any) {
      // Provide user-friendly error messages
      const errorDetail = err.response?.data?.detail;
      let userMessage = 'Failed to execute batch workflow';
      
      if (err.response?.status === 400) {
        userMessage = errorDetail || 'Invalid request parameters';
      } else if (err.response?.status === 403) {
        userMessage = 'You do not have permission to execute on one or more selected instances';
      } else if (err.response?.status === 404) {
        userMessage = 'Workflow not found';
      } else if (err.response?.status === 500) {
        userMessage = 'Server error occurred. Please try again later';
      } else if (err.code === 'ECONNABORTED' || err.code === 'ETIMEDOUT') {
        userMessage = 'Request timed out. Please try again';
      }
      
      setError(userMessage);
      setIsExecuting(false);
    }
  };

  const handleCancel = async () => {
    if (batchId && isExecuting) {
      try {
        await workflowService.cancelBatchExecution(batchId);
        setIsExecuting(false);
        // Clear polling timeout
        if (pollingIntervalRef.current) {
          clearTimeout(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        // Reset poll counter
        pollCountRef.current = 0;
      } catch (err) {
        console.error('Error cancelling batch:', err);
      }
    }
  };

  const handleDownloadResults = () => {
    if (!batchResults?.aggregatedData) return;

    const csv = [
      // Headers
      batchResults.aggregatedData.columns.map(col => col.name).join(','),
      // Data rows
      ...batchResults.aggregatedData.rows.map(row => 
        batchResults.aggregatedData!.columns.map(col => row[col.name] || '').join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${batchName.replace(/[^a-z0-9]/gi, '_')}_results.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'partial':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'failed':
        return 'text-red-600 bg-red-50';
      case 'running':
        return 'text-blue-600 bg-blue-50';
      case 'partial':
        return 'text-yellow-600 bg-yellow-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="batch-execution-title"
      aria-describedby="batch-execution-description"
    >
      <div 
        ref={modalRef}
        className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h2 id="batch-execution-title" className="text-xl font-semibold text-gray-900">
              Batch Execute Workflow
            </h2>
            <p id="batch-execution-description" className="text-sm text-gray-500 mt-1">{workflow.name}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
            aria-label="Close batch execution dialog"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Live region for status updates */}
        <div 
          role="status" 
          aria-live="polite" 
          aria-atomic="true"
          className="sr-only"
        >
          {batchStatus && `Batch execution ${batchStatus.status}. ${batchStatus.completedInstances} of ${batchStatus.totalInstances} instances completed.`}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Configuration Section */}
          {!isExecuting && !batchResults && (
            <div className="space-y-6">
              {/* Batch Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Batch Execution Name
                </label>
                <input
                  ref={batchNameInputRef}
                  type="text"
                  value={batchName}
                  onChange={(e) => setBatchName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter a name for this batch execution"
                  aria-label="Batch execution name"
                  aria-required="true"
                />
              </div>

              {/* Instance Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Instances ({selectedInstances.length} selected)
                </label>
                <MultiInstanceSelector
                  instances={instances}
                  value={selectedInstances}
                  onChange={setSelectedInstances}
                  placeholder="Select instances to execute on..."
                />
              </div>

              {/* Parameters */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Execution Parameters
                </label>
                <ParameterEditor
                  parameters={parameters}
                  onChange={setParameters}
                />
              </div>

              {/* Error Display */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                  <div className="flex">
                    <AlertCircle className="h-5 w-5 text-red-400" />
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-red-800">Execution Error</h3>
                      <p className="text-sm text-red-700 mt-1">{error}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Execution Status */}
          {batchStatus && (
            <div className="space-y-6">
              {/* Overall Status */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(batchStatus.status)}
                    <div>
                      <h3 className="font-medium text-gray-900">{batchStatus.name}</h3>
                      <p className="text-sm text-gray-500">Batch ID: {batchStatus.batchId}</p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(batchStatus.status)}`}>
                    {batchStatus.status.charAt(0).toUpperCase() + batchStatus.status.slice(1)}
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>{batchStatus.completedInstances} of {batchStatus.totalInstances} completed</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2" role="progressbar" aria-valuenow={batchStatus.completedInstances} aria-valuemin={0} aria-valuemax={batchStatus.totalInstances} aria-label="Batch execution progress">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${(batchStatus.completedInstances / batchStatus.totalInstances) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Status Counts */}
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div className="text-center">
                    <div className="text-2xl font-semibold text-gray-900">{batchStatus.pendingInstances}</div>
                    <div className="text-gray-500">Pending</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-semibold text-blue-600">{batchStatus.runningInstances}</div>
                    <div className="text-gray-500">Running</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-semibold text-green-600">{batchStatus.completedInstances}</div>
                    <div className="text-gray-500">Completed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-semibold text-red-600">{batchStatus.failedInstances}</div>
                    <div className="text-gray-500">Failed</div>
                  </div>
                </div>
              </div>

              {/* Instance Status List */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3" id="instance-status-heading">Instance Execution Status</h3>
                <div className="space-y-2 max-h-64 overflow-y-auto" role="list" aria-labelledby="instance-status-heading">
                  {batchStatus.executions.map((exec: any) => {
                    const instance = instances.find(i => i.id === exec.target_instance_id || i.instanceId === exec.instance_id);
                    return (
                      <div key={exec.id || exec.instance_id} className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-md" role="listitem">
                        <div className="flex items-center gap-3">
                          <Database className="h-4 w-4 text-gray-400" />
                          <div>
                            <div className="font-medium text-sm">{instance?.instanceName || 'Unknown Instance'}</div>
                            <div className="text-xs text-gray-500">{instance?.instanceId}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(exec.status)}
                          <span className={`px-2 py-1 text-xs rounded ${getStatusColor(exec.status)}`}>
                            {exec.status}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Results Display */}
          {batchResults && batchResults.aggregatedData && (
            <div className="space-y-4">
              {/* Results Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Batch Results</h3>
                  <p className="text-sm text-gray-500">
                    {batchResults.aggregatedData.totalRows} total rows from {batchResults.completedInstances} instances
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {/* View Mode Toggle */}
                  <div className="flex rounded-md shadow-sm" role="group" aria-label="View mode selection">
                    <button
                      onClick={() => setViewMode('table')}
                      className={`px-3 py-1 text-sm font-medium rounded-l-md border ${
                        viewMode === 'table'
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                      aria-pressed={viewMode === 'table'}
                      aria-label="Table view"
                    >
                      Table
                    </button>
                    <button
                      onClick={() => setViewMode('chart')}
                      className={`px-3 py-1 text-sm font-medium border-t border-b ${
                        viewMode === 'chart'
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                      aria-pressed={viewMode === 'chart'}
                      aria-label="Chart view"
                    >
                      Chart
                    </button>
                    <button
                      onClick={() => setViewMode('raw')}
                      className={`px-3 py-1 text-sm font-medium rounded-r-md border ${
                        viewMode === 'raw'
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                      aria-pressed={viewMode === 'raw'}
                      aria-label="Raw data view"
                    >
                      Raw
                    </button>
                  </div>
                  <button
                    onClick={handleDownloadResults}
                    className="flex items-center gap-2 px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                    aria-label="Download results as CSV file"
                  >
                    <Download className="h-4 w-4" aria-hidden="true" />
                    Download CSV
                  </button>
                </div>
              </div>

              {/* Results Content */}
              <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-auto" tabIndex={0} aria-label="Batch execution results">
                {viewMode === 'table' && (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200" role="table" aria-label="Batch execution results table">
                      <thead>
                        <tr role="row">
                          {batchResults.aggregatedData.columns.map((col) => (
                            <th
                              key={col.name}
                              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                              scope="col"
                            >
                              {col.name}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {batchResults.aggregatedData.rows.slice(0, 100).map((row, idx) => (
                          <tr key={idx} role="row">
                            {batchResults.aggregatedData!.columns.map((col) => (
                              <td key={col.name} className="px-3 py-2 text-sm text-gray-900">
                                {row[col.name] || '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {batchResults.aggregatedData.rows.length > 100 && (
                      <p className="text-sm text-gray-500 mt-2 text-center">
                        Showing first 100 of {batchResults.aggregatedData.rows.length} rows
                      </p>
                    )}
                  </div>
                )}
                {viewMode === 'chart' && (
                  <div className="text-center py-8 text-gray-500">
                    <p>Chart visualization not available</p>
                    <p className="text-sm mt-2">Switch to Table or Raw view</p>
                  </div>
                )}
                {viewMode === 'raw' && (
                  <pre className="text-xs overflow-auto">
                    {JSON.stringify(batchResults.aggregatedData, null, 2)}
                  </pre>
                )}
              </div>

              {/* Instance Results Summary */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Instance Results Summary</h4>
                <div className="grid grid-cols-2 gap-2">
                  {batchResults.instanceResults.map(result => (
                    <div key={result.instanceId} className="flex items-center justify-between p-2 bg-white border border-gray-200 rounded">
                      <div className="flex items-center gap-2">
                        <Database className="h-4 w-4 text-gray-400" />
                        <div>
                          <div className="text-sm font-medium">{result.instanceName}</div>
                          <div className="text-xs text-gray-500">{result.instanceRegion}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium">{result.rowCount} rows</div>
                        <div className="text-xs text-gray-500">{result.durationSeconds}s</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          {isExecuting ? (
            <>
              <button
                onClick={handleCancel}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                aria-label="Cancel batch execution"
              >
                Cancel Batch
              </button>
            </>
          ) : batchResults ? (
            <>
              <button
                onClick={() => {
                  setBatchResults(null);
                  setBatchStatus(null);
                  setBatchId(null);
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                aria-label="Start a new batch execution"
              >
                Run Another Batch
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                aria-label="Close batch execution dialog"
              >
                Close
              </button>
            </>
          ) : (
            <>
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                aria-label="Cancel and close dialog"
              >
                Cancel
              </button>
              <button
                onClick={handleExecute}
                disabled={selectedInstances.length === 0}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                aria-label={`Execute workflow on ${selectedInstances.length} instance${selectedInstances.length !== 1 ? 's' : ''}`}
                aria-disabled={selectedInstances.length === 0}
              >
                <Play className="h-4 w-4" aria-hidden="true" />
                Execute on {selectedInstances.length} Instance{selectedInstances.length !== 1 ? 's' : ''}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}