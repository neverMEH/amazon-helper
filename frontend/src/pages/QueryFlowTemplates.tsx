import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, Star, TrendingUp, Clock, Users, Grid, List, ChevronDown } from 'lucide-react';
import { queryFlowTemplateService } from '../services/queryFlowTemplateService';
import type { QueryFlowTemplate } from '../types/queryFlowTemplate';
import TemplateCard from '../components/query-flow-templates/TemplateCard';
import TemplateDetailModal from '../components/query-flow-templates/TemplateDetailModal';

interface FilterState {
  search: string;
  category: string;
  tags: string[];
  sortBy: 'name' | 'execution_count' | 'created_at' | 'avg_rating';
  sortOrder: 'asc' | 'desc';
}

const QueryFlowTemplates: React.FC = () => {
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    category: '',
    tags: [],
    sortBy: 'execution_count',
    sortOrder: 'desc'
  });
  
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedTemplate, setSelectedTemplate] = useState<QueryFlowTemplate | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  
  const limit = 12;

  // Fetch templates
  const { data: templatesData, isLoading, error, refetch } = useQuery({
    queryKey: ['queryFlowTemplates', filters, currentPage],
    queryFn: () => queryFlowTemplateService.listTemplates({
      category: filters.category || undefined,
      search: filters.search || undefined,
      tags: filters.tags.length > 0 ? filters.tags : undefined,
      limit,
      offset: currentPage * limit,
      include_stats: true
    }),
    staleTime: 5 * 60 * 1000
  });

  // Fetch categories for filter dropdown
  const { data: categories } = useQuery({
    queryKey: ['templateCategories'],
    queryFn: queryFlowTemplateService.getCategories,
    staleTime: 10 * 60 * 1000
  });

  // Fetch popular tags
  const { data: popularTags } = useQuery({
    queryKey: ['templateTags'],
    queryFn: () => queryFlowTemplateService.getPopularTags(20),
    staleTime: 10 * 60 * 1000
  });

  // Sort templates client-side
  const sortedTemplates = templatesData?.templates?.sort((a, b) => {
    let aValue: any;
    let bValue: any;
    
    // Handle special cases
    if (filters.sortBy === 'avg_rating') {
      aValue = a.rating_info?.avg_rating || 0;
      bValue = b.rating_info?.avg_rating || 0;
    } else {
      aValue = a[filters.sortBy];
      bValue = b[filters.sortBy];
    }
    
    // Handle string comparison
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      const comparison = aValue.localeCompare(bValue);
      return filters.sortOrder === 'asc' ? comparison : -comparison;
    }
    
    // Handle numeric comparison
    const comparison = (aValue || 0) - (bValue || 0);
    return filters.sortOrder === 'asc' ? comparison : -comparison;
  }) || [];

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters(prev => ({ ...prev, search: e.target.value }));
    setCurrentPage(0);
  };

  const handleCategoryChange = (category: string) => {
    setFilters(prev => ({ ...prev, category }));
    setCurrentPage(0);
  };

  const handleTagToggle = (tag: string) => {
    setFilters(prev => ({
      ...prev,
      tags: prev.tags.includes(tag)
        ? prev.tags.filter(t => t !== tag)
        : [...prev.tags, tag]
    }));
    setCurrentPage(0);
  };

  const handleSortChange = (sortBy: FilterState['sortBy']) => {
    setFilters(prev => ({
      ...prev,
      sortBy,
      sortOrder: prev.sortBy === sortBy && prev.sortOrder === 'desc' ? 'asc' : 'desc'
    }));
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      category: '',
      tags: [],
      sortBy: 'execution_count',
      sortOrder: 'desc'
    });
    setCurrentPage(0);
  };

  const hasActiveFilters = filters.search || filters.category || filters.tags.length > 0;

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-96 text-center">
        <div className="text-red-600 mb-4">
          Failed to load query flow templates
        </div>
        <button 
          onClick={() => refetch()}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Query Flow Templates</h1>
            <p className="text-gray-600 mt-1">
              Pre-built query templates with dynamic parameters and visualizations
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-md ${viewMode === 'grid' ? 'bg-indigo-100 text-indigo-600' : 'text-gray-400 hover:text-gray-600'}`}
            >
              <Grid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-md ${viewMode === 'list' ? 'bg-indigo-100 text-indigo-600' : 'text-gray-400 hover:text-gray-600'}`}
            >
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Search and Filters Bar */}
        <div className="flex flex-col lg:flex-row lg:items-center space-y-4 lg:space-y-0 lg:space-x-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={filters.search}
              onChange={handleSearchChange}
              placeholder="Search templates..."
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Category Filter */}
          <select
            value={filters.category}
            onChange={(e) => handleCategoryChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">All Categories</option>
            {categories?.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>

          {/* Sort */}
          <div className="relative">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <Filter className="h-4 w-4" />
              <span>More Filters</span>
              <ChevronDown className="h-4 w-4" />
            </button>
          </div>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800"
            >
              Clear all
            </button>
          )}
        </div>

        {/* Advanced Filters */}
        {showFilters && (
          <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-md">
            <div className="flex flex-wrap items-center gap-4">
              {/* Sort Options */}
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-700">Sort by:</span>
                <div className="flex space-x-1">
                  {[
                    { key: 'execution_count' as const, label: 'Popular', icon: TrendingUp },
                    { key: 'created_at' as const, label: 'Newest', icon: Clock },
                    { key: 'avg_rating' as const, label: 'Rated', icon: Star },
                    { key: 'name' as const, label: 'Name', icon: Users }
                  ].map(({ key, label, icon: Icon }) => (
                    <button
                      key={key}
                      onClick={() => handleSortChange(key)}
                      className={`flex items-center space-x-1 px-2 py-1 rounded text-sm ${
                        filters.sortBy === key 
                          ? 'bg-indigo-100 text-indigo-700' 
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="h-3 w-3" />
                      <span>{label}</span>
                      {filters.sortBy === key && (
                        <span className="text-xs">
                          {filters.sortOrder === 'desc' ? '↓' : '↑'}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Popular Tags */}
              {popularTags && popularTags.length > 0 && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-700">Tags:</span>
                  <div className="flex flex-wrap gap-1">
                    {popularTags.slice(0, 8).map(({ tag, count }) => (
                      <button
                        key={tag}
                        onClick={() => handleTagToggle(tag)}
                        className={`px-2 py-1 rounded-full text-xs ${
                          filters.tags.includes(tag)
                            ? 'bg-indigo-100 text-indigo-700'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        {tag} ({count})
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Active Filters Summary */}
        {hasActiveFilters && (
          <div className="mt-3 flex items-center space-x-2 text-sm text-gray-600">
            <span>Active filters:</span>
            {filters.search && (
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                Search: "{filters.search}"
              </span>
            )}
            {filters.category && (
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded">
                Category: {filters.category}
              </span>
            )}
            {filters.tags.map(tag => (
              <span key={tag} className="px-2 py-1 bg-purple-100 text-purple-700 rounded">
                Tag: {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="border border-gray-200 rounded-lg p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-full mb-4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : sortedTemplates.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 mb-4">
            {hasActiveFilters ? 'No templates match your filters' : 'No templates available'}
          </div>
          {hasActiveFilters && (
            <button 
              onClick={clearFilters}
              className="text-indigo-600 hover:text-indigo-700"
            >
              Clear filters to see all templates
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Template Grid/List */}
          <div className={
            viewMode === 'grid' 
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' 
              : 'space-y-4'
          }>
            {sortedTemplates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                viewMode={viewMode}
                onClick={() => setSelectedTemplate(template)}
              />
            ))}
          </div>

          {/* Pagination */}
          {templatesData && templatesData.has_more && (
            <div className="mt-8 flex justify-center">
              <button
                onClick={() => setCurrentPage(prev => prev + 1)}
                className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                Load More Templates
              </button>
            </div>
          )}
        </>
      )}

      {/* Template Detail Modal */}
      {selectedTemplate && (
        <TemplateDetailModal
          template={selectedTemplate}
          isOpen={!!selectedTemplate}
          onClose={() => setSelectedTemplate(null)}
        />
      )}
    </div>
  );
};

export default QueryFlowTemplates;