import { AlertTriangle, XCircle, Info, Code, AlertCircle } from 'lucide-react';

interface ExecutionErrorDetailsProps {
  errorMessage?: string | null;
  status?: string;
  className?: string;
}

export default function ExecutionErrorDetails({ 
  errorMessage, 
  status,
  className = '' 
}: ExecutionErrorDetailsProps) {
  
  if (!errorMessage || status !== 'failed') {
    return null;
  }

  // Parse the error message to extract different sections
  const parseErrorMessage = (message: string) => {
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

  const errorSections = parseErrorMessage(errorMessage);
  
  return (
    <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start">
        <XCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">
            Query Execution Failed
          </h3>
          
          {/* Main Error */}
          <div className="mt-2 text-sm text-red-700">
            {errorSections.mainError || errorMessage}
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
  );
}