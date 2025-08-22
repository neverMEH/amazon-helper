#!/usr/bin/env python3
"""
Seed script for Audience that added to cart but did not purchase Build Guide
This script creates the audience building guide content in the database
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

def create_cart_abandonment_guide():
    """Create the Audience that added to cart but did not purchase guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_cart_abandonment_audience',
            'name': 'Audience that added to cart but did not purchase',
            'category': 'Audience Building',
            'short_description': 'Learn how to identify and build audiences of users who added items to their cart but haven\'t completed a purchase, enabling targeted remarketing campaigns.',
            'tags': ['Audience Building', 'Remarketing', 'Cart Abandonment', 'Conversion Optimization'],
            'icon': 'ShoppingCart',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 30,
            'prerequisites': [
                'Access to AMC instance with conversion data',
                'Understanding of AMC audience queries',
                'Familiarity with _for_audiences table suffixes',
                'Minimum audience size requirements (typically 1000+ users)'
            ],
            'is_published': True,
            'display_order': 10,
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
                'section_id': 'audience_instructions',
                'title': '1. Audience Query Instructions',
                'content_markdown': """## 1.1 About AMC audience queries

AMC audience queries require selecting a set of user_id values. For more information, refer to Amazon Marketing Cloud custom audiences.

## 1.2 Tables used

**Note:** AMC audience queries use tables that contain the `_for_audiences` suffix in the names.

**conversions_for_audiences**: Much like the conversions table, conversions_for_audiences provides shoppingCart and order information in the event_subtype field for ASIN conversions. This table contains relevant conversions for all ASINs that were tracked to an Amazon DSP or sponsored ads campaign in the AMC instance if the user was served a qualifying traffic event within the 28-day period before the conversion event.

### Key Fields:
- `user_id`: Unique identifier for users (only available in audience queries)
- `event_subtype`: Type of conversion event (shoppingCart, order, detailPageView)
- `event_dt_utc`: Timestamp of the conversion event
- `tracked_item`: ASIN that was involved in the conversion event""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'exploratory_query',
                'title': '2. Exploratory Query',
                'content_markdown': """## 2.1 Purpose of Exploratory Query

Before creating an audience, investigating the value of the opportunity is important. While user_id can never be returned in an AMC measurement query, COUNT of user_id can be returned. Our exploratory query counts the number of people that added to cart more recently than they purchased or added to cart and never purchased.

## 2.2 ASIN Filtering

We add an optional ASIN filter to help limit the products analyzed if you have a large portfolio of products. This allows you to:
- Focus on specific product categories
- Target high-value or strategic ASINs
- Create more granular audiences for specialized campaigns

## 2.3 Query Returns

This query returns the number of user_id's that meet the criteria and indicates the potential size of our audience.

**Note:** It is a best practice to check the estimated size of the audience prior to submitting the query to AMC. This allows you to not only investigate the opportunity, but also make sure the audience reaches the minimum number of records required. For more information, refer to Rule-based audience queries.""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'create_audience',
                'title': '3. Create an Audience',
                'content_markdown': """## 3.1 Audience Creation Query

The following query creates an audience that added to cart, which is the same audience that you counted in the exploratory query. The only difference is you can use SELECT user_id with AMC Audiences queries.

## 3.2 Customization Ideas

### Event Type Variations
- Replace `shoppingCart` with `detailPageView` or other events to reach consumers at different moments in their customer journey
- Combine multiple event types for broader audience reach
- Create sequential audiences (e.g., viewed → added to cart → no purchase)

### ASIN Filtering Strategies
- The filter is set to simply remove all users who made a purchase from the ASIN list
- The join could be extended to ensure that if they had a `detailPageView` of an ASIN but purchased another ASIN, they were not eliminated from the set
- Consider category-level filtering for broader targeting

### Time-Based Segmentation
- Add recency filters to target users who abandoned cart within specific timeframes
- Create urgency-based segments (e.g., abandoned within last 24 hours vs. last 7 days)
- Layer seasonal considerations for holiday or promotional periods""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'shopping_insights',
                'title': '4. Shopping Insights Paid Features',
                'content_markdown': """## 4.1 Reaching customers by attribution

**Note:** You must be a Flexible Shopping Insights Paid Features subscriber to run the following query. To learn more, navigate to the Paid Features tab.

## 4.2 Advanced Attribution Filtering

The Amazon Flexible Shopping Insights Paid Feature provides conversions for tracked ASINs which can be filtered by ad attribution. You can further filter customers that have added to cart (or have any website engagement) but did not purchase further based on their ad attribution.

## 4.3 Use Case Example

As an example, you can identify and reach customers that:
1. Have added to cart (can be any website conversion)
2. Are non-ad-attributed
3. Have not made a purchase

The following query would allow you to leverage AMC Audiences to target these users.

### Benefits of Attribution-Based Targeting:
- **Non-ad-attributed users**: Target organic traffic that showed purchase intent
- **Ad-attributed users**: Retarget users who engaged with your ads but didn't convert
- **Mixed attribution**: Create sophisticated audiences based on attribution patterns

### Key Considerations:
- `exposure_type` field distinguishes between 'ad-exposed' and 'non-ad-exposed' users
- `event_category` helps filter by interaction type (website, purchase, etc.)
- Combining attribution data with behavioral signals creates more precise audiences""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'best_practices',
                'title': '5. Best Practices',
                'content_markdown': """## 5.1 Audience Size Validation

1. **Always run the exploratory query first** to check audience size
2. **Ensure minimum size requirements** - typically 1000+ users for audience activation
3. **Monitor audience refresh rates** - cart abandonment audiences can change rapidly

## 5.2 ASIN Strategy

1. **Start broad, then narrow** - Begin without ASIN filters to understand total opportunity
2. **Test different product sets** - Create separate audiences for different product categories
3. **Consider price points** - High-value ASINs may warrant different remarketing strategies

## 5.3 Event Type Selection

1. **DetailPageView vs ShoppingCart** - Different events indicate different levels of purchase intent
2. **Combine events strategically** - Layer multiple signals for more qualified audiences
3. **Test different combinations** - What works for one product category may not work for another

## 5.4 Remarketing Campaign Strategies

1. **Urgency messaging** - Recent cart abandoners may respond to time-limited offers
2. **Product reminders** - Show the exact products they added to cart
3. **Cross-sell opportunities** - Suggest complementary products
4. **Dynamic creative** - Use the cart data to personalize ad creative

## 5.5 Performance Monitoring

1. **Track audience growth** - Monitor how your audience size changes over time
2. **Measure incremental impact** - Compare performance vs. standard retargeting
3. **Test activation channels** - DSP, Sponsored Display, and other available channels
4. **Optimize frequency** - Balance reminder frequency with user experience""",
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
                'title': 'Exploratory Query - Count Cart Abandoners',
                'description': 'Count the number of users who added to cart but did not purchase to estimate audience size before creation.',
                'sql_query': """/* Audience Exploratory Query: Added to cart but did not purchase */
-- Optional update: To filter by ASINs, add one or more ASINs to the list of ASINs below and uncomment lines [1 of 2] and [2 of 2]
WITH asins (asin) AS (
  VALUES
    /* Optional update: Populate the list of ASINs below to filter by ASINs */
    ('{{asin1}}'),
    ('{{asin2}}')
),
purchase AS(
  SELECT
    user_id,
    MAX(event_dt_utc) AS purchase_dt_max
  FROM
    conversions
  WHERE
    event_subtype = 'order'
    /* AND tracked_item IN (SELECT asin FROM asins) -- Optional update [1 of 2]: Uncomment this line to enable ASIN filters. Leave the line commented to skip filters. */
  GROUP BY
    1
),
atc AS (
  SELECT
    user_id,
    MAX(event_dt_utc) AS atc_dt_max
  FROM
    conversions
  WHERE
    event_subtype = 'shoppingCart'
    /* AND tracked_item IN ( SELECT asin FROM asins ) -- Optional update [2 of 2]: Uncomment this line to enable ASIN filters. Leave the line commented to skip filters. */
  GROUP BY
    1
)
SELECT
  COUNT(DISTINCT atc.user_id) as user_count
FROM
  atc
  LEFT JOIN purchase ON atc.user_id = purchase.user_id
WHERE
  atc_dt_max > purchase_dt_max
  OR purchase_dt_max IS NULL""",
                'parameters_schema': {
                    'asin1': {
                        'type': 'string',
                        'default': '',
                        'description': 'First ASIN to filter (optional - leave empty to skip filtering)'
                    },
                    'asin2': {
                        'type': 'string',
                        'default': '',
                        'description': 'Second ASIN to filter (optional - leave empty to skip filtering)'
                    }
                },
                'default_parameters': {
                    'asin1': '',
                    'asin2': ''
                },
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'This query returns the count of unique users who have added items to cart but haven\'t purchased. Use this count to validate that your audience meets minimum size requirements (typically 1000+ users) before creating the actual audience.'
            },
            {
                'guide_id': guide_id,
                'title': 'Create Cart Abandonment Audience',
                'description': 'Create an audience of users who added to cart but did not purchase for remarketing campaigns.',
                'sql_query': """/* Audience Instructional Query: Audience that added to cart but did not purchase */
-- Optional update: To filter by ASINs, add one or more ASINs to the list of ASINs below and uncomment lines [1 of 2] and [2 of 2]
WITH asins (asin) AS (
  VALUES
    /* Update: Populate the list of ASINs below to filter by ASINs */
    ('{{asin1}}'),
    ('{{asin2}}')
),
purchase AS(
  SELECT
    user_id,
    MAX(event_dt_utc) AS purchase_dt_max
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'order'
    /* AND tracked_item IN ( SELECT asin FROM asins ) -- Optional update [1 of 2]: Uncomment this line to enable ASIN filters. Leave the line commented to skip filters. */
  GROUP BY
    1
),
atc AS (
  SELECT
    user_id,
    MAX(event_dt_utc) AS atc_dt_max
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'shoppingCart'
    /* AND tracked_item IN ( SELECT asin FROM asins ) -- Optional update [2 of 2]: Uncomment this line to enable ASIN filters. Leave the line commented to skip filters. */
  GROUP BY
    1
)
SELECT
  atc.user_id
FROM
  atc
  LEFT JOIN purchase ON atc.user_id = purchase.user_id
WHERE
  atc_dt_max > purchase_dt_max
  OR purchase_dt_max IS NULL""",
                'parameters_schema': {
                    'asin1': {
                        'type': 'string',
                        'default': '',
                        'description': 'First ASIN to filter (optional - leave empty to skip filtering)'
                    },
                    'asin2': {
                        'type': 'string',
                        'default': '',
                        'description': 'Second ASIN to filter (optional - leave empty to skip filtering)'
                    }
                },
                'default_parameters': {
                    'asin1': '',
                    'asin2': ''
                },
                'display_order': 2,
                'query_type': 'main_analysis',
                'interpretation_notes': 'This query creates the actual audience for activation. The user_id values returned can be used to create a custom audience in Amazon DSP or other advertising platforms for remarketing campaigns.'
            },
            {
                'guide_id': guide_id,
                'title': 'Shopping Insights - Non-Ad-Attributed Cart Abandoners',
                'description': 'Identify non-ad-attributed users who added to cart but did not purchase (requires Shopping Insights Paid Features).',
                'sql_query': """/* Audience Instructional Query: Reach engaged customers who are non-ad-attributed and have yet to make a purchase */
-- Note: Requires Flexible Shopping Insights Paid Features subscription
SELECT
  user_id
FROM
  conversions_all_for_audiences
WHERE
  exposure_type = 'non-ad-exposed'
  AND event_subtype = '{{event_type}}' -- EVENT SUBTYPE CAN BE ANY TYPE OF WEBSITE CONVERSION
  AND user_id IN (
    SELECT
      DISTINCT user_id
    FROM
      conversions_all_for_audiences
    WHERE
      event_category = 'website'
    GROUP BY
      1
    HAVING
      COUNT (DISTINCT event_category) = 1
  )""",
                'parameters_schema': {
                    'event_type': {
                        'type': 'string',
                        'default': 'shoppingCart',
                        'description': 'Type of website conversion event (shoppingCart, detailPageView, etc.)',
                        'enum': ['shoppingCart', 'detailPageView', 'addToWishlist', 'subscribe']
                    }
                },
                'default_parameters': {
                    'event_type': 'shoppingCart'
                },
                'display_order': 3,
                'query_type': 'advanced',
                'interpretation_notes': 'This query targets organic traffic that showed purchase intent but didn\'t convert. These users may be more receptive to remarketing as they discovered your products organically.'
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add example results for queries
                if query['query_type'] == 'exploratory':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Exploratory Results',
                        'sample_data': {
                            'rows': [
                                {'user_count': 125435}
                            ]
                        },
                        'interpretation_markdown': """**Audience Size Analysis:**

The exploratory query identified **125,435 users** who added items to cart but haven't purchased yet.

**Key Insights:**
- This audience size is well above the minimum requirement (1000+ users)
- Large enough for effective A/B testing and campaign optimization
- Represents a significant remarketing opportunity

**Next Steps:**
1. Proceed with audience creation using the main query
2. Consider segmenting by recency (last 7 days vs. 8-30 days)
3. Test different creative messages for cart abandonment""",
                        'insights': [
                            '125,435 users represents a substantial remarketing opportunity',
                            'Audience is large enough for multiple test segments',
                            'Consider urgency-based messaging for recent abandoners'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created exploratory example results")
                        
                elif query['query_type'] == 'main_analysis':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Audience Creation Success',
                        'sample_data': {
                            'rows': [
                                {'message': 'Audience created successfully', 'user_count': 125435, 'status': 'READY_FOR_ACTIVATION'}
                            ]
                        },
                        'interpretation_markdown': """**Audience Creation Complete:**

Successfully created an audience of **125,435 cart abandoners** ready for activation.

**Activation Recommendations:**

**Immediate Actions (0-7 days since abandonment):**
- Deploy urgency messaging ("Items in your cart are selling fast!")
- Offer limited-time discounts (10-15% off)
- Show exact products from their cart

**Follow-up Actions (8-30 days since abandonment):**
- Broader product recommendations
- Category-level promotions
- New arrival notifications for similar items

**Campaign Setup Tips:**
- Set frequency caps at 3-5 impressions per week
- Use dynamic creative to show abandoned products
- Test different calls-to-action (Complete Purchase vs. View Cart)
- Monitor conversion rates and adjust bidding accordingly""",
                        'insights': [
                            'Audience ready for immediate activation across DSP and Sponsored Display',
                            'Test urgency vs. incentive-based messaging',
                            'Monitor daily for optimal refresh frequency',
                            'Consider dayparting based on original cart addition times'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info("Created main analysis example results")
            else:
                logger.error(f"Failed to create query: {query['title']}")
        
        # Create metrics definitions
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'user_count',
                'display_name': 'User Count',
                'definition': 'The count of unique users matching the audience criteria',
                'metric_type': 'metric',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_id',
                'display_name': 'User ID',
                'definition': 'Unique identifier for a user (only available in audience queries, not measurement queries)',
                'metric_type': 'dimension',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'atc_dt_max',
                'display_name': 'Last Add to Cart Date',
                'definition': 'Most recent date when the user added an item to their cart',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'purchase_dt_max',
                'display_name': 'Last Purchase Date',
                'definition': 'Most recent date when the user completed a purchase',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'event_subtype',
                'display_name': 'Event Subtype',
                'definition': 'Type of conversion event (shoppingCart, order, detailPageView, addToWishlist)',
                'metric_type': 'dimension',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'tracked_item',
                'display_name': 'Tracked Item (ASIN)',
                'definition': 'ASIN that was involved in the conversion event',
                'metric_type': 'dimension',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'exposure_type',
                'display_name': 'Exposure Type',
                'definition': 'Attribution type indicating whether user was ad-exposed or non-ad-exposed (Shopping Insights only)',
                'metric_type': 'dimension',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'event_category',
                'display_name': 'Event Category',
                'definition': 'High-level category of the event (website, purchase, etc.)',
                'metric_type': 'dimension',
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
        
        logger.info("✅ Successfully created Cart Abandonment Audience guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {e}")
        return False

if __name__ == "__main__":
    success = create_cart_abandonment_guide()
    sys.exit(0 if success else 1)