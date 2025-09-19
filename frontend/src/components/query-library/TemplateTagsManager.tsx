import { useState, useEffect } from 'react';
import { X, Plus, Tag, Hash, Folder, TrendingUp, Filter } from 'lucide-react';
import type { QueryTemplate } from '../../types/queryTemplate';

interface TemplateTagsManagerProps {
  template: QueryTemplate;
  onUpdate: (tags: string[], category: string) => void;
  readOnly?: boolean;
}

// Predefined categories with descriptions
const TEMPLATE_CATEGORIES = [
  { id: 'performance', label: 'Performance Analysis', icon: TrendingUp, color: 'blue' },
  { id: 'attribution', label: 'Attribution', icon: Hash, color: 'green' },
  { id: 'audience', label: 'Audience Building', icon: Filter, color: 'purple' },
  { id: 'incrementality', label: 'Incrementality', icon: TrendingUp, color: 'yellow' },
  { id: 'cross-channel', label: 'Cross-Channel', icon: Folder, color: 'indigo' },
  { id: 'optimization', label: 'Optimization', icon: TrendingUp, color: 'red' },
  { id: 'custom', label: 'Custom', icon: Tag, color: 'gray' },
];

// Suggested tags based on category
const SUGGESTED_TAGS: Record<string, string[]> = {
  performance: ['campaign-metrics', 'roas', 'acos', 'conversion-rate', 'ctr', 'impressions', 'clicks'],
  attribution: ['multi-touch', 'last-touch', 'first-touch', 'path-analysis', 'touchpoints'],
  audience: ['segmentation', 'targeting', 'lookalike', 'custom-audience', 'retargeting'],
  incrementality: ['lift-measurement', 'control-group', 'test-vs-control', 'causal-impact'],
  'cross-channel': ['dsp', 'sponsored-ads', 'display', 'video', 'omnichannel'],
  optimization: ['bid-optimization', 'budget-allocation', 'keyword-analysis', 'negative-keywords'],
  custom: [],
};

export default function TemplateTagsManager({
  template,
  onUpdate,
  readOnly = false
}: TemplateTagsManagerProps) {
  const [selectedCategory, setSelectedCategory] = useState(template.category || 'custom');
  const [tags, setTags] = useState<string[]>(template.tags || []);
  const [newTag, setNewTag] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);

  useEffect(() => {
    setSelectedCategory(template.category || 'custom');
    setTags(template.tags || []);
  }, [template]);

  const handleAddTag = (tag: string) => {
    const normalizedTag = tag.toLowerCase().replace(/\s+/g, '-');
    if (normalizedTag && !tags.includes(normalizedTag)) {
      const newTags = [...tags, normalizedTag];
      setTags(newTags);
      if (!readOnly) {
        onUpdate(newTags, selectedCategory);
      }
    }
    setNewTag('');
  };

  const handleRemoveTag = (tag: string) => {
    const newTags = tags.filter(t => t !== tag);
    setTags(newTags);
    if (!readOnly) {
      onUpdate(newTags, selectedCategory);
    }
  };

  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    if (!readOnly) {
      onUpdate(tags, category);
    }
    setShowSuggestions(true);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && newTag.trim()) {
      e.preventDefault();
      handleAddTag(newTag);
    }
  };

  const categoryConfig = TEMPLATE_CATEGORIES.find(c => c.id === selectedCategory);
  const CategoryIcon = categoryConfig?.icon || Tag;
  const categoryColor = categoryConfig?.color || 'gray';

  const suggestedTags = SUGGESTED_TAGS[selectedCategory] || [];
  const availableSuggestions = suggestedTags.filter(t => !tags.includes(t));

  return (
    <div className="space-y-4">
      {/* Category Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Category
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {TEMPLATE_CATEGORIES.map((category) => {
            const Icon = category.icon;
            const isSelected = selectedCategory === category.id;
            return (
              <button
                key={category.id}
                onClick={() => handleCategoryChange(category.id)}
                disabled={readOnly}
                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all
                          ${isSelected
                            ? `bg-${category.color}-100 text-${category.color}-800 border-2 border-${category.color}-300`
                            : 'bg-gray-50 text-gray-700 border-2 border-gray-200 hover:bg-gray-100'
                          } ${readOnly ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
              >
                <Icon className="h-4 w-4" />
                <span className="truncate">{category.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Current Category Display */}
      <div className={`bg-${categoryColor}-50 border border-${categoryColor}-200 rounded-lg p-3`}>
        <div className="flex items-center gap-2">
          <CategoryIcon className={`h-5 w-5 text-${categoryColor}-600`} />
          <div>
            <p className={`text-sm font-medium text-${categoryColor}-900`}>
              {categoryConfig?.label}
            </p>
            <p className={`text-xs text-${categoryColor}-700`}>
              {tags.length} tags applied
            </p>
          </div>
        </div>
      </div>

      {/* Tags Management */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tags
        </label>

        {/* Current Tags */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm
                         bg-indigo-100 text-indigo-800"
              >
                <Tag className="h-3 w-3" />
                {tag}
                {!readOnly && (
                  <button
                    onClick={() => handleRemoveTag(tag)}
                    className="ml-1 hover:text-indigo-900"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </span>
            ))}
          </div>
        )}

        {/* Add New Tag */}
        {!readOnly && (
          <div className="flex gap-2">
            <input
              type="text"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Add a tag..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm
                       focus:ring-indigo-500 focus:border-indigo-500"
            />
            <button
              onClick={() => handleAddTag(newTag)}
              disabled={!newTag.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md
                       hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                       disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Suggested Tags */}
        {!readOnly && showSuggestions && availableSuggestions.length > 0 && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg">
            <p className="text-xs font-medium text-gray-700 mb-2">Suggested tags for {categoryConfig?.label}:</p>
            <div className="flex flex-wrap gap-2">
              {availableSuggestions.map((suggestedTag) => (
                <button
                  key={suggestedTag}
                  onClick={() => handleAddTag(suggestedTag)}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs
                           bg-white border border-gray-300 text-gray-700 hover:bg-gray-100"
                >
                  <Plus className="h-3 w-3" />
                  {suggestedTag}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Tag Statistics */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900">{tags.length}</p>
          <p className="text-xs text-gray-500">Total Tags</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-indigo-600">
            {SUGGESTED_TAGS[selectedCategory]?.length || 0}
          </p>
          <p className="text-xs text-gray-500">Suggested</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-green-600">
            {tags.filter(t => SUGGESTED_TAGS[selectedCategory]?.includes(t)).length}
          </p>
          <p className="text-xs text-gray-500">Matched</p>
        </div>
      </div>
    </div>
  );
}