"""AI Service Foundation - Core AI integration for RecomAMP"""

import os
import json
import hashlib
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

# AI Provider imports
try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

import tiktoken
from ..core.logger_simple import get_logger
from ..core.supabase_client import SupabaseManager

logger = get_logger(__name__)


class AIProvider(Enum):
    """Available AI providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AIServiceError(Exception):
    """Base exception for AI service errors"""
    pass


class RateLimitError(AIServiceError):
    """Exception raised when rate limit is exceeded"""
    pass


class TokenLimitError(AIServiceError):
    """Exception raised when token limit is exceeded"""
    pass


@dataclass
class AIResponse:
    """Standard response from AI providers"""
    content: str
    tokens_used: int
    provider: AIProvider
    model: str = ""
    cached: bool = False
    fallback_used: bool = False
    processing_time_ms: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AIService:
    """
    Core AI Service for RecomAMP

    Provides unified interface for multiple AI providers with:
    - Automatic fallback between providers
    - Rate limiting and token management
    - Response caching
    - Usage tracking and cost management
    - Retry logic for transient failures
    """

    def __init__(self):
        """Initialize AI service with provider clients and configuration"""
        # Get API keys from environment
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

        # Validate at least one provider is available
        if not self.openai_api_key and not self.anthropic_api_key:
            raise AIServiceError(
                "No AI API keys configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY"
            )

        # Initialize provider clients
        self.openai_client = None
        self.anthropic_client = None

        if self.openai_api_key and OPENAI_AVAILABLE:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized")

        if self.anthropic_api_key and ANTHROPIC_AVAILABLE:
            self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_api_key)
            logger.info("Anthropic client initialized")

        # Set primary and fallback providers
        self.primary_provider = (
            AIProvider.OPENAI if self.openai_client
            else AIProvider.ANTHROPIC
        )
        self.fallback_provider = (
            AIProvider.ANTHROPIC if self.primary_provider == AIProvider.OPENAI and self.anthropic_client
            else AIProvider.OPENAI if self.openai_client
            else None
        )

        # Configuration
        self.models = {
            AIProvider.OPENAI: {
                'default': 'gpt-4-turbo-preview',
                'fast': 'gpt-3.5-turbo',
                'vision': 'gpt-4-vision-preview'
            },
            AIProvider.ANTHROPIC: {
                'default': 'claude-3-opus-20240229',
                'fast': 'claude-3-sonnet-20240229',
                'vision': 'claude-3-opus-20240229'
            }
        }

        # Rate limiting configuration
        self.rate_limit_per_minute = int(os.getenv('AI_RATE_LIMIT_PER_MINUTE', '20'))
        self.request_timestamps = []
        self.request_count = 0
        self.rate_limit_reset_time = datetime.now()

        # Token limits
        self.max_tokens_per_request = int(os.getenv('AI_MAX_TOKENS_PER_REQUEST', '4000'))
        self.max_context_tokens = 8000

        # Response cache
        self.response_cache = {}
        self.cache_ttl_seconds = int(os.getenv('AI_CACHE_TTL_SECONDS', '3600'))

        # Usage tracking
        self.db = SupabaseManager.get_client(use_service_role=True)
        self.total_tokens_used = 0
        self.total_requests = 0

        # Token encoding for counting
        try:
            self.encoder = tiktoken.encoding_for_model("gpt-4")
        except:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def _validate_api_key(self, key: Optional[str]) -> bool:
        """Validate API key format"""
        if not key or len(key) < 10:
            return False
        return True

    def get_model(self, provider: AIProvider, task_type: str = 'default') -> str:
        """Get appropriate model for provider and task type"""
        return self.models.get(provider, {}).get(task_type, 'gpt-4-turbo-preview')

    async def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits"""
        now = datetime.now()

        # Reset rate limit counter if window has passed
        if now - self.rate_limit_reset_time > timedelta(minutes=1):
            self.request_count = 0
            self.rate_limit_reset_time = now
            self.request_timestamps = []

        # Check if we're at the limit
        if self.request_count >= self.rate_limit_per_minute:
            wait_time = 60 - (now - self.rate_limit_reset_time).seconds
            raise RateLimitError(
                f"Rate limit exceeded. Please wait {wait_time} seconds"
            )

        self.request_count += 1
        self.request_timestamps.append(now)
        return True

    async def _check_token_limit(self, prompt: str, max_tokens: int) -> bool:
        """Check if prompt is within token limits"""
        try:
            prompt_tokens = len(self.encoder.encode(prompt))
            total_expected = prompt_tokens + max_tokens

            if total_expected > self.max_context_tokens:
                raise TokenLimitError(
                    f"Request would use {total_expected} tokens, exceeding limit of {self.max_context_tokens}"
                )
            return True
        except Exception as e:
            if isinstance(e, TokenLimitError):
                raise
            # If encoding fails, estimate tokens
            estimated_tokens = len(prompt) // 4 + max_tokens
            if estimated_tokens > self.max_context_tokens:
                raise TokenLimitError("Estimated tokens exceed limit")
            return True

    def _generate_cache_key(self, prompt: str, provider: AIProvider, model: str) -> str:
        """Generate cache key for response caching"""
        content = f"{provider.value}:{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[AIResponse]:
        """Get cached response if available and not expired"""
        if cache_key not in self.response_cache:
            return None

        cached = self.response_cache[cache_key]
        if datetime.now() - cached['timestamp'] > timedelta(seconds=self.cache_ttl_seconds):
            del self.response_cache[cache_key]
            return None

        response = cached['response']
        response.cached = True
        return response

    def _cache_response(self, cache_key: str, response: AIResponse):
        """Cache a response with timestamp"""
        self.response_cache[cache_key] = {
            'response': response,
            'timestamp': datetime.now()
        }

    async def _track_usage(
        self,
        provider: AIProvider,
        tokens: int,
        model: str,
        user_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        operation_type: str = 'completion'
    ):
        """Track AI usage for analytics and cost management"""
        try:
            # Calculate estimated cost
            cost_per_1k_tokens = {
                'gpt-4-turbo-preview': 0.01,
                'gpt-3.5-turbo': 0.001,
                'claude-3-opus-20240229': 0.015,
                'claude-3-sonnet-20240229': 0.003
            }

            cost = (tokens / 1000) * cost_per_1k_tokens.get(model, 0.01)

            # Store in database
            self.db.table('ai_usage_tracking').insert({
                'user_id': user_id,
                'execution_id': execution_id,
                'service_type': provider.value,
                'operation_type': operation_type,
                'tokens_used': tokens,
                'cost_usd': cost,
                'model': model,
                'created_at': datetime.now().isoformat()
            }).execute()

            # Update totals
            self.total_tokens_used += tokens
            self.total_requests += 1

        except Exception as e:
            logger.error(f"Failed to track AI usage: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException))
    )
    async def _openai_completion(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None
    ) -> AIResponse:
        """Execute OpenAI completion with retry logic"""
        if not self.openai_client:
            raise AIServiceError("OpenAI client not initialized")

        start_time = datetime.now()

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            content = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0

            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return AIResponse(
                content=content,
                tokens_used=tokens,
                provider=AIProvider.OPENAI,
                model=model,
                processing_time_ms=processing_time,
                metadata={
                    'finish_reason': response.choices[0].finish_reason,
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'completion_tokens': response.usage.completion_tokens if response.usage else 0
                }
            )

        except Exception as e:
            logger.error(f"OpenAI completion error: {e}")
            if "network" in str(e).lower():
                raise httpx.NetworkError(f"Network error: {e}")
            raise AIServiceError(f"OpenAI API error: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException))
    )
    async def _anthropic_completion(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None
    ) -> AIResponse:
        """Execute Anthropic completion with retry logic"""
        if not self.anthropic_client:
            raise AIServiceError("Anthropic client not initialized")

        start_time = datetime.now()

        try:
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            response = await self.anthropic_client.messages.create(**kwargs)

            content = response.content[0].text if response.content else ""
            tokens = (response.usage.input_tokens + response.usage.output_tokens
                     if response.usage else 0)

            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return AIResponse(
                content=content,
                tokens_used=tokens,
                provider=AIProvider.ANTHROPIC,
                model=model,
                processing_time_ms=processing_time,
                metadata={
                    'input_tokens': response.usage.input_tokens if response.usage else 0,
                    'output_tokens': response.usage.output_tokens if response.usage else 0
                }
            )

        except Exception as e:
            logger.error(f"Anthropic completion error: {e}")
            if "network" in str(e).lower():
                raise httpx.NetworkError(f"Network error: {e}")
            raise AIServiceError(f"Anthropic API error: {e}")

    async def complete(
        self,
        prompt: str,
        provider: Optional[AIProvider] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
        user_id: Optional[str] = None,
        use_cache: bool = True
    ) -> AIResponse:
        """
        Execute AI completion with specified or default provider

        Args:
            prompt: The prompt to send to the AI
            provider: AI provider to use (defaults to primary)
            model: Model to use (defaults to provider's default)
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation
            system_prompt: System prompt to set context
            user_id: User ID for usage tracking
            use_cache: Whether to use cached responses

        Returns:
            AIResponse with content and metadata
        """
        # Check rate limit
        await self._check_rate_limit()

        # Use primary provider if not specified
        if provider is None:
            provider = self.primary_provider

        # Get model if not specified
        if model is None:
            model = self.get_model(provider, 'default')

        # Check token limits
        await self._check_token_limit(prompt, max_tokens)

        # Check cache
        cache_key = self._generate_cache_key(prompt, provider, model)
        if use_cache:
            cached = self._get_cached_response(cache_key)
            if cached:
                logger.debug(f"Using cached response for {cache_key[:8]}...")
                return cached

        # Execute completion based on provider
        try:
            if provider == AIProvider.OPENAI:
                response = await self._openai_completion(
                    prompt, model, max_tokens, temperature, system_prompt
                )
            elif provider == AIProvider.ANTHROPIC:
                response = await self._anthropic_completion(
                    prompt, model, max_tokens, temperature, system_prompt
                )
            else:
                raise AIServiceError(f"Unsupported provider: {provider}")

            # Track usage
            await self._track_usage(
                provider, response.tokens_used, model, user_id
            )

            # Cache response
            if use_cache:
                self._cache_response(cache_key, response)

            return response

        except Exception as e:
            logger.error(f"Completion error with {provider.value}: {e}")
            raise

    async def complete_with_fallback(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
        user_id: Optional[str] = None,
        use_cache: bool = True
    ) -> AIResponse:
        """
        Execute AI completion with automatic fallback to secondary provider

        This method tries the primary provider first, and falls back to
        the secondary provider if the primary fails.
        """
        try:
            # Try primary provider
            response = await self.complete(
                prompt=prompt,
                provider=self.primary_provider,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
                user_id=user_id,
                use_cache=use_cache
            )
            return response

        except Exception as primary_error:
            logger.warning(
                f"Primary provider {self.primary_provider.value} failed: {primary_error}"
            )

            # Try fallback provider if available
            if self.fallback_provider:
                try:
                    logger.info(f"Attempting fallback to {self.fallback_provider.value}")
                    response = await self.complete(
                        prompt=prompt,
                        provider=self.fallback_provider,
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system_prompt=system_prompt,
                        user_id=user_id,
                        use_cache=use_cache
                    )
                    response.fallback_used = True
                    return response

                except Exception as fallback_error:
                    logger.error(
                        f"Fallback provider {self.fallback_provider.value} also failed: {fallback_error}"
                    )
                    raise AIServiceError(
                        f"All AI providers failed. Primary: {primary_error}, Fallback: {fallback_error}"
                    )
            else:
                raise AIServiceError(f"Primary provider failed and no fallback available: {primary_error}")

    def _reset_rate_limit(self):
        """Reset rate limit counters (for testing)"""
        self.request_count = 0
        self.rate_limit_reset_time = datetime.now()
        self.request_timestamps = []

    async def get_usage_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get AI usage statistics"""
        try:
            query = self.db.table('ai_usage_tracking').select('*')

            if user_id:
                query = query.eq('user_id', user_id)

            # Get last 30 days
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            query = query.gte('created_at', thirty_days_ago)

            result = query.execute()

            if not result.data:
                return {
                    'total_requests': 0,
                    'total_tokens': 0,
                    'total_cost': 0,
                    'by_provider': {},
                    'by_operation': {}
                }

            # Aggregate statistics
            stats = {
                'total_requests': len(result.data),
                'total_tokens': sum(r['tokens_used'] for r in result.data),
                'total_cost': sum(r.get('cost_usd', 0) for r in result.data),
                'by_provider': {},
                'by_operation': {}
            }

            # Group by provider
            for record in result.data:
                provider = record['service_type']
                if provider not in stats['by_provider']:
                    stats['by_provider'][provider] = {
                        'requests': 0,
                        'tokens': 0,
                        'cost': 0
                    }
                stats['by_provider'][provider]['requests'] += 1
                stats['by_provider'][provider]['tokens'] += record['tokens_used']
                stats['by_provider'][provider]['cost'] += record.get('cost_usd', 0)

            # Group by operation
            for record in result.data:
                operation = record.get('operation_type', 'unknown')
                if operation not in stats['by_operation']:
                    stats['by_operation'][operation] = {
                        'requests': 0,
                        'tokens': 0
                    }
                stats['by_operation'][operation]['requests'] += 1
                stats['by_operation'][operation]['tokens'] += record['tokens_used']

            return stats

        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {
                'error': str(e),
                'total_requests': 0,
                'total_tokens': 0,
                'total_cost': 0
            }


# Export singleton instance
ai_service = AIService()