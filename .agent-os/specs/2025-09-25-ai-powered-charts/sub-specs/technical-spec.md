# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-25-ai-powered-charts/spec.md

> Created: 2025-09-25
> Version: 1.0.0

## Technical Requirements

### Backend Implementation
- **AI Service Layer**: New `ai_insights_service.py` extending existing `data_analysis_service.py`
- **LLM Integration**: Anthropic Claude Opus 4.1 primary, OpenAI GPT-4 fallback
- **Statistical Analysis**: NumPy/SciPy for trend detection and anomaly identification
- **API Endpoints**: New `/api/ai-insights/` router with chart, insights, and chat endpoints
- **Database Schema**: 4 new tables for insights cache, chat history, usage tracking
- **Caching Strategy**: Redis for AI responses (TTL: 3600s), Supabase for persistent storage
- **Rate Limiting**: 20 requests/minute per user for cost management

### Frontend Implementation
- **Component Architecture**: New AI components in `frontend/src/components/ai/`
- **State Management**: TanStack Query with 5-minute stale time for AI data
- **UI Integration**: Enhanced tabs in `AMCExecutionDetail.tsx` for AI features
- **Chart Rendering**: Extend existing Recharts with AI configuration
- **Real-time Updates**: WebSocket for chat responses, polling for insight generation
- **Progressive Enhancement**: Core functionality works without AI features

### Performance Requirements
- Chart recommendations: <3 seconds for up to 10,000 rows
- Insight generation: <10 seconds for complex analysis
- Chat responses: <5 seconds for simple queries
- Concurrent users: Support 50 simultaneous AI analyses
- Data sampling: Representative sampling for datasets >10,000 rows

### Integration Points
- **Authentication**: Uses existing `get_current_user` from auth system
- **Data Access**: Respects existing user permissions and dashboard access
- **Error Handling**: Follows patterns from `amc_executions.py`
- **Logging**: Integrates with existing logger_simple.py
- **Testing**: Extends existing pytest and Vitest test suites

## Approach

The implementation follows a layered architecture approach with AI services sitting above the existing data layer. The system uses a multi-LLM strategy for reliability and cost optimization, with Claude Opus for complex analysis and GPT-4 as fallback. Statistical analysis uses proven Python libraries for trend detection and anomaly identification.

## External Dependencies

### Required Libraries
- **anthropic>=0.25.0** - Claude Opus 4.1 API integration
- **openai>=1.0.0** - GPT-4 fallback option
- **tiktoken>=0.5.0** - Token counting for cost management
- **scikit-learn>=1.3.0** - Statistical analysis algorithms
- **scipy>=1.10.0** - Advanced statistical functions
- **reportlab>=4.0.0** - Enhanced PDF generation

**Justification**: These libraries provide essential AI/ML capabilities not available in the existing stack. Anthropic and OpenAI provide state-of-the-art language models for natural language generation. Statistical libraries enable sophisticated data analysis beyond basic aggregations.

### Frontend Dependencies
- **jspdf@^2.5.1** - Client-side PDF generation
- **html2canvas@^1.4.1** - Chart-to-image conversion for PDFs
- **react-markdown@^10.1.0** - Rendering AI-generated markdown content
- **framer-motion@^10.16.0** - Smooth animations for AI interactions

**Justification**: These enhance the existing React setup with AI-specific visualization and export capabilities while maintaining consistency with the current tech stack.