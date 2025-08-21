/**
 * Build Guides Page
 * Main listing page for all available build guides
 */

import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  BookOpen,
  Clock,
  Award,
  Filter,
  TrendingUp,
  Package,
  Users,
  BarChart,
  Target,
  ShoppingCart,
  Layers,
  Star,
  ChevronRight
} from 'lucide-react';
import { buildGuideService } from '../services/buildGuideService';
import type { BuildGuideListItem } from '../types/buildGuide';

// Icon mapping for guide categories and types
const categoryIcons: Record<string, any> = {
  'ASIN Analysis': Package,
  'Performance Deep Dive': TrendingUp,
  'Audience Insights': Users,
  'Campaign Optimization': Target,
  'Attribution Analysis': BarChart,
  'Custom Queries': Layers,
  'Default': BookOpen
};

// Difficulty colors
const difficultyColors = {
  beginner: 'bg-green-100 text-green-800',
  intermediate: 'bg-yellow-100 text-yellow-800',
  advanced: 'bg-red-100 text-red-800'
};

export default function BuildGuides() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string | null>(null);
  const [showFavorites, setShowFavorites] = useState(false);
  const [statusFilter, setStatusFilter] = useState<'all' | 'not_started' | 'in_progress' | 'completed'>('all');

  // Fetch guides
  const { data: guides = [], isLoading } = useQuery({
    queryKey: ['build-guides'],
    queryFn: () => buildGuideService.listGuides(),
    staleTime: 5 * 60 * 1000 // 5 minutes
  });

  // Fetch categories
  const { data: categories = [] } = useQuery({
    queryKey: ['build-guide-categories'],
    queryFn: () => buildGuideService.getCategories(),
    staleTime: 10 * 60 * 1000 // 10 minutes
  });

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['build-guide-stats'],
    queryFn: () => buildGuideService.getGuideStatistics(),
    staleTime: 5 * 60 * 1000
  });

  // Filter guides
  const filteredGuides = useMemo(() => {
    let filtered = [...guides];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(guide =>
        guide.name.toLowerCase().includes(query) ||
        guide.short_description?.toLowerCase().includes(query) ||
        guide.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    // Category filter
    if (selectedCategory) {
      filtered = filtered.filter(guide => guide.category === selectedCategory);
    }

    // Difficulty filter
    if (selectedDifficulty) {
      filtered = filtered.filter(guide => guide.difficulty_level === selectedDifficulty);
    }

    // Favorites filter
    if (showFavorites) {
      filtered = filtered.filter(guide => guide.is_favorite);
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(guide => 
        (guide.user_progress?.status || 'not_started') === statusFilter
      );
    }

    return filtered;
  }, [guides, searchQuery, selectedCategory, selectedDifficulty, showFavorites, statusFilter]);

  // Group guides by category
  const groupedGuides = useMemo(() => {
    const groups: Record<string, BuildGuideListItem[]> = {};
    filteredGuides.forEach(guide => {
      const category = guide.category || 'Uncategorized';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(guide);
    });
    return groups;
  }, [filteredGuides]);

  const handleGuideClick = (guideId: string) => {
    navigate(`/build-guides/${guideId}`);
  };

  const toggleFavorite = async (e: React.MouseEvent, guideId: string) => {
    e.stopPropagation();
    try {
      await buildGuideService.toggleFavorite(guideId);
      // Refetch guides to update favorite status
      // In a real app, you'd use optimistic updates
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Build Guides</h1>
                <p className="mt-2 text-gray-600">
                  Step-by-step tactical guidance for AMC query use cases
                </p>
              </div>
              
              {/* Statistics */}
              {stats && (
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
                    <div className="text-sm text-gray-500">Total Guides</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
                    <div className="text-sm text-gray-500">Completed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{stats.in_progress}</div>
                    <div className="text-sm text-gray-500">In Progress</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-4 flex items-center justify-between">
            {/* Search */}
            <div className="flex-1 max-w-lg">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search guides..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Filters */}
            <div className="flex items-center space-x-4 ml-6">
              {/* Category Filter */}
              <select
                value={selectedCategory || ''}
                onChange={(e) => setSelectedCategory(e.target.value || null)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Categories</option>
                {categories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>

              {/* Difficulty Filter */}
              <select
                value={selectedDifficulty || ''}
                onChange={(e) => setSelectedDifficulty(e.target.value || null)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Levels</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Status</option>
                <option value="not_started">Not Started</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
              </select>

              {/* Favorites Toggle */}
              <button
                onClick={() => setShowFavorites(!showFavorites)}
                className={`px-4 py-2 rounded-md flex items-center space-x-2 transition-colors ${
                  showFavorites
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Star className={`h-4 w-4 ${showFavorites ? 'fill-current' : ''}`} />
                <span>Favorites</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredGuides.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No guides found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your search or filter criteria
            </p>
          </div>
        ) : (
          <div className="space-y-8">
            {Object.entries(groupedGuides).map(([category, categoryGuides]) => (
              <div key={category}>
                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                  {categoryIcons[category] && (
                    <categoryIcons[category] className="h-5 w-5 mr-2 text-gray-600" />
                  )}
                  {category}
                  <span className="ml-2 text-sm text-gray-500">({categoryGuides.length})</span>
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {categoryGuides.map(guide => (
                    <GuideCard
                      key={guide.guide_id}
                      guide={guide}
                      onClick={() => handleGuideClick(guide.guide_id)}
                      onToggleFavorite={(e) => toggleFavorite(e, guide.guide_id)}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Guide Card Component
interface GuideCardProps {
  guide: BuildGuideListItem;
  onClick: () => void;
  onToggleFavorite: (e: React.MouseEvent) => void;
}

function GuideCard({ guide, onClick, onToggleFavorite }: GuideCardProps) {
  const Icon = categoryIcons[guide.category] || categoryIcons.Default;
  const progress = guide.user_progress?.progress_percentage || 0;
  const status = guide.user_progress?.status || 'not_started';

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow cursor-pointer"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start space-x-3">
          <div className="p-2 bg-blue-50 rounded-lg">
            <Icon className="h-6 w-6 text-blue-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{guide.name}</h3>
            <p className="mt-1 text-sm text-gray-600 line-clamp-2">
              {guide.short_description}
            </p>
          </div>
        </div>
        <button
          onClick={onToggleFavorite}
          className="text-gray-400 hover:text-yellow-500 transition-colors"
        >
          <Star className={`h-5 w-5 ${guide.is_favorite ? 'fill-yellow-500 text-yellow-500' : ''}`} />
        </button>
      </div>

      {/* Tags */}
      {guide.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {guide.tags.slice(0, 3).map(tag => (
            <span
              key={tag}
              className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
            >
              {tag}
            </span>
          ))}
          {guide.tags.length > 3 && (
            <span className="px-2 py-1 text-gray-500 text-xs">
              +{guide.tags.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Metadata */}
      <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
        <div className="flex items-center space-x-4">
          <span className={`px-2 py-1 rounded text-xs font-medium ${difficultyColors[guide.difficulty_level]}`}>
            {guide.difficulty_level}
          </span>
          <span className="flex items-center">
            <Clock className="h-3 w-3 mr-1" />
            {guide.estimated_time_minutes} min
          </span>
        </div>
      </div>

      {/* Progress */}
      {status !== 'not_started' && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Progress</span>
            <span className="font-medium">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                status === 'completed' ? 'bg-green-600' : 'bg-blue-600'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Status Badge */}
      <div className="mt-4 flex items-center justify-between">
        <span className={`text-xs font-medium px-2 py-1 rounded-full ${
          status === 'completed' 
            ? 'bg-green-100 text-green-800'
            : status === 'in_progress'
            ? 'bg-blue-100 text-blue-800'
            : 'bg-gray-100 text-gray-600'
        }`}>
          {status === 'completed' ? 'Completed' : status === 'in_progress' ? 'In Progress' : 'Not Started'}
        </span>
        <ChevronRight className="h-4 w-4 text-gray-400" />
      </div>
    </div>
  );
}