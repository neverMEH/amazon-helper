import React, { useState, useCallback, useRef } from 'react';
import { X, Upload, FileText, AlertCircle, CheckCircle, Info } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import asinService, { type ImportResponse, type ImportStatus } from '../../services/asinService';
import LoadingSpinner from '../LoadingSpinner';

interface ASINImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const ASINImportModal: React.FC<ASINImportModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [updateExisting, setUpdateExisting] = useState(true);
  const [importStatus, setImportStatus] = useState<ImportStatus | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Import mutation
  const importMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('No file selected');
      return asinService.importASINs(file, updateExisting);
    },
    onSuccess: async (data: ImportResponse) => {
      if (data.import_id) {
        // Start polling for import status
        pollImportStatus(data.import_id);
      } else {
        toast.error(data.message || 'Import failed');
      }
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Import failed');
    }
  });

  // Poll import status
  const pollImportStatus = useCallback(async (importId: string) => {
    const checkStatus = async () => {
      try {
        const status = await asinService.getImportStatus(importId);
        setImportStatus(status);
        
        if (status.status === 'completed') {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
          toast.success(`Import completed: ${status.successful_imports} ASINs imported`);
          setTimeout(() => {
            onSuccess();
          }, 2000);
        } else if (status.status === 'failed') {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
          toast.error('Import failed. Check the error details.');
        }
      } catch (error) {
        console.error('Error polling status:', error);
      }
    };

    // Initial check
    checkStatus();
    
    // Poll every 2 seconds
    pollIntervalRef.current = setInterval(checkStatus, 2000);
  }, [onSuccess]);

  // Clean up polling on unmount
  React.useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.size > 50 * 1024 * 1024) {
        toast.error('File size must be less than 50MB');
        return;
      }
      setFile(selectedFile);
    }
  };

  // Handle drag and drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (droppedFile.size > 50 * 1024 * 1024) {
        toast.error('File size must be less than 50MB');
        return;
      }
      setFile(droppedFile);
    }
  };

  // Handle import
  const handleImport = () => {
    if (!file) {
      toast.error('Please select a file');
      return;
    }
    importMutation.mutate();
  };

  // Reset modal
  const handleClose = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
    setFile(null);
    setImportStatus(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold">Import ASINs</h2>
            <p className="text-sm text-gray-600 mt-1">
              Upload a CSV or TSV file containing ASIN data
            </p>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-500"
            disabled={importMutation.isPending}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {!importStatus ? (
            <>
              {/* File Upload Area */}
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  isDragging 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.txt,.tsv"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                
                {file ? (
                  <div className="space-y-4">
                    <FileText className="w-12 h-12 text-green-500 mx-auto" />
                    <div>
                      <p className="font-medium">{file.name}</p>
                      <p className="text-sm text-gray-600">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="text-blue-600 hover:text-blue-700 text-sm"
                    >
                      Choose Different File
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <Upload className="w-12 h-12 text-gray-400 mx-auto" />
                    <div>
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="text-blue-600 hover:text-blue-700 font-medium"
                      >
                        Choose File
                      </button>
                      <p className="text-sm text-gray-600 mt-1">
                        or drag and drop here
                      </p>
                    </div>
                    <p className="text-xs text-gray-500">
                      CSV, TSV, or TXT files up to 50MB
                    </p>
                  </div>
                )}
              </div>

              {/* File Format Info */}
              <div className="mt-6 bg-blue-50 rounded-lg p-4">
                <div className="flex items-start">
                  <Info className="w-5 h-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
                  <div className="text-sm text-gray-700">
                    <p className="font-medium mb-2">Expected file format (tab-delimited):</p>
                    <ul className="space-y-1 ml-4">
                      <li>• <strong>ASIN</strong> - Product ASIN (required)</li>
                      <li>• <strong>TITLE</strong> - Product title</li>
                      <li>• <strong>BRAND</strong> - Brand name</li>
                      <li>• <strong>MARKETPLACE</strong> - Marketplace ID (optional)</li>
                      <li>• <strong>ACTIVE</strong> - Active status (1 or 0)</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Options */}
              <div className="mt-6">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={updateExisting}
                    onChange={(e) => setUpdateExisting(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Update existing ASINs if found
                  </span>
                </label>
              </div>
            </>
          ) : (
            /* Import Status */
            <div className="space-y-6">
              {importStatus.status === 'processing' ? (
                <div className="text-center">
                  <LoadingSpinner />
                  <p className="mt-4 text-gray-600">Processing import...</p>
                </div>
              ) : importStatus.status === 'completed' ? (
                <div className="text-center">
                  <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-green-600">Import Completed!</h3>
                  <div className="mt-4 space-y-2 text-sm">
                    <p>Total Rows: {importStatus.total_rows}</p>
                    <p>Successfully Imported: {importStatus.successful_imports}</p>
                    {importStatus.failed_imports > 0 && (
                      <p className="text-red-600">Failed: {importStatus.failed_imports}</p>
                    )}
                    {importStatus.duplicate_skipped && importStatus.duplicate_skipped > 0 && (
                      <p className="text-yellow-600">Duplicates: {importStatus.duplicate_skipped}</p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center">
                  <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-red-600">Import Failed</h3>
                  {importStatus.error_details && (
                    <div className="mt-4 text-sm text-left bg-red-50 p-4 rounded">
                      <pre className="whitespace-pre-wrap">
                        {JSON.stringify(importStatus.error_details, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 py-4 bg-gray-50 border-t">
          {!importStatus && (
            <>
              <button
                onClick={handleClose}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                disabled={importMutation.isPending}
              >
                Cancel
              </button>
              <button
                onClick={handleImport}
                disabled={!file || importMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {importMutation.isPending && <LoadingSpinner size="sm" />}
                Start Import
              </button>
            </>
          )}
          {importStatus?.status === 'completed' && (
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ASINImportModal;