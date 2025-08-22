#!/usr/bin/env python
"""
Seed script for Extended Customer Value build guide
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    print("Error: Missing Supabase credentials")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

def create_extended_customer_value_guide():
    """Create the Extended Customer Value build guide"""
    
    # 1. Create the main guide
    guide_data = {
        "guide_id": "guide_extended_customer_value",
        "name": "Compare Customer Value with Extended Lookback Window",
        "category": "Customer Analytics",
        "short_description": "Analyze long-term customer value beyond 14-day attribution using Flexible Shopping Insights to understand repeat purchase behavior and optimize remarketing strategies",
        "tags": ["customer-value", "ltv", "extended-attribution", "fsi", "repeat-purchase", "retention", "new-to-brand"],
        "icon": "TrendingUp",
        "difficulty_level": "advanced",
        "estimated_time_minutes": 40,
        "prerequisites": ["Amazon FSI subscription required", "Understanding of attribution windows", "Customer ASIN purchases on Amazon", "Knowledge of customer segmentation"],
        "is_published": True,
        "display_order": 2,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    result = supabase.table("build_guides").insert(guide_data).execute()
    if not result.data:
        print("❌ Failed to create guide")
        return False
        
    guide_uuid = result.data[0]['id']  # Get the UUID for foreign key references
    guide_id = guide_data["guide_id"]  # Keep the string ID for logging
    print(f"✓ Created guide: {guide_id} (UUID: {guide_uuid})")
    
    # 2. Create sections  
    sections = [
        {
            "guide_id": guide_uuid,
            "section_id": "introduction",
            "title": "Introduction",
            "display_order": 1,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Introduction

### Purpose of Extended Attribution Analysis

Standard 14-day attribution windows provide valuable insights into immediate campaign impact, but they often miss the full customer journey. Many customers, especially for considered purchases, take weeks or months to convert. This guide helps you understand the true long-term value of your advertising investments.

### Moving Beyond 14-Day ROAS

Traditional ROAS calculations based on 14-day attribution can significantly undervalue your campaigns:
- **Misses delayed conversions**: Customers researching high-consideration products often convert after 14 days
- **Undervalues brand building**: Initial touchpoints that drive awareness aren't credited
- **Ignores repeat purchases**: Customers acquired through ads often make multiple purchases over time
- **Limited remarketing insights**: Can't identify valuable customer segments for retention campaigns

### Requirements

To complete this analysis, you'll need:
- **Amazon FSI (Flexible Shopping Insights) subscription**: Required for extended attribution data
- **ASIN-level purchase data**: Track specific products your customers buy on Amazon
- **Historical campaign data**: At least 90 days of campaign history for meaningful insights
- **AMC instance access**: With appropriate permissions to query conversion data

### Benefits for Remarketing Strategy

This analysis will help you:
1. **Identify true customer lifetime value** by capturing purchases beyond 14 days
2. **Segment customers effectively** based on purchase behavior and timing
3. **Optimize budget allocation** between acquisition and retention campaigns
4. **Improve bidding strategies** with accurate long-term value data
5. **Develop targeted remarketing campaigns** for high-value customer segments"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "data_query_instructions",
            "title": "Data Query Instructions",
            "display_order": 2,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Data Query Instructions

### Data Returned Overview

The queries in this guide analyze customer purchase behavior across different attribution windows:

**Key metrics returned:**
- Customer segments (new-to-brand vs existing, one-off vs repeat)
- Total users in each segment
- Average revenue per user
- Units sold per customer
- Time between purchases distribution

### Tables Used

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `dsp_impressions` | DSP campaign exposure data | user_id, campaign_id, event_dt |
| `sponsored_ads_traffic` | Sponsored Ads clicks | user_id, campaign, click_dt |
| `amazon_attributed_events_by_conversion_time` | 14-day attribution conversions | user_id, purchases_14d, new_to_brand |
| `conversions_all` | All conversions (FSI required) | user_id, conversion_event_dt, product_sales |

### Important Timing Considerations

**Data Availability:**
- AMC data has a 14-day lag (most recent data is from 14 days ago)
- FSI data may have additional 1-2 day processing delay
- Run queries for completed time periods to ensure data accuracy

**Attribution Windows:**
- **Standard**: 14 days post-impression/click
- **Extended**: Customizable (30, 60, 90+ days)
- **Lookback**: Historical period for identifying existing customers

**Best Practices:**
- Schedule queries to run weekly for consistent tracking
- Use rolling windows to smooth out daily variations
- Account for seasonality in purchase patterns"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "understanding_time_between_purchases",
            "title": "Understanding Time Between Purchases",
            "display_order": 3,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Understanding Time Between Purchases

### Exploratory Analysis for Repeat Purchase Patterns

Before setting your extended attribution window, it's crucial to understand your customers' natural purchase cycles. The exploratory query analyzes the time gap between consecutive purchases for the same customer.

### How to Interpret the Distribution

The time between purchases analysis reveals:

1. **Immediate Repurchases (< 1 day)**: Often indicates:
   - Bundle purchases or forgot items
   - Multiple household members ordering
   - Subscription-like behavior

2. **Short-term Repeats (1-30 days)**: Suggests:
   - High satisfaction leading to quick reorders
   - Consumable products with short usage cycles
   - Trial to full-size progression

3. **Medium-term Repeats (30-90 days)**: Indicates:
   - Standard replenishment cycles
   - Seasonal purchase patterns
   - Considered purchase decisions

4. **Long-term Repeats (90+ days)**: Shows:
   - Durable goods replacement cycles
   - Annual or semi-annual purchases
   - Brand loyalty over extended periods

### Using Insights to Set Extended Window

**Finding the Optimal Window:**

1. **Identify the median purchase interval**: This represents typical customer behavior
2. **Look for natural breakpoints**: Where purchase frequency drops significantly
3. **Consider your business model**:
   - Consumables: 30-60 days may capture most value
   - Durables: 90-180 days might be necessary
   - Seasonal: Align with your selling seasons

**Example Analysis:**
```
If median time between purchases = 65 days:
- Set primary extended window to 60-90 days
- This captures ~50% of repeat purchases
- Balances data recency with completeness
```

### Recommendations by Industry

| Industry | Suggested Window | Rationale |
|----------|-----------------|-----------|
| CPG/Consumables | 30-60 days | Frequent repurchase cycles |
| Fashion/Apparel | 60-90 days | Seasonal shopping patterns |
| Electronics | 90-180 days | Longer consideration periods |
| Home/Garden | 120-365 days | Annual purchase cycles |"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "customer_segment_definitions",
            "title": "Customer Segment Definitions",
            "display_order": 4,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Customer Segment Definitions

### Core Segmentation Framework

The analysis divides customers into segments based on two key dimensions:

1. **Attribution Window**: When the purchase occurred relative to ad exposure
2. **Customer History**: New-to-brand vs existing customer status
3. **Purchase Frequency**: One-off vs repeat purchaser behavior

### 14-Day Attributed Segments

**Standard attribution window segments (baseline for comparison):**

| Segment | Definition | Use Case |
|---------|------------|----------|
| `14days_attributed` | All conversions within 14 days of ad exposure | Standard ROAS calculation |
| `14days_attributed_ntb` | New customers converting within 14 days | Acquisition campaign performance |
| `14days_attributed_existing` | Existing customers converting within 14 days | Retention campaign effectiveness |

### Extended Window Segments

**Extended attribution segments capture longer-term value:**

| Segment | Definition | Business Value |
|---------|------------|----------------|
| `extended_all` | All conversions within extended window (e.g., 60 days) | True campaign value |
| `extended_beyond_14days` | Conversions between day 15 and extended window end | Incremental value missed by standard attribution |
| `extended_attributed` | Customers with any conversion in extended window | Total addressable audience |

### New-to-Brand vs Existing Customers

**New-to-Brand (NTB) Customers:**
- No purchases of tracked ASINs in prior 365 days
- First-time buyers of your brand
- Higher acquisition cost but potential for long-term value
- Key metric for growth campaigns

**Existing Customers:**
- Previous purchasers within 365 days
- Lower acquisition cost
- Higher conversion rates
- Focus of retention campaigns

### One-off vs Repeat Purchasers

**Segmentation by purchase frequency:**

| Segment | Definition | Characteristics |
|---------|------------|-----------------|
| `ntb_oneoff` | New customers with single purchase | Trial users, need nurturing |
| `ntb_repeat` | New customers with 2+ purchases | High-value acquisitions |
| `existing_oneoff` | Returning customers, single purchase | Re-engaged but not loyal |
| `existing_repeat` | Returning customers, multiple purchases | Loyal customer base |

### Segment Value Hierarchy

Typical value progression (lowest to highest):
1. **One-off new customers**: Lowest immediate value, highest potential
2. **One-off existing customers**: Moderate value, reactivation opportunity
3. **Repeat new customers**: High value, successful acquisition
4. **Repeat existing customers**: Highest value, loyal advocates

### Using Segments for Campaign Optimization

| Segment Pattern | Action | Strategy |
|-----------------|--------|----------|
| High ntb_oneoff, low ntb_repeat | Improve onboarding | Focus on first purchase experience |
| Low existing_repeat rate | Enhance retention | Develop loyalty programs |
| High extended vs 14-day gap | Adjust attribution | Consider longer conversion cycles |
| Strong existing_repeat value | Increase retention spend | Maximize customer lifetime value |"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "example_query_results",
            "title": "Example Query Results",
            "display_order": 5,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Example Query Results

### Time Between Purchases Distribution

The exploratory query reveals natural purchase cycles for your products:

**Sample Distribution Analysis:**

| Days Between Purchases | User Count | Percentage | Cumulative % | Insight |
|------------------------|------------|------------|--------------|---------|
| < 1 day | 50,422 | 3.61% | 3.61% | Immediate reorders/bundles |
| 1-7 days | 187,234 | 13.42% | 17.03% | Quick satisfaction repeats |
| 7-14 days | 145,678 | 10.44% | 27.47% | Standard 14-day window |
| 14-30 days | 201,345 | 14.43% | 41.90% | Just missed by standard attribution |
| 30-60 days | 198,765 | 14.25% | 56.15% | Monthly replenishment |
| **60-90 days** | **215,843** | **15.47%** | **71.62%** | **Median purchase interval** |
| 90-180 days | 225,432 | 16.16% | 87.78% | Quarterly cycles |
| 180+ days | 170,943 | 12.25% | 100.00% | Annual/infrequent |

**Key Finding**: Median at 60-90 days suggests extending attribution window to at least 60 days would capture majority of repeat purchase value.

### Customer Value by Segment Comparison

The main analysis query compares customer value across attribution windows and segments:

**Aggregate Performance Metrics:**

| Segment | Total Users | Total Sales | Sales/User | Units/User | vs 14-day |
|---------|-------------|-------------|------------|------------|-----------|
| 14days_attributed | 2,933 | $72,802 | $24.82 | 1.8 | Baseline |
| extended_all (60d) | 56,797 | $2,156,234 | $37.96 | 2.9 | +53% value |
| extended_beyond_14d | 53,864 | $2,083,432 | $38.68 | 3.0 | Incremental |

**Detailed Segment Breakdown:**

| Customer Segment | Users | Sales/User | Units/User | % of Extended | Value Index |
|------------------|-------|------------|------------|---------------|-------------|
| **New-to-Brand** |
| ntb_all | 18,234 | $28.45 | 2.1 | 32.1% | 1.00 |
| ntb_oneoff | 14,681 | $22.30 | 1.0 | 25.9% | 0.78 |
| ntb_repeat | 3,553 | $40.20 | 4.2 | 6.3% | 1.41 |
| **Existing Customers** |
| existing_all | 38,563 | $42.44 | 3.4 | 67.9% | 1.49 |
| existing_oneoff | 26,700 | $35.82 | 2.0 | 47.0% | 1.26 |
| existing_repeat | 11,863 | $58.46 | 5.8 | 20.9% | 2.06 |

### Sample Data Interpretation

**Key Insights from Results:**

1. **Extended Attribution Captures 53% More Value**
   - 14-day window: $24.82 per user
   - 60-day window: $37.96 per user
   - Missing 19.4x more customers with standard attribution

2. **Repeat Customers Drive Disproportionate Value**
   - Repeat customers: 27.2% of users, 42.8% of revenue
   - Existing repeat: 2.6x higher value than one-off customers
   - New repeat: 1.8x higher value than new one-off

3. **New-to-Brand Conversion Quality**
   - 19.5% of new customers make repeat purchases (3,553/18,234)
   - New repeat customers worth 1.8x more than average new customer
   - Indicates strong product-market fit for acquired customers

4. **Existing Customer Reactivation Success**
   - 30.8% of existing customers make multiple purchases
   - Average 3.4 units per existing customer
   - Higher unit volumes suggest upselling success

### Actionable Recommendations

Based on these results:

1. **Adjust Attribution Windows**: Move to 60-day attribution for more accurate ROAS
2. **Increase Retention Investment**: Repeat customers show 2.6x higher value
3. **Optimize New Customer Experience**: Only 19.5% become repeat buyers
4. **Segment Bidding Strategies**: Bid higher for existing customer remarketing
5. **Develop Loyalty Programs**: Focus on converting one-off to repeat purchasers"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "metrics_definitions",
            "title": "Metrics Definitions",
            "display_order": 6,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Metrics Definitions

### User Group Classifications

| Metric | Definition | Calculation | Business Meaning |
|--------|------------|-------------|------------------|
| `user_group` | Customer segment identifier | Categorical assignment based on attribution and history | Enables targeted marketing strategies |
| `total_users` | Count of unique customers | COUNT(DISTINCT user_id) | Audience size for each segment |
| `unique_user_count` | Users in specific time interval | COUNT(DISTINCT user_id) per interval | Distribution analysis metric |

### Value Metrics

| Metric | Definition | Formula | Use Case |
|--------|------------|---------|----------|
| `total_product_sales` | Revenue from product purchases | SUM(product_sales) | Total monetary value generated |
| `sales_per_user` | Average revenue per customer | total_product_sales / total_users | Customer value comparison |
| `total_units_sold` | Quantity of items purchased | SUM(units_sold) | Volume metric for operations |
| `units_per_user` | Average items per customer | total_units_sold / total_users | Purchase depth indicator |

### Conversion Metrics

| Metric | Definition | Calculation | Insight |
|--------|------------|-------------|---------|
| `conversion_rate` | % of exposed users who purchase | (converters / exposed_users) × 100 | Campaign effectiveness |
| `repeat_purchase_rate` | % making 2+ purchases | (repeat_users / total_users) × 100 | Customer satisfaction proxy |
| `new_to_brand_rate` | % of customers new to brand | (ntb_users / total_users) × 100 | Acquisition effectiveness |

### Time-Based Metrics

| Metric | Definition | Measurement | Application |
|--------|------------|-------------|-------------|
| `time_between_purchases` | Days between consecutive orders | DATEDIFF(purchase_2, purchase_1) | Replenishment cycle analysis |
| `days_to_conversion` | Time from exposure to purchase | DATEDIFF(conversion, impression) | Conversion velocity |
| `purchase_percent` | % of users in time interval | (interval_users / total_users) × 100 | Distribution analysis |
| `cumulative_percent` | Running total percentage | SUM(purchase_percent) OVER (ORDER BY days) | Identify optimal windows |

### Segment Performance Indices

| Index | Formula | Interpretation | Action Threshold |
|-------|---------|----------------|------------------|
| `value_index` | segment_value / baseline_value | Relative performance vs baseline | > 1.5 = High value |
| `retention_index` | repeat_rate / avg_repeat_rate | Segment stickiness | > 1.2 = Strong retention |
| `ltv_multiplier` | extended_value / 14day_value | Long-term value capture | > 1.3 = Extend attribution |

### Advanced Calculations

**Customer Lifetime Value (CLV):**
```sql
CLV = (sales_per_user × purchase_frequency × customer_lifespan)
Where:
- purchase_frequency = total_purchases / time_period
- customer_lifespan = average active customer months
```

**Return on Ad Spend (ROAS):**
```sql
Standard ROAS = 14day_revenue / ad_spend
Extended ROAS = extended_revenue / ad_spend
True ROAS = (extended_revenue + repeat_revenue) / ad_spend
```

**Cohort Retention Rate:**
```sql
retention_rate_month_n = users_active_month_n / users_acquired_month_0
```

### Metric Relationships

Understanding how metrics relate helps identify optimization opportunities:

1. **Value Creation Chain:**
   - Impressions → Clicks → Conversions → Repeat Purchases → Customer Lifetime Value

2. **Efficiency Indicators:**
   - High sales_per_user + Low units_per_user = Premium positioning
   - Low sales_per_user + High units_per_user = Volume/discount strategy

3. **Growth Drivers:**
   - New-to-brand rate × Repeat purchase rate × Sales per user = Sustainable growth metric"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "kpi_calculations",
            "title": "KPI Calculations",
            "display_order": 7,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## KPI Calculations

### New-to-Brand Rate Formula

The new-to-brand rate measures customer acquisition effectiveness:

```sql
new_to_brand_rate = (ntb_customers / total_customers) × 100

Where:
- ntb_customers = Users with no purchases in prior 365 days
- total_customers = All converting users in period
```

**Calculation Example:**
```
Given:
- New-to-brand customers: 18,234
- Total customers: 56,797

new_to_brand_rate = (18,234 / 56,797) × 100 = 32.1%
```

**Benchmarks by Category:**
| Category | Good | Average | Needs Improvement |
|----------|------|---------|-------------------|
| Established Brands | 20-30% | 10-20% | <10% |
| New/Niche Brands | 40-60% | 25-40% | <25% |
| Commodity Products | 15-25% | 8-15% | <8% |

### Customer Lifetime Value Calculations

**Basic CLV Formula:**
```sql
CLV = Average_Order_Value × Purchase_Frequency × Customer_Lifespan

Components:
- AOV = total_product_sales / total_orders
- Frequency = total_orders / unique_customers / time_period
- Lifespan = average months customer remains active
```

**Extended CLV with Retention:**
```sql
CLV = Σ(t=0 to n) [Revenue_t × Retention_Rate_t × Discount_Factor_t]

Where:
- Revenue_t = Expected revenue in period t
- Retention_Rate_t = Probability customer active in period t
- Discount_Factor_t = 1 / (1 + discount_rate)^t
```

**Practical CLV Calculation from AMC Data:**
```sql
WITH customer_values AS (
  SELECT
    user_group,
    AVG(total_sales) as avg_first_purchase,
    AVG(CASE WHEN purchase_count > 1 THEN repeat_sales END) as avg_repeat_value,
    AVG(purchase_count) as avg_purchases,
    COUNT(CASE WHEN purchase_count > 1 THEN 1 END) * 1.0 / COUNT(*) as repeat_rate
  FROM customer_data
  GROUP BY user_group
)
SELECT
  user_group,
  avg_first_purchase + (avg_repeat_value * repeat_rate * estimated_cycles) as clv_estimate
FROM customer_values
```

**Example CLV by Segment:**
| Segment | First Purchase | Repeat Rate | Repeat Value | Est. CLV |
|---------|---------------|-------------|--------------|----------|
| NTB One-off | $22.30 | 0% | $0 | $22.30 |
| NTB Repeat | $25.50 | 100% | $14.70 | $69.60 |
| Existing One-off | $35.82 | 0% | $0 | $35.82 |
| Existing Repeat | $38.20 | 100% | $20.26 | $139.24 |

### Repeat Purchase Rate

**Standard Calculation:**
```sql
repeat_purchase_rate = (customers_with_2plus_purchases / total_customers) × 100
```

**Cohort-Based Repeat Rate:**
```sql
WITH cohort_analysis AS (
  SELECT
    DATE_TRUNC('month', first_purchase_date) as cohort_month,
    user_id,
    COUNT(DISTINCT order_date) as purchase_count
  FROM orders
  GROUP BY 1, 2
)
SELECT
  cohort_month,
  COUNT(DISTINCT user_id) as cohort_size,
  COUNT(DISTINCT CASE WHEN purchase_count > 1 THEN user_id END) as repeat_customers,
  (COUNT(DISTINCT CASE WHEN purchase_count > 1 THEN user_id END) * 100.0 / 
   COUNT(DISTINCT user_id)) as repeat_rate
FROM cohort_analysis
GROUP BY cohort_month
```

**Time-Windowed Repeat Rate:**
```sql
-- Repeat purchase within specific time windows
WITH purchase_windows AS (
  SELECT
    user_id,
    MIN(order_date) as first_purchase,
    COUNT(CASE WHEN order_date <= MIN(order_date) + INTERVAL '30 days' 
               THEN 1 END) as purchases_30d,
    COUNT(CASE WHEN order_date <= MIN(order_date) + INTERVAL '60 days' 
               THEN 1 END) as purchases_60d,
    COUNT(CASE WHEN order_date <= MIN(order_date) + INTERVAL '90 days' 
               THEN 1 END) as purchases_90d
  FROM orders
  GROUP BY user_id
)
SELECT
  AVG(CASE WHEN purchases_30d > 1 THEN 1.0 ELSE 0 END) * 100 as repeat_rate_30d,
  AVG(CASE WHEN purchases_60d > 1 THEN 1.0 ELSE 0 END) * 100 as repeat_rate_60d,
  AVG(CASE WHEN purchases_90d > 1 THEN 1.0 ELSE 0 END) * 100 as repeat_rate_90d
FROM purchase_windows
```

### Advanced KPI Formulas

**Customer Acquisition Cost (CAC) Payback:**
```sql
CAC_Payback_Days = Customer_Acquisition_Cost / (CLV / Customer_Lifespan_Days)
```

**Revenue Retention Rate:**
```sql
Revenue_Retention = (Revenue_Existing_Customers_Period_N / 
                     Revenue_Same_Customers_Period_0) × 100
```

**Incremental Extended Attribution Value:**
```sql
Incremental_Value = (Extended_Window_Revenue - Standard_14Day_Revenue) / 
                    Standard_14Day_Revenue × 100
```

### KPI Target Setting

| KPI | Excellent | Good | Average | Action Needed |
|-----|-----------|------|---------|---------------|
| NTB Rate | >40% | 25-40% | 15-25% | <15% |
| Repeat Rate (60d) | >25% | 15-25% | 8-15% | <8% |
| CLV:CAC Ratio | >3:1 | 2-3:1 | 1-2:1 | <1:1 |
| Extended Value Lift | >50% | 30-50% | 15-30% | <15% |"""
        },
        {
            "guide_id": guide_uuid,
            "section_id": "insights_and_interpretation",
            "title": "Insights and Data Interpretation",
            "display_order": 8,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Insights and Data Interpretation

### Extended vs Standard Attribution Comparison

**Key Finding: Extended Attribution Reveals Hidden Value**

Standard 14-day attribution significantly undervalues campaign performance:

| Metric | 14-Day Window | 60-Day Window | Impact |
|--------|---------------|---------------|--------|
| Attributed Users | 2,933 | 56,797 | **19.4x more customers** |
| Revenue per User | $24.82 | $37.96 | **53% higher value** |
| Total Revenue | $72,802 | $2,156,234 | **29.6x more revenue** |
| Repeat Purchase Rate | 8.2% | 27.2% | **3.3x higher** |

**Interpretation:**
- The 14-day window captures only 5.2% of actual converting customers
- Extended attribution shows true campaign impact on customer acquisition
- Longer consideration periods are normal for your product category
- Budget decisions based on 14-day ROAS may be severely underinvesting

### Repeat Customer Value Analysis

**Discovery: Repeat Customers Generate 2.6x More Value**

Segmentation reveals dramatic value differences:

| Customer Type | % of Users | % of Revenue | Value Multiple |
|---------------|------------|--------------|----------------|
| One-off Purchasers | 72.8% | 57.2% | 0.79x average |
| Repeat Purchasers | 27.2% | 42.8% | 1.57x average |
| NTB Repeat | 6.3% | 10.6% | 1.68x average |
| Existing Repeat | 20.9% | 32.2% | 1.54x average |

**Strategic Implications:**
1. **Focus on Retention**: Converting one-off to repeat buyers has highest ROI
2. **Segment Bidding**: Bid 2.6x higher for high repeat-probability audiences
3. **Experience Optimization**: First purchase experience critical for repeat behavior
4. **Loyalty Programs**: Investment in retention yields compound returns

### Actionable Recommendations

#### 1. Adjust Attribution and Measurement

**Immediate Actions:**
- Implement 60-day attribution window for true ROAS calculation
- Create dashboards showing both 14-day and extended metrics
- Educate stakeholders on hidden value in extended attribution

**Expected Impact:**
- 53% increase in reported ROAS
- Better budget allocation decisions
- Improved campaign optimization

#### 2. Develop Segment-Specific Strategies

**New-to-Brand Optimization:**
- Current: 32.1% of customers, 19.5% become repeat buyers
- Target: Increase repeat rate to 25% through:
  - Welcome series emails
  - First-purchase discounts for second order
  - Product education content

**Existing Customer Reactivation:**
- Current: 67.9% of customers, 30.8% make multiple purchases
- Target: Increase to 40% through:
  - Personalized remarketing based on purchase history
  - Loyalty rewards program
  - Cross-selling complementary products

#### 3. Optimize Budget Allocation

**Current State Analysis:**
| Campaign Type | Current Spend | 14-Day ROAS | Extended ROAS | Recommended Spend |
|---------------|---------------|-------------|---------------|-------------------|
| Acquisition | 70% | 1.8x | 2.8x | 60% |
| Retention | 20% | 3.2x | 8.3x | 35% |
| Brand | 10% | 0.9x | 2.1x | 5% |

**Reallocation Strategy:**
- Shift 15% of budget from acquisition to retention
- Maintain brand spending for long-term growth
- Focus acquisition on high-repeat-probability segments

#### 4. Implement Progressive Remarketing

**Time-Based Engagement Strategy:**

| Days Since Last Purchase | Message | Offer | Channel |
|--------------------------|---------|-------|---------|
| 0-14 | Thank you + Review request | None | Email |
| 15-30 | Product tips + Complementary items | 10% off | Email + Display |
| 31-60 | Replenishment reminder | 15% off | Email + Social |
| 61-90 | Win-back campaign | 20% off | All channels |
| 90+ | Re-engagement | Special offer | Targeted DSP |

#### 5. Enhance Customer Experience

**First Purchase Optimization:**
- Reduce friction in checkout process
- Provide immediate value confirmation
- Set expectations for product usage
- Offer instant second-purchase incentive

**Repeat Purchase Drivers:**
- Subscription options for regular buyers
- Volume discounts for bulk purchases
- Exclusive access to new products
- Personalized recommendations

### Success Metrics and Monitoring

**Weekly KPIs to Track:**
1. Extended attribution ROAS vs 14-day ROAS gap
2. New-to-brand repeat purchase rate
3. Existing customer reactivation rate
4. Average time between purchases
5. Customer lifetime value by acquisition source

**Monthly Analysis:**
- Cohort retention curves
- Segment migration patterns
- Campaign performance by customer segment
- CLV:CAC ratios by channel

**Quarterly Reviews:**
- Attribution window optimization
- Budget reallocation effectiveness
- Segment strategy performance
- Overall customer value growth

### Expected Outcomes

By implementing these recommendations, expect:

**Year 1 Targets:**
- 25% increase in reported ROAS through extended attribution
- 30% improvement in customer lifetime value
- 20% increase in repeat purchase rate
- 15% reduction in customer acquisition costs through better targeting

**Long-term Benefits:**
- Sustainable growth through improved retention
- Higher marketing efficiency from segment optimization
- Competitive advantage from superior customer understanding
- Increased profitability from repeat customer focus"""
        }
    ]
    
    for section in sections:
        result = supabase.table("build_guide_sections").upsert(section).execute()
    print(f"✓ Created {len(sections)} sections")
    
    # 3. Create queries
    queries = [
        {
            "guide_id": guide_uuid,
            "title": "Time Between Purchases Analysis",
            "query_type": "exploratory",
            "display_order": 1,
            "description": "Analyzes the time gap between consecutive purchases to understand customer repurchase patterns and determine optimal extended attribution window",
            "sql_query": """-- Time Between Purchases Analysis
-- This query helps determine the optimal extended attribution window by analyzing repeat purchase patterns

WITH purchase_sequence AS (
  -- Get all purchases for tracked ASINs with purchase dates
  SELECT
    user_id,
    conversion_event_dt as purchase_date,
    product_sales,
    units_sold,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY conversion_event_dt) as purchase_number
  FROM conversions_all
  WHERE 
    -- UPDATE: Add your tracked ASINs
    asin IN ('B08N5WRWNW', 'B07XQXZXJC', 'B09B8W5FX7')
    -- UPDATE: Set analysis time range (recommend 6-12 months)
    AND conversion_event_dt >= CURRENT_DATE - INTERVAL '180' DAY
    AND conversion_event_dt <= CURRENT_DATE - INTERVAL '14' DAY
),

time_gaps AS (
  -- Calculate time between consecutive purchases for each user
  SELECT
    p1.user_id,
    p1.purchase_date as first_purchase,
    p2.purchase_date as second_purchase,
    DATE_DIFF('day', p1.purchase_date, p2.purchase_date) as days_between_purchases,
    p1.product_sales as first_purchase_value,
    p2.product_sales as second_purchase_value
  FROM purchase_sequence p1
  INNER JOIN purchase_sequence p2
    ON p1.user_id = p2.user_id
    AND p1.purchase_number = p2.purchase_number - 1
  WHERE p2.purchase_date IS NOT NULL
),

distribution AS (
  -- Group into time intervals for distribution analysis
  SELECT
    CASE
      WHEN days_between_purchases < 1 THEN '< 1 day'
      WHEN days_between_purchases <= 7 THEN '1-7 days'
      WHEN days_between_purchases <= 14 THEN '7-14 days'
      WHEN days_between_purchases <= 30 THEN '14-30 days'
      WHEN days_between_purchases <= 60 THEN '30-60 days'
      WHEN days_between_purchases <= 90 THEN '60-90 days'
      WHEN days_between_purchases <= 180 THEN '90-180 days'
      ELSE '180+ days'
    END as time_between_purchases,
    COUNT(DISTINCT user_id) as unique_user_count,
    AVG(days_between_purchases) as avg_days_in_interval,
    AVG(second_purchase_value) as avg_repeat_purchase_value
  FROM time_gaps
  GROUP BY 1
)

-- Final output with percentages and cumulative distribution
SELECT
  time_between_purchases,
  unique_user_count,
  ROUND(avg_days_in_interval, 1) as avg_days_in_interval,
  ROUND(avg_repeat_purchase_value, 2) as avg_repeat_purchase_value,
  ROUND(100.0 * unique_user_count / SUM(unique_user_count) OVER (), 2) as purchase_percent,
  ROUND(100.0 * SUM(unique_user_count) OVER (ORDER BY 
    CASE time_between_purchases
      WHEN '< 1 day' THEN 1
      WHEN '1-7 days' THEN 2
      WHEN '7-14 days' THEN 3
      WHEN '14-30 days' THEN 4
      WHEN '30-60 days' THEN 5
      WHEN '60-90 days' THEN 6
      WHEN '90-180 days' THEN 7
      ELSE 8
    END
  ) / SUM(unique_user_count) OVER (), 2) as cumulative_percent
FROM distribution
ORDER BY 
  CASE time_between_purchases
    WHEN '< 1 day' THEN 1
    WHEN '1-7 days' THEN 2
    WHEN '7-14 days' THEN 3
    WHEN '14-30 days' THEN 4
    WHEN '30-60 days' THEN 5
    WHEN '60-90 days' THEN 6
    WHEN '90-180 days' THEN 7
    ELSE 8
  END;""",
            "parameters_schema": {
                "tracked_asins": {"type": "array", "description": "List of ASINs to track", "required": True},
                "time_range": {"type": "integer", "description": "Analysis time range in days", "default": 180}
            },
            "default_parameters": {
                "tracked_asins": ["B08N5WRWNW", "B07XQXZXJC", "B09B8W5FX7"],
                "time_range": 180
            }
        },
        {
            "guide_id": guide_uuid,
            "title": "Extended Customer Value Comparison",
            "query_type": "main_analysis",
            "display_order": 2,
            "description": "Compares customer value across standard 14-day and extended attribution windows, segmented by new/existing and one-off/repeat purchase behavior",
            "sql_query": """-- Extended Customer Value Comparison
-- Analyzes customer value beyond 14-day attribution to understand true long-term impact

WITH campaign_exposure AS (
  -- Get all users exposed to campaigns
  SELECT DISTINCT
    user_id,
    MIN(event_dt) as first_exposure_date
  FROM (
    -- DSP impressions
    SELECT user_id, event_dt
    FROM dsp_impressions
    WHERE 
      -- UPDATE: Add your DSP campaign IDs
      campaign_id IN ('1234567', '2345678', '3456789')
      AND event_dt >= CURRENT_DATE - INTERVAL '90' DAY
      AND event_dt <= CURRENT_DATE - INTERVAL '14' DAY
    
    UNION ALL
    
    -- Sponsored Ads clicks
    SELECT user_id, click_dt as event_dt
    FROM sponsored_ads_traffic
    WHERE 
      -- UPDATE: Add your Sponsored Ads campaign names
      campaign IN ('Campaign_Name_1', 'Campaign_Name_2')
      AND click_dt >= CURRENT_DATE - INTERVAL '90' DAY
      AND click_dt <= CURRENT_DATE - INTERVAL '14' DAY
  )
  GROUP BY user_id
),

standard_attribution AS (
  -- 14-day attribution window (standard)
  SELECT
    e.user_id,
    a.new_to_brand,
    SUM(a.purchases_14d) as total_purchases_14d,
    SUM(a.total_product_sales_14d) as total_sales_14d,
    SUM(a.total_units_sold_14d) as total_units_14d
  FROM campaign_exposure e
  INNER JOIN amazon_attributed_events_by_conversion_time a
    ON e.user_id = a.user_id
    AND a.conversion_event_dt BETWEEN e.first_exposure_date AND e.first_exposure_date + INTERVAL '14' DAY
  WHERE 
    -- UPDATE: Add your tracked ASINs
    a.asin IN ('B08N5WRWNW', 'B07XQXZXJC', 'B09B8W5FX7')
  GROUP BY e.user_id, a.new_to_brand
),

extended_attribution AS (
  -- Extended attribution window (customizable)
  SELECT
    e.user_id,
    -- Determine if new-to-brand based on purchase history
    CASE 
      WHEN MIN(c.conversion_event_dt) = MIN(CASE WHEN c.conversion_event_dt >= e.first_exposure_date - INTERVAL '365' DAY THEN c.conversion_event_dt END)
      THEN TRUE 
      ELSE FALSE 
    END as new_to_brand,
    COUNT(DISTINCT c.conversion_event_dt) as purchase_count,
    SUM(c.product_sales) as total_sales,
    SUM(c.units_sold) as total_units
  FROM campaign_exposure e
  INNER JOIN conversions_all c
    ON e.user_id = c.user_id
    -- UPDATE: Set your extended window (e.g., 60 days)
    AND c.conversion_event_dt BETWEEN e.first_exposure_date AND e.first_exposure_date + INTERVAL '60' DAY
  WHERE 
    -- UPDATE: Add your tracked ASINs (same as above)
    c.asin IN ('B08N5WRWNW', 'B07XQXZXJC', 'B09B8W5FX7')
  GROUP BY e.user_id
),

user_segments AS (
  -- Combine and segment users
  SELECT
    COALESCE(s.user_id, e.user_id) as user_id,
    -- Segment definitions
    CASE
      -- 14-day attributed segments
      WHEN s.user_id IS NOT NULL AND s.new_to_brand = TRUE THEN '14days_attributed_ntb'
      WHEN s.user_id IS NOT NULL AND s.new_to_brand = FALSE THEN '14days_attributed_existing'
      WHEN s.user_id IS NOT NULL THEN '14days_attributed'
      
      -- Extended window segments
      WHEN e.new_to_brand = TRUE AND e.purchase_count = 1 THEN 'ntb_oneoff'
      WHEN e.new_to_brand = TRUE AND e.purchase_count > 1 THEN 'ntb_repeat'
      WHEN e.new_to_brand = FALSE AND e.purchase_count = 1 THEN 'existing_oneoff'
      WHEN e.new_to_brand = FALSE AND e.purchase_count > 1 THEN 'existing_repeat'
      
      -- Aggregate segments
      WHEN e.new_to_brand = TRUE THEN 'ntb'
      WHEN e.new_to_brand = FALSE THEN 'existing'
      ELSE 'extended_all'
    END as user_group,
    
    COALESCE(s.total_sales_14d, 0) as sales_14d,
    COALESCE(s.total_units_14d, 0) as units_14d,
    COALESCE(e.total_sales, 0) as sales_extended,
    COALESCE(e.total_units, 0) as units_extended,
    e.purchase_count
  FROM standard_attribution s
  FULL OUTER JOIN extended_attribution e
    ON s.user_id = e.user_id
)

-- Final aggregation and metrics
SELECT
  user_group,
  COUNT(DISTINCT user_id) as total_users,
  SUM(CASE WHEN user_group LIKE '14days%' THEN sales_14d ELSE sales_extended END) as total_product_sales,
  SUM(CASE WHEN user_group LIKE '14days%' THEN units_14d ELSE units_extended END) as total_units_sold,
  ROUND(AVG(CASE WHEN user_group LIKE '14days%' THEN sales_14d ELSE sales_extended END), 2) as sales_per_user,
  ROUND(AVG(CASE WHEN user_group LIKE '14days%' THEN units_14d ELSE units_extended END), 1) as units_per_user,
  
  -- Calculate lift vs 14-day attribution
  CASE 
    WHEN user_group NOT LIKE '14days%' THEN
      ROUND(AVG(sales_extended) / NULLIF(
        (SELECT AVG(sales_14d) FROM user_segments WHERE user_group = '14days_attributed'), 0
      ), 2)
    ELSE NULL
  END as value_index_vs_14day
  
FROM user_segments
GROUP BY user_group

UNION ALL

-- Add summary rows
SELECT
  'SUMMARY: ' || 
  CASE 
    WHEN user_group LIKE '14days%' THEN '14-Day Attribution Total'
    ELSE 'Extended Attribution Total'
  END as user_group,
  COUNT(DISTINCT user_id) as total_users,
  SUM(CASE WHEN user_group LIKE '14days%' THEN sales_14d ELSE sales_extended END) as total_product_sales,
  SUM(CASE WHEN user_group LIKE '14days%' THEN units_14d ELSE units_extended END) as total_units_sold,
  ROUND(AVG(CASE WHEN user_group LIKE '14days%' THEN sales_14d ELSE sales_extended END), 2) as sales_per_user,
  ROUND(AVG(CASE WHEN user_group LIKE '14days%' THEN units_14d ELSE units_extended END), 1) as units_per_user,
  NULL as value_index_vs_14day
FROM user_segments
GROUP BY 
  CASE 
    WHEN user_group LIKE '14days%' THEN '14-Day Attribution Total'
    ELSE 'Extended Attribution Total'
  END

ORDER BY 
  CASE 
    WHEN user_group LIKE 'SUMMARY%' THEN 1
    WHEN user_group LIKE '14days%' THEN 2
    ELSE 3
  END,
  total_product_sales DESC;""",
            "parameters_schema": {
                "dsp_campaign_ids": {"type": "array", "description": "DSP campaign IDs", "required": True},
                "sa_campaign_names": {"type": "array", "description": "Sponsored Ads campaign names", "required": True},
                "tracked_asins": {"type": "array", "description": "ASINs to track", "required": True},
                "extended_window_days": {"type": "integer", "description": "Extended attribution window in days", "default": 60}
            },
            "default_parameters": {
                "dsp_campaign_ids": ["1234567", "2345678", "3456789"],
                "sa_campaign_names": ["Campaign_Name_1", "Campaign_Name_2"],
                "tracked_asins": ["B08N5WRWNW", "B07XQXZXJC", "B09B8W5FX7"],
                "extended_window_days": 60
            }
        }
    ]
    
    query_ids = {}
    for query in queries:
        result = supabase.table("build_guide_queries").insert(query).execute()
        if result.data:
            # Store query IDs for examples reference
            query_ids[query["title"]] = result.data[0]["id"]
    print(f"✓ Created {len(queries)} queries")
    
    # 4. Create example results
    examples = [
        {
            "guide_query_id": query_ids.get("Time Between Purchases Analysis"),
            "example_name": "Time Between Purchases Distribution",
            "display_order": 1,
            "sample_data": {
                "rows": [
                    {"time_between_purchases": "< 1 day", "unique_user_count": 50422, "avg_days_in_interval": 0.5, "avg_repeat_purchase_value": 45.23, "purchase_percent": 3.61, "cumulative_percent": 3.61},
                    {"time_between_purchases": "1-7 days", "unique_user_count": 187234, "avg_days_in_interval": 3.8, "avg_repeat_purchase_value": 52.14, "purchase_percent": 13.42, "cumulative_percent": 17.03},
                    {"time_between_purchases": "7-14 days", "unique_user_count": 145678, "avg_days_in_interval": 10.2, "avg_repeat_purchase_value": 48.76, "purchase_percent": 10.44, "cumulative_percent": 27.47},
                    {"time_between_purchases": "14-30 days", "unique_user_count": 201345, "avg_days_in_interval": 21.5, "avg_repeat_purchase_value": 55.32, "purchase_percent": 14.43, "cumulative_percent": 41.90},
                    {"time_between_purchases": "30-60 days", "unique_user_count": 198765, "avg_days_in_interval": 42.3, "avg_repeat_purchase_value": 61.45, "purchase_percent": 14.25, "cumulative_percent": 56.15},
                    {"time_between_purchases": "60-90 days", "unique_user_count": 215843, "avg_days_in_interval": 72.8, "avg_repeat_purchase_value": 58.92, "purchase_percent": 15.47, "cumulative_percent": 71.62},
                    {"time_between_purchases": "90-180 days", "unique_user_count": 225432, "avg_days_in_interval": 124.6, "avg_repeat_purchase_value": 62.18, "purchase_percent": 16.16, "cumulative_percent": 87.78},
                    {"time_between_purchases": "180+ days", "unique_user_count": 170943, "avg_days_in_interval": 287.4, "avg_repeat_purchase_value": 71.29, "purchase_percent": 12.25, "cumulative_percent": 100.00}
                ]
            },
            "interpretation_markdown": """**Key Findings:**

1. **Median Purchase Interval**: The highest concentration of repeat purchases occurs in the 60-90 day window (15.47%), indicating this is the natural repurchase cycle

2. **Quick Repurchases**: 27.47% of repeat purchases happen within 14 days, likely representing:
   - Bundle completions
   - Highly satisfied customers making additional purchases
   - Gift purchases or multiple household members

3. **Extended Window Recommendation**: Setting a 60-day attribution window would capture 56.15% of repeat purchases, while 90 days would capture 71.62%

4. **Long-tail Value**: 12.25% of customers repurchase after 180+ days, suggesting strong brand loyalty that standard attribution completely misses"""
        },
        {
            "guide_query_id": query_ids.get("Extended Customer Value Comparison"),
            "example_name": "Customer Value by Segment",
            "display_order": 2,
            "sample_data": {
                "rows": [
                    {"user_group": "SUMMARY: 14-Day Attribution Total", "total_users": 2933, "total_product_sales": 72802.45, "total_units_sold": 5282, "sales_per_user": 24.82, "units_per_user": 1.8, "value_index_vs_14day": None},
                    {"user_group": "SUMMARY: Extended Attribution Total", "total_users": 56797, "total_product_sales": 2156234.78, "total_units_sold": 164711, "sales_per_user": 37.96, "units_per_user": 2.9, "value_index_vs_14day": None},
                    {"user_group": "14days_attributed", "total_users": 2933, "total_product_sales": 72802.45, "total_units_sold": 5282, "sales_per_user": 24.82, "units_per_user": 1.8, "value_index_vs_14day": None},
                    {"user_group": "14days_attributed_ntb", "total_users": 942, "total_product_sales": 21234.56, "total_units_sold": 1508, "sales_per_user": 22.54, "units_per_user": 1.6, "value_index_vs_14day": None},
                    {"user_group": "14days_attributed_existing", "total_users": 1991, "total_product_sales": 51567.89, "total_units_sold": 3774, "sales_per_user": 25.90, "units_per_user": 1.9, "value_index_vs_14day": None},
                    {"user_group": "extended_all", "total_users": 56797, "total_product_sales": 2156234.78, "total_units_sold": 164711, "sales_per_user": 37.96, "units_per_user": 2.9, "value_index_vs_14day": 1.53},
                    {"user_group": "ntb", "total_users": 18234, "total_product_sales": 518781.30, "total_units_sold": 38295, "sales_per_user": 28.45, "units_per_user": 2.1, "value_index_vs_14day": 1.15},
                    {"user_group": "ntb_oneoff", "total_users": 14681, "total_product_sales": 327386.30, "total_units_sold": 14681, "sales_per_user": 22.30, "units_per_user": 1.0, "value_index_vs_14day": 0.90},
                    {"user_group": "ntb_repeat", "total_users": 3553, "total_product_sales": 142830.60, "total_units_sold": 14923, "sales_per_user": 40.20, "units_per_user": 4.2, "value_index_vs_14day": 1.62},
                    {"user_group": "existing", "total_users": 38563, "total_product_sales": 1637453.48, "total_units_sold": 131042, "sales_per_user": 42.44, "units_per_user": 3.4, "value_index_vs_14day": 1.71},
                    {"user_group": "existing_oneoff", "total_users": 26700, "total_product_sales": 956394.00, "total_units_sold": 53400, "sales_per_user": 35.82, "units_per_user": 2.0, "value_index_vs_14day": 1.44},
                    {"user_group": "existing_repeat", "total_users": 11863, "total_product_sales": 693751.38, "total_units_sold": 68805, "sales_per_user": 58.46, "units_per_user": 5.8, "value_index_vs_14day": 2.35}
                ]
            },
            "interpretation_markdown": """**Critical Insights:**

1. **Extended Attribution Captures 53% More Value**
   - Standard 14-day: $24.82 per user
   - Extended 60-day: $37.96 per user
   - This represents a 1.53x value multiplier

2. **Massive Audience Loss with Standard Attribution**
   - 14-day window: 2,933 users
   - 60-day window: 56,797 users
   - **You're missing 94.8% of converting customers with standard attribution**

3. **Repeat Customers Drive Exceptional Value**
   - Existing repeat customers: $58.46 per user (2.35x baseline)
   - New-to-brand repeat: $40.20 per user (1.62x baseline)
   - One-off customers significantly underperform

4. **New-to-Brand Success Rate**
   - 19.5% of new customers become repeat buyers (3,553/18,234)
   - These repeat new customers are worth 1.8x more than one-off new customers
   - Focus on converting first-time buyers to repeat customers

5. **Strategic Implications**
   - Existing customers show 49% higher value than new customers
   - Repeat purchasers generate 63% more value than one-off buyers
   - Investment in retention and repeat purchase drivers will yield highest returns"""
        }
    ]
    
    for example in examples:
        result = supabase.table("build_guide_examples").upsert(example).execute()
    print(f"✓ Created {len(examples)} examples")
    
    # 5. Create metrics
    metrics = [
        {
            "guide_id": guide_uuid,
            "metric_name": "user_group",
            "display_name": "User Group",
            "definition": "Customer segment identifier based on attribution window and purchase behavior. Enables targeted marketing strategies for different customer value segments",
            "metric_type": "dimension",
            "display_order": 1
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "total_users",
            "display_name": "Total Users",
            "definition": "Count of unique customers in each segment. Calculated as COUNT(DISTINCT user_id). Used for audience size in campaign planning and budget allocation",
            "metric_type": "metric",
            "display_order": 2
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "total_product_sales",
            "display_name": "Total Product Sales",
            "definition": "Total revenue from product purchases. Calculated as SUM(product_sales). Used for revenue impact measurement and ROI calculations",
            "metric_type": "metric",
            "display_order": 3
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "sales_per_user",
            "display_name": "Sales Per User",
            "definition": "Average revenue per customer. Calculated as total_product_sales / total_users. Used for customer value comparison across segments",
            "metric_type": "metric",
            "display_order": 4
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "units_per_user",
            "display_name": "Units Per User",
            "definition": "Average units purchased per customer. Calculated as total_units_sold / total_users. Purchase depth and engagement indicator",
            "metric_type": "metric",
            "display_order": 5
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "time_between_purchases",
            "display_name": "Time Between Purchases",
            "definition": "Categorized time interval between consecutive purchases. Used for understanding natural repurchase cycles and optimizing retention timing",
            "metric_type": "dimension",
            "display_order": 6
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "purchase_percent",
            "display_name": "Purchase Percentage",
            "definition": "Percentage of users in each time interval. Calculated as (interval_users / total_users) × 100. Used for distribution analysis when setting attribution windows",
            "metric_type": "metric",
            "display_order": 7
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "cumulative_percent",
            "display_name": "Cumulative Percentage",
            "definition": "Running total percentage of users. Calculated as SUM(purchase_percent) OVER (ORDER BY interval). Identifies coverage at different attribution windows",
            "metric_type": "metric",
            "display_order": 8
        },
        {
            "guide_id": guide_uuid,
            "metric_name": "value_index_vs_14day",
            "display_name": "Value Index vs 14-Day",
            "definition": "Relative value compared to 14-day attribution baseline. Calculated as segment_value / baseline_14day_value. Quantifies incremental value of extended attribution",
            "metric_type": "metric",
            "display_order": 9
        }
    ]
    
    for metric in metrics:
        result = supabase.table("build_guide_metrics").upsert(metric).execute()
    print(f"✓ Created {len(metrics)} metrics")
    
    print(f"\n✅ Successfully created Extended Customer Value build guide!")
    print(f"   Guide ID: {guide_id}")
    print(f"   Sections: {len(sections)}")
    print(f"   Queries: {len(queries)}")
    print(f"   Examples: {len(examples)}")
    print(f"   Metrics: {len(metrics)}")

if __name__ == "__main__":
    try:
        create_extended_customer_value_guide()
    except Exception as e:
        print(f"❌ Error creating guide: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)