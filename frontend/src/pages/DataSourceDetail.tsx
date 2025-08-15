/**
 * Data Source Detail Page
 * Display complete schema documentation with fields, examples, and sections
 * Enhanced with two-panel layout, TOC, and field explorer
 */

import { useState, useEffect, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import {
  ArrowLeft,
  Database,
  Code,
  Link2,
  Tag,
  Lock,
  Globe,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Download,
  PlayCircle
} from 'lucide-react';
import { dataSourceService } from '../services/dataSourceService';
import SQLEditor from '../components/common/SQLEditor';
import { TableOfContents } from '../components/data-sources/TableOfContents';
import { FieldExplorer } from '../components/data-sources/FieldExplorer';
import type { QueryExample, CompleteSchema } from '../types/dataSource';

export default function DataSourceDetail() {
  const { schemaId } = useParams<{ schemaId: string }>();
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState('overview');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [copiedExample, setCopiedExample] = useState<string | null>(null);
  const [fieldSearch] = useState('');
  const contentRef = useRef<HTMLDivElement>(null);

  // Fetch complete schema
  console.log('DataSourceDetail - schemaId from URL:', schemaId);
  const { data: schema, isLoading, error } = useQuery<CompleteSchema>({
    queryKey: ['dataSource', schemaId],
    queryFn: () => {
      console.log('Fetching schema for:', schemaId);
      return dataSourceService.getCompleteSchema(schemaId!);
    },
    enabled: !!schemaId,
    staleTime: 10 * 60 * 1000
  });

  // Build TOC items
  const tocItems = useMemo(() => {
    if (!schema) return [];
    return [
      { id: 'overview', title: 'Overview', level: 1 },
      { id: 'schema', title: `Fields (${schema.fields.length})`, level: 1 },
      { id: 'examples', title: `Examples (${schema.examples.length})`, level: 1 },
      { id: 'relationships', title: 'Relationships', level: 1 },
      ...schema.sections.map(section => ({
        id: section.id,
        title: section.section_type.replace(/_/g, ' ').split(' ')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' '),
        level: 2
      }))
    ];
  }, [schema]);

  // Handle section navigation
  const handleSectionClick = (sectionId: string) => {
    setActiveSection(sectionId);
    const element = document.getElementById(sectionId);
    if (element) {
      const offset = 80;
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.scrollY - offset;
      
      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
    }
  };

  // Observe active section based on scroll
  useEffect(() => {
    if (!schema) return;

    const observerOptions = {
      root: null,
      rootMargin: '-80px 0px -70% 0px',
      threshold: 0
    };

    const observerCallback = (entries: IntersectionObserverEntry[]) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          setActiveSection(entry.target.id);
        }
      });
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);

    tocItems.forEach(item => {
      const element = document.getElementById(item.id);
      if (element) observer.observe(element);
    });

    return () => observer.disconnect();
  }, [schema, tocItems]);


  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  const copyExample = async (example: QueryExample) => {
    try {
      await navigator.clipboard.writeText(example.sql_query);
      setCopiedExample(example.id);
      setTimeout(() => setCopiedExample(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const navigateToQueryBuilder = (example: QueryExample) => {
    // Store the example in session storage
    sessionStorage.setItem('queryBuilderDraft', JSON.stringify({
      name: example.title,
      description: example.description,
      sql_query: example.sql_query,
      parameters: example.parameters || {},
      fromDataSource: schema?.schema.schema_id
    }));
    navigate('/query-builder/new');
  };


  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !schema) {
    // Log the error for debugging
    if (error) {
      console.error('Error loading schema:', error);
    }
    
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {error ? 'Unable to load schema' : 'Schema not found'}
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            {error ? 
              'There was an error loading the schema details. Please ensure you are logged in and try again.' : 
              `Schema "${schemaId}" could not be found.`}
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => navigate('/data-sources')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Return to data sources
            </button>
            {error && (
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Try again
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-20">
        <div className="px-6">
          <div className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => navigate('/data-sources')}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <ArrowLeft className="h-5 w-5" />
                </button>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-2xl font-bold text-gray-900">
                      {schema.schema.name}
                    </h1>
                    {schema.schema.is_paid_feature && (
                      <Lock className="h-5 w-5 text-yellow-600" />
                    )}
                  </div>
                  <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                    <span>{schema.schema.category}</span>
                    <span>•</span>
                    <span>Version {schema.schema.version}</span>
                    {schema.schema.availability?.marketplaces && (
                      <>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Globe className="h-3 w-3" />
                          {Object.keys(schema.schema.availability.marketplaces).length} regions
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-2">
                  <Download className="h-4 w-4" />
                  Export
                </button>
                {schema.examples.length > 0 && (
                  <button
                    onClick={() => navigateToQueryBuilder(schema.examples[0])}
                    className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                  >
                    <PlayCircle className="h-4 w-4" />
                    Open in Query Builder
                  </button>
                )}
              </div>
            </div>

            {/* Removed traditional tabs - using TOC navigation instead */}
          </div>
        </div>
      </div>

      {/* Two-Panel Layout */}
      <div className="flex gap-8 px-6 py-8">
        {/* Left Sidebar - TOC */}
        <aside className="w-64 flex-shrink-0 hidden xl:block">
          <TableOfContents
            sections={tocItems}
            activeSection={activeSection}
            onSectionClick={handleSectionClick}
          />
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-w-0" ref={contentRef}>
          <div className="space-y-8">
            {/* Overview Section */}
            <section id="overview" className="scroll-mt-24">
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h2 className="text-xl font-semibold mb-4">Overview</h2>
                <p className="text-gray-600 mb-6">{schema.schema.description}</p>
              
                {/* AMC Tables */}
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">AMC Tables</h3>
                  <div className="flex flex-wrap gap-2">
                    {schema.schema.data_sources.map(source => (
                      <code
                        key={source}
                        className="px-3 py-1 bg-gray-100 text-gray-800 rounded text-sm font-mono"
                      >
                        {source}
                      </code>
                    ))}
                  </div>
                </div>

                {/* Tags */}
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {schema.schema.tags.map(tag => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm"
                      >
                        <Tag className="h-3 w-3" />
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Statistics */}
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-gray-900">{schema.fields.length}</div>
                    <div className="text-sm text-gray-500">Total Fields</div>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-blue-900">
                      {schema.fields.filter(f => f.dimension_or_metric === 'Dimension').length}
                    </div>
                    <div className="text-sm text-blue-600">Dimensions</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-green-900">
                      {schema.fields.filter(f => f.dimension_or_metric === 'Metric').length}
                    </div>
                    <div className="text-sm text-green-600">Metrics</div>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-purple-900">{schema.examples.length}</div>
                    <div className="text-sm text-purple-600">Examples</div>
                  </div>
                </div>
              </div>

              {/* Documentation Sections */}
              {schema.sections.map(section => (
                <div key={section.id} id={section.id} className="scroll-mt-24 mt-6">
                  <div className="bg-white rounded-lg border border-gray-200">
                    <button
                      onClick={() => toggleSection(section.id)}
                      className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                    >
                      <h3 className="text-lg font-semibold capitalize">
                        {section.section_type.replace(/_/g, ' ')}
                      </h3>
                      {expandedSections.has(section.id) ? (
                        <ChevronDown className="h-5 w-5 text-gray-400" />
                      ) : (
                        <ChevronRight className="h-5 w-5 text-gray-400" />
                      )}
                    </button>
                    {expandedSections.has(section.id) && (
                      <div className="px-6 pb-6 prose prose-sm max-w-none">
                        <ReactMarkdown>{section.content_markdown}</ReactMarkdown>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </section>

            {/* Schema Fields Section */}
            <section id="schema" className="scroll-mt-24">
              <div className="">
                <h2 className="text-xl font-semibold mb-4">Schema Fields</h2>
                <FieldExplorer fields={schema.fields} searchQuery={fieldSearch} />
              </div>
            </section>

            {/* Query Examples Section */}
            <section id="examples" className="scroll-mt-24">
              <div className="">
                <h2 className="text-xl font-semibold mb-4">Query Examples</h2>
                {schema.examples.length === 0 ? (
                  <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
                    <Code className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">No query examples available yet</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {schema.examples.map(example => (
                      <div key={example.id} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                        <div className="px-6 py-4 border-b bg-gray-50">
                          <div className="flex items-start justify-between">
                            <div>
                              <h3 className="text-lg font-semibold text-gray-900">
                                {example.title}
                              </h3>
                              {example.description && (
                                <p className="mt-1 text-sm text-gray-600">
                                  {example.description}
                                </p>
                              )}
                              {example.category && (
                                <span className="inline-block mt-2 px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                                  {example.category}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => copyExample(example)}
                                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                                title="Copy SQL"
                              >
                                {copiedExample === example.id ? (
                                  <Check className="h-4 w-4 text-green-600" />
                                ) : (
                                  <Copy className="h-4 w-4" />
                                )}
                              </button>
                              <button
                                onClick={() => navigateToQueryBuilder(example)}
                                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                              >
                                Open in Query Builder
                              </button>
                            </div>
                          </div>
                        </div>
                        <div className="p-6">
                          <SQLEditor 
                            value={example.sql_query} 
                            onChange={() => {}} 
                            readOnly={true}
                            height="200px"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>

            {/* Relationships Section */}
            <section id="relationships" className="scroll-mt-24">
              <div className="">
                <h2 className="text-xl font-semibold mb-4">Relationships</h2>
                
                {/* Outgoing Relationships */}
                {schema.relationships.from.length > 0 && (
                  <div className="bg-white rounded-lg border border-gray-200 p-6 mb-4">
                    <h3 className="text-lg font-semibold mb-4">Related Schemas</h3>
                    <div className="space-y-3">
                      {schema.relationships.from.map(rel => (
                        <div
                          key={rel.id}
                          className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                              {rel.relationship_type}
                            </span>
                            <div>
                              <button
                                onClick={() => navigate(`/data-sources/${rel.target?.schema_id}`)}
                                className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                              >
                                {rel.target?.name}
                                <ExternalLink className="h-3 w-3" />
                              </button>
                              {rel.description && (
                                <p className="text-sm text-gray-600 mt-1">{rel.description}</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Incoming Relationships */}
                {schema.relationships.to.length > 0 && (
                  <div className="bg-white rounded-lg border border-gray-200 p-6">
                    <h3 className="text-lg font-semibold mb-4">Referenced By</h3>
                    <div className="space-y-3">
                      {schema.relationships.to.map(rel => (
                        <div
                          key={rel.id}
                          className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">
                              {rel.relationship_type}
                            </span>
                            <div>
                              <button
                                onClick={() => navigate(`/data-sources/${rel.source?.schema_id}`)}
                                className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                              >
                                {rel.source?.name}
                                <ExternalLink className="h-3 w-3" />
                              </button>
                              {rel.description && (
                                <p className="text-sm text-gray-600 mt-1">{rel.description}</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {schema.relationships.from.length === 0 && schema.relationships.to.length === 0 && (
                  <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
                    <Link2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">No relationships defined for this schema</p>
                  </div>
                )}
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}