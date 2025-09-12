import { useState } from 'react';
import { Code, ChevronDown, ChevronUp, Copy, Edit3, AlertCircle } from 'lucide-react';
import SQLHighlight from '../common/SQLHighlight';
import toast from 'react-hot-toast';

interface SQLPreviewProps {
  sql: string | null | undefined;
  maxLines?: number;
  className?: string;
  onEdit?: () => void;
  showActions?: boolean;
}

export default function SQLPreview({ 
  sql, 
  maxLines = 3, 
  className = '',
  onEdit,
  showActions = true 
}: SQLPreviewProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Handle empty or missing SQL
  if (!sql || sql.trim() === '') {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-700">No SQL query defined yet</p>
            <p className="text-xs text-gray-500 mt-1">
              Click "Edit" to add SQL to this template using the Monaco editor
            </p>
            {onEdit && (
              <button
                onClick={onEdit}
                className="mt-2 inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 transition-colors"
              >
                <Edit3 className="h-3 w-3 mr-1" />
                Add SQL Query
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Calculate if SQL needs truncation
  const lines = sql.split('\n');
  const needsTruncation = lines.length > maxLines;
  const displaySQL = needsTruncation && !isExpanded 
    ? lines.slice(0, maxLines).join('\n') + '\n...'
    : sql;

  const handleCopySQL = () => {
    navigator.clipboard.writeText(sql);
    toast.success('SQL copied to clipboard');
  };

  return (
    <div className={`relative group ${className}`}>
      {/* SQL Preview Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center text-xs text-gray-500">
          <Code className="h-3 w-3 mr-1" />
          <span>SQL Query</span>
          {needsTruncation && !isExpanded && (
            <span className="ml-2 text-amber-600">
              ({lines.length - maxLines} more lines)
            </span>
          )}
        </div>
        
        {showActions && (
          <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleCopySQL}
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title="Copy SQL"
            >
              <Copy className="h-3 w-3" />
            </button>
            {onEdit && (
              <button
                onClick={onEdit}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                title="Edit in Monaco Editor"
              >
                <Edit3 className="h-3 w-3" />
              </button>
            )}
            {needsTruncation && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                title={isExpanded ? 'Collapse' : 'Expand'}
              >
                {isExpanded ? (
                  <ChevronUp className="h-3 w-3" />
                ) : (
                  <ChevronDown className="h-3 w-3" />
                )}
              </button>
            )}
          </div>
        )}
      </div>

      {/* SQL Content */}
      <div className={`overflow-hidden transition-all duration-200 ${
        isExpanded ? 'max-h-96' : `max-h-${maxLines * 6}`
      }`}>
        <div className="text-xs">
          <SQLHighlight sql={displaySQL} className="!p-3 !text-xs" />
        </div>
      </div>

      {/* Expand/Collapse Button (alternative position) */}
      {needsTruncation && !showActions && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium"
        >
          {isExpanded ? 'Show less' : `Show ${lines.length - maxLines} more lines`}
        </button>
      )}
    </div>
  );
}