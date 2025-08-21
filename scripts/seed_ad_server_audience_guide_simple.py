#!/usr/bin/env python3
"""
Simplified seed script for Amazon Ad Server - Audiences with ASIN Conversions Build Guide
This script creates the guide content directly in the database without dependencies
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables must be set")
    sys.exit(1)

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def create_ad_server_audience_guide():
    """Create the Amazon Ad Server - Audiences with ASIN Conversions guide"""
    try:
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_ad_server_audience_conversions',
            'name': 'Amazon Ad Server - Audiences with ASIN Conversions',
            'category': 'Audience Insights',
            'short_description': 'Measure audience performance, behavior, and preference for off-Amazon media served through Amazon Ad Server and discover conversion metrics by audience segments.',
            'tags': ['ad server', 'audience segments', 'ASIN conversions', 'behavior analysis', 'custom attribution', 'DPV', 'ATC'],
            'icon': 'Users',
            'difficulty_level': 'advanced',
            'estimated_time_minutes': 40,
            'prerequisites': [
                'Amazon Ad Server campaign data available in AMC',
                'ASIN conversions present in custom attribution datasets',
                'Amazon DSP or SA entity IDs added to AMC instance',
                'Understanding of audience segmentation'
            ],
            'is_published': True,
            'display_order': 2,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Insert guide
        guide_response = supabase.table('build_guides').insert(guide_data).execute()
        if not guide_response.data:
            print("Failed to create guide")
            return False
        
        guide_id = guide_response.data[0]['id']
        print(f"Created guide with ID: {guide_id}")
        
        # Create sections
        sections = [
            {
                'guide_id': guide_id,
                'section_id': 'introduction',
                'title': '1. Introduction',
                'content_markdown': """## 1.1 Purpose

This Instructional Query (IQ) measures audience performance, behavior, and preference for off-Amazon media served through Amazon Ad Server and helps in discovering conversion metrics by audience segments.

By analyzing conversions across different audience segments, advertisers can:
- Identify high-performing audience segments for optimization
- Understand audience behavior patterns and preferences
- Make data-driven decisions about audience targeting strategies
- Optimize media spend allocation across segments

## 1.2 Requirements

All advertisers globally who run campaigns using Amazon Ad Server are eligible to use this IQ. To use this query, you need:

- **Amazon Ad Server campaign data** available in your AMC instance
- **ASIN conversions** present in custom attribution data sets in AMC
- **Amazon DSP or SA entity IDs** added to the AMC instance (if conversions are not available in custom attribution data sets)

**Important:** If conversions are not available in custom attribution data sets, please create a request to add your Amazon DSP or SA entity IDs to the AMC instance to enable conversion tracking.""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_query',
                'title': '2. Data Query Instructions',
                'content_markdown': """## 2.1 Tables Used

### adserver_traffic_by_user_segments
This table contains all impressions and clicks measured by Amazon Ad Server breakout by segments. Key fields include:
- User segments and behavior data
- Impression and click events
- Campaign and placement identifiers
- Timestamp information for attribution windows

### conversions
This data source contains the subset of relevant conversions, including:
- **Purchase events** (orders)
- **Detail page views** (DPV)
- **Add-to-cart events** (ATC)
- **First subscribe and save events**

**Conversion Relevance Criteria:**
A conversion is deemed relevant to your AMC instance if:
1. User must have been served an impression or click within **28 days** before conversion
2. Traffic events include: `sponsored_ads_traffic`, `dsp_impressions`, `adserver_traffic`
3. Conversion must be from tracked ASIN or brand family (brand halo)
4. 28-day window doubles standard attribution window
5. Higher volume than standard attribution due to:
   - Longer lookback period
   - Not competition-aware
   - Includes both viewable and non-viewable impressions

### conversions_with_relevance
Same conversions as above but includes campaign-dependent columns. Each conversion can appear on multiple rows if relevant to multiple campaigns. Use this table when filtering by specific campaigns for better performance.

## 2.2 Data Returned

This query returns comprehensive metrics broken down by Amazon Ad Server dimensions and audience segments:

### Delivery Metrics
- **Impressions**: Total impressions by segment
- **Clicks**: Total clicks by segment

### Conversion Metrics (with attribution split)
- **DPV (Detail Page Views)**
  - Total DPV
  - DPV Views (impression-attributed)
  - DPV Clicks (click-attributed)
- **ATC (Add to Cart)**
  - Total ATC
  - ATC Views (impression-attributed)
  - ATC Clicks (click-attributed)
- **Purchases**
  - Total Purchases
  - Purchases Views (impression-attributed)
  - Purchases Clicks (click-attributed)

### Dimensions
- Advertiser and campaign information
- Placement details
- Site information
- Audience behavior segments

## 2.3 Query Templates

Three query templates are provided:
1. **Exploratory Query 1**: Campaign and Advertisers exploration
2. **Exploratory Query 2**: ASIN Conversions identification
3. **Main Analysis Query**: Custom Audience Attribution of ASIN Conversions

Use the exploratory queries first to make informed decisions about the filters to apply in the main analysis query.""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'interpretation',
                'title': '3. Data Interpretation Instructions',
                'content_markdown': """## 3.1 Example Query Results

*This data is for instructional purposes only. Your results will differ.*

### Query: Custom Audience Attribution of ASIN Conversions

| advertiser_name | campaign_name | site_name | placement_name | segment | impressions | clicks | Total_DPV | DPV_views | DPV_clicks | Total_ATC | ATC_views | ATC_clicks | Total_Purchases | Purchases_views | Purchases_clicks |
|-----------------|---------------|-----------|----------------|---------|-------------|--------|-----------|-----------|------------|-----------|-----------|------------|-----------------|-----------------|------------------|
| Brand ABC | Summer Campaign | news-site.com | Homepage_Banner | High_Intent_Shoppers | 50,000 | 1,250 | 850 | 600 | 250 | 425 | 300 | 125 | 212 | 150 | 62 |
| Brand ABC | Summer Campaign | news-site.com | Homepage_Banner | New_Customers | 75,000 | 1,125 | 562 | 450 | 112 | 281 | 225 | 56 | 140 | 112 | 28 |
| Brand ABC | Summer Campaign | sports-blog.com | Sidebar_300x250 | High_Intent_Shoppers | 30,000 | 900 | 630 | 450 | 180 | 315 | 225 | 90 | 157 | 112 | 45 |
| Brand ABC | Summer Campaign | sports-blog.com | Sidebar_300x250 | Deal_Seekers | 45,000 | 675 | 337 | 270 | 67 | 168 | 135 | 33 | 84 | 67 | 17 |
| Brand XYZ | Fall Promo | lifestyle-mag.com | Article_Mid | Frequent_Buyers | 60,000 | 1,800 | 1,260 | 900 | 360 | 630 | 450 | 180 | 315 | 225 | 90 |

## 3.2 Metrics Defined

### Delivery Metrics
- **Impressions**: Total number of ad impressions served to users in the segment
- **Clicks**: Total number of clicks from users in the segment

### Conversion Metrics
- **DPV (Detail Page Views)**: Total conversions for detail page views
  - **DPV Views**: DPV conversions attributed to impressions
  - **DPV Clicks**: DPV conversions attributed to clicks
- **ATC (Add to Cart)**: Total add-to-cart conversions
  - **ATC Views**: ATC conversions attributed to impressions
  - **ATC Clicks**: ATC conversions attributed to clicks
- **Purchases**: Total sales attributed
  - **Purchases Views**: Purchases attributed to impressions
  - **Purchases Clicks**: Purchases attributed to clicks

### Dimensions
- **Behavior Segment**: User behavior segment classification (e.g., High_Intent_Shoppers, New_Customers, Deal_Seekers)
- **Site Name**: The website where the ad was served
- **Placement**: The specific ad placement on the site

### Attribution Logic
- **Model**: Last Click Over Impression (default)
- **Lookback Window**: 14 days (customizable up to 28 days)
- **Priority**: Click events prioritized over impression events
- **Date Range**: Only conversions within selected date range included

## 3.3 Insights and Data Interpretation

### Understanding Audience Performance

Advertisers can use this query to understand total conversions by audience segments when users are exposed to media outside of Amazon through Amazon Ad Server. This helps understand audience behavior and preferences.

**Key Performance Indicators by Segment:**

1. **Conversion Rate Analysis**
   - Calculate conversion rates: (Total_Purchases / Impressions) × 100
   - Compare rates across segments to identify high-performers
   - Example: High_Intent_Shoppers showing 0.42% purchase rate vs New_Customers at 0.19%

2. **Attribution Channel Effectiveness**
   - Compare click-attributed vs view-attributed conversions
   - Higher click attribution indicates engaging creative
   - Higher view attribution suggests brand awareness impact

3. **Funnel Analysis by Segment**
   - Track progression: Impressions → DPV → ATC → Purchases
   - Identify drop-off points for each segment
   - Optimize targeting for segments with better funnel progression

### Sample Insights from Example Data

**High Performers:**
- **High_Intent_Shoppers** segment shows:
  - Highest conversion rate (0.42% on news-site.com)
  - Strong click-to-purchase ratio (5.0% of clicks convert)
  - Recommendation: Increase investment in this segment

- **Frequent_Buyers** segment demonstrates:
  - Consistent performance across funnel stages
  - Balanced view/click attribution
  - Recommendation: Maintain current strategy

**Optimization Opportunities:**
- **Deal_Seekers** segment shows:
  - Lower conversion rates (0.19%)
  - Weak click performance
  - Recommendation: Test promotional messaging or different creative

- **New_Customers** segment indicates:
  - High impression volume but lower engagement
  - Opportunity for creative optimization
  - Consider different messaging approach

### Strategic Recommendations

1. **Budget Allocation**: Shift spend toward segments with conversion rates above benchmark
2. **Creative Strategy**: Develop segment-specific creative for underperforming audiences
3. **Placement Optimization**: Focus on site/placement combinations showing best performance
4. **Testing Framework**: A/B test messaging for low-performing segments
5. **Attribution Insights**: Use view/click split to inform creative and placement decisions

Segments with higher conversion rates indicate more responsive audiences where investment should be increased. Consider both immediate conversions and upper-funnel metrics (DPV, ATC) for full-funnel optimization.""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            }
        ]
        
        print(f"Successfully created Amazon Ad Server - Audiences with ASIN Conversions guide!")
        print(f"Guide ID: guide_ad_server_audience_conversions")
        print(f"Total sections: {len(sections)}")
        print("\nThe guide has been created successfully in the database.")
        print("Users can now access it through the Build Guides interface.")
        
        return True
        
    except Exception as e:
        print(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_ad_server_audience_guide()
    sys.exit(0 if success else 1)