/**
 * Data Sources List Page
 * Browse and search AMC schema documentation
 */

import { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Filter,
  Database,
  ChevronRight,
  Tag,
  Lock,
  Globe,
  X
} from 'lucide-react';
import { dataSourceService } from '../services/dataSourceService';
import type { DataSource } from '../types/dataSource';

export default function DataSources() {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // State from URL params
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || '');
  const [selectedTags, setSelectedTags] = useState<string[]>(
    searchParams.getAll('tag') || []
  );
  const [showFilters, setShowFilters] = useState(false);

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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
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
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="lg:hidden p-2 text-gray-500 hover:text-gray-700"
              >
                <Filter className="h-5 w-5" />
              </button>
            </div>

            {/* Search Bar */}
            <div className="mt-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search schemas, fields, or descriptions..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Sidebar Filters - Desktop */}
          <aside className={`${showFilters ? 'block' : 'hidden'} lg:block lg:w-64 flex-shrink-0`}>
            <div className="bg-white rounded-lg shadow p-6 sticky top-4">
              <h3 className="text-lg font-semibold mb-4">Filters</h3>

              {/* Categories */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Category</h4>
                <div className="space-y-1">
                  <button
                    onClick={() => setSelectedCategory('')}
                    className={`w-full text-left px-3 py-2 rounded-md text-sm ${
                      !selectedCategory
                        ? 'bg-blue-50 text-blue-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    All Categories
                  </button>
                  {categories.map(category => (
                    <button
                      key={category}
                      onClick={() => setSelectedCategory(category)}
                      className={`w-full text-left px-3 py-2 rounded-md text-sm ${
                        selectedCategory === category
                          ? 'bg-blue-50 text-blue-700 font-medium'
                          : 'text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      {category}
                    </button>
                  ))}
                </div>
              </div>

              {/* Popular Tags */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Popular Tags</h4>
                <div className="flex flex-wrap gap-2">
                  {popularTags.slice(0, 15).map(({ tag, count }) => (
                    <button
                      key={tag}
                      onClick={() => handleTagToggle(tag)}
                      className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs ${
                        selectedTags.includes(tag)
                          ? 'bg-green-100 text-green-700 font-medium'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      <Tag className="h-3 w-3" />
                      {tag}
                      <span className="text-gray-500">({count})</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1">
            {isLoading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : dataSources.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No data sources found</h3>
                <p className="text-gray-500">
                  {hasActiveFilters
                    ? 'Try adjusting your filters or search query'
                    : 'No data sources are available yet'}
                </p>
              </div>
            ) : selectedCategory ? (
              // Show filtered results as cards
              <div className="grid gap-4 md:grid-cols-2">
                {dataSources.map(dataSource => (
                  <DataSourceCard key={dataSource.id} dataSource={dataSource} />
                ))}
              </div>
            ) : (
              // Show grouped by category
              <div className="space-y-8">
                {Object.entries(groupedDataSources).map(([category, sources]) => (
                  <div key={category}>
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">
                      {category}
                      <span className="ml-2 text-sm font-normal text-gray-500">
                        ({sources.length} {sources.length === 1 ? 'schema' : 'schemas'})
                      </span>
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2">
                      {sources.map(dataSource => (
                        <DataSourceCard key={dataSource.id} dataSource={dataSource} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

function DataSourceCard({ dataSource }: { dataSource: DataSource }) {
  const navigate = useNavigate();

  return (
    <div
      onClick={() => navigate(`/data-sources/${dataSource.schema_id}`)}
      className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer p-6"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            {dataSource.name}
            {dataSource.is_paid_feature && (
              <Lock className="h-4 w-4 text-yellow-600" />
            )}
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            {dataSource.data_sources.join(', ')}
          </p>
        </div>
        <ChevronRight className="h-5 w-5 text-gray-400 flex-shrink-0" />
      </div>

      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
        {dataSource.description}
      </p>

      <div className="flex items-center justify-between">
        <div className="flex flex-wrap gap-2">
          {dataSource.tags.slice(0, 3).map(tag => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs"
            >
              <Tag className="h-3 w-3" />
              {tag}
            </span>
          ))}
          {dataSource.tags.length > 3 && (
            <span className="text-xs text-gray-500">
              +{dataSource.tags.length - 3} more
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 text-xs text-gray-500">
          {dataSource.availability?.marketplaces && (
            <span className="flex items-center gap-1">
              <Globe className="h-3 w-3" />
              {Object.keys(dataSource.availability.marketplaces).length} regions
            </span>
          )}
          <span className="text-gray-300">v{dataSource.version}</span>
        </div>
      </div>
    </div>
  );
}