#!/usr/bin/env python3

"""
Seed script for Experian Vehicle Purchase Attribution Build Guide
Creates a comprehensive guide for measuring vehicle purchase conversions
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    sys.exit(1)

supabase: Client = create_client(url, key)

def create_experian_vehicle_guide():
    """Create the Experian Vehicle Purchase Attribution build guide"""
    
    # 1. Create the main guide
    guide_id = "guide_experian_vehicle_attribution"
    
    guide_data = {
        "guide_id": guide_id,
        "name": "Ad-Attributed Vehicle Purchases from Experian Auto",
        "category": "Conversion Analysis",
        "short_description": "Measure the impact of Amazon DSP campaigns on vehicle purchases using Experian DMV data with customizable attribution models and lookback windows",
        "difficulty_level": "Advanced",
        "estimated_time_minutes": 60,
        "prerequisites": [
            "Experian Vehicle Purchase Insights subscription added to AMC instance",
            "DSP campaigns ended at least 60 days ago (for complete attribution)",
            "US-based automotive advertiser account",
            "Understanding of attribution models and lookback windows",
            "Selected vehicle makes configured in subscription"
        ],
        "tags": ["Vehicle purchases", "Experian data", "Attribution modeling", "Automotive", "DSP analysis", "Conversion tracking", "DMV data", "Purchase journey"],
        "icon": "Car",
        "display_order": 10,
        "is_published": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Check if guide exists
    existing = supabase.table('build_guides').select("*").eq('guide_id', guide_id).execute()
    
    if existing.data:
        print(f"Guide {guide_id} already exists, updating...")
        result = supabase.table('build_guides').update(guide_data).eq('guide_id', guide_id).execute()
        guide_db_id = existing.data[0]['id']
    else:
        print(f"Creating guide {guide_id}...")
        result = supabase.table('build_guides').insert(guide_data).execute()
        guide_db_id = result.data[0]['id']
    
    # 2. Create guide sections
    sections = [
        {
            "section_id": "introduction",
            "title": "Introduction",
            "display_order": 1,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Purpose

Through their partnership with the Department of Motor Vehicles (DMV), Experian enables automotive advertisers to measure the impact of Amazon DSP campaigns against actual vehicle purchases. This analysis helps you understand which channels and campaigns are most effective at attracting vehicle buyers and driving purchases, enabling better campaign planning and media investment optimization.

## Attribution Model Options

### First-Touch Attribution
Identifies which campaigns are most efficient at reaching new vehicle buyers for the first time. This model gives 100% credit to the first touchpoint in the customer journey, helping you understand which campaigns are best at initiating the purchase consideration process.

### Last-Touch Attribution  
Determines which campaigns are most efficient at driving vehicle purchase conversions. This model gives 100% credit to the last touchpoint before purchase, revealing which campaigns are most effective at closing the sale.

### Customizable Lookback Window
Adjust the attribution window from the default 60 days to match your typical purchase consideration cycle. Longer windows capture more of the customer journey but may include less relevant touchpoints.

### Event Type Prioritization
Customize which touchpoints (impressions, clicks, pixel conversions) are valued for attribution. By default, pixel conversions have highest priority, followed by clicks, then impressions.

## What You'll Learn

- **Total ad-attributed vehicle purchases** by campaign and channel
- **Attribution breakdown** by event type (impression, click, pixel conversion)  
- **Cost per attributed vehicle purchase** for ROI analysis
- **Vehicle purchase rates** by campaign type and creative format
- **Optimal channel mix** for automotive marketing investment
- **Impact of different attribution models** on campaign performance measurement
- **Purchase patterns** by vehicle type, class, and fuel type
- **Geographic distribution** of attributed purchases"""
        },
        {
            "section_id": "requirements",
            "title": "Requirements & Data Considerations",
            "display_order": 2,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Essential Requirements

| Requirement | Description |
|-------------|-------------|
| **Advertiser Type** | US-based automotive advertiser account |
| **Data Subscription** | Experian Vehicle Purchase Insights added to AMC instance |
| **Campaign Timing** | DSP campaigns ended at least 60 days ago for complete attribution |
| **Vehicle Selection** | Specific vehicle makes selected in subscription configuration |
| **AMC Setup** | Active AMC instance with DSP campaign data |

## Data Lag Considerations

### Two-Month Processing Delay
Experian vehicle purchase data has an inherent two-month lag due to DMV processing times:
- Current month: No data available
- Prior month: Partial data only
- Two months ago: Complete data available

### Example Timeline
If analyzing in December 2024:
- December 2024 purchases: Not yet available
- November 2024 purchases: Incomplete (~50-70% available)
- October 2024 purchases: Complete data available
- September 2024 and earlier: Complete historical data

## Historical Data Availability

The Experian dataset includes:
- **12.5 months** of historical vehicle purchase data
- **Monthly refresh** with new purchase records
- **Retroactive updates** as DMV records are processed
- **Identity matching** to AMC user IDs for attribution

## Important Limitations

⚠️ **Cannot be used for market-level insights**: Data only includes purchases matched to AMC identity
⚠️ **Not for total market calculations**: Represents attributed purchases only, not all vehicle sales  
⚠️ **Subscription-dependent**: Only includes makes/models selected in your subscription
⚠️ **US-only**: Limited to US vehicle registrations and DMV data"""
        },
        {
            "section_id": "data_schema",
            "title": "Data Schema & Tables",
            "display_order": 3,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Primary Tables Used

### experian_vehicle_purchases
The core table containing DMV vehicle purchase data matched to AMC identities.

| Column Name | Description | Data Type | Aggregation Threshold |
|-------------|-------------|-----------|----------------------|
| user_id | Resolved AMC identity | String | VERY_HIGH |
| purchase_date | Date of vehicle purchase | Date | LOW |
| vehicle_model_year | Model year of purchased vehicle | Integer | LOW |
| new_or_used | N=New, U=Used vehicle | String | LOW |
| vehicle_make | Manufacturer/brand | String | LOW |
| vehicle_model | Specific model name | String | LOW |
| vehicle_type | Type (SUV, Sedan, Truck, etc.) | String | LOW |
| vehicle_class | Class (Luxury, Economy, etc.) | String | LOW |
| vehicle_fuel_type | Fuel type (Gas, Electric, Hybrid) | String | LOW |
| vehicle_registered_state | State of registration | String | MEDIUM |
| vehicle_trim | Trim level details | String | LOW |
| vehicle_body_style | Body style category | String | LOW |

### dsp_impressions
DSP impression events with campaign and spend data.

| Column Name | Description | Data Type |
|-------------|-------------|-----------|
| user_id | AMC user identifier | String |
| impression_dt | Timestamp of impression | Timestamp |
| campaign | Campaign name | String |
| advertiser | Advertiser name | String |
| total_cost | Media spend | Decimal |
| creative_id | Creative identifier | String |
| placement | Placement details | String |

### dsp_clicks
DSP click events for engagement tracking.

| Column Name | Description | Data Type |
|-------------|-------------|-----------|
| user_id | AMC user identifier | String |
| click_dt | Timestamp of click | Timestamp |
| campaign | Campaign name | String |
| advertiser | Advertiser name | String |
| creative_id | Creative identifier | String |

### amazon_attributed_events_by_traffic_time
Pixel conversion events from advertiser websites.

| Column Name | Description | Data Type |
|-------------|-------------|-----------|
| user_id | AMC user identifier | String |
| traffic_dt | Timestamp of pixel fire | Timestamp |
| conversion_event_dt | Conversion timestamp | Timestamp |
| event_name | Conversion event type | String |
| advertiser | Advertiser name | String |

## Aggregation Thresholds

AMC enforces minimum aggregation thresholds to protect user privacy:

- **VERY_HIGH (100+)**: user_id fields require 100+ unique users
- **HIGH (50+)**: Combination of sensitive fields
- **MEDIUM (20+)**: Geographic data like state
- **LOW (10+)**: Most vehicle attributes

Always ensure your queries meet these thresholds to avoid suppressed results."""
        },
        {
            "section_id": "attribution_configuration",
            "title": "Attribution Configuration",
            "display_order": 4,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Attribution Model Selection

### First-Touch Attribution (Default)

First-touch attribution credits the initial campaign that introduced a customer to your brand within the lookback window. This model is valuable for understanding which campaigns are most effective at generating awareness and initiating the purchase journey.

```sql
-- First-touch: Orders by oldest exposure first
ROW_NUMBER() OVER(
    PARTITION BY vehicle_purchase_id 
    ORDER BY match_type ASC, match_age DESC
) = 1
```

**Use Cases:**
- Identifying top-of-funnel campaign effectiveness
- Understanding awareness drivers
- Optimizing reach campaigns
- Budget allocation for new customer acquisition

### Last-Touch Attribution

Last-touch attribution credits the final campaign interaction before purchase. This model helps identify which campaigns are most effective at driving conversions and closing sales.

```sql
-- Last-touch: Orders by newest exposure first  
ROW_NUMBER() OVER(
    PARTITION BY vehicle_purchase_id 
    ORDER BY match_type ASC, match_age ASC
) = 1
```

**Use Cases:**
- Identifying conversion drivers
- Optimizing retargeting campaigns
- Understanding purchase triggers
- Lower-funnel campaign effectiveness

## Event Type Prioritization

Control which interaction types receive attribution credit when multiple events occur:

### Default Priority Order
1. **Pixel Conversions** (Highest Priority)
   - Indicates deepest engagement
   - Website actions like configurator usage
   - Test drive scheduling
   
2. **Clicks** (Medium Priority)
   - Active engagement signal
   - Intent to learn more
   - Direct response indicator

3. **Impressions** (Lowest Priority)
   - Awareness and reach
   - Brand exposure
   - View-through attribution

### Custom Priority Configuration

Modify the CASE statement in the query to adjust priorities:

```sql
CASE 
    WHEN event_type = 'pixel' THEN 1  -- Highest priority
    WHEN event_type = 'click' THEN 2  
    WHEN event_type = 'impression' THEN 3  -- Lowest priority
END AS match_type
```

## Attribution Window Configuration

### Default: 60 Days
The standard 60-day window balances data completeness with relevance for most automotive purchase cycles.

### Customization Options

| Window | Use Case | Considerations |
|--------|----------|----------------|
| **30 days** | Promotional campaigns, used vehicles | May miss longer consideration journeys |
| **60 days** | Standard analysis, balanced view | Default recommendation |
| **90 days** | Luxury vehicles, first-time buyers | Captures extended research phase |
| **120+ days** | New model launches, custom orders | Maximum journey visibility |

### Window Selection Factors

Consider these factors when choosing your attribution window:

- **Vehicle Type**: Luxury and new models typically have longer consideration periods
- **Price Point**: Higher prices correlate with longer research phases  
- **Customer Type**: First-time buyers take longer than repeat customers
- **Campaign Type**: Awareness campaigns need longer windows than retargeting
- **Seasonality**: Account for model year transitions and sales events"""
        },
        {
            "section_id": "query_customization",
            "title": "Query Customization Guide",
            "display_order": 5,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Query Customization Points

The main attribution query includes 8 customization points to tailor the analysis to your specific needs:

### 1. Campaign Selection (Required)

Specify which DSP campaigns to include in the attribution analysis:

```sql
-- Single campaign
WHERE LOWER(campaign) = 'q3 2024 - model launch'

-- Multiple campaigns  
WHERE LOWER(campaign) IN (
    'q3 2024 - model launch',
    'q3 2024 - year end sales',
    'q3 2024 - certified pre-owned'
)

-- Campaign pattern matching
WHERE LOWER(campaign) LIKE '%2024%'
```

### 2. Attribution Model

Toggle between first-touch and last-touch attribution:

```sql
-- First-touch (default)
ORDER BY match_type ASC, match_age DESC

-- Last-touch
ORDER BY match_type ASC, match_age ASC
```

### 3. Attribution Window

Adjust the lookback period for attribution:

```sql
-- Default 60 days
AND exposure_date >= purchase_date - INTERVAL '60' DAY

-- Extended 90-day window
AND exposure_date >= purchase_date - INTERVAL '90' DAY

-- Short 30-day window for promotions
AND exposure_date >= purchase_date - INTERVAL '30' DAY
```

### 4. Event Type Inclusion

Control which interaction types to include:

```sql
-- All event types (default)
-- No WHERE clause needed

-- Exclude impressions (clicks and pixels only)
WHERE event_type IN ('click', 'pixel')

-- Clicks only analysis
WHERE event_type = 'click'
```

### 5. Event Priority Ordering

Customize the priority of different event types:

```sql
-- Standard priority (pixel > click > impression)
CASE 
    WHEN event_type = 'pixel' THEN 1
    WHEN event_type = 'click' THEN 2
    WHEN event_type = 'impression' THEN 3
END

-- Click-first priority
CASE 
    WHEN event_type = 'click' THEN 1
    WHEN event_type = 'pixel' THEN 2
    WHEN event_type = 'impression' THEN 3
END
```

### 6. Vehicle Filtering

Filter results by vehicle attributes:

```sql
-- Specific makes
AND vehicle_make IN ('Toyota', 'Honda', 'Ford')

-- Vehicle type
AND vehicle_type = 'SUV'

-- New vehicles only
AND new_or_used = 'N'

-- Luxury segment
AND vehicle_class = 'Luxury'

-- Electric vehicles
AND vehicle_fuel_type IN ('Electric', 'Plug-in Hybrid')
```

### 7. Date Range

Control the analysis time period:

```sql
-- Last 6 months
WHERE purchase_date >= CURRENT_DATE - INTERVAL '6' MONTH

-- Specific quarter
WHERE purchase_date BETWEEN '2024-07-01' AND '2024-09-30'

-- Year-to-date
WHERE purchase_date >= DATE_TRUNC('year', CURRENT_DATE)
```

### 8. Spend Calculations

Adjust how media spend is calculated:

```sql
-- Standard CPM-based calculation
SUM(impressions * (total_cost / 1000))

-- Include frequency capping adjustments
SUM(DISTINCT impressions * (total_cost / 1000))

-- Weight by viewability metrics (if available)
SUM(impressions * viewability_rate * (total_cost / 1000))
```

## Query Testing Recommendations

1. **Start Small**: Test with a single campaign before expanding
2. **Validate Totals**: Check purchase counts against known benchmarks
3. **Compare Models**: Run both attribution models to understand differences
4. **Iterate Windows**: Test multiple attribution windows
5. **Check Thresholds**: Ensure results meet AMC aggregation minimums"""
        },
        {
            "section_id": "data_interpretation",
            "title": "Data Interpretation & Analysis",
            "display_order": 6,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Understanding Your Results

### Key Metrics Explained

| Metric | Definition | Strategic Use |
|--------|------------|---------------|
| **vehicle_purchases_total** | Total ad-attributed purchases | Overall campaign impact |
| **impressions_attributed** | Purchases attributed to impressions | Upper-funnel effectiveness |
| **clicks_attributed** | Purchases attributed to clicks | Engagement quality |
| **pixel_attributed** | Purchases attributed to pixels | Website conversion power |
| **spend_per_vehicle_purchase** | Total spend / attributed purchases | Efficiency benchmark |
| **vehicle_purchase_rate** | Purchases / unique reach | Conversion effectiveness |
| **unique_reach** | Distinct users exposed | Campaign scale |

## Example Analysis Results

### Campaign Performance Comparison

| Campaign | Attribution Model | Vehicle Purchases | Spend per Purchase | Purchase Rate | Primary Attribution |
|----------|------------------|-------------------|-------------------|---------------|-------------------|
| Q3'24 - Streaming TV - Awareness | First Touch | 556 | $98.22 | 0.15% | 89% Impressions |
| Q3'24 - Video Ads - Consideration | First Touch | 204 | $145.70 | 0.07% | 62% Pixels |
| Q3'24 - Display - Retargeting | First Touch | 58 | $1,896.52 | 0.01% | 94% Pixels |
| Q3'24 - Streaming TV - Awareness | Last Touch | 287 | $190.32 | 0.08% | 76% Impressions |
| Q3'24 - Video Ads - Consideration | Last Touch | 341 | $87.16 | 0.11% | 71% Pixels |
| Q3'24 - Display - Retargeting | Last Touch | 190 | $579.00 | 0.02% | 97% Pixels |

### Key Insights from Results

#### Channel Effectiveness Analysis

**Streaming TV Performance:**
- Most efficient for first-touch attribution ($98/purchase)
- Highest purchase rate (0.15%) indicating strong audience quality
- Primarily impression-driven attribution (89%)
- Excellent for awareness and purchase initiation

**Video Campaign Dynamics:**
- Balanced performance across attribution models
- Strong pixel attribution (62-71%) shows website engagement
- Better last-touch performance suggests consideration influence
- Good middle-funnel effectiveness

**Display Retargeting Observations:**
- High cost per purchase in first-touch model
- Improved efficiency in last-touch attribution
- Almost entirely pixel-driven attribution (94-97%)
- Clear lower-funnel/closing role

## Attribution Model Comparison

### First-Touch vs Last-Touch Insights

| Insight Category | First-Touch Leaders | Last-Touch Leaders | Strategic Implication |
|------------------|--------------------|--------------------|----------------------|
| **Volume** | Streaming TV (556) | Video Ads (341) | Different channels drive initiation vs completion |
| **Efficiency** | Streaming TV ($98) | Video Ads ($87) | Optimize budget by funnel position |
| **Purchase Rate** | Streaming TV (0.15%) | Video Ads (0.11%) | Quality of reach varies by model |
| **Attribution Type** | Impressions (73%) | Pixels (68%) | Engagement deepens through journey |

## Strategic Recommendations

### 1. Channel Mix Optimization
- **Increase Streaming TV** for new customer acquisition
- **Maintain Video** for consideration and research phase
- **Optimize Display** for closing and retargeting only

### 2. Budget Allocation Framework
```
First-Touch Winners (60% budget):
- Streaming TV: 40%
- Video Awareness: 20%

Last-Touch Winners (40% budget):
- Video Consideration: 25%
- Display Retargeting: 15%
```

### 3. Campaign Sequencing
1. **Weeks 1-4**: Heavy Streaming TV for awareness
2. **Weeks 3-8**: Layer in Video for consideration
3. **Weeks 6-12**: Add Display retargeting for conversion
4. **Weeks 10+**: Maintain display for long-cycle buyers

### 4. Performance Benchmarks

| Metric | Excellent | Good | Needs Improvement |
|--------|-----------|------|-------------------|
| **Spend per Purchase** | <$150 | $150-500 | >$500 |
| **Purchase Rate** | >0.10% | 0.05-0.10% | <0.05% |
| **Pixel Attribution %** | 30-70% | 20-30% or 70-80% | <20% or >80% |"""
        },
        {
            "section_id": "advanced_analysis",
            "title": "Advanced Analysis Techniques",
            "display_order": 7,
            "is_collapsible": True,
            "default_expanded": False,
            "content_markdown": """## Multi-Touch Attribution Analysis

While AMC's standard attribution models are single-touch, you can create custom multi-touch views:

### Fractional Attribution Approach

```sql
-- Assign fractional credit based on touchpoint position
WITH journey_mapping AS (
    SELECT 
        vehicle_purchase_id,
        campaign,
        event_type,
        ROW_NUMBER() OVER (PARTITION BY vehicle_purchase_id ORDER BY exposure_date) as touchpoint_order,
        COUNT(*) OVER (PARTITION BY vehicle_purchase_id) as total_touchpoints,
        CASE 
            WHEN ROW_NUMBER() OVER (PARTITION BY vehicle_purchase_id ORDER BY exposure_date) = 1 THEN 0.4  -- First touch: 40%
            WHEN ROW_NUMBER() OVER (PARTITION BY vehicle_purchase_id ORDER BY exposure_date DESC) = 1 THEN 0.4  -- Last touch: 40%
            ELSE 0.2 / NULLIF(COUNT(*) OVER (PARTITION BY vehicle_purchase_id) - 2, 0)  -- Middle touches: share 20%
        END as attribution_weight
    FROM attribution_base
)
```

## Seasonality and Market Adjustments

### Seasonal Patterns in Vehicle Purchases

| Period | Index | Key Factors | Campaign Adjustments |
|--------|-------|-------------|---------------------|
| **Q1 (Jan-Mar)** | 85 | Post-holiday slowdown, tax refunds in March | Focus on value messaging, tax refund targeting |
| **Q2 (Apr-Jun)** | 110 | Spring selling season, Memorial Day | Increase awareness campaigns, family focus |
| **Q3 (Jul-Sep)** | 120 | Model year clearance, back-to-school | Heavy promotional activity, clearance events |
| **Q4 (Oct-Dec)** | 95 | Year-end sales, weather impact | Holiday campaigns, year-end tax benefits |

### Market Share Context

Combine attribution data with market metrics:

```sql
-- Calculate share of attributed purchases
WITH market_totals AS (
    SELECT 
        DATE_TRUNC('month', purchase_date) as month,
        COUNT(DISTINCT vehicle_purchase_id) as total_purchases
    FROM experian_vehicle_purchases
    WHERE vehicle_make IN ('Toyota', 'Honda', 'Ford')  -- Your competitive set
    GROUP BY 1
)
```

## Customer Lifetime Value Integration

### Purchase Cycle Analysis

Track repeat purchase patterns and loyalty:

| Customer Segment | Avg Purchase Cycle | LTV Multiplier | Attribution Window |
|------------------|-------------------|----------------|-------------------|
| **Luxury Buyers** | 3.5 years | 3.2x | 120 days |
| **Mass Market** | 5.2 years | 2.1x | 60 days |
| **Fleet/Commercial** | 2.8 years | 4.5x | 30 days |
| **First-Time Buyers** | 6.7 years | 1.8x | 90 days |

## Competitive Conquest Analysis

### Identifying Conquest Opportunities

Analyze which campaigns effectively convert competitive owners:

```sql
-- Assuming you have previous vehicle data
WITH conquest_analysis AS (
    SELECT 
        e.vehicle_make as purchased_make,
        LAG(e.vehicle_make) OVER (PARTITION BY e.user_id ORDER BY e.purchase_date) as previous_make,
        a.campaign,
        COUNT(DISTINCT e.vehicle_purchase_id) as conquest_purchases
    FROM experian_vehicle_purchases e
    JOIN attribution_results a ON e.vehicle_purchase_id = a.vehicle_purchase_id
    GROUP BY 1, 2, 3
)
```

## Geographic Performance Analysis

### Regional Attribution Patterns

| Region | Indexing | Top Performing Channels | Optimization Strategy |
|--------|----------|------------------------|----------------------|
| **Northeast** | 92 | Video (45%), Display (30%) | Increase digital presence |
| **Southeast** | 108 | Streaming TV (55%), Video (25%) | Maintain TV focus |
| **Midwest** | 95 | Streaming TV (48%), Display (28%) | Test radio integration |
| **Southwest** | 112 | Video (42%), Streaming TV (35%) | Mobile-first approach |
| **West** | 104 | Display (38%), Video (37%) | Digital-heavy mix |

## Cross-Device Attribution

### Device Journey Mapping

Understanding how users move across devices before purchase:

1. **Research Phase** (Desktop: 65%, Mobile: 30%, Tablet: 5%)
2. **Comparison Phase** (Desktop: 55%, Mobile: 40%, Tablet: 5%)
3. **Dealer Locator** (Mobile: 75%, Desktop: 25%)
4. **Purchase Decision** (In-person: 85%, Online: 15%)

## Incrementality Testing

### Holdout Group Design

Structure geo-based holdout tests:

```sql
-- Define treatment and control DMAs
WITH holdout_test AS (
    SELECT 
        dma_code,
        CASE 
            WHEN dma_code IN ('501', '602', '803') THEN 'Control'
            ELSE 'Treatment'
        END as test_group,
        COUNT(DISTINCT vehicle_purchase_id) as purchases,
        SUM(total_spend) as spend
    FROM attribution_base
    GROUP BY 1, 2
)
```"""
        },
        {
            "section_id": "implementation_strategy",
            "title": "Implementation Strategy",
            "display_order": 8,
            "is_collapsible": True,
            "default_expanded": False,
            "content_markdown": """## Step-by-Step Implementation Guide

### Phase 1: Setup and Configuration (Week 1)

#### Day 1-2: Subscription Setup
1. **Add Experian Vehicle Purchase Insights** to your AMC instance
2. **Select vehicle makes** relevant to your business
3. **Verify data flow** with exploratory query
4. **Document available makes/models** for analysis

#### Day 3-4: Historical Analysis
1. **Identify completed campaigns** (60+ days old)
2. **Gather campaign metadata** (dates, budgets, objectives)
3. **Map campaign taxonomy** to funnel stages
4. **Create campaign groupings** for analysis

#### Day 5: Initial Query Execution
1. **Run exploratory query** to understand data volume
2. **Test attribution query** with single campaign
3. **Validate results** against known metrics
4. **Document any data gaps** or issues

### Phase 2: Attribution Analysis (Week 2)

#### Day 6-7: First-Touch Analysis
1. **Execute first-touch query** for all campaigns
2. **Export results** for detailed analysis
3. **Calculate key metrics** (efficiency, reach, rate)
4. **Identify top performers** by channel

#### Day 8-9: Last-Touch Analysis
1. **Execute last-touch query** for same campaigns
2. **Compare results** to first-touch
3. **Analyze attribution shift** between models
4. **Document channel roles** in journey

#### Day 10: Attribution Window Testing
1. **Test 30, 60, 90-day windows**
2. **Analyze volume vs relevance tradeoff**
3. **Select optimal window** for your cycle
4. **Document rationale** for selection

### Phase 3: Insights Development (Week 3)

#### Day 11-12: Performance Analysis
1. **Calculate ROI metrics** by campaign
2. **Benchmark against goals** and industry
3. **Identify optimization opportunities**
4. **Create performance dashboard**

#### Day 13-14: Strategic Recommendations
1. **Develop channel mix recommendations**
2. **Create budget allocation model**
3. **Design campaign sequencing strategy**
4. **Build measurement framework**

#### Day 15: Stakeholder Reporting
1. **Create executive summary**
2. **Build detailed analysis deck**
3. **Prepare optimization roadmap**
4. **Schedule review meetings**

## Ongoing Optimization Process

### Monthly Analysis Cycle

| Week | Activities | Deliverables |
|------|------------|--------------|
| **Week 1** | Data refresh, query execution | Updated attribution results |
| **Week 2** | Performance analysis, trending | Monthly performance report |
| **Week 3** | Optimization testing, adjustments | Test results and learnings |
| **Week 4** | Planning, forecasting | Next month campaign plan |

### Quarterly Deep Dives

#### Q1: Attribution Model Review
- Test alternative attribution approaches
- Validate model accuracy
- Adjust for market changes
- Update benchmarks

#### Q2: Customer Journey Mapping
- Analyze path to purchase
- Identify journey bottlenecks
- Optimize touchpoint sequence
- Enhance personalization

#### Q3: Competitive Analysis
- Benchmark against competition
- Identify conquest opportunities
- Analyze share of voice
- Adjust positioning

#### Q4: Annual Planning
- Synthesize year's learnings
- Develop next year strategy
- Set performance targets
- Allocate annual budget

## Success Metrics Framework

### Primary KPIs

| Metric | Target | Measurement Frequency |
|--------|--------|----------------------|
| **Cost per Attributed Purchase** | <$200 | Weekly |
| **Purchase Rate** | >0.10% | Weekly |
| **Attribution Coverage** | >60% | Monthly |
| **ROI** | >5:1 | Monthly |

### Secondary Metrics

| Metric | Target | Measurement Frequency |
|--------|--------|----------------------|
| **New vs Used Mix** | Match inventory | Monthly |
| **Geographic Coverage** | All key DMAs | Monthly |
| **Model Mix** | Align with goals | Quarterly |
| **Conquest Rate** | >20% | Quarterly |

## Common Pitfalls to Avoid

### 1. Incomplete Attribution Window
**Issue**: Analyzing campaigns too soon after completion
**Solution**: Always wait 60+ days for complete data

### 2. Ignoring Data Lag
**Issue**: Including recent months with incomplete data
**Solution**: Exclude current and prior month from analysis

### 3. Over-Relying on Single Model
**Issue**: Using only first or last-touch attribution
**Solution**: Compare both models for complete picture

### 4. Neglecting Seasonality
**Issue**: Comparing different seasonal periods
**Solution**: Use year-over-year or indexed comparisons

### 5. Missing Event Types
**Issue**: Excluding impression or pixel data
**Solution**: Include all event types, then filter if needed"""
        },
        {
            "section_id": "troubleshooting",
            "title": "Troubleshooting Guide",
            "display_order": 9,
            "is_collapsible": True,
            "default_expanded": False,
            "content_markdown": """## Common Issues and Solutions

### Issue 1: No Results Returned

#### Symptoms
- Query returns empty dataset
- Zero attributed purchases despite known sales

#### Diagnostic Steps
1. **Verify subscription is active**
   ```sql
   SELECT DISTINCT vehicle_make 
   FROM experian_vehicle_purchases 
   WHERE purchase_date >= CURRENT_DATE - INTERVAL '90' DAY
   ```

2. **Check campaign names match exactly**
   ```sql
   SELECT DISTINCT campaign 
   FROM dsp_impressions 
   WHERE LOWER(campaign) LIKE '%your_campaign%'
   ```

3. **Confirm date ranges overlap**
   - Campaigns must be 60+ days old
   - Purchase data has 2-month lag

#### Solutions
- ✅ Ensure Experian subscription includes your vehicle makes
- ✅ Use exact campaign names from DSP
- ✅ Adjust date ranges to account for data lag
- ✅ Verify user_id matching between tables

### Issue 2: Lower Than Expected Attribution

#### Symptoms
- Attribution counts seem low
- Known purchasers not appearing
- Large gap between sales and attribution

#### Diagnostic Steps
1. **Check attribution window**
   - Default 60 days may be too short
   - Test 90 or 120-day windows

2. **Verify all event types included**
   - Impressions often account for 60%+ of attribution
   - Don't exclude event types initially

3. **Confirm identity matching**
   - Not all purchases match to AMC identity
   - Typical match rates: 15-30%

#### Solutions
- ✅ Extend attribution window to 90+ days
- ✅ Include all event types (impressions, clicks, pixels)
- ✅ Accept that not all purchases will match
- ✅ Use results for relative performance, not absolutes

### Issue 3: Data Freshness Issues

#### Symptoms
- Recent purchases not appearing
- Data seems outdated
- Inconsistent counts over time

#### Understanding Data Lag
```
Current Date: December 15, 2024

December 2024: ❌ No data (current month)
November 2024: ⚠️ ~60% complete (prior month) 
October 2024: ✅ 100% complete (2 months ago)
September 2024: ✅ 100% complete (3+ months ago)
```

#### Solutions
- ✅ Exclude current and prior month from analysis
- ✅ Run analysis on 3+ month old data only
- ✅ Schedule monthly updates for trending
- ✅ Set stakeholder expectations on data lag

### Issue 4: Aggregation Threshold Errors

#### Symptoms
- Query fails with privacy error
- Results show as "suppressed"
- Certain segments missing

#### Common Threshold Violations
| Field Combination | Minimum Users Required |
|-------------------|----------------------|
| user_id alone | 100+ |
| state + model | 20+ |
| make + model + trim | 50+ |
| All dimensions | 100+ |

#### Solutions
- ✅ Reduce granularity of analysis
- ✅ Aggregate to higher levels (make vs model)
- ✅ Remove sparse dimensions
- ✅ Increase date range for more users

### Issue 5: Campaign Name Mismatches

#### Symptoms
- Known campaigns not showing results
- Partial campaign data only
- Inconsistent attribution

#### Diagnostic Query
```sql
-- Find all campaign name variations
SELECT DISTINCT 
    campaign,
    COUNT(DISTINCT user_id) as users,
    MIN(impression_dt) as first_imp,
    MAX(impression_dt) as last_imp
FROM dsp_impressions
WHERE impression_dt >= CURRENT_DATE - INTERVAL '180' DAY
GROUP BY 1
ORDER BY 2 DESC
```

#### Solutions
- ✅ Use LOWER() function for case-insensitive matching
- ✅ Use LIKE with wildcards for partial matches
- ✅ Create campaign mapping table for consistency
- ✅ Standardize naming conventions going forward

### Issue 6: Spend Calculation Discrepancies

#### Symptoms
- Spend doesn't match DSP reports
- Cost per purchase seems wrong
- Missing or duplicate spend

#### Common Causes
1. **Partial impression delivery**
2. **Multiple attribution of spend**
3. **Currency or unit mismatches**
4. **Date range differences**

#### Solutions
- ✅ Verify spend calculation formula
- ✅ Check for duplicate impression records
- ✅ Confirm currency and CPM units
- ✅ Align date ranges with DSP reports

## Performance Optimization Tips

### Query Performance

#### Slow Query Issues
```sql
-- Add date filters early in CTEs
WITH filtered_purchases AS (
    SELECT * FROM experian_vehicle_purchases
    WHERE purchase_date >= '2024-07-01'  -- Filter early
    AND purchase_date <= '2024-09-30'
)

-- Use appropriate JOIN types
LEFT JOIN for optional matches
INNER JOIN for required matches

-- Limit columns selected
SELECT only needed columns, not SELECT *
```

### Memory Management
- Process one quarter at a time for large datasets
- Use temporary tables for complex joins
- Clear cache between runs if needed

### Best Practices Checklist

✅ **Before Running Queries:**
- [ ] Verify Experian subscription is active
- [ ] Confirm campaigns are 60+ days old
- [ ] Check that selected makes are in subscription
- [ ] Review attribution model selection
- [ ] Set appropriate attribution window

✅ **During Analysis:**
- [ ] Monitor query execution time
- [ ] Validate results against benchmarks
- [ ] Check for aggregation threshold issues
- [ ] Document any anomalies

✅ **After Analysis:**
- [ ] Export results for backup
- [ ] Create summary documentation
- [ ] Schedule follow-up analysis
- [ ] Share insights with stakeholders"""
        }
    ]
    
    # Delete existing sections for this guide
    supabase.table('build_guide_sections').delete().eq('guide_id', guide_db_id).execute()
    
    # Insert all sections
    for section in sections:
        section['guide_id'] = guide_db_id
        supabase.table('build_guide_sections').insert(section).execute()
    
    print(f"Created {len(sections)} sections")
    
    # 3. Create queries
    queries = [
        {
            "query_id": f"{guide_id}_explore",
            "query_name": "Explore Available Vehicle Makes and Models",
            "query_type": "exploratory",
            "query_sql": """-- Explore available vehicle makes and models in your Experian subscription
-- This query helps you understand what vehicle data is available for analysis

SELECT 
    vehicle_make,
    vehicle_model,
    vehicle_type,
    vehicle_class,
    new_or_used,
    vehicle_fuel_type,
    COUNT(DISTINCT user_id) as unique_purchasers,
    COUNT(*) as total_purchases
FROM experian_vehicle_purchases
WHERE purchase_date >= CURRENT_DATE - INTERVAL '180' DAY
    -- Exclude incomplete recent months
    AND purchase_date < DATE_TRUNC('month', CURRENT_DATE - INTERVAL '2' MONTH)
GROUP BY 1, 2, 3, 4, 5, 6
HAVING COUNT(DISTINCT user_id) >= 100  -- Meet aggregation threshold
ORDER BY total_purchases DESC
LIMIT 100""",
            "query_description": "Explores available vehicle makes, models, and attributes in your Experian Vehicle Purchase Insights subscription. Use this to understand what vehicles are available for attribution analysis.",
            "parameters": [],
            "order_index": 1
        },
        {
            "query_id": f"{guide_id}_attribution",
            "query_name": "Vehicle Purchase Attribution Analysis",
            "query_type": "main_analysis",
            "query_sql": """-- Ad-Attributed Vehicle Purchase Analysis with Customizable Attribution Models
-- Measures the impact of DSP campaigns on actual vehicle purchases using Experian DMV data

WITH 
-- CUSTOMIZATION POINT 1: Select your DSP campaigns
campaign_filter AS (
    SELECT DISTINCT campaign
    FROM dsp_impressions
    WHERE LOWER(campaign) IN (
        -- === REPLACE WITH YOUR CAMPAIGN NAMES ===
        'q3 2024 - streaming tv - awareness',
        'q3 2024 - video ads - consideration',
        'q3 2024 - display ads - retargeting'
    )
),

-- Get vehicle purchases with data lag handling
vehicle_purchases AS (
    SELECT 
        user_id,
        purchase_date,
        vehicle_make,
        vehicle_model,
        vehicle_type,
        vehicle_class,
        new_or_used,
        vehicle_fuel_type,
        vehicle_registered_state,
        CONCAT(user_id, '_', purchase_date) as vehicle_purchase_id
    FROM experian_vehicle_purchases
    WHERE purchase_date >= CURRENT_DATE - INTERVAL '365' DAY
        -- Exclude incomplete recent months due to DMV processing lag
        AND purchase_date < DATE_TRUNC('month', CURRENT_DATE - INTERVAL '2' MONTH)
        -- CUSTOMIZATION POINT 2: Filter specific vehicle attributes if needed
        -- AND vehicle_make IN ('Toyota', 'Honda', 'Ford')
        -- AND new_or_used = 'N'
        -- AND vehicle_type = 'SUV'
),

-- Collect all DSP touchpoints
dsp_touchpoints AS (
    -- Impressions
    SELECT 
        i.user_id,
        i.campaign,
        i.advertiser,
        'impression' as event_type,
        i.impression_dt as exposure_date,
        i.total_cost / 1000.0 as event_cost  -- CPM to unit cost
    FROM dsp_impressions i
    INNER JOIN campaign_filter cf ON i.campaign = cf.campaign
    
    UNION ALL
    
    -- Clicks
    SELECT 
        c.user_id,
        c.campaign,
        c.advertiser,
        'click' as event_type,
        c.click_dt as exposure_date,
        0 as event_cost  -- Cost already in impressions
    FROM dsp_clicks c
    INNER JOIN campaign_filter cf ON c.campaign = cf.campaign
    
    UNION ALL
    
    -- Pixel Conversions
    SELECT 
        p.user_id,
        'Pixel Conversions' as campaign,  -- Group all pixel events
        p.advertiser,
        'pixel' as event_type,
        p.traffic_dt as exposure_date,
        0 as event_cost
    FROM amazon_attributed_events_by_traffic_time p
    WHERE p.advertiser IN (
        SELECT DISTINCT advertiser 
        FROM dsp_impressions 
        WHERE campaign IN (SELECT campaign FROM campaign_filter)
    )
),

-- Match touchpoints to purchases within attribution window
attribution_base AS (
    SELECT 
        vp.*,
        dt.campaign,
        dt.advertiser,
        dt.event_type,
        dt.exposure_date,
        dt.event_cost,
        vp.purchase_date - dt.exposure_date as match_age,
        -- CUSTOMIZATION POINT 3: Event type priority (lower number = higher priority)
        CASE 
            WHEN dt.event_type = 'pixel' THEN 1
            WHEN dt.event_type = 'click' THEN 2
            WHEN dt.event_type = 'impression' THEN 3
        END as match_type
    FROM vehicle_purchases vp
    INNER JOIN dsp_touchpoints dt 
        ON vp.user_id = dt.user_id
    WHERE dt.exposure_date <= vp.purchase_date
        -- CUSTOMIZATION POINT 4: Attribution window (default 60 days)
        AND dt.exposure_date >= vp.purchase_date - INTERVAL '60' DAY
        -- CUSTOMIZATION POINT 5: Optional - exclude certain event types
        -- AND dt.event_type IN ('click', 'pixel')
),

-- Apply attribution model
attributed_purchases AS (
    SELECT 
        *,
        -- CUSTOMIZATION POINT 6: Attribution model
        -- First-touch: ORDER BY match_type ASC, match_age DESC (oldest first)
        -- Last-touch: ORDER BY match_type ASC, match_age ASC (newest first)
        ROW_NUMBER() OVER(
            PARTITION BY vehicle_purchase_id 
            ORDER BY match_type ASC, match_age DESC  -- First-touch attribution
        ) as attribution_rank
    FROM attribution_base
),

-- Get attributed purchases only
final_attribution AS (
    SELECT * 
    FROM attributed_purchases 
    WHERE attribution_rank = 1
),

-- Calculate campaign-level metrics
campaign_metrics AS (
    SELECT 
        campaign,
        COUNT(DISTINCT user_id) as unique_reach,
        SUM(impressions) as total_impressions,
        SUM(clicks) as total_clicks,
        SUM(total_cost) as total_spend
    FROM (
        SELECT 
            campaign,
            user_id,
            COUNT(CASE WHEN event_type = 'impression' THEN 1 END) as impressions,
            COUNT(CASE WHEN event_type = 'click' THEN 1 END) as clicks,
            SUM(event_cost) as total_cost
        FROM dsp_touchpoints
        GROUP BY 1, 2
    ) user_metrics
    GROUP BY 1
)

-- Final results with comprehensive metrics
SELECT 
    'First Touch' as attribution_model,  -- Update if using last-touch
    fa.campaign,
    
    -- Volume metrics
    cm.total_impressions as impressions,
    cm.total_clicks as clicks,
    COUNT(DISTINCT CASE WHEN fa.event_type = 'pixel' THEN fa.vehicle_purchase_id END) as pixel_conversions,
    cm.total_spend,
    cm.unique_reach,
    
    -- Attribution metrics
    COUNT(DISTINCT fa.vehicle_purchase_id) as vehicle_purchases_total,
    COUNT(DISTINCT CASE WHEN fa.event_type = 'impression' THEN fa.vehicle_purchase_id END) as impressions_attributed,
    COUNT(DISTINCT CASE WHEN fa.event_type = 'click' THEN fa.vehicle_purchase_id END) as clicks_attributed,
    COUNT(DISTINCT CASE WHEN fa.event_type = 'pixel' THEN fa.vehicle_purchase_id END) as pixels_attributed,
    
    -- Efficiency metrics
    ROUND(100.0 * COUNT(DISTINCT fa.vehicle_purchase_id) / NULLIF(cm.unique_reach, 0), 2) as vehicle_purchase_rate,
    ROUND(cm.total_spend / NULLIF(COUNT(DISTINCT fa.vehicle_purchase_id), 0), 2) as spend_per_vehicle_purchase,
    
    -- Vehicle details
    COUNT(DISTINCT CASE WHEN fa.new_or_used = 'N' THEN fa.vehicle_purchase_id END) as new_vehicles,
    COUNT(DISTINCT CASE WHEN fa.new_or_used = 'U' THEN fa.vehicle_purchase_id END) as used_vehicles,
    
    -- Additional segmentation
    ARRAY_AGG(DISTINCT fa.vehicle_make ORDER BY fa.vehicle_make) as vehicle_makes_purchased,
    ARRAY_AGG(DISTINCT fa.vehicle_type ORDER BY fa.vehicle_type) as vehicle_types_purchased

FROM final_attribution fa
LEFT JOIN campaign_metrics cm ON fa.campaign = cm.campaign
GROUP BY 1, 2, 3, 4, 5, 6, 7
HAVING COUNT(DISTINCT fa.user_id) >= 100  -- Meet AMC aggregation threshold
ORDER BY vehicle_purchases_total DESC""",
            "query_description": "Comprehensive vehicle purchase attribution analysis with customizable attribution models, lookback windows, and event type prioritization. Measures the impact of DSP campaigns on actual vehicle purchases using Experian DMV data.",
            "parameters": [
                {
                    "name": "campaign_names",
                    "description": "List of DSP campaign names to analyze",
                    "type": "array",
                    "required": True
                },
                {
                    "name": "attribution_window_days",
                    "description": "Number of days to look back for attribution (default: 60)",
                    "type": "integer",
                    "default_value": "60"
                },
                {
                    "name": "attribution_model",
                    "description": "Attribution model: 'first_touch' or 'last_touch'",
                    "type": "string",
                    "default_value": "first_touch"
                },
                {
                    "name": "vehicle_make_filter",
                    "description": "Optional: Filter by specific vehicle makes",
                    "type": "array",
                    "required": False
                }
            ],
            "order_index": 2
        }
    ]
    
    # Delete existing queries for this guide
    supabase.table('build_guide_queries').delete().eq('guide_id', guide_db_id).execute()
    
    # Insert queries directly into build_guide_queries
    query_ids = []
    for query in queries:
        guide_query_data = {
            "guide_id": guide_db_id,
            "title": query["query_name"],
            "sql_query": query["query_sql"],
            "description": query["query_description"],
            "query_type": query["query_type"],
            "display_order": query["order_index"],
            "interpretation_notes": "Review the results to understand vehicle purchase attribution patterns and optimize campaign investment."
        }
        
        # Handle parameters if they exist
        if "parameters" in query and query["parameters"]:
            params_schema = {}
            default_params = {}
            for param in query["parameters"]:
                params_schema[param["name"]] = {
                    "type": param["type"],
                    "description": param["description"]
                }
                if "default_value" in param:
                    default_params[param["name"]] = param["default_value"]
                if param.get("required", False):
                    params_schema[param["name"]]["required"] = True
            
            guide_query_data["parameters_schema"] = params_schema
            guide_query_data["default_parameters"] = default_params
        
        result = supabase.table('build_guide_queries').insert(guide_query_data).execute()
        if result.data:
            query_ids.append(result.data[0]['id'])
        else:
            print(f"Failed to create query: {query['query_name']}")
    
    print(f"Created {len(queries)} queries")
    
    # 4. Create example results
    examples = [
        {
            "guide_query_id": query_ids[0] if query_ids else None,
            "example_name": "Available Vehicle Makes and Models",
            "sample_data": {
                "rows": [
                    {"vehicle_make": "Toyota", "vehicle_model": "RAV4", "vehicle_type": "SUV", "vehicle_class": "Standard", "new_or_used": "N", "vehicle_fuel_type": "Gas", "unique_purchasers": 3542, "total_purchases": 3789},
                    {"vehicle_make": "Honda", "vehicle_model": "CR-V", "vehicle_type": "SUV", "vehicle_class": "Standard", "new_or_used": "N", "vehicle_fuel_type": "Gas", "unique_purchasers": 2981, "total_purchases": 3156},
                    {"vehicle_make": "Ford", "vehicle_model": "F-150", "vehicle_type": "Truck", "vehicle_class": "Standard", "new_or_used": "N", "vehicle_fuel_type": "Gas", "unique_purchasers": 2764, "total_purchases": 2899},
                    {"vehicle_make": "Tesla", "vehicle_model": "Model Y", "vehicle_type": "SUV", "vehicle_class": "Luxury", "new_or_used": "N", "vehicle_fuel_type": "Electric", "unique_purchasers": 1876, "total_purchases": 1923},
                    {"vehicle_make": "Toyota", "vehicle_model": "Camry", "vehicle_type": "Sedan", "vehicle_class": "Standard", "new_or_used": "N", "vehicle_fuel_type": "Gas", "unique_purchasers": 1654, "total_purchases": 1798},
                    {"vehicle_make": "Chevrolet", "vehicle_model": "Silverado", "vehicle_type": "Truck", "vehicle_class": "Standard", "new_or_used": "N", "vehicle_fuel_type": "Gas", "unique_purchasers": 1543, "total_purchases": 1612},
                    {"vehicle_make": "Honda", "vehicle_model": "Accord", "vehicle_type": "Sedan", "vehicle_class": "Standard", "new_or_used": "N", "vehicle_fuel_type": "Gas", "unique_purchasers": 1432, "total_purchases": 1521},
                    {"vehicle_make": "Mazda", "vehicle_model": "CX-5", "vehicle_type": "SUV", "vehicle_class": "Standard", "new_or_used": "N", "vehicle_fuel_type": "Gas", "unique_purchasers": 987, "total_purchases": 1034}
                ]
            },
            "interpretation_markdown": """### Key Insights from Available Vehicle Data

**Vehicle Type Distribution:**
- SUVs dominate purchases (45% of total), led by Toyota RAV4 and Honda CR-V
- Trucks represent 28% of purchases, with Ford F-150 leading
- Sedans account for 20%, showing decline from historical norms
- Electric vehicles growing but still <10% of matched purchases

**Brand Performance:**
- Toyota leads with 5,587 total purchases across models
- Honda second with 4,677 purchases
- Domestic brands (Ford, Chevrolet) strong in truck segment
- Tesla showing rapid growth in luxury electric segment

**New vs Used Patterns:**
- New vehicles represent 73% of matched purchases
- Used vehicle data may be underrepresented due to private sales
- Luxury segments show higher new vehicle percentage (85%+)

**Data Quality Considerations:**
- All results meet 100+ unique user threshold
- Total represents ~25-30% of actual sales (identity match rate)
- Use for relative performance, not absolute market sizing""",
            "display_order": 1
        },
        {
            "guide_query_id": query_ids[1] if len(query_ids) > 1 else None,
            "example_name": "Campaign Attribution Performance",
            "sample_data": {
                "rows": [
                    {
                        "attribution_model": "First Touch",
                        "campaign": "Q3'24 - Streaming TV - Awareness",
                        "impressions": 3505163,
                        "clicks": 0,
                        "pixel_conversions": 11607,
                        "total_spend": 53823.12,
                        "unique_reach": 354693,
                        "vehicle_purchases_total": 556,
                        "impressions_attributed": 496,
                        "clicks_attributed": 0,
                        "pixels_attributed": 60,
                        "vehicle_purchase_rate": 0.16,
                        "spend_per_vehicle_purchase": 96.84,
                        "new_vehicles": 412,
                        "used_vehicles": 144
                    },
                    {
                        "attribution_model": "First Touch",
                        "campaign": "Q3'24 - Video Ads - Consideration",
                        "impressions": 1554215,
                        "clicks": 1737,
                        "pixel_conversions": 30413,
                        "total_spend": 29431.42,
                        "unique_reach": 293189,
                        "vehicle_purchases_total": 204,
                        "impressions_attributed": 89,
                        "clicks_attributed": 43,
                        "pixels_attributed": 72,
                        "vehicle_purchase_rate": 0.07,
                        "spend_per_vehicle_purchase": 144.27,
                        "new_vehicles": 165,
                        "used_vehicles": 39
                    },
                    {
                        "attribution_model": "First Touch",
                        "campaign": "Q3'24 - Display - Retargeting",
                        "impressions": 5138437,
                        "clicks": 3045,
                        "pixel_conversions": 15491,
                        "total_spend": 92929.26,
                        "unique_reach": 969336,
                        "vehicle_purchases_total": 58,
                        "impressions_attributed": 12,
                        "clicks_attributed": 8,
                        "pixels_attributed": 38,
                        "vehicle_purchase_rate": 0.01,
                        "spend_per_vehicle_purchase": 1602.23,
                        "new_vehicles": 51,
                        "used_vehicles": 7
                    }
                ]
            },
            "interpretation_markdown": """### Campaign Attribution Analysis Results

**Overall Performance Summary:**
- **Total Attributed Purchases**: 818 vehicles across all campaigns
- **Blended Cost per Purchase**: $220.70
- **Average Purchase Rate**: 0.08% of unique reach
- **Attribution Mix**: 73% impressions, 6% clicks, 21% pixels

**Channel Effectiveness Rankings:**

1. **Streaming TV - Highest Efficiency**
   - Best cost per purchase: $96.84 (56% below average)
   - Highest purchase rate: 0.16% (2x average)
   - Strong impression-based attribution (89%)
   - Ideal for upper-funnel awareness and reach

2. **Video Ads - Balanced Performance**
   - Moderate cost per purchase: $144.27
   - Balanced attribution across all event types
   - Higher pixel attribution (35%) shows consideration behavior
   - Effective for mid-funnel engagement

3. **Display Retargeting - Lower Funnel Focus**
   - Highest cost per purchase: $1,602.23
   - Lowest purchase rate: 0.01%
   - Pixel-dominant attribution (66%)
   - Best suited for closing near-purchase consumers

**Strategic Recommendations:**

📈 **Budget Reallocation**
- Increase Streaming TV investment by 40% (high efficiency)
- Maintain Video at current levels (solid performance)
- Reduce Display by 50% and reallocate to upper funnel

🎯 **Targeting Optimization**
- Streaming TV: Expand reach to similar audiences
- Video: Focus on high-intent signals and behaviors
- Display: Narrow to cart abandoners and configurator users

📊 **Attribution Insights**
- 73% of purchases attributed to awareness campaigns (first-touch)
- Impression-based attribution validates brand building importance
- Consider testing last-touch model for different perspective""",
            "display_order": 2
        }
    ]
    
    # Delete existing examples for the queries
    if query_ids:
        for query_id in query_ids:
            supabase.table('build_guide_examples').delete().eq('guide_query_id', query_id).execute()
    
    # Insert examples only if queries were created
    if query_ids:
        for i, example in enumerate(examples):
            if example.get('guide_query_id') is not None:
                # Insert the example
                supabase.table('build_guide_examples').insert(example).execute()
    
    print(f"Created {len(examples)} examples")
    
    # 5. Create metrics
    metrics = [
        {
            "guide_id": guide_db_id,
            "metric_name": "vehicle_purchases_total",
            "display_name": "Vehicle Purchases Total",
            "definition": "Total number of vehicle purchases attributed to the campaign within the attribution window",
            "metric_type": "metric",
            "display_order": 1
        },
        {
            "guide_id": guide_db_id,
            "metric_name": "spend_per_vehicle_purchase",
            "display_name": "Spend per Vehicle Purchase",
            "definition": "Total media spend divided by attributed vehicle purchases",
            "metric_type": "metric",
            "display_order": 2
        },
        {
            "guide_id": guide_db_id,
            "metric_name": "vehicle_purchase_rate",
            "display_name": "Vehicle Purchase Rate",
            "definition": "Percentage of unique users reached who purchased a vehicle",
            "metric_type": "metric",
            "display_order": 3
        },
        {
            "guide_id": guide_db_id,
            "metric_name": "attribution_model",
            "display_name": "Attribution Model",
            "definition": "Attribution model used: First-touch or Last-touch",
            "metric_type": "dimension",
            "display_order": 4
        },
        {
            "guide_id": guide_db_id,
            "metric_name": "vehicle_make",
            "display_name": "Vehicle Make",
            "definition": "Manufacturer/brand of the purchased vehicle",
            "metric_type": "dimension",
            "display_order": 5
        },
        {
            "guide_id": guide_db_id,
            "metric_name": "new_or_used",
            "display_name": "New or Used",
            "definition": "Whether the purchased vehicle was new (N) or used (U)",
            "metric_type": "dimension",
            "display_order": 6
        }
    ]
    
    # Delete existing metrics
    supabase.table('build_guide_metrics').delete().eq('guide_id', guide_db_id).execute()
    
    # Insert metrics
    for metric in metrics:
        supabase.table('build_guide_metrics').insert(metric).execute()
    
    print(f"Created {len(metrics)} metrics")
    
    print(f"\n✅ Successfully created Experian Vehicle Purchase Attribution build guide!")
    print(f"Guide ID: {guide_id}")
    print(f"Sections: {len(sections)}")
    print(f"Queries: {len(queries)}")
    print(f"Examples: {len(examples)}")
    print(f"Metrics: {len(metrics)}")

if __name__ == "__main__":
    create_experian_vehicle_guide()