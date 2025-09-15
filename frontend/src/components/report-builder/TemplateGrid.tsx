import { useState, useMemo } from 'react';
import { Search, Filter, ChevronRight, FileText, BarChart3, Users, TrendingUp, Package, DollarSign } from 'lucide-react';
import type { QueryTemplate } from '../../types/queryTemplate';

interface TemplateGridProps {
  templates: QueryTemplate[];
  onSelect: (template: QueryTemplate) => void;
}

const categoryIcons: Record<string, any> = {
  performance: BarChart3,
  conversion: TrendingUp,
  audience: Users,
  attribution: FileText,
  inventory: Package,
  financial: DollarSign,
};

const categoryColors: Record<string, string> = {
  performance: 'bg-blue-100 text-blue-800',
  conversion: 'bg-green-100 text-green-800',
  audience: 'bg-purple-100 text-purple-800',
  attribution: 'bg-orange-100 text-orange-800',
  inventory: 'bg-yellow-100 text-yellow-800',
  financial: 'bg-pink-100 text-pink-800',
};

export default function TemplateGrid({ templates, onSelect }: TemplateGridProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedInstanceType, setSelectedInstanceType] = useState<string>('');
  const [selectedReportType, setSelectedReportType] = useState<string>('');

  // Extract unique values for filters
  const categories = useMemo(() => {
    const cats = new Set(templates.map(t => t.category).filter(Boolean));
    return Array.from(cats).sort();
  }, [templates]);

  const instanceTypes = useMemo(() => {
    const types = new Set(templates.flatMap(t => t.instance_types || []));
    return Array.from(types).sort();
  }, [templates]);

  const reportTypes = useMemo(() => {
    const types = new Set(templates.map(t => t.report_type).filter(Boolean));
    return Array.from(types).sort();
  }, [templates]);

  // Filter templates
  const filteredTemplates = useMemo(() => {
    return templates.filter(template => {
      // Search filter
      if (searchTerm) {
        const search = searchTerm.toLowerCase();
        const matchesSearch =
          template.name.toLowerCase().includes(search) ||
          template.description?.toLowerCase().includes(search) ||
          template.category?.toLowerCase().includes(search);

        if (!matchesSearch) return false;
      }

      // Category filter
      if (selectedCategory && template.category !== selectedCategory) {
        return false;
      }

      // Instance type filter
      if (selectedInstanceType && !template.instance_types?.includes(selectedInstanceType)) {
        return false;
      }

      // Report type filter
      if (selectedReportType && template.report_type !== selectedReportType) {
        return false;
      }

      return true;
    });
  }, [templates, searchTerm, selectedCategory, selectedInstanceType, selectedReportType]);

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedCategory('');
    setSelectedInstanceType('');
    setSelectedReportType('');
  };

  const hasActiveFilters = searchTerm || selectedCategory || selectedInstanceType || selectedReportType;

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 gap-4
                        md:grid-cols-2
                        lg:grid-cols-5">
          {/* Search */}
          <div className="lg:col-span-2">
            <label htmlFor="search" className="sr-only">Search templates</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                id="search"
                placeholder="Search templates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Category Filter */}
          <div>
            <label htmlFor="category" className="sr-only">Category</label>
            <select
              id="category"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                       focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Instance Type Filter */}
          <div>
            <label htmlFor="instanceType" className="sr-only">Instance Type</label>
            <select
              id="instanceType"
              value={selectedInstanceType}
              onChange={(e) => setSelectedInstanceType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                       focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Instances</option>
              {instanceTypes.map(type => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Report Type Filter */}
          <div>
            <label htmlFor="reportType" className="sr-only">Report Type</label>
            <select
              id="reportType"
              value={selectedReportType}
              onChange={(e) => setSelectedReportType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                       focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Types</option>
              {reportTypes.map(type => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Active filters indicator */}
        {hasActiveFilters && (
          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm text-gray-500">
              {filteredTemplates.length} of {templates.length} templates
            </span>
            <button
              onClick={clearFilters}
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>

      {/* Template Grid */}
      {filteredTemplates.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Filter className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No templates found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search or filters
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4
                        sm:grid-cols-2
                        lg:grid-cols-3
                        xl:grid-cols-4">
          {filteredTemplates.map((template) => {
            const Icon = categoryIcons[template.category] || FileText;
            const colorClass = categoryColors[template.category] || 'bg-gray-100 text-gray-800';

            return (
              <div
                key={template.id}
                role="button"
                tabIndex={0}
                onClick={() => onSelect(template)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelect(template);
                  }
                }}
                className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer p-4 border border-gray-200
                         hover:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-shrink-0">
                    <Icon className="h-8 w-8 text-indigo-600" />
                  </div>
                  <ChevronRight className="h-4 w-4 text-gray-400" />
                </div>

                <h3 className="text-sm font-semibold text-gray-900 mb-1 line-clamp-2">
                  {template.name}
                </h3>

                <p className="text-xs text-gray-500 mb-3 line-clamp-2">
                  {template.description || 'No description available'}
                </p>

                <div className="flex flex-wrap gap-1">
                  {/* Category Badge */}
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
                    {template.category}
                  </span>

                  {/* Report Type Badge */}
                  {template.report_type && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                      {template.report_type}
                    </span>
                  )}

                  {/* Instance Types */}
                  {template.instance_types?.slice(0, 1).map(type => (
                    <span
                      key={type}
                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800"
                    >
                      {type}
                    </span>
                  ))}
                  {template.instance_types && template.instance_types.length > 1 && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                      +{template.instance_types.length - 1}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}