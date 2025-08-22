#!/usr/bin/env python3
"""
Seed script for Audiences based on high value customer segments Build Guide
This script creates the advanced audience building guide for identifying high-value customers
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

def create_high_value_customer_guide():
    """Create the Audiences based on high value customer segments guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_high_value_customer_segments',
            'name': 'Audiences based on high value customer segments',
            'category': 'Audience Building',
            'short_description': 'Learn how to identify and build audiences of high-value customers using percentile rankings and purchase history, enabling targeted campaigns for your most valuable customer segments.',
            'tags': ['Audience Building', 'Customer Segmentation', 'High Value Customers', 'Percentile Analysis', 'Flexible Shopping Insights'],
            'icon': 'TrendingUp',
            'difficulty_level': 'advanced',
            'estimated_time_minutes': 60,
            'prerequisites': [
                'Subscribe to Flexible Amazon shopping insights',
                'Access to AMC instance with customer purchase data',
                'Understanding of AMC audience queries and _for_audiences tables',
                'Customer purchases on Amazon e-commerce site (not just pixel conversions)',
                'Familiarity with percentile calculations and customer value metrics'
            ],
            'is_published': True,
            'display_order': 15,
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
                'section_id': 'data_query_instructions',
                'title': '1. Data Query Instructions',
                'content_markdown': """## 1.1 About rule-based audience queries

Unlike standard AMC queries, AMC Audience queries do not return visible results that you can download. Instead, the audience defined by the query is pushed directly to Amazon DSP. AMC rule-based audience queries require selecting a set of user_id values to create the Amazon DSP audience.

## 1.2 Tables used

**Note:** AMC rule-based queries use a unique set of tables that contain the `_for_audiences` suffix in the names.

**conversions_all_for_audiences**: This is a copy of the conversions_all table designed for use with AMC Audiences. More information about the conversions_all table can be found in the Instructional Query: Introduction to Flexible Amazon Shopping Insights.

### Key Fields:
- `user_id`: Unique identifier for users (only available in audience queries)
- `total_product_sales`: Total sales amount for products
- `tracked_asin`: ASIN that was involved in the conversion
- `advertiser_id`: Identifier for the advertiser account

## 1.3 Requirements

To use this query, you must:

1. **Subscribe to Flexible Amazon shopping insights** - Navigate to the Paid features tab and subscribe to Flexible Amazon shopping insights. Paid features are only available in certain regions. If you're unable to see the Paid features tab, reach out to your AdTech Account Executive.

2. **Have customer purchases on the Amazon e-commerce site** (for example https://www.amazon.com/). Note that if you have pixel conversions only, this query will not give you desired results.

We also strongly recommend using the High Value Customer Segment using Flexible shopping insights measurement IQ to better understand audience attributes prior to building the audience.""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'companion_measurement',
                'title': '2. Companion Measurement Query',
                'content_markdown': """## 2.1 Companion measurement query

A starting point to building this audience is assessing the appropriate percentile rank threshold to be used and the estimated audience size that would be created. This information can be obtained by executing the companion measurement query - Instructional Query: Identify High Value Customer Segments using Flexible shopping insights.

## 2.2 Understanding percentile rankings

Percentile rankings allow you to segment customers based on their relative value compared to all customers:

- **90th percentile (Top 10%)**: Ultra-high value customers who contribute disproportionately to revenue
- **75th percentile (Top 25%)**: High value customers with strong purchase behavior
- **50th percentile (Top 50%)**: Above-average customers showing consistent engagement
- **Below 50th percentile**: Lower value customers requiring different engagement strategies

## 2.3 Selecting the right percentile threshold

Consider these factors when choosing your percentile threshold:

1. **Audience size requirements**: Ensure you meet minimum audience sizes (typically 1000+ users)
2. **Campaign objectives**: Higher percentiles for exclusive offers, lower for broader campaigns
3. **Budget allocation**: Focus resources on customers with highest ROI potential
4. **Product strategy**: Different products may warrant different value thresholds""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'create_audience',
                'title': '3. Create an Audience: High Value Customer Segment',
                'content_markdown': """## 3.1 High value customer segment query

After you have identified a target percentile for high valued customers, you can continue by creating the audience.

For example, the following query creates an audience of customers whose value is greater than 50 percentile (as indicated by `WHERE Percentile >= 50`).

## 3.2 Query customization instructions

The query requires two key customizations:

1. **ASIN Filtering** - Choose one of two approaches:
   - Use `advertiser_id` to include all ASINs for a brand
   - Provide a specific list of ASINs for targeted campaigns

2. **Percentile Threshold** - Adjust the percentile value (1-100) based on your segmentation strategy:
   - Values outside 1-100 range will result in NULL resultset
   - Higher values create smaller, more exclusive audiences
   - Lower values create larger, more inclusive audiences

## 3.3 Understanding the query logic

The query works in three steps:

1. **Purchase Aggregation**: Sums total product sales per user for specified ASINs
2. **Percentile Calculation**: Ranks users and calculates their percentile position
3. **Audience Selection**: Filters users above the specified percentile threshold

## 3.4 Performance considerations

- Pre-filter ASINs to reduce computation time
- Consider running during off-peak hours for large datasets
- Monitor query execution time and optimize ASIN lists if needed""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'exploratory_analysis',
                'title': '4. Exploratory Analysis',
                'content_markdown': """## 4.1 Understanding your customer value distribution

Before creating the audience, it's important to understand how customer value is distributed in your data. The exploratory queries help you:

- Identify natural breakpoints in customer value
- Understand the concentration of revenue across customer segments
- Validate that your chosen percentile aligns with business objectives
- Ensure audience sizes meet activation requirements

## 4.2 Customer value distribution analysis

The distribution query segments customers into percentile buckets and provides key metrics:

- **User count**: Number of customers in each segment
- **Average sales**: Mean purchase value per segment
- **Min/Max sales**: Range of values within each segment

This helps you understand the revenue concentration and identify the most valuable segments for targeting.

## 4.3 Audience size validation

The validation query shows exactly how many users would be included at different percentile thresholds:

- **Top 10%**: Typically your VIP customers
- **Top 25%**: Loyal, high-value customers
- **Top 50%**: Above-average customers

Use this to ensure your audience meets minimum size requirements while maintaining targeting precision.

## 4.4 Interpreting the results

Look for:
- Sharp increases in average sales between segments (indicates clear value tiers)
- Sufficient audience sizes at your target percentiles
- Alignment between percentile thresholds and campaign objectives""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'best_practices',
                'title': '5. Best Practices and Implementation Tips',
                'content_markdown': """## 5.1 Percentile Selection Strategy

Choose your percentile threshold based on campaign objectives:

- **Top 10% (90th percentile)**: Ultra-high value customers for exclusive offers
  - VIP programs and early access
  - Premium product launches
  - Personalized account management

- **Top 25% (75th percentile)**: High value customers for premium campaigns
  - Loyalty program invitations
  - Upsell to higher-margin products
  - Special promotional offers

- **Top 50% (50th percentile)**: Above-average customers for loyalty programs
  - Repeat purchase campaigns
  - Cross-category promotions
  - Subscription program targeting

Consider your audience size requirements: Minimum 1000 users for DSP campaigns

## 5.2 ASIN Filtering Best Practices

- **Brand-level targeting**: Use advertiser_id filter for all products from a brand
- **Category-specific**: Group ASINs by product category for specialized campaigns
- **Price-point segmentation**: Separate luxury vs. mainstream product lines
- **Seasonal considerations**: Account for seasonal products and their impact on percentiles

## 5.3 Time Window Considerations

- **Default lookback**: Typically 14 days (check your instance settings)
- **Seasonal variations**: Consider longer windows during peak seasons
- **New product launches**: May need adjusted thresholds for newer products
- **Regular refreshing**: Run exploratory queries regularly to understand shifting percentiles

## 5.4 Campaign Strategy by Segment

**Top 10% Strategies:**
- Focus on retention and reducing churn
- Offer exclusive products or early access
- Provide superior customer service
- Create VIP experiences and rewards

**Top 25% Strategies:**
- Upsell to premium product lines
- Bundle complementary products
- Offer loyalty program benefits
- Provide personalized recommendations

**Top 50% Strategies:**
- Encourage repeat purchases
- Introduce subscription programs
- Cross-sell across categories
- Build brand affinity

## 5.5 Performance Optimization

- **Query efficiency**: Pre-aggregate purchase data when possible
- **Index usage**: Ensure proper indexes on user_id and tracked_asin
- **Batch processing**: Consider breaking large ASIN lists into smaller batches
- **Monitoring**: Track query execution times and optimize as needed

## 5.6 Validation Steps

1. **Run exploratory queries** to understand value distribution
2. **Validate audience sizes** at different thresholds
3. **Ensure minimum requirements** are met (1000+ users)
4. **Test with small campaign** before scaling
5. **Monitor performance metrics** and adjust thresholds as needed

## 5.7 Common Pitfalls to Avoid

- Setting percentile thresholds too high (resulting in audiences too small)
- Not accounting for seasonal variations in purchase behavior
- Forgetting to filter for relevant ASINs
- Not validating audience size before campaign launch
- Using stale data without regular refreshing""",
                'display_order': 5,
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
                'title': 'Customer Value Distribution Analysis',
                'description': 'Analyze how customer value is distributed across your customer base to identify natural segmentation points.',
                'sql_query': """-- Exploratory Query: Analyze customer value distribution
WITH purchase AS (
  SELECT
    user_id,
    SUM(total_product_sales) AS total_product_sales
  FROM
    conversions_all
  WHERE
    total_product_sales > 0
    /* Update with your ASIN filters */
    AND tracked_asin IN ('{{asin1}}', '{{asin2}}')
    AND user_id IS NOT NULL
  GROUP BY
    1
),
percentile_buckets AS (
  SELECT
    CASE 
      WHEN PERCENT_RANK() OVER (ORDER BY total_product_sales) >= 0.9 THEN 'Top 10%'
      WHEN PERCENT_RANK() OVER (ORDER BY total_product_sales) >= 0.75 THEN 'Top 25%'
      WHEN PERCENT_RANK() OVER (ORDER BY total_product_sales) >= 0.5 THEN 'Top 50%'
      ELSE 'Bottom 50%'
    END AS customer_segment,
    COUNT(DISTINCT user_id) as user_count,
    AVG(total_product_sales) as avg_sales,
    MIN(total_product_sales) as min_sales,
    MAX(total_product_sales) as max_sales
  FROM
    purchase
  GROUP BY
    1
)
SELECT * FROM percentile_buckets
ORDER BY 
  CASE customer_segment
    WHEN 'Top 10%' THEN 1
    WHEN 'Top 25%' THEN 2
    WHEN 'Top 50%' THEN 3
    ELSE 4
  END""",
                'parameters_schema': {
                    'asin1': {
                        'type': 'string',
                        'default': '',
                        'description': 'First ASIN to analyze'
                    },
                    'asin2': {
                        'type': 'string',
                        'default': '',
                        'description': 'Second ASIN to analyze'
                    }
                },
                'default_parameters': {
                    'asin1': '',
                    'asin2': ''
                },
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'This query segments your customers into value tiers and shows the distribution of sales across each segment. Use this to understand the concentration of revenue and identify natural breakpoints for audience creation.'
            },
            {
                'guide_id': guide_id,
                'title': 'Audience Size Validation',
                'description': 'Validate how many users would be included at different percentile thresholds before creating the audience.',
                'sql_query': """-- Exploratory Query: Validate audience sizes at different thresholds
WITH purchase AS (
  SELECT
    user_id,
    SUM(total_product_sales) AS total_product_sales
  FROM
    conversions_all
  WHERE
    total_product_sales > 0
    AND tracked_asin IN ('{{asin1}}', '{{asin2}}')
    AND user_id IS NOT NULL
  GROUP BY
    1
),
percentile_calc AS (
  SELECT
    user_id,
    total_product_sales,
    PERCENT_RANK() OVER (ORDER BY total_product_sales) * 100 AS percentile
  FROM
    purchase
)
SELECT
  'Top 10%' as segment,
  COUNT(DISTINCT CASE WHEN percentile >= 90 THEN user_id END) as user_count
FROM percentile_calc
UNION ALL
SELECT
  'Top 25%' as segment,
  COUNT(DISTINCT CASE WHEN percentile >= 75 THEN user_id END) as user_count
FROM percentile_calc
UNION ALL
SELECT
  'Top 50%' as segment,
  COUNT(DISTINCT CASE WHEN percentile >= 50 THEN user_id END) as user_count
FROM percentile_calc""",
                'parameters_schema': {
                    'asin1': {
                        'type': 'string',
                        'default': '',
                        'description': 'First ASIN to analyze'
                    },
                    'asin2': {
                        'type': 'string',
                        'default': '',
                        'description': 'Second ASIN to analyze'
                    }
                },
                'default_parameters': {
                    'asin1': '',
                    'asin2': ''
                },
                'display_order': 2,
                'query_type': 'exploratory',
                'interpretation_notes': 'This query shows the exact number of users at each percentile threshold. Ensure your chosen threshold provides sufficient audience size (typically 1000+ users) for campaign activation.'
            },
            {
                'guide_id': guide_id,
                'title': 'Create High Value Customer Segment Audience',
                'description': 'Create an audience of high-value customers based on percentile rankings for targeted campaigns.',
                'sql_query': """-- Instructional Query: High Value Custom Segments
/*
 ------- Customization Instructions -------
 1. Update the tracked_asin filter in the purchase CTE.
 2. Either provide an advertiser to include all the ASINs for
 or provide a specific set of ASINs.
 */
WITH purchase AS (
  SELECT
    user_id,
    SUM(total_product_sales) AS total_product_sales
  FROM
    conversions_all_for_audiences
  WHERE
    total_product_sales > 0
    /* This condition helps filter in only 
     relevant purchase conversions and filter out all others */
    /* REQUIRED UPDATE [1 OF 2]: Use either one of the below ASIN filters 
     based on your needs and comment out the other one. */
    AND tracked_asin IN (
      SELECT
        DISTINCT tracked_asin
      FROM
        amazon_attributed_events_by_conversion_time_for_audiences
      WHERE
        advertiser_id IN ('{{advertiser_id}}')
        /* Update with actual advertiser_id */
    )
    -- AND tracked_asin IN ('{{asin1}}', '{{asin2}}')
    /* Update with actual ASIN values */
    AND user_id IS NOT NULL
  GROUP BY
    1
),
-- Calculate rank percentile
percentile_calc AS (
  SELECT
    user_id,
    total_product_sales,
    RANK() OVER (
      ORDER BY
        total_product_sales
    ) AS rnk,
    (
      RANK() OVER (
        ORDER BY
          total_product_sales
      ) * 100
    ) / COUNT(user_id) OVER () AS Percentile
  FROM
    purchase
)
SELECT
  user_id
FROM
  percentile_calc c
WHERE
  /* REQUIRED UPDATE [2 OF 2]: To modify the percentile, 
   set '50' to another integer value (between 1 and 100).
   Values outside of this range with result in a NULL resultset. */
  Percentile >= {{percentile_threshold}}""",
                'parameters_schema': {
                    'advertiser_id': {
                        'type': 'string',
                        'default': '',
                        'description': 'Advertiser ID for brand-level targeting'
                    },
                    'asin1': {
                        'type': 'string',
                        'default': '',
                        'description': 'First ASIN for specific product targeting (optional)'
                    },
                    'asin2': {
                        'type': 'string',
                        'default': '',
                        'description': 'Second ASIN for specific product targeting (optional)'
                    },
                    'percentile_threshold': {
                        'type': 'integer',
                        'default': 50,
                        'description': 'Percentile threshold (1-100) - users above this percentile will be included',
                        'min': 1,
                        'max': 100
                    }
                },
                'default_parameters': {
                    'advertiser_id': '',
                    'asin1': '',
                    'asin2': '',
                    'percentile_threshold': 50
                },
                'display_order': 3,
                'query_type': 'main_analysis',
                'interpretation_notes': 'This query creates the actual audience of high-value customers based on your percentile threshold. The user_id values can be pushed to Amazon DSP for campaign activation.'
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add example results for queries
                if query['title'] == 'Customer Value Distribution Analysis':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Distribution Analysis',
                        'sample_data': {
                            'rows': [
                                {'customer_segment': 'Top 10%', 'user_count': 12345, 'avg_sales': 2456.78, 'min_sales': 987.65, 'max_sales': 15234.56},
                                {'customer_segment': 'Top 25%', 'user_count': 30862, 'avg_sales': 657.89, 'min_sales': 456.78, 'max_sales': 987.64},
                                {'customer_segment': 'Top 50%', 'user_count': 61725, 'avg_sales': 234.56, 'min_sales': 123.45, 'max_sales': 456.77},
                                {'customer_segment': 'Bottom 50%', 'user_count': 61725, 'avg_sales': 45.67, 'min_sales': 10.00, 'max_sales': 123.44}
                            ]
                        },
                        'interpretation_markdown': """**Customer Value Distribution Insights:**

The analysis reveals a clear concentration of value in the top customer segments:

**Key Findings:**
- **Top 10% (12,345 users)**: Average sales of $2,456.78 - these VIP customers drive disproportionate revenue
- **Top 25% (30,862 users)**: Average sales of $657.89 - strong segment for loyalty programs
- **Top 50% (61,725 users)**: Average sales of $234.56 - above-average customers with growth potential
- **Bottom 50% (61,725 users)**: Average sales of $45.67 - require different engagement strategies

**Revenue Concentration:**
- The top 10% of customers generate approximately 54x more revenue per customer than the bottom 50%
- Clear value tiers exist, making percentile-based segmentation highly effective

**Recommended Actions:**
1. Create separate campaigns for each value tier
2. Focus retention efforts on Top 10% to prevent churn
3. Develop upsell strategies for Top 25% segment
4. Build engagement programs to move Bottom 50% up the value chain""",
                        'insights': [
                            'Top 10% customers generate 54x more revenue than bottom 50%',
                            'Clear value breakpoints exist at 10%, 25%, and 50% percentiles',
                            'All segments have sufficient size for campaign activation',
                            'Consider tiered loyalty programs based on these segments'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created distribution analysis example")
                        
                elif query['title'] == 'Audience Size Validation':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Audience Size at Different Thresholds',
                        'sample_data': {
                            'rows': [
                                {'segment': 'Top 10%', 'user_count': 12345},
                                {'segment': 'Top 25%', 'user_count': 30862},
                                {'segment': 'Top 50%', 'user_count': 61725}
                            ]
                        },
                        'interpretation_markdown': """**Audience Size Validation Results:**

All percentile thresholds provide sufficient audience size for activation:

**Audience Sizes by Threshold:**
- **Top 10%**: 12,345 users - Ideal for VIP programs and exclusive offers
- **Top 25%**: 30,862 users - Perfect for premium campaigns and loyalty programs
- **Top 50%**: 61,725 users - Excellent for broad retention campaigns

**Campaign Activation Readiness:**
✅ All segments exceed minimum requirement (1000+ users)
✅ Top 10% large enough for A/B testing
✅ Top 25% suitable for multi-variant testing
✅ Top 50% enables geographic and demographic segmentation

**Recommended Approach:**
1. Start with Top 50% for initial campaign testing
2. Create specialized offers for Top 25%
3. Develop VIP experience for Top 10%
4. Monitor performance and adjust thresholds based on ROI""",
                        'insights': [
                            'All segments meet minimum size requirements for DSP activation',
                            'Top 10% provides focused targeting with sufficient scale',
                            'Top 25% balances reach and value concentration',
                            'Top 50% enables broad campaigns while maintaining value focus'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created size validation example")
                        
                elif query['query_type'] == 'main_analysis':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'High Value Audience Creation Success',
                        'sample_data': {
                            'rows': [
                                {'message': 'Audience created successfully', 'percentile_threshold': 50, 'user_count': 61725, 'status': 'READY_FOR_ACTIVATION'}
                            ]
                        },
                        'interpretation_markdown': """**High Value Customer Audience Created:**

Successfully created an audience of **61,725 high-value customers** (top 50%) ready for activation.

**Audience Characteristics:**
- Customers in the 50th percentile and above
- Average purchase value 5x higher than bottom 50%
- Demonstrated strong purchase history with your brand
- Ready for immediate DSP activation

**Campaign Strategy Recommendations:**

**Immediate Actions:**
1. **Retention Campaigns**: Prevent churn of valuable customers
2. **Cross-sell Opportunities**: Introduce complementary product lines
3. **Loyalty Programs**: Offer exclusive benefits and rewards
4. **Premium Products**: Upsell to higher-margin items

**Channel Activation:**
- **Amazon DSP**: Display and video campaigns
- **Sponsored Display**: Product targeting with custom audiences
- **Email Marketing**: Personalized offers (if available)

**Budget Allocation:**
- Allocate 60-70% of budget to this high-value segment
- Set higher bids to ensure competitive reach
- Use frequency caps of 5-7 impressions per week

**Success Metrics to Track:**
- Repeat purchase rate
- Average order value increase
- Customer lifetime value growth
- Campaign ROI by percentile segment""",
                        'insights': [
                            'Audience of 61,725 high-value customers ready for activation',
                            'Focus on retention and upsell strategies for maximum ROI',
                            'Monitor performance metrics by customer value tier',
                            'Consider creating sub-segments for personalized messaging'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created main analysis example")
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'total_product_sales',
                'display_name': 'Total Product Sales',
                'definition': 'Sum of all product sales for a user across the analysis period',
                'metric_type': 'metric',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'percentile',
                'display_name': 'Percentile Rank',
                'definition': 'The percentile rank of a user based on their total sales value (0-100)',
                'metric_type': 'metric',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'rnk',
                'display_name': 'Rank',
                'definition': 'The absolute rank of a user in the sales distribution',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_count',
                'display_name': 'User Count',
                'definition': 'Count of unique users in a segment or meeting criteria',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'avg_sales',
                'display_name': 'Average Sales',
                'definition': 'Average sales value per customer in a segment',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'min_sales',
                'display_name': 'Minimum Sales',
                'definition': 'Minimum sales value in a customer segment',
                'metric_type': 'metric',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'max_sales',
                'display_name': 'Maximum Sales',
                'definition': 'Maximum sales value in a customer segment',
                'metric_type': 'metric',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_id',
                'display_name': 'User ID',
                'definition': 'Unique identifier for a user (only available in audience queries, not measurement queries)',
                'metric_type': 'dimension',
                'display_order': 8
            },
            {
                'guide_id': guide_id,
                'metric_name': 'tracked_asin',
                'display_name': 'Tracked ASIN',
                'definition': 'ASIN that was involved in the conversion',
                'metric_type': 'dimension',
                'display_order': 9
            },
            {
                'guide_id': guide_id,
                'metric_name': 'advertiser_id',
                'display_name': 'Advertiser ID',
                'definition': 'Identifier for the advertiser account',
                'metric_type': 'dimension',
                'display_order': 10
            },
            {
                'guide_id': guide_id,
                'metric_name': 'customer_segment',
                'display_name': 'Customer Segment',
                'definition': 'Categorization of customers by value percentile (e.g., Top 10%, Top 25%)',
                'metric_type': 'dimension',
                'display_order': 11
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
            else:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info("✅ Successfully created High Value Customer Segments guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_high_value_customer_guide()
    sys.exit(0 if success else 1)