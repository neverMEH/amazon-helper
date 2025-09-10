# Build Guides System

## Overview

The Build Guides system provides structured, step-by-step tutorials that teach users how to build effective AMC queries for specific use cases. It combines educational content with hands-on practice, progress tracking, and example results to accelerate user learning.

## Key Components

### Backend Services
- `amc_manager/services/build_guide_service.py` - Guide management and progress tracking
- `amc_manager/api/supabase/build_guides.py` - Guide API endpoints
- `amc_manager/services/workflow_service.py` - Integration with query execution

### Frontend Components
- `frontend/src/pages/BuildGuides.tsx` - Guide list and navigation
- `frontend/src/pages/BuildGuideDetail.tsx` - Individual guide reader
- `frontend/src/components/BuildGuideProgress.tsx` - Progress tracking
- `frontend/src/components/GuideQueryEditor.tsx` - Interactive query building

### Database Tables
- `build_guides` - Guide metadata and configuration
- `build_guide_sections` - Guide content sections
- `build_guide_queries` - Associated SQL queries
- `build_guide_examples` - Example results and explanations
- `build_guide_metrics` - Metric definitions and context
- `user_guide_progress` - User progress tracking
- `user_guide_favorites` - User favorites

## Guide Data Model

### Guide Structure
```python
# build_guides table schema
class BuildGuide:
    id: UUID                    # Guide identifier
    title: str                 # Guide title
    description: str           # Guide description
    category: str              # Guide category (e.g., "Attribution", "Optimization")
    
    # Guide Configuration
    difficulty_level: str      # BEGINNER, INTERMEDIATE, ADVANCED
    estimated_time: int        # Minutes to complete
    prerequisites: List[str]   # Required knowledge/skills
    
    # Content Organization
    section_count: int         # Number of sections
    query_count: int          # Number of queries
    
    # Tracking Metrics
    completion_count: int      # Times completed by users
    favorite_count: int        # Number of users who favorited
    
    # Status
    is_published: bool         # Whether guide is live
    
    # Audit Fields
    created_at: datetime
    updated_at: datetime
```

### Section Structure
```python
# build_guide_sections table schema
class BuildGuideSection:
    id: UUID                   # Section identifier
    guide_id: UUID            # FK to build_guides
    
    # Section Properties
    section_number: int        # Order within guide
    title: str                # Section title
    content: str              # Markdown content
    section_type: str         # INTRODUCTION, CONCEPT, HANDS_ON, EXAMPLE, SUMMARY
    
    # Interactive Elements
    has_query: bool           # Whether section includes a query
    has_example: bool         # Whether section includes examples
    
    # Completion Requirements
    is_required: bool         # Must complete to progress
    estimated_time: int       # Minutes to complete section
```

## Content Management

### Guide Creation Service
```python
# build_guide_service.py - Guide management
class BuildGuideService(DatabaseService):
    def __init__(self):
        super().__init__()
    
    async def create_guide(self, guide_data: dict) -> dict:
        """Create new build guide with sections"""
        
        # Create guide record
        guide = self.db.table('build_guides').insert({
            'title': guide_data['title'],
            'description': guide_data['description'],
            'category': guide_data['category'],
            'difficulty_level': guide_data.get('difficulty_level', 'BEGINNER'),
            'estimated_time': guide_data.get('estimated_time', 30),
            'prerequisites': guide_data.get('prerequisites', []),
            'is_published': guide_data.get('is_published', False),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).execute()
        
        guide_id = guide.data[0]['id']
        
        # Create sections if provided
        if 'sections' in guide_data:
            await self.create_guide_sections(guide_id, guide_data['sections'])
        
        return guide.data[0]
    
    async def create_guide_sections(self, guide_id: str, sections: List[dict]):
        """Create sections for a guide"""
        
        section_records = []
        for i, section_data in enumerate(sections, 1):
            section_records.append({
                'guide_id': guide_id,
                'section_number': i,
                'title': section_data['title'],
                'content': section_data['content'],
                'section_type': section_data.get('section_type', 'CONCEPT'),
                'has_query': section_data.get('has_query', False),
                'has_example': section_data.get('has_example', False),
                'is_required': section_data.get('is_required', True),
                'estimated_time': section_data.get('estimated_time', 5)
            })
        
        # Insert all sections
        self.db.table('build_guide_sections')\
            .insert(section_records)\
            .execute()
        
        # Update guide section count
        self.db.table('build_guides')\
            .update({'section_count': len(section_records)})\
            .eq('id', guide_id)\
            .execute()
    
    async def get_guide_with_sections(self, guide_id: str) -> dict:
        """Get complete guide with all sections"""
        
        # Get guide metadata
        guide_result = self.db.table('build_guides')\
            .select('*')\
            .eq('id', guide_id)\
            .execute()
        
        if not guide_result.data:
            raise HTTPException(status_code=404, detail="Guide not found")
        
        guide = guide_result.data[0]
        
        # Get sections
        sections_result = self.db.table('build_guide_sections')\
            .select('*')\
            .eq('guide_id', guide_id)\
            .order('section_number')\
            .execute()
        
        # Get associated queries
        queries_result = self.db.table('build_guide_queries')\
            .select('*')\
            .eq('guide_id', guide_id)\
            .execute()
        
        # Get examples
        examples_result = self.db.table('build_guide_examples')\
            .select('*')\
            .eq('guide_id', guide_id)\
            .execute()
        
        return {
            **guide,
            'sections': sections_result.data,
            'queries': queries_result.data,
            'examples': examples_result.data
        }
```

### Query Integration
```python
async def associate_query_with_guide(self, guide_id: str, section_number: int, 
                                   query_data: dict) -> dict:
    """Associate SQL query with guide section"""
    
    query_record = {
        'guide_id': guide_id,
        'section_number': section_number,
        'query_title': query_data['title'],
        'sql_query': query_data['sql'],
        'parameters': query_data.get('parameters', {}),
        'explanation': query_data.get('explanation'),
        'expected_result_description': query_data.get('expected_result'),
        'difficulty_notes': query_data.get('difficulty_notes')
    }
    
    result = self.db.table('build_guide_queries')\
        .insert(query_record)\
        .execute()
    
    # Update guide query count
    await self.update_guide_query_count(guide_id)
    
    return result.data[0]

async def create_example_result(self, guide_id: str, query_id: str, 
                              example_data: dict) -> dict:
    """Create example result for guide query"""
    
    example_record = {
        'guide_id': guide_id,
        'query_id': query_id,
        'example_type': example_data.get('type', 'SAMPLE_OUTPUT'),
        'title': example_data['title'],
        'description': example_data.get('description'),
        'sample_data': example_data.get('sample_data'),
        'interpretation': example_data.get('interpretation'),
        'key_insights': example_data.get('key_insights', [])
    }
    
    result = self.db.table('build_guide_examples')\
        .insert(example_record)\
        .execute()
    
    return result.data[0]
```

## User Progress Tracking

### Progress Management
```python
class UserProgressService(DatabaseService):
    async def start_guide(self, user_id: str, guide_id: str) -> dict:
        """Initialize user progress for guide"""
        
        # Check if progress already exists
        existing = self.db.table('user_guide_progress')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('guide_id', guide_id)\
            .execute()
        
        if existing.data:
            # Update last accessed time
            self.db.table('user_guide_progress')\
                .update({'last_accessed_at': datetime.utcnow().isoformat()})\
                .eq('id', existing.data[0]['id'])\
                .execute()
            
            return existing.data[0]
        
        # Create new progress record
        progress = self.db.table('user_guide_progress').insert({
            'user_id': user_id,
            'guide_id': guide_id,
            'current_section': 1,
            'completed_sections': [],
            'progress_percentage': 0.0,
            'status': 'IN_PROGRESS',
            'started_at': datetime.utcnow().isoformat(),
            'last_accessed_at': datetime.utcnow().isoformat()
        }).execute()
        
        return progress.data[0]
    
    async def update_progress(self, user_id: str, guide_id: str, 
                            progress_data: dict) -> dict:
        """Update user's guide progress"""
        
        # Get current progress
        current_progress = self.db.table('user_guide_progress')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('guide_id', guide_id)\
            .execute()
        
        if not current_progress.data:
            raise HTTPException(status_code=404, detail="Progress not found")
        
        current = current_progress.data[0]
        
        # Update completed sections
        completed_sections = current['completed_sections'] or []
        new_section = progress_data.get('completed_section')
        
        if new_section and new_section not in completed_sections:
            completed_sections.append(new_section)
        
        # Get guide section count for percentage calculation
        guide = self.db.table('build_guides')\
            .select('section_count')\
            .eq('id', guide_id)\
            .execute()
        
        total_sections = guide.data[0]['section_count'] if guide.data else 1
        progress_percentage = (len(completed_sections) / total_sections) * 100
        
        # Determine status
        status = 'COMPLETED' if progress_percentage >= 100 else 'IN_PROGRESS'
        
        # Update progress
        update_data = {
            'current_section': progress_data.get('current_section', current['current_section']),
            'completed_sections': completed_sections,
            'progress_percentage': progress_percentage,
            'status': status,
            'last_accessed_at': datetime.utcnow().isoformat()
        }
        
        if status == 'COMPLETED' and current['status'] != 'COMPLETED':
            update_data['completed_at'] = datetime.utcnow().isoformat()
            
            # Increment guide completion count
            self.db.table('build_guides')\
                .update({'completion_count': self.db.func.coalesce(self.db.column('completion_count'), 0) + 1})\
                .eq('id', guide_id)\
                .execute()
        
        self.db.table('user_guide_progress')\
            .update(update_data)\
            .eq('user_id', user_id)\
            .eq('guide_id', guide_id)\
            .execute()
        
        return {**current, **update_data}
    
    async def favorite_guide(self, user_id: str, guide_id: str) -> dict:
        """Add guide to user's favorites"""
        
        # Check if already favorited
        existing = self.db.table('user_guide_favorites')\
            .select('id')\
            .eq('user_id', user_id)\
            .eq('guide_id', guide_id)\
            .execute()
        
        if existing.data:
            return {'already_favorited': True}
        
        # Add favorite
        self.db.table('user_guide_favorites').insert({
            'user_id': user_id,
            'guide_id': guide_id,
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        # Increment guide favorite count
        self.db.table('build_guides')\
            .update({'favorite_count': self.db.func.coalesce(self.db.column('favorite_count'), 0) + 1})\
            .eq('id', guide_id)\
            .execute()
        
        return {'favorited': True}
```

## Frontend Implementation

### Guide Reader Component
```typescript
// BuildGuideDetail.tsx - Interactive guide reader
interface BuildGuideDetailProps {
  guideId: string;
}

const BuildGuideDetail: React.FC<BuildGuideDetailProps> = ({ guideId }) => {
  const [currentSection, setCurrentSection] = useState(1);
  const [completedSections, setCompletedSections] = useState<number[]>([]);
  
  const { data: guide, isLoading } = useQuery({
    queryKey: ['build-guide', guideId],
    queryFn: () => buildGuideService.getGuide(guideId)
  });
  
  const { data: progress } = useQuery({
    queryKey: ['guide-progress', guideId],
    queryFn: () => buildGuideService.getUserProgress(guideId),
    enabled: !!guideId
  });
  
  const updateProgressMutation = useMutation({
    mutationFn: (progressData: any) => 
      buildGuideService.updateProgress(guideId, progressData),
    onSuccess: () => {
      queryClient.invalidateQueries(['guide-progress', guideId]);
    }
  });
  
  const handleSectionComplete = (sectionNumber: number) => {
    const newCompleted = [...completedSections, sectionNumber];
    setCompletedSections(newCompleted);
    
    updateProgressMutation.mutate({
      current_section: sectionNumber + 1,
      completed_section: sectionNumber
    });
  };
  
  const navigateToSection = (sectionNumber: number) => {
    setCurrentSection(sectionNumber);
    updateProgressMutation.mutate({
      current_section: sectionNumber
    });
  };
  
  if (isLoading) return <LoadingSpinner />;
  if (!guide) return <div>Guide not found</div>;
  
  const currentSectionData = guide.sections.find(
    s => s.section_number === currentSection
  );
  
  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Guide Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{guide.title}</h1>
        <p className="text-lg text-gray-600 mt-2">{guide.description}</p>
        
        <div className="flex items-center space-x-4 mt-4">
          <span className={`px-3 py-1 rounded-full text-sm ${getDifficultyColor(guide.difficulty_level)}`}>
            {guide.difficulty_level}
          </span>
          <span className="text-gray-500">
            ⏱️ {guide.estimated_time} minutes
          </span>
          <span className="text-gray-500">
            📚 {guide.section_count} sections
          </span>
        </div>
      </div>
      
      {/* Progress Bar */}
      <ProgressBar 
        progress={progress?.progress_percentage || 0}
        completedSections={completedSections.length}
        totalSections={guide.section_count}
      />
      
      {/* Section Navigation */}
      <div className="flex overflow-x-auto space-x-2 py-4 mb-6">
        {guide.sections.map((section) => (
          <SectionTab
            key={section.section_number}
            section={section}
            isActive={currentSection === section.section_number}
            isCompleted={completedSections.includes(section.section_number)}
            onClick={() => navigateToSection(section.section_number)}
          />
        ))}
      </div>
      
      {/* Section Content */}
      {currentSectionData && (
        <GuideSection
          section={currentSectionData}
          guide={guide}
          onComplete={() => handleSectionComplete(currentSection)}
          onNext={() => navigateToSection(currentSection + 1)}
          onPrevious={() => navigateToSection(currentSection - 1)}
          canGoNext={currentSection < guide.section_count}
          canGoPrevious={currentSection > 1}
        />
      )}
    </div>
  );
};
```

### Interactive Query Section
```typescript
// GuideQueryEditor.tsx - Interactive query building
interface GuideQueryEditorProps {
  query: BuildGuideQuery;
  onQueryExecute: (results: any) => void;
}

const GuideQueryEditor: React.FC<GuideQueryEditorProps> = ({ 
  query, 
  onQueryExecute 
}) => {
  const [sql, setSql] = useState(query.sql_query);
  const [parameters, setParameters] = useState(query.parameters || {});
  const [isExecuting, setIsExecuting] = useState(false);
  const [results, setResults] = useState(null);
  
  const executeQuery = async () => {
    setIsExecuting(true);
    
    try {
      // Create temporary workflow for execution
      const tempWorkflow = {
        sql_query: sql,
        parameters: parameters
      };
      
      const execution = await workflowService.executeTemporary(tempWorkflow);
      setResults(execution.results);
      onQueryExecute(execution.results);
      
    } catch (error) {
      console.error('Query execution failed:', error);
    } finally {
      setIsExecuting(false);
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Query Explanation */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-2">Query Explanation</h4>
        <p className="text-blue-800">{query.explanation}</p>
      </div>
      
      {/* SQL Editor */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          SQL Query
        </label>
        <SQLEditor
          value={sql}
          onChange={setSql}
          height="300px"
        />
      </div>
      
      {/* Parameters */}
      {Object.keys(parameters).length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Parameters
          </label>
          <ParameterForm
            parameters={Object.keys(parameters)}
            values={parameters}
            onChange={setParameters}
          />
        </div>
      )}
      
      {/* Execute Button */}
      <button
        onClick={executeQuery}
        disabled={isExecuting}
        className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
      >
        {isExecuting ? 'Executing...' : 'Run Query'}
      </button>
      
      {/* Results */}
      {results && (
        <div>
          <h4 className="font-medium text-gray-900 mb-2">Results</h4>
          <ExecutionResults results={results} />
          
          {/* Expected vs Actual Comparison */}
          {query.expected_result_description && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h5 className="font-medium text-gray-700 mb-2">Expected Results</h5>
              <p className="text-gray-600">{query.expected_result_description}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

## Content Creation Tools

### Markdown Processing
```typescript
// Process markdown content with AMC-specific enhancements
const processGuideContent = (markdown: string) => {
  return markdown
    // Highlight AMC table names
    .replace(/`([a-z_]+_data|[a-z_]+_events)`/g, '<code class="amc-table">$1</code>')
    // Highlight SQL keywords
    .replace(/\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY)\b/g, '<strong class="sql-keyword">$1</strong>')
    // Add parameter highlighting
    .replace(/\{\{([^}]+)\}\}/g, '<span class="parameter">{{$1}}</span>');
};
```

### Guide Templates
```python
# Pre-built guide templates for common use cases
GUIDE_TEMPLATES = {
    'attribution_analysis': {
        'title': 'Attribution Analysis with AMC',
        'description': 'Learn to analyze cross-channel attribution using AMC data',
        'sections': [
            {
                'title': 'Understanding Attribution Models',
                'content': '# Attribution Models\n\nAttribution models help...',
                'section_type': 'CONCEPT'
            },
            {
                'title': 'Building Attribution Queries',
                'content': '# Query Construction\n\nLet\'s build a query...',
                'section_type': 'HANDS_ON',
                'has_query': True
            }
        ]
    }
}
```

## Analytics and Insights

### Guide Performance Tracking
```python
async def get_guide_analytics(self, guide_id: str) -> dict:
    """Get analytics for guide performance"""
    
    # Basic metrics
    guide_stats = self.db.table('build_guides')\
        .select('completion_count, favorite_count')\
        .eq('id', guide_id)\
        .execute()
    
    # User progress distribution
    progress_distribution = self.db.rpc('get_guide_progress_distribution', {
        'guide_id': guide_id
    }).execute()
    
    # Time-to-completion analysis
    completion_times = self.db.table('user_guide_progress')\
        .select('started_at, completed_at')\
        .eq('guide_id', guide_id)\
        .eq('status', 'COMPLETED')\
        .execute()
    
    # Section difficulty analysis (where users get stuck)
    section_analytics = self.db.rpc('analyze_section_completion', {
        'guide_id': guide_id
    }).execute()
    
    return {
        'basic_stats': guide_stats.data[0] if guide_stats.data else {},
        'progress_distribution': progress_distribution.data,
        'completion_times': completion_times.data,
        'section_analytics': section_analytics.data
    }
```

## Testing and Quality Assurance

### Content Validation
```python
def validate_guide_content(guide_data: dict) -> List[str]:
    """Validate guide content for completeness and quality"""
    errors = []
    
    # Check required fields
    required_fields = ['title', 'description', 'category', 'sections']
    for field in required_fields:
        if not guide_data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate sections
    sections = guide_data.get('sections', [])
    if len(sections) < 2:
        errors.append("Guide must have at least 2 sections")
    
    for i, section in enumerate(sections):
        if not section.get('title'):
            errors.append(f"Section {i+1} missing title")
        
        if not section.get('content'):
            errors.append(f"Section {i+1} missing content")
        
        # Validate queries if present
        if section.get('has_query') and not section.get('query'):
            errors.append(f"Section {i+1} marked as having query but no query provided")
    
    return errors
```