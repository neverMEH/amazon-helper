import { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Database,
  Table,
  Code,
  Hash,
  X,
  CornerDownLeft
} from 'lucide-react';
import { dataSourceService } from '../../services/dataSourceService';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

type SearchResult = {
  type: 'schema' | 'field' | 'example';
  id: string;
  title: string;
  subtitle: string;
  path?: string;
  data?: unknown;
};

export function DataSourceCommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Fetch all data sources for searching
  const { data: dataSources = [] } = useQuery({
    queryKey: ['dataSources'],
    queryFn: () => dataSourceService.listDataSources(),
    staleTime: 5 * 60 * 1000,
    enabled: isOpen
  });

  // Search fields across all schemas
  const { data: fieldResults = [] } = useQuery({
    queryKey: ['fieldSearch', query],
    queryFn: () => dataSourceService.searchFields(query, 20),
    enabled: isOpen && query.length > 2,
    staleTime: 30 * 1000
  });

  // Combine and filter results
  const searchResults = useMemo(() => {
    if (!query) return [];

    const results: SearchResult[] = [];
    const lowerQuery = query.toLowerCase();

    // Search schemas
    dataSources
      .filter(ds => 
        ds.name.toLowerCase().includes(lowerQuery) ||
        ds.description.toLowerCase().includes(lowerQuery) ||
        ds.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
      )
      .slice(0, 5)
      .forEach(ds => {
        results.push({
          type: 'schema',
          id: ds.id,
          title: ds.name,
          subtitle: `${ds.category} • ${ds.description.substring(0, 60)}...`,
          path: `/data-sources/${ds.schema_id}`,
          data: ds
        });
      });

    // Add field search results
    fieldResults.slice(0, 5).forEach(field => {
      results.push({
        type: 'field',
        id: field.id,
        title: field.field_name,
        subtitle: `${field.data_source.name} • ${field.dimension_or_metric} • ${field.data_type}`,
        path: `/data-sources/${field.data_source.schema_id}#schema`,
        data: field
      });
    });

    return results;
  }, [query, dataSources, fieldResults]);

  // Reset selected index when results change
  useEffect(() => {
    setSelectedIndex(0);
  }, [searchResults]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev < searchResults.length - 1 ? prev + 1 : prev
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => prev > 0 ? prev - 1 : 0);
          break;
        case 'Enter':
          e.preventDefault();
          if (searchResults[selectedIndex]) {
            handleSelect(searchResults[selectedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, searchResults, selectedIndex, onClose]);

  // Scroll selected item into view
  useEffect(() => {
    if (resultsRef.current) {
      const selectedElement = resultsRef.current.children[selectedIndex] as HTMLElement;
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedIndex]);

  const handleSelect = (result: SearchResult) => {
    if (result.path) {
      navigate(result.path);
    }
    onClose();
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'schema':
        return Database;
      case 'field':
        return Table;
      case 'example':
        return Code;
      default:
        return Hash;
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Command Palette */}
      <div className="fixed inset-x-0 top-20 mx-auto max-w-2xl z-50">
        <div className="bg-white rounded-lg shadow-2xl overflow-hidden">
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search schemas, fields, examples..."
              className="w-full pl-12 pr-12 py-4 text-lg border-b border-gray-200 focus:outline-none"
            />
            <button
              onClick={onClose}
              className="absolute right-4 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
            >
              <X className="h-5 w-5 text-gray-400" />
            </button>
          </div>

          {/* Results */}
          {query && (
            <div ref={resultsRef} className="max-h-96 overflow-y-auto">
              {searchResults.length === 0 ? (
                <div className="px-4 py-8 text-center text-gray-500">
                  No results found for "{query}"
                </div>
              ) : (
                <>
                  {/* Group results by type */}
                  {['schema', 'field', 'example'].map(type => {
                    const typeResults = searchResults.filter(r => r.type === type);
                    if (typeResults.length === 0) return null;

                    const Icon = getIcon(type);
                    return (
                      <div key={type}>
                        <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
                          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                            <Icon className="h-3 w-3" />
                            {type === 'schema' ? 'Schemas' : type === 'field' ? 'Fields' : 'Examples'}
                          </span>
                        </div>
                        {typeResults.map((result) => {
                          const globalIndex = searchResults.indexOf(result);
                          return (
                            <button
                              key={result.id}
                              onClick={() => handleSelect(result)}
                              className={`w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors ${
                                globalIndex === selectedIndex ? 'bg-blue-50' : ''
                              }`}
                              onMouseEnter={() => setSelectedIndex(globalIndex)}
                            >
                              <div className="flex items-center gap-3">
                                <Icon className="h-4 w-4 text-gray-400" />
                                <div className="text-left">
                                  <div className="font-medium text-gray-900">
                                    {highlightMatch(result.title, query)}
                                  </div>
                                  <div className="text-sm text-gray-500">
                                    {result.subtitle}
                                  </div>
                                </div>
                              </div>
                              {globalIndex === selectedIndex && (
                                <div className="flex items-center gap-1 text-xs text-gray-400">
                                  <span>Open</span>
                                  <CornerDownLeft className="h-3 w-3" />
                                </div>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    );
                  })}
                </>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white border border-gray-300 rounded">↑↓</kbd>
                Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white border border-gray-300 rounded">⏎</kbd>
                Select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white border border-gray-300 rounded">Esc</kbd>
                Close
              </span>
            </div>
            {searchResults.length > 0 && (
              <span>{searchResults.length} results</span>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

// Helper function to highlight matching text
function highlightMatch(text: string, query: string): React.ReactElement {
  if (!query) return <>{text}</>;
  
  const parts = text.split(new RegExp(`(${query})`, 'gi'));
  return (
    <>
      {parts.map((part, i) => 
        part.toLowerCase() === query.toLowerCase() ? (
          <mark key={i} className="bg-yellow-200 text-gray-900">{part}</mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
}