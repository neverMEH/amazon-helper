import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, FileText, Globe, Lock } from 'lucide-react';
import { queryTemplateService } from '../../services/queryTemplateService';
import type { QueryTemplate } from '../../types/queryTemplate';

interface QueryTemplateSelectorProps {
  onSelectTemplate: (template: QueryTemplate) => void;
}

export default function QueryTemplateSelector({ onSelectTemplate }: QueryTemplateSelectorProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');

  const { data: templatesResponse, isLoading } = useQuery({
    queryKey: ['query-templates', selectedCategory],
    queryFn: () => queryTemplateService.listTemplates(true, selectedCategory ? { category: selectedCategory } : undefined),
  });

  const templates = templatesResponse?.data?.templates || [];

  const { data: categories = [] } = useQuery({
    queryKey: ['query-template-categories'],
    queryFn: () => queryTemplateService.getCategories(),
  });

  const filteredTemplates = templates.filter((template: QueryTemplate) =>
    template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    template.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (template.tags || []).some((tag: string) => tag.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (isLoading) {
    return (
      <div className="border border-gray-300 rounded-md p-4">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading templates...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="border border-gray-300 rounded-md p-4 space-y-4">
      <div className="flex space-x-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search templates..."
              className="pl-10 pr-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        {categories.length > 0 && (
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="max-h-96 overflow-y-auto space-y-2">
        {filteredTemplates.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="mx-auto h-12 w-12 mb-2 text-gray-400" />
            <p>No templates found</p>
          </div>
        ) : (
          filteredTemplates.map((template: QueryTemplate) => (
            <div
              key={template.templateId || template.id}
              onClick={() => onSelectTemplate(template)}
              className="p-4 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-medium text-gray-900">{template.name}</h4>
                    {template.isPublic ? (
                      <span title="Public template">
                        <Globe className="h-4 w-4 text-green-600" />
                      </span>
                    ) : (
                      <span title="Private template">
                        <Lock className="h-4 w-4 text-gray-600" />
                      </span>
                    )}
                  </div>
                  {template.description && (
                    <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                  )}
                  <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                    <span>{template.category}</span>
                    <span>Used {template.usageCount || 0} times</span>
                    {template.tags && template.tags.length > 0 && (
                      <div className="flex gap-1">
                        {template.tags.map((tag: string) => (
                          <span
                            key={tag}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}