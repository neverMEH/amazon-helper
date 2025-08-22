#!/usr/bin/env python3
"""
Seed script for ASIN Conversions: Tracked Item vs. Tracked ASIN Build Guide
This script creates a comprehensive guide explaining the critical distinction between
tracked_item and tracked_asin fields in AMC for accurate ASIN conversion analysis.
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def create_asin_conversions_guide():
    """Create the ASIN Conversions: Tracked Item vs. Tracked ASIN guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_asin_conversions_tracked_fields',
            'name': 'ASIN Conversions: Tracked Item vs. Tracked ASIN',
            'category': 'ASIN Analysis',
            'short_description': 'Understand the critical difference between tracked_item and tracked_asin fields for accurate ASIN conversion analysis',
            'tags': ['asin-analysis', 'conversions', 'tracked-item', 'tracked-asin', 'attribution', 'fundamentals'],
            'icon': 'Package',
            'difficulty_level': 'beginner',
            'estimated_time_minutes': 20,
            'prerequisites': [
                'AMC Instance with conversion data',
                'Understanding of ASIN tracking'
            ],
            'is_published': True,
            'display_order': 2,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Insert guide
        guide_response = client.table('build_guides').insert(guide_data).execute()
        if not guide_response.data:
            logger.error("Failed to create guide")
            return False
        
        guide_id = guide_response.data[0]['id']
        logger.info(f"Created guide with ID: {guide_id}")
        
        # Create sections
        sections = [
            {
                'guide_id': guide_id,
                'section_id': 'introduction',
                'title': 'Introduction',
                'content_markdown': """## Understanding the Two ASIN Tracking Fields

In Amazon Marketing Cloud, ASIN conversions are stored in two different fields depending on the type of conversion event. Understanding this distinction is **critical** for accurate reporting and analysis.

### The Two Types of ASIN Conversions

#### 1. Purchase-Related Conversions
These require an actual purchase on Amazon:
- **Examples**: purchases, new_to_brand_purchases, product_sales
- **Storage**: Recorded in BOTH `tracked_asin` AND `tracked_item` fields
- **Key Point**: Only purchase events populate `tracked_asin`

#### 2. Non-Purchase Conversions
These involve customer actions without a purchase:
- **Examples**: detail_page_view, add_to_cart, add_to_wishlist
- **Storage**: Recorded ONLY in `tracked_item` field
- **Key Point**: `tracked_asin` will be NULL for these events

### Why This Matters

Using the wrong field can lead to:
- **Missing conversions** (using tracked_asin for detail page views)
- **Incomplete analysis** (not understanding the full customer journey)
- **Incorrect attribution** (mixing purchase and non-purchase metrics)

### Quick Reference Table

| Conversion Type | tracked_item | tracked_asin | Example Events |
|----------------|--------------|--------------|----------------|
| Purchase Events | ✓ Populated | ✓ Populated | purchases, new_to_brand_purchases |
| Non-Purchase Events | ✓ Populated | ✗ NULL | detail_page_view, add_to_cart |
| Pixel Conversions | ✓ UUID String | ✗ NULL | Custom pixel events |
| Branded Search | ✓ "keyword.*" | ✗ NULL | Branded keyword conversions |

## Special Considerations

### Pixel Conversions
If your advertiser uses pixel conversions:
- These appear in `tracked_item` as UUID strings (long alphanumeric identifiers)
- They are NOT ASINs and should be filtered out for ASIN analysis
- Example: "550e8400-e29b-41d4-a716-446655440000"

### Branded Search Conversions
- Appear in `tracked_item` with prefix "keyword."
- Should be filtered out for ASIN-specific analysis
- Use filter: `WHERE tracked_item NOT SIMILAR TO '^keyword.'`

### Brand Halo Effect
Both fields can include:
- **Promoted ASINs**: Directly advertised products
- **Brand Halo ASINs**: Other products from the same brand
- Use "total_" prefixed metrics to include brand halo""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'field_comparison',
                'title': 'Field Comparison Deep Dive',
                'content_markdown': """## Detailed Field Comparison

### tracked_item Field

**What it contains:**
- ALL conversion events with an associated ASIN
- Pixel conversion UUIDs
- Branded search keywords (prefixed with "keyword.")

**When to use:**
- Analyzing the complete customer journey
- Tracking non-purchase interactions (browsing, considering)
- Comprehensive conversion reporting
- Upper-funnel metrics analysis

**Common metrics available:**
- detail_page_view / total_detail_page_view
- add_to_cart / total_add_to_cart
- add_to_wishlist
- customer_review_click
- All purchase metrics (when ASIN-related)

### tracked_asin Field

**What it contains:**
- ONLY purchase-related conversion events
- Cleaner data (no pixels or keywords)
- Direct purchase attribution

**When to use:**
- Purchase-specific analysis
- Revenue reporting
- New-to-brand analysis
- Lower-funnel metrics only

**Common metrics available:**
- purchases / total_purchases
- new_to_brand_purchases / new_to_brand_total_purchases
- product_sales / total_product_sales
- units_sold / total_units_sold

## Visual Data Flow

```
Customer Journey:
    Ad Exposure
         ↓
    Detail Page View → [tracked_item ✓] [tracked_asin ✗]
         ↓
    Add to Cart → [tracked_item ✓] [tracked_asin ✗]
         ↓
    Purchase → [tracked_item ✓] [tracked_asin ✓]
```

## Common Pitfalls to Avoid

### Pitfall 1: Using tracked_asin for all conversions
**Problem**: Missing all non-purchase interactions
**Solution**: Use tracked_item for comprehensive analysis

### Pitfall 2: Not filtering tracked_item properly
**Problem**: Including pixels and branded search in ASIN analysis
**Solution**: Apply appropriate filters:
```sql
WHERE tracked_item NOT SIMILAR TO '^keyword.'
  AND LENGTH(tracked_item) < 20  -- Filters out pixel UUIDs
  AND tracked_item IS NOT NULL
```

### Pitfall 3: Double-counting in aggregations
**Problem**: Summing metrics from both fields incorrectly
**Solution**: Understand which metrics are available in which context

## Best Practice Decision Tree

```
Are you analyzing purchases only?
├── YES → Use tracked_asin (cleaner data)
└── NO → Are you including browsing behavior?
    ├── YES → Use tracked_item (comprehensive)
    └── NO → Are you tracking custom pixels?
        ├── YES → Use tracked_item with UUID filter
        └── NO → Use tracked_asin for simplicity
```""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'use_cases',
                'title': 'Practical Use Cases',
                'content_markdown': """## Use Case Examples

### Use Case 1: Identifying High-Browse, Low-Purchase ASINs

**Business Question**: Which products get lots of views but few purchases?

**Approach**: Use tracked_item for views, combine with tracked_asin for purchases

```sql
WITH browse_purchase AS (
  SELECT
    tracked_item AS asin,
    SUM(total_detail_page_view) AS views,
    SUM(total_purchases) AS purchases,
    CASE 
      WHEN SUM(total_detail_page_view) > 0 
      THEN ROUND(100.0 * SUM(total_purchases) / SUM(total_detail_page_view), 2)
      ELSE 0 
    END AS conversion_rate
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    tracked_item NOT SIMILAR TO '^keyword.'
    AND LENGTH(tracked_item) <= 20
  GROUP BY 1
)
SELECT
  asin,
  views,
  purchases,
  conversion_rate,
  CASE
    WHEN conversion_rate < 1 AND views > 1000 THEN 'High Priority - Low Conversion'
    WHEN conversion_rate < 2 AND views > 500 THEN 'Medium Priority'
    WHEN views < 100 THEN 'Insufficient Data'
    ELSE 'Performing Well'
  END AS action_needed
FROM
  browse_purchase
WHERE
  views > 50
ORDER BY
  views DESC, conversion_rate ASC
```

**Actions Based on Results:**
- High views, low conversion → Review pricing, images, descriptions
- Medium conversion → A/B test improvements
- Low views → Increase advertising spend

### Use Case 2: Brand Halo Analysis

**Business Question**: How much do ads for one product drive sales of other brand products?

**Approach**: Compare promoted vs. total metrics

```sql
SELECT
  tracked_asin,
  SUM(purchases) AS direct_purchases,
  SUM(total_purchases) AS total_purchases_including_halo,
  SUM(total_purchases) - SUM(purchases) AS halo_purchases,
  ROUND(100.0 * (SUM(total_purchases) - SUM(purchases)) / NULLIF(SUM(purchases), 0), 2) AS halo_lift_percent
FROM
  amazon_attributed_events_by_conversion_time
WHERE
  tracked_asin IS NOT NULL
GROUP BY 1
HAVING 
  SUM(purchases) > 10
ORDER BY
  halo_lift_percent DESC
```

**Insights:**
- High halo lift → Product drives brand discovery
- Low halo lift → Product is typically purchased alone
- Use for campaign strategy and budget allocation

### Use Case 3: Custom Pixel Integration Check

**Business Question**: Are custom pixels firing correctly alongside ASIN conversions?

**Approach**: Identify UUID patterns in tracked_item

```sql
SELECT
  CASE
    WHEN tracked_item SIMILAR TO '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' 
      THEN 'Pixel Conversion'
    WHEN tracked_item SIMILAR TO '^keyword.' 
      THEN 'Branded Search'
    WHEN LENGTH(tracked_item) <= 20 
      THEN 'ASIN Conversion'
    ELSE 'Unknown Type'
  END AS conversion_type,
  COUNT(*) AS event_count,
  COUNT(DISTINCT user_id) AS unique_users
FROM
  amazon_attributed_events_by_conversion_time
WHERE
  tracked_item IS NOT NULL
GROUP BY 1
ORDER BY event_count DESC
```

**Validation Points:**
- Pixel conversions should show consistent UUID format
- ASIN conversions should be 10 characters
- Investigate any "Unknown Type" entries

### Use Case 4: Full Funnel Performance Dashboard

**Business Question**: What's the complete journey from view to purchase?

**Approach**: Build comprehensive funnel metrics

```sql
WITH funnel_stages AS (
  SELECT
    tracked_item AS asin,
    SUM(total_detail_page_view) AS stage_1_views,
    SUM(total_add_to_cart) AS stage_2_carts,
    SUM(total_purchases) AS stage_3_purchases,
    AVG(total_product_sales / NULLIF(total_purchases, 0)) AS avg_order_value
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    tracked_item NOT SIMILAR TO '^keyword.'
    AND LENGTH(tracked_item) <= 20
  GROUP BY 1
)
SELECT
  asin,
  stage_1_views,
  stage_2_carts,
  stage_3_purchases,
  ROUND(avg_order_value, 2) AS aov,
  -- Conversion rates between stages
  ROUND(100.0 * stage_2_carts / NULLIF(stage_1_views, 0), 2) AS view_to_cart_rate,
  ROUND(100.0 * stage_3_purchases / NULLIF(stage_2_carts, 0), 2) AS cart_to_purchase_rate,
  ROUND(100.0 * stage_3_purchases / NULLIF(stage_1_views, 0), 2) AS overall_conversion_rate
FROM
  funnel_stages
WHERE
  stage_1_views > 100
ORDER BY
  stage_3_purchases DESC
```

**Dashboard Metrics:**
- Stage progression rates
- Bottleneck identification
- AOV by product
- Prioritization for optimization""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'best_practices',
                'title': 'Best Practices and Tips',
                'content_markdown': """## Best Practices for Using tracked_item vs tracked_asin

### 1. Choose the Right Field for Your Analysis

#### Quick Decision Guide

| Your Goal | Use This Field | Why |
|-----------|---------------|-----|
| Purchase-only analysis | tracked_asin | Cleaner, no filtering needed |
| Full funnel analysis | tracked_item | Includes all interactions |
| Revenue reporting | tracked_asin | Direct purchase attribution |
| Browse behavior | tracked_item | Only field with non-purchase events |
| Mixed pixel + ASIN | tracked_item | Contains both data types |

### 2. Always Apply Proper Filters

#### For tracked_item:
```sql
-- Standard filter set
WHERE tracked_item NOT SIMILAR TO '^keyword.'  -- Remove branded search
  AND LENGTH(tracked_item) <= 20               -- Remove pixel UUIDs
  AND tracked_item IS NOT NULL                 -- Remove nulls
  AND tracked_item NOT LIKE '%test%'           -- Remove test ASINs
```

#### For tracked_asin:
```sql
-- Simpler filtering needed
WHERE tracked_asin IS NOT NULL
  AND tracked_asin NOT LIKE '%test%'  -- Remove test ASINs if applicable
```

### 3. Understand Metric Availability

#### Metrics Available in BOTH Fields (when purchase-related):
- purchases / total_purchases
- new_to_brand_purchases / new_to_brand_total_purchases
- product_sales / total_product_sales
- units_sold / total_units_sold

#### Metrics ONLY in tracked_item Context:
- detail_page_view / total_detail_page_view
- add_to_cart / total_add_to_cart
- add_to_wishlist / total_add_to_wishlist
- customer_review_click

### 4. Handle Edge Cases

#### Edge Case 1: Products with views but no purchases
- Will appear in tracked_item
- Will NOT appear in tracked_asin
- Solution: Use FULL OUTER JOIN when combining

#### Edge Case 2: Pixel conversions in ASIN analysis
- Filter by string length: `LENGTH(tracked_item) <= 20`
- Or use regex pattern matching for UUIDs
- Consider maintaining a pixel UUID lookup table

#### Edge Case 3: Test or invalid ASINs
- Create exclusion list for known test ASINs
- Validate ASIN format (typically 10 alphanumeric characters)
- Check against product catalog if available

### 5. Performance Optimization

#### For Large Datasets:
```sql
-- Use materialized CTEs for better performance
WITH asin_metrics AS MATERIALIZED (
  SELECT tracked_item, 
         SUM(total_detail_page_view) as dpv
  FROM amazon_attributed_events_by_conversion_time
  WHERE DATE(conversion_event_dt) >= CURRENT_DATE - 30
    AND tracked_item NOT SIMILAR TO '^keyword.'
  GROUP BY 1
)
```

#### Index Usage Tips:
- Filter on date first when possible
- Use tracked_asin for purchase-only queries (smaller dataset)
- Consider partitioning by date for very large instances

### 6. Common Mistakes to Avoid

#### ❌ Mistake 1: Assuming all conversions are in tracked_asin
```sql
-- WRONG: Misses non-purchase conversions
SELECT tracked_asin, SUM(total_detail_page_view) 
FROM amazon_attributed_events_by_conversion_time
```

#### ✅ Correct Approach:
```sql
-- RIGHT: Uses tracked_item for detail page views
SELECT tracked_item, SUM(total_detail_page_view) 
FROM amazon_attributed_events_by_conversion_time
WHERE tracked_item NOT SIMILAR TO '^keyword.'
```

#### ❌ Mistake 2: Not handling NULLs in JOINs
```sql
-- WRONG: Loses products with no purchases
SELECT * FROM browsing_data b
INNER JOIN purchase_data p ON b.asin = p.asin
```

#### ✅ Correct Approach:
```sql
-- RIGHT: Keeps all products
SELECT * FROM browsing_data b
FULL OUTER JOIN purchase_data p ON b.asin = p.asin
```

### 7. Validation Queries

#### Check Data Quality:
```sql
-- Validate ASIN formats in your data
SELECT
  CASE
    WHEN LENGTH(tracked_item) = 10 THEN 'Valid ASIN'
    WHEN LENGTH(tracked_item) = 36 THEN 'Pixel UUID'
    WHEN tracked_item SIMILAR TO '^keyword.' THEN 'Branded Search'
    ELSE 'Check Format'
  END as item_type,
  COUNT(*) as count,
  MIN(tracked_item) as example
FROM amazon_attributed_events_by_conversion_time
WHERE tracked_item IS NOT NULL
GROUP BY 1
```

#### Verify Field Population:
```sql
-- Check which events populate which fields
SELECT
  conversion_event_type_description,
  COUNT(*) as total_events,
  COUNT(tracked_item) as has_tracked_item,
  COUNT(tracked_asin) as has_tracked_asin,
  ROUND(100.0 * COUNT(tracked_asin) / COUNT(*), 2) as pct_with_asin
FROM amazon_attributed_events_by_conversion_time
GROUP BY 1
ORDER BY total_events DESC
```

## Summary Checklist

Before running your analysis, verify:

- [ ] Identified whether you need purchase-only or full funnel metrics
- [ ] Selected appropriate field (tracked_item vs tracked_asin)
- [ ] Applied necessary filters for data quality
- [ ] Understood which metrics are available in your chosen field
- [ ] Handled edge cases appropriately
- [ ] Validated data quality with test queries
- [ ] Optimized query performance for large datasets""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            }
        ]
        
        # Insert sections
        for section in sections:
            response = client.table('build_guide_sections').insert(section).execute()
            if response.data:
                logger.info(f"Created section: {section['title']}")
            else:
                logger.error(f"Failed to create section: {section['title']}")
        
        # Create queries
        queries = [
            {
                'guide_id': guide_id,
                'title': 'Total Conversions by ASIN (All Types)',
                'description': 'Returns ALL conversion types using tracked_item field for comprehensive analysis',
                'sql_query': """-- All conversions by ASIN and conversion type
SELECT
  tracked_item AS ASIN,
  conversion_event_type_description,
  SUM(conversions) AS conversions,
  COUNT(DISTINCT user_id) AS unique_users
FROM
  amazon_attributed_events_by_conversion_time
WHERE
  -- Remove branded search conversions
  tracked_item NOT SIMILAR TO '^keyword.'
  -- Remove pixel conversions (UUIDs are typically 36 characters)
  AND LENGTH(tracked_item) <= 20
  AND tracked_item IS NOT NULL
GROUP BY
  1, 2
ORDER BY
  conversions DESC""",
                'parameters_schema': {},
                'default_parameters': {},
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'Use this query when you need a complete view of all customer interactions, building conversion funnels, or understanding the full customer journey.'
            },
            {
                'guide_id': guide_id,
                'title': 'Funnel Analysis (Non-Purchase Events)',
                'description': 'Shows upper and mid-funnel metrics using tracked_item field',
                'sql_query': """-- Detail page views and add-to-cart by ASIN
SELECT
  tracked_item AS ASIN,
  -- Promoted ASINs only
  SUM(detail_page_view) AS dpv_promoted,
  -- Including brand halo
  SUM(total_detail_page_view) AS dpv_total,
  -- Add to cart - promoted
  SUM(add_to_cart) AS atc_promoted,
  -- Add to cart - including brand halo
  SUM(total_add_to_cart) AS atc_total,
  -- Calculate conversion rates
  CASE 
    WHEN SUM(total_detail_page_view) > 0 
    THEN ROUND(100.0 * SUM(total_add_to_cart) / SUM(total_detail_page_view), 2)
    ELSE 0 
  END AS atc_rate_percent
FROM
  amazon_attributed_events_by_conversion_time
WHERE
  tracked_item NOT SIMILAR TO '^keyword.'
  AND LENGTH(tracked_item) <= 20
  AND tracked_item IS NOT NULL
  -- Optional: Filter to specific date range
  AND conversion_event_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
GROUP BY
  1
HAVING
  SUM(total_detail_page_view) > {{min_views}}  -- Minimum threshold for significance
ORDER BY
  dpv_total DESC""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back'
                    },
                    'min_views': {
                        'type': 'integer',
                        'default': 100,
                        'description': 'Minimum detail page views for significance'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'min_views': 100
                },
                'display_order': 2,
                'query_type': 'exploratory',
                'interpretation_notes': 'Use this query when analyzing browsing behavior, identifying products with high browse but low purchase, or optimizing product detail pages.'
            },
            {
                'guide_id': guide_id,
                'title': 'Purchase Analysis (Clean Purchase Data)',
                'description': 'Uses tracked_asin field for purchase-only metrics with cleaner data',
                'sql_query': """-- Purchase metrics using tracked_asin
SELECT
  tracked_asin,
  -- Promoted ASIN purchases
  SUM(purchases) AS purchases_promoted,
  -- Including brand halo
  SUM(total_purchases) AS purchases_total,
  -- New to brand
  SUM(new_to_brand_purchases) AS ntb_purchases_promoted,
  SUM(new_to_brand_total_purchases) AS ntb_purchases_total,
  -- Calculate NTB rate
  CASE 
    WHEN SUM(total_purchases) > 0 
    THEN ROUND(100.0 * SUM(new_to_brand_total_purchases) / SUM(total_purchases), 2)
    ELSE 0 
  END AS ntb_rate_percent,
  -- Revenue metrics
  SUM(product_sales) AS revenue_promoted,
  SUM(total_product_sales) AS revenue_total
FROM
  amazon_attributed_events_by_conversion_time
WHERE
  tracked_asin IS NOT NULL
  AND conversion_event_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
GROUP BY
  1
HAVING
  SUM(total_purchases) > 0
ORDER BY
  revenue_total DESC""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30
                },
                'display_order': 3,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Use this query when focusing solely on purchase metrics, calculating ROAS, or performing new-to-brand analysis.'
            },
            {
                'guide_id': guide_id,
                'title': 'Complete Funnel View (Combining Both Fields)',
                'description': 'Advanced query creating a full funnel view by combining both tracked_item and tracked_asin',
                'sql_query': """-- Complete funnel analysis
WITH browsing_metrics AS (
  SELECT
    tracked_item AS asin,
    SUM(total_detail_page_view) AS dpv,
    SUM(total_add_to_cart) AS atc,
    SUM(total_add_to_wishlist) AS wishlist
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    tracked_item NOT SIMILAR TO '^keyword.'
    AND LENGTH(tracked_item) <= 20
    AND tracked_item IS NOT NULL
    AND conversion_event_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
  GROUP BY 1
),
purchase_metrics AS (
  SELECT
    tracked_asin AS asin,
    SUM(total_purchases) AS purchases,
    SUM(new_to_brand_total_purchases) AS ntb_purchases,
    SUM(total_product_sales) AS revenue,
    SUM(total_units_sold) AS units
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    tracked_asin IS NOT NULL
    AND conversion_event_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
  GROUP BY 1
)
SELECT
  COALESCE(b.asin, p.asin) AS asin,
  -- Browsing metrics
  COALESCE(b.dpv, 0) AS detail_page_views,
  COALESCE(b.atc, 0) AS add_to_carts,
  COALESCE(b.wishlist, 0) AS wishlists,
  -- Purchase metrics
  COALESCE(p.purchases, 0) AS purchases,
  COALESCE(p.ntb_purchases, 0) AS new_to_brand,
  COALESCE(p.revenue, 0) AS total_revenue,
  -- Conversion rates
  CASE 
    WHEN b.dpv > 0 
    THEN ROUND(100.0 * p.purchases / b.dpv, 2)
    ELSE 0 
  END AS dpv_to_purchase_rate,
  CASE 
    WHEN b.atc > 0 
    THEN ROUND(100.0 * p.purchases / b.atc, 2)
    ELSE 0 
  END AS atc_to_purchase_rate
FROM
  browsing_metrics b
  FULL OUTER JOIN purchase_metrics p ON b.asin = p.asin
WHERE
  COALESCE(b.dpv, 0) + COALESCE(p.purchases, 0) > 0
ORDER BY
  total_revenue DESC
LIMIT {{limit}}""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back'
                    },
                    'limit': {
                        'type': 'integer',
                        'default': 100,
                        'description': 'Maximum number of ASINs to return'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'limit': 100
                },
                'display_order': 4,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Use this query when you need complete funnel visualization, identifying conversion bottlenecks, or comprehensive ASIN performance analysis.'
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add example results for main analysis queries
                if query['query_type'] == 'main_analysis' and 'Purchase Analysis' in query['title']:
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Purchase Analysis Results',
                        'sample_data': {
                            'rows': [
                                {
                                    'tracked_asin': 'B0ABC12345',
                                    'purchases_promoted': 150,
                                    'purchases_total': 180,
                                    'ntb_purchases_promoted': 45,
                                    'ntb_purchases_total': 54,
                                    'ntb_rate_percent': 30.00,
                                    'revenue_promoted': 4500.00,
                                    'revenue_total': 5400.00
                                },
                                {
                                    'tracked_asin': 'B0DEF67890',
                                    'purchases_promoted': 120,
                                    'purchases_total': 125,
                                    'ntb_purchases_promoted': 60,
                                    'ntb_purchases_total': 62,
                                    'ntb_rate_percent': 49.60,
                                    'revenue_promoted': 2400.00,
                                    'revenue_total': 2500.00
                                },
                                {
                                    'tracked_asin': 'B0GHI12345',
                                    'purchases_promoted': 80,
                                    'purchases_total': 95,
                                    'ntb_purchases_promoted': 20,
                                    'ntb_purchases_total': 24,
                                    'ntb_rate_percent': 25.26,
                                    'revenue_promoted': 3200.00,
                                    'revenue_total': 3800.00
                                }
                            ]
                        },
                        'interpretation_markdown': """**Key Insights from Purchase Analysis:**

1. **Top Performer**: ASIN B0ABC12345 drives the highest revenue ($5,400 total) with strong brand halo effect (20% additional purchases)

2. **New Customer Acquisition**: ASIN B0DEF67890 shows exceptional new-to-brand performance at 49.6%, nearly half of all purchasers are new to the brand

3. **Brand Halo Champion**: ASIN B0GHI12345 shows the strongest brand halo with 18.75% additional purchases beyond the promoted ASIN

**Recommendations:**
- Increase investment in B0DEF67890 for customer acquisition campaigns
- Use B0ABC12345 for revenue-focused campaigns
- Consider bundling strategies for B0GHI12345 given its strong brand halo effect""",
                        'insights': [
                            'tracked_asin provides cleaner purchase data without filtering requirements',
                            'Brand halo effect varies significantly by product (4-20% additional purchases)',
                            'New-to-brand rates can help optimize campaign targeting strategies',
                            'Revenue and purchase volume don\'t always correlate with NTB rates'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created example results for Purchase Analysis")
                
                # Add example for Complete Funnel View
                if 'Complete Funnel View' in query['title']:
                    funnel_example = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Funnel Analysis Results',
                        'sample_data': {
                            'rows': [
                                {
                                    'asin': 'B0ABC12345',
                                    'detail_page_views': 5000,
                                    'add_to_carts': 500,
                                    'wishlists': 150,
                                    'purchases': 180,
                                    'new_to_brand': 54,
                                    'total_revenue': 5400.00,
                                    'dpv_to_purchase_rate': 3.60,
                                    'atc_to_purchase_rate': 36.00
                                },
                                {
                                    'asin': 'B0XYZ98765',
                                    'detail_page_views': 8000,
                                    'add_to_carts': 400,
                                    'wishlists': 200,
                                    'purchases': 60,
                                    'new_to_brand': 30,
                                    'total_revenue': 1200.00,
                                    'dpv_to_purchase_rate': 0.75,
                                    'atc_to_purchase_rate': 15.00
                                },
                                {
                                    'asin': 'B0MNO45678',
                                    'detail_page_views': 2000,
                                    'add_to_carts': 0,
                                    'wishlists': 50,
                                    'purchases': 0,
                                    'new_to_brand': 0,
                                    'total_revenue': 0.00,
                                    'dpv_to_purchase_rate': 0.00,
                                    'atc_to_purchase_rate': 0.00
                                }
                            ]
                        },
                        'interpretation_markdown': """**Funnel Analysis Insights:**

1. **High Converter**: B0ABC12345 shows excellent funnel performance:
   - 10% view-to-cart rate (500/5000)
   - 36% cart-to-purchase rate
   - Strong overall conversion at 3.6%

2. **Bottleneck Product**: B0XYZ98765 has issues converting views to carts:
   - Only 5% view-to-cart rate despite 8000 views
   - But 15% cart-to-purchase shows product quality isn't the issue
   - Likely needs better product page optimization

3. **Browse-Only Product**: B0MNO45678 gets views and wishlists but no purchases:
   - Zero add-to-carts despite 2000 views
   - 50 wishlists suggest interest but price/availability issues
   - Requires investigation into barriers to purchase

**Key Takeaway**: Using tracked_item for browsing metrics and combining with purchase data reveals conversion bottlenecks that tracked_asin alone would miss.""",
                        'insights': [
                            'Full funnel analysis requires tracked_item for non-purchase events',
                            'High browse with low add-to-cart indicates product page issues',
                            'High wishlist with no purchases suggests price or availability problems',
                            'Cart-to-purchase rates help identify checkout friction'
                        ],
                        'display_order': 2
                    }
                    
                    funnel_response = client.table('build_guide_examples').insert(funnel_example).execute()
                    if funnel_response.data:
                        logger.info("Created example results for Funnel Analysis")
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'tracked_item',
                'display_name': 'Tracked Item',
                'definition': 'Field containing ALL conversion events including non-purchase interactions, pixel UUIDs, and branded search keywords. Primary field for comprehensive conversion analysis.',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'tracked_asin',
                'display_name': 'Tracked ASIN',
                'definition': 'Field containing ONLY purchase-related conversion events. Cleaner data source for purchase-specific analysis without pixels or keywords.',
                'metric_type': 'dimension',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'detail_page_view',
                'display_name': 'Detail Page Views',
                'definition': 'Number of times customers viewed the product detail page. Only available through tracked_item field.',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'add_to_cart',
                'display_name': 'Add to Cart',
                'definition': 'Number of times customers added the product to their cart. Only available through tracked_item field.',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'purchases',
                'display_name': 'Purchases',
                'definition': 'Number of completed purchases for promoted ASINs. Available in both tracked_item and tracked_asin fields.',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'total_purchases',
                'display_name': 'Total Purchases (with Brand Halo)',
                'definition': 'Total purchases including both promoted ASINs and brand halo effect. Available in both fields for purchase events.',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversion_rate',
                'display_name': 'Conversion Rate',
                'definition': 'Percentage of users who complete a desired action (e.g., purchase after viewing). Calculation depends on chosen funnel stages.',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'brand_halo_lift',
                'display_name': 'Brand Halo Lift',
                'definition': 'Percentage increase in sales from other brand products beyond the advertised ASIN. Calculated as (total_purchases - purchases) / purchases.',
                'metric_type': 'metric',
                'display_order': 8
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info("✅ Successfully created ASIN Conversions: Tracked Item vs. Tracked ASIN guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_asin_conversions_guide()
    sys.exit(0 if success else 1)