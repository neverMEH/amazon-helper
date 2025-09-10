import React from 'react';
import { ExclamationTriangleIcon, XCircleIcon } from '@heroicons/react/24/outline';

interface ErrorMessageProps {
  title?: string;
  message: string;
  type?: 'error' | 'warning';
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'Error',
  message,
  type = 'error',
  onRetry,
  onDismiss,
  className = '',
}) => {
  const isError = type === 'error';
  const Icon = isError ? XCircleIcon : ExclamationTriangleIcon;
  
  const baseClasses = 'rounded-md p-4';
  const typeClasses = isError
    ? 'bg-red-50 border border-red-200'
    : 'bg-yellow-50 border border-yellow-200';
  
  const iconClasses = isError
    ? 'text-red-400'
    : 'text-yellow-400';
    
  const textClasses = isError
    ? 'text-red-800'
    : 'text-yellow-800';
    
  const buttonClasses = isError
    ? 'bg-red-50 text-red-800 hover:bg-red-100 focus:ring-red-600'
    : 'bg-yellow-50 text-yellow-800 hover:bg-yellow-100 focus:ring-yellow-600';

  return (
    <div className={`${baseClasses} ${typeClasses} ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <Icon className={`h-5 w-5 ${iconClasses}`} aria-hidden="true" />
        </div>
        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${textClasses}`}>
            {title}
          </h3>
          <div className={`mt-2 text-sm ${textClasses}`}>
            <p>{message}</p>
          </div>
          {(onRetry || onDismiss) && (
            <div className="mt-4">
              <div className="-mx-2 -my-1.5 flex">
                {onRetry && (
                  <button
                    type="button"
                    onClick={onRetry}
                    className={`px-2 py-1.5 rounded-md text-sm font-medium ${buttonClasses} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-red-50`}
                  >
                    Retry
                  </button>
                )}
                {onDismiss && (
                  <button
                    type="button"
                    onClick={onDismiss}
                    className={`ml-3 px-2 py-1.5 rounded-md text-sm font-medium ${buttonClasses} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-red-50`}
                  >
                    Dismiss
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorMessage;