/**
 * Parameter Preview Panel Component
 *
 * Displays a collapsible SQL preview with parameter substitution.
 * Uses Monaco Editor in read-only mode for syntax highlighting.
 */

import { ChevronDown, ChevronUp, Eye } from 'lucide-react';
import Editor from '@monaco-editor/react';

export interface ParameterPreviewPanelProps {
  /** The SQL query to display (with or without parameters substituted) */
  sqlQuery: string;
  /** Whether the panel is currently expanded */
  isOpen: boolean;
  /** Callback when the user toggles the panel */
  onToggle: () => void;
  /** Optional CSS class names */
  className?: string;
}

/**
 * ParameterPreviewPanel Component
 *
 * A collapsible panel that displays SQL queries in a read-only Monaco Editor
 * with syntax highlighting. Useful for previewing final SQL after parameter
 * substitution.
 */
export default function ParameterPreviewPanel({
  sqlQuery,
  isOpen,
  onToggle,
  className = ''
}: ParameterPreviewPanelProps) {
  return (
    <div
      className={`border border-gray-300 rounded-lg shadow-sm bg-white ${className}`}
    >
      {/* Header / Toggle Button */}
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors rounded-t-lg"
        aria-expanded={isOpen}
        aria-label="SQL Preview - Click to toggle"
      >
        <div className="flex items-center space-x-2">
          <Eye className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">
            SQL Preview
          </span>
          <span className="text-xs text-gray-500">
            (Read-only)
          </span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-gray-500" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-500" />
        )}
      </button>

      {/* Expandable Content */}
      {isOpen && (
        <div className="border-t border-gray-200">
          <div className="p-4">
            {/* Monaco Editor */}
            <div className="border border-gray-200 rounded-md overflow-hidden">
              <Editor
                height="400px"
                language="sql"
                value={sqlQuery || ''}
                theme="vs"
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  fontSize: 13,
                  lineNumbers: 'on',
                  folding: true,
                  wordWrap: 'on',
                  automaticLayout: true,
                  renderLineHighlight: 'none',
                  contextmenu: false,
                  selectionHighlight: false,
                  occurrencesHighlight: 'off',
                  renderWhitespace: 'none',
                  cursorStyle: 'line',
                  cursorBlinking: 'solid',
                }}
                loading={
                  <div className="flex items-center justify-center h-full">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                }
              />
            </div>

            {/* Helper Text */}
            <p className="mt-2 text-xs text-gray-500">
              This preview shows your SQL query with all parameters substituted. The editor is read-only.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
