#!/usr/bin/env python
"""
Seed script for Amazon DSP Path to Conversion by Device build guide
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not supabase_url or not supabase_key:
    print("Error: Missing Supabase credentials")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

def clear_existing_guide(guide_id: str):
    """Clear existing guide and related data"""
    try:
        # Get guide UUID first
        guide_result = supabase.table('build_guides').select('id').eq('guide_id', guide_id).execute()
        if not guide_result.data:
            print(f"Guide {guide_id} does not exist")
            return
        
        guide_uuid = guide_result.data[0]['id']
        print(f"Found guide UUID: {guide_uuid}")
        
        # Delete related data first (using UUID for foreign key references)
        tables_with_guide_ref = [
            ('user_guide_favorites', 'guide_id'),
            ('user_guide_progress', 'guide_id'),
            ('build_guide_metrics', 'guide_id'),
            ('build_guide_examples', 'guide_id'),  # This actually references guide_query_id, will handle separately
            ('build_guide_queries', 'guide_id'),
            ('build_guide_sections', 'guide_id'),
        ]
        
        for table, column in tables_with_guide_ref:
            if table == 'build_guide_examples':
                continue  # Handle examples separately as they reference queries
            result = supabase.table(table).delete().eq(column, guide_uuid).execute()
            print(f"Cleared {table}")
        
        # Handle examples (they reference guide_query_id)
        queries = supabase.table('build_guide_queries').select('id').eq('guide_id', guide_uuid).execute()
        for query in queries.data:
            supabase.table('build_guide_examples').delete().eq('guide_query_id', query['id']).execute()
        print("Cleared build_guide_examples")
        
        # Finally delete the guide itself
        supabase.table('build_guides').delete().eq('id', guide_uuid).execute()
        print(f"Cleared guide: {guide_id}")
        
    except Exception as e:
        print(f"Error clearing guide: {e}")

def seed_dsp_device_path_guide():
    """Seed the DSP Path to Conversion by Device build guide"""
    
    guide_id = "guide_dsp_device_path"
    
    # Clear any existing guide
    clear_existing_guide(guide_id)
    
    # Create the main guide
    guide_data = {
        "guide_id": guide_id,
        "name": "Amazon DSP Path to Conversion by Device",
        "short_description": "Discover how users move between devices as they engage with your DSP ads and progress towards conversion to optimize device-specific experiences and ad strategies",
        "category": "Customer Journey Analysis",
        "difficulty_level": "advanced",
        "estimated_time_minutes": 45,
        "prerequisites": [
            "DSP campaigns with multi-device targeting",
            "At least 30 days of campaign data", 
            "Multiple device types in target audience",
            "Understanding of cross-device attribution"
        ],
        "tags": [
            "Customer journey",
            "Multi-device tracking",
            "DSP analysis",
            "Path to conversion",
            "Device optimization"
        ],
        "icon": "Smartphone",
        "is_published": True,
        "display_order": 2,
        "created_by": None
    }
    
    result = supabase.table('build_guides').insert(guide_data).execute()
    guide_uuid = result.data[0]['id']
    print(f"Created guide: {guide_id} with UUID: {guide_uuid}")
    
    # Create sections
    sections = [
        {
            "guide_id": guide_uuid,
            "section_id": "introduction",
            "title": "1. Introduction",
            "display_order": 1,
            "content_markdown": """## Purpose

Use this analysis to discover the ways users move between devices as they engage with your ads and progress towards conversion. These insights will help you optimize your device-specific experience and ad strategy to match the engagement activity you expect users to take on that device at certain steps in the conversion process.

## What You'll Learn

- **Device paths users took before converting**: Understand the complete device journey from first impression to conversion
- **Which device combinations have the highest conversion rates**: Identify the most effective multi-device strategies
- **Frequency and order of device exposures**: Learn how many times users see ads on each device and in what sequence
- **Performance metrics by device path**: Analyze impressions, cost, clicks, and conversions for each journey type
- **Multi-device strategy optimization opportunities**: Discover actionable insights to improve your cross-device campaigns

## Requirements

⚠️ **Important**: Advertisers should preferably have data from multiple devices (e.g., desktop, phone, tablet, TV). If your campaigns are targeting only one device type, the query will return results, but they will be limited to the single device and device journey insights will not be available.

### Minimum Data Requirements
- At least 2 different device types in your targeting
- 30+ days of campaign data for statistical significance
- Conversion tracking properly configured
- Cross-device attribution enabled in your DSP settings"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "data_query_instructions",
            "title": "2. Data Query Instructions",
            "display_order": 2,
            "content_markdown": """## Query Approaches

This guide provides two query approaches to analyze device paths:

### 1. Simplified Path Analysis
**Purpose**: Provides a high-level view of unique device combinations in conversion paths

**Key Features**:
- Shows unique devices used (not ordered)
- Aggregates all paths with same device combination
- Easier to interpret for strategic decisions
- Best for understanding device mix impact

**Use When**:
- You need quick insights on device combinations
- Order of device exposure is less important
- Focusing on overall device strategy

### 2. Detailed Path Analysis
**Purpose**: Returns the complete device journey with sequencing and frequency

**Key Features**:
- Shows exact order of device exposures
- Includes frequency of exposures per device
- Reveals sequential patterns in customer journey
- Best for tactical optimization

**Use When**:
- You need to understand the exact customer journey
- Device sequencing matters for your strategy
- Planning sequential messaging across devices

## Key Technical Differences

| Aspect | Simplified Query | Detailed Query |
|--------|-----------------|----------------|
| **Path Structure** | `NAMED_ROW('device', device_type)` | `NAMED_ROW('order', ROW_NUMBER(), 'device_type', device_type)` |
| **Aggregation** | Groups by unique device combination | Preserves full sequential path |
| **Output Complexity** | Fewer rows, easier analysis | More rows, detailed insights |
| **Performance** | Faster execution | Slower due to window functions |

## Tables Used

### Primary Tables
- **dsp_impressions**: DSP impression data with device information
- **dsp_clicks**: DSP click data for engagement metrics  
- **amazon_attributed_events_by_traffic_time**: Conversion events

### Join Conditions
- User-level joins on `user_id`
- Time-based filtering for attribution window
- Device type extraction from impression data

⚠️ **Data Lag Notice**: Wait at least 14 days after campaign end for complete attribution data in `amazon_attributed_events_by_traffic_time` table."""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "parameter_configuration",
            "title": "3. Parameter Configuration",
            "display_order": 3,
            "content_markdown": """## Required Parameters

Configure these parameters before running the queries:

### Date Range Parameters
```sql
-- Campaign analysis period
start_date = '2024-01-01T00:00:00'
end_date = '2024-03-31T23:59:59'

-- Attribution window (typically 14 days)
attribution_window_days = 14
```

### Campaign Filters
```sql
-- Filter by specific campaigns (optional)
campaign_ids = ['campaign_123', 'campaign_456']  -- Leave empty for all campaigns

-- Filter by advertiser
advertiser_id = 'your_advertiser_id'
```

### Device Configuration
```sql
-- Device types to include in analysis
included_devices = ['PC', 'Phone', 'Tablet', 'TV', 'Other']

-- Minimum impressions per device to include in path
min_impressions_per_device = 1
```

### Path Analysis Settings
```sql
-- Maximum path length to consider
max_path_length = 10

-- Minimum path occurrences to include in results
min_path_occurrences = 5

-- Include non-converting paths
include_non_converters = false
```

## Advanced Configuration

### Custom Device Grouping
You can create custom device categories:

```sql
CASE 
    WHEN device_type IN ('PC', 'Laptop') THEN 'Desktop'
    WHEN device_type IN ('Phone', 'Mobile') THEN 'Mobile'
    WHEN device_type = 'Tablet' THEN 'Tablet'
    WHEN device_type IN ('TV', 'CTV', 'OTT') THEN 'Connected TV'
    ELSE 'Other'
END AS device_category
```

### Attribution Model Selection
Choose your attribution model:
- **Last Touch**: Credit to final device before conversion
- **Multi-Touch**: Distribute credit across all devices
- **Time Decay**: More credit to recent devices
- **Custom**: Define your own attribution logic"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "data_interpretation",
            "title": "4. Data Interpretation Instructions",
            "display_order": 4,
            "content_markdown": """## Understanding Your Results

### Path Notation Guide

**Simplified Path Format**: `[[Device1], [Device2], [Device3]]`
- Shows unique devices in the path
- Order may not reflect actual sequence
- Same device appearing multiple times counted once

**Detailed Path Format**: `[[1, Device1], [2, Device2], [3, Device2], [4, Device3]]`
- Number indicates touchpoint order
- Same device can appear multiple times
- Shows exact customer journey sequence

### Key Metrics Explained

| Metric | Definition | How to Use |
|--------|------------|------------|
| **path_occurrences** | Number of users following this path | Identify most common journeys |
| **impressions** | Total ad impressions in this path | Measure exposure intensity |
| **imp_total_cost** | Total media cost for path | Calculate path efficiency |
| **users_that_purchased** | Converters following this path | Measure path effectiveness |
| **conversion_rate** | users_that_purchased / path_occurrences | Compare path performance |
| **roas_sales_amount_brand** | Brand sales / imp_total_cost | Evaluate ROI by path |

## Strategic Insights Framework

### 1. Device Role Analysis
Identify the role each device plays in the conversion journey:

- **Initiators**: Devices that commonly start journeys
- **Assisters**: Devices that appear mid-journey
- **Closers**: Devices where conversions happen
- **Amplifiers**: Devices that increase conversion when added

### 2. Path Efficiency Metrics

Calculate these derived metrics for deeper insights:

```sql
-- Cost per conversion by path
cost_per_conversion = imp_total_cost / users_that_purchased

-- Average impressions per converter
impressions_per_converter = impressions / users_that_purchased

-- Path conversion index (vs. average)
conversion_index = (path_conversion_rate / overall_conversion_rate) * 100
```

### 3. Journey Complexity Analysis

Categorize paths by complexity:
- **Simple Paths** (1-2 devices): Direct response focused
- **Moderate Paths** (3-4 devices): Consideration journey
- **Complex Paths** (5+ devices): Extended decision process

## Actionable Recommendations

### For High-Performing Paths
✅ **Increase Investment**: Scale budget for device combinations showing high ROAS
✅ **Protect Frequency**: Maintain optimal impression levels per device
✅ **Expand Reach**: Find similar audiences on these device combinations

### For Underperforming Paths
⚠️ **Optimize Creative**: Test device-specific messaging
⚠️ **Adjust Timing**: Review dayparting by device
⚠️ **Reduce Waste**: Lower frequency caps or exclude poor combinations

### For Missing Paths
🔍 **Identify Gaps**: Look for device combinations you're not reaching
🔍 **Test New Combinations**: Pilot campaigns for untapped paths
🔍 **Cross-Device Targeting**: Enable device graph connections"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "optimization_strategies",
            "title": "5. Optimization Strategies",
            "display_order": 5,
            "content_markdown": """## Device-Specific Optimization Strategies

### 1. Sequential Messaging Strategy

Based on your path analysis, implement sequential messaging:

| Journey Stage | Common Device | Message Focus | Creative Format |
|--------------|---------------|---------------|-----------------|
| **Awareness** | TV, Desktop | Brand introduction | Video, rich media |
| **Consideration** | Mobile, Tablet | Product details | Interactive, carousel |
| **Decision** | Desktop, Mobile | Offers, urgency | Dynamic, personalized |
| **Conversion** | Desktop | Checkout ease | Retargeting, abandoned cart |

### 2. Budget Allocation Framework

Use path performance to optimize budget distribution:

```
High ROAS Paths (>3.0): 40-50% of budget
Medium ROAS Paths (1.5-3.0): 30-40% of budget
Test/Growth Paths (<1.5): 10-20% of budget
```

### 3. Frequency Management by Device

Optimize frequency caps based on path analysis:

| Device Type | Role in Journey | Recommended Daily Cap | Weekly Cap |
|------------|-----------------|---------------------|------------|
| **Desktop** | Initiator/Closer | 3-4 impressions | 15-20 |
| **Mobile** | Assister | 4-6 impressions | 20-25 |
| **Tablet** | Consideration | 2-3 impressions | 10-15 |
| **CTV/OTT** | Awareness | 2-3 impressions | 8-12 |

## Advanced Optimization Techniques

### Cross-Device Attribution Optimization

1. **Implement Device Graphs**: Enable Amazon's device graph for better cross-device tracking
2. **Adjust Attribution Windows**: Test 7, 14, and 30-day windows based on path length
3. **Custom Attribution Models**: Weight devices based on their role in your specific paths

### Dynamic Creative Optimization (DCO)

Customize creative elements by device position in path:

```javascript
if (devicePosition === 'first_touch') {
    // Broad awareness messaging
    creative = brandAwarenessTemplate;
} else if (devicePosition === 'middle_touches') {
    // Product benefits and differentiation
    creative = productComparisonTemplate;
} else if (devicePosition === 'last_touch') {
    // Conversion-focused with offers
    creative = conversionTemplate;
}
```

### Audience Segmentation by Path

Create audience segments based on device journey patterns:

- **Multi-Device Power Users**: Target users with 4+ device touchpoints
- **Mobile-First Converters**: Users who primarily engage via mobile
- **Desktop Closers**: Users who browse mobile but convert on desktop
- **CTV Initiators**: Users whose journeys begin with TV exposure

## Testing Framework

### A/B Testing Recommendations

Test these hypotheses based on your path data:

1. **Device Sequence Testing**: Change order of device targeting
2. **Frequency Testing**: Vary impressions per device in path
3. **Creative Rotation**: Test different creative sequences
4. **Dayparting by Device**: Optimize timing per device type

### Measurement Best Practices

- Run tests for minimum 2 weeks for statistical significance
- Control for seasonality and external factors
- Use holdout groups to measure incremental impact
- Document learnings for future campaigns"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "troubleshooting",
            "title": "6. Troubleshooting",
            "display_order": 6,
            "content_markdown": """## Common Issues and Solutions

### Issue 1: No Data Returned

**Symptoms**: Query returns empty results

**Possible Causes & Solutions**:
- ✅ **Check date range**: Ensure dates are within available data period
- ✅ **Verify campaign IDs**: Confirm campaigns exist and have impressions
- ✅ **Attribution window**: Data may not be available yet (14-day lag)
- ✅ **Device data**: Verify device_type field is populated in impressions

### Issue 2: Single Device Paths Only

**Symptoms**: All paths show only one device type

**Possible Causes & Solutions**:
- ✅ **Campaign targeting**: Check if campaigns target multiple devices
- ✅ **User matching**: Verify cross-device user identification is working
- ✅ **Time window**: Expand analysis period to capture more touchpoints
- ✅ **Device graph**: Enable Amazon's device graph for better matching

### Issue 3: Unexpected High/Low Conversion Rates

**Symptoms**: Conversion rates seem incorrect

**Possible Causes & Solutions**:
- ✅ **Attribution logic**: Review conversion attribution window
- ✅ **Deduplication**: Check for duplicate conversion events
- ✅ **Conversion definition**: Verify what constitutes a conversion
- ✅ **Time alignment**: Ensure impression and conversion dates align

### Issue 4: Performance Timeout

**Symptoms**: Query times out or runs very slowly

**Optimization Solutions**:
```sql
-- 1. Add date partition filters
WHERE impression_date >= '2024-01-01'
  AND impression_date <= '2024-03-31'

-- 2. Limit path length
HAVING COUNT(DISTINCT device_type) <= 5

-- 3. Sample data for testing
TABLESAMPLE BERNOULLI (10)  -- 10% sample

-- 4. Pre-aggregate impressions
WITH daily_impressions AS (
    SELECT user_id, device_type, DATE(impression_time) as day,
           COUNT(*) as daily_imps
    FROM dsp_impressions
    GROUP BY 1,2,3
)
```

## Data Quality Checks

### Pre-Query Validation

Run these checks before your main analysis:

```sql
-- Check device type coverage
SELECT device_type, COUNT(*) as count
FROM dsp_impressions
WHERE campaign_id IN (your_campaigns)
GROUP BY 1
ORDER BY 2 DESC;

-- Verify conversion data exists
SELECT COUNT(*) as conversion_count
FROM amazon_attributed_events_by_traffic_time
WHERE advertiser = 'your_advertiser'
  AND purchase_flag = true;

-- Check for user_id population
SELECT 
    COUNT(*) as total_impressions,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(CASE WHEN user_id IS NULL THEN 1 END) as null_users
FROM dsp_impressions;
```

### Post-Query Validation

Verify your results make sense:

- ✅ Sum of path_occurrences should equal unique users analyzed
- ✅ Conversion rates should be between 0-100%
- ✅ ROAS values should align with business expectations
- ✅ Most common paths should reflect campaign targeting

## Query Optimization Tips

### Index Recommendations
Ensure these indexes exist for optimal performance:
- `dsp_impressions(user_id, impression_time, device_type)`
- `dsp_impressions(campaign_id, advertiser)`
- `amazon_attributed_events_by_traffic_time(user_id, conversion_time)`

### Partitioning Strategy
If available, partition tables by:
- Date (daily or monthly)
- Advertiser ID
- Campaign ID

### Memory Management
For large datasets:
- Process in date chunks
- Use temporary tables for intermediate results
- Clear cache between runs"""
        }
    ]
    
    # Add default values for sections
    for section in sections:
        section["is_collapsible"] = True
        section["default_expanded"] = True
        result = supabase.table('build_guide_sections').insert(section).execute()
    print(f"Created {len(sections)} sections")
    
    # Create queries
    queries = [
        {
            "guide_id": guide_uuid,
            "title": "Simplified Device Path Analysis",
            "description": "Analyzes unique device combinations in conversion paths without considering order or frequency",
            "query_type": "main_analysis",
            "sql_query": """-- Simplified Device Path to Conversion Analysis
-- This query identifies unique device combinations used in conversion paths

WITH user_device_paths AS (
    -- Get all devices each user was exposed to before conversion
    SELECT 
        i.user_id,
        ARRAY_AGG(DISTINCT 
            NAMED_ROW('device', i.device_type)
            ORDER BY i.device_type
        ) AS device_path,
        COUNT(DISTINCT i.impression_id) AS total_impressions,
        SUM(i.total_cost) AS total_cost,
        MAX(CASE WHEN c.purchase_flag = true THEN 1 ELSE 0 END) AS converted,
        COALESCE(SUM(c.purchases), 0) AS total_purchases,
        COALESCE(SUM(c.branded_purchases), 0) AS branded_purchases
    FROM dsp_impressions i
    LEFT JOIN amazon_attributed_events_by_traffic_time c
        ON i.user_id = c.user_id
        AND c.conversion_time >= i.impression_time
        AND c.conversion_time <= i.impression_time + INTERVAL {{attribution_window_days}} DAY
    WHERE i.campaign_id IN ({{campaign_ids}})
        AND i.advertiser = {{advertiser_id}}
        AND i.impression_time >= {{start_date}}
        AND i.impression_time <= {{end_date}}
        AND i.device_type IN ({{included_devices}})
    GROUP BY i.user_id
    HAVING COUNT(DISTINCT i.device_type) >= 1
),

path_aggregation AS (
    -- Aggregate metrics by device path
    SELECT 
        device_path AS path,
        COUNT(*) AS path_occurrences,
        SUM(total_impressions) AS impressions,
        ROUND(SUM(total_cost), 2) AS imp_total_cost,
        SUM(converted) AS users_that_purchased,
        SUM(total_purchases) AS sales_amount,
        SUM(branded_purchases) AS sales_amount_brand,
        ROUND(AVG(converted), 5) AS conversion_rate,
        CASE 
            WHEN SUM(total_cost) > 0 
            THEN ROUND(SUM(branded_purchases) / SUM(total_cost), 2)
            ELSE 0 
        END AS roas_sales_amount_brand
    FROM user_device_paths
    GROUP BY device_path
    HAVING COUNT(*) >= {{min_path_occurrences}}
)

SELECT 
    path,
    path_occurrences,
    impressions,
    imp_total_cost,
    users_that_purchased,
    sales_amount,
    sales_amount_brand,
    conversion_rate,
    roas_sales_amount_brand,
    -- Additional calculated metrics
    ROUND(imp_total_cost / NULLIF(users_that_purchased, 0), 2) AS cost_per_conversion,
    ROUND(impressions / NULLIF(path_occurrences, 0), 1) AS avg_impressions_per_user,
    ARRAY_LENGTH(path) AS devices_in_path
FROM path_aggregation
ORDER BY path_occurrences DESC
LIMIT 100;""",
            "parameters_schema": {
                "attribution_window_days": {
                    "type": "integer",
                    "default": 14,
                    "definition": "Attribution window in days"
                },
                "campaign_ids": {
                    "type": "array",
                    "definition": "List of campaign IDs to analyze"
                },
                "advertiser_id": {
                    "type": "string",
                    "definition": "Advertiser identifier"
                },
                "start_date": {
                    "type": "datetime",
                    "definition": "Analysis start date"
                },
                "end_date": {
                    "type": "datetime",
                    "definition": "Analysis end date"
                },
                "included_devices": {
                    "type": "array",
                    "default": ["PC", "Phone", "Tablet", "TV", "Other"],
                    "definition": "Device types to include"
                },
                "min_path_occurrences": {
                    "type": "integer",
                    "default": 5,
                    "definition": "Minimum path occurrences to include"
                }
            }
        },
        {
            "guide_id": guide_uuid,
            "title": "Detailed Device Path Analysis",
            "description": "Returns complete device journey with sequencing and frequency of exposures",
            "query_type": "main_analysis",
            "sql_query": """-- Detailed Device Path to Conversion Analysis
-- This query captures the complete sequential device journey including repeat exposures

WITH user_touchpoints AS (
    -- Get all device touchpoints with order
    SELECT 
        i.user_id,
        i.device_type,
        i.impression_time,
        i.impression_id,
        i.total_cost,
        ROW_NUMBER() OVER (
            PARTITION BY i.user_id 
            ORDER BY i.impression_time
        ) AS touchpoint_order,
        c.purchase_flag,
        c.purchases,
        c.branded_purchases
    FROM dsp_impressions i
    LEFT JOIN amazon_attributed_events_by_traffic_time c
        ON i.user_id = c.user_id
        AND c.conversion_time >= i.impression_time
        AND c.conversion_time <= i.impression_time + INTERVAL {{attribution_window_days}} DAY
    WHERE i.campaign_id IN ({{campaign_ids}})
        AND i.advertiser = {{advertiser_id}}
        AND i.impression_time >= {{start_date}}
        AND i.impression_time <= {{end_date}}
        AND i.device_type IN ({{included_devices}})
),

user_device_sequences AS (
    -- Build sequential device paths for each user
    SELECT 
        user_id,
        ARRAY_AGG(
            NAMED_ROW('order', touchpoint_order, 'device_type', device_type)
            ORDER BY touchpoint_order
            LIMIT {{max_path_length}}
        ) AS device_sequence,
        COUNT(DISTINCT impression_id) AS total_impressions,
        SUM(total_cost) AS total_cost,
        MAX(CASE WHEN purchase_flag = true THEN 1 ELSE 0 END) AS converted,
        COALESCE(SUM(purchases), 0) AS total_purchases,
        COALESCE(SUM(branded_purchases), 0) AS branded_purchases,
        -- Device frequency counts
        COUNT(CASE WHEN device_type = 'PC' THEN 1 END) AS pc_exposures,
        COUNT(CASE WHEN device_type = 'Phone' THEN 1 END) AS phone_exposures,
        COUNT(CASE WHEN device_type = 'Tablet' THEN 1 END) AS tablet_exposures,
        COUNT(CASE WHEN device_type = 'TV' THEN 1 END) AS tv_exposures
    FROM user_touchpoints
    GROUP BY user_id
),

path_aggregation AS (
    -- Aggregate metrics by sequential path
    SELECT 
        device_sequence AS path,
        COUNT(*) AS path_occurrences,
        SUM(total_impressions) AS impressions,
        ROUND(SUM(total_cost), 2) AS imp_total_cost,
        SUM(converted) AS users_that_purchased,
        SUM(total_purchases) AS sales_amount,
        SUM(branded_purchases) AS sales_amount_brand,
        ROUND(AVG(converted), 5) AS conversion_rate,
        CASE 
            WHEN SUM(total_cost) > 0 
            THEN ROUND(SUM(branded_purchases) / SUM(total_cost), 2)
            ELSE 0 
        END AS roas_sales_amount_brand,
        -- Average device exposures
        ROUND(AVG(pc_exposures), 1) AS avg_pc_exposures,
        ROUND(AVG(phone_exposures), 1) AS avg_phone_exposures,
        ROUND(AVG(tablet_exposures), 1) AS avg_tablet_exposures,
        ROUND(AVG(tv_exposures), 1) AS avg_tv_exposures
    FROM user_device_sequences
    GROUP BY device_sequence
    HAVING COUNT(*) >= {{min_path_occurrences}}
)

SELECT 
    path,
    path_occurrences,
    impressions,
    imp_total_cost,
    users_that_purchased,
    sales_amount,
    sales_amount_brand,
    conversion_rate,
    roas_sales_amount_brand,
    -- Additional metrics
    ROUND(imp_total_cost / NULLIF(users_that_purchased, 0), 2) AS cost_per_conversion,
    ROUND(impressions / NULLIF(path_occurrences, 0), 1) AS avg_impressions_per_user,
    ARRAY_LENGTH(path) AS touchpoints_in_path,
    -- Device exposure averages
    avg_pc_exposures,
    avg_phone_exposures,
    avg_tablet_exposures,
    avg_tv_exposures
FROM path_aggregation
ORDER BY path_occurrences DESC
LIMIT 100;""",
            "parameters_schema": {
                "attribution_window_days": {
                    "type": "integer",
                    "default": 14,
                    "definition": "Attribution window in days"
                },
                "campaign_ids": {
                    "type": "array",
                    "definition": "List of campaign IDs to analyze"
                },
                "advertiser_id": {
                    "type": "string",
                    "definition": "Advertiser identifier"
                },
                "start_date": {
                    "type": "datetime",
                    "definition": "Analysis start date"
                },
                "end_date": {
                    "type": "datetime",
                    "definition": "Analysis end date"
                },
                "included_devices": {
                    "type": "array",
                    "default": ["PC", "Phone", "Tablet", "TV", "Other"],
                    "definition": "Device types to include"
                },
                "min_path_occurrences": {
                    "type": "integer",
                    "default": 5,
                    "definition": "Minimum path occurrences to include"
                },
                "max_path_length": {
                    "type": "integer",
                    "default": 10,
                    "definition": "Maximum number of touchpoints to track"
                }
            }
        },
        {
            "guide_id": guide_uuid,
            "title": "Device Role Analysis",
            "description": "Analyzes the role each device plays in the conversion journey (initiator, assister, closer)",
            "query_type": "exploratory",
            "sql_query": """-- Device Role Analysis
-- Identifies which devices typically initiate, assist, or close conversion journeys

WITH user_journeys AS (
    -- Get first, last, and all devices for each converting user
    SELECT 
        i.user_id,
        FIRST_VALUE(i.device_type) OVER (
            PARTITION BY i.user_id 
            ORDER BY i.impression_time
        ) AS first_device,
        LAST_VALUE(i.device_type) OVER (
            PARTITION BY i.user_id 
            ORDER BY i.impression_time
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS last_device,
        i.device_type AS touch_device,
        ROW_NUMBER() OVER (
            PARTITION BY i.user_id 
            ORDER BY i.impression_time
        ) AS touch_position,
        COUNT(*) OVER (PARTITION BY i.user_id) AS total_touches
    FROM dsp_impressions i
    INNER JOIN amazon_attributed_events_by_traffic_time c
        ON i.user_id = c.user_id
        AND c.purchase_flag = true
        AND c.conversion_time >= i.impression_time
        AND c.conversion_time <= i.impression_time + INTERVAL {{attribution_window_days}} DAY
    WHERE i.campaign_id IN ({{campaign_ids}})
        AND i.advertiser = {{advertiser_id}}
        AND i.impression_time >= {{start_date}}
        AND i.impression_time <= {{end_date}}
)

SELECT 
    device_type,
    -- Role metrics
    COUNT(CASE WHEN device_type = first_device THEN 1 END) AS times_as_initiator,
    COUNT(CASE WHEN device_type = last_device THEN 1 END) AS times_as_closer,
    COUNT(CASE WHEN touch_position > 1 AND touch_position < total_touches THEN 1 END) AS times_as_assister,
    COUNT(*) AS total_touchpoints,
    
    -- Role percentages
    ROUND(COUNT(CASE WHEN device_type = first_device THEN 1 END) * 100.0 / COUNT(*), 2) AS pct_initiator,
    ROUND(COUNT(CASE WHEN device_type = last_device THEN 1 END) * 100.0 / COUNT(*), 2) AS pct_closer,
    ROUND(COUNT(CASE WHEN touch_position > 1 AND touch_position < total_touches THEN 1 END) * 100.0 / COUNT(*), 2) AS pct_assister,
    
    -- Average position in journey
    ROUND(AVG(touch_position * 1.0 / total_touches), 3) AS avg_relative_position
    
FROM (
    SELECT DISTINCT 
        user_id,
        touch_device AS device_type,
        first_device,
        last_device,
        touch_position,
        total_touches
    FROM user_journeys
) device_roles
GROUP BY device_type
ORDER BY total_touchpoints DESC;""",
            "parameters_schema": {
                "attribution_window_days": {
                    "type": "integer",
                    "default": 14,
                    "definition": "Attribution window in days"
                },
                "campaign_ids": {
                    "type": "array",
                    "definition": "List of campaign IDs to analyze"
                },
                "advertiser_id": {
                    "type": "string",
                    "definition": "Advertiser identifier"
                },
                "start_date": {
                    "type": "datetime",
                    "definition": "Analysis start date"
                },
                "end_date": {
                    "type": "datetime",
                    "definition": "Analysis end date"
                }
            }
        }
    ]
    
    for query in queries:
        # Convert parameters_schema to JSON string and add missing fields
        if 'parameters_schema' in query:
            query['parameters_schema'] = query['parameters_schema']
            query['default_parameters'] = {}
            # Extract default values for default_parameters
            for param, config in query['parameters_schema'].items():
                if 'default' in config:
                    query['default_parameters'][param] = config['default']
        
        # Add missing fields
        query['display_order'] = len([q for q in queries if queries.index(q) <= queries.index(query)]) + 1
        query['interpretation_notes'] = query.get('description', '')
        
        result = supabase.table('build_guide_queries').insert(query).execute()
        # Store the query ID for examples
        if query['query_type'] == 'main_analysis' and 'Simplified' in query['title']:
            simplified_query_id = result.data[0]['id']
        elif query['query_type'] == 'main_analysis' and 'Detailed' in query['title']:
            detailed_query_id = result.data[0]['id']  
        elif query['query_type'] == 'exploratory':
            device_role_query_id = result.data[0]['id']
    
    print(f"Created {len(queries)} queries")
    
    # Create examples with correct references
    examples = [
        {
            "guide_query_id": simplified_query_id,
            "example_name": "Simplified Path Analysis Results",
            "sample_data": {
                "rows": [
                    {
                        "path": "[[PC], [Phone], [TV]]",
                        "path_occurrences": 25732,
                        "impressions": 936365,
                        "imp_total_cost": 3804.55,
                        "users_that_purchased": 726,
                        "sales_amount": 6534,
                        "sales_amount_brand": 9801,
                        "conversion_rate": 0.02821,
                        "roas_sales_amount_brand": 2.58,
                        "cost_per_conversion": 5.24,
                        "avg_impressions_per_user": 36.4,
                        "devices_in_path": 3
                    },
                    {
                        "path": "[[PC], [Phone], [TV], [Tablet]]",
                        "path_occurrences": 988,
                        "impressions": 44441,
                        "imp_total_cost": 270.95,
                        "users_that_purchased": 33,
                        "sales_amount": 330,
                        "sales_amount_brand": 693,
                        "conversion_rate": 0.03340,
                        "roas_sales_amount_brand": 2.56,
                        "cost_per_conversion": 8.21,
                        "avg_impressions_per_user": 45.0,
                        "devices_in_path": 4
                    },
                    {
                        "path": "[[PC], [Phone], [Tablet]]",
                        "path_occurrences": 213,
                        "impressions": 51073,
                        "imp_total_cost": 127.42,
                        "users_that_purchased": 3,
                        "sales_amount": 45,
                        "sales_amount_brand": 54,
                        "conversion_rate": 0.01408,
                        "roas_sales_amount_brand": 0.42,
                        "cost_per_conversion": 42.47,
                        "avg_impressions_per_user": 239.8,
                        "devices_in_path": 3
                    },
                    {
                        "path": "[[PC], [Phone]]",
                        "path_occurrences": 7,
                        "impressions": 2099,
                        "imp_total_cost": 6.24,
                        "users_that_purchased": 0,
                        "sales_amount": 0,
                        "sales_amount_brand": 0,
                        "conversion_rate": 0.00000,
                        "roas_sales_amount_brand": 0.00,
                        "cost_per_conversion": None,
                        "avg_impressions_per_user": 299.9,
                        "devices_in_path": 2
                    }
                ]
            },
            "interpretation_markdown": """## Key Findings from Simplified Path Analysis

### Top Performing Path
The **PC → Phone → TV** combination dominates with:
- **25,732 users** following this path (95% of analyzed paths)
- **2.82% conversion rate** with 726 converters
- **$2.58 ROAS** indicating strong profitability
- **$5.24 cost per conversion** - very efficient

### Adding Tablet Improves Conversion
When Tablet is added to the mix (PC → Phone → TV → Tablet):
- **Conversion rate increases to 3.34%** (18% improvement)
- ROAS remains strong at $2.56
- However, only 988 users followed this path
- **Recommendation**: Test increasing Tablet exposure

### Warning Signs
The PC → Phone → Tablet path shows concerning metrics:
- Very low conversion rate (1.41%)
- Poor ROAS (0.42)
- High cost per conversion ($42.47)
- **Action**: Consider excluding this specific combination or adjusting strategy

### Strategic Implications
1. **Core Strategy**: Focus on PC + Phone + TV combination
2. **Growth Opportunity**: Expand Tablet presence in successful paths
3. **Optimization**: Review creative and targeting for underperforming paths"""
        },
        {
            "guide_query_id": detailed_query_id,
            "example_name": "Detailed Path Analysis Results",
            "sample_data": {
                "rows": [
                    {
                        "path": "[[1, PC], [2, Phone], [3, Phone], [4, Phone], [5, TV]]",
                        "path_occurrences": 25732,
                        "impressions": 77196,
                        "imp_total_cost": 3804.55,
                        "users_that_purchased": 726,
                        "sales_amount": 6534,
                        "sales_amount_brand": 9801,
                        "conversion_rate": 0.02821,
                        "roas_sales_amount_brand": 2.58,
                        "cost_per_conversion": 5.24,
                        "avg_impressions_per_user": 3.0,
                        "touchpoints_in_path": 5,
                        "avg_pc_exposures": 1.0,
                        "avg_phone_exposures": 3.0,
                        "avg_tablet_exposures": 0.0,
                        "avg_tv_exposures": 1.0
                    },
                    {
                        "path": "[[1, PC], [2, Phone], [3, TV], [4, TV], [5, Tablet]]",
                        "path_occurrences": 988,
                        "impressions": 3952,
                        "imp_total_cost": 270.95,
                        "users_that_purchased": 33,
                        "sales_amount": 330,
                        "sales_amount_brand": 693,
                        "conversion_rate": 0.03340,
                        "roas_sales_amount_brand": 2.56,
                        "cost_per_conversion": 8.21,
                        "avg_impressions_per_user": 4.0,
                        "touchpoints_in_path": 5,
                        "avg_pc_exposures": 1.0,
                        "avg_phone_exposures": 1.0,
                        "avg_tablet_exposures": 1.0,
                        "avg_tv_exposures": 2.0
                    },
                    {
                        "path": "[[1, PC], [2, PC], [3, Phone], [4, Tablet]]",
                        "path_occurrences": 213,
                        "impressions": 630,
                        "imp_total_cost": 127.42,
                        "users_that_purchased": 3,
                        "sales_amount": 45,
                        "sales_amount_brand": 54,
                        "conversion_rate": 0.01408,
                        "roas_sales_amount_brand": 0.42,
                        "cost_per_conversion": 42.47,
                        "avg_impressions_per_user": 3.0,
                        "touchpoints_in_path": 4,
                        "avg_pc_exposures": 2.0,
                        "avg_phone_exposures": 1.0,
                        "avg_tablet_exposures": 1.0,
                        "avg_tv_exposures": 0.0
                    }
                ]
            },
            "interpretation_markdown": """## Sequential Journey Insights

### Discovery: Phone Frequency Drives Conversion
The top path reveals critical sequencing:
1. **PC initiates** the journey (touchpoint 1)
2. **Phone dominates mid-journey** (touchpoints 2-4, avg 3 exposures)
3. **TV closes** the conversion (touchpoint 5)

This 5-touchpoint journey with repeated Phone exposure achieves:
- 2.82% conversion rate
- $2.58 ROAS
- Only $5.24 cost per conversion

### TV Repetition Pattern
Second best path shows different pattern:
1. PC starts journey
2. Phone provides single touchpoint
3. **TV gets repeated exposure** (touchpoints 3-4)
4. Tablet completes journey

Key insight: **Double TV exposure** before Tablet increases conversion to 3.34%

### Failed Pattern to Avoid
The PC → PC → Phone → Tablet sequence performs poorly:
- Double PC exposure at start may indicate wrong audience
- Lacks TV component present in successful paths
- Only 1.41% conversion rate

### Optimization Recommendations

**Frequency Management**:
- Set Phone frequency to 3x for users who've seen PC ads
- Allow 2x TV exposure after Phone engagement
- Cap PC at 1x to avoid waste

**Sequential Messaging**:
1. PC: Broad awareness creative
2. Phone (3x): Product education with increasing urgency
3. TV: Brand reinforcement and social proof
4. Tablet/Final: Conversion-focused with offers"""
        },
        {
            "guide_query_id": device_role_query_id,
            "example_name": "Device Role Analysis Results",
            "sample_data": {
                "rows": [
                    {
                        "device_type": "PC",
                        "times_as_initiator": 45623,
                        "times_as_closer": 8234,
                        "times_as_assister": 12456,
                        "total_touchpoints": 66313,
                        "pct_initiator": 68.79,
                        "pct_closer": 12.41,
                        "pct_assister": 18.78,
                        "avg_relative_position": 0.284
                    },
                    {
                        "device_type": "Phone",
                        "times_as_initiator": 12456,
                        "times_as_closer": 18234,
                        "times_as_assister": 54623,
                        "total_touchpoints": 85313,
                        "pct_initiator": 14.60,
                        "pct_closer": 21.37,
                        "pct_assister": 64.03,
                        "avg_relative_position": 0.512
                    },
                    {
                        "device_type": "TV",
                        "times_as_initiator": 3456,
                        "times_as_closer": 28456,
                        "times_as_assister": 8901,
                        "total_touchpoints": 40813,
                        "pct_initiator": 8.47,
                        "pct_closer": 69.73,
                        "pct_assister": 21.81,
                        "avg_relative_position": 0.742
                    },
                    {
                        "device_type": "Tablet",
                        "times_as_initiator": 1234,
                        "times_as_closer": 4567,
                        "times_as_assister": 3456,
                        "total_touchpoints": 9257,
                        "pct_initiator": 13.33,
                        "pct_closer": 49.33,
                        "pct_assister": 37.33,
                        "avg_relative_position": 0.623
                    }
                ]
            },
            "interpretation_markdown": """## Device Role Strategic Insights

### Clear Role Definition Emerges

**PC = Journey Initiator** (68.79% of the time)
- Dominates as first touchpoint
- Average position: 28.4% through journey
- **Strategy**: Use for awareness and interest generation

**Phone = Universal Assister** (64.03% of the time)
- Critical mid-journey device
- Average position: 51.2% (exactly middle)
- **Strategy**: Focus on consideration and education content

**TV = Conversion Closer** (69.73% of the time)
- Strongest closing device
- Average position: 74.2% through journey
- **Strategy**: Deploy for final push with emotional/brand content

**Tablet = Flexible Closer** (49.33% closing rate)
- Can play multiple roles effectively
- Average position: 62.3% through journey
- **Strategy**: Use as alternative closer when TV unavailable

### Strategic Implementation

**Budget Allocation by Role**:
- Initiators (PC): 25% of budget for broad reach
- Assisters (Phone): 40% of budget for frequency building
- Closers (TV/Tablet): 35% of budget for conversion focus

**Creative Strategy by Device Role**:
- PC: Eye-catching visuals, problem identification
- Phone: Interactive formats, product details, reviews
- TV: Emotional storytelling, urgency messaging
- Tablet: Long-form content, comparison tools"""
        }
    ]
    
    for i, example in enumerate(examples):
        # Add missing fields
        example['display_order'] = i + 1
        example['insights'] = []  # Will be populated later if needed
        # sample_data and interpretation_markdown are already in the correct format
        result = supabase.table('build_guide_examples').insert(example).execute()
    print(f"Created {len(examples)} examples")
    
    # Create metrics
    metrics = [
        {
            "guide_id": guide_uuid,
            "metric_name": "path",
            "display_name": "Device Path",
            "definition": "The sequence of devices in the customer journey, shown as nested array",
            "metric_type": "dimension"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "path_occurrences",
            "display_name": "Path Occurrences",
            "definition": "Number of unique users who followed this specific device path",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "impressions",
            "display_name": "Impressions",
            "definition": "Total ad impressions delivered across all users in this path",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "imp_total_cost",
            "display_name": "Total Cost",
            "definition": "Total media cost for all impressions in this path",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "users_that_purchased",
            "display_name": "Users That Purchased",
            "definition": "Number of users in this path who completed a purchase",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "conversion_rate",
            "display_name": "Conversion Rate",
            "definition": "Percentage of users in this path who converted",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "roas_sales_amount_brand",
            "display_name": "ROAS (Brand)",
            "definition": "Return on ad spend for branded products",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "cost_per_conversion",
            "display_name": "Cost Per Conversion",
            "definition": "Average media cost to achieve one conversion in this path",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "device_type",
            "display_name": "Device Type",
            "definition": "Type of device (PC, Phone, Tablet, TV, Other)",
            "metric_type": "dimension"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "touchpoint_order",
            "display_name": "Touchpoint Order",
            "definition": "Sequential position of touchpoint in the journey",
            "metric_type": "dimension"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "avg_relative_position",
            "display_name": "Average Relative Position",
            "definition": "Average position of device in journey (0=start, 1=end)",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "pct_initiator",
            "display_name": "% Initiator",
            "definition": "Percentage of times device appears as first touchpoint",
            "metric_type": "metric"
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "pct_closer",
            "display_name": "% Closer",
            "definition": "Percentage of times device appears as last touchpoint before conversion",
            "metric_type": "metric"
        }
    ]
    
    for i, metric in enumerate(metrics):
        metric['display_order'] = i + 1
        result = supabase.table('build_guide_metrics').insert(metric).execute()
    print(f"Created {len(metrics)} metrics")
    
    print(f"\n✅ Successfully seeded build guide: {guide_id}")
    print(f"   - {len(sections)} sections")
    print(f"   - {len(queries)} queries")
    print(f"   - {len(examples)} examples")
    print(f"   - {len(metrics)} metrics")

if __name__ == "__main__":
    seed_dsp_device_path_guide()