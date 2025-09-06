"""AI Insights Service - Generates business insights using LLM integration"""

import os
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, date
from enum import Enum
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from ..core.logger_simple import get_logger
from .reporting_database_service import reporting_db_service
from .dashboard_data_service import dashboard_data_service
from .data_aggregation_service import data_aggregation_service
from .db_service import db_service

logger = get_logger(__name__)


class InsightType(Enum):
    """Types of insights that can be generated"""
    TREND_ANALYSIS = "trend_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    OPTIMIZATION = "optimization"
    COMPARISON = "comparison"
    FORECAST = "forecast"
    SUMMARY = "summary"


class AIInsightsService:
    """Service for generating AI-powered business insights"""
    
    def __init__(self):
        self.db = db_service
        self.reporting_db = reporting_db_service
        self.dashboard_service = dashboard_data_service
        self.aggregation_service = data_aggregation_service
        
        # AI Configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.default_model = 'gpt-4-turbo-preview'
        self.fallback_model = 'claude-3-sonnet'
        
        # Conversation context management
        self.conversation_contexts = {}  # user_id -> context
        self.context_max_tokens = 4000
        self.context_max_messages = 10
        
        # Prompt templates
        self.prompt_templates = self._initialize_prompt_templates()
    
    def _initialize_prompt_templates(self) -> Dict[str, str]:
        """Initialize prompt templates for different insight types"""
        return {
            'trend_analysis': """
Analyze the following AMC advertising metrics data and identify key trends:

Data Context:
{data_context}

Please provide:
1. Main trend direction (improving, declining, stable)
2. Key inflection points or changes
3. Potential causes for observed trends
4. Recommended actions based on trends

Format your response in clear, business-friendly language.
""",
            
            'anomaly_detection': """
Review the following AMC advertising data for anomalies or unusual patterns:

Data Context:
{data_context}

Identify:
1. Any significant anomalies or outliers
2. Potential causes for these anomalies
3. Whether they represent opportunities or risks
4. Recommended investigation or action items

Be specific about dates and metrics affected.
""",
            
            'optimization': """
Based on the following AMC campaign performance data, provide optimization recommendations:

Data Context:
{data_context}

Provide:
1. Top 3 optimization opportunities
2. Specific metrics that need improvement
3. Actionable recommendations with expected impact
4. Priority order for implementation

Focus on practical, implementable suggestions.
""",
            
            'comparison': """
Compare the following periods/segments in the AMC data:

Data Context:
{data_context}

Analyze:
1. Key differences between periods/segments
2. Performance improvements or declines
3. Factors contributing to changes
4. Lessons learned and recommendations

Provide specific percentage changes where applicable.
""",
            
            'forecast': """
Based on historical AMC advertising data, provide a forecast analysis:

Data Context:
{data_context}

Include:
1. Expected performance trends for next period
2. Key assumptions and risk factors
3. Confidence level in predictions
4. Recommendations to achieve or exceed forecast

Be realistic and highlight any uncertainties.
""",
            
            'summary': """
Provide an executive summary of the AMC advertising performance:

Data Context:
{data_context}

Summarize:
1. Overall performance status
2. Key achievements and successes
3. Main challenges or concerns
4. Top 3 priorities for next period

Keep the summary concise and action-oriented.
"""
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_insight(
        self,
        user_id: str,
        dashboard_id: Optional[str],
        query_text: str,
        data_context: Dict[str, Any],
        insight_type: InsightType = InsightType.SUMMARY
    ) -> Dict[str, Any]:
        """
        Generate an AI insight based on query and data context
        
        Args:
            user_id: User ID requesting the insight
            dashboard_id: Optional dashboard ID for context
            query_text: Natural language query from user
            data_context: Relevant data and metrics for analysis
            insight_type: Type of insight to generate
            
        Returns:
            Generated insight with metadata
        """
        try:
            # Prepare context for AI
            context_str = self._prepare_data_context(data_context)
            
            # Get or create conversation context
            conversation_context = self._get_conversation_context(user_id)
            
            # Build prompt
            prompt = self._build_prompt(
                query_text,
                context_str,
                insight_type,
                conversation_context
            )
            
            # Generate insight using AI
            response_text, confidence_score = await self._call_ai_api(
                prompt,
                user_id
            )
            
            # Extract metrics referenced in the response
            related_metrics = self._extract_related_metrics(
                response_text,
                data_context
            )
            
            # Store insight in database
            insight_data = {
                'user_id': user_id,
                'dashboard_id': dashboard_id,
                'query_text': query_text,
                'response_text': response_text,
                'data_context': data_context,
                'confidence_score': confidence_score,
                'insight_type': insight_type.value,
                'related_metrics': related_metrics
            }
            
            stored_insight = self.reporting_db.create_insight(insight_data)
            
            # Update conversation context
            self._update_conversation_context(
                user_id,
                query_text,
                response_text
            )
            
            return {
                'insight_id': stored_insight['insight_id'] if stored_insight else None,
                'response': response_text,
                'confidence': confidence_score,
                'type': insight_type.value,
                'related_metrics': related_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating insight: {e}")
            return {
                'error': str(e),
                'response': "I encountered an error while analyzing the data. Please try again.",
                'confidence': 0
            }
    
    def _prepare_data_context(self, data_context: Dict[str, Any]) -> str:
        """Prepare data context for AI prompt"""
        try:
            # Extract key information from data context
            context_parts = []
            
            # Add metrics summary
            if 'metrics' in data_context:
                metrics = data_context['metrics']
                context_parts.append("Current Metrics:")
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        context_parts.append(f"  - {key}: {value:,.2f}")
            
            # Add time period
            if 'date_range' in data_context:
                date_range = data_context['date_range']
                context_parts.append(f"\nTime Period: {date_range[0]} to {date_range[1]}")
            
            # Add trends if available
            if 'trends' in data_context:
                context_parts.append("\nTrends:")
                for trend in data_context['trends'][:5]:  # Limit to 5 trends
                    context_parts.append(f"  - {trend}")
            
            # Add dimensions
            if 'dimensions' in data_context:
                dims = data_context['dimensions']
                if 'total_campaigns' in dims:
                    context_parts.append(f"\nCampaigns: {dims['total_campaigns']}")
                if 'total_asins' in dims:
                    context_parts.append(f"ASINs: {dims['total_asins']}")
            
            # Add comparisons if available
            if 'comparison' in data_context:
                comp = data_context['comparison']
                context_parts.append("\nPeriod-over-Period Changes:")
                for key, value in comp.items():
                    if isinstance(value, (int, float)):
                        context_parts.append(f"  - {key}: {value:+.1f}%")
            
            return '\n'.join(context_parts)
            
        except Exception as e:
            logger.error(f"Error preparing data context: {e}")
            return str(data_context)[:2000]  # Fallback to truncated raw context
    
    def _build_prompt(
        self,
        query_text: str,
        context_str: str,
        insight_type: InsightType,
        conversation_context: List[Dict[str, str]]
    ) -> str:
        """Build the complete prompt for AI"""
        
        # Get template for insight type
        template = self.prompt_templates.get(
            insight_type.value,
            self.prompt_templates['summary']
        )
        
        # Build system context
        system_prompt = """You are an expert Amazon Advertising analyst specializing in AMC (Amazon Marketing Cloud) data interpretation. 
You provide clear, actionable insights based on advertising performance metrics.
Focus on practical recommendations that can improve campaign performance.
Use specific numbers and percentages when available.
Keep responses concise but comprehensive."""
        
        # Add conversation context if available
        context_prompt = ""
        if conversation_context:
            context_prompt = "\nPrevious conversation context:\n"
            for msg in conversation_context[-3:]:  # Last 3 exchanges
                context_prompt += f"User: {msg['query']}\nAssistant: {msg['response'][:200]}...\n"
        
        # Combine all parts
        full_prompt = f"{system_prompt}\n\n{context_prompt}\n\nUser Query: {query_text}\n\n{template.format(data_context=context_str)}"
        
        return full_prompt
    
    async def _call_ai_api(
        self,
        prompt: str,
        user_id: str
    ) -> Tuple[str, float]:
        """
        Call AI API (OpenAI or Anthropic) to generate insight
        
        Returns:
            Tuple of (response_text, confidence_score)
        """
        try:
            # Try OpenAI first if available
            if self.openai_api_key:
                return await self._call_openai(prompt)
            
            # Fallback to Anthropic
            elif self.anthropic_api_key:
                return await self._call_anthropic(prompt)
            
            # No AI service available - use mock response
            else:
                logger.warning("No AI API keys configured, using mock response")
                return self._generate_mock_response(prompt)
                
        except Exception as e:
            logger.error(f"Error calling AI API: {e}")
            # Return a generic error response
            return (
                "I'm unable to generate insights at the moment. Please check your data and try again.",
                0.0
            )
    
    async def _call_openai(self, prompt: str) -> Tuple[str, float]:
        """Call OpenAI API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {self.openai_api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': self.default_model,
                        'messages': [
                            {'role': 'system', 'content': 'You are an expert AMC data analyst.'},
                            {'role': 'user', 'content': prompt}
                        ],
                        'temperature': 0.7,
                        'max_tokens': 1000
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']
                    
                    # Calculate confidence based on model's response
                    confidence = 0.85  # Base confidence for GPT-4
                    
                    return content, confidence
                else:
                    logger.error(f"OpenAI API error: {response.status_code}")
                    raise Exception(f"OpenAI API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error calling OpenAI: {e}")
            raise
    
    async def _call_anthropic(self, prompt: str) -> Tuple[str, float]:
        """Call Anthropic Claude API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.anthropic.com/v1/messages',
                    headers={
                        'x-api-key': self.anthropic_api_key,
                        'anthropic-version': '2023-06-01',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': self.fallback_model,
                        'messages': [
                            {'role': 'user', 'content': prompt}
                        ],
                        'max_tokens': 1000,
                        'temperature': 0.7
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data['content'][0]['text']
                    
                    # Calculate confidence
                    confidence = 0.82  # Base confidence for Claude
                    
                    return content, confidence
                else:
                    logger.error(f"Anthropic API error: {response.status_code}")
                    raise Exception(f"Anthropic API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error calling Anthropic: {e}")
            raise
    
    def _generate_mock_response(self, prompt: str) -> Tuple[str, float]:
        """Generate a mock response when no AI service is available"""
        
        # Extract some context from the prompt
        if 'trend' in prompt.lower():
            response = """Based on the provided data, here are the key trends:

1. **Performance Trend**: The metrics show a generally stable pattern with minor fluctuations.
2. **Key Observation**: Recent periods show consistent performance across main KPIs.
3. **Recommendation**: Continue monitoring current strategies while testing small optimizations.

This is a simulated insight. Configure AI API keys for actual analysis."""
            
        elif 'optimization' in prompt.lower():
            response = """Optimization opportunities identified:

1. **Campaign Efficiency**: Consider reviewing underperforming campaigns for budget reallocation.
2. **Keyword Strategy**: Analyze search term reports for negative keyword opportunities.
3. **Bid Adjustments**: Test incremental bid changes on high-performing targets.

This is a simulated insight. Configure AI API keys for actual analysis."""
            
        else:
            response = """Summary of advertising performance:

- Overall metrics are within expected ranges
- No significant anomalies detected in the data
- Performance appears stable across key dimensions

This is a simulated insight. Configure AI API keys for detailed analysis."""
        
        return response, 0.5  # Low confidence for mock responses
    
    def _extract_related_metrics(
        self,
        response_text: str,
        data_context: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Extract metrics mentioned in the AI response"""
        
        related_metrics = {
            'primary': [],
            'secondary': []
        }
        
        # Common metric keywords to look for
        metric_keywords = {
            'impressions': ['impression', 'views', 'reach'],
            'clicks': ['click', 'ctr', 'click-through'],
            'conversions': ['conversion', 'cvr', 'orders'],
            'spend': ['spend', 'cost', 'budget'],
            'sales': ['sales', 'revenue'],
            'roas': ['roas', 'return on ad spend'],
            'acos': ['acos', 'advertising cost'],
            'cpc': ['cpc', 'cost per click'],
            'cpm': ['cpm', 'cost per thousand']
        }
        
        response_lower = response_text.lower()
        
        for metric, keywords in metric_keywords.items():
            for keyword in keywords:
                if keyword in response_lower:
                    if metric in data_context.get('metrics', {}):
                        related_metrics['primary'].append(metric)
                    else:
                        related_metrics['secondary'].append(metric)
                    break
        
        # Remove duplicates
        related_metrics['primary'] = list(set(related_metrics['primary']))
        related_metrics['secondary'] = list(set(related_metrics['secondary']))
        
        return related_metrics
    
    def _get_conversation_context(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation context for a user"""
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = []
        return self.conversation_contexts[user_id]
    
    def _update_conversation_context(
        self,
        user_id: str,
        query: str,
        response: str
    ) -> None:
        """Update conversation context with new exchange"""
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = []
        
        context = self.conversation_contexts[user_id]
        
        # Add new exchange
        context.append({
            'query': query[:500],  # Truncate long queries
            'response': response[:500],  # Truncate long responses
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only recent context
        if len(context) > self.context_max_messages:
            context = context[-self.context_max_messages:]
        
        self.conversation_contexts[user_id] = context
    
    async def get_suggested_questions(
        self,
        user_id: str,
        dashboard_id: Optional[str],
        current_data: Dict[str, Any]
    ) -> List[str]:
        """
        Generate suggested questions based on current data
        
        Args:
            user_id: User ID
            dashboard_id: Optional dashboard ID
            current_data: Current dashboard data context
            
        Returns:
            List of suggested questions
        """
        suggestions = []
        
        # Analyze current data for suggestion topics
        if 'metrics' in current_data:
            metrics = current_data['metrics']
            
            # ROAS-related questions
            if 'roas' in metrics:
                roas = metrics['roas']
                if roas < 2:
                    suggestions.append("How can I improve my ROAS above 2x?")
                elif roas > 4:
                    suggestions.append("What factors are driving my high ROAS performance?")
            
            # ACOS-related questions
            if 'acos' in metrics:
                acos = metrics['acos']
                if acos > 30:
                    suggestions.append("Why is my ACOS above 30% and how can I reduce it?")
            
            # CTR-related questions
            if 'ctr' in metrics:
                ctr = metrics['ctr']
                if ctr < 0.5:
                    suggestions.append("How can I improve my click-through rate?")
        
        # Time-based questions
        if 'date_range' in current_data:
            suggestions.append("How does this period compare to the previous period?")
            suggestions.append("What are the main trends over this timeframe?")
        
        # General optimization questions
        suggestions.extend([
            "What are my top optimization opportunities?",
            "Are there any anomalies I should investigate?",
            "What should be my focus for next week?"
        ])
        
        # Limit to 5 suggestions
        return suggestions[:5]
    
    async def analyze_anomalies(
        self,
        workflow_id: str,
        instance_id: str,
        date_range: Tuple[date, date],
        sensitivity: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in metrics data
        
        Args:
            workflow_id: Workflow UUID
            instance_id: Instance UUID
            date_range: Date range to analyze
            sensitivity: Standard deviations for anomaly threshold
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        try:
            # Get aggregated data
            aggregates = self.reporting_db.get_aggregates_for_dashboard(
                workflow_id, instance_id, 'weekly',
                date_range[0], date_range[1]
            )
            
            if len(aggregates) < 4:
                return []  # Need at least 4 data points
            
            # Analyze each metric
            metrics_to_analyze = ['impressions', 'clicks', 'spend', 'sales', 'roas', 'acos']
            
            for metric in metrics_to_analyze:
                values = []
                dates = []
                
                for agg in aggregates:
                    if metric in agg.get('metrics', {}):
                        values.append(agg['metrics'][metric])
                        dates.append(agg['data_date'])
                
                if len(values) < 4:
                    continue
                
                # Calculate statistics
                import statistics
                mean = statistics.mean(values)
                stdev = statistics.stdev(values)
                
                # Find anomalies
                for i, value in enumerate(values):
                    z_score = abs((value - mean) / stdev) if stdev > 0 else 0
                    
                    if z_score > sensitivity:
                        anomalies.append({
                            'metric': metric,
                            'date': dates[i],
                            'value': value,
                            'expected': mean,
                            'deviation': z_score,
                            'type': 'high' if value > mean else 'low'
                        })
            
            # Sort by deviation (most significant first)
            anomalies.sort(key=lambda x: x['deviation'], reverse=True)
            
            return anomalies[:10]  # Return top 10 anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing anomalies: {e}")
            return []
    
    def clear_conversation_context(self, user_id: str) -> None:
        """Clear conversation context for a user"""
        if user_id in self.conversation_contexts:
            del self.conversation_contexts[user_id]
            logger.info(f"Cleared conversation context for user {user_id}")


# Create singleton instance
ai_insights_service = AIInsightsService()