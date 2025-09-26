-- AI Service Database Schema
-- Migration: 14_ai_service_tables.sql
-- Description: Creates tables for AI service usage tracking, insights cache, and chat history

-- AI Usage Tracking Table
CREATE TABLE IF NOT EXISTS ai_usage_tracking (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    execution_id TEXT,
    service_type TEXT NOT NULL CHECK (service_type IN ('openai', 'anthropic')),
    operation_type TEXT NOT NULL DEFAULT 'completion',
    model TEXT,
    tokens_used INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6),
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes for performance
    INDEX idx_ai_usage_user_date (user_id, created_at DESC),
    INDEX idx_ai_usage_operation (operation_type, created_at DESC)
);

-- AI Insights Cache Table
CREATE TABLE IF NOT EXISTS ai_insights_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cache_key TEXT NOT NULL UNIQUE,
    execution_id TEXT,
    instance_id TEXT,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    cache_type TEXT NOT NULL CHECK (cache_type IN ('chart_config', 'insights', 'analysis', 'completion')),
    cache_data JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    INDEX idx_ai_cache_key (cache_key),
    INDEX idx_ai_cache_expiry (expires_at),
    INDEX idx_ai_cache_execution (execution_id, instance_id)
);

-- AI Chat History Table
CREATE TABLE IF NOT EXISTS ai_chat_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    execution_id TEXT,
    instance_id TEXT,
    message_role TEXT NOT NULL CHECK (message_role IN ('user', 'assistant', 'system')),
    message_content TEXT NOT NULL,
    message_metadata JSONB,
    tokens_used INTEGER,
    provider TEXT CHECK (provider IN ('openai', 'anthropic')),
    model TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    INDEX idx_ai_chat_conversation (conversation_id, created_at),
    INDEX idx_ai_chat_user (user_id, created_at DESC),
    INDEX idx_ai_chat_dashboard (dashboard_id, created_at DESC)
);

-- AI Chart Recommendations Table
CREATE TABLE IF NOT EXISTS ai_chart_recommendations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    widget_id UUID REFERENCES dashboard_widgets(id) ON DELETE CASCADE,
    execution_id TEXT,
    instance_id TEXT,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    recommended_chart_type TEXT NOT NULL,
    confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    reasoning TEXT NOT NULL,
    config_suggestions JSONB,
    user_action TEXT CHECK (user_action IN ('accepted', 'rejected', 'modified', NULL)),
    user_feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    INDEX idx_ai_recommendations_widget (widget_id, created_at DESC),
    INDEX idx_ai_recommendations_action (user_action, created_at DESC)
);

-- AI Generated Insights Table
CREATE TABLE IF NOT EXISTS ai_insights (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    widget_id UUID REFERENCES dashboard_widgets(id) ON DELETE CASCADE,
    execution_id TEXT,
    instance_id TEXT,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    insight_type TEXT NOT NULL CHECK (insight_type IN ('trend', 'anomaly', 'comparison', 'correlation', 'forecast', 'optimization', 'summary')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    supporting_data JSONB,
    recommendations TEXT[],
    visualization_config JSONB,
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    INDEX idx_ai_insights_dashboard (dashboard_id, created_at DESC),
    INDEX idx_ai_insights_widget (widget_id, created_at DESC),
    INDEX idx_ai_insights_type (insight_type, created_at DESC),
    INDEX idx_ai_insights_archived (is_archived, created_at DESC)
);

-- AI Performance Metrics Table
CREATE TABLE IF NOT EXISTS ai_performance_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    feature_type TEXT NOT NULL CHECK (feature_type IN ('chart_recommendation', 'insight_generation', 'chat', 'data_analysis', 'pdf_generation')),
    operation TEXT,
    response_time_ms INTEGER NOT NULL,
    tokens_used INTEGER,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    accuracy_score DECIMAL(3,2) CHECK (accuracy_score >= 0 AND accuracy_score <= 1),
    user_satisfaction INTEGER CHECK (user_satisfaction >= 1 AND user_satisfaction <= 5),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes for analytics
    INDEX idx_ai_metrics_feature (feature_type, created_at DESC),
    INDEX idx_ai_metrics_performance (response_time_ms, created_at DESC),
    INDEX idx_ai_metrics_success (success, created_at DESC)
);

-- AI Conversation Context Table (for maintaining chat context)
CREATE TABLE IF NOT EXISTS ai_conversation_context (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    context_data JSONB NOT NULL,
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours'),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    INDEX idx_ai_context_user (user_id, last_activity DESC),
    INDEX idx_ai_context_expiry (expires_at)
);

-- Row Level Security Policies
ALTER TABLE ai_usage_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_insights_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_chart_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_conversation_context ENABLE ROW LEVEL SECURITY;

-- RLS Policies for ai_usage_tracking
CREATE POLICY "Users can view their own usage" ON ai_usage_tracking
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert usage" ON ai_usage_tracking
    FOR INSERT WITH CHECK (true);

-- RLS Policies for ai_insights_cache
CREATE POLICY "Users can view their own cached insights" ON ai_insights_cache
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create cache entries" ON ai_insights_cache
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- RLS Policies for ai_chat_history
CREATE POLICY "Users can view their own chat history" ON ai_chat_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create chat messages" ON ai_chat_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- RLS Policies for ai_chart_recommendations
CREATE POLICY "Users can view recommendations for their widgets" ON ai_chart_recommendations
    FOR SELECT USING (
        widget_id IN (
            SELECT w.id FROM dashboard_widgets w
            JOIN dashboards d ON w.dashboard_id = d.id
            WHERE d.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update recommendation feedback" ON ai_chart_recommendations
    FOR UPDATE USING (
        widget_id IN (
            SELECT w.id FROM dashboard_widgets w
            JOIN dashboards d ON w.dashboard_id = d.id
            WHERE d.user_id = auth.uid()
        )
    );

-- RLS Policies for ai_insights
CREATE POLICY "Users can view insights for their dashboards" ON ai_insights
    FOR SELECT USING (
        dashboard_id IN (
            SELECT id FROM dashboards WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create insights" ON ai_insights
    FOR INSERT WITH CHECK (
        dashboard_id IN (
            SELECT id FROM dashboards WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their insights" ON ai_insights
    FOR UPDATE USING (
        dashboard_id IN (
            SELECT id FROM dashboards WHERE user_id = auth.uid()
        )
    );

-- RLS Policies for ai_conversation_context
CREATE POLICY "Users can manage their own conversation context" ON ai_conversation_context
    FOR ALL USING (auth.uid() = user_id);

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_ai_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM ai_insights_cache WHERE expires_at < NOW();
    DELETE FROM ai_conversation_context WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_ai_insights_cache_updated_at
    BEFORE UPDATE ON ai_insights_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_chart_recommendations_updated_at
    BEFORE UPDATE ON ai_chart_recommendations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_insights_updated_at
    BEFORE UPDATE ON ai_insights
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE ai_usage_tracking IS 'Tracks AI API usage for cost management and analytics';
COMMENT ON TABLE ai_insights_cache IS 'Caches AI-generated insights and analysis for performance';
COMMENT ON TABLE ai_chat_history IS 'Stores conversation history for AI chat interactions';
COMMENT ON TABLE ai_chart_recommendations IS 'Stores AI-generated chart type recommendations';
COMMENT ON TABLE ai_insights IS 'Stores AI-generated business insights and analysis';
COMMENT ON TABLE ai_performance_metrics IS 'Tracks performance metrics for AI features';
COMMENT ON TABLE ai_conversation_context IS 'Maintains conversation context for multi-turn AI chats';