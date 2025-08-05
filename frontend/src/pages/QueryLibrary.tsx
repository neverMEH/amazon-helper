import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  Search, 
  Star, 
  Clock, 
  ChevronRight, 
  ChevronDown,
  BookOpen,
  TrendingUp,
  Users,
  Package,
  ShoppingCart,
  Target,
  BarChart,
  Code,
  Play
} from 'lucide-react';
import { queryTemplateService } from '../services/queryTemplateService';
import type { QueryTemplate } from '../types/queryTemplate';
import { TEMPLATE_CATEGORIES } from '../constants/templateCategories';

// Icon mapping for categories
const iconMap: Record<string, any> = {
  TrendingUp,
  Users,
  Package,
  ShoppingCart,
  Target,
  BarChart,
  Code
};

export default function QueryLibrary() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [showFavorites, setShowFavorites] = useState(false);

  // Fetch templates
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['query-templates'],
    queryFn: () => queryTemplateService.listTemplates(true),
  });

  // Filter templates based on search and category
  const filteredTemplates = useMemo(() => {
    let filtered = templates;

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(t => 
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.description?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter(t => t.category === selectedCategory);
    }

    // Filter by favorites
    if (showFavorites) {
      filtered = filtered.filter(t => t.isFavorite);
    }

    return filtered;
  }, [templates, searchQuery, selectedCategory, showFavorites]);

  // Group templates by category
  const templatesByCategory = useMemo(() => {
    const grouped: Record<string, QueryTemplate[]> = {};
    filteredTemplates.forEach(template => {
      const category = template.category || 'custom-queries';
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(template);
    });
    return grouped;
  }, [filteredTemplates]);

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId);
      } else {
        newSet.add(categoryId);
      }
      return newSet;
    });
  };

  const handleUseTemplate = (template: QueryTemplate) => {
    // Navigate to query builder with template
    navigate(`/query-builder/template/${template.templateId}`);
  };

  const handleCreateNew = () => {
    navigate('/query-builder/new');
  };

  return (
    <div className="flex h-full">
      {/* Left Sidebar */}
      <div className="w-72 bg-gray-50 border-r border-gray-200 overflow-y-auto">
        <div className="p-4">
          {/* Search Bar */}
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search templates..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Filter Tabs */}
          <div className="mb-4 space-y-2">
            <button
              onClick={() => {
                setShowFavorites(false);
                setSelectedCategory(null);
              }}
              className={`w-full text-left px-3 py-2 rounded-md ${
                !showFavorites && !selectedCategory
                  ? 'bg-blue-100 text-blue-700'
                  : 'hover:bg-gray-100'
              }`}
            >
              <BookOpen className="inline-block h-4 w-4 mr-2" />
              All Queries ({templates.length})
            </button>
            <button
              onClick={() => {
                setShowFavorites(true);
                setSelectedCategory(null);
              }}
              className={`w-full text-left px-3 py-2 rounded-md ${
                showFavorites
                  ? 'bg-blue-100 text-blue-700'
                  : 'hover:bg-gray-100'
              }`}
            >
              <Star className="inline-block h-4 w-4 mr-2" />
              My Favorites
            </button>
          </div>

          <div className="border-t border-gray-200 my-4"></div>

          {/* Categories */}
          <div className="space-y-1">
            {Object.values(TEMPLATE_CATEGORIES).map(category => {
              const isExpanded = expandedCategories.has(category.id);
              const isSelected = selectedCategory === category.id;
              const templateCount = templatesByCategory[category.id]?.length || 0;
              const Icon = iconMap[category.icon || 'BookOpen'] || BookOpen;

              return (
                <div key={category.id}>
                  <button
                    onClick={() => {
                      toggleCategory(category.id);
                      setSelectedCategory(isSelected ? null : category.id);
                      setShowFavorites(false);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-md flex items-center justify-between ${
                      isSelected
                        ? 'bg-blue-100 text-blue-700'
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex items-center">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 mr-2" />
                      ) : (
                        <ChevronRight className="h-4 w-4 mr-2" />
                      )}
                      <Icon className="h-4 w-4 mr-2" />
                      <span className="text-sm font-medium">{category.name}</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {templateCount}
                    </span>
                  </button>
                  
                  {/* Expanded template list */}
                  {isExpanded && templatesByCategory[category.id] && (
                    <div className="ml-8 mt-1 space-y-1">
                      {templatesByCategory[category.id].map(template => (
                        <button
                          key={template.templateId}
                          onClick={() => handleUseTemplate(template)}
                          className="w-full text-left px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
                        >
                          {template.name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Query Library</h1>
                <p className="mt-1 text-sm text-gray-600">
                  Browse and use pre-built query templates or create your own
                </p>
              </div>
              <button
                onClick={handleCreateNew}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
              >
                <Code className="h-4 w-4 mr-2" />
                New Query
              </button>
            </div>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">Loading templates...</div>
            </div>
          )}

          {/* Template Grid */}
          {!isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredTemplates.map(template => (
                <TemplateCard
                  key={template.templateId}
                  template={template}
                  onUse={() => handleUseTemplate(template)}
                />
              ))}
            </div>
          )}

          {/* Empty State */}
          {!isLoading && filteredTemplates.length === 0 && (
            <div className="text-center py-12">
              <BookOpen className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No templates found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchQuery
                  ? 'Try adjusting your search criteria'
                  : 'Get started by creating a new query'}
              </p>
              <div className="mt-6">
                <button
                  onClick={handleCreateNew}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                >
                  <Code className="h-4 w-4 mr-2" />
                  Create New Query
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Template Card Component
interface TemplateCardProps {
  template: QueryTemplate;
  onUse: () => void;
}

function TemplateCard({ template, onUse }: TemplateCardProps) {
  const [isFavorite, setIsFavorite] = useState(template.isFavorite || false);

  const handleToggleFavorite = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsFavorite(!isFavorite);
    // TODO: Call API to update favorite status
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-900 line-clamp-2">
          {template.name}
        </h3>
        <button
          onClick={handleToggleFavorite}
          className="ml-2 text-gray-400 hover:text-yellow-500"
        >
          <Star
            className={`h-4 w-4 ${
              isFavorite ? 'fill-yellow-500 text-yellow-500' : ''
            }`}
          />
        </button>
      </div>

      <p className="text-xs text-gray-600 mb-3 line-clamp-2">
        {template.description || 'No description available'}
      </p>

      <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
        <div className="flex items-center">
          <Clock className="h-3 w-3 mr-1" />
          <span>Run Times: {template.usageCount || 0}</span>
        </div>
        {template.category && (
          <span className="px-2 py-1 bg-gray-100 rounded text-xs">
            {TEMPLATE_CATEGORIES[template.category]?.name || template.category}
          </span>
        )}
      </div>

      <button
        onClick={onUse}
        className="w-full inline-flex items-center justify-center px-3 py-2 border border-blue-600 text-sm font-medium rounded-md text-blue-600 bg-white hover:bg-blue-50"
      >
        <Play className="h-4 w-4 mr-2" />
        Use Template
      </button>
    </div>
  );
}