import React, { useState } from 'react';
import {
  ArrowDownTrayIcon,
  ShareIcon,
  DocumentTextIcon,
  TableCellsIcon,
  ChartBarIcon,
  ClipboardDocumentIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import * as reportDashboardService from '../../services/reportDashboardService';

interface ExportShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  collectionId: string;
  dashboardData: any;
  activeConfig?: any;
}

type ExportFormat = 'csv' | 'excel' | 'pdf' | 'json';

const ExportShareModal: React.FC<ExportShareModalProps> = ({
  isOpen,
  onClose,
  collectionId,
  dashboardData,
  activeConfig,
}) => {
  const [activeTab, setActiveTab] = useState<'export' | 'share'>('export');
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('csv');
  const [isExporting, setIsExporting] = useState(false);
  const [snapshotName, setSnapshotName] = useState('');
  const [snapshotDescription, setSnapshotDescription] = useState('');
  const [isCreatingSnapshot, setIsCreatingSnapshot] = useState(false);
  const [shareLink, setShareLink] = useState('');
  const [linkCopied, setLinkCopied] = useState(false);

  if (!isOpen) return null;

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const exportData = await reportDashboardService.exportDashboardData(
        collectionId,
        selectedFormat
      );
      
      // Create download link
      const blob = new Blob([exportData], { 
        type: selectedFormat === 'csv' ? 'text/csv' : 'application/json' 
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dashboard-export-${new Date().toISOString().split('T')[0]}.${selectedFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      // Show success message
      onClose();
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const handleCreateSnapshot = async () => {
    if (!snapshotName.trim()) return;
    
    setIsCreatingSnapshot(true);
    try {
      const snapshot = await reportDashboardService.createSnapshot(collectionId, {
        name: snapshotName,
        description: snapshotDescription,
        data: dashboardData,
        config: activeConfig,
      });
      
      // Generate share link
      const link = `${window.location.origin}/shared/dashboard/${snapshot.id}`;
      setShareLink(link);
    } catch (error) {
      console.error('Failed to create snapshot:', error);
    } finally {
      setIsCreatingSnapshot(false);
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(shareLink);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  };

  const exportFormats = [
    { value: 'csv', label: 'CSV', icon: TableCellsIcon, description: 'Comma-separated values' },
    { value: 'excel', label: 'Excel', icon: TableCellsIcon, description: 'Microsoft Excel format' },
    { value: 'pdf', label: 'PDF', icon: DocumentTextIcon, description: 'Portable document format' },
    { value: 'json', label: 'JSON', icon: ChartBarIcon, description: 'Raw data format' },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold">Export & Share Dashboard</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            aria-label="Close"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('export')}
            className={`flex-1 px-4 py-3 text-sm font-medium ${
              activeTab === 'export'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            data-testid="export-button"
          >
            <div className="flex items-center justify-center gap-2">
              <ArrowDownTrayIcon className="w-4 h-4" />
              Export Data
            </div>
          </button>
          <button
            onClick={() => setActiveTab('share')}
            className={`flex-1 px-4 py-3 text-sm font-medium ${
              activeTab === 'share'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            data-testid="share-button"
          >
            <div className="flex items-center justify-center gap-2">
              <ShareIcon className="w-4 h-4" />
              Share Dashboard
            </div>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === 'export' && (
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-4">Select Export Format</h4>
              <div className="space-y-2">
                {exportFormats.map((format) => (
                  <label
                    key={format.value}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                      selectedFormat === format.value ? 'border-indigo-600 bg-indigo-50' : 'border-gray-200'
                    }`}
                  >
                    <input
                      type="radio"
                      value={format.value}
                      checked={selectedFormat === format.value}
                      onChange={(e) => setSelectedFormat(e.target.value as ExportFormat)}
                      className="sr-only"
                      data-testid={`export-${format.value}`}
                    />
                    <format.icon className="w-5 h-5 text-gray-400 mr-3" />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{format.label}</div>
                      <div className="text-xs text-gray-500">{format.description}</div>
                    </div>
                    {selectedFormat === format.value && (
                      <CheckIcon className="w-5 h-5 text-indigo-600" />
                    )}
                  </label>
                ))}
              </div>
              <div className="mt-6 flex justify-end">
                <button
                  onClick={handleExport}
                  disabled={isExporting}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  data-testid="confirm-export"
                >
                  {isExporting ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Exporting...
                    </span>
                  ) : (
                    `Export as ${selectedFormat.toUpperCase()}`
                  )}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'share' && (
            <div>
              {!shareLink ? (
                <>
                  <h4 className="text-sm font-medium text-gray-900 mb-4">Create Shareable Snapshot</h4>
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="snapshot-name" className="block text-sm font-medium text-gray-700 mb-1">
                        Snapshot Name *
                      </label>
                      <input
                        id="snapshot-name"
                        type="text"
                        value={snapshotName}
                        onChange={(e) => setSnapshotName(e.target.value)}
                        placeholder="e.g., Q4 2024 Performance Dashboard"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
                        data-testid="snapshot-name"
                      />
                    </div>
                    <div>
                      <label htmlFor="snapshot-description" className="block text-sm font-medium text-gray-700 mb-1">
                        Description (Optional)
                      </label>
                      <textarea
                        id="snapshot-description"
                        value={snapshotDescription}
                        onChange={(e) => setSnapshotDescription(e.target.value)}
                        placeholder="Add notes about this snapshot..."
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                  </div>
                  <div className="mt-6 flex justify-end">
                    <button
                      onClick={handleCreateSnapshot}
                      disabled={!snapshotName.trim() || isCreatingSnapshot}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      data-testid="create-snapshot"
                    >
                      {isCreatingSnapshot ? (
                        <span className="flex items-center gap-2">
                          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          Creating...
                        </span>
                      ) : (
                        'Create Snapshot'
                      )}
                    </button>
                  </div>
                </>
              ) : (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-4">Share Link Created!</h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <input
                        type="text"
                        value={shareLink}
                        readOnly
                        className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded-l-lg text-sm"
                        data-testid="share-link"
                      />
                      <button
                        onClick={handleCopyLink}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-r-lg hover:bg-indigo-700 flex items-center gap-2"
                        data-testid="copy-link"
                      >
                        {linkCopied ? (
                          <>
                            <CheckIcon className="w-4 h-4" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <ClipboardDocumentIcon className="w-4 h-4" />
                            Copy
                          </>
                        )}
                      </button>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      Anyone with this link can view the dashboard snapshot
                    </p>
                  </div>
                  <div className="mt-6 flex justify-between">
                    <button
                      onClick={() => {
                        setShareLink('');
                        setSnapshotName('');
                        setSnapshotDescription('');
                      }}
                      className="px-4 py-2 text-gray-700 hover:text-gray-900"
                    >
                      Create Another
                    </button>
                    <button
                      onClick={onClose}
                      className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                    >
                      Done
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Validation error */}
        {activeTab === 'share' && !snapshotName.trim() && snapshotName !== '' && (
          <div className="px-6 pb-4">
            <p className="text-sm text-red-600" data-testid="validation-error">
              Name is required
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExportShareModal;