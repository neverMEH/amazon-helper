import { useState } from 'react';
import { AlertTriangle, XCircle, Info, Code, AlertCircle, Copy, Maximize2, CheckCircle } from 'lucide-react';
import ErrorDetailsModal from './ErrorDetailsModal';
import type { AMCErrorDetails } from '../../types/amcExecution';

interface ExecutionErrorDetailsProps {
  errorMessage?: string | null;
  errorDetails?: AMCErrorDetails;
  status?: string;
  className?: string;
  sqlQuery?: string;
  executionId?: string;
  instanceName?: string;
}

export default function ExecutionErrorDetails({ 
  errorMessage, 
  errorDetails,
  status,
  className = '',
  sqlQuery,
  executionId,
  instanceName
}: ExecutionErrorDetailsProps) {
  const [showFullError, setShowFullError] = useState(false);
  const [copiedItem, setCopiedItem] = useState<string | null>(null);
  
  if ((!errorMessage && !errorDetails) || status !== 'failed') {
    return null;
  }

  const copyToClipboard = async (text: string, itemKey: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedItem(itemKey);
      setTimeout(() => setCopiedItem(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Parse the error message to extract different sections
  const parseErrorMessage = (message: string | null | undefined) => {
    if (!message) return {};
    const sections: { [key: string]: string | string[] } = {};
    
    // Extract main error
    const mainErrorMatch = message.match(/^([^\n]+)/);
    if (mainErrorMatch) {
      sections.mainError = mainErrorMatch[1];
    }
    
    // Extract validation errors
    const validationMatch = message.match(/Validation Errors:\n([\s\S]*?)(?:\n\n|$)/);
    if (validationMatch) {
      sections.validationErrors = validationMatch[1].split('\n').filter(e => e.trim());
    }
    
    // Extract error code
    const errorCodeMatch = message.match(/Error Code:\s*(.+?)(?:\n|$)/);
    if (errorCodeMatch) {
      sections.errorCode = errorCodeMatch[1];
    }
    
    // Extract details
    const detailsMatch = message.match(/Details:\s*([\s\S]*?)(?:\n\n|$)/);
    if (detailsMatch) {
      sections.details = detailsMatch[1];
    }
    
    // Extract query validation
    const queryValidationMatch = message.match(/Query Validation:\s*([\s\S]*?)$/);
    if (queryValidationMatch) {
      sections.queryValidation = queryValidationMatch[1];
    }
    
    return sections;
  };

  // Use errorDetails if available, otherwise parse errorMessage
  const errorSections = errorDetails ? {
    mainError: errorDetails.failureReason || errorMessage,
    validationErrors: errorDetails.validationErrors,
    errorCode: errorDetails.errorCode,
    details: errorDetails.errorDetails,
    queryValidation: errorDetails.queryValidation
  } : parseErrorMessage(errorMessage);
  
  return (
    <>
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-start">
          <XCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div className="ml-3 flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-red-800">
                Query Execution Failed
              </h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => {
                    const errorText = typeof errorSections.mainError === 'string' 
                      ? errorSections.mainError 
                      : Array.isArray(errorSections.mainError) 
                        ? errorSections.mainError.join('\n')
                        : errorMessage || '';
                    copyToClipboard(errorText, 'main');
                  }}
                  className="text-red-600 hover:text-red-800"
                  title="Copy error message"
                >
                  {copiedItem === 'main' ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </button>
                <button
                  onClick={() => setShowFullError(true)}
                  className="text-red-600 hover:text-red-800"
                  title="View full error details"
                >
                  <Maximize2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          
          {/* Main Error */}
          <div className="mt-2 text-sm text-red-700">
            {typeof errorSections.mainError === 'string' 
              ? errorSections.mainError 
              : Array.isArray(errorSections.mainError)
                ? errorSections.mainError.join('\n')
                : errorMessage}
          </div>
          
          {/* Error Code */}
          {errorSections.errorCode && (
            <div className="mt-3 flex items-center text-sm">
              <Code className="h-4 w-4 text-red-500 mr-2" />
              <span className="font-medium text-red-800">Error Code:</span>
              <span className="ml-2 font-mono text-red-700">{errorSections.errorCode}</span>
            </div>
          )}
          
          {/* Validation Errors */}
          {errorSections.validationErrors && Array.isArray(errorSections.validationErrors) && (
            <div className="mt-3">
              <div className="flex items-center text-sm font-medium text-red-800 mb-2">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Validation Errors:
              </div>
              <ul className="ml-6 space-y-1">
                {errorSections.validationErrors.map((error, index) => (
                  <li key={index} className="text-sm text-red-700 list-disc">
                    {error}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Additional Details */}
          {errorSections.details && (
            <div className="mt-3">
              <div className="flex items-center text-sm font-medium text-red-800 mb-1">
                <Info className="h-4 w-4 mr-2" />
                Additional Details:
              </div>
              <div className="ml-6 text-sm text-red-700 whitespace-pre-wrap">
                {errorSections.details}
              </div>
            </div>
          )}
          
          {/* Query Validation Info */}
          {errorSections.queryValidation && (
            <div className="mt-3">
              <div className="flex items-center text-sm font-medium text-red-800 mb-1">
                <AlertCircle className="h-4 w-4 mr-2" />
                Query Validation:
              </div>
              <div className="ml-6 text-sm text-red-700 bg-red-100 rounded p-2 font-mono text-xs overflow-x-auto">
                {errorSections.queryValidation}
              </div>
            </div>
          )}
          
          {/* Common Rejection Reasons Help */}
          <details className="mt-4">
            <summary className="cursor-pointer text-sm text-red-600 hover:text-red-700 font-medium">
              Common AMC Query Rejection Reasons
            </summary>
            <div className="mt-2 ml-4 space-y-2 text-xs text-gray-600">
              <div>
                <strong>Privacy Violations:</strong> Queries that could expose individual user data or violate differential privacy thresholds.
              </div>
              <div>
                <strong>Insufficient Data:</strong> Query results that don't meet minimum aggregation requirements (typically 100+ users).
              </div>
              <div>
                <strong>Invalid Table/Column:</strong> References to tables or columns that don't exist or aren't accessible.
              </div>
              <div>
                <strong>Syntax Errors:</strong> SQL syntax issues specific to AMC's SQL dialect.
              </div>
              <div>
                <strong>Resource Limits:</strong> Queries that exceed computational or time limits.
              </div>
              <div>
                <strong>Date Range Issues:</strong> Queries spanning invalid or excessive date ranges.
              </div>
            </div>
          </details>
          </div>
        </div>
      </div>

      {/* Error Details Modal */}
      <ErrorDetailsModal
        isOpen={showFullError}
        onClose={() => setShowFullError(false)}
        errorMessage={errorMessage || undefined}
        errorDetails={errorDetails}
        sqlQuery={sqlQuery}
        executionId={executionId}
        instanceName={instanceName}
      />
    </>
  );
}