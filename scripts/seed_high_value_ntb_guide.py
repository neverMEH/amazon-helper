"""
Seed script for High-Value New-to-Brand Customer Audiences build guide
This creates a comprehensive guide for creating rule-based audiences of new-to-brand customers
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
if not supabase_url or not supabase_key:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

def seed_high_value_ntb_guide():
    """Seeds the High-Value New-to-Brand Customer Audiences build guide"""
    
    # Create the main guide
    guide_data = {
        "guide_id": "guide_high_value_ntb_audiences",
        "name": "High-Value New-to-Brand Customer Audiences",
        "category": "Audience Creation",
        "short_description": "Create rule-based audiences of new-to-brand customers with high purchase values, non-ad attributed customers, and sponsored ads engaged customers not reached by DSP",
        "tags": ["New-to-brand", "Audience creation", "Rule-based audiences", "Customer segmentation", "High-value customers"],
        "difficulty_level": "advanced",
        "estimated_time_minutes": 60,
        "prerequisites": [
            "AMC instance with rule-based audience capabilities",
            "Flexible Amazon Shopping Insights subscription",
            "Understanding of new-to-brand definitions",
            "Amazon DSP access for audience activation"
        ],
        "is_published": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Delete existing guide if it exists
    supabase.table('build_guides').delete().eq('guide_id', guide_data['guide_id']).execute()
    
    result = supabase.table('build_guides').insert(guide_data).execute()
    guide_uuid = result.data[0]['id']  # Get the UUID from the response
    guide_string_id = guide_data['guide_id']
    print(f"Created guide: {guide_string_id} (UUID: {guide_uuid})")
    
    # Create sections
    sections = [
        {
            "guide_id": guide_uuid,
            "section_id": "introduction",
            "title": "Introduction",
            "display_order": 1,
            "content_markdown": """## Purpose

This guide helps you create three specific high-value new-to-brand (NTB) customer audiences:

1. **High-Value NTB Customers**: Customers that are new-to-brand and have made high-value purchases
2. **Non-Ad Attributed NTB**: Customers that are new-to-brand and have not been exposed to ads
3. **Sponsored-Only NTB**: Customers engaged with sponsored ads but not reached by Amazon DSP

## What You'll Learn

- How to define and segment high-value new-to-brand customers
- Rule-based audience creation techniques for AMC
- Measurement queries to estimate audience sizes before creation
- Advanced filtering techniques for precise audience targeting
- Integration with Amazon DSP for audience activation

## Key Business Applications

- **Acquisition Strategy**: Target high-value customers who haven't discovered your brand through ads
- **Cross-Channel Optimization**: Reach sponsored ads customers through DSP for complete funnel coverage
- **Value-Based Segmentation**: Focus marketing efforts on customers with demonstrated high spending behavior
- **Incremental Reach**: Expand beyond current ad-exposed audiences to organic high-value customers

## Requirements

### Essential Requirements
- AMC instance with rule-based audience capabilities
- Flexible Amazon Shopping Insights subscription (navigate to Paid features tab)
- Amazon DSP access for audience activation
- At least 90 days of historical data for accurate NTB identification

### Data Requirements
- Conversion events with new-to-brand flags
- Purchase value data for customer segmentation
- Traffic data from both sponsored ads and DSP campaigns"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "understanding_rule_based",
            "title": "Understanding Rule-Based Audiences",
            "display_order": 2,
            "content_markdown": """## How Rule-Based Audiences Work

Unlike standard AMC queries that return downloadable results, rule-based audience queries:
- Select user_id values to create Amazon DSP audiences
- Send audiences directly to DSP for activation
- Do not return data for download or analysis
- Require specific table variants with "_for_audiences" suffix

## Audience Tables Used

### Core Tables

| Table Name | Description | Key Fields |
|------------|-------------|------------|
| `dsp_impressions_for_audiences` | DSP Display and Streaming TV impression data | user_id, campaign, ad_product_type |
| `sponsored_ads_traffic_for_audiences` | Sponsored ads traffic with keywords and search terms | user_id, keyword, search_term |
| `amazon_attributed_events_by_conversion_time_for_audiences` | Conversion events by conversion time | user_id, new_to_brand_indicator, product_sales |
| `amazon_attributed_events_by_traffic_time_for_audiences` | Conversion events by traffic time | user_id, attribution_type, total_product_sales |
| `conversions_all_for_audiences` | All conversion types including pixel conversions | user_id, asin, conversion_type |

## New-to-Brand Definition

### Key Concepts
- **New-to-Brand (NTB)**: Customers who have not purchased from your brand in the previous 12 months
- **High-Value**: Customers with purchase amounts above defined thresholds
- **Attribution Types**: Ad-attributed vs non-ad-attributed purchase behavior

### Time Windows
- **Lookback Period**: 12 months for NTB determination
- **Conversion Window**: 14-day standard attribution window
- **Audience Refresh**: Daily or weekly based on campaign needs"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "audience_creation_process",
            "title": "Audience Creation Process",
            "display_order": 3,
            "content_markdown": """## Step 1: Measurement and Sizing

Before creating audiences, use measurement queries to:
- Estimate audience sizes for budget planning
- Understand value distribution among NTB customers
- Validate filtering criteria effectiveness
- Set appropriate purchase value thresholds

### Size Estimation Best Practices

| Metric | Recommended Range | Action if Outside Range |
|--------|-------------------|------------------------|
| Audience Size | 10,000 - 1,000,000 users | Too small: Broaden criteria. Too large: Add filters |
| Average Purchase Value | > $50 | Adjust threshold based on category |
| NTB Percentage | 20-40% of total customers | Validate NTB definition accuracy |

## Step 2: Audience Definition

Define three distinct audience types:

### High-Value NTB
- **Criteria**: NTB customers with purchases > $100
- **Use Case**: Premium product marketing, loyalty programs
- **Expected Size**: 5-15% of total NTB

### Non-Ad Attributed NTB
- **Criteria**: NTB customers with organic purchases
- **Use Case**: Brand awareness campaigns, first-touch attribution
- **Expected Size**: 30-50% of total NTB

### Sponsored-Only NTB
- **Criteria**: NTB customers with sponsored ads exposure but no DSP
- **Use Case**: Cross-channel expansion, full-funnel coverage
- **Expected Size**: 20-30% of total NTB

## Step 3: Audience Activation

### Activation Workflow
1. **Create Audience**: Execute rule-based query in AMC
2. **Sync to DSP**: Automatic transfer (15-30 minutes)
3. **Campaign Setup**: Create DSP line items targeting audience
4. **Monitor Performance**: Track reach, frequency, and conversions

### Refresh Settings

| Setting | Fixed Window | Auto-Adjusting | Recommendation |
|---------|--------------|----------------|----------------|
| Use Case | Evergreen campaigns | Time-sensitive promotions | Most campaigns use Fixed |
| Consistency | High | Variable | Fixed for testing |
| Maintenance | Low | Minimal | Fixed for simplicity |"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "advanced_customization",
            "title": "Advanced Customization Options",
            "display_order": 4,
            "content_markdown": """## Purchase Value Thresholds

### Customization Options

| Metric | Definition | Use Case |
|--------|------------|----------|
| `total_product_sales` | Includes promoted ASINs + brand halo purchases | Comprehensive value assessment |
| `product_sales` | Only promoted ASINs purchases | Direct campaign attribution |
| `order_value` | Complete basket value | Customer spending power |

### Dynamic Threshold Examples

```sql
-- Category-based thresholds
CASE 
    WHEN category = 'Electronics' THEN 200
    WHEN category = 'Home & Kitchen' THEN 75
    WHEN category = 'Beauty' THEN 50
    ELSE 100
END as value_threshold

-- Percentile-based thresholds
PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_product_sales) as p75_value
```

## ASIN Filtering

### When to Use ASIN Filters

| Scenario | Filter Type | Example |
|----------|-------------|---------|
| Focus on specific products | Include list | Top 10 best sellers |
| Exclude low-margin items | Exclude list | Sample/trial products |
| Target competitor customers | Competitor ASINs | Similar product buyers |
| Seasonal campaigns | Time-based + ASIN | Holiday gift sets |

### Implementation Example

```sql
WHERE asin IN (
    'B08N5WRWNW',  -- Echo Echo Dot (Echo 4th Gen)
    'B07FZ8S74R',  -- Echo Show 8
    'B07HZLHPKP'   -- Echo Show 5
)
AND new_to_brand_indicator = 'Y'
AND total_product_sales >= 100
```

## Time Window Management

### Fixed vs Auto-Adjusting

| Aspect | Fixed Window | Auto-Adjusting |
|--------|--------------|----------------|
| **Date Range** | Static (e.g., 2024-01-01 to 2024-12-31) | Dynamic (e.g., last 90 days) |
| **Audience Stability** | Consistent membership | Changes with time |
| **Use Cases** | A/B testing, controlled experiments | Evergreen campaigns |
| **Maintenance** | Requires manual updates | Self-maintaining |

### Recommended Settings by Campaign Type

| Campaign Type | Window Type | Lookback Period | Refresh Frequency |
|---------------|-------------|-----------------|-------------------|
| Brand Launch | Fixed | 30 days | Daily |
| Seasonal | Fixed | Season duration | Weekly |
| Always-On | Auto-Adjusting | 90 days | Daily |
| Test & Learn | Fixed | Test period | No refresh |"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "strategic_implementation",
            "title": "Strategic Implementation",
            "display_order": 5,
            "content_markdown": """## Audience Prioritization

### Tiered Approach

| Tier | Audience Type | Priority | Budget Allocation | Messaging Strategy |
|------|---------------|----------|-------------------|-------------------|
| **Tier 1** | High-Value NTB | Highest | 40-50% | Premium products, exclusive offers |
| **Tier 2** | Sponsored-Only NTB | Medium | 30-35% | Cross-sell, category expansion |
| **Tier 3** | Non-Ad Attributed NTB | Lower | 20-25% | Brand awareness, education |

### ROI Expectations

- **High-Value NTB**: 3-5x ROAS, 15-20% conversion rate
- **Sponsored-Only NTB**: 2-3x ROAS, 10-15% conversion rate
- **Non-Ad Attributed NTB**: 1.5-2x ROAS, 5-10% conversion rate

## Cross-Channel Strategy

### Sponsored Ads + DSP Integration

| Strategy Component | Implementation | Expected Outcome |
|-------------------|----------------|------------------|
| **Overlap Analysis** | Measure shared audiences | Identify incremental reach |
| **Sequential Messaging** | Sponsored → DSP funnel | Improved conversion path |
| **Frequency Management** | Cap at 3-5x per week | Prevent ad fatigue |
| **Creative Alignment** | Consistent brand message | Higher brand recall |

### Channel Allocation Matrix

```
Customer Journey Stage → Channel Priority
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Discovery → Sponsored Ads (70%) + DSP Display (30%)
Consideration → DSP Display (50%) + Sponsored Brands (50%)
Purchase → Sponsored Products (60%) + DSP Retargeting (40%)
Loyalty → DSP CRM (80%) + Sponsored Display (20%)
```

## Performance Optimization

### Key Metrics to Monitor

| Metric | Target Range | Optimization Action |
|--------|--------------|-------------------|
| **Audience Refresh Rate** | 95-100% | Check data pipeline if < 95% |
| **Match Rate** | > 70% | Expand criteria if below |
| **NTB Conversion Rate** | 8-12% | Adjust value thresholds |
| **Cost per NTB** | < $50 | Refine targeting if higher |
| **Audience Overlap** | < 30% | Increase differentiation if higher |

### Testing Framework

1. **Baseline Period** (Weeks 1-2)
   - Establish performance benchmarks
   - Monitor audience sizes and refresh rates
   
2. **Optimization Period** (Weeks 3-6)
   - Test value thresholds
   - Adjust refresh frequencies
   - Refine ASIN filters
   
3. **Scale Period** (Weeks 7+)
   - Expand successful segments
   - Increase budget allocation
   - Roll out to additional campaigns

### Troubleshooting Common Issues

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Small audience size | Threshold too high | Lower value requirements |
| Poor match rate | Data quality issues | Verify tracking implementation |
| Low conversion rate | Wrong audience | Review NTB definition |
| High overlap | Similar criteria | Add distinguishing filters |"""
        }
    ]
    
    for section in sections:
        result = supabase.table('build_guide_sections').upsert(section).execute()
    print(f"Created {len(sections)} sections")
    
    # Create queries
    queries = [
        {
            "guide_id": guide_uuid,
            "title": "Measurement Query - Size High-Value NTB Audiences",
            "query_type": "exploratory",
            "display_order": 1,
            "sql_query": """-- Measurement Query: Estimate sizes of high-value NTB customer audiences
-- This query helps you understand audience sizes before creating rule-based audiences

WITH ntb_customers AS (
    -- Get all new-to-brand customers in the measurement period
    SELECT 
        COUNT(DISTINCT user_id) as total_ntb_customers,
        AVG(total_product_sales) as avg_purchase_value,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_product_sales) as median_purchase_value,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_product_sales) as p75_purchase_value,
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY total_product_sales) as p90_purchase_value,
        MAX(total_product_sales) as max_purchase_value
    FROM amazon_attributed_events_by_conversion_time
    WHERE conversion_event_dt BETWEEN {{start_date}} AND {{end_date}}
        AND new_to_brand_indicator = 'Y'
        AND total_product_sales > 0
        {{asin_filter}}
),
high_value_ntb AS (
    -- Count customers above value threshold
    SELECT 
        COUNT(DISTINCT user_id) as high_value_customers
    FROM amazon_attributed_events_by_conversion_time
    WHERE conversion_event_dt BETWEEN {{start_date}} AND {{end_date}}
        AND new_to_brand_indicator = 'Y'
        AND total_product_sales >= {{value_threshold}}
        {{asin_filter}}
),
non_ad_attributed AS (
    -- Count non-ad attributed NTB customers
    SELECT 
        COUNT(DISTINCT user_id) as organic_ntb_customers
    FROM amazon_attributed_events_by_conversion_time
    WHERE conversion_event_dt BETWEEN {{start_date}} AND {{end_date}}
        AND new_to_brand_indicator = 'Y'
        AND (ad_attributed = 'N' OR ad_attributed IS NULL)
        {{asin_filter}}
),
sponsored_only AS (
    -- Count customers with sponsored ads but no DSP exposure
    SELECT 
        COUNT(DISTINCT sa.user_id) as sponsored_only_customers
    FROM (
        SELECT DISTINCT user_id
        FROM sponsored_ads_traffic
        WHERE click_dt BETWEEN {{start_date}} AND {{end_date}}
    ) sa
    LEFT JOIN (
        SELECT DISTINCT user_id
        FROM dsp_impressions
        WHERE impression_dt BETWEEN {{start_date}} AND {{end_date}}
    ) dsp ON sa.user_id = dsp.user_id
    INNER JOIN (
        SELECT DISTINCT user_id
        FROM amazon_attributed_events_by_conversion_time
        WHERE conversion_event_dt BETWEEN {{start_date}} AND {{end_date}}
            AND new_to_brand_indicator = 'Y'
            {{asin_filter}}
    ) ntb ON sa.user_id = ntb.user_id
    WHERE dsp.user_id IS NULL
)
SELECT 
    'Audience Size Estimates' as metric_category,
    ntb.total_ntb_customers,
    ROUND(ntb.avg_purchase_value, 2) as avg_purchase_value,
    ROUND(ntb.median_purchase_value, 2) as median_purchase_value,
    ROUND(ntb.p75_purchase_value, 2) as p75_purchase_value,
    ROUND(ntb.p90_purchase_value, 2) as p90_purchase_value,
    hv.high_value_customers,
    ROUND(100.0 * hv.high_value_customers / NULLIF(ntb.total_ntb_customers, 0), 2) as high_value_percentage,
    na.organic_ntb_customers,
    ROUND(100.0 * na.organic_ntb_customers / NULLIF(ntb.total_ntb_customers, 0), 2) as organic_percentage,
    so.sponsored_only_customers,
    ROUND(100.0 * so.sponsored_only_customers / NULLIF(ntb.total_ntb_customers, 0), 2) as sponsored_only_percentage
FROM ntb_customers ntb
CROSS JOIN high_value_ntb hv
CROSS JOIN non_ad_attributed na
CROSS JOIN sponsored_only so""",
            "parameters_schema": {
                "start_date": {
                    "type": "date",
                    "description": "Start date for measurement period",
                    "required": True,
                    "default": "2024-01-01T00:00:00"
                },
                "end_date": {
                    "type": "date", 
                    "description": "End date for measurement period",
                    "required": True,
                    "default": "2024-03-31T00:00:00"
                },
                "value_threshold": {
                    "type": "number",
                    "description": "Minimum purchase value for high-value classification",
                    "required": True,
                    "default": 100
                },
                "asin_filter": {
                    "type": "string",
                    "description": "Optional ASIN filter (e.g., AND asin IN ('B001', 'B002'))",
                    "required": False,
                    "default": ""
                }
            }
        },
        {
            "guide_id": guide_uuid,
            "title": "Create High-Value NTB Audience",
            "query_type": "main_analysis",
            "display_order": 2,
            "sql_query": """-- Rule-Based Audience: High-Value New-to-Brand Customers
-- Creates an audience of NTB customers with purchases above value threshold

SELECT DISTINCT 
    user_id
FROM amazon_attributed_events_by_conversion_time_for_audiences
WHERE conversion_event_dt BETWEEN {{start_date}} AND {{end_date}}
    AND new_to_brand_indicator = 'Y'
    AND total_product_sales >= {{value_threshold}}
    {{asin_filter}}
    {{advertiser_filter}}
GROUP BY user_id
HAVING SUM(total_product_sales) >= {{cumulative_threshold}}""",
            "parameters_schema": {
                "start_date": {
                    "type": "date",
                    "description": "Start date for audience window",
                    "required": True,
                    "default": "2024-01-01T00:00:00"
                },
                "end_date": {
                    "type": "date",
                    "description": "End date for audience window",
                    "required": True,
                    "default": "2024-03-31T00:00:00"
                },
                "value_threshold": {
                    "type": "number",
                    "description": "Minimum single purchase value",
                    "required": True,
                    "default": 100
                },
                "cumulative_threshold": {
                    "type": "number",
                    "description": "Minimum total purchase value across period",
                    "required": True,
                    "default": 150
                },
                "asin_filter": {
                    "type": "string",
                    "description": "Optional ASIN filter",
                    "required": False,
                    "default": ""
                },
                "advertiser_filter": {
                    "type": "string",
                    "description": "Optional advertiser filter for multi-brand instances",
                    "required": False,
                    "default": ""
                }
            }
        },
        {
            "guide_id": guide_uuid,
            "title": "Create Non-Ad Attributed NTB Audience",
            "query_type": "main_analysis",
            "display_order": 3,
            "sql_query": """-- Rule-Based Audience: Non-Ad Attributed New-to-Brand Customers
-- Creates an audience of NTB customers who purchased without ad exposure

SELECT DISTINCT 
    c.user_id
FROM amazon_attributed_events_by_conversion_time_for_audiences c
LEFT JOIN (
    -- Get all users with ad exposure
    SELECT DISTINCT user_id
    FROM (
        SELECT user_id FROM dsp_impressions_for_audiences
        WHERE impression_dt BETWEEN {{start_date}} AND {{end_date}}
        UNION
        SELECT user_id FROM sponsored_ads_traffic_for_audiences
        WHERE click_dt BETWEEN {{start_date}} AND {{end_date}}
    ) ad_exposed
) ads ON c.user_id = ads.user_id
WHERE c.conversion_event_dt BETWEEN {{start_date}} AND {{end_date}}
    AND c.new_to_brand_indicator = 'Y'
    AND ads.user_id IS NULL  -- No ad exposure
    AND c.total_product_sales > 0
    {{asin_filter}}
    {{value_filter}}""",
            "parameters_schema": {
                "start_date": {
                    "type": "date",
                    "description": "Start date for audience window",
                    "required": True,
                    "default": "2024-01-01T00:00:00"
                },
                "end_date": {
                    "type": "date",
                    "description": "End date for audience window",
                    "required": True,
                    "default": "2024-03-31T00:00:00"
                },
                "asin_filter": {
                    "type": "string",
                    "description": "Optional ASIN filter",
                    "required": False,
                    "default": ""
                },
                "value_filter": {
                    "type": "string",
                    "description": "Optional value filter (e.g., AND total_product_sales >= 50)",
                    "required": False,
                    "default": ""
                }
            }
        },
        {
            "guide_id": guide_uuid,
            "title": "Create Sponsored-Only NTB Audience",
            "query_type": "main_analysis",
            "display_order": 4,
            "sql_query": """-- Rule-Based Audience: Sponsored Ads Only New-to-Brand Customers
-- Creates an audience of NTB customers with sponsored ads exposure but no DSP

SELECT DISTINCT 
    sa.user_id
FROM sponsored_ads_traffic_for_audiences sa
INNER JOIN amazon_attributed_events_by_conversion_time_for_audiences c
    ON sa.user_id = c.user_id
LEFT JOIN dsp_impressions_for_audiences dsp
    ON sa.user_id = dsp.user_id
    AND dsp.impression_dt BETWEEN {{start_date}} AND {{end_date}}
WHERE sa.click_dt BETWEEN {{start_date}} AND {{end_date}}
    AND c.conversion_event_dt BETWEEN {{start_date}} AND {{end_date}}
    AND c.new_to_brand_indicator = 'Y'
    AND dsp.user_id IS NULL  -- No DSP exposure
    {{keyword_filter}}
    {{value_filter}}
    {{asin_filter}}
GROUP BY sa.user_id
HAVING COUNT(DISTINCT sa.keyword) >= {{min_keywords}}""",
            "parameters_schema": {
                "start_date": {
                    "type": "date",
                    "description": "Start date for audience window",
                    "required": True,
                    "default": "2024-01-01T00:00:00"
                },
                "end_date": {
                    "type": "date",
                    "description": "End date for audience window",
                    "required": True,
                    "default": "2024-03-31T00:00:00"
                },
                "min_keywords": {
                    "type": "number",
                    "description": "Minimum number of unique keywords interacted with",
                    "required": True,
                    "default": 1
                },
                "keyword_filter": {
                    "type": "string",
                    "description": "Optional keyword filter (e.g., AND sa.keyword LIKE '%brand%')",
                    "required": False,
                    "default": ""
                },
                "value_filter": {
                    "type": "string",
                    "description": "Optional value filter for conversions",
                    "required": False,
                    "default": ""
                },
                "asin_filter": {
                    "type": "string",
                    "description": "Optional ASIN filter",
                    "required": False,
                    "default": ""
                }
            }
        }
    ]
    
    query_ids = {}
    for query in queries:
        # Convert parameters_schema to JSON string
        query['parameters_schema'] = json.dumps(query['parameters_schema'])
        result = supabase.table('build_guide_queries').upsert(query).execute()
        # Store query ID for examples
        query_title = query['title']
        query_ids[query_title] = result.data[0]['id']
    print(f"Created {len(queries)} queries")
    
    # Create examples
    examples = [
        {
            "guide_query_id": query_ids["Measurement Query - Size High-Value NTB Audiences"],
            "example_name": "Audience Size Measurement Results",
            "sample_data": {
                "rows": [
                    {
                        "metric_category": "Audience Size Estimates",
                        "total_ntb_customers": 125430,
                        "avg_purchase_value": 87.50,
                        "median_purchase_value": 65.00,
                        "p75_purchase_value": 105.00,
                        "p90_purchase_value": 175.00,
                        "high_value_customers": 31357,
                        "high_value_percentage": 25.00,
                        "organic_ntb_customers": 50172,
                        "organic_percentage": 40.00,
                        "sponsored_only_customers": 37629,
                        "sponsored_only_percentage": 30.00
                    }
                ]
            },
            "interpretation_markdown": """## Audience Size Analysis

### Key Findings
- **Total NTB Customer Base**: 125,430 customers identified as new-to-brand
- **High-Value Segment**: 31,357 customers (25%) exceed the $100 threshold
- **Organic Discovery**: 50,172 customers (40%) found the brand without ad exposure
- **Cross-Channel Opportunity**: 37,629 customers (30%) engaged with sponsored ads but not DSP

### Value Distribution Insights
- **Median Purchase**: $65 indicates broad market appeal
- **75th Percentile**: $105 suggests natural breakpoint for high-value segmentation
- **90th Percentile**: $175 represents premium customer segment

### Recommendations
1. **High-Value Audience**: Size of 31K is optimal for targeted DSP campaigns
2. **Organic Audience**: Large 50K segment indicates strong brand discovery
3. **Sponsored-Only**: 37K customers represent immediate DSP expansion opportunity""",
            "display_order": 1
        },
        {
            "guide_query_id": query_ids["Create High-Value NTB Audience"],
            "example_name": "High-Value Audience Creation Result",
            "sample_data": {
                "rows": [
                    {
                        "audience_name": "High_Value_NTB_Q1_2024",
                        "audience_status": "Created Successfully",
                        "total_users": 31357,
                        "sync_status": "Synced to DSP",
                        "refresh_schedule": "Daily at 2 AM UTC",
                        "last_updated": "2024-03-15 02:15:00"
                    }
                ]
            },
            "interpretation_markdown": """## Audience Creation Success

### Audience Details
- **Name**: High_Value_NTB_Q1_2024
- **Size**: 31,357 users successfully identified
- **DSP Sync**: Completed within 15 minutes
- **Refresh**: Set to daily for fresh audience data

### Next Steps
1. **Create DSP Campaign**: Target this audience with premium product messaging
2. **Set Frequency Cap**: Recommend 3-5 impressions per week
3. **Monitor Performance**: Track NTB conversion rate and ROAS
4. **Optimize**: Adjust value thresholds based on performance""",
            "display_order": 2
        }
    ]
    
    for example in examples:
        # Convert sample_data to JSON string
        example['sample_data'] = json.dumps(example['sample_data'])
        result = supabase.table('build_guide_examples').upsert(example).execute()
    print(f"Created {len(examples)} examples")
    
    # Create metrics
    metrics = [
        {
            "guide_id": guide_uuid,
            "metric_name": "total_ntb_customers",
            "display_name": "Total NTB Customers",
            "definition": "Count of unique customers identified as new-to-brand",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "avg_purchase_value",
            "display_name": "Average Purchase Value",
            "definition": "Mean purchase value for NTB customers",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "high_value_percentage",
            "display_name": "High-Value Percentage",
            "definition": "Percentage of NTB customers above value threshold",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "organic_percentage",
            "display_name": "Organic Discovery Rate",
            "definition": "Percentage of NTB customers without ad attribution",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "sponsored_only_percentage",
            "display_name": "Sponsored-Only Rate",
            "definition": "Percentage of NTB customers with sponsored ads but no DSP",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "new_to_brand_indicator",
            "display_name": "New-to-Brand Indicator",
            "definition": "Flag indicating if customer has not purchased in last 12 months (Y = New to brand, N = Existing customer)",
            "metric_type": "dimension"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "total_product_sales",
            "display_name": "Total Product Sales",
            "definition": "Total sales including promoted ASINs and brand halo",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "attribution_type",
            "display_name": "Attribution Type",
            "definition": "Type of attribution for the conversion (DSP, Sponsored Ads, Organic, Multi-Touch)",
            "metric_type": "dimension"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "user_id",
            "display_name": "User ID",
            "definition": "Hashed user identifier for privacy-compliant targeting",
            "metric_type": "dimension"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "audience_size",
            "display_name": "Audience Size",
            "definition": "Count of users in the created audience",
            "metric_type": "metric"
        }
    ]
    
    for metric in metrics:
        result = supabase.table('build_guide_metrics').upsert(metric).execute()
    print(f"Created {len(metrics)} metrics")
    
    print(f"Successfully seeded High-Value NTB Customer Audiences build guide!")

if __name__ == "__main__":
    seed_high_value_ntb_guide()