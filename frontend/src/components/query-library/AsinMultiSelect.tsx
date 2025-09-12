import React, { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { X, Upload, Search, AlertCircle, Check, Copy, Trash2 } from 'lucide-react';
import { FixedSizeList as List } from 'react-window';

interface AsinMultiSelectProps {
  value: string[];
  onChange: (asins: string[]) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  maxItems?: number;
  className?: string;
}

// ASIN validation regex - Amazon's standard format
const ASIN_REGEX = /^B[0-9A-Z]{9}$/;

// Validate ASIN format
const isValidAsin = (asin: string): boolean => {
  return ASIN_REGEX.test(asin.trim().toUpperCase());
};

// Parse ASINs from text with various separators
const parseAsins = (text: string): string[] => {
  // Split by common separators: comma, newline, tab, space, semicolon
  const asins = text
    .split(/[,\n\t\s;]+/)
    .map(asin => asin.trim().toUpperCase())
    .filter(asin => asin.length > 0);
  
  // Remove duplicates
  return [...new Set(asins)];
};

export default function AsinMultiSelect({
  value = [],
  onChange,
  placeholder = 'Enter ASINs...',
  required = false,
  disabled = false,
  error,
  maxItems = 1000,
  className = ''
}: AsinMultiSelectProps) {
  const [inputValue, setInputValue] = useState('');
  const [searchFilter, setSearchFilter] = useState('');
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkInput, setBulkInput] = useState('');
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [successMessage, setSuccessMessage] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const bulkTextareaRef = useRef<HTMLTextAreaElement>(null);

  // Filter displayed ASINs based on search
  const filteredAsins = useMemo(() => {
    if (!searchFilter) return value;
    const filter = searchFilter.toLowerCase();
    return value.filter(asin => asin.toLowerCase().includes(filter));
  }, [value, searchFilter]);

  // Add single ASIN
  const handleAddAsin = useCallback(() => {
    const asin = inputValue.trim().toUpperCase();
    
    if (!asin) return;
    
    if (!isValidAsin(asin)) {
      setValidationErrors([`Invalid ASIN format: ${asin}`]);
      setTimeout(() => setValidationErrors([]), 3000);
      return;
    }
    
    if (value.includes(asin)) {
      setValidationErrors([`ASIN already added: ${asin}`]);
      setTimeout(() => setValidationErrors([]), 3000);
      return;
    }
    
    if (value.length >= maxItems) {
      setValidationErrors([`Maximum ${maxItems} ASINs allowed`]);
      setTimeout(() => setValidationErrors([]), 3000);
      return;
    }
    
    onChange([...value, asin]);
    setInputValue('');
    setSuccessMessage(`Added ${asin}`);
    setTimeout(() => setSuccessMessage(''), 2000);
  }, [inputValue, value, onChange, maxItems]);

  // Remove ASIN
  const handleRemoveAsin = useCallback((asinToRemove: string) => {
    onChange(value.filter(asin => asin !== asinToRemove));
  }, [value, onChange]);

  // Clear all ASINs
  const handleClearAll = useCallback(() => {
    onChange([]);
    setSearchFilter('');
    setSuccessMessage('Cleared all ASINs');
    setTimeout(() => setSuccessMessage(''), 2000);
  }, [onChange]);

  // Handle bulk paste
  const handleBulkImport = useCallback(() => {
    const asins = parseAsins(bulkInput);
    const errors: string[] = [];
    const validAsins: string[] = [];
    const duplicates: string[] = [];
    
    asins.forEach(asin => {
      if (!isValidAsin(asin)) {
        errors.push(asin);
      } else if (value.includes(asin)) {
        duplicates.push(asin);
      } else {
        validAsins.push(asin);
      }
    });
    
    if (errors.length > 0) {
      setValidationErrors([
        `${errors.length} invalid ASIN${errors.length > 1 ? 's' : ''}: ${errors.slice(0, 5).join(', ')}${errors.length > 5 ? '...' : ''}`
      ]);
    }
    
    if (value.length + validAsins.length > maxItems) {
      const allowed = maxItems - value.length;
      validAsins.splice(allowed);
      setValidationErrors(prev => [
        ...prev,
        `Only ${allowed} ASINs added due to ${maxItems} item limit`
      ]);
    }
    
    if (validAsins.length > 0) {
      onChange([...value, ...validAsins]);
      setSuccessMessage(
        `Added ${validAsins.length} ASIN${validAsins.length > 1 ? 's' : ''}${duplicates.length > 0 ? ` (${duplicates.length} duplicate${duplicates.length > 1 ? 's' : ''} skipped)` : ''}`
      );
      setTimeout(() => setSuccessMessage(''), 3000);
      setShowBulkModal(false);
      setBulkInput('');
    }
    
    if (errors.length > 0) {
      setTimeout(() => setValidationErrors([]), 5000);
    }
  }, [bulkInput, value, onChange, maxItems]);

  // Copy ASINs to clipboard
  const handleCopyToClipboard = useCallback(() => {
    const text = value.join('\n');
    navigator.clipboard.writeText(text).then(() => {
      setSuccessMessage('Copied to clipboard');
      setTimeout(() => setSuccessMessage(''), 2000);
    });
  }, [value]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && inputRef.current === document.activeElement) {
        e.preventDefault();
        handleAddAsin();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleAddAsin]);

  // Row renderer for virtualized list
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const asin = filteredAsins[index];
    return (
      <div
        style={style}
        className="flex items-center justify-between px-2 py-1 hover:bg-gray-50"
        data-testid="asin-tag"
      >
        <span className="text-sm font-mono">{asin}</span>
        <button
          onClick={() => handleRemoveAsin(asin)}
          className="text-gray-400 hover:text-red-600 p-1"
          aria-label={`Remove ${asin}`}
          disabled={disabled}
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    );
  };

  const showError = error || (required && value.length === 0 && 'This field is required');

  return (
    <div className={`${className}`}>
      {/* Header with controls */}
      <div className="flex items-center justify-between mb-2">
        <label className="block text-sm font-medium text-gray-700" aria-label="ASIN input">
          ASINs
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <div className="flex items-center space-x-2">
          {value.length > 0 && (
            <>
              <span className="text-xs text-gray-500" role="status">
                {value.length} ASIN{value.length !== 1 ? 's' : ''} selected
              </span>
              <button
                onClick={handleCopyToClipboard}
                className="p-1 text-gray-400 hover:text-gray-600"
                title="Copy ASINs"
                disabled={disabled}
              >
                <Copy className="h-4 w-4" />
              </button>
              <button
                onClick={handleClearAll}
                className="p-1 text-gray-400 hover:text-red-600"
                aria-label="Clear all"
                disabled={disabled || value.length === 0}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Input field */}
      <div className="flex space-x-2 mb-2">
        <div className="flex-1 relative">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={placeholder}
            disabled={disabled}
            className={`
              w-full px-3 py-2 border rounded-md
              ${showError ? 'border-red-300' : 'border-gray-300'}
              ${disabled ? 'bg-gray-50 cursor-not-allowed' : 'bg-white'}
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
            `}
            aria-label="ASIN input"
          />
        </div>
        <button
          onClick={handleAddAsin}
          disabled={disabled || !inputValue.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Add
        </button>
        <button
          onClick={() => setShowBulkModal(true)}
          disabled={disabled}
          className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
          aria-label="Bulk paste"
        >
          <Upload className="h-4 w-4 inline mr-2" />
          Bulk Paste
        </button>
      </div>

      {/* Search filter for large lists */}
      {value.length > 10 && (
        <div className="relative mb-2">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="Search ASINs..."
            className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {/* ASIN list - virtualized for performance */}
      {filteredAsins.length > 0 && (
        <div className="border border-gray-200 rounded-md">
          {filteredAsins.length > 20 ? (
            <List
              height={200}
              itemCount={filteredAsins.length}
              itemSize={32}
              width="100%"
            >
              {Row}
            </List>
          ) : (
            <div className="max-h-[200px] overflow-y-auto">
              {filteredAsins.map(asin => (
                <div
                  key={asin}
                  className="flex items-center justify-between px-2 py-1 hover:bg-gray-50"
                  data-testid="asin-tag"
                >
                  <span className="text-sm font-mono">{asin}</span>
                  <button
                    onClick={() => handleRemoveAsin(asin)}
                    className="text-gray-400 hover:text-red-600 p-1"
                    aria-label={`Remove ${asin}`}
                    disabled={disabled}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Error messages */}
      {showError && (
        <div className="mt-2 text-sm text-red-600 flex items-center">
          <AlertCircle className="h-4 w-4 mr-1" />
          {showError}
        </div>
      )}

      {/* Validation errors */}
      {validationErrors.length > 0 && (
        <div className="mt-2 space-y-1">
          {validationErrors.map((err, idx) => (
            <div key={idx} className="text-sm text-red-600 flex items-center">
              <AlertCircle className="h-4 w-4 mr-1" />
              {err}
            </div>
          ))}
        </div>
      )}

      {/* Success message */}
      {successMessage && (
        <div className="mt-2 text-sm text-green-600 flex items-center">
          <Check className="h-4 w-4 mr-1" />
          {successMessage}
        </div>
      )}

      {/* Bulk paste modal */}
      {showBulkModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Bulk Paste ASINs</h3>
              <button
                onClick={() => {
                  setShowBulkModal(false);
                  setBulkInput('');
                  setValidationErrors([]);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <p className="text-sm text-gray-600 mb-4">
              Paste ASINs separated by commas, spaces, tabs, or new lines. 
              Duplicates will be automatically removed.
            </p>
            
            <textarea
              ref={bulkTextareaRef}
              value={bulkInput}
              onChange={(e) => setBulkInput(e.target.value)}
              placeholder="B08N5WRWNW, B07XJ8C8F5, B09B3S4KGC..."
              className="w-full h-64 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Bulk input"
              autoFocus
            />
            
            <div className="mt-4 flex justify-between items-center">
              <div className="text-sm text-gray-500">
                {bulkInput && (
                  <span>
                    Found {parseAsins(bulkInput).length} potential ASIN{parseAsins(bulkInput).length !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
              <div className="space-x-2">
                <button
                  onClick={() => {
                    setShowBulkModal(false);
                    setBulkInput('');
                    setValidationErrors([]);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleBulkImport}
                  disabled={!bulkInput.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  aria-label="Import"
                >
                  Import ASINs
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}