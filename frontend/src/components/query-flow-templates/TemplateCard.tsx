import React from 'react';
import { Star, Play, Clock, TrendingUp, Users, Heart, BarChart3 } from 'lucide-react';
import type { QueryFlowTemplate } from '../../types/queryFlowTemplate';

interface TemplateCardProps {
  template: QueryFlowTemplate;
  viewMode?: 'grid' | 'list';
  onClick: () => void;
}

const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  viewMode = 'grid',
  onClick
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
  };

  const getDifficultyColor = (category: string) => {
    const colors = {
      'Performance Analysis': 'bg-blue-100 text-blue-800',
      'Attribution': 'bg-green-100 text-green-800',
      'Audience Analysis': 'bg-purple-100 text-purple-800',
      'Campaign Optimization': 'bg-orange-100 text-orange-800',
      'Creative Analysis': 'bg-pink-100 text-pink-800'
    };
    return colors[category as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  if (viewMode === 'list') {
    return (
      <div 
        onClick={onClick}
        className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h3 className="text-lg font-semibold text-gray-900 hover:text-indigo-600">
                {template.name}
              </h3>
              
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(template.category)}`}>
                {template.category}
              </span>
              
              {template.is_favorite && (
                <Heart className="h-4 w-4 text-red-500 fill-current" />
              )}
            </div>
            
            <p className="text-gray-600 mb-3 line-clamp-2">
              {template.description}
            </p>
            
            <div className="flex items-center space-x-6 text-sm text-gray-500">
              <div className="flex items-center space-x-1">
                <TrendingUp className="h-4 w-4" />
                <span>{formatNumber(template.execution_count)} runs</span>
              </div>
              
              {template.rating_info && template.rating_info.rating_count > 0 && (
                <div className="flex items-center space-x-1">
                  <Star className="h-4 w-4 text-yellow-400 fill-current" />
                  <span>{template.rating_info.avg_rating.toFixed(1)} ({template.rating_info.rating_count})</span>
                </div>
              )}
              
              <div className="flex items-center space-x-1">
                <BarChart3 className="h-4 w-4" />
                <span>{template.chart_configs?.length || 0} charts</span>
              </div>
              
              <div className="flex items-center space-x-1">
                <Clock className="h-4 w-4" />
                <span>{formatDate(template.updated_at)}</span>
              </div>
              
              {template.avg_execution_time_ms && (
                <div className="flex items-center space-x-1">
                  <span>~{Math.round(template.avg_execution_time_ms / 1000)}s avg</span>
                </div>
              )}
            </div>
          </div>
          
          <div className="ml-6 flex-shrink-0">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onClick();
              }}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors flex items-center space-x-2"
            >
              <Play className="h-4 w-4" />
              <span>Use Template</span>
            </button>
          </div>
        </div>
        
        {/* Tags */}
        {template.tags && template.tags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {template.tags.slice(0, 5).map((tag) => (
              <span
                key={tag}
                className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
              >
                {tag}
              </span>
            ))}
            {template.tags.length > 5 && (
              <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded text-xs">
                +{template.tags.length - 5} more
              </span>
            )}
          </div>
        )}
      </div>
    );
  }

  // Grid view
  return (
    <div 
      onClick={onClick}
      className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <h3 className="text-lg font-semibold text-gray-900 hover:text-indigo-600 line-clamp-1">
              {template.name}
            </h3>
            {template.is_favorite && (
              <Heart className="h-4 w-4 text-red-500 fill-current flex-shrink-0" />
            )}
          </div>
          
          <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(template.category)}`}>
            {template.category}
          </span>
        </div>
      </div>
      
      {/* Description */}
      <p className="text-gray-600 text-sm mb-4 line-clamp-3">
        {template.description}
      </p>
      
      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div className="flex items-center space-x-1 text-gray-500">
          <TrendingUp className="h-4 w-4" />
          <span>{formatNumber(template.execution_count)} runs</span>
        </div>
        
        <div className="flex items-center space-x-1 text-gray-500">
          <BarChart3 className="h-4 w-4" />
          <span>{template.chart_configs?.length || 0} charts</span>
        </div>
        
        {template.rating_info && template.rating_info.rating_count > 0 ? (
          <div className="flex items-center space-x-1 text-gray-500">
            <Star className="h-4 w-4 text-yellow-400 fill-current" />
            <span>{template.rating_info.avg_rating.toFixed(1)}</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1 text-gray-400">
            <Star className="h-4 w-4" />
            <span>No ratings</span>
          </div>
        )}
        
        <div className="flex items-center space-x-1 text-gray-500">
          <Users className="h-4 w-4" />
          <span>{template.parameters?.length || 0} params</span>
        </div>
      </div>
      
      {/* Tags */}
      {template.tags && template.tags.length > 0 && (
        <div className="mb-4">
          <div className="flex flex-wrap gap-1">
            {template.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
              >
                {tag}
              </span>
            ))}
            {template.tags.length > 3 && (
              <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded text-xs">
                +{template.tags.length - 3}
              </span>
            )}
          </div>
        </div>
      )}
      
      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <div className="text-xs text-gray-500">
          Updated {formatDate(template.updated_at)}
        </div>
        
        <button
          onClick={(e) => {
            e.stopPropagation();
            onClick();
          }}
          className="px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors flex items-center space-x-2 text-sm"
        >
          <Play className="h-3 w-3" />
          <span>Use</span>
        </button>
      </div>
    </div>
  );
};

export default TemplateCard;