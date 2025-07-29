-- Supabase Database Functions for Amazon AMC Manager

-- Function to get campaigns by ASINs
CREATE OR REPLACE FUNCTION get_campaigns_by_asins(
    user_id_param UUID,
    asin_list TEXT[]
)
RETURNS TABLE (
    campaign_id BIGINT,
    campaign_name TEXT,
    brand_tag TEXT,
    matching_asins TEXT[],
    campaign_type TEXT,
    marketplace_id TEXT
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cm.campaign_id,
        cm.campaign_name,
        cm.brand_tag,
        ARRAY(
            SELECT jsonb_array_elements_text(cm.asins) 
            INTERSECT 
            SELECT unnest(asin_list)
        ) as matching_asins,
        cm.campaign_type,
        cm.marketplace_id
    FROM campaign_mappings cm
    WHERE cm.user_id = user_id_param
        AND cm.asins::jsonb ?| asin_list;
END;
$$;

-- Function to analyze brand campaigns
CREATE OR REPLACE FUNCTION analyze_brand_campaigns(
    brand_tag_param TEXT,
    start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW() - INTERVAL '30 days',
    end_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
RETURNS TABLE (
    total_campaigns BIGINT,
    campaign_types JSONB,
    marketplace_distribution JSONB,
    unique_asins INTEGER,
    recent_executions INTEGER
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    WITH campaign_stats AS (
        SELECT 
            COUNT(DISTINCT cm.campaign_id) as total_campaigns,
            jsonb_object_agg(
                COALESCE(cm.campaign_type, 'unknown'), 
                COUNT(DISTINCT cm.campaign_id)
            ) as campaign_types,
            jsonb_object_agg(
                cm.marketplace_id, 
                COUNT(DISTINCT cm.campaign_id)
            ) as marketplace_distribution,
            COUNT(DISTINCT jsonb_array_elements_text(cm.asins)) as unique_asins
        FROM campaign_mappings cm
        WHERE cm.brand_tag = brand_tag_param
            AND cm.user_id = auth.uid()
        GROUP BY cm.brand_tag
    ),
    execution_stats AS (
        SELECT COUNT(*) as recent_executions
        FROM workflow_executions we
        JOIN workflows w ON we.workflow_id = w.id
        WHERE w.user_id = auth.uid()
            AND we.created_at BETWEEN start_date AND end_date
            AND we.execution_parameters->>'brand_tag' = brand_tag_param
    )
    SELECT 
        cs.total_campaigns,
        cs.campaign_types,
        cs.marketplace_distribution,
        cs.unique_asins,
        es.recent_executions
    FROM campaign_stats cs
    CROSS JOIN execution_stats es;
END;
$$;

-- Function to auto-tag campaigns based on patterns
CREATE OR REPLACE FUNCTION auto_tag_campaign(
    campaign_name_param TEXT,
    user_id_param UUID
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    brand_tag_result TEXT;
    pattern TEXT;
    brand_record RECORD;
BEGIN
    -- Check each brand configuration for matching patterns
    FOR brand_record IN 
        SELECT brand_tag, campaign_name_patterns
        FROM brand_configurations
        WHERE owner_user_id = user_id_param
           OR shared_with_users::jsonb ? user_id_param::text
    LOOP
        -- Check each pattern in the brand's patterns array
        FOR pattern IN SELECT jsonb_array_elements_text(brand_record.campaign_name_patterns)
        LOOP
            IF campaign_name_param ~* pattern THEN
                RETURN brand_record.brand_tag;
            END IF;
        END LOOP;
    END LOOP;
    
    RETURN NULL;
END;
$$;

-- Function to aggregate ASINs by brand
CREATE OR REPLACE FUNCTION get_brand_asin_summary(
    user_id_param UUID
)
RETURNS TABLE (
    brand_tag TEXT,
    brand_name TEXT,
    total_asins INTEGER,
    primary_asins_count INTEGER,
    campaigns_using_brand INTEGER,
    last_updated TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        bc.brand_tag,
        bc.brand_name,
        jsonb_array_length(bc.all_asins) as total_asins,
        jsonb_array_length(bc.primary_asins) as primary_asins_count,
        COUNT(DISTINCT cm.campaign_id)::INTEGER as campaigns_using_brand,
        MAX(cm.updated_at) as last_updated
    FROM brand_configurations bc
    LEFT JOIN campaign_mappings cm ON bc.brand_tag = cm.brand_tag
    WHERE bc.owner_user_id = user_id_param
       OR bc.shared_with_users::jsonb ? user_id_param::text
    GROUP BY bc.brand_tag, bc.brand_name, bc.all_asins, bc.primary_asins;
END;
$$;

-- Function to validate AMC instance access
CREATE OR REPLACE FUNCTION validate_instance_access(
    instance_id_param UUID,
    user_id_param UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 
        FROM amc_instances ai
        JOIN amc_accounts aa ON ai.account_id = aa.id
        WHERE ai.id = instance_id_param
          AND aa.user_id = user_id_param
          AND ai.status = 'active'
          AND aa.status = 'active'
    );
END;
$$;

-- Function to get workflow execution statistics
CREATE OR REPLACE FUNCTION get_workflow_execution_stats(
    workflow_id_param UUID,
    days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    total_executions BIGINT,
    successful_executions BIGINT,
    failed_executions BIGINT,
    average_duration_seconds NUMERIC,
    average_row_count NUMERIC,
    status_distribution JSONB
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_executions,
        COUNT(*) FILTER (WHERE status = 'completed') as successful_executions,
        COUNT(*) FILTER (WHERE status = 'failed') as failed_executions,
        AVG(duration_seconds) as average_duration_seconds,
        AVG(row_count) as average_row_count,
        jsonb_object_agg(status, count) as status_distribution
    FROM (
        SELECT 
            we.status,
            we.duration_seconds,
            we.row_count,
            COUNT(*) as count
        FROM workflow_executions we
        WHERE we.workflow_id = workflow_id_param
          AND we.created_at >= NOW() - INTERVAL '1 day' * days_back
        GROUP BY we.status, we.duration_seconds, we.row_count
    ) stats
    GROUP BY status;
END;
$$;

-- Function to search campaigns across multiple fields
CREATE OR REPLACE FUNCTION search_campaigns(
    search_term TEXT,
    user_id_param UUID,
    limit_param INTEGER DEFAULT 50
)
RETURNS TABLE (
    campaign_id BIGINT,
    campaign_name TEXT,
    brand_tag TEXT,
    campaign_type TEXT,
    marketplace_id TEXT,
    relevance_score NUMERIC
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cm.campaign_id,
        cm.campaign_name,
        cm.brand_tag,
        cm.campaign_type,
        cm.marketplace_id,
        (
            CASE WHEN cm.campaign_name ILIKE '%' || search_term || '%' THEN 3
                 WHEN cm.brand_tag ILIKE '%' || search_term || '%' THEN 2
                 WHEN cm.tags::text ILIKE '%' || search_term || '%' THEN 1
                 ELSE 0
            END +
            CASE WHEN cm.campaign_id::text = search_term THEN 5 ELSE 0 END
        )::NUMERIC as relevance_score
    FROM campaign_mappings cm
    WHERE cm.user_id = user_id_param
      AND (
          cm.campaign_name ILIKE '%' || search_term || '%'
          OR cm.brand_tag ILIKE '%' || search_term || '%'
          OR cm.campaign_id::text = search_term
          OR cm.tags::text ILIKE '%' || search_term || '%'
          OR EXISTS (
              SELECT 1 
              FROM jsonb_array_elements_text(cm.asins) AS asin
              WHERE asin ILIKE '%' || search_term || '%'
          )
      )
    ORDER BY relevance_score DESC, cm.campaign_name
    LIMIT limit_param;
END;
$$;