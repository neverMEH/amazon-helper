-- Create optimized function for fetching brands with counts
-- This dramatically improves performance compared to fetching all campaigns

CREATE OR REPLACE FUNCTION get_campaign_brands_with_counts()
RETURNS TABLE (
    brand TEXT,
    campaign_count BIGINT,
    enabled_count BIGINT,
    paused_count BIGINT,
    archived_count BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.brand::TEXT,
        COUNT(*)::BIGINT as campaign_count,
        COUNT(*) FILTER (WHERE c.state = 'ENABLED')::BIGINT as enabled_count,
        COUNT(*) FILTER (WHERE c.state = 'PAUSED')::BIGINT as paused_count,
        COUNT(*) FILTER (WHERE c.state = 'ARCHIVED')::BIGINT as archived_count
    FROM campaigns c
    WHERE c.brand IS NOT NULL AND c.brand != ''
    GROUP BY c.brand
    ORDER BY c.brand;
END;
$$;

-- Create index for better performance on brand and state columns
CREATE INDEX IF NOT EXISTS idx_campaigns_brand_state 
ON campaigns(brand, state) 
WHERE brand IS NOT NULL;

-- Create index for sorting by common fields
CREATE INDEX IF NOT EXISTS idx_campaigns_sorting 
ON campaigns(name, brand, state, created_at, updated_at);

-- Create composite index for filtering
CREATE INDEX IF NOT EXISTS idx_campaigns_filter_composite 
ON campaigns(state, type, brand) 
WHERE state IN ('ENABLED', 'PAUSED', 'ARCHIVED');

-- Function to get campaign statistics efficiently
CREATE OR REPLACE FUNCTION get_campaign_statistics()
RETURNS TABLE (
    total_campaigns BIGINT,
    enabled_campaigns BIGINT,
    paused_campaigns BIGINT,
    archived_campaigns BIGINT,
    unique_brands BIGINT,
    sponsored_products BIGINT,
    sponsored_brands BIGINT,
    sponsored_display BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_campaigns,
        COUNT(*) FILTER (WHERE state = 'ENABLED')::BIGINT as enabled_campaigns,
        COUNT(*) FILTER (WHERE state = 'PAUSED')::BIGINT as paused_campaigns,
        COUNT(*) FILTER (WHERE state = 'ARCHIVED')::BIGINT as archived_campaigns,
        COUNT(DISTINCT brand)::BIGINT as unique_brands,
        COUNT(*) FILTER (WHERE type = 'sp')::BIGINT as sponsored_products,
        COUNT(*) FILTER (WHERE type = 'sb')::BIGINT as sponsored_brands,
        COUNT(*) FILTER (WHERE type = 'sd')::BIGINT as sponsored_display
    FROM campaigns;
END;
$$;

-- Drop existing search_campaigns function if it exists (to avoid conflicts)
DROP FUNCTION IF EXISTS search_campaigns CASCADE;

-- Function for advanced filtering with performance optimization
CREATE OR REPLACE FUNCTION search_campaigns_optimized(
    p_search TEXT DEFAULT NULL,
    p_brands TEXT[] DEFAULT NULL,
    p_states TEXT[] DEFAULT NULL,
    p_types TEXT[] DEFAULT NULL,
    p_sort_by TEXT DEFAULT 'name',
    p_sort_order TEXT DEFAULT 'ASC',
    p_limit INT DEFAULT 50,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    campaign_id TEXT,
    name TEXT,
    brand TEXT,
    state TEXT,
    type TEXT,
    targeting_type TEXT,
    bidding_strategy TEXT,
    portfolio_id TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    total_count BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_query TEXT;
    v_where_clauses TEXT[] := ARRAY[]::TEXT[];
    v_where_clause TEXT := '';
    v_order_by TEXT;
BEGIN
    -- Build WHERE clauses
    IF p_search IS NOT NULL AND p_search != '' THEN
        v_where_clauses := array_append(v_where_clauses, 
            format('c.name ILIKE %L', '%' || p_search || '%'));
    END IF;
    
    IF p_brands IS NOT NULL AND array_length(p_brands, 1) > 0 THEN
        v_where_clauses := array_append(v_where_clauses, 
            format('c.brand = ANY(%L::TEXT[])', p_brands));
    END IF;
    
    IF p_states IS NOT NULL AND array_length(p_states, 1) > 0 THEN
        v_where_clauses := array_append(v_where_clauses, 
            format('c.state = ANY(%L::TEXT[])', p_states));
    END IF;
    
    IF p_types IS NOT NULL AND array_length(p_types, 1) > 0 THEN
        v_where_clauses := array_append(v_where_clauses, 
            format('c.type = ANY(%L::TEXT[])', p_types));
    END IF;
    
    -- Combine WHERE clauses
    IF array_length(v_where_clauses, 1) > 0 THEN
        v_where_clause := 'WHERE ' || array_to_string(v_where_clauses, ' AND ');
    END IF;
    
    -- Build ORDER BY clause
    v_order_by := format('ORDER BY c.%I %s', 
        CASE p_sort_by
            WHEN 'campaign_id' THEN 'campaign_id'
            WHEN 'brand' THEN 'brand'
            WHEN 'state' THEN 'state'
            WHEN 'type' THEN 'type'
            WHEN 'created_at' THEN 'created_at'
            WHEN 'updated_at' THEN 'updated_at'
            ELSE 'name'
        END,
        CASE WHEN upper(p_sort_order) = 'DESC' THEN 'DESC' ELSE 'ASC' END
    );
    
    -- Build and execute query
    v_query := format($SQL$
        WITH filtered_campaigns AS (
            SELECT c.*, COUNT(*) OVER() as total_count
            FROM campaigns c
            %s
            %s
            LIMIT %s OFFSET %s
        )
        SELECT 
            id, campaign_id, name, brand, state, type,
            targeting_type, bidding_strategy, portfolio_id,
            created_at, updated_at, total_count
        FROM filtered_campaigns
    $SQL$, v_where_clause, v_order_by, p_limit, p_offset);
    
    RETURN QUERY EXECUTE v_query;
END;
$$;

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION get_campaign_brands_with_counts() TO authenticated;
GRANT EXECUTE ON FUNCTION get_campaign_statistics() TO authenticated;
GRANT EXECUTE ON FUNCTION search_campaigns_optimized(TEXT, TEXT[], TEXT[], TEXT[], TEXT, TEXT, INT, INT) TO authenticated;