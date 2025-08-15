/**
 * Data Sources List Page
 * Browse and search AMC schema documentation
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Database,
  X,
  SlidersHorizontal,
  Command,
  Filter,
  ChevronDown
} from 'lucide-react';
import { dataSourceService } from '../services/dataSourceService';
import { DataSourceCard } from '../components/data-sources/DataSourceCard';
import { DataSourcePreview } from '../components/data-sources/DataSourcePreview';
import { DataSourceCommandPalette } from '../components/data-sources/DataSourceCommandPalette';
import { DataSourceSkeleton } from '../components/data-sources/DataSourceSkeleton';
import { BulkActions } from '../components/data-sources/BulkActions';
import { AdvancedFilterBuilder, type FilterGroup } from '../components/data-sources/AdvancedFilterBuilder';
import { FilterPresets, DEFAULT_PRESETS } from '../components/data-sources/FilterPresets';
import { DataSourceCompare } from '../components/data-sources/DataSourceCompare';
import type { DataSource } from '../types/dataSource';

export default function DataSources() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  // State from URL params
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || '');
  const [selectedTags, setSelectedTags] = useState<string[]>(
    searchParams.getAll('tag') || []
  );
  // Master-detail view pattern
  const [selectedDataSourceId, setSelectedDataSourceId] = useState<string | null>(null);
  const [previewDataSource, setPreviewDataSource] = useState<DataSource | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [selectionMode, setSelectionMode] = useState(false);
  const [showAdvancedFilter, setShowAdvancedFilter] = useState(false);
  const [advancedFilter, setAdvancedFilter] = useState<FilterGroup | null>(null);
  const [filterPresets, setFilterPresets] = useState(DEFAULT_PRESETS);
  const [activePresetId, setActivePresetId] = useState<string>('all');
  const [showCompareMode, setShowCompareMode] = useState(false);
  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);

  // Fetch data sources
  const { data: dataSources = [], isLoading } = useQuery({
    queryKey: ['dataSources', { search, category: selectedCategory, tags: selectedTags }],
    queryFn: () => dataSourceService.listDataSources({
      search: search || undefined,
      category: selectedCategory || undefined,
      tags: selectedTags.length > 0 ? selectedTags : undefined
    }),
    staleTime: 5 * 60 * 1000
  });

  // Fetch categories
  const { data: categories = [] } = useQuery({
    queryKey: ['dataSourceCategories'],
    queryFn: () => dataSourceService.getCategories(),
    staleTime: 10 * 60 * 1000
  });

  // Fetch popular tags
  const { data: popularTags = [] } = useQuery({
    queryKey: ['dataSourceTags'],
    queryFn: () => dataSourceService.getPopularTags(30),
    staleTime: 10 * 60 * 1000
  });

  // Update URL params when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (selectedCategory) params.set('category', selectedCategory);
    selectedTags.forEach(tag => params.append('tag', tag));
    setSearchParams(params);
  }, [search, selectedCategory, selectedTags, setSearchParams]);

  const handleTagToggle = (tag: string) => {
    setSelectedTags(prev =>
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const clearFilters = () => {
    setSearch('');
    setSelectedCategory('');
    setSelectedTags([]);
  };

  const hasActiveFilters = search || selectedCategory || selectedTags.length > 0;

  // Single click selects and shows preview
  const handleDataSourceClick = useCallback((dataSource: DataSource) => {
    setSelectedDataSourceId(dataSource.id);
    if (showPreview) {
      setPreviewDataSource(dataSource);
    }
  }, [showPreview]);

  // Double click opens full details
  const handleDataSourceDoubleClick = useCallback((dataSource: DataSource) => {
    console.log('Double-click navigating to:', `/data-sources/${dataSource.schema_id}`);
    navigate(`/data-sources/${dataSource.schema_id}`);
  }, [navigate]);

  // Navigate to details (from preview or action button)
  const handleViewDetails = useCallback((dataSource: DataSource) => {
    navigate(`/data-sources/${dataSource.schema_id}`);
  }, [navigate]);

  const handlePreview = useCallback((dataSource: DataSource) => {
    if (!showPreview) {
      setShowPreview(true);
    }
    setSelectedDataSourceId(dataSource.id);
    setPreviewDataSource(dataSource);
  }, [showPreview]);

  const handleSelect = useCallback((id: string, selected: boolean) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(id);
      } else {
        newSet.delete(id);
      }
      return newSet;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    setSelectedIds(new Set(dataSources.map(ds => ds.id)));
  }, [dataSources]);

  const handleDeselectAll = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  // Keyboard shortcuts and navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't handle navigation if typing in search
      const isSearching = document.activeElement?.id === 'search-input';
      
      // Cmd/Ctrl + K for command palette
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setShowCommandPalette(true);
      }
      // Cmd/Ctrl + A to select all
      if ((e.metaKey || e.ctrlKey) && e.key === 'a' && selectionMode) {
        e.preventDefault();
        handleSelectAll();
      }
      // Escape to clear search or close preview
      if (e.key === 'Escape') {
        if (isSearching) {
          setSearch('');
        } else if (previewDataSource) {
          setPreviewDataSource(null);
          setSelectedDataSourceId(null);
        }
      }
      
      // Arrow key navigation (when not searching)
      if (!isSearching && dataSources.length > 0) {
        const currentIndex = dataSources.findIndex(ds => ds.id === selectedDataSourceId);
        
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          const nextIndex = currentIndex < dataSources.length - 1 ? currentIndex + 1 : 0;
          const nextDataSource = dataSources[nextIndex];
          handleDataSourceClick(nextDataSource);
        }
        
        if (e.key === 'ArrowUp') {
          e.preventDefault();
          const prevIndex = currentIndex > 0 ? currentIndex - 1 : dataSources.length - 1;
          const prevDataSource = dataSources[prevIndex];
          handleDataSourceClick(prevDataSource);
        }
        
        // Enter to open details
        if (e.key === 'Enter' && selectedDataSourceId) {
          const selectedDataSource = dataSources.find(ds => ds.id === selectedDataSourceId);
          if (selectedDataSource) {
            handleDataSourceDoubleClick(selectedDataSource);
          }
        }
        
        // Space to toggle preview panel
        if (e.key === ' ' && !isSearching) {
          e.preventDefault();
          setShowPreview(prev => !prev);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectionMode, handleSelectAll, dataSources, selectedDataSourceId, previewDataSource, handleDataSourceClick, handleDataSourceDoubleClick]);

  // Enable selection mode when items are selected
  useEffect(() => {
    if (selectedIds.size > 0) {
      setSelectionMode(true);
    }
  }, [selectedIds]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (showCategoryDropdown && !(e.target as HTMLElement).closest('.category-dropdown')) {
        setShowCategoryDropdown(false);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [showCategoryDropdown]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-20">
        <div className="px-6">
          <div className="py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                  <Database className="h-6 w-6" />
                  AMC Data Sources
                </h1>
                <p className="mt-1 text-sm text-gray-500">
                  Browse and search Amazon Marketing Cloud schema documentation
                </p>
                <p className="mt-0.5 text-xs text-gray-400">
                  Double-click to open details • ↑↓ arrows to navigate • Space to toggle preview
                </p>
              </div>
              <div className="flex items-center gap-2">
                {/* Selection Mode Toggle */}
                <button
                  onClick={() => {
                    setSelectionMode(!selectionMode);
                    if (selectionMode) {
                      setSelectedIds(new Set());
                    }
                  }}
                  className={`px-3 py-1.5 rounded text-sm font-medium transition-colors flex items-center gap-1 ${
                    selectionMode
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-600 hover:text-gray-900'
                  }`}
                  title="Toggle Selection Mode"
                >
                  <Command className="h-4 w-4" />
                  <span className="text-xs">{selectionMode ? 'Exit' : 'Select'}</span>
                </button>
                {/* Preview Toggle */}
                <button
                  onClick={() => setShowPreview(!showPreview)}
                  className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                    showPreview
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-600 hover:text-gray-900'
                  }`}
                  title="Toggle Preview Panel"
                >
                  <SlidersHorizontal className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Search and Filters Bar */}
            <div className="mt-4 flex gap-3">
              {/* Search Input */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="search-input"
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Type to filter results or press ⌘K for advanced search..."
                  className="w-full pl-10 pr-20 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
                  <button
                    onClick={() => setShowAdvancedFilter(true)}
                    className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 border border-gray-300 rounded hover:bg-gray-200 transition-colors"
                    title="Advanced Filter"
                  >
                    <Filter className="h-3 w-3" />
                    Filter
                  </button>
                  <button
                    onClick={() => setShowCommandPalette(true)}
                    className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 border border-gray-300 rounded hover:bg-gray-200 transition-colors"
                  >
                    <Command className="h-3 w-3" />K
                  </button>
                </div>
              </div>

              {/* Category Dropdown */}
              <div className="relative category-dropdown">
                <button
                  onClick={() => setShowCategoryDropdown(!showCategoryDropdown)}
                  className={`px-4 py-2.5 border rounded-lg flex items-center gap-2 transition-colors ${
                    selectedCategory 
                      ? 'bg-blue-50 border-blue-300 text-blue-700' 
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <span className="text-sm font-medium">
                    {selectedCategory || 'All Categories'}
                  </span>
                  <ChevronDown className="h-4 w-4" />
                </button>
                
                {showCategoryDropdown && (
                  <div className="absolute top-full left-0 mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-30">
                    <div className="py-1">
                      <button
                        onClick={() => {
                          setSelectedCategory('');
                          setShowCategoryDropdown(false);
                        }}
                        className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                          !selectedCategory ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
                        }`}
                      >
                        All Categories
                        <span className="float-right text-xs text-gray-500">
                          {dataSources.length}
                        </span>
                      </button>
                      {categories.map(category => {
                        const count = dataSources.filter(ds => ds.category === category).length;
                        return (
                          <button
                            key={category}
                            onClick={() => {
                              setSelectedCategory(category);
                              setShowCategoryDropdown(false);
                            }}
                            className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                              selectedCategory === category ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
                            }`}
                          >
                            {category}
                            <span className="float-right text-xs text-gray-500">
                              {count}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Tag Filters */}
            <div className="mt-3 flex items-center gap-2">
              <span className="text-xs text-gray-500 font-medium">Quick filters:</span>
              <div className="flex flex-wrap gap-1.5">
                {popularTags.slice(0, 8).map(({ tag, count }) => (
                  <button
                    key={tag}
                    onClick={() => handleTagToggle(tag)}
                    className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-colors ${
                      selectedTags.includes(tag)
                        ? 'bg-green-100 text-green-700 font-medium'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {tag}
                    <span className="text-gray-400 text-xs">({count})</span>
                  </button>
                ))}
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="text-xs text-red-600 hover:text-red-700 underline ml-2"
                  >
                    Clear all
                  </button>
                )}
              </div>
            </div>

            {/* Filter Presets */}
            <div className="mt-3">
              <FilterPresets
                presets={filterPresets}
                activePresetId={activePresetId}
                onSelectPreset={(preset) => {
                  setActivePresetId(preset.id);
                  setAdvancedFilter(preset.filter);
                  console.log('Applying preset:', preset);
                }}
                onCreateNew={() => setShowAdvancedFilter(true)}
                onDeletePreset={(id) => {
                  setFilterPresets(filterPresets.filter(p => p.id !== id));
                  if (activePresetId === id) {
                    setActivePresetId('all');
                  }
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-220px)]">
        {/* Main Content Area - Full Width */}
        <main className="flex-1 overflow-y-auto bg-gray-50">
          <div className="p-6">
            {/* Results Header */}
            {!isLoading && (
              <div className="mb-4 flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Showing <span className="font-semibold">{dataSources.length}</span> results
                  {hasActiveFilters && ' (filtered)'}
                </p>
                {selectedIds.size > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">
                      {selectedIds.size} selected
                    </span>
                    <button
                      onClick={() => setSelectedIds(new Set())}
                      className="text-sm text-blue-600 hover:text-blue-700"
                    >
                      Clear selection
                    </button>
                  </div>
                )}
              </div>
            )}

            {isLoading ? (
              <DataSourceSkeleton count={8} />
            ) : dataSources.length === 0 ? (
              <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
                <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No data sources found</h3>
                <p className="text-gray-500">
                  {hasActiveFilters
                    ? 'Try adjusting your filters or search query'
                    : 'No data sources are available yet'}
                </p>
              </div>
            ) : (
              // List Table View
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <table className="min-w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Data Source
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tables
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Fields
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Audience Types
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Joins With
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Data Freshness
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Use Cases
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {dataSources.map(dataSource => (
                      <DataSourceCard
                        key={dataSource.id}
                        dataSource={dataSource}
                        onClick={() => handleDataSourceClick(dataSource)}
                        onDoubleClick={() => handleDataSourceDoubleClick(dataSource)}
                        onPreview={() => handlePreview(dataSource)}
                        onViewDetails={() => handleViewDetails(dataSource)}
                        isSelected={selectedDataSourceId === dataSource.id}
                        isChecked={selectedIds.has(dataSource.id)}
                        searchQuery={search}
                        onSelect={handleSelect}
                        selectionMode={selectionMode}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </main>

        {/* Preview Panel */}
        {showPreview && (
          <aside className="w-[400px] flex-shrink-0 border-l bg-white overflow-hidden">
            <DataSourcePreview
              dataSource={previewDataSource}
              onClose={() => {
                setPreviewDataSource(null);
                setSelectedDataSourceId(null);
              }}
              onOpenDetail={handleViewDetails}
            />
          </aside>
        )}
      </div>

      {/* Command Palette */}
      <DataSourceCommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
      />

      {/* Bulk Actions Bar */}
      <BulkActions
        selectedItems={selectedIds}
        dataSources={dataSources}
        onClearSelection={() => {
          setSelectedIds(new Set());
          setSelectionMode(false);
        }}
        onSelectAll={handleSelectAll}
        onDeselectAll={handleDeselectAll}
        onCompare={() => setShowCompareMode(true)}
      />

      {/* Advanced Filter Builder */}
      <AdvancedFilterBuilder
        isOpen={showAdvancedFilter}
        onClose={() => setShowAdvancedFilter(false)}
        onApply={(filter) => {
          setAdvancedFilter(filter);
          console.log('Applying advanced filter:', filter);
        }}
        currentFilter={advancedFilter || undefined}
      />

      {/* Compare Mode */}
      <DataSourceCompare
        isOpen={showCompareMode}
        onClose={() => setShowCompareMode(false)}
        dataSourceIds={Array.from(selectedIds)}
        dataSources={dataSources}
      />
    </div>
  );
}