import { useState } from 'react';
import { X, GitBranch, Copy, History } from 'lucide-react';
import type { QueryTemplate } from '../../types/queryTemplate';
import SQLEditor from '../common/SQLEditor';
import { queryTemplateService } from '../../services/queryTemplateService';
import toast from 'react-hot-toast';

interface TemplateForkDialogProps {
  isOpen: boolean;
  onClose: () => void;
  template: QueryTemplate;
  onForked?: (newTemplate: QueryTemplate) => void;
}

export default function TemplateForkDialog({
  isOpen,
  onClose,
  template,
  onForked
}: TemplateForkDialogProps) {
  const [forkName, setForkName] = useState(`${template.name} (Fork)`);
  const [forkDescription, setForkDescription] = useState(template.description || '');
  const [forkSql, setForkSql] = useState(template.sqlTemplate || template.sql_query || '');
  const [isPrivate, setIsPrivate] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [showVersionHistory, setShowVersionHistory] = useState(false);

  if (!isOpen) return null;

  const handleFork = async () => {
    if (!forkName.trim()) {
      toast.error('Please provide a name for your fork');
      return;
    }

    setIsSaving(true);
    try {
      const forkedTemplate = await queryTemplateService.forkTemplate(template.id, {
        name: forkName,
        description: forkDescription,
        sql_query: forkSql,
        is_public: !isPrivate,
        parent_template_id: template.id,
        version: 1,
      });

      toast.success('Template forked successfully');
      if (onForked) {
        onForked(forkedTemplate);
      }
      onClose();
    } catch (error: any) {
      toast.error(error.message || 'Failed to fork template');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <GitBranch className="h-5 w-5 text-indigo-600" />
            <h2 className="text-xl font-semibold text-gray-900">
              Fork Template
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500 focus:outline-none"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Original Template Info */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-700">Forking from:</h3>
              <button
                onClick={() => setShowVersionHistory(!showVersionHistory)}
                className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
              >
                <History className="h-4 w-4" />
                Version History
              </button>
            </div>
            <p className="font-medium text-gray-900">{template.name}</p>
            {template.description && (
              <p className="text-sm text-gray-600 mt-1">{template.description}</p>
            )}
            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
              {template.usageCount !== undefined && (
                <span>Used {template.usageCount} times</span>
              )}
              {/* Created by and version fields not available in QueryTemplate type */}
            </div>
          </div>

          {/* Version History (collapsible) */}
          {showVersionHistory && (
            <div className="bg-blue-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-blue-900 mb-2">Version History</h4>
              <div className="space-y-2">
                {/* Version history not available in QueryTemplate type */}
                {[].map((version: any, index: number) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-blue-700">v{version.version}</span>
                      <span className="text-blue-600">{version.date}</span>
                    </div>
                    <span className="text-blue-600">{version.changes}</span>
                  </div>
                )) || (
                  <p className="text-sm text-blue-700">No version history available</p>
                )}
              </div>
            </div>
          )}

          {/* Fork Details */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Fork Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={forkName}
                onChange={(e) => setForkName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter a name for your fork"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={forkDescription}
                onChange={(e) => setForkDescription(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Describe your modifications..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                SQL Query
              </label>
              <div className="border border-gray-300 rounded-md overflow-hidden">
                <SQLEditor
                  value={forkSql}
                  onChange={setForkSql}
                  height="300px"
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Modify the SQL query as needed for your fork
              </p>
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={isPrivate}
                  onChange={(e) => setIsPrivate(e.target.checked)}
                  className="mr-2 text-indigo-600 focus:ring-indigo-500 rounded"
                />
                <span className="text-sm text-gray-700">Keep this fork private</span>
              </label>
              <span className="text-xs text-gray-500">
                {isPrivate ? 'Only you can see and use this fork' : 'Others in your organization can discover and use this fork'}
              </span>
            </div>
          </div>

          {/* Fork Attribution */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <Copy className="h-4 w-4 text-yellow-600 mt-0.5" />
              <div className="text-sm">
                <p className="text-yellow-800 font-medium">Fork Attribution</p>
                <p className="text-yellow-700 text-xs mt-1">
                  This fork will be linked to the original template. The original author will be credited,
                  and users can trace back to the source template.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md
                     hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
          <button
            onClick={handleFork}
            disabled={isSaving || !forkName.trim()}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md
                     hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                     disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Creating Fork...
              </>
            ) : (
              <>
                <GitBranch className="h-4 w-4" />
                Create Fork
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}