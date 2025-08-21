/**
 * Build Guide Detail Page
 * Displays a single build guide with sections, queries, and progress tracking
 */

import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  BookOpen,
  Clock,
  Play,
  CheckCircle,
  Circle,
  ChevronRight,
  ChevronDown,
  Star,
  Copy
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import { buildGuideService } from '../services/buildGuideService';
import SQLEditor from '../components/common/SQLEditor';
import type { BuildGuideQuery } from '../types/buildGuide';

export default function BuildGuideDetail() {
  const { guideId } = useParams<{ guideId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const contentRef = useRef<HTMLDivElement>(null);
  
  const [activeSection, setActiveSection] = useState<string>('');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [expandedQueries, setExpandedQueries] = useState<Set<string>>(new Set());

  // Function to scroll to section
  const scrollToSection = (sectionId: string) => {
    setActiveSection(sectionId);
    const element = document.getElementById(sectionId);
    if (element) {
      // Account for sticky header
      const yOffset = -100;
      const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  // Fetch guide data
  const { data: guide, isLoading, error } = useQuery({
    queryKey: ['build-guide', guideId],
    queryFn: () => buildGuideService.getGuide(guideId!),
    enabled: !!guideId,
    staleTime: 5 * 60 * 1000
  });

  // Start guide mutation
  const startGuideMutation = useMutation({
    mutationFn: () => buildGuideService.startGuide(guideId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['build-guide', guideId] });
      toast.success('Guide started!');
    }
  });

  // Update progress mutation
  const updateProgressMutation = useMutation({
    mutationFn: (params: { sectionId?: string; queryId?: string }) => {
      if (params.sectionId) {
        return buildGuideService.markSectionComplete(guideId!, params.sectionId);
      } else if (params.queryId) {
        return buildGuideService.markQueryExecuted(guideId!, params.queryId);
      }
      return Promise.reject('No section or query specified');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['build-guide', guideId] });
    }
  });

  // Toggle favorite mutation
  const toggleFavoriteMutation = useMutation({
    mutationFn: () => buildGuideService.toggleFavorite(guideId!),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['build-guide', guideId] });
      toast.success(data.is_favorite ? 'Added to favorites' : 'Removed from favorites');
    }
  });

  // Initialize guide on mount
  useEffect(() => {
    if (guide && (!guide.user_progress || guide.user_progress.status === 'not_started')) {
      startGuideMutation.mutate();
    }
  }, [guide]);

  // Set initial active section
  useEffect(() => {
    if (guide?.sections && guide.sections.length > 0 && !activeSection) {
      setActiveSection(guide.sections[0].section_id);
      // Expand all sections by default
      const allSections = new Set(guide.sections.map(s => s.section_id));
      setExpandedSections(allSections);
    }
  }, [guide, activeSection]);

  // Track scroll position to update active section
  useEffect(() => {
    const handleScroll = () => {
      if (!guide?.sections) return;
      
      const scrollPosition = window.scrollY + 150; // Account for header
      
      // Check queries section
      const queriesElement = document.getElementById('queries');
      if (queriesElement && scrollPosition >= queriesElement.offsetTop) {
        setActiveSection('queries');
        return;
      }
      
      // Check content sections
      for (let i = guide.sections.length - 1; i >= 0; i--) {
        const section = guide.sections[i];
        const element = document.getElementById(section.section_id);
        if (element && scrollPosition >= element.offsetTop) {
          setActiveSection(section.section_id);
          return;
        }
      }
      
      // Default to first section if at top
      if (guide.sections.length > 0) {
        setActiveSection(guide.sections[0].section_id);
      }
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Call once to set initial state
    
    return () => window.removeEventListener('scroll', handleScroll);
  }, [guide]);

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  };

  const toggleQuery = (queryId: string) => {
    setExpandedQueries(prev => {
      const newSet = new Set(prev);
      if (newSet.has(queryId)) {
        newSet.delete(queryId);
      } else {
        newSet.add(queryId);
      }
      return newSet;
    });
  };

  const handleSectionComplete = (sectionId: string) => {
    updateProgressMutation.mutate({ sectionId });
  };

  const handleQueryExecute = async (query: BuildGuideQuery) => {
    // Navigate to query builder with the query pre-filled
    sessionStorage.setItem('queryBuilderDraft', JSON.stringify({
      name: query.title,
      description: query.description,
      sql_query: query.sql_query,
      parameters: query.default_parameters || {},
      fromGuide: guideId
    }));
    navigate('/query-builder/new');
  };

  const handleQueryCopy = async (query: BuildGuideQuery) => {
    try {
      await navigator.clipboard.writeText(query.sql_query);
      toast.success('Query copied to clipboard');
    } catch (error) {
      toast.error('Failed to copy query');
    }
  };

  const handleCreateTemplate = async (query: BuildGuideQuery) => {
    try {
      await buildGuideService.createTemplateFromQuery(guideId!, query.id);
      toast.success('Template created successfully');
    } catch (error) {
      toast.error('Failed to create template');
    }
  };

  const handleCompleteGuide = async () => {
    try {
      await buildGuideService.markGuideComplete(guideId!);
      queryClient.invalidateQueries({ queryKey: ['build-guide', guideId] });
      toast.success('Congratulations! Guide completed!');
    } catch (error) {
      toast.error('Failed to mark guide as complete');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !guide) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Guide not found</h3>
          <p className="text-sm text-gray-600 mb-4">
            The guide you're looking for doesn't exist or has been removed.
          </p>
          <button
            onClick={() => navigate('/build-guides')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Guides
          </button>
        </div>
      </div>
    );
  }

  const progress = guide.user_progress?.progress_percentage || 0;
  const status = guide.user_progress?.status || 'not_started';
  const completedSections = guide.user_progress?.completed_sections || [];
  const executedQueries = guide.user_progress?.executed_queries || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => navigate('/build-guides')}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <ArrowLeft className="h-5 w-5" />
                </button>
                <div>
                  <div className="flex items-center space-x-2">
                    <h1 className="text-2xl font-bold text-gray-900">{guide.name}</h1>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      guide.difficulty_level === 'beginner' 
                        ? 'bg-green-100 text-green-800'
                        : guide.difficulty_level === 'intermediate'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {guide.difficulty_level}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                    <span>{guide.category}</span>
                    <span>•</span>
                    <span className="flex items-center">
                      <Clock className="h-3 w-3 mr-1" />
                      {guide.estimated_time_minutes} min
                    </span>
                    <span>•</span>
                    <span>{guide.sections?.length || 0} sections</span>
                    <span>•</span>
                    <span>{guide.queries?.length || 0} queries</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => toggleFavoriteMutation.mutate()}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <Star className={`h-5 w-5 ${guide.is_favorite ? 'fill-yellow-500 text-yellow-500' : 'text-gray-400'}`} />
                </button>
                {status === 'completed' ? (
                  <div className="px-4 py-2 bg-green-100 text-green-800 rounded-lg font-medium flex items-center">
                    <CheckCircle className="h-5 w-5 mr-2" />
                    Completed
                  </div>
                ) : (
                  <button
                    onClick={handleCompleteGuide}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                  >
                    Mark as Complete
                  </button>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mt-4">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-gray-600">Overall Progress</span>
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
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Table of Contents */}
          <aside className="w-64 flex-shrink-0 hidden lg:block">
            <div className="bg-white rounded-lg border border-gray-200 p-4 sticky top-24">
              <h3 className="font-semibold text-gray-900 mb-4">Table of Contents</h3>
              <nav className="space-y-2">
                {guide.sections?.map(section => (
                  <button
                    key={section.section_id}
                    onClick={() => scrollToSection(section.section_id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center justify-between ${
                      activeSection === section.section_id
                        ? 'bg-blue-50 text-blue-700'
                        : 'hover:bg-gray-50 text-gray-600'
                    }`}
                  >
                    <span className="flex items-center">
                      {completedSections.includes(section.section_id) ? (
                        <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
                      ) : (
                        <Circle className="h-4 w-4 mr-2" />
                      )}
                      {section.title}
                    </span>
                  </button>
                ))}
                
                {/* Queries Section */}
                {guide.queries && guide.queries.length > 0 && (
                  <button
                    onClick={() => scrollToSection('queries')}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center justify-between ${
                      activeSection === 'queries'
                        ? 'bg-blue-50 text-blue-700'
                        : 'hover:bg-gray-50 text-gray-600'
                    }`}
                  >
                    <span className="flex items-center">
                      <Play className="h-4 w-4 mr-2" />
                      Queries ({guide.queries.length})
                    </span>
                  </button>
                )}
              </nav>
            </div>
          </aside>

          {/* Content Area */}
          <main className="flex-1 min-w-0" ref={contentRef}>
            <div className="space-y-6">
              {/* Description */}
              {guide.short_description && (
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <p className="text-gray-600">{guide.short_description}</p>
                  
                  {/* Tags */}
                  {guide.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-4">
                      {guide.tags.map(tag => (
                        <span
                          key={tag}
                          className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  
                  {/* Prerequisites */}
                  {guide.prerequisites.length > 0 && (
                    <div className="mt-4">
                      <h4 className="font-medium text-gray-900 mb-2">Prerequisites</h4>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        {guide.prerequisites.map((prereq, index) => (
                          <li key={index}>{prereq}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Sections */}
              {guide.sections?.map(section => (
                <div
                  key={section.section_id}
                  id={section.section_id}
                  className="bg-white rounded-lg border border-gray-200 overflow-hidden"
                >
                  <div
                    className="px-6 py-4 bg-gray-50 flex items-center justify-between cursor-pointer"
                    onClick={() => toggleSection(section.section_id)}
                  >
                    <div className="flex items-center space-x-3">
                      {completedSections.includes(section.section_id) ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <Circle className="h-5 w-5 text-gray-400" />
                      )}
                      <h2 className="text-lg font-semibold text-gray-900">{section.title}</h2>
                    </div>
                    <div className="flex items-center space-x-2">
                      {!completedSections.includes(section.section_id) && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSectionComplete(section.section_id);
                          }}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          Mark Complete
                        </button>
                      )}
                      {expandedSections.has(section.section_id) ? (
                        <ChevronDown className="h-5 w-5 text-gray-400" />
                      ) : (
                        <ChevronRight className="h-5 w-5 text-gray-400" />
                      )}
                    </div>
                  </div>
                  
                  {expandedSections.has(section.section_id) && (
                    <div className="px-6 py-4">
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>{section.content_markdown}</ReactMarkdown>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Queries */}
              {guide.queries && guide.queries.length > 0 && (
                <div id="queries" className="space-y-4">
                  <h2 className="text-xl font-semibold text-gray-900">Queries</h2>
                  
                  {guide.queries.map(query => (
                    <div
                      key={query.id}
                      className="bg-white rounded-lg border border-gray-200 overflow-hidden"
                    >
                      <div
                        className="px-6 py-4 bg-gray-50 flex items-center justify-between cursor-pointer"
                        onClick={() => toggleQuery(query.id)}
                      >
                        <div className="flex items-center space-x-3">
                          {executedQueries.includes(query.id) ? (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          ) : (
                            <Circle className="h-5 w-5 text-gray-400" />
                          )}
                          <div>
                            <h3 className="font-semibold text-gray-900">{query.title}</h3>
                            {query.description && (
                              <p className="text-sm text-gray-600 mt-1">{query.description}</p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 text-xs rounded ${
                            query.query_type === 'exploratory' 
                              ? 'bg-blue-100 text-blue-700'
                              : query.query_type === 'validation'
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-green-100 text-green-700'
                          }`}>
                            {query.query_type}
                          </span>
                          {expandedQueries.has(query.id) ? (
                            <ChevronDown className="h-5 w-5 text-gray-400" />
                          ) : (
                            <ChevronRight className="h-5 w-5 text-gray-400" />
                          )}
                        </div>
                      </div>
                      
                      {expandedQueries.has(query.id) && (
                        <div className="p-6 space-y-4">
                          {/* SQL Editor */}
                          <div>
                            <SQLEditor
                              value={query.sql_query}
                              onChange={() => {}}
                              readOnly={true}
                              height="300px"
                            />
                          </div>
                          
                          {/* Interpretation Notes */}
                          {query.interpretation_notes && (
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                              <h4 className="font-medium text-blue-900 mb-2">How to Interpret Results</h4>
                              <p className="text-sm text-blue-800">{query.interpretation_notes}</p>
                            </div>
                          )}
                          
                          {/* Examples */}
                          {query.examples && query.examples.length > 0 && (
                            <div className="space-y-3">
                              <h4 className="font-medium text-gray-900">Example Results</h4>
                              {query.examples.map(example => (
                                <div key={example.id} className="bg-gray-50 rounded-lg p-4">
                                  <h5 className="font-medium text-gray-900 mb-2">{example.example_name}</h5>
                                  {example.interpretation_markdown && (
                                    <div className="prose prose-sm max-w-none">
                                      <ReactMarkdown>{example.interpretation_markdown}</ReactMarkdown>
                                    </div>
                                  )}
                                  {example.insights.length > 0 && (
                                    <div className="mt-3">
                                      <h6 className="text-sm font-medium text-gray-700 mb-1">Key Insights:</h6>
                                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                                        {example.insights.map((insight, index) => (
                                          <li key={index}>{insight}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                          
                          {/* Actions */}
                          <div className="flex items-center justify-between pt-4 border-t">
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => handleQueryExecute(query)}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
                              >
                                <Play className="h-4 w-4 mr-2" />
                                Open in Query Builder
                              </button>
                              <button
                                onClick={() => handleQueryCopy(query)}
                                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 flex items-center"
                              >
                                <Copy className="h-4 w-4 mr-2" />
                                Copy SQL
                              </button>
                            </div>
                            
                            <button
                              onClick={() => handleCreateTemplate(query)}
                              className="text-sm text-gray-600 hover:text-gray-900"
                            >
                              Save as Template
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Metrics Definitions */}
              {guide.metrics && guide.metrics.length > 0 && (
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Metrics & Dimensions</h2>
                  <div className="space-y-3">
                    {guide.metrics.map(metric => (
                      <div key={metric.id} className="border-l-4 border-blue-500 pl-4">
                        <div className="flex items-center space-x-2">
                          <h4 className="font-medium text-gray-900">{metric.display_name}</h4>
                          <span className={`px-2 py-1 text-xs rounded ${
                            metric.metric_type === 'dimension'
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-green-100 text-green-700'
                          }`}>
                            {metric.metric_type}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{metric.definition}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}