import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  Play,
  Plus,
  Filter,
  SortAsc,
  Grid,
  List,
  Edit2,
  Trash2,
  Copy,
  Lock,
  Globe,
  User
} from 'lucide-react';
import { queryTemplateService } from '../services/queryTemplateService';
import type { QueryTemplate } from '../types/queryTemplate';
import { TEMPLATE_CATEGORIES } from '../constants/templateCategories';
import toast from 'react-hot-toast';
import TemplateEditor from '../components/query-library/TemplateEditor';

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

type ViewMode = 'grid' | 'list';
type SortOption = 'newest' | 'oldest' | 'usage' | 'alphabetical';
type OwnershipFilter = 'all' | 'my-templates' | 'public';

export default function QueryLibrary() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [showFavorites, setShowFavorites] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [ownershipFilter, setOwnershipFilter] = useState<OwnershipFilter>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<QueryTemplate | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  // Fetch templates
  const { data: templatesResponse, isLoading } = useQuery({
    queryKey: ['query-templates'],
    queryFn: () => queryTemplateService.listTemplates(true),
  });

  const templates = templatesResponse?.data?.templates || [];

  // Fetch categories - commented out until backend implementation
  // const { data: categories = [] } = useQuery({
  //   queryKey: ['query-template-categories'],
  //   queryFn: () => queryTemplateService.getCategories(),
  // });

  // Delete template mutation
  const deleteTemplateMutation = useMutation({
    mutationFn: (templateId: string) => queryTemplateService.deleteTemplate(templateId),
    onSuccess: () => {
      toast.success('Template deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['query-templates'] });
      setShowDeleteConfirm(null);
    },
    onError: () => {
      toast.error('Failed to delete template');
    },
  });

  // Filter and sort templates
  const filteredAndSortedTemplates = useMemo(() => {
    let filtered = templates;

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((t: QueryTemplate) =>
        t.name.toLowerCase().includes(query) ||
        t.description?.toLowerCase().includes(query) ||
        t.tags?.some((tag: string) => tag.toLowerCase().includes(query))
      );
    }

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter((t: QueryTemplate) => t.category === selectedCategory);
    }

    // Filter by ownership
    if (ownershipFilter === 'my-templates') {
      filtered = filtered.filter((t: QueryTemplate) => t.isOwner);
    } else if (ownershipFilter === 'public') {
      filtered = filtered.filter((t: QueryTemplate) => t.isPublic && !t.isOwner);
    }

    // Filter by favorites (if implemented)
    if (showFavorites) {
      // TODO: Implement favorites filtering when backend support is added
      // filtered = filtered.filter(t => t.isFavorite);
    }

    // Sort templates
    const sorted = [...filtered];
    switch (sortBy) {
      case 'newest':
        sorted.sort((a, b) => new Date(b.createdAt || b.created_at || '').getTime() - new Date(a.createdAt || a.created_at || '').getTime());
        break;
      case 'oldest':
        sorted.sort((a, b) => new Date(a.createdAt || a.created_at || '').getTime() - new Date(b.createdAt || b.created_at || '').getTime());
        break;
      case 'usage':
        sorted.sort((a, b) => (b.usageCount || 0) - (a.usageCount || 0));
        break;
      case 'alphabetical':
        sorted.sort((a, b) => a.name.localeCompare(b.name));
        break;
    }

    return sorted;
  }, [templates, searchQuery, selectedCategory, ownershipFilter, showFavorites, sortBy]);

  // Group templates by category
  const templatesByCategory = useMemo(() => {
    const grouped: Record<string, QueryTemplate[]> = {};
    filteredAndSortedTemplates.forEach(template => {
      const category = template.category || 'custom-queries';
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(template);
    });
    return grouped;
  }, [filteredAndSortedTemplates]);

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
    // Track template usage
    const templateId = template.templateId || template.id;
    queryTemplateService.useTemplate(templateId);
    // Navigate to query builder with template using the proper route
    navigate(`/query-builder/template/${templateId}`);
  };

  const handleEditTemplate = (template: QueryTemplate) => {
    setSelectedTemplate(template);
    setShowCreateModal(true);
  };

  const handleDeleteTemplate = (templateId: string) => {
    setShowDeleteConfirm(templateId);
  };

  const confirmDelete = () => {
    if (showDeleteConfirm) {
      deleteTemplateMutation.mutate(showDeleteConfirm);
    }
  };

  const handleCreateNew = () => {
    setSelectedTemplate(null);
    setShowCreateModal(true);
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

          {/* Filters */}
          <div className="mb-4 space-y-2">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                <Filter className="inline-block h-3 w-3 mr-1" />
                Ownership
              </label>
              <select
                value={ownershipFilter}
                onChange={(e) => setOwnershipFilter(e.target.value as OwnershipFilter)}
                className="w-full text-sm border-gray-300 rounded-md"
                aria-label="ownership"
              >
                <option value="all">All Templates</option>
                <option value="my-templates">My Templates</option>
                <option value="public">Public Templates</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                <SortAsc className="inline-block h-3 w-3 mr-1" />
                Sort by
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                className="w-full text-sm border-gray-300 rounded-md"
                aria-label="sort"
              >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="usage">Most Used</option>
                <option value="alphabetical">Alphabetical</option>
              </select>
            </div>
          </div>

          <div className="border-t border-gray-200 my-4"></div>

          {/* Quick Filters */}
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
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Categories
            </h3>
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
                      {templatesByCategory[category.id].slice(0, 5).map(template => (
                        <button
                          key={template.templateId}
                          onClick={() => handleUseTemplate(template)}
                          className="w-full text-left px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded truncate"
                        >
                          {template.name}
                        </button>
                      ))}
                      {templateCount > 5 && (
                        <div className="px-3 py-1 text-xs text-gray-500">
                          +{templateCount - 5} more...
                        </div>
                      )}
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
              <div className="flex items-center space-x-2">
                {/* View Mode Toggle */}
                <div className="flex items-center bg-gray-100 rounded-md p-1">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-1 rounded ${
                      viewMode === 'grid' ? 'bg-white shadow' : ''
                    }`}
                    aria-label="Grid view"
                  >
                    <Grid className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-1 rounded ${
                      viewMode === 'list' ? 'bg-white shadow' : ''
                    }`}
                    aria-label="List view"
                  >
                    <List className="h-4 w-4" />
                  </button>
                </div>
                
                {/* Create Button */}
                <button
                  onClick={handleCreateNew}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Template
                </button>
              </div>
            </div>
          </div>

          {/* Stats Bar */}
          <div className="mb-4 flex items-center justify-between text-sm text-gray-600">
            <div>
              Showing {filteredAndSortedTemplates.length} of {templates.length} templates
            </div>
            <div className="flex items-center space-x-4">
              <span>
                <Globe className="inline-block h-4 w-4 mr-1" />
                {templates.filter((t: QueryTemplate) => t.isPublic).length} public
              </span>
              <span>
                <User className="inline-block h-4 w-4 mr-1" />
                {templates.filter((t: QueryTemplate) => t.isOwner).length} owned
              </span>
            </div>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">Loading templates...</div>
            </div>
          )}

          {/* Template Grid/List */}
          {!isLoading && viewMode === 'grid' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredAndSortedTemplates.map((template: QueryTemplate) => (
                <TemplateCard
                  key={template.templateId || template.id}
                  template={template}
                  onUse={() => handleUseTemplate(template)}
                  onEdit={() => handleEditTemplate(template)}
                  onDelete={() => handleDeleteTemplate(template.templateId || template.id)}
                  testId="template-card"
                />
              ))}
            </div>
          )}

          {!isLoading && viewMode === 'list' && (
            <div className="space-y-2">
              {filteredAndSortedTemplates.map(template => (
                <TemplateListItem
                  key={template.templateId}
                  template={template}
                  onUse={() => handleUseTemplate(template)}
                  onEdit={() => handleEditTemplate(template)}
                  onDelete={() => handleDeleteTemplate(template.templateId || template.id)}
                />
              ))}
            </div>
          )}

          {/* Empty State */}
          {!isLoading && filteredAndSortedTemplates.length === 0 && (
            <div className="text-center py-12">
              <BookOpen className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No templates found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchQuery
                  ? 'Try adjusting your search criteria'
                  : 'Get started by creating a new template'}
              </p>
              <div className="mt-6">
                <button
                  onClick={handleCreateNew}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create New Template
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Delete Template</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this template? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Template Editor Modal */}
      {showCreateModal && (
        <TemplateEditor
          template={selectedTemplate || undefined}
          onSave={async (template: any) => {
            // The template data is already in snake_case format from TemplateEditor
            try {

              if (selectedTemplate) {
                // Update existing template - just update the template data
                // Parameters are included in the template data itself (parameters_schema)
                await queryTemplateService.updateTemplate(
                  selectedTemplate.templateId || selectedTemplate.id,
                  template
                );
                toast.success('Template updated successfully');
              } else {
                // Create new template - parameters are included in the template data
                const result = await queryTemplateService.createTemplate(template);
                toast.success('Template created successfully');
              }
              queryClient.invalidateQueries({ queryKey: ['query-templates'] });
              setShowCreateModal(false);
              setSelectedTemplate(null);
            } catch (error) {
              console.error('Failed to save template:', error);
              toast.error('Failed to save template');
            }
          }}
          onCancel={() => {
            setShowCreateModal(false);
            setSelectedTemplate(null);
          }}
        />
      )}
    </div>
  );
}

// Template Card Component for Grid View
interface TemplateCardProps {
  template: QueryTemplate;
  onUse: () => void;
  onEdit: () => void;
  onDelete: () => void;
  testId?: string;
}

function TemplateCard({ template, onUse, onEdit, onDelete, testId }: TemplateCardProps) {
  const [isFavorite, setIsFavorite] = useState(false);

  const handleToggleFavorite = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsFavorite(!isFavorite);
    // TODO: Call API to update favorite status
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow" data-testid={testId}>
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

      {/* Tags */}
      {template.tags && template.tags.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1">
          {template.tags.slice(0, 3).map(tag => (
            <span key={tag} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
        <div className="flex items-center">
          <Clock className="h-3 w-3 mr-1" />
          <span>{template.usageCount || 0} uses</span>
        </div>
        <div className="flex items-center space-x-2">
          {template.isOwner && (
            <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
              Your Template
            </span>
          )}
          {template.isPublic ? (
            <span title="Public">
              <Globe className="h-3 w-3 text-green-600" />
            </span>
          ) : (
            <span title="Private">
              <Lock className="h-3 w-3 text-gray-400" />
            </span>
          )}
        </div>
      </div>

      {template.category && (
        <div className="mb-3">
          <span className="px-2 py-1 bg-gray-100 rounded text-xs">
            {TEMPLATE_CATEGORIES[template.category]?.name || template.category}
          </span>
        </div>
      )}

      <div className="flex items-center space-x-2">
        <button
          onClick={onUse}
          className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-blue-600 text-sm font-medium rounded-md text-blue-600 bg-white hover:bg-blue-50"
        >
          <Play className="h-4 w-4 mr-2" />
          Use Template
        </button>
        {template.isOwner && (
          <>
            <button
              onClick={onEdit}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
              aria-label="Edit template"
            >
              <Edit2 className="h-4 w-4" />
            </button>
            <button
              onClick={onDelete}
              className="p-2 text-red-600 hover:text-red-900 hover:bg-red-50 rounded"
              aria-label="Delete template"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </>
        )}
        {!template.isOwner && template.isPublic && (
          <button
            onClick={() => {/* TODO: Implement fork */}}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
            aria-label="Fork template"
          >
            <Copy className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}

// Template List Item Component for List View
interface TemplateListItemProps {
  template: QueryTemplate;
  onUse: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

function TemplateListItem({ template, onUse, onEdit, onDelete }: TemplateListItemProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center">
            <h3 className="text-sm font-semibold text-gray-900 mr-2">
              {template.name}
            </h3>
            {template.isOwner && (
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                Your Template
              </span>
            )}
            {template.isPublic ? (
              <span title="Public">
                <Globe className="h-3 w-3 text-green-600 ml-2" />
              </span>
            ) : (
              <span title="Private">
                <Lock className="h-3 w-3 text-gray-400 ml-2" />
              </span>
            )}
          </div>
          <p className="text-xs text-gray-600 mt-1">
            {template.description || 'No description available'}
          </p>
          <div className="flex items-center mt-2 space-x-4 text-xs text-gray-500">
            <span>{TEMPLATE_CATEGORIES[template.category]?.name || template.category}</span>
            <span>{template.usageCount || 0} uses</span>
            <span>Created {new Date(template.createdAt || template.created_at || '').toLocaleDateString()}</span>
          </div>
        </div>
        <div className="flex items-center space-x-2 ml-4">
          <button
            onClick={onUse}
            className="inline-flex items-center px-3 py-1.5 border border-blue-600 text-sm font-medium rounded-md text-blue-600 bg-white hover:bg-blue-50"
          >
            <Play className="h-3 w-3 mr-1" />
            Use
          </button>
          {template.isOwner && (
            <>
              <button
                onClick={onEdit}
                className="p-1.5 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
                aria-label="Edit template"
              >
                <Edit2 className="h-3 w-3" />
              </button>
              <button
                onClick={onDelete}
                className="p-1.5 text-red-600 hover:text-red-900 hover:bg-red-50 rounded"
                aria-label="Delete template"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}