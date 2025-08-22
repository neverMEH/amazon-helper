#!/usr/bin/env python
"""
Seed script for Amazon Ad Server - Daily Performance with ASIN Conversions build guide
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

def create_guide() -> Dict[str, Any]:
    """Create the main build guide"""
    
    guide_data = {
        "guide_id": "guide_adserver_daily_asin_conversions",
        "name": "Amazon Ad Server - Daily Performance with ASIN Conversions",
        "short_description": "Track the impact of Amazon Ad Server advertising on Amazon conversions and Ad Server Tag Manager conversions with custom attribution",
        "category": "Amazon Ad Server",
        "difficulty_level": "advanced",
        "estimated_time_minutes": 45,
        "prerequisites": [
            "AMC Instance with Ad Server data",
            "Understanding of attribution models",
            "Knowledge of ASIN tracking"
        ],
        "tags": ["ad-server", "conversions", "attribution", "asin-tracking", "cross-channel"],
        "is_published": True,
        "display_order": 10,
        "icon": "📊"
    }
    
    # Check if guide exists
    existing = supabase.table("build_guides").select("*").eq("guide_id", guide_data["guide_id"]).execute()
    
    if existing.data:
        print(f"Guide {guide_data['guide_id']} already exists, updating...")
        result = supabase.table("build_guides").update(guide_data).eq("guide_id", guide_data["guide_id"]).execute()
    else:
        print(f"Creating new guide {guide_data['guide_id']}...")
        result = supabase.table("build_guides").insert(guide_data).execute()
    
    return result.data[0]

def create_sections(guide_uuid: str):
    """Create all sections for the guide"""
    
    sections = [
        {
            "guide_id": guide_uuid,
            "section_id": "introduction",
            "title": "Introduction",
            "display_order": 1,
            "content_markdown": """## Purpose

This Instructional Query (IQ) demonstrates the impact that Amazon Ad Server advertising has on Amazon conversions and Amazon Ad Server Tag Manager conversions. Find the impact on ad-attributed conversions, such as add-to-cart conversions, when customers are exposed to ads running outside of Amazon DSP.

This guide provides examples of daily custom attribution of ASIN conversions and the AdServer Tag Manager conversions on all Amazon Ad Server traffic including:
- Brand halo conversions performance
- Tracked ASIN performance  
- Cross-channel attribution insights

### Key Concepts

**Amazon Ad Server Tag Manager** is a single piece of code that resides on all pages of an advertiser's website. Using this unique code minimizes the need for constant communication between the Amazon Ad Server user and the webmaster. In Amazon Ad Server, users define when, where, and how often to fire activity entities to track conversion, retargeting, and 3rd party events.

> **Note**: AdServer Tag Manager is different from Amazon Ad Tags (AAT) used in DSP. AAT is a site-wide tag that captures events on a website for Amazon DSP audience building and conversion measurement.

## Requirements

This query will run for all endemic brands that track ASINs on any of the Amazon campaigns:
- Amazon DSP
- Sponsored Ads  
- Amazon Ad Server

⚠️ **Important**: Since Amazon Ad Server doesn't yet have the ability to track ASINs to campaigns directly, an Amazon Ad Server advertiser must track the ASINs through Amazon DSP or Sponsored Ads to use the AMC custom attribution data."""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "data-sources",
            "title": "Data Sources Overview",
            "display_order": 2,
            "content_markdown": """## Tables Used in This Query

### 1. adserver_traffic
Contains all impressions and clicks measured by the Amazon Ad Server.

**Key fields:**
- `event_date_utc`: Date of the traffic event
- `advertiser_id`, `campaign_id`: Identifiers for advertiser and campaign
- `user_id`: Unique user identifier for attribution matching
- `impressions`, `clicks`: Traffic metrics

### 2. adserver_conversions  
Includes all conversion events measured by the Amazon Ad Server conversion activity tags.

**Key fields:**
- `conversion_id`: Unique conversion identifier
- `conversion_activity`: Type of conversion activity
- `revenue`: Revenue associated with conversion
- `event_dt_utc`: Timestamp of conversion

### 3. conversions
Contains relevant conversions including purchases, detail page views, add-to-cart, and subscribe & save events.

**Relevance criteria:**
1. User was served an impression or had a click within 28 days before conversion
2. Conversion is from a tracked ASIN or brand family ASIN
3. At least one attributed conversion exists in the 28-day period

**Note**: The 28-day window doubles the standard 14-day attribution window, providing more comprehensive attribution insights.

### 4. conversions_with_relevance
Same conversions as the `conversions` table but includes campaign-specific columns. Since conversions can be relevant to multiple campaigns, each conversion event could appear on multiple rows.

**Example**: If a user is exposed to both campaign_a and campaign_b on the same day and then purchases, the purchase conversion will be recorded twice - once for each campaign.

## Attribution Model

**Default**: Last Click Over Impression
- The last event gets credit for the conversion
- Clicks are prioritized over impressions
- 14-day lookback window

This means a conversion will be attributed to the last click even if there are impressions that follow."""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "implementation",
            "title": "Implementation Steps",
            "display_order": 3,
            "content_markdown": """## Step-by-Step Implementation

### Step 1: Choose Your Use Case

**Use Case 1: Total Brand Conversions (Brand Halo)**
- Includes all ASINs from the same brand family
- Broader attribution scope
- Best for understanding overall brand impact

**Use Case 2: Tracked ASINs Only**
- Specific to ASINs tracked in campaigns
- More precise attribution
- Two methods available:
  - Method 1: ASINs defined at campaign level in Ad Server
  - Method 2: Manual ASIN-to-campaign mapping in query

### Step 2: Run Exploratory Queries

Before implementing the main query, run these exploratory queries to identify the correct IDs and filters:

#### Find Advertiser and Campaign IDs
Use the first exploratory query to list all advertisers and campaigns in your instance.

#### Identify ASIN Conversions
Use the second exploratory query to see which ASINs have conversions and their volume.

### Step 3: Customize the Query Template

1. **Update Advertiser IDs**: Replace placeholder values in the `advertiser_ids` CTE
2. **Set Campaign IDs**: Update the `campaign_ids` CTE with your campaigns
3. **Configure ASIN Tracking**:
   - For Use Case 1: Optionally filter by specific ASINs
   - For Use Case 2: Map campaign_id to tracked ASINs
4. **Replace Activity Names**: Find and replace "Activity1" and "Activity2" with your actual conversion activity names

### Step 4: Configure Attribution Settings

**Lookback Window**: Default is 14 days, can be adjusted
```sql
SECONDS_BETWEEN(t.event_dt_utc, c.event_dt_utc) BETWEEN 0 AND 14 * 24 * 60 * 60
```

**Attribution Model**: To change from last touch to first touch:
```sql
ROW_NUMBER() OVER(PARTITION BY conversion_id ORDER BY match_age DESC)
```

### Step 5: Optional Enhancements

Enable these features by uncommenting relevant sections:
- **DCO Ad Versions**: Track performance by creative version
- **Target Audiences**: Analyze by audience segments
- **Additional Filters**: Apply advertiser or campaign filters"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "metrics",
            "title": "Metrics Definitions",
            "display_order": 4,
            "content_markdown": """## Core Metrics Explained

### Traffic Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| **Impressions** | Total ad impressions served | adserver_traffic |
| **Clicks** | Total clicks on ads | adserver_traffic |

### Amazon Conversion Metrics

| Metric | Description | Attribution |
|--------|-------------|-------------|
| **DPV (Detail Page View)** | Views of product detail pages | 14-day lookback, last touch |
| **ATC (Add to Cart)** | Products added to shopping cart | 14-day lookback, last touch |
| **Purchases** | Completed purchase events | 14-day lookback, last touch |
| **Total Units Sold** | Quantity of products purchased | Includes brand halo products |
| **Total Sales USD** | Revenue from tracked ASINs | Includes brand family ASINs |

### Attribution Splits

Each conversion metric is split by attribution type:
- **_views**: Conversions attributed to impressions
- **_clicks**: Conversions attributed to clicks

### Ad Server Conversion Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **Total Conversions** | All conversions from Ad Server tags | Sum of all conversion activities |
| **Conversion Rate** | Percentage of impressions converting | (Conversions / Impressions) × 100 |
| **Conversion Revenue** | Revenue from Ad Server conversions | Sum of revenue field |

### Tracked vs Total Metrics

- **Total_** prefix: Includes brand halo (all brand family ASINs)
- **No prefix**: Only tracked ASINs from campaigns"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "query-templates",
            "title": "Query Templates",
            "display_order": 5,
            "content_markdown": """## Query Templates

### Exploratory Queries

These queries help you understand your data before running the main analysis."""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "results",
            "title": "Interpreting Results",
            "display_order": 6,
            "content_markdown": """## Understanding Your Results

### Sample Output Structure

Results will include daily metrics broken down by:
- Date
- Advertiser and Campaign details
- Site/Placement hierarchy
- Ad creative information
- All conversion metrics (views vs clicks attribution)

### Key Analysis Points

#### 1. Attribution Split Analysis
Compare **_views** vs **_clicks** metrics to understand:
- Which touchpoint drives more conversions
- Where to optimize creative for better engagement

#### 2. Brand Halo Effect
Compare Total metrics vs Tracked ASIN metrics:
- **High ratio**: Strong brand halo effect
- **Low ratio**: Limited cross-ASIN impact

#### 3. Conversion Funnel Analysis
Track progression through funnel:
```
DPV → ATC → Purchase
```
Calculate conversion rates between stages to identify drop-off points.

### Performance Insights

**High DPV, Low Purchase**: 
- Product page needs optimization
- Pricing or availability issues

**High Click Rate, Low Conversion**:
- Landing page mismatch
- Targeting needs refinement

**Strong View-Through Conversions**:
- Brand awareness driving results
- Display creative is effective

### Optimization Recommendations

1. **Campaign Comparison**: Run analysis over longer periods and group by date to confirm patterns
2. **Investment Decisions**: Allocate budget to campaigns with highest conversion efficiency
3. **Creative Testing**: Use version tracking to identify best-performing creatives
4. **Audience Refinement**: Analyze by target audience to optimize segments"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "troubleshooting",
            "title": "Common Issues and Solutions",
            "display_order": 7,
            "content_markdown": """## Troubleshooting Guide

### Issue: No Results Returned

**Possible Causes:**
- No ASIN tracking configured in DSP/Sponsored Ads
- Incorrect advertiser or campaign IDs
- Date range outside data availability

**Solutions:**
1. Verify ASINs are tracked in at least one Amazon channel
2. Run exploratory queries to confirm IDs
3. Check data availability (28-day lookback maximum)

### Issue: Missing Ad Server Conversions

**Possible Causes:**
- Activity names not replaced correctly
- Ad Server Tag not firing properly
- Conversion events outside lookback window

**Solutions:**
1. Replace "Activity1/Activity2" with actual activity names in two places
2. Verify Ad Server Tag implementation
3. Adjust lookback window if needed

### Issue: Discrepancies with Standard Reports

**Expected Differences:**
- AMC uses longer lookback (28 days vs 14 days)
- Not competition-aware (all touchpoints counted)
- Includes non-viewable impressions

These differences typically result in higher conversion counts in AMC.

### Issue: Query Performance

**Optimization Tips:**
1. Use `conversions` table for Use Case 1 (better performance)
2. Only use `conversions_with_relevance` when filtering by campaign
3. Limit date ranges to necessary periods
4. Apply filters early in CTEs

### Issue: DCO/Audience Data Missing

**Solution:**
Uncomment the relevant sections marked with:
```sql
-- UPDATE: Uncomment to use dco ad versions
```

Remember to uncomment in all locations (traffic, attribution, and final SELECT)."""
        }
    ]
    
    # Delete existing sections
    supabase.table("build_guide_sections").delete().eq("guide_id", guide_uuid).execute()
    
    # Insert new sections
    for section in sections:
        result = supabase.table("build_guide_sections").insert(section).execute()
        print(f"Created section: {section['title']}")

def create_queries(guide_uuid: str):
    """Create query templates for the guide"""
    
    queries = [
        {
            "guide_id": guide_uuid,
            "query_type": "exploratory",
            "title": "Campaign and Advertisers Exploratory Query",
            "definition": "Find all advertisers and campaigns with their traffic metrics",
            "sql_query": """-- Exploratory query: Campaign and Advertisers Exploratory Query
SELECT
  advertiser,
  advertiser_id,
  campaign,
  campaign_id,
  SUM(impressions) AS impressions,
  SUM(clicks) AS total_clicks
FROM
  adserver_traffic
GROUP BY
  1, 2, 3, 4
ORDER BY
  impressions DESC""",
            "default_parameters": {},
            "display_order": 1
        },
        {
            "guide_id": guide_uuid,
            "query_type": "exploratory",
            "title": "ASIN Conversions Exploratory Query",
            "definition": "Identify which ASINs have conversions and their volume",
            "sql_query": """-- Exploratory Query: custom attribution exploratory query for ASIN conversions
SELECT
  tracked_item AS ASIN,
  SUM(conversions) AS Total_DPV
FROM
  conversions_with_relevance c
WHERE
  event_subtype = 'detailPageView' -- Update based on conversion types needed
GROUP BY
  1
ORDER BY
  Total_DPV DESC
LIMIT 100""",
            "parameters": [
                {
                    "title": "event_subtype",
                    "type": "string",
                    "default_value": "detailPageView",
                    "definition": "Type of conversion to analyze (detailPageView, addToCart, purchase)"
                }
            ],
            "display_order": 2
        },
        {
            "guide_id": guide_uuid,
            "query_type": "main_analysis",
            "title": "Brand Halo Analysis Query",
            "definition": "Analyze total brand conversions including brand family ASINs",
            "sql_query": """-- Main Query: Brand Halo Analysis
WITH advertiser_ids AS (
    SELECT '12345' AS advertiser_id -- UPDATE: Replace with your advertiser IDs
),
campaign_ids AS (
    SELECT '67890' AS campaign_id -- UPDATE: Replace with your campaign IDs
),
traffic AS (
    SELECT
        event_date_utc AS date,
        advertiser_id,
        advertiser,
        campaign_id,
        campaign,
        site,
        placement_id,
        placement,
        ad_id,
        ad,
        user_id,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks
    FROM adserver_traffic
    WHERE advertiser_id IN (SELECT advertiser_id FROM advertiser_ids)
    GROUP BY 1,2,3,4,5,6,7,8,9,10,11
),
custom_attribution AS (
    SELECT
        t.date,
        t.advertiser_id,
        t.advertiser,
        t.campaign_id,
        t.campaign,
        t.site,
        t.placement_id,
        t.placement,
        t.ad_id,
        t.ad,
        c.conversion_id,
        c.event_subtype,
        c.tracked_item,
        c.order_amount,
        c.units_sold,
        CASE WHEN t.clicks > 0 THEN 'click' ELSE 'view' END AS attribution_type,
        SECONDS_BETWEEN(t.event_dt_utc, c.event_dt_utc) AS match_age,
        ROW_NUMBER() OVER(PARTITION BY c.conversion_id ORDER BY 
            CASE WHEN t.clicks > 0 THEN 0 ELSE 1 END, match_age) AS rn
    FROM traffic t
    JOIN conversions c ON t.user_id = c.user_id
    WHERE SECONDS_BETWEEN(t.event_dt_utc, c.event_dt_utc) BETWEEN 0 AND 14 * 24 * 60 * 60
),
final_attribution AS (
    SELECT * FROM custom_attribution WHERE rn = 1
)
SELECT
    date,
    advertiser,
    campaign,
    site,
    placement,
    ad,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(CASE WHEN event_subtype = 'detailPageView' AND attribution_type = 'view' THEN 1 ELSE 0 END) AS dpv_views,
    SUM(CASE WHEN event_subtype = 'detailPageView' AND attribution_type = 'click' THEN 1 ELSE 0 END) AS dpv_clicks,
    SUM(CASE WHEN event_subtype = 'addToCart' AND attribution_type = 'view' THEN 1 ELSE 0 END) AS atc_views,
    SUM(CASE WHEN event_subtype = 'addToCart' AND attribution_type = 'click' THEN 1 ELSE 0 END) AS atc_clicks,
    SUM(CASE WHEN event_subtype = 'purchase' AND attribution_type = 'view' THEN 1 ELSE 0 END) AS purchase_views,
    SUM(CASE WHEN event_subtype = 'purchase' AND attribution_type = 'click' THEN 1 ELSE 0 END) AS purchase_clicks,
    SUM(CASE WHEN event_subtype = 'purchase' THEN units_sold ELSE 0 END) AS total_units_sold,
    SUM(CASE WHEN event_subtype = 'purchase' THEN order_amount ELSE 0 END) AS total_sales_usd
FROM final_attribution
GROUP BY 1,2,3,4,5,6
ORDER BY date DESC, impressions DESC""",
            "parameters": [
                {
                    "title": "advertiser_id",
                    "type": "string",
                    "default_value": "12345",
                    "definition": "Your advertiser ID from Ad Server"
                },
                {
                    "title": "campaign_id",
                    "type": "string",
                    "default_value": "67890",
                    "definition": "Your campaign ID from Ad Server"
                },
                {
                    "title": "lookback_days",
                    "type": "integer",
                    "default_value": "14",
                    "definition": "Attribution lookback window in days"
                }
            ],
            "display_order": 3
        },
        {
            "guide_id": guide_uuid,
            "query_type": "main_analysis",
            "title": "Tracked ASINs Analysis Query",
            "definition": "Analyze only specifically tracked ASINs from campaigns",
            "sql_query": """-- Main Query: Tracked ASINs Analysis
WITH advertiser_ids AS (
    SELECT '12345' AS advertiser_id -- UPDATE: Replace with your advertiser IDs
),
campaign_ids AS (
    SELECT '67890' AS campaign_id -- UPDATE: Replace with your campaign IDs  
),
campaign_asin_mapping AS (
    -- UPDATE: Map campaign IDs to their tracked ASINs
    SELECT '67890' AS campaign_id, 'B08N5WRWNW' AS asin
    UNION ALL
    SELECT '67890' AS campaign_id, 'B08N5LNQCX' AS asin
),
traffic AS (
    SELECT
        event_date_utc AS date,
        advertiser_id,
        advertiser,
        campaign_id,
        campaign,
        site,
        placement_id,
        placement,
        ad_id,
        ad,
        user_id,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks
    FROM adserver_traffic
    WHERE campaign_id IN (SELECT campaign_id FROM campaign_ids)
    GROUP BY 1,2,3,4,5,6,7,8,9,10,11
),
custom_attribution AS (
    SELECT
        t.date,
        t.advertiser_id,
        t.advertiser,
        t.campaign_id,
        t.campaign,
        t.site,
        t.placement_id,
        t.placement,
        t.ad_id,
        t.ad,
        c.conversion_id,
        c.event_subtype,
        c.tracked_item,
        c.order_amount,
        c.units_sold,
        CASE WHEN t.clicks > 0 THEN 'click' ELSE 'view' END AS attribution_type,
        SECONDS_BETWEEN(t.event_dt_utc, c.event_dt_utc) AS match_age,
        ROW_NUMBER() OVER(PARTITION BY c.conversion_id ORDER BY 
            CASE WHEN t.clicks > 0 THEN 0 ELSE 1 END, match_age) AS rn
    FROM traffic t
    JOIN conversions_with_relevance c ON t.user_id = c.user_id AND t.campaign_id = c.campaign_id
    JOIN campaign_asin_mapping cam ON c.tracked_item = cam.asin AND c.campaign_id = cam.campaign_id
    WHERE SECONDS_BETWEEN(t.event_dt_utc, c.event_dt_utc) BETWEEN 0 AND 14 * 24 * 60 * 60
),
final_attribution AS (
    SELECT * FROM custom_attribution WHERE rn = 1
)
SELECT
    date,
    advertiser,
    campaign,
    site,
    placement,
    ad,
    tracked_item AS asin,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(CASE WHEN event_subtype = 'detailPageView' AND attribution_type = 'view' THEN 1 ELSE 0 END) AS dpv_views,
    SUM(CASE WHEN event_subtype = 'detailPageView' AND attribution_type = 'click' THEN 1 ELSE 0 END) AS dpv_clicks,
    SUM(CASE WHEN event_subtype = 'addToCart' AND attribution_type = 'view' THEN 1 ELSE 0 END) AS atc_views,
    SUM(CASE WHEN event_subtype = 'addToCart' AND attribution_type = 'click' THEN 1 ELSE 0 END) AS atc_clicks,
    SUM(CASE WHEN event_subtype = 'purchase' AND attribution_type = 'view' THEN 1 ELSE 0 END) AS purchase_views,
    SUM(CASE WHEN event_subtype = 'purchase' AND attribution_type = 'click' THEN 1 ELSE 0 END) AS purchase_clicks,
    SUM(CASE WHEN event_subtype = 'purchase' THEN units_sold ELSE 0 END) AS units_sold,
    SUM(CASE WHEN event_subtype = 'purchase' THEN order_amount ELSE 0 END) AS sales_usd
FROM final_attribution
GROUP BY 1,2,3,4,5,6,7
ORDER BY date DESC, asin, impressions DESC""",
            "parameters": [
                {
                    "title": "advertiser_id",
                    "type": "string",
                    "default_value": "12345",
                    "definition": "Your advertiser ID from Ad Server"
                },
                {
                    "title": "campaign_id",
                    "type": "string",
                    "default_value": "67890",
                    "definition": "Your campaign ID from Ad Server"
                },
                {
                    "title": "tracked_asins",
                    "type": "array",
                    "default_value": ["B08N5WRWNW", "B08N5LNQCX"],
                    "definition": "List of ASINs tracked in this campaign"
                },
                {
                    "title": "lookback_days",
                    "type": "integer",
                    "default_value": "14",
                    "definition": "Attribution lookback window in days"
                }
            ],
            "display_order": 4
        }
    ]
    
    # Delete existing queries
    supabase.table("build_guide_queries").delete().eq("guide_id", guide_uuid).execute()
    
    # Insert new queries and track their IDs
    query_ids = {}
    for query in queries:
        query_title = query["title"]
        
        # Convert parameters to the proper format
        if "parameters" in query:
            params = query.pop("parameters")
            default_params = {}
            params_schema = {}
            for param in params:
                param_name = param.get("title", param.get("name"))
                default_params[param_name] = param.get("default_value")
                params_schema[param_name] = {
                    "type": param.get("type"),
                    "default": param.get("default_value"),
                    "definition": param.get("description")
                }
            query["default_parameters"] = json.dumps(default_params) if default_params else None
            query["parameters_schema"] = json.dumps(params_schema) if params_schema else None
        
        # Handle empty default_parameters
        if "default_parameters" in query and isinstance(query["default_parameters"], dict):
            query["default_parameters"] = json.dumps(query["default_parameters"]) if query["default_parameters"] else None
        
        result = supabase.table("build_guide_queries").insert(query).execute()
        query_ids[query_title] = result.data[0]["id"]
        print(f"Created query: {query_title}")
    
    return query_ids

def create_examples(guide_uuid: str, query_ids: dict):
    """Create example results for the guide"""
    
    examples = [
        {
            "guide_query_id": query_ids.get("Brand Halo Analysis Query"),
            "example_name": "Brand Halo Analysis Sample Results",
            "sample_data": {
                "rows": [
                    {
                        "date": "2025-08-20",
                        "advertiser": "Acme Electronics",
                        "campaign": "Summer Promotion 2025",
                        "site": "Amazon.com",
                        "placement": "Homepage Carousel",
                        "ad": "Summer Sale Banner",
                        "impressions": 125000,
                        "clicks": 2500,
                        "dpv_views": 450,
                        "dpv_clicks": 380,
                        "atc_views": 120,
                        "atc_clicks": 145,
                        "purchase_views": 45,
                        "purchase_clicks": 78,
                        "total_units_sold": 123,
                        "total_sales_usd": 8547.50
                    },
                    {
                        "date": "2025-08-20",
                        "advertiser": "Acme Electronics",
                        "campaign": "Summer Promotion 2025",
                        "site": "External Publisher",
                        "placement": "Banner 728x90",
                        "ad": "Product Showcase",
                        "impressions": 85000,
                        "clicks": 1200,
                        "dpv_views": 220,
                        "dpv_clicks": 190,
                        "atc_views": 65,
                        "atc_clicks": 88,
                        "purchase_views": 22,
                        "purchase_clicks": 45,
                        "total_units_sold": 67,
                        "total_sales_usd": 4321.75
                    },
                    {
                        "date": "2025-08-19",
                        "advertiser": "Acme Electronics",
                        "campaign": "Always On Campaign",
                        "site": "Amazon.com",
                        "placement": "Search Results",
                        "ad": "Product Ad",
                        "impressions": 98000,
                        "clicks": 3100,
                        "dpv_views": 380,
                        "dpv_clicks": 520,
                        "atc_views": 95,
                        "atc_clicks": 210,
                        "purchase_views": 38,
                        "purchase_clicks": 92,
                        "total_units_sold": 130,
                        "total_sales_usd": 9875.00
                    }
                ]
            },
            "interpretation_markdown": """### Key Insights from Sample Results

1. **Click Attribution Dominance**: Click-attributed conversions consistently outperform view-attributed conversions across all funnel stages, suggesting strong intent-driven performance.

2. **Conversion Funnel Health**: 
   - DPV to ATC conversion: ~30% (healthy)
   - ATC to Purchase conversion: ~40% (strong)
   - Overall funnel efficiency is performing well

3. **Placement Performance**:
   - Amazon.com placements show higher conversion rates
   - External publishers drive significant volume but lower conversion rates
   - Consider optimization strategies for external placements

4. **Brand Halo Impact**: Total sales include brand family ASINs, showing 15-20% lift beyond tracked ASINs""",
            "display_order": 1
        },
        {
            "guide_query_id": query_ids.get("Tracked ASINs Analysis Query"),
            "example_name": "Tracked ASINs Analysis Sample Results",
            "sample_data": {
                "rows": [
                    {
                        "date": "2025-08-20",
                        "advertiser": "Acme Electronics",
                        "campaign": "Product Launch Q3",
                        "site": "Amazon.com",
                        "placement": "Product Page",
                        "ad": "New Product Video",
                        "asin": "B08N5WRWNW",
                        "impressions": 45000,
                        "clicks": 890,
                        "dpv_views": 120,
                        "dpv_clicks": 180,
                        "atc_views": 35,
                        "atc_clicks": 65,
                        "purchase_views": 12,
                        "purchase_clicks": 28,
                        "units_sold": 40,
                        "sales_usd": 3599.60
                    },
                    {
                        "date": "2025-08-20",
                        "advertiser": "Acme Electronics",
                        "campaign": "Product Launch Q3",
                        "site": "Amazon.com",
                        "placement": "Product Page",
                        "ad": "New Product Video",
                        "asin": "B08N5LNQCX",
                        "impressions": 45000,
                        "clicks": 890,
                        "dpv_views": 95,
                        "dpv_clicks": 145,
                        "atc_views": 28,
                        "atc_clicks": 52,
                        "purchase_views": 8,
                        "purchase_clicks": 22,
                        "units_sold": 30,
                        "sales_usd": 2249.70
                    },
                    {
                        "date": "2025-08-19",
                        "advertiser": "Acme Electronics",
                        "campaign": "Product Launch Q3",
                        "site": "External Publisher",
                        "placement": "Native Ad",
                        "ad": "Product Review",
                        "asin": "B08N5WRWNW",
                        "impressions": 32000,
                        "clicks": 420,
                        "dpv_views": 65,
                        "dpv_clicks": 88,
                        "atc_views": 18,
                        "atc_clicks": 32,
                        "purchase_views": 5,
                        "purchase_clicks": 15,
                        "units_sold": 20,
                        "sales_usd": 1799.80
                    }
                ]
            },
            "interpretation_markdown": """### ASIN-Level Performance Analysis

1. **ASIN Performance Variance**:
   - B08N5WRWNW shows stronger conversion rates (2.0% CTR, 4.5% purchase rate)
   - B08N5LNQCX has lower conversion but similar traffic volume
   - Consider creative optimization for underperforming ASINs

2. **Placement Efficiency**:
   - Product Page placements drive highest ASIN-specific conversions
   - Native ads on external sites show promise but need optimization

3. **Attribution Insights**:
   - 70% of purchases are click-attributed
   - View-through conversions still contribute 30% of sales
   - Multi-touch attribution may reveal additional value""",
            "display_order": 2
        }
    ]
    
    # Delete existing examples for these queries
    for query_id in query_ids.values():
        if query_id:
            supabase.table("build_guide_examples").delete().eq("guide_query_id", query_id).execute()
    
    # Insert new examples
    for example in examples:
        # Skip if no query_id
        if not example.get("guide_query_id"):
            continue
        
        # Handle sample_data JSON
        if "sample_data" in example:
            example["sample_data"] = json.dumps(example["sample_data"])
        result = supabase.table("build_guide_examples").insert(example).execute()
        print(f"Created example: {example['example_name']}")

def create_metrics(guide_uuid: str):
    """Create metrics definitions for the guide"""
    
    metrics = [
        # Traffic Metrics
        {
            "guide_id": guide_uuid,
            "metric_name": "impressions",
            "display_name": "Impressions",
            "metric_type": "dimension",
            "definition": "Total number of ad impressions served (SUM(impressions) from adserver_traffic)",
            "display_order": 1
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "clicks",
            "display_name": "Clicks",
            "metric_type": "dimension",
            "definition": "Total number of clicks on ads (SUM(clicks) from adserver_traffic)",
            "display_order": 2
        },
        # Conversion Metrics - Views
        {
            "guide_id": guide_uuid,
            "metric_name": "dpv_views",
            "display_name": "DPV Views",
            "metric_type": "metric",
            "definition": "Detail page views attributed to ad impressions",
            "display_order": 3
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "DPV Clicks",
            "metric_type": "metric",
            "definition": "Detail page views attributed to ad clicks",
            "display_name": "SUM(CASE WHEN event_subtype = 'detailPageView' AND attribution_type = 'click' THEN 1 ELSE 0 END)",
            "metric_info": "conversions",
            "display_order": 4
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "ATC Views",
            "metric_type": "metric",
            "definition": "Add to cart events attributed to ad impressions",
            "display_name": "SUM(CASE WHEN event_subtype = 'addToCart' AND attribution_type = 'view' THEN 1 ELSE 0 END)",
            "metric_info": "conversions",
            "display_order": 5
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "ATC Clicks",
            "metric_type": "metric",
            "definition": "Add to cart events attributed to ad clicks",
            "display_name": "SUM(CASE WHEN event_subtype = 'addToCart' AND attribution_type = 'click' THEN 1 ELSE 0 END)",
            "metric_info": "conversions",
            "display_order": 6
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "Purchase Views",
            "metric_type": "metric",
            "definition": "Purchases attributed to ad impressions",
            "display_name": "SUM(CASE WHEN event_subtype = 'purchase' AND attribution_type = 'view' THEN 1 ELSE 0 END)",
            "metric_info": "conversions",
            "display_order": 7
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "Purchase Clicks",
            "metric_type": "metric",
            "definition": "Purchases attributed to ad clicks",
            "display_name": "SUM(CASE WHEN event_subtype = 'purchase' AND attribution_type = 'click' THEN 1 ELSE 0 END)",
            "metric_info": "conversions",
            "display_order": 8
        },
        # Sales Metrics
        {
            "guide_id": guide_uuid,
            "metric_name": "Total Units Sold",
            "metric_type": "metric",
            "definition": "Total quantity of products purchased (includes brand halo)",
            "display_name": "SUM(CASE WHEN event_subtype = 'purchase' THEN units_sold ELSE 0 END)",
            "metric_info": "conversions",
            "display_order": 9
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "Total Sales USD",
            "metric_type": "metric",
            "definition": "Total revenue from purchases (includes brand family ASINs)",
            "display_name": "SUM(CASE WHEN event_subtype = 'purchase' THEN order_amount ELSE 0 END)",
            "metric_info": "conversions",
            "display_order": 10
        },
        # Calculated Metrics
        {
            "guide_id": guide_uuid,
            "metric_name": "CTR",
            "metric_type": "metric",
            "definition": "Click-through rate",
            "display_name": "(clicks / NULLIF(impressions, 0)) * 100",
            "metric_info": "calculated",
            "display_order": 11
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "View Conversion Rate",
            "metric_type": "metric",
            "definition": "Percentage of impressions resulting in purchase",
            "display_name": "(purchase_views / NULLIF(impressions, 0)) * 100",
            "metric_info": "calculated",
            "display_order": 12
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "Click Conversion Rate",
            "metric_type": "metric",
            "definition": "Percentage of clicks resulting in purchase",
            "display_name": "(purchase_clicks / NULLIF(clicks, 0)) * 100",
            "metric_info": "calculated",
            "display_order": 13
        },
        # Ad Server Metrics
        {
            "guide_id": guide_uuid,
            "metric_name": "Ad Server Conversions",
            "metric_type": "metric",
            "definition": "Conversions tracked by Ad Server Tag Manager",
            "display_name": "COUNT(DISTINCT conversion_id)",
            "metric_info": "adserver_conversions",
            "display_order": 14
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "Ad Server Revenue",
            "metric_type": "metric",
            "definition": "Revenue tracked by Ad Server Tag Manager",
            "display_name": "SUM(revenue)",
            "metric_info": "adserver_conversions",
            "display_order": 15
        }
    ]
    
    # Delete existing metrics
    supabase.table("build_guide_metrics").delete().eq("guide_id", guide_uuid).execute()
    
    # Insert new metrics
    for metric in metrics:
        result = supabase.table("build_guide_metrics").insert(metric).execute()
        print(f"Created metric: {metric['metric_name']}")

def main():
    """Main execution function"""
    print("Starting Amazon Ad Server - Daily ASIN Conversions guide creation...")
    
    try:
        # Create the guide
        guide = create_guide()
        guide_uuid = guide["id"]  # Use the UUID id for foreign key references
        guide_id = guide["guide_id"]  # Keep the string guide_id for display
        print(f"Successfully created/updated guide: {guide_id}")
        
        # Create sections
        create_sections(guide_uuid)
        print("Successfully created sections")
        
        # Create queries
        query_ids = create_queries(guide_uuid)
        print("Successfully created queries")
        
        # Create examples
        create_examples(guide_uuid, query_ids)
        print("Successfully created examples")
        
        # Create metrics
        create_metrics(guide_uuid)
        print("Successfully created metrics")
        
        print("\n✅ Guide successfully created!")
        print(f"Guide ID: {guide_id}")
        print(f"Name: {guide['name']}")
        print(f"Category: {guide['category']}")
        print(f"Difficulty: {guide['difficulty_level']}")
        
    except Exception as e:
        print(f"\n❌ Error creating guide: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()