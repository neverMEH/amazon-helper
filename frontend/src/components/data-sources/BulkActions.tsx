import { useState } from 'react';
import {
  Download,
  Copy,
  FolderOpen,
  X,
  CheckSquare,
  FileText
} from 'lucide-react';
import type { DataSource } from '../../types/dataSource';

interface BulkActionsProps {
  selectedItems: Set<string>;
  dataSources: DataSource[];
  onClearSelection: () => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
}

export function BulkActions({
  selectedItems,
  dataSources,
  onClearSelection,
  onSelectAll,
  onDeselectAll
}: BulkActionsProps) {
  const [isExporting, setIsExporting] = useState(false);
  
  const selectedDataSources = dataSources.filter(ds => selectedItems.has(ds.id));

  const handleExportSelected = async () => {
    setIsExporting(true);
    
    // Create export data
    const exportData = {
      exported_at: new Date().toISOString(),
      total_schemas: selectedDataSources.length,
      schemas: selectedDataSources.map(ds => ({
        id: ds.schema_id,
        name: ds.name,
        category: ds.category,
        description: ds.description,
        tables: ds.data_sources,
        tags: ds.tags,
        version: ds.version,
        is_paid: ds.is_paid_feature
      }))
    };

    // Create and download JSON file
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `amc-schemas-export-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setIsExporting(false);
  };

  const handleCopySchemaIds = async () => {
    const ids = selectedDataSources.map(ds => ds.schema_id).join('\n');
    await navigator.clipboard.writeText(ids);
  };

  const handleOpenInNewTabs = () => {
    selectedDataSources.slice(0, 5).forEach(ds => {
      window.open(`/data-sources/${ds.schema_id}`, '_blank');
    });
  };

  if (selectedItems.size === 0) return null;

  return (
    <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-30 animate-slide-up">
      <div className="bg-gray-900 text-white rounded-lg shadow-2xl px-6 py-4">
        <div className="flex items-center gap-6">
          {/* Selection Info */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <CheckSquare className="h-5 w-5 text-blue-400" />
              <span className="font-medium">{selectedItems.size} selected</span>
            </div>
            
            <div className="h-6 w-px bg-gray-700" />
            
            <button
              onClick={selectedItems.size === dataSources.length ? onDeselectAll : onSelectAll}
              className="text-sm text-gray-300 hover:text-white transition-colors"
            >
              {selectedItems.size === dataSources.length ? 'Deselect all' : 'Select all'}
            </button>
          </div>

          <div className="h-6 w-px bg-gray-700" />

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleExportSelected}
              disabled={isExporting}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-md transition-colors flex items-center gap-2 text-sm"
            >
              <Download className="h-4 w-4" />
              Export JSON
            </button>
            
            <button
              onClick={handleCopySchemaIds}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-md transition-colors flex items-center gap-2 text-sm"
            >
              <Copy className="h-4 w-4" />
              Copy IDs
            </button>
            
            {selectedItems.size <= 5 && (
              <button
                onClick={handleOpenInNewTabs}
                className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-md transition-colors flex items-center gap-2 text-sm"
              >
                <FolderOpen className="h-4 w-4" />
                Open in Tabs
              </button>
            )}
            
            <button
              onClick={() => {
                // Generate documentation
                const docs = selectedDataSources.map(ds => 
                  `## ${ds.name}\n\n${ds.description}\n\n**Category:** ${ds.category}\n**Tables:** ${ds.data_sources.join(', ')}\n**Tags:** ${ds.tags.join(', ')}\n`
                ).join('\n---\n\n');
                
                const blob = new Blob([docs], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `amc-schemas-docs-${Date.now()}.md`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
              }}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-md transition-colors flex items-center gap-2 text-sm"
            >
              <FileText className="h-4 w-4" />
              Export Docs
            </button>
          </div>

          <div className="h-6 w-px bg-gray-700" />

          {/* Close */}
          <button
            onClick={onClearSelection}
            className="p-1.5 hover:bg-gray-800 rounded-md transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}