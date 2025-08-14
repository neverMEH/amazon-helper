import { useState } from 'react';
import { X, Copy, Download, AlertTriangle, Code, FileText, Eye, CheckCircle } from 'lucide-react';
import type { AMCErrorDetails } from '../../types/amcExecution';
import SQLEditor from '../common/SQLEditor';

interface ErrorDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  errorMessage?: string;
  errorDetails?: AMCErrorDetails;
  sqlQuery?: string;
  executionId?: string;
  instanceName?: string;
}

export default function ErrorDetailsModal({
  isOpen,
  onClose,
  errorMessage,
  errorDetails,
  sqlQuery,
  executionId,
  instanceName
}: ErrorDetailsModalProps) {
  const [viewMode, setViewMode] = useState<'structured' | 'raw' | 'sql'>('structured');
  const [copiedItem, setCopiedItem] = useState<string | null>(null);

  if (!isOpen) return null;

  const copyToClipboard = async (text: string, itemKey: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedItem(itemKey);
      setTimeout(() => setCopiedItem(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const downloadErrorReport = () => {
    const report = {
      executionId,
      instanceName,
      timestamp: new Date().toISOString(),
      errorMessage,
      errorDetails,
      sqlQuery
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `amc-error-${executionId || 'unknown'}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getRawErrorText = () => {
    const parts: string[] = [];
    
    if (errorMessage) {
      parts.push(`Error Message:\n${errorMessage}`);
    }
    
    if (errorDetails) {
      if (errorDetails.failureReason) {
        parts.push(`\nFailure Reason:\n${errorDetails.failureReason}`);
      }
      
      if (errorDetails.validationErrors && errorDetails.validationErrors.length > 0) {
        parts.push(`\nValidation Errors:\n${errorDetails.validationErrors.join('\n')}`);
      }
      
      if (errorDetails.errorCode) {
        parts.push(`\nError Code: ${errorDetails.errorCode}`);
      }
      
      if (errorDetails.queryValidation) {
        parts.push(`\nQuery Validation:\n${errorDetails.queryValidation}`);
      }
      
      if (errorDetails.errorDetails) {
        parts.push(`\nAdditional Details:\n${errorDetails.errorDetails}`);
      }
    }
    
    return parts.join('\n');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[70]">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-red-50 border-b border-red-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <AlertTriangle className="h-6 w-6 text-red-500 mr-3" />
              <div>
                <h2 className="text-lg font-semibold text-red-900">AMC Query Execution Error</h2>
                {executionId && (
                  <p className="text-sm text-red-600 mt-1">
                    Execution ID: {executionId}
                    {instanceName && ` • Instance: ${instanceName}`}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-red-500 hover:text-red-700"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Action Bar */}
        <div className="bg-gray-50 border-b px-6 py-3">
          <div className="flex items-center justify-between">
            {/* View Mode Tabs */}
            <div className="flex space-x-1">
              <button
                onClick={() => setViewMode('structured')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'structured'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <FileText className="h-4 w-4 inline-block mr-2" />
                Structured
              </button>
              <button
                onClick={() => setViewMode('raw')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'raw'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Eye className="h-4 w-4 inline-block mr-2" />
                Raw
              </button>
              {sqlQuery && (
                <button
                  onClick={() => setViewMode('sql')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    viewMode === 'sql'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Code className="h-4 w-4 inline-block mr-2" />
                  SQL Query
                </button>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-2">
              <button
                onClick={() => copyToClipboard(getRawErrorText(), 'full')}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                {copiedItem === 'full' ? (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2 text-green-500" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 mr-2" />
                    Copy All
                  </>
                )}
              </button>
              <button
                onClick={downloadErrorReport}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <Download className="h-4 w-4 mr-2" />
                Download Report
              </button>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 180px)' }}>
          {viewMode === 'structured' && (
            <div className="space-y-6">
              {/* Main Error Message */}
              {errorMessage && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-sm font-semibold text-red-800 mb-2">Error Message</h3>
                      <p className="text-sm text-red-700 whitespace-pre-wrap">{errorMessage}</p>
                    </div>
                    <button
                      onClick={() => copyToClipboard(errorMessage, 'message')}
                      className="ml-3 text-red-500 hover:text-red-700"
                    >
                      {copiedItem === 'message' ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Error Details */}
              {errorDetails && (
                <>
                  {/* Error Code */}
                  {errorDetails.errorCode && (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="text-sm font-semibold text-gray-800 mb-2">Error Code</h3>
                          <code className="text-sm bg-gray-100 px-2 py-1 rounded text-gray-700 font-mono">
                            {errorDetails.errorCode}
                          </code>
                        </div>
                        <button
                          onClick={() => copyToClipboard(errorDetails.errorCode!, 'code')}
                          className="ml-3 text-gray-500 hover:text-gray-700"
                        >
                          {copiedItem === 'code' ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Validation Errors */}
                  {errorDetails.validationErrors && errorDetails.validationErrors.length > 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <h3 className="text-sm font-semibold text-yellow-800 mb-3">Validation Errors</h3>
                      <ul className="space-y-2">
                        {errorDetails.validationErrors.map((error, index) => (
                          <li key={index} className="flex justify-between items-start">
                            <span className="text-sm text-yellow-700 flex-1">
                              • {error}
                            </span>
                            <button
                              onClick={() => copyToClipboard(error, `validation-${index}`)}
                              className="ml-3 text-yellow-500 hover:text-yellow-700"
                            >
                              {copiedItem === `validation-${index}` ? (
                                <CheckCircle className="h-4 w-4 text-green-500" />
                              ) : (
                                <Copy className="h-4 w-4" />
                              )}
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Query Validation */}
                  {errorDetails.queryValidation && (
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="text-sm font-semibold text-orange-800 mb-2">Query Validation</h3>
                          <pre className="text-sm text-orange-700 whitespace-pre-wrap font-mono bg-orange-100 p-3 rounded overflow-x-auto">
                            {errorDetails.queryValidation}
                          </pre>
                        </div>
                        <button
                          onClick={() => copyToClipboard(errorDetails.queryValidation!, 'queryValidation')}
                          className="ml-3 text-orange-500 hover:text-orange-700"
                        >
                          {copiedItem === 'queryValidation' ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Additional Details */}
                  {errorDetails.errorDetails && (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="text-sm font-semibold text-gray-800 mb-2">Additional Details</h3>
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">{errorDetails.errorDetails}</p>
                        </div>
                        <button
                          onClick={() => copyToClipboard(errorDetails.errorDetails!, 'details')}
                          className="ml-3 text-gray-500 hover:text-gray-700"
                        >
                          {copiedItem === 'details' ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Common Issues Help */}
              <details className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <summary className="cursor-pointer text-sm font-semibold text-blue-800 hover:text-blue-900">
                  Common AMC Query Issues & Solutions
                </summary>
                <div className="mt-4 space-y-3 text-sm text-blue-700">
                  <div>
                    <strong>Syntax Errors:</strong>
                    <ul className="ml-4 mt-1 list-disc">
                      <li>Check for missing commas between columns</li>
                      <li>Verify all parentheses and quotes are matched</li>
                      <li>Ensure table and column names are spelled correctly</li>
                    </ul>
                  </div>
                  <div>
                    <strong>Privacy Violations:</strong>
                    <ul className="ml-4 mt-1 list-disc">
                      <li>Ensure queries aggregate to at least 100 users</li>
                      <li>Avoid selecting individual user-level data</li>
                      <li>Use appropriate aggregation functions (COUNT, SUM, AVG)</li>
                    </ul>
                  </div>
                  <div>
                    <strong>Date Range Issues:</strong>
                    <ul className="ml-4 mt-1 list-disc">
                      <li>Use format: YYYY-MM-DDTHH:MM:SS (no 'Z' suffix)</li>
                      <li>Account for 14-day data lag in AMC</li>
                      <li>Ensure date range doesn't exceed 400 days</li>
                    </ul>
                  </div>
                  <div>
                    <strong>Table/Column Not Found:</strong>
                    <ul className="ml-4 mt-1 list-disc">
                      <li>Verify table names match AMC schema exactly</li>
                      <li>Check if tables require specific permissions</li>
                      <li>Some tables may be region or instance-specific</li>
                    </ul>
                  </div>
                </div>
              </details>
            </div>
          )}

          {viewMode === 'raw' && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-sm font-semibold text-gray-800">Raw Error Output</h3>
                <button
                  onClick={() => copyToClipboard(getRawErrorText(), 'raw')}
                  className="text-gray-500 hover:text-gray-700"
                >
                  {copiedItem === 'raw' ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </button>
              </div>
              <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-white p-4 rounded border border-gray-300 overflow-x-auto">
                {getRawErrorText()}
              </pre>
            </div>
          )}

          {viewMode === 'sql' && sqlQuery && (
            <div>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-sm font-semibold text-gray-800">Failed SQL Query</h3>
                <button
                  onClick={() => copyToClipboard(sqlQuery, 'sql')}
                  className="inline-flex items-center text-gray-500 hover:text-gray-700"
                >
                  {copiedItem === 'sql' ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 mr-2" />
                      Copy SQL
                    </>
                  )}
                </button>
              </div>
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <SQLEditor
                  value={sqlQuery}
                  readOnly={true}
                  height="400px"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}