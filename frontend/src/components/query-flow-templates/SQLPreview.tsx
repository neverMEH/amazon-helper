import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, RefreshCw, Copy, Check } from 'lucide-react';
import { queryFlowTemplateService } from '../../services/queryFlowTemplateService';
import type { ParameterFormValues } from '../../types/queryFlowTemplate';
import SQLEditor from '../common/SQLEditor';

interface SQLPreviewProps {
  templateId: string;
  parameters: ParameterFormValues;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  className?: string;
}

const SQLPreview: React.FC<SQLPreviewProps> = ({
  templateId,
  parameters,
  isCollapsed = false,
  onToggleCollapse,
  className = ''
}) => {
  const [previewData, setPreviewData] = useState<{
    sql: string;
    parameter_count: number;
    estimated_cost?: number;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Fetch preview when parameters change
  useEffect(() => {
    const fetchPreview = async () => {
      if (!templateId || Object.keys(parameters).length === 0) {
        setPreviewData(null);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await queryFlowTemplateService.previewSQL(templateId, parameters);
        setPreviewData(response);
      } catch (err: any) {
        console.error('Error fetching SQL preview:', err);
        setError(err.response?.data?.detail || 'Failed to generate SQL preview');
        setPreviewData(null);
      } finally {
        setIsLoading(false);
      }
    };

    // Debounce the preview request
    const timeoutId = setTimeout(fetchPreview, 500);
    return () => clearTimeout(timeoutId);
  }, [templateId, parameters]);

  const handleRefresh = () => {
    // Force immediate refresh
    if (templateId && Object.keys(parameters).length > 0) {
      setIsLoading(true);
      setError(null);

      queryFlowTemplateService.previewSQL(templateId, parameters)
        .then(response => {
          setPreviewData(response);
        })
        .catch(err => {
          console.error('Error refreshing SQL preview:', err);
          setError(err.response?.data?.detail || 'Failed to generate SQL preview');
          setPreviewData(null);
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  };

  const handleCopySQL = async () => {
    if (!previewData?.sql) return;

    try {
      await navigator.clipboard.writeText(previewData.sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy SQL:', err);
    }
  };

  return (
    <div className={`border border-gray-200 rounded-lg ${className}`}>
      {/* Header */}
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-medium text-gray-700">SQL Preview</h3>
            {isLoading && (
              <RefreshCw className="h-4 w-4 text-gray-400 animate-spin" />
            )}
            {previewData && (
              <span className="text-xs text-gray-500">
                {previewData.parameter_count} parameter{previewData.parameter_count !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {previewData?.sql && (
              <button
                onClick={handleCopySQL}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                title="Copy SQL"
              >
                {copied ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>
            )}
            
            <button
              onClick={handleRefresh}
              disabled={isLoading || !templateId}
              className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Refresh preview"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            
            {onToggleCollapse && (
              <button
                onClick={onToggleCollapse}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                title={isCollapsed ? 'Show preview' : 'Hide preview'}
              >
                {isCollapsed ? (
                  <Eye className="h-4 w-4" />
                ) : (
                  <EyeOff className="h-4 w-4" />
                )}
              </button>
            )}
          </div>
        </div>

        {previewData?.estimated_cost && (
          <div className="mt-2 text-xs text-gray-600">
            Estimated cost: ${previewData.estimated_cost.toFixed(4)}
          </div>
        )}
      </div>

      {/* Content */}
      {!isCollapsed && (
        <div className="p-4">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
              <div className="flex items-center">
                <div className="text-sm text-red-700">
                  <strong>Preview Error:</strong> {error}
                </div>
              </div>
            </div>
          )}

          {!previewData && !error && !isLoading && (
            <div className="text-center py-8 text-gray-500">
              <p className="text-sm">
                Configure template parameters to see SQL preview
              </p>
            </div>
          )}

          {isLoading && (
            <div className="text-center py-8 text-gray-500">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
              <p className="text-sm">Generating SQL preview...</p>
            </div>
          )}

          {previewData && !error && (
            <div className="space-y-3">
              <div className="bg-gray-900 rounded-lg overflow-hidden">
                <SQLEditor
                  value={previewData.sql}
                  height="300px"
                  readOnly={true}
                  options={{
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    fontSize: 12,
                    theme: 'vs-dark'
                  }}
                />
              </div>

              {/* Parameter summary */}
              {Object.keys(parameters).length > 0 && (
                <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
                  <h4 className="text-xs font-medium text-gray-700 mb-2">
                    Active Parameters ({previewData.parameter_count})
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {Object.entries(parameters)
                      .filter(([, value]) => value != null && value !== '')
                      .map(([key, value]) => (
                        <div key={key} className="flex">
                          <span className="font-medium text-gray-600 mr-2 truncate">
                            {key}:
                          </span>
                          <span className="text-gray-800 truncate">
                            {Array.isArray(value) 
                              ? `[${value.length} items]`
                              : typeof value === 'object'
                              ? JSON.stringify(value)
                              : String(value)
                            }
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SQLPreview;