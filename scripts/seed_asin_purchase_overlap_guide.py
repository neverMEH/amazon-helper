#!/usr/bin/env python3
"""
Seed script for ASIN Purchase Overlap for Upselling Build Guide
This script creates a comprehensive guide for identifying products frequently purchased together
to create targeted upselling and cross-selling campaigns
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

def create_asin_overlap_guide():
    """Create the ASIN Purchase Overlap for Upselling guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_asin_purchase_overlap_upselling',
            'name': 'ASIN Purchase Overlap for Upselling',
            'category': 'ASIN Analysis',
            'short_description': 'Identify products frequently purchased together to create targeted upselling and cross-selling campaigns',
            'tags': ['asin-analysis', 'upselling', 'cross-sell', 'purchase-patterns', 'customer-insights'],
            'icon': 'ShoppingCart',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 30,
            'prerequisites': [
                'AMC Instance with conversion data',
                'On-Amazon conversions tracked',
                'Multiple ASINs in campaigns'
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
                'content_markdown': """## Purpose

This instructional query helps you identify products (ASINs) that customers frequently purchase together. By understanding these purchase patterns, you can:

- **Create targeted remarketing campaigns** for customers who purchased one product but not the other
- **Identify upselling opportunities** based on actual purchase behavior
- **Develop bundle strategies** for products with high purchase overlap
- **Optimize product recommendations** on detail pages

### Key Business Applications

1. **Remarketing Strategy**: Target customers who bought Product A with ads for frequently co-purchased Product B
2. **Bundle Creation**: Package products with high overlap for increased average order value
3. **Inventory Planning**: Stock related products together based on purchase patterns
4. **Email Marketing**: Personalize follow-up emails with relevant product suggestions

## Requirements

### Required:
- AMC instance with conversion data
- On-Amazon conversions (this analysis is limited to Amazon purchases)
- Multiple ASINs tracked in campaigns

### Recommended:
- At least 30 days of conversion data for meaningful patterns
- Minimum of 100 purchases per ASIN for statistical significance
- Campaign attribution properly configured

> **Note**: This query uses ASIN-level conversion data and is therefore limited to advertisers with on-Amazon conversions.""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'data_sources',
                'title': 'Data Sources Overview',
                'content_markdown': """## Primary Table Used

### amazon_attributed_events_by_conversion_time

This table contains conversion events organized by when the conversion occurred, allowing us to identify purchase patterns.

**Key Fields:**
- `tracked_asin`: The ASIN that was purchased
- `user_id`: Unique identifier for the customer
- `purchases`: Number of purchase events
- `campaign_id_string`: Campaign identifier for filtering
- `ad_product_type`: Type of advertising (DSP, Sponsored Products, etc.)

**Why This Table?**
We use the conversion time table because we're interested in when customers actually made purchases, not when they were exposed to ads. This gives us the clearest picture of purchase behavior patterns.

### Alternative: amazon_attributed_events_by_traffic_time

You could also use the traffic time table if you want to analyze based on when customers were exposed to ads rather than when they converted. This might be useful for understanding the influence of ad exposure on subsequent purchase patterns.

## How the Analysis Works

### Step 1: Identify Lead ASINs
The query first identifies all ASINs that have been purchased (lead ASINs) and counts:
- Distinct users who purchased each ASIN
- Total purchases for each ASIN

### Step 2: Create Purchase Lists
For each ASIN, we create a list of all users who purchased it, filtered by any campaign restrictions you specify.

### Step 3: Calculate Overlaps
Using an INNER JOIN on user_id, we identify users who purchased both:
- The lead ASIN
- Any other ASIN (overlap ASIN)

### Step 4: Compute Overlap Metrics
For each ASIN pair, we calculate:
- Number of users who bought both
- Percentage overlap (users who bought both / users who bought lead ASIN)

## Data Flow Diagram

```
1. All Conversions
       ↓
2. Filter by Campaigns (optional)
       ↓
3. Group by ASIN + User
       ↓
4. Self-Join on User ID
       ↓
5. Calculate Overlap %
       ↓
6. Output ASIN Pairs
```""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'implementation',
                'title': 'Implementation Steps',
                'content_markdown': """## Step-by-Step Implementation

### Step 1: Run the Exploratory Query

First, identify available campaigns and ASINs in your data:

```sql
SELECT
  campaign,
  campaign_id_string,
  ad_product_type,
  tracked_asin,
  COUNT(DISTINCT user_id) as unique_purchasers,
  SUM(purchases) as total_purchases
FROM
  amazon_attributed_events_by_conversion_time
WHERE
  purchases > 0
GROUP BY
  1, 2, 3, 4
ORDER BY
  total_purchases DESC
```

### Step 2: Configure Query Parameters

Based on your exploratory results, set up parameters:

#### Campaign Filtering (Optional)
If you want to focus on specific campaigns:
```sql
campaign_id:
  dataType:
    type: ARRAY
    elementDataType: STRING
  value:
    - "campaign_id_1"
    - "campaign_id_2"
```

Leave empty to analyze all campaigns.

#### Ad Product Type Filtering (Optional)
To focus on specific ad types:
```sql
ad_product_type:
  dataType:
    type: ARRAY
    elementDataType: STRING
  value:
    - sponsored_products
    - sponsored_brands
    - DSP
```

### Step 3: Customize the Main Query

#### Set Minimum Thresholds
Adjust the minimum user count to filter out noise:
```sql
-- Default: at least 2 users must have bought both
WHERE dist_lead_and_overlap_asin_purchased_user_count > 1

-- For larger datasets, increase threshold
WHERE dist_lead_and_overlap_asin_purchased_user_count > 10
```

#### Add URL Generation (Optional)
Uncomment and adjust domain for your marketplace:
```sql
-- For US:
,concat('https://amazon.com/dp/', ai.lead_asin) as url_to_lead_asin

-- For UK:
,concat('https://amazon.co.uk/dp/', ai.lead_asin) as url_to_lead_asin

-- For Germany:
,concat('https://amazon.de/dp/', ai.lead_asin) as url_to_lead_asin
```

### Step 4: Run and Export Results

1. Execute the query with your configured parameters
2. Export results to CSV for analysis
3. Sort by user_overlap descending to find strongest relationships

## Optimization Tips

### For Large Datasets
If query is slow, add date filters:
```sql
WHERE conversion_event_dt >= CURRENT_DATE - INTERVAL '30' DAY
```

### For Category Analysis
Add category filtering if you only want within-category overlaps:
```sql
-- Add to WITH clause
,product_categories AS (
  SELECT DISTINCT
    asin,
    category
  FROM your_product_catalog
)
-- Join in main query to filter same-category only
```

### For Seasonal Analysis
Add time-based segmentation:
```sql
-- Group by month to see seasonal patterns
,DATE_TRUNC('month', conversion_event_dt) as purchase_month
```""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'query_templates',
                'title': 'Query Templates',
                'content_markdown': """## Exploratory Query

Use this to understand your data before running the main analysis:

```sql
-- Exploratory Query to identify campaigns and ASINs
SELECT
  campaign,
  CONCAT('campaign_id: ', campaign_id_string) AS campaign_id,
  CASE
    WHEN ad_product_type IS NULL THEN 'DSP'
    ELSE ad_product_type
  END AS ad_product_type,
  tracked_asin,
  COUNT(DISTINCT user_id) AS unique_purchasers,
  SUM(purchases) AS total_purchases
FROM
  amazon_attributed_events_by_conversion_time
WHERE
  purchases > 0
  AND tracked_asin IS NOT NULL
GROUP BY
  1, 2, 3, 4
HAVING
  COUNT(DISTINCT user_id) >= 10  -- Minimum threshold for meaningful analysis
ORDER BY
  total_purchases DESC
LIMIT 100
```

## Main Query: ASIN Purchase Overlap Analysis

```sql
/* ASIN Purchase Overlap for Upselling
   Identifies products frequently purchased together */

-- Get lead ASIN information
WITH asin_info AS (
  SELECT
    tracked_asin AS lead_asin,
    COUNT(DISTINCT user_id) AS asin_info_dist_user_count,
    SUM(purchases) AS asin_info_purchases_sum
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    purchases > 0
    AND user_id IS NOT NULL
  GROUP BY
    1
),

-- Get list of purchased ASINs and purchasing users
tracked_asin_list AS (
  SELECT
    DISTINCT tracked_asin,
    user_id
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    purchases > 0
    AND user_id IS NOT NULL
    -- Optional campaign filtering
    AND (
      CUSTOM_PARAMETER('campaign_id') IS NULL
      OR CARDINALITY(CUSTOM_PARAMETER('campaign_id')) = 0
      OR ARRAY_CONTAINS(
        CUSTOM_PARAMETER('campaign_id'),
        campaign_id_string
      )
    )
),

-- Determine overlap between purchase audiences
determine_overlap AS (
  SELECT
    ta.tracked_asin AS lead_asin,
    tb.tracked_asin AS overlap_asin,
    COUNT(DISTINCT ta.user_id) AS dist_lead_and_overlap_asin_purchased_user_count
  FROM
    tracked_asin_list ta
    INNER JOIN tracked_asin_list tb 
      ON ta.user_id = tb.user_id
  WHERE
    ta.tracked_asin <> tb.tracked_asin
  GROUP BY
    1, 2
)

-- Final output with overlap calculations
SELECT
  ai.lead_asin,
  ai.asin_info_purchases_sum AS lead_asin_purchases,
  ai.asin_info_dist_user_count AS dist_lead_asin_purchased_user_count,
  do.overlap_asin,
  do.dist_lead_and_overlap_asin_purchased_user_count,
  ROUND(
    do.dist_lead_and_overlap_asin_purchased_user_count::DECIMAL / 
    ai.asin_info_dist_user_count,
    2
  ) AS user_overlap,
  -- Optional: Generate URLs (adjust domain for your marketplace)
  CONCAT('https://amazon.com/dp/', ai.lead_asin) AS url_to_lead_asin,
  CONCAT('https://amazon.com/dp/', do.overlap_asin) AS url_to_overlap_asin
FROM
  asin_info ai
  LEFT JOIN determine_overlap do 
    ON ai.lead_asin = do.lead_asin
WHERE
  ai.lead_asin <> do.overlap_asin
  AND do.dist_lead_and_overlap_asin_purchased_user_count > 1
ORDER BY
  user_overlap DESC,
  lead_asin_purchases DESC
```

## Advanced Query: Directional Overlap Analysis

This variation shows directional relationships (A→B vs B→A):

```sql
-- Shows which product is more likely to lead to the other
WITH purchase_sequences AS (
  SELECT
    user_id,
    tracked_asin,
    MIN(conversion_event_dt) as first_purchase_date
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    purchases > 0
  GROUP BY
    1, 2
),
sequential_purchases AS (
  SELECT
    p1.tracked_asin as first_asin,
    p2.tracked_asin as second_asin,
    COUNT(DISTINCT p1.user_id) as sequence_count
  FROM
    purchase_sequences p1
    JOIN purchase_sequences p2
      ON p1.user_id = p2.user_id
      AND p1.tracked_asin <> p2.tracked_asin
      AND p1.first_purchase_date <= p2.first_purchase_date
  GROUP BY
    1, 2
)
SELECT
  first_asin,
  second_asin,
  sequence_count,
  RANK() OVER (PARTITION BY first_asin ORDER BY sequence_count DESC) as rank_for_first
FROM
  sequential_purchases
WHERE
  sequence_count >= 5
ORDER BY
  first_asin,
  sequence_count DESC
```""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'metrics',
                'title': 'Metrics Definitions',
                'content_markdown': """## Core Metrics

### Base Metrics

| Metric | Description | Business Use |
|--------|-------------|--------------|
| **lead_asin** | The primary ASIN being analyzed | Identify your hero products |
| **lead_asin_purchases** | Total purchases of the lead ASIN | Measure product popularity |
| **dist_lead_asin_purchased_user_count** | Unique users who bought lead ASIN | Understand customer reach |

### Overlap Metrics

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| **overlap_asin** | The ASIN checked for co-purchase | Potential upsell target |
| **dist_lead_and_overlap_asin_purchased_user_count** | Users who bought both ASINs | Size of overlap opportunity |
| **user_overlap** | Percentage of lead buyers who also bought overlap | Strength of relationship |

### Calculated Metrics

#### User Overlap Percentage
```
user_overlap = (Users who bought both) / (Users who bought lead ASIN)
```

**Interpretation:**
- **>50%**: Very strong relationship, excellent upsell candidate
- **30-50%**: Strong relationship, good bundle opportunity
- **10-30%**: Moderate relationship, worth testing
- **<10%**: Weak relationship, may not be worth targeting

#### Purchase Affinity Score (Optional)
```
affinity = (Overlap %) × (Volume of overlap purchases)
```
Combines relationship strength with opportunity size.

## URL Fields (Optional)

| Field | Purpose | Customization |
|-------|---------|---------------|
| **url_to_lead_asin** | Direct link to lead product | Adjust domain per marketplace |
| **url_to_overlap_asin** | Direct link to overlap product | Format: https://amazon.[domain]/dp/[ASIN] |

## Key Performance Indicators

### For Upselling Success
1. **High Overlap % + High Volume**: Priority targets for remarketing
2. **High Overlap % + Low Volume**: Test opportunities
3. **Low Overlap % + High Volume**: Broad appeal products

### For Bundle Strategy
Look for:
- Bidirectional high overlap (A→B and B→A both strong)
- Similar price points
- Complementary categories

### For Campaign Optimization
Monitor:
- Overlap changes over time
- Seasonal patterns in co-purchases
- Campaign influence on overlap rates""",
                'display_order': 5,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'interpretation',
                'title': 'Interpreting Results',
                'content_markdown': """## Understanding Your Results

### Sample Output Analysis

| lead_asin | lead_purchases | lead_users | overlap_asin | overlap_users | user_overlap |
|-----------|---------------|------------|--------------|---------------|--------------|
| ASIN000001 | 2,360 | 2,100 | ASIN000100 | 1,240 | 0.59 |
| ASIN000002 | 7 | 7 | ASIN000101 | 3 | 0.43 |
| ASIN000003 | 440 | 300 | ASIN000102 | 100 | 0.33 |

### Key Insights from This Example

#### Row 1: Strong Upsell Opportunity
- **59% overlap** indicates majority of ASIN000001 buyers also buy ASIN000100
- **High volume** (1,240 users) makes this economically viable
- **Action**: Create remarketing campaign targeting ASIN000001 buyers who haven't purchased ASIN000100

#### Row 2: Statistical Noise
- **43% overlap** looks strong but only 7 total users
- **Too small sample** for reliable conclusions
- **Action**: Wait for more data before making decisions

#### Row 3: Moderate Opportunity
- **33% overlap** with decent volume (100 users)
- **Worth testing** but not priority
- **Action**: Include in broader remarketing efforts

## Strategic Applications

### 1. Remarketing Campaign Development

**High Overlap Products (>40%)**
- Create dedicated remarketing campaigns
- Use "Customers who bought X also bought Y" messaging
- Set higher bids for these high-intent audiences

**Example Campaign Structure:**
```
Campaign: Upsell_ASIN000001_Buyers
Target: Purchased ASIN000001, Not purchased ASIN000100
Message: "Complete your set with our bestselling companion product"
Budget: Proportional to overlap percentage
```

### 2. Bundle Strategy

**Identifying Bundle Candidates:**
Look for ASINs where:
- Both A→B and B→A overlap >30%
- Combined purchase rate is high
- Products are complementary (not substitutes)

**Bundle Pricing Strategy:**
```
Bundle Discount = (1 - User Overlap) × 10%
```
Higher overlap = lower discount needed

### 3. Inventory Management

**Stock Planning:**
- High overlap pairs should be stocked together
- Plan inventory based on overlap ratios
- Consider fulfillment center placement

### 4. Product Page Optimization

**"Frequently Bought Together" Section:**
- Rank products by overlap percentage
- Show top 3-5 overlap products
- A/B test placement and messaging

## Common Patterns and What They Mean

### Pattern 1: Accessories and Main Products
**Example**: Camera (lead) → Memory Card (overlap: 75%)
- **Interpretation**: Natural accessory relationship
- **Action**: Bundle at point of purchase

### Pattern 2: Consumables Replenishment
**Example**: Printer (lead) → Ink Cartridges (overlap: 60%)
- **Interpretation**: Repeat purchase pattern
- **Action**: Set up subscription offerings

### Pattern 3: Category Exploration
**Example**: Book A (lead) → Book B same author (overlap: 35%)
- **Interpretation**: Brand/author loyalty
- **Action**: Author-focused marketing

### Pattern 4: Upgrade Path
**Example**: Basic Model (lead) → Premium Model (overlap: 15%)
- **Interpretation**: Customer upgrade journey
- **Action**: Time-based upgrade campaigns

## Action Planning Template

Based on your overlap analysis, prioritize actions:

### Immediate Actions (Overlap >50%)
1. Launch remarketing campaigns this week
2. Update product page recommendations
3. Create bundle offerings

### Short-term Tests (Overlap 30-50%)
1. A/B test email recommendations
2. Trial limited-time bundles
3. Adjust inventory co-location

### Long-term Strategy (Overlap 10-30%)
1. Monitor for pattern changes
2. Include in seasonal campaigns
3. Consider for future product development

## Avoiding Common Pitfalls

### 1. Sample Size Issues
- Always check absolute numbers, not just percentages
- Require minimum 50-100 users for decisions
- Rerun analysis monthly for fresh data

### 2. Correlation vs Causation
- High overlap doesn't mean one causes the other
- Consider external factors (seasonality, promotions)
- Test before scaling

### 3. Bidirectional Analysis
- Check both A→B and B→A relationships
- Asymmetric overlaps reveal purchase sequences
- Use for journey mapping""",
                'display_order': 6,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'best_practices',
                'title': 'Best Practices and Optimization',
                'content_markdown': """## Best Practices

### Data Quality Checks

#### 1. Verify Data Completeness
```sql
-- Check for data gaps
SELECT
  DATE_TRUNC('day', conversion_event_dt) as date,
  COUNT(DISTINCT user_id) as users,
  COUNT(DISTINCT tracked_asin) as asins
FROM
  amazon_attributed_events_by_conversion_time
WHERE
  purchases > 0
GROUP BY 1
ORDER BY 1 DESC
```

#### 2. Validate ASIN Coverage
Ensure your major ASINs have sufficient data:
- Minimum 100 purchases per ASIN
- At least 30 days of history
- Consistent tracking across campaigns

#### 3. Check for Anomalies
Look for unusual patterns that might indicate issues:
- Sudden spikes in overlap percentages
- Missing ASINs that should be present
- Duplicate entries

### Query Optimization

#### For Performance
1. **Add date filters** to reduce data volume:
```sql
WHERE conversion_event_dt >= CURRENT_DATE - INTERVAL '90' DAY
```

2. **Pre-filter ASINs** if you have many products:
```sql
AND tracked_asin IN (
  SELECT tracked_asin
  FROM top_asins_by_revenue
  LIMIT 100
)
```

3. **Use sampling** for initial exploration:
```sql
TABLESAMPLE (10 PERCENT)
```

#### For Accuracy
1. **Set appropriate thresholds**:
- Minimum user count: 10-50 depending on scale
- Minimum overlap percentage: 5-10%
- Statistical significance testing

2. **Account for seasonality**:
```sql
-- Add seasonal adjustment
,EXTRACT(MONTH FROM conversion_event_dt) as purchase_month
```

3. **Control for promotions**:
Exclude or flag promotional periods that might skew relationships

### Advanced Techniques

#### 1. Time-Lagged Analysis
Understand purchase sequences:
```sql
-- How long between purchases?
WITH time_between AS (
  SELECT
    user_id,
    tracked_asin,
    LAG(conversion_event_dt) OVER (
      PARTITION BY user_id 
      ORDER BY conversion_event_dt
    ) as previous_purchase
  FROM conversions
)
SELECT
  tracked_asin,
  AVG(conversion_event_dt - previous_purchase) as avg_days_between
FROM time_between
WHERE previous_purchase IS NOT NULL
GROUP BY 1
```

#### 2. Cohort-Based Analysis
Track overlap patterns by customer cohort:
```sql
-- First purchase cohorts
WITH first_purchase AS (
  SELECT
    user_id,
    MIN(conversion_event_dt) as cohort_date,
    DATE_TRUNC('month', MIN(conversion_event_dt)) as cohort_month
  FROM conversions
  GROUP BY 1
)
```

#### 3. Category-Level Patterns
Identify category relationships:
```sql
-- Requires product catalog join
WITH category_overlap AS (
  SELECT
    pc1.category as lead_category,
    pc2.category as overlap_category,
    COUNT(DISTINCT user_id) as cross_category_users
  FROM overlap_results o
  JOIN product_catalog pc1 ON o.lead_asin = pc1.asin
  JOIN product_catalog pc2 ON o.overlap_asin = pc2.asin
  GROUP BY 1, 2
)
```

## Implementation Checklist

### Pre-Launch
- [ ] Run exploratory query to understand data
- [ ] Identify top 20-50 ASINs to focus on
- [ ] Set minimum threshold values
- [ ] Verify campaign attribution is working

### Analysis Phase
- [ ] Run main overlap query
- [ ] Export results to spreadsheet
- [ ] Calculate additional metrics (affinity scores)
- [ ] Identify top 10 upsell opportunities

### Action Phase
- [ ] Create remarketing audiences
- [ ] Design bundle offerings
- [ ] Brief creative team on relationships found
- [ ] Set up tracking for results

### Monitoring
- [ ] Schedule weekly/monthly query runs
- [ ] Track changes in overlap percentages
- [ ] Measure campaign performance
- [ ] Adjust strategies based on results

## Troubleshooting

### Issue: Very Low or No Overlaps
**Causes:**
- Insufficient data volume
- Products are substitutes, not complements
- Attribution window too narrow

**Solutions:**
1. Extend analysis period
2. Lower minimum thresholds
3. Check data quality

### Issue: Too Many Results
**Causes:**
- Threshold too low
- Including low-volume ASINs

**Solutions:**
1. Increase minimum user count
2. Filter to top ASINs only
3. Add overlap percentage minimum

### Issue: Unexpected Relationships
**Causes:**
- Promotional effects
- Seasonal patterns
- Data quality issues

**Solutions:**
1. Segment by time period
2. Exclude promotional periods
3. Validate with business knowledge

## Success Metrics

Track these KPIs to measure strategy effectiveness:

### Campaign Performance
- CTR on upsell campaigns
- Conversion rate for recommended products
- Revenue from cross-sells

### Business Impact
- Average order value increase
- Customer lifetime value improvement
- Inventory turnover optimization

### Efficiency Gains
- Reduced marketing waste
- Improved ROAS
- Higher customer satisfaction""",
                'display_order': 7,
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
                'title': 'Exploratory Query for Campaign and ASIN Data',
                'description': 'Explore available campaigns and ASINs to understand your data before running the main overlap analysis',
                'sql_query': """-- Exploratory Query to identify campaigns and ASINs
SELECT
  campaign,
  CONCAT('campaign_id: ', campaign_id_string) AS campaign_id,
  CASE
    WHEN ad_product_type IS NULL THEN 'DSP'
    ELSE ad_product_type
  END AS ad_product_type,
  tracked_asin,
  COUNT(DISTINCT user_id) AS unique_purchasers,
  SUM(purchases) AS total_purchases
FROM
  amazon_attributed_events_by_conversion_time
WHERE
  purchases > 0
  AND tracked_asin IS NOT NULL
  AND conversion_event_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
GROUP BY
  1, 2, 3, 4
HAVING
  COUNT(DISTINCT user_id) >= {{min_users}}  -- Minimum threshold for meaningful analysis
ORDER BY
  total_purchases DESC
LIMIT 100""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for conversion data'
                    },
                    'min_users': {
                        'type': 'integer',
                        'default': 10,
                        'description': 'Minimum unique purchasers required'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'min_users': 10
                },
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'Use this query to identify which campaigns and ASINs have sufficient data for overlap analysis. Focus on ASINs with at least 100 unique purchasers for best results.'
            },
            {
                'guide_id': guide_id,
                'title': 'ASIN Purchase Overlap Analysis',
                'description': 'Main query to identify products frequently purchased together for upselling opportunities',
                'sql_query': """/* ASIN Purchase Overlap for Upselling
   Identifies products frequently purchased together */

-- Get lead ASIN information
WITH asin_info AS (
  SELECT
    tracked_asin AS lead_asin,
    COUNT(DISTINCT user_id) AS asin_info_dist_user_count,
    SUM(purchases) AS asin_info_purchases_sum
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    purchases > 0
    AND user_id IS NOT NULL
    AND conversion_event_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
  GROUP BY
    1
),

-- Get list of purchased ASINs and purchasing users
tracked_asin_list AS (
  SELECT
    DISTINCT tracked_asin,
    user_id
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    purchases > 0
    AND user_id IS NOT NULL
    AND conversion_event_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
    -- Optional campaign filtering
    {{#if campaign_ids}}
    AND campaign_id_string IN ({{campaign_ids}})
    {{/if}}
    -- Optional ad product type filtering
    {{#if ad_product_types}}
    AND ad_product_type IN ({{ad_product_types}})
    {{/if}}
),

-- Determine overlap between purchase audiences
determine_overlap AS (
  SELECT
    ta.tracked_asin AS lead_asin,
    tb.tracked_asin AS overlap_asin,
    COUNT(DISTINCT ta.user_id) AS dist_lead_and_overlap_asin_purchased_user_count
  FROM
    tracked_asin_list ta
    INNER JOIN tracked_asin_list tb 
      ON ta.user_id = tb.user_id
  WHERE
    ta.tracked_asin <> tb.tracked_asin
  GROUP BY
    1, 2
)

-- Final output with overlap calculations
SELECT
  ai.lead_asin,
  ai.asin_info_purchases_sum AS lead_asin_purchases,
  ai.asin_info_dist_user_count AS dist_lead_asin_purchased_user_count,
  do.overlap_asin,
  do.dist_lead_and_overlap_asin_purchased_user_count,
  ROUND(
    do.dist_lead_and_overlap_asin_purchased_user_count::DECIMAL / 
    ai.asin_info_dist_user_count,
    2
  ) AS user_overlap,
  -- Generate URLs for marketplace
  CONCAT('https://{{marketplace_domain}}/dp/', ai.lead_asin) AS url_to_lead_asin,
  CONCAT('https://{{marketplace_domain}}/dp/', do.overlap_asin) AS url_to_overlap_asin
FROM
  asin_info ai
  LEFT JOIN determine_overlap do 
    ON ai.lead_asin = do.lead_asin
WHERE
  ai.lead_asin <> do.overlap_asin
  AND do.dist_lead_and_overlap_asin_purchased_user_count > {{min_overlap_users}}
ORDER BY
  user_overlap DESC,
  lead_asin_purchases DESC
LIMIT {{result_limit}}""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for conversion data'
                    },
                    'min_overlap_users': {
                        'type': 'integer',
                        'default': 1,
                        'description': 'Minimum users who must have bought both products'
                    },
                    'marketplace_domain': {
                        'type': 'string',
                        'default': 'amazon.com',
                        'description': 'Amazon marketplace domain (amazon.com, amazon.co.uk, amazon.de, etc.)'
                    },
                    'result_limit': {
                        'type': 'integer',
                        'default': 500,
                        'description': 'Maximum number of results to return'
                    },
                    'campaign_ids': {
                        'type': 'array',
                        'default': None,
                        'description': 'Optional: Specific campaign IDs to filter by'
                    },
                    'ad_product_types': {
                        'type': 'array',
                        'default': None,
                        'description': 'Optional: Ad product types to include (sponsored_products, sponsored_brands, DSP)'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30,
                    'min_overlap_users': 1,
                    'marketplace_domain': 'amazon.com',
                    'result_limit': 500
                },
                'display_order': 2,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Focus on pairs with high user_overlap percentages (>30%) and significant volume. These represent the best upselling opportunities.'
            },
            {
                'guide_id': guide_id,
                'title': 'Directional Purchase Sequence Analysis',
                'description': 'Advanced query to understand the order in which products are purchased',
                'sql_query': """-- Directional Purchase Sequence Analysis
-- Shows which product is more likely to lead to the purchase of another

WITH purchase_sequences AS (
  SELECT
    user_id,
    tracked_asin,
    MIN(conversion_event_dt) as first_purchase_date
  FROM
    amazon_attributed_events_by_conversion_time
  WHERE
    purchases > 0
    AND conversion_event_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
  GROUP BY
    1, 2
),

sequential_purchases AS (
  SELECT
    p1.tracked_asin as first_asin,
    p2.tracked_asin as second_asin,
    COUNT(DISTINCT p1.user_id) as sequence_count,
    AVG(DATE_DIFF('day', p1.first_purchase_date, p2.first_purchase_date)) as avg_days_between
  FROM
    purchase_sequences p1
    JOIN purchase_sequences p2
      ON p1.user_id = p2.user_id
      AND p1.tracked_asin <> p2.tracked_asin
      AND p1.first_purchase_date <= p2.first_purchase_date
  GROUP BY
    1, 2
),

ranked_sequences AS (
  SELECT
    first_asin,
    second_asin,
    sequence_count,
    avg_days_between,
    RANK() OVER (PARTITION BY first_asin ORDER BY sequence_count DESC) as rank_for_first,
    RANK() OVER (PARTITION BY second_asin ORDER BY sequence_count DESC) as rank_for_second
  FROM
    sequential_purchases
  WHERE
    sequence_count >= {{min_sequence_count}}
)

SELECT
  first_asin,
  second_asin,
  sequence_count,
  ROUND(avg_days_between, 1) as avg_days_between_purchases,
  rank_for_first,
  rank_for_second,
  CONCAT('https://{{marketplace_domain}}/dp/', first_asin) AS url_to_first_asin,
  CONCAT('https://{{marketplace_domain}}/dp/', second_asin) AS url_to_second_asin
FROM
  ranked_sequences
WHERE
  rank_for_first <= {{top_n_sequences}}
ORDER BY
  first_asin,
  sequence_count DESC""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 90,
                        'description': 'Number of days to look back for purchase sequences'
                    },
                    'min_sequence_count': {
                        'type': 'integer',
                        'default': 5,
                        'description': 'Minimum number of sequential purchases required'
                    },
                    'top_n_sequences': {
                        'type': 'integer',
                        'default': 10,
                        'description': 'Show top N sequence relationships per product'
                    },
                    'marketplace_domain': {
                        'type': 'string',
                        'default': 'amazon.com',
                        'description': 'Amazon marketplace domain'
                    }
                },
                'default_parameters': {
                    'lookback_days': 90,
                    'min_sequence_count': 5,
                    'top_n_sequences': 10,
                    'marketplace_domain': 'amazon.com'
                },
                'display_order': 3,
                'query_type': 'advanced',
                'interpretation_notes': 'This analysis reveals purchase order patterns. Products frequently purchased first can be used as entry points for customer acquisition, while products purchased later are ideal for upselling campaigns.'
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add example results for the main analysis query
                if query['query_type'] == 'main_analysis':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'High-Value Upselling Opportunities',
                        'sample_data': {
                            'rows': [
                                {
                                    'lead_asin': 'B08N5WRWNW',
                                    'lead_asin_purchases': 2360,
                                    'dist_lead_asin_purchased_user_count': 2100,
                                    'overlap_asin': 'B08N5LNQCX',
                                    'dist_lead_and_overlap_asin_purchased_user_count': 1240,
                                    'user_overlap': 0.59,
                                    'url_to_lead_asin': 'https://amazon.com/dp/B08N5WRWNW',
                                    'url_to_overlap_asin': 'https://amazon.com/dp/B08N5LNQCX'
                                },
                                {
                                    'lead_asin': 'B08N5WRWNW',
                                    'lead_asin_purchases': 2360,
                                    'dist_lead_asin_purchased_user_count': 2100,
                                    'overlap_asin': 'B07ZPKN6YR',
                                    'dist_lead_and_overlap_asin_purchased_user_count': 890,
                                    'user_overlap': 0.42,
                                    'url_to_lead_asin': 'https://amazon.com/dp/B08N5WRWNW',
                                    'url_to_overlap_asin': 'https://amazon.com/dp/B07ZPKN6YR'
                                },
                                {
                                    'lead_asin': 'B09JS1RSJ4',
                                    'lead_asin_purchases': 1580,
                                    'dist_lead_asin_purchased_user_count': 1450,
                                    'overlap_asin': 'B09JS234KL',
                                    'dist_lead_and_overlap_asin_purchased_user_count': 520,
                                    'user_overlap': 0.36,
                                    'url_to_lead_asin': 'https://amazon.com/dp/B09JS1RSJ4',
                                    'url_to_overlap_asin': 'https://amazon.com/dp/B09JS234KL'
                                },
                                {
                                    'lead_asin': 'B07FZ8S74R',
                                    'lead_asin_purchases': 440,
                                    'dist_lead_asin_purchased_user_count': 300,
                                    'overlap_asin': 'B07G2BWLKJ',
                                    'dist_lead_and_overlap_asin_purchased_user_count': 100,
                                    'user_overlap': 0.33,
                                    'url_to_lead_asin': 'https://amazon.com/dp/B07FZ8S74R',
                                    'url_to_overlap_asin': 'https://amazon.com/dp/B07G2BWLKJ'
                                },
                                {
                                    'lead_asin': 'B091G3WT74',
                                    'lead_asin_purchases': 7,
                                    'dist_lead_asin_purchased_user_count': 7,
                                    'overlap_asin': 'B091G4CZR8',
                                    'dist_lead_and_overlap_asin_purchased_user_count': 3,
                                    'user_overlap': 0.43,
                                    'url_to_lead_asin': 'https://amazon.com/dp/B091G3WT74',
                                    'url_to_overlap_asin': 'https://amazon.com/dp/B091G4CZR8'
                                }
                            ]
                        },
                        'interpretation_markdown': """## Analysis of Purchase Overlap Results

### Top Upselling Opportunities

**1. B08N5WRWNW → B08N5LNQCX (59% overlap)**
- **Extremely strong relationship**: 1,240 out of 2,100 customers bought both
- **Action**: Immediate remarketing campaign for the 860 customers who only bought B08N5WRWNW
- **Bundle opportunity**: These products are natural companions
- **Expected ROI**: Very high based on existing purchase patterns

**2. B08N5WRWNW → B07ZPKN6YR (42% overlap)**
- **Strong cross-sell potential**: 890 customers already purchase both
- **Secondary target**: Good for multi-product campaigns
- **Consider**: "Complete your set" messaging

**3. B09JS1RSJ4 → B09JS234KL (36% overlap)**
- **Moderate but valuable**: 520 customer overlap with good volume
- **Test opportunity**: Worth A/B testing bundle vs separate campaigns
- **Likely related**: Product codes suggest these are from same product line

**4. B07FZ8S74R → B07G2BWLKJ (33% overlap)**
- **Moderate relationship**: 100 customer overlap, worth exploring
- **Lower priority**: Include in broader remarketing efforts
- **Monitor**: Track if relationship strengthens over time

**5. B091G3WT74 → B091G4CZR8 (43% overlap - IGNORE)**
- **Statistical noise**: Only 7 total customers, not actionable
- **Insufficient data**: Wait for more purchases before drawing conclusions
- **Action**: Exclude from campaigns due to low volume

### Recommended Campaign Structure

#### Priority 1: High-Volume, High-Overlap Campaign
- **Target ASINs**: B08N5WRWNW buyers
- **Promote**: B08N5LNQCX and B07ZPKN6YR
- **Audience size**: ~1,000 customers who haven't purchased overlap products
- **Expected conversion rate**: 15-20% based on overlap data

#### Priority 2: Product Line Expansion
- **Target ASINs**: B09JS1RSJ4 buyers
- **Promote**: B09JS234KL
- **Test**: Bundle discount vs individual product promotion
- **Measure**: Incremental revenue from cross-sells

#### Priority 3: Category Exploration
- **Target**: Customers of any high-volume ASIN
- **Promote**: Related products with 20-35% overlap
- **Strategy**: Broader targeting with lower bids
- **Goal**: Discover new overlap patterns""",
                        'insights': [
                            '59% of B08N5WRWNW buyers also purchase B08N5LNQCX - strongest upsell opportunity',
                            'Products with 30%+ overlap and high volume are prime candidates for bundles',
                            'Ignore relationships with <50 total customers to avoid statistical noise',
                            'B08N5WRWNW appears to be a gateway product with multiple strong overlaps',
                            'Focus remarketing budget on products with >40% overlap for best ROI'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created example results for main analysis")
                    
                    # Add second example for edge cases
                    edge_case_example = {
                        'guide_query_id': query_id,
                        'example_name': 'Edge Cases and Patterns to Recognize',
                        'sample_data': {
                            'rows': [
                                {
                                    'lead_asin': 'B07XL5SHPS',
                                    'lead_asin_purchases': 15420,
                                    'dist_lead_asin_purchased_user_count': 14200,
                                    'overlap_asin': 'B07XL5TQJR',
                                    'dist_lead_and_overlap_asin_purchased_user_count': 11360,
                                    'user_overlap': 0.80,
                                    'url_to_lead_asin': 'https://amazon.com/dp/B07XL5SHPS',
                                    'url_to_overlap_asin': 'https://amazon.com/dp/B07XL5TQJR'
                                },
                                {
                                    'lead_asin': 'B086KKT3RX',
                                    'lead_asin_purchases': 850,
                                    'dist_lead_asin_purchased_user_count': 820,
                                    'overlap_asin': 'B086KKTXYZ',
                                    'dist_lead_and_overlap_asin_purchased_user_count': 12,
                                    'user_overlap': 0.01,
                                    'url_to_lead_asin': 'https://amazon.com/dp/B086KKT3RX',
                                    'url_to_overlap_asin': 'https://amazon.com/dp/B086KKTXYZ'
                                },
                                {
                                    'lead_asin': 'B09KGCW8HM',
                                    'lead_asin_purchases': 3200,
                                    'dist_lead_asin_purchased_user_count': 2900,
                                    'overlap_asin': 'B09KGCWABC',
                                    'dist_lead_and_overlap_asin_purchased_user_count': 1450,
                                    'user_overlap': 0.50,
                                    'url_to_lead_asin': 'https://amazon.com/dp/B09KGCW8HM',
                                    'url_to_overlap_asin': 'https://amazon.com/dp/B09KGCWABC'
                                }
                            ]
                        },
                        'interpretation_markdown': """## Recognizing Special Patterns

### Pattern 1: Consumable/Accessory Relationship (80% overlap)
**B07XL5SHPS → B07XL5TQJR**
- **Interpretation**: This is likely a main product + essential accessory or consumable
- **Strategy**: Always bundle these together at point of purchase
- **Warning**: Not a true upsell opportunity since most customers already buy both
- **Action**: Focus on new customer acquisition rather than cross-selling

### Pattern 2: False Positive (1% overlap)
**B086KKT3RX → B086KKTXYZ**
- **Interpretation**: Despite similar ASINs, these products have minimal overlap
- **Likely scenario**: Different variants that serve as substitutes, not complements
- **Action**: Do NOT create cross-sell campaigns between these products
- **Learning**: Similar ASIN patterns don't guarantee purchase relationships

### Pattern 3: Perfect Balance (50% overlap)
**B09KGCW8HM → B09KGCWABC**
- **Interpretation**: Exactly half of customers buy both - strong optional accessory
- **Opportunity**: 1,450 customers already see value in both
- **Target audience**: The 1,450 customers who only bought the lead ASIN
- **Campaign message**: "50% of customers also bought..."
- **Expected success**: High conversion rate due to social proof""",
                        'insights': [
                            '80%+ overlap often indicates essential accessories or consumables, not true upsell opportunities',
                            'Low overlap (<5%) between similar ASINs suggests substitute products',
                            '50% overlap represents the sweet spot for optional accessories',
                            'Always validate overlap patterns against product knowledge',
                            'High overlap with high volume may indicate bundle opportunities rather than upsell targets'
                        ],
                        'display_order': 2
                    }
                    
                    edge_response = client.table('build_guide_examples').insert(edge_case_example).execute()
                    if edge_response.data:
                        logger.info("Created edge case examples")
                        
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'lead_asin',
                'display_name': 'Lead ASIN',
                'definition': 'The primary ASIN being analyzed for purchase relationships',
                'metric_type': 'dimension',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'lead_asin_purchases',
                'display_name': 'Lead ASIN Purchases',
                'definition': 'Total number of purchases for the lead ASIN',
                'metric_type': 'metric',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'dist_lead_asin_purchased_user_count',
                'display_name': 'Lead ASIN Unique Purchasers',
                'definition': 'Number of unique users who purchased the lead ASIN',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'overlap_asin',
                'display_name': 'Overlap ASIN',
                'definition': 'The ASIN being checked for co-purchase with the lead ASIN',
                'metric_type': 'dimension',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'dist_lead_and_overlap_asin_purchased_user_count',
                'display_name': 'Overlap User Count',
                'definition': 'Number of unique users who purchased both the lead ASIN and overlap ASIN',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_overlap',
                'display_name': 'User Overlap Percentage',
                'definition': 'Percentage of lead ASIN buyers who also purchased the overlap ASIN (overlap users / lead users)',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'sequence_count',
                'display_name': 'Sequence Count',
                'definition': 'Number of times products were purchased in a specific order (for directional analysis)',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'avg_days_between_purchases',
                'display_name': 'Average Days Between Purchases',
                'definition': 'Average number of days between purchasing the first and second product',
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
        
        logger.info("✅ Successfully created ASIN Purchase Overlap for Upselling guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_asin_overlap_guide()
    sys.exit(0 if success else 1)