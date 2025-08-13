/**
 * Data Sources List Page
 * Browse and search AMC schema documentation
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Database,
  X,
  Grid3x3,
  List,
  SlidersHorizontal,
  Command
} from 'lucide-react';
import { dataSourceService } from '../services/dataSourceService';
import { DataSourceCard } from '../components/data-sources/DataSourceCard';
import { DataSourcePreview } from '../components/data-sources/DataSourcePreview';
import { DataSourceCommandPalette } from '../components/data-sources/DataSourceCommandPalette';
import { DataSourceSkeleton } from '../components/data-sources/DataSourceSkeleton';
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
  const [viewMode, setViewMode] = useState<'card' | 'compact'>(searchParams.get('view') as 'card' | 'compact' || 'card');
  const [previewDataSource, setPreviewDataSource] = useState<DataSource | null>(null);
  const [showPreview, setShowPreview] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [selectionMode, setSelectionMode] = useState(false);

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

  // Group data sources by category
  const groupedDataSources = useMemo(() => {
    const groups: Record<string, DataSource[]> = {};
    dataSources.forEach(ds => {
      if (!groups[ds.category]) {
        groups[ds.category] = [];
      }
      groups[ds.category].push(ds);
    });
    return groups;
  }, [dataSources]);

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

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
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
      // Escape to clear search
      if (e.key === 'Escape' && document.activeElement?.id === 'search-input') {
        setSearch('');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectionMode, handleSelectAll]);

  const handleDataSourceClick = useCallback((dataSource: DataSource) => {
    navigate(`/data-sources/${dataSource.schema_id}`);
  }, [navigate]);

  const handlePreview = useCallback((dataSource: DataSource) => {
    if (showPreview) {
      setPreviewDataSource(dataSource);
    }
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

  // Enable selection mode when items are selected
  useEffect(() => {
    if (selectedIds.size > 0) {
      setSelectionMode(true);
    }
  }, [selectedIds]);

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
              </div>
              <div className="flex items-center gap-2">
                {/* View Mode Toggle */}
                <div className="flex items-center bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => setViewMode('card')}
                    className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                      viewMode === 'card'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                    title="Card View"
                  >
                    <Grid3x3 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setViewMode('compact')}
                    className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                      viewMode === 'compact'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                    title="List View"
                  >
                    <List className="h-4 w-4" />
                  </button>
                </div>
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

            {/* Search Bar */}
            <div className="mt-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="search-input"
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Type to filter results or press ⌘K for advanced search..."
                  className="w-full pl-10 pr-20 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  onClick={() => setShowCommandPalette(true)}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 border border-gray-300 rounded hover:bg-gray-200 transition-colors"
                >
                  <Command className="h-3 w-3" />K
                </button>
              </div>
            </div>

            {/* Active Filters Summary */}
            {hasActiveFilters && (
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <span className="text-sm text-gray-500">Active filters:</span>
                {selectedCategory && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-md text-sm">
                    {selectedCategory}
                    <button
                      onClick={() => setSelectedCategory('')}
                      className="hover:text-blue-900"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                )}
                {selectedTags.map(tag => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-md text-sm"
                  >
                    {tag}
                    <button
                      onClick={() => handleTagToggle(tag)}
                      className="hover:text-green-900"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
                <button
                  onClick={clearFilters}
                  className="text-sm text-gray-500 hover:text-gray-700 underline"
                >
                  Clear all
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-180px)]">
        {/* Sidebar Filters */}
        <aside className="w-64 flex-shrink-0 bg-white border-r overflow-y-auto">
          <div className="p-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">Filters</h3>

            {/* Categories */}
            <div className="mb-6">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Category</h4>
              <div className="space-y-1">
                <button
                  onClick={() => setSelectedCategory('')}
                  className={`w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors ${
                    !selectedCategory
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  All Categories
                  {!selectedCategory && (
                    <span className="float-right text-xs bg-blue-600 text-white px-1.5 py-0.5 rounded">
                      {dataSources.length}
                    </span>
                  )}
                </button>
                {categories.map(category => {
                  const count = dataSources.filter(ds => ds.category === category).length;
                  return (
                    <button
                      key={category}
                      onClick={() => setSelectedCategory(category)}
                      className={`w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors flex items-center justify-between ${
                        selectedCategory === category
                          ? 'bg-blue-100 text-blue-700 font-medium'
                          : 'text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <span>{category}</span>
                      {selectedCategory === category && (
                        <span className="text-xs bg-blue-600 text-white px-1.5 py-0.5 rounded">
                          {count}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Popular Tags */}
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Popular Tags</h4>
              <div className="flex flex-wrap gap-1.5">
                {popularTags.slice(0, 12).map(({ tag, count }) => (
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
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
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
              <DataSourceSkeleton viewMode={viewMode} count={8} />
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
            ) : viewMode === 'compact' ? (
              // Compact Table View
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden animate-fade-in">
                <table className="min-w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Category
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Stats
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Complexity
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tags
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {dataSources.map(dataSource => (
                      <DataSourceCard
                        key={dataSource.id}
                        dataSource={dataSource}
                        onClick={() => handleDataSourceClick(dataSource)}
                        onPreview={handlePreview}
                        isSelected={selectedIds.has(dataSource.id)}
                        viewMode="compact"
                        searchQuery={search}
                        onSelect={handleSelect}
                        selectionMode={selectionMode}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            ) : selectedCategory ? (
              // Show filtered results as cards
              <div className="grid gap-4 grid-cols-1 xl:grid-cols-2 animate-fade-in">
                {dataSources.map(dataSource => (
                  <DataSourceCard
                    key={dataSource.id}
                    dataSource={dataSource}
                    onClick={() => handleDataSourceClick(dataSource)}
                    onPreview={handlePreview}
                    isSelected={selectedIds.has(dataSource.id)}
                    searchQuery={search}
                    onSelect={handleSelect}
                    selectionMode={selectionMode}
                  />
                ))}
              </div>
            ) : (
              // Show grouped by category
              <div className="space-y-8 animate-fade-in">
                {Object.entries(groupedDataSources).map(([category, sources]) => (
                  <div key={category}>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
                      {category}
                      <span className="ml-2 text-sm font-normal text-gray-500">
                        ({sources.length} {sources.length === 1 ? 'schema' : 'schemas'})
                      </span>
                    </h2>
                    <div className="grid gap-4 grid-cols-1 xl:grid-cols-2">
                      {sources.map(dataSource => (
                        <DataSourceCard
                          key={dataSource.id}
                          dataSource={dataSource}
                          onClick={() => handleDataSourceClick(dataSource)}
                          onPreview={handlePreview}
                          isSelected={selectedIds.has(dataSource.id)}
                          searchQuery={search}
                          onSelect={handleSelect}
                          selectionMode={selectionMode}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>

        {/* Preview Panel */}
        {showPreview && (
          <aside className="w-[350px] flex-shrink-0 border-l bg-white overflow-hidden">
            <DataSourcePreview
              dataSource={previewDataSource}
              onClose={() => setPreviewDataSource(null)}
              onOpenDetail={handleDataSourceClick}
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
      />
    </div>
  );
}