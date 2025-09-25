# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-09-25-ai-powered-charts/spec.md

> Created: 2025-09-25
> Version: 1.0.0

## Endpoints

### POST /api/ai-insights/executions/{instance_id}/{execution_id}/generate-charts

**Purpose:** Generate AI-powered chart recommendations for execution data
**Parameters:**
- instance_id (path): AMC instance identifier
- execution_id (path): Execution identifier
- data (body): Array of execution result data
- context (body): Dashboard and user context
**Response:** List of chart recommendations with confidence scores and reasoning
**Errors:** 400 (insufficient data), 429 (rate limit), 503 (AI service unavailable)

### POST /api/ai-insights/executions/{instance_id}/{execution_id}/chat

**Purpose:** Handle conversational queries about execution data
**Parameters:**
- instance_id (path): AMC instance identifier
- execution_id (path): Execution identifier
- question (body): Natural language question
- chat_history (body): Previous conversation context
**Response:** AI-generated answer with supporting data and follow-up suggestions
**Errors:** 400 (invalid question), 429 (rate limit), 503 (AI unavailable)

### GET /api/ai-insights/executions/{instance_id}/{execution_id}/insights

**Purpose:** Retrieve cached AI insights for an execution
**Parameters:**
- instance_id (path): AMC instance identifier
- execution_id (path): Execution identifier
**Response:** Cached insights with trends, anomalies, and recommendations
**Errors:** 404 (insights not found), 401 (unauthorized)

### POST /api/ai-insights/generate-insights

**Purpose:** Generate statistical insights from dashboard data
**Parameters:**
- dashboard_id (body): Dashboard identifier
- data (body): Dashboard data for analysis
- analysis_types (body): Types of analysis to perform
**Response:** Generated insights with confidence scores and visualizations
**Errors:** 400 (invalid data), 503 (service unavailable)

## Controllers

### AIInsightsController
- **generate_ai_charts()**: Orchestrates chart recommendation generation
- **chat_with_ai()**: Manages conversational AI interactions
- **get_cached_insights()**: Retrieves stored insights
- **generate_insights()**: Triggers insight generation pipeline

### Business Logic
- Data validation and sanitization before AI processing
- User permission checks for dashboard access
- Rate limiting enforcement per user/organization
- Cost tracking for AI API usage
- Fallback to rule-based recommendations if AI unavailable

### Error Handling
- Graceful degradation when AI services unavailable
- Clear error messages with retry guidance
- Automatic fallback to cached responses when possible
- Audit logging for all AI interactions

## Purpose

These API endpoints enable the AI-powered analytics features to integrate seamlessly with the existing AMC execution detail system, providing intelligent chart recommendations, automated insights discovery, and natural language data exploration while maintaining security, performance, and cost efficiency.