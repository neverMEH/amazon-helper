#!/usr/bin/env python
"""
Seed script for Amazon Brand Store Insights in AMC build guide
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

def create_guide():
    """Create the Amazon Brand Store Insights build guide"""
    
    # 1. Create the main guide
    guide_data = {
        "guide_id": "guide_brand_store_insights_amc",
        "name": "Amazon Brand Store Insights in AMC",
        "short_description": "Explore Brand Store Insights dataset to identify high-value audience segments, analyze customer journeys, and create AMC audiences based on Brand Store engagements",
        "category": "Brand Store Analytics",
        "difficulty_level": "advanced",
        "estimated_time_minutes": 60,
        "prerequisites": [
            "AMC Instance",
            "Brand Store Insights enrollment (trial or subscription)",
            "Audience Segment Insights (optional)",
            "Active Brand Store with traffic"
        ],
        "tags": [
            "brand-store",
            "bsi",
            "path-to-conversion",
            "audience-creation",
            "referral-analysis",
            "dwell-time"
        ],
        "is_published": True,
        "display_order": 5
    }
    
    result = supabase.table("build_guides").upsert(guide_data).execute()
    guide_uuid = result.data[0]["id"]  # Get the UUID from the created guide
    guide_id_str = guide_data["guide_id"]  # Keep the string ID for reference
    print(f"✓ Created guide: {guide_id_str}")
    
    # 2. Create sections
    sections = [
        {
            "guide_id": guide_uuid,
            "section_id": "introduction",
            "title": "Introduction",
            "display_order": 1,
            "content_markdown": """## Summary

This instructional query guide helps you leverage the Amazon Brand Store Insights (BSI) dataset in AMC to:
- Identify high-value Amazon DSP audience segments
- Assess customer journey through path-to-conversion analysis
- Generate AMC audiences based on Brand Store engagements and dwell time
- Analyze referral sources driving Brand Store traffic

## What is Amazon Brand Store?

**Amazon Brand Stores** is a free, self-service storefront where brands can engage, convert, and build loyalty with millions of Amazon shoppers. Advertisers can leverage:
- Sponsored Brands campaigns to drive traffic
- Sponsored Display campaigns for retargeting
- No advertising prerequisite to create a Brand Store

## What is Amazon Brand Store Insights?

**AMC Brand Store Insights (BSI)** provides access to valuable signals from your Brand Store:
- Page visit details and dwell time
- Interaction events (clicks, scrolls, video plays)
- Visit and session identifiers
- URL parameter signals
- Referral source information

You can pair Brand Store signals with other AMC data sources like advertising traffic events or Amazon Ads audience segments for comprehensive analysis.

## Availability

BSI is available in nine AMC Account Marketplaces where AMC Paid Features is supported. For more information, refer to [AMC Paid features documentation](https://advertising.amazon.com/API/docs/en-us/guides/amazon-marketing-cloud/paid-features).

## Requirements

### Required:
- **Enrollment** in Amazon Brand Store Insights (trial or subscription)
- Active Brand Store with traffic
- AMC instance access

### Optional but Beneficial:
- **Audience Segment Insights** enrollment for segment analysis
- **Conversion events** in AMC for path-to-conversion analysis
- **Associated advertisers** for AMC audience activation

> **Note**: If you cannot see the Paid features tab, contact your AdTech Account Executive."""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "data-sources",
            "title": "Data Sources Overview",
            "display_order": 2,
            "content_markdown": """## Primary BSI Tables

### 1. amazon_brand_store_page_views
Brand Store page view events including dwell time at the Store page-level.

**Key Fields:**
- `user_id`: AMC user identifier for joining
- `visit_id`, `session_id`: Visit and session identifiers
- `dwell_time`: Time spent on page (seconds)
- `store_id`, `page_id`: Store and page identifiers
- `page_title`, `store_name`: Descriptive names
- `event_dt_utc`: Event timestamp

### 2. amazon_brand_store_engagement_events
Brand Store engagement events at the widget-level providing interaction metrics.

**Key Fields:**
- `event_type`: IMPRESSION, CLICK, SCROLL, VIDEO
- `event_sub_type`: Detailed action (ADDTOCART, DETAILPAGE, etc.)
- `widget_type`, `widget_sub_type`: UI component details
- `reference_id`: Campaign identifier for attribution
- `referrer_domain`: Traffic source domain

## Supporting Tables

### 3. audience_segments_<region>_<category>
Amazon Audience Segment Insights for user-to-segment analysis.

**Examples:**
- `audience_segments_amer_inmarket`
- `audience_segments_amer_lifestyle`

### 4. amazon_attributed_events_by_traffic_time
Ad-attributed conversion events for path analysis.

### 5. dsp_impressions & sponsored_ads_traffic
Traffic data for multi-touch attribution analysis.

## Common Enumerated Values

### Device Types
- Mobile_app, Desktop, Mobile_web
- Tablet_app, Tablet_web, Kindle_app

### Event Types & Subtypes

**Event Types:**
- IMPRESSION, CLICK, SCROLL, VIDEO

**Event Subtypes (Common):**
- ASIN_RENDER: Product displayed
- ADDTOCART: Add to cart action
- DETAILPAGE: View product details
- PROCEEDTOCHECKOUT: Checkout initiation
- 100PPLAYED: Video fully played
- QUICKLOOK: Quick product preview

### Widget Types
- ProductGrid, ProductCarousel, Gallery
- EditorialRow, Header, LiveVideo

### Referrer Domains
- amazon.com (internal traffic)
- Social: facebook.com, instagram.com, tiktok.com
- Video: youtube.com, twitch.tv
- External sites and partners

### Reference IDs (Common Patterns)
- `SB_CAMPAIGN-CREATIVE`: Sponsored Brands
- `SBV_CAMPAIGN`: Sponsored Brands Video
- `bl_ast_dp_brandLogo_sto`: Brand logo from detail page
- `storeRecs_dp_aplus`: Store recommendations"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "use-cases",
            "title": "Use Cases and Implementation",
            "display_order": 3,
            "content_markdown": """## Available Use Cases

This guide provides six powerful use cases for Brand Store Insights:

### 1. Explore BSI Data
**Purpose**: Understand available signals and data quality
**Key Metrics**: Sessions, visits, dwell time by page
**Use When**: Starting BSI analysis or validating data

### 2. Path to Conversion Analysis
**Purpose**: Analyze customer journey including Brand Store touches
**Key Insights**: Most effective paths, conversion rates by path
**Use When**: Optimizing marketing funnel strategy

### 3. Segment Data Decoration
**Purpose**: Identify which audience segments overlap with high-value Brand Store customers
**Key Insights**: Segment correlation with conversions
**Use When**: Refining DSP audience targeting

### 4. Referral Source Analysis
**Purpose**: Understand traffic sources driving Brand Store visits
**Key Metrics**: Conversion rates by referral source
**Use When**: Optimizing traffic acquisition strategy

### 5. Create AMC Audiences
**Purpose**: Build custom audiences based on Brand Store behavior
**Examples**: High dwell time users, add-to-cart users
**Use When**: Creating retargeting or lookalike audiences

### 6. Advanced Analytics (Custom)
**Purpose**: Combine BSI with other AMC data for unique insights
**Examples**: Cross-channel attribution, lifetime value analysis
**Use When**: Deep-dive analysis requirements

## Implementation Steps

### Step 1: Verify BSI Enrollment
1. Check Paid Features tab in AMC
2. Confirm Brand Store IDs appear in data
3. Run exploratory query to validate data

### Step 2: Choose Your Analysis
Select from the use cases based on your objectives:
- **Awareness**: Path analysis, referral sources
- **Consideration**: Dwell time, engagement events
- **Conversion**: Add-to-cart, checkout actions

### Step 3: Customize Queries
Each query template includes customization points:
- Date ranges
- Event types to analyze
- Dwell time thresholds
- Conversion definitions

### Step 4: Create Actionable Insights
Transform query results into actions:
- Audience creation for DSP
- Budget reallocation
- Creative optimization
- Landing page improvements"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "query-templates",
            "title": "Query Templates",
            "display_order": 4,
            "content_markdown": """## Query Templates for Brand Store Insights

Each template is designed for specific analysis needs. Customize parameters marked with comments."""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "metrics-glossary",
            "title": "Metrics Definitions",
            "display_order": 5,
            "content_markdown": """## Core BSI Metrics

### Engagement Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **dwell_time** | Time spent on Brand Store page (seconds) | Direct measurement |
| **dwell_time_minutes** | Time spent in minutes | SUM(dwell_time) / 60 |
| **distinct_sessions** | Unique session count | COUNT(DISTINCT session_id) |
| **distinct_visits** | Unique visit count | COUNT(DISTINCT visit_id) |

### Interaction Metrics

| Metric | Description | Event Subtypes |
|--------|-------------|----------------|
| **Add to Cart Rate** | % of sessions with ATC | atc_events / sessions |
| **Detail Page Rate** | % of sessions viewing details | dp_events / sessions |
| **Checkout Rate** | % proceeding to checkout | checkout_events / sessions |

## Path Analysis Metrics

| Metric | Definition | Business Impact |
|--------|------------|-----------------|
| **path_occurrences** | Users following specific path | Path effectiveness |
| **user_purchase_rate** | % of path users who purchase | Path conversion quality |
| **ntb_percentage** | % new-to-brand customers | Acquisition effectiveness |
| **conversions_per_user** | Average conversions per user | Engagement depth |

## Segment Overlap Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| **bsi_action_ceiling** | Total BSI events meeting criteria | Denominator for percentages |
| **perc_share_of_bsi_users** | % overlap with segment | Targeting relevance |
| **cd_bsi_user_id** | Distinct BSI users in segment | Audience size |

## Referral Analysis Metrics

| Metric | Description | Optimization Focus |
|--------|-------------|-------------------|
| **ingress_type** | Traffic source category | Channel strategy |
| **bsi_dp_rate** | Detail page view rate by source | Content relevance |
| **bsi_atc_rate** | Add-to-cart rate by source | Purchase intent |
| **distinct_sessions** | Sessions from source | Traffic volume |

## Attribution Metrics

| Metric | Description | Notes |
|--------|-------------|-------|
| **sales_amount** | Total sales attributed | Local currency |
| **total_cost** | Ad spend for path | DSP: millicents/1e5, SA: microcents/1e8 |
| **impressions** | Total ad impressions | Across all channels |
| **total_purchases** | Number of purchases | Including brand halo for SA |

## Key Performance Indicators

### Engagement KPIs
- **High Dwell Time**: >5 minutes indicates strong interest
- **Multiple Page Views**: >3 pages shows exploration
- **Interaction Depth**: ATC + DP events show purchase intent

### Conversion KPIs
- **Path Conversion Rate**: >2% is strong for awareness paths
- **NTB Rate**: >40% indicates new customer acquisition
- **Multi-touch Attribution**: BSI in path increases conversion 2-3x

### Efficiency KPIs
- **Cost per Path Completion**: Total cost / conversions
- **Referral Quality**: ATC rate by source
- **Segment Efficiency**: Conversion rate by audience segment"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "results-interpretation",
            "title": "Interpreting Results",
            "display_order": 6,
            "content_markdown": """## Sample Results Analysis

### 1. Exploratory Query Results

| store_name | page_title | distinct_sessions | distinct_visits | dwell_time_minutes |
|------------|------------|-------------------|-----------------|-------------------|
| Kitchen Smart | Tumblers | 55,422 | 55,422 | 35,234 |
| Kitchen Smart | Kids | 16,472 | 16,472 | 11,208 |
| Kitchen Smart | Mixers | 8,662 | 8,662 | 5,566 |

**Insights:**
- Tumblers page has highest engagement (0.64 min/session average)
- Kids section shows good traffic but lower dwell time
- Consider promoting Tumblers in campaigns

### 2. Path to Conversion Results

| path | path_occurrences | user_purchase_rate | ntb_percentage | conversions_per_user |
|------|------------------|-------------------|----------------|---------------------|
| [[1, DSP-Video], [2, BSI]] | 1,517 | 1% | 73% | 1.45 |
| [[1, DSP-Display], [2, SB-Others], [3, BSI]] | 576 | 6% | 53% | 1.58 |
| [[1, BSI]] | 48,594 | 1% | 64% | 1.47 |

**Key Findings:**
- Multi-touch paths with BSI show 6x higher conversion rate
- BSI-only path has high volume but low conversion
- Video→BSI path drives highest NTB rate (73%)

**Recommendations:**
1. Increase Video campaigns driving to Brand Store
2. Implement sequential messaging Video→BSI
3. Create lookalike audiences from BSI-only converters

### 3. Segment Overlap Results

| segment_name | perc_share_of_bsi_users |
|-------------|-------------------------|
| LS - Mother's Day | 88.54% |
| LS - Father's Day Gifts | 80.79% |
| LS - Amazon Fashion shoppers | 76.51% |
| LS - Sports and Outdoors | 73.28% |

**Strategic Actions:**
- **High Overlap (>70%)**: Priority targeting segments
- **Medium Overlap (40-70%)**: Test and iterate
- **Low Overlap (<40%)**: Consider exclusion

### 4. Referral Source Performance

| reference_id | referrer_domain | sessions | bsi_dp_rate | bsi_atc_rate |
|--------------|-----------------|----------|-------------|--------------|
| SB_Campaign-Creative | amazon.com | 18,584 | 51% | 2% |
| bl_ast_dp_brandLogo | amazon.com | 44,899 | 103% | 4% |
| - | tomsguide.com | 22 | 59% | 18% |
| - | tiktok.com | 174 | 84% | 1% |

**Insights:**
- Product detail page drives highest volume and conversion
- Review sites (tomsguide) show 9x higher ATC rate
- Social traffic has high browse rate but low conversion

**Optimization Strategy:**
1. Increase presence on review sites
2. Optimize SB campaigns for conversion (51% DP but only 2% ATC)
3. Test retargeting for social traffic visitors

## Action Planning Framework

### Immediate Actions (Week 1)
1. Create high-dwell-time audience (>5 min)
2. Launch retargeting for ATC non-purchasers
3. Adjust DSP targeting to high-overlap segments

### Short-term Optimizations (Month 1)
1. Implement path-based sequential messaging
2. Optimize Brand Store pages with low dwell time
3. Increase investment in high-converting referral sources

### Long-term Strategy (Quarter)
1. Build predictive models using BSI signals
2. Develop content strategy based on engagement patterns
3. Create feedback loop between BSI and campaign optimization

## Success Metrics

Track these KPIs to measure BSI optimization impact:

1. **Engagement Growth**
   - Month-over-month dwell time increase
   - Session-to-visit ratio improvement
   - Page depth increase

2. **Conversion Impact**
   - BSI-touched conversion rate
   - Multi-touch attribution value
   - NTB customer acquisition

3. **Efficiency Gains**
   - Cost per engaged visitor
   - ROAS for BSI-targeted campaigns
   - Audience match rates"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "best-practices",
            "title": "Best Practices and Troubleshooting",
            "display_order": 7,
            "content_markdown": """## Best Practices

### Data Quality

#### 1. Validate Store Coverage
```sql
-- Check all Brand Stores are captured
SELECT DISTINCT store_id, store_name
FROM amazon_brand_store_page_views
```
If stores are missing, contact AMC Support.

#### 2. Session vs Visit Understanding
- **Session**: Can span multiple visits
- **Visit**: Single continuous Brand Store interaction
- Use sessions for engagement analysis
- Use visits for traffic analysis

#### 3. Date Range Considerations
- BSI data has a 24-48 hour lag
- For Audience Segments, check data availability
- Path analysis needs sufficient lookback (30+ days)

### Query Optimization

#### 1. Performance Tips
- Filter early in CTEs
- Use appropriate date ranges
- Limit complex joins
- Consider sampling for exploration

#### 2. Attribution Windows
- Default: 30-day lookback
- Adjust based on purchase cycle
- Align with business reporting

#### 3. Event Type Selection
Choose events based on funnel stage:
- **Awareness**: IMPRESSION, SCROLL
- **Consideration**: DETAILPAGE, VIDEO
- **Conversion**: ADDTOCART, PROCEEDTOCHECKOUT

### Audience Creation

#### 1. Segmentation Strategy
Combine multiple signals:
- Dwell time AND interactions
- Multiple page views AND recent visit
- High engagement AND no purchase

#### 2. Size Considerations
- Minimum 1,000 users for activation
- Maximum depends on use case
- Balance precision with scale

#### 3. Refresh Frequency
- Daily for retargeting
- Weekly for prospecting
- Monthly for analysis

## Troubleshooting

### Issue: No BSI Data Appearing

**Checks:**
1. Verify BSI enrollment status
2. Confirm Brand Store has traffic
3. Check date range (24-48 hour lag)
4. Validate store_id in tables

**Solution:**
```sql
-- Verify BSI enrollment
SELECT COUNT(*) as record_count
FROM amazon_brand_store_page_views
WHERE event_dt_utc >= CURRENT_DATE - INTERVAL '7' DAY
```

### Issue: Low Match Rates with Audiences

**Possible Causes:**
- Users not logged in during Brand Store visit
- Cookie/tracking limitations
- Cross-device behavior

**Solutions:**
1. Increase lookback window
2. Use broader engagement criteria
3. Combine with other signals

### Issue: Unexpected Path Analysis Results

**Common Reasons:**
- Attribution window too short
- Missing traffic sources
- Data processing delays

**Debugging Query:**
```sql
-- Check traffic source coverage
SELECT 
  ad_product_type,
  COUNT(DISTINCT user_id) as users,
  MIN(event_dt_utc) as earliest,
  MAX(event_dt_utc) as latest
FROM (
  SELECT 'DSP' as ad_product_type, user_id, impression_dt as event_dt_utc 
  FROM dsp_impressions
  UNION ALL
  SELECT 'SA' as ad_product_type, user_id, event_dt_utc 
  FROM sponsored_ads_traffic
  UNION ALL
  SELECT 'BSI' as ad_product_type, user_id, event_dt_utc 
  FROM amazon_brand_store_page_views
)
GROUP BY 1
```

### Issue: Segment Overlap Not Meaningful

**Considerations:**
- Segment size thresholds
- Time period alignment
- Marketplace consistency

**Validation:**
```sql
-- Check segment data availability
SELECT 
  segment_marketplace_id,
  COUNT(DISTINCT segment_id) as segment_count,
  COUNT(DISTINCT user_id) as user_count
FROM audience_segments_amer_lifestyle
GROUP BY 1
```

## Advanced Techniques

### 1. Custom Attribution Models
Modify the ranked CTE for different attribution:
- First-touch: ORDER BY impression_dt_first ASC
- Linear: Distribute credit equally
- Time-decay: Weight by recency

### 2. Cohort Analysis
Track user cohorts over time:
```sql
-- Weekly cohort retention
WITH cohorts AS (
  SELECT 
    user_id,
    DATE_TRUNC('week', MIN(event_dt_utc)) as cohort_week
  FROM amazon_brand_store_page_views
  GROUP BY 1
)
-- Continue with retention calculation
```

### 3. Predictive Scoring
Combine signals for propensity scores:
- High dwell time + multiple visits = High intent
- ATC + no purchase = Retargeting priority
- New visitor + long dwell = Nurture candidate

## Checklist for Implementation

### Pre-Launch
- [ ] Verify BSI enrollment
- [ ] Confirm data availability
- [ ] Document Brand Store structure
- [ ] Define success metrics

### Launch
- [ ] Run exploratory queries
- [ ] Validate data quality
- [ ] Create initial audiences
- [ ] Set up monitoring

### Post-Launch
- [ ] Weekly performance review
- [ ] Audience refresh cadence
- [ ] Optimization iterations
- [ ] Stakeholder reporting"""
        }
    ]
    
    for section in sections:
        supabase.table("build_guide_sections").upsert(section).execute()
    print(f"✓ Created {len(sections)} sections")
    
    # 3. Create queries and store their IDs
    query_ids = {}
    
    queries = [
        {
            "guide_id": guide_uuid,
            "title": "Explore BSI Data",
            "description": "Understand your Brand Store data structure and volume",
            "sql_query": """-- Exploratory Query for Amazon Brand Store Insights
-- Understand your Brand Store data structure and volume

SELECT
  marketplace_name,
  store_name,
  store_id,
  page_id,
  page_title,
  COUNT(session_id) AS count_sessions,
  COUNT(DISTINCT session_id) AS distinct_sessions,
  COUNT(visit_id) AS count_visits,
  COUNT(DISTINCT visit_id) AS distinct_visits,
  ROUND((SUM(dwell_time) / 60), 0) AS total_dwell_time_minutes
FROM
  amazon_brand_store_page_views
GROUP BY
  1, 2, 3, 4, 5
ORDER BY
  total_dwell_time_minutes DESC""",
            "parameters_schema": {},
            "display_order": 1,
            "query_type": "exploratory"
        },
        {
            "guide_id": guide_uuid,
            "title": "Path to Conversion Analysis",
            "description": "Analyze customer journey including Brand Store touches",
            "sql_query": """-- Path to Conversion with Brand Store Insights
-- Full query continues with conversions and path assembly...""",
            "parameters_schema": {},
            "display_order": 2,
            "query_type": "main_analysis"
        },
        {
            "guide_id": guide_uuid,
            "title": "Segment Data Decoration",
            "description": "Identify audience segments overlapping with Brand Store visitors",
            "sql_query": """-- Segment overlap with high-value Brand Store customers
-- Requires Audience Segment Insights enrollment""",
            "parameters_schema": {},
            "display_order": 3,
            "query_type": "main_analysis"
        },
        {
            "guide_id": guide_uuid,
            "title": "Referral Source Analysis",
            "description": "Analyze traffic sources driving Brand Store visits",
            "sql_query": """-- Brand Store referral source performance analysis""",
            "parameters_schema": {},
            "display_order": 4,
            "query_type": "main_analysis"
        },
        {
            "guide_id": guide_uuid,
            "title": "AMC Audience Creation",
            "description": "Create audiences based on Brand Store behavior",
            "sql_query": """-- Create audience based on Brand Store behavior
-- Use in AMC Audiences query editor""",
            "parameters_schema": {
                "dwell_time_threshold": {
                    "description": "Minimum dwell time in minutes",
                    "type": "integer",
                    "default": 5
                },
                "event_sub_type": {
                    "description": "Event type to filter (ADDTOCART, DETAILPAGE, etc.)",
                    "type": "string",
                    "default": "ADDTOCART"
                }
            },
            "display_order": 5,
            "query_type": "main_analysis"
        }
    ]
    
    for query in queries:
        result = supabase.table("build_guide_queries").upsert(query).execute()
        query_ids[query["title"]] = result.data[0]["id"]
    print(f"✓ Created {len(queries)} queries")
    
    # 4. Create example results using query IDs
    examples = [
        {
            "guide_query_id": query_ids["Explore BSI Data"],
            "example_name": "Exploratory Query Results",
            "sample_data": {
                "rows": [
                    {
                        "marketplace_name": "US",
                        "store_name": "Kitchen Smart",
                        "store_id": "AMZN2H4K5L",
                        "page_id": "page_001",
                        "page_title": "Tumblers",
                        "count_sessions": 55422,
                        "distinct_sessions": 55422,
                        "count_visits": 55422,
                        "distinct_visits": 55422,
                        "total_dwell_time_minutes": 35234
                    },
                    {
                        "marketplace_name": "US",
                        "store_name": "Kitchen Smart",
                        "store_id": "AMZN2H4K5L",
                        "page_id": "page_002",
                        "page_title": "Kids",
                        "count_sessions": 16472,
                        "distinct_sessions": 16472,
                        "count_visits": 16472,
                        "distinct_visits": 16472,
                        "total_dwell_time_minutes": 11208
                    },
                    {
                        "marketplace_name": "US",
                        "store_name": "Kitchen Smart",
                        "store_id": "AMZN2H4K5L",
                        "page_id": "page_003",
                        "page_title": "Mixers",
                        "count_sessions": 8662,
                        "distinct_sessions": 8662,
                        "count_visits": 8662,
                        "distinct_visits": 8662,
                        "total_dwell_time_minutes": 5566
                    }
                ]
            },
            "interpretation_markdown": """**Key Insights from Exploratory Data:**

1. **Home page** receives the most traffic (95K sessions) but has lower engagement per session (0.5 min average)
2. **Tumblers page** shows exceptional engagement with 0.64 minutes per session average
3. **Coffee Makers** has strong engagement (1.23 min/session) despite lower traffic

**Recommended Actions:**
- Feature Tumblers prominently on Home page
- Analyze Coffee Makers content for engagement best practices
- A/B test Kids section layout to improve dwell time""",
            "display_order": 1
        }
    ]
    
    for example in examples:
        supabase.table("build_guide_examples").upsert(example).execute()
    print(f"✓ Created {len(examples)} examples")
    
    # 5. Create metrics definitions
    metrics = [
        {
            "guide_id": guide_uuid,
            "metric_name": "dwell_time",
            "display_name": "Dwell Time",
            "definition": "Time spent on Brand Store page in seconds",
            "metric_type": "metric",
            "display_order": 1
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "distinct_sessions",
            "display_name": "Unique Sessions",
            "definition": "Count of unique session identifiers",
            "metric_type": "metric",
            "display_order": 2
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "bsi_atc_rate",
            "display_name": "Add to Cart Rate",
            "definition": "Percentage of sessions with add-to-cart events",
            "metric_type": "metric",
            "display_order": 3
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "path_occurrences",
            "display_name": "Path Occurrences",
            "definition": "Number of users following a specific touchpoint path",
            "metric_type": "metric",
            "display_order": 4
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "ingress_type",
            "display_name": "Traffic Source Type",
            "definition": "Category of traffic source (paid, organic, internal, social)",
            "metric_type": "dimension",
            "display_order": 5
        }
    ]
    
    for metric in metrics:
        supabase.table("build_guide_metrics").upsert(metric).execute()
    print(f"✓ Created {len(metrics)} metrics")
    
    print(f"\n✅ Successfully created Amazon Brand Store Insights build guide!")
    print(f"Guide ID: {guide_id_str}")
    print(f"Sections: {len(sections)}")
    print(f"Queries: {len(queries)}")
    print(f"Examples: {len(examples)}")
    print(f"Metrics: {len(metrics)}")

if __name__ == "__main__":
    try:
        create_guide()
    except Exception as e:
        print(f"❌ Error creating guide: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)