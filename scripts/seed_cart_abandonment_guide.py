#!/usr/bin/env python3
"""
Seed script for Cart Abandonment Audience Build Guide
Creates a comprehensive guide for building audiences of users who abandoned their shopping carts
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def create_cart_abandonment_guide():
    """Create the Cart Abandonment Audience guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Delete existing guide if it exists
        guide_id_str = 'guide_cart_abandonment_audience'
        try:
            # First get the guide to find its UUID
            existing = client.table('build_guides').select('id').eq('guide_id', guide_id_str).execute()
            if existing.data:
                guide_uuid = existing.data[0]['id']
                # Delete related data
                client.table('build_guide_metrics').delete().eq('guide_id', guide_uuid).execute()
                client.table('build_guide_examples').delete().match({'guide_query_id': guide_uuid}).execute()
                client.table('build_guide_queries').delete().eq('guide_id', guide_uuid).execute()
                client.table('build_guide_sections').delete().eq('guide_id', guide_uuid).execute()
                # Delete the guide itself
                client.table('build_guides').delete().eq('id', guide_uuid).execute()
                logger.info(f"Deleted existing guide: {guide_id_str}")
        except Exception as e:
            logger.info(f"No existing guide to delete or error deleting: {e}")
        
        # Create the main guide
        guide_data = {
            'guide_id': 'guide_cart_abandonment_audience',
            'name': 'Cart Abandonment Audience Creation',
            'category': 'Audience Creation',
            'short_description': 'Create rule-based audiences of users who added products to cart but haven\'t purchased, enabling targeted cart recovery campaigns',
            'tags': [
                'Cart abandonment',
                'Audience creation',
                'Recovery campaigns',
                'Rule-based audiences',
                'Conversion optimization',
                'Remarketing'
            ],
            'icon': 'ShoppingCart',
            'difficulty_level': 'intermediate',
            'estimated_time_minutes': 30,
            'prerequisites': [
                'AMC instance with rule-based audience capabilities',
                'Active e-commerce campaigns with cart tracking',
                'Amazon DSP access for audience activation',
                'Understanding of conversion event types'
            ],
            'is_published': True,
            'display_order': 3,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
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
                'title': '1. Introduction',
                'content_markdown': """## 1.1 Purpose

This guide helps you create audiences of users who have demonstrated high purchase intent by adding products to their shopping cart but have not yet completed the purchase. These cart abandoners represent a critical opportunity for recovery campaigns, as they've already shown strong interest in your products.

## 1.2 What You'll Learn

- How to identify and size cart abandonment audiences
- Creating rule-based audiences for cart abandoners
- Advanced segmentation based on attribution and timing
- Customization options for ASIN-specific targeting
- Strategic approaches to cart recovery campaigns
- Integration with Flexible Shopping Insights for enhanced targeting

## 1.3 Business Value

**Industry Statistics:**
- Average cart abandonment rate: 69.82% across industries
- Cart recovery campaigns can recover 10-30% of abandoned carts
- Abandoned cart emails have 45% open rates and 21% click-through rates
- ROI of cart abandonment campaigns often exceeds 1000%

## 1.4 Key Applications

- **Cart Recovery Campaigns**: Target users with reminders and incentives
- **Cross-Device Retargeting**: Reach users across different devices
- **Dynamic Product Ads**: Show exact products left in cart
- **Urgency Messaging**: Create time-sensitive offers
- **Competitive Conquest**: Win back users comparing products""",
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'section_id': 'understanding_abandonment',
                'title': '2. Understanding Cart Abandonment',
                'content_markdown': """## 2.1 Common Abandonment Reasons

Understanding why users abandon carts helps tailor recovery strategies:

- **Unexpected costs**: Shipping, taxes revealed at checkout
- **Complex checkout process**: Too many steps or required registration
- **Price comparison shopping**: Using cart to save items while comparing
- **Saving for later purchase**: Intentional delay for budget or timing
- **Technical issues or distractions**: Interruptions, errors, or timeouts

## 2.2 Event Types in AMC

| Event Type | event_subtype | Description | Use Case |
|------------|---------------|-------------|-----------|
| Add to Cart | shoppingCart | User added item to cart | Primary abandonment signal |
| Purchase | order | User completed purchase | Exclusion criteria |
| Detail Page View | detailPageView | User viewed product | Earlier funnel targeting |
| Wishlist | wishList | User saved for later | Alternative intent signal |
| Subscribe & Save | subscribe | Subscription purchase | Special handling needed |

## 2.3 Attribution Windows

**Standard Window**: 28-day window in conversions_for_audiences
- Balances recency with sufficient audience size
- Aligns with typical purchase consideration cycles

**Custom Windows**: Adjust based on your product category
- **Short (1-7 days)**: Consumables, impulse purchases
- **Medium (7-14 days)**: Fashion, electronics
- **Long (14-28 days)**: High-consideration items, luxury goods

**Real-time Updates**: Audiences refresh daily
- New abandoners added automatically
- Purchasers removed from targeting
- Maintains audience freshness""",
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'section_id': 'query_implementation',
                'title': '3. Query Implementation',
                'content_markdown': """## 3.1 Step 1: Exploratory Query - Size Your Audience

Always check audience size before creating to ensure minimum thresholds (typically 1,000+ users):

### Basic Exploratory Query
Check the size of your cart abandonment audience before creation.

### ASIN-Specific Exploratory
Filter to specific products when targeting particular items.

## 3.2 Step 2: Create the Audience

Convert the exploratory query to an audience creation query by:
1. Changing from `conversions` to `conversions_for_audiences`
2. Selecting only `user_id` (no aggregations)
3. Ensuring proper JOIN logic for exclusions

### Basic Audience Creation
Standard cart abandonment audience for all products.

### ASIN-Filtered Audience
Target abandoners of specific products only.

## 3.3 Advanced: Non-Ad-Attributed Cart Abandoners

For Flexible Shopping Insights subscribers, target organic cart abandoners who discovered products without ad exposure:

### Organic Cart Abandoners
Users who added to cart through organic discovery, not paid ads.

This audience is valuable for:
- Understanding organic demand
- Optimizing organic listing content
- Measuring true brand affinity
- Reducing advertising waste""",
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'section_id': 'customization_options',
                'title': '4. Customization Options',
                'content_markdown': """## 4.1 Time-Based Segmentation

Segment abandoners by recency for tailored messaging:

### Recent Abandoners (0-24 hours)
```sql
WHERE atc_dt_max >= CURRENT_TIMESTAMP - INTERVAL '1' DAY
```
**Strategy**: Gentle reminder, no discount needed

### Mid-Term Abandoners (1-7 days)
```sql
WHERE atc_dt_max BETWEEN CURRENT_TIMESTAMP - INTERVAL '7' DAY 
  AND CURRENT_TIMESTAMP - INTERVAL '1' DAY
```
**Strategy**: Small incentive, urgency messaging

### Long-Term Abandoners (7+ days)
```sql
WHERE atc_dt_max < CURRENT_TIMESTAMP - INTERVAL '7' DAY
```
**Strategy**: Stronger incentive, alternative products

## 4.2 Value-Based Segmentation

Target high-value carts for premium recovery efforts:

```sql
-- Add to atc CTE
SELECT
  user_id,
  MAX(event_dt_utc) AS atc_dt_max,
  SUM(product_value) AS cart_value
FROM conversions_for_audiences
WHERE event_subtype = 'shoppingCart'
GROUP BY user_id
HAVING SUM(product_value) > 100  -- High-value carts only
```

**Value Tiers**:
- **Low (<$50)**: Standard recovery tactics
- **Medium ($50-$150)**: Enhanced incentives
- **High (>$150)**: Premium treatment, personal outreach

## 4.3 Category-Specific Audiences

Create audiences by product category for specialized campaigns:

```sql
-- Add category filter using product catalog join
AND tracked_item IN (
  SELECT asin 
  FROM product_catalog 
  WHERE category = 'Electronics'
)
```

**Category Strategies**:
- **Fashion**: Highlight limited availability
- **Electronics**: Emphasize specifications and reviews
- **Consumables**: Suggest Subscribe & Save
- **Luxury**: Focus on exclusivity and quality""",
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'section_id': 'strategic_implementation',
                'title': '5. Strategic Implementation',
                'content_markdown': """## 5.1 Recovery Campaign Timeline

Implement a graduated approach based on time since abandonment:

### Hour 1-3: Immediate Recovery
- **Message**: "Did you forget something?"
- **Tactic**: Simple reminder, show cart contents
- **Channel**: Email notification
- **Incentive**: None needed

### Day 1-3: Incentive Phase
- **Message**: "Still interested? Here's 10% off"
- **Tactic**: Small discount, free shipping
- **Channel**: Email + Display retargeting
- **Incentive**: 5-10% discount

### Day 4-7: Stronger Incentive
- **Message**: "Last chance for your saved items"
- **Tactic**: Urgency, higher discount
- **Channel**: Multi-channel push
- **Incentive**: 15-20% discount

### Day 8+: Win-Back
- **Message**: "We miss you - here's our best offer"
- **Tactic**: Maximum discount, alternatives
- **Channel**: Full marketing mix
- **Incentive**: Best available offer

## 5.2 Message Personalization Framework

### Dynamic Elements
- Product images from abandoned cart
- Exact cart value and savings
- Personalized discount amount
- Stock availability alerts
- Price drop notifications
- Recently viewed alternatives

### Copy Variations by Abandonment Reason

| Suspected Reason | Message Approach | Example Copy |
|-----------------|------------------|--------------|
| High shipping cost | Free shipping offer | "Free shipping on your saved items" |
| Price comparison | Price guarantee | "Best price guaranteed" |
| Saved for later | Gentle reminder | "Your cart is waiting" |
| Payment issues | Payment options | "Now accepting PayPal" |
| Out of stock | Back in stock | "Good news - it's available!" |

## 5.3 Channel Orchestration

**Email Marketing** (Primary)
- Highest ROI channel
- Rich content capabilities
- Direct cart links

**Display Retargeting** (Visual)
- Dynamic product ads
- Cross-device reach
- Frequency capping essential

**Streaming TV** (Premium)
- For high-value carts only
- Brand reinforcement
- Halo effect on other channels

**Sponsored Products** (Search)
- Capture comparison shoppers
- Defend against competitors
- Category-level targeting

**Social Media** (Engagement)
- Instagram/Facebook dynamic ads
- User-generated content
- Social proof messaging""",
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'section_id': 'performance_optimization',
                'title': '6. Performance Optimization',
                'content_markdown': """## 6.1 Key Metrics

### Primary KPIs
- **Cart Recovery Rate**: Recovered carts / Total abandoned
  - Target: 10-20%
- **Revenue Recovery**: Revenue from recovered carts
  - Target: 5-10% of abandoned value
- **Cost Per Recovery**: Ad spend / Recovered carts
  - Target: <20% of average order value
- **Time to Recovery**: Average days from abandonment to purchase
  - Target: <7 days

### Secondary Metrics
- **Audience Growth Rate**: New abandoners per day
- **Click-Through Rate**: By message variant and channel
- **Discount Utilization**: % using offered discounts
- **Cross-Sell Success**: Additional items in recovered carts
- **Lifetime Value Impact**: LTV of recovered vs non-recovered

## 6.2 A/B Testing Framework

### Test Variables

**Timing Tests**
- First contact: 1hr vs 3hr vs 24hr
- Message frequency: Daily vs every 2 days
- Campaign duration: 7 days vs 14 days vs 30 days

**Incentive Tests**
- Discount levels: 0% vs 5% vs 10% vs 15%
- Discount type: Percentage vs dollar amount
- Free shipping threshold testing

**Message Tests**
- Urgency level: Soft vs medium vs high
- Personalization depth: Basic vs full dynamic
- Subject lines: Question vs statement vs emoji

**Creative Tests**
- Format: Static vs carousel vs video
- Product display: Single vs multiple items
- Call-to-action: "Complete purchase" vs "View cart"

## 6.3 Performance Benchmarks

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| Recovery Rate | <5% | 5-10% | 10-20% | >20% |
| Email Open Rate | <15% | 15-30% | 30-45% | >45% |
| Click-Through Rate | <2% | 2-5% | 5-10% | >10% |
| Conversion Rate | <1% | 1-3% | 3-5% | >5% |
| ROI | <500% | 500-1000% | 1000-2000% | >2000% |
| Time to Recovery | >14 days | 7-14 days | 3-7 days | <3 days |

### Optimization Tips
- Monitor performance by product category
- Adjust strategies for seasonal patterns
- Test different approaches for new vs returning customers
- Consider day-of-week and time-of-day impacts
- Track competitor promotional calendars""",
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'section_id': 'advanced_techniques',
                'title': '7. Advanced Techniques',
                'content_markdown': """## 7.1 Machine Learning Applications

### Predictive Abandonment Scoring
Build models to predict:
- **Recovery Likelihood**: Score 0-100 for recovery probability
- **Optimal Discount**: Minimum incentive needed
- **Best Contact Time**: When user most likely to convert
- **Channel Preference**: Email vs display vs social

### Implementation Approach
```sql
-- Include behavioral signals for ML scoring
SELECT
  user_id,
  COUNT(DISTINCT session_id) as browse_sessions,
  AVG(session_duration) as avg_session_time,
  COUNT(DISTINCT tracked_item) as products_viewed,
  MAX(product_value) as max_item_value
FROM conversions_for_audiences
WHERE event_dt_utc >= CURRENT_TIMESTAMP - INTERVAL '30' DAY
GROUP BY user_id
```

## 7.2 Cross-Sell Opportunities

Expand beyond simple cart recovery:

### Related Product Audiences
```sql
-- Include users who viewed related products
SELECT user_id
FROM conversions_for_audiences
WHERE event_subtype = 'detailPageView'
  AND tracked_item IN (
    SELECT related_asin 
    FROM product_relationships 
    WHERE primary_asin IN (cart_asins)
  )
```

### Bundle Recommendations
- Frequently bought together items
- Complementary products
- Upgrade opportunities
- Subscribe & Save conversions

## 7.3 Competitive Intelligence

### Target Competitor Cart Abandoners
```sql
-- Users who viewed competitor ASINs after cart abandonment
SELECT DISTINCT a.user_id
FROM atc_users a
JOIN conversions_for_audiences c
  ON a.user_id = c.user_id
WHERE c.event_subtype = 'detailPageView'
  AND c.tracked_item IN (competitor_asins)
  AND c.event_dt_utc > a.atc_dt_max
```

### Competitive Strategies
- **Price Matching**: Offer to match competitor prices
- **Value Proposition**: Highlight unique benefits
- **Exclusive Offers**: Member-only discounts
- **Quality Emphasis**: Focus on reviews and ratings

## 7.4 Attribution Analysis

Understanding multi-touch attribution for recovered carts:

```sql
-- Analyze touchpoints leading to recovery
SELECT
  channel,
  COUNT(*) as touches,
  AVG(time_to_conversion) as avg_time
FROM attribution_data
WHERE user_id IN (recovered_cart_users)
GROUP BY channel
ORDER BY touches DESC
```

### Attribution Insights
- Average touchpoints to recovery: 3-5
- Most influential channels by category
- Optimal channel sequence
- Incremental lift by channel""",
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'section_id': 'troubleshooting',
                'title': '8. Troubleshooting',
                'content_markdown': """## 8.1 Common Issues and Solutions

### Issue: Audience Too Small (<1,000 users)

**Possible Causes**:
- Time window too narrow
- ASIN filters too restrictive
- High purchase rate (low abandonment)

**Solutions**:
- Expand lookback window to 28+ days
- Remove or broaden ASIN filters
- Include detail page viewers
- Combine with wishlist audiences

### Issue: Low Recovery Rates (<5%)

**Possible Causes**:
- Messaging not compelling
- Timing not optimal
- Incentives insufficient
- Technical issues with campaigns

**Solutions**:
- A/B test message urgency and personalization
- Test contact timing (1hr vs 24hr)
- Gradually increase discount levels
- Verify campaign delivery and rendering
- Check for cart expiration issues

### Issue: High Unsubscribe Rates (>2%)

**Possible Causes**:
- Over-communication
- Irrelevant messaging
- Poor targeting
- Aggressive tone

**Solutions**:
- Implement frequency caps (max 3-5 messages)
- Improve segmentation and personalization
- Test softer messaging approaches
- Provide clear value in each communication
- Offer preference management options

### Issue: Duplicate Audiences

**Possible Causes**:
- Multiple queries creating overlapping audiences
- Lack of proper exclusion logic

**Solutions**:
- Use consistent naming conventions
- Implement proper user_id deduplication
- Document audience definitions clearly
- Regular audience audits

## 8.2 Best Practices

### Audience Management
✅ **DO**:
- Exclude recent purchasers (last 24-48 hours)
- Set minimum audience size thresholds
- Implement frequency caps
- Regular audience refresh (daily)
- Monitor audience quality metrics

❌ **DON'T**:
- Over-segment into tiny audiences
- Ignore cross-device behavior
- Forget to exclude employees/tests
- Message too frequently
- Use outdated audience data

### Campaign Execution
✅ **DO**:
- Start with conservative approach
- Test one variable at a time
- Document successful strategies
- Monitor competitive responses
- Maintain consistent brand voice

❌ **DON'T**:
- Launch without proper testing
- Change multiple variables simultaneously
- Ignore seasonal patterns
- Copy competitor tactics blindly
- Sacrifice brand for conversion

## 8.3 Privacy and Compliance

### Privacy Considerations
- **User Consent**: Ensure proper consent for remarketing
- **Opt-Out Options**: Clear unsubscribe mechanisms
- **Data Retention**: Follow regional requirements
- **Transparency**: Clear privacy policy communication

### Regional Regulations
- **GDPR (Europe)**: Explicit consent required
- **CCPA (California)**: Right to opt-out prominent
- **LGPD (Brazil)**: Similar to GDPR requirements
- **Industry Standards**: Follow IAB guidelines

### Security Best Practices
- Encrypt sensitive user data
- Regular security audits
- Access control implementation
- Audit trail maintenance
- Incident response planning""",
                'display_order': 8
            }
        ]
        
        # Insert sections
        for section in sections:
            response = client.table('build_guide_sections').insert(section).execute()
            if not response.data:
                logger.error(f"Failed to create section: {section['title']}")
        
        logger.info(f"Created {len(sections)} sections")
        
        # Create queries
        queries = [
            {
                'guide_id': guide_id,
                'query_type': 'exploratory',
                'title': 'Basic Cart Abandonment Audience Size',
                'description': 'Check the total size of your cart abandonment audience across all products',
                'sql_query': """/* Audience Exploratory Query: Added to cart but did not purchase */
-- Check audience size before creation to ensure minimum thresholds

WITH purchase AS(
  SELECT
    user_id,
    MAX(event_dt_utc) AS purchase_dt_max
  FROM
    conversions
  WHERE
    event_subtype = 'order'
  GROUP BY user_id
),
atc AS (
  SELECT
    user_id,
    MAX(event_dt_utc) AS atc_dt_max
  FROM
    conversions
  WHERE
    event_subtype = 'shoppingCart'
  GROUP BY user_id
)
SELECT
  COUNT(DISTINCT atc.user_id) as audience_size,
  COUNT(DISTINCT CASE 
    WHEN atc_dt_max >= CURRENT_TIMESTAMP - INTERVAL '1' DAY 
    THEN atc.user_id END) as last_24_hours,
  COUNT(DISTINCT CASE 
    WHEN atc_dt_max >= CURRENT_TIMESTAMP - INTERVAL '7' DAY 
    THEN atc.user_id END) as last_7_days
FROM
  atc
  LEFT JOIN purchase ON atc.user_id = purchase.user_id
WHERE
  atc_dt_max > purchase_dt_max
  OR purchase_dt_max IS NULL""",
                'parameters_schema': {},
                'default_parameters': {},
                'display_order': 1,
                'interpretation_notes': 'Use this query to check audience size before creation. Ensure minimum threshold of 1,000 users.'
            },
            {
                'guide_id': guide_id,
                'query_type': 'exploratory',
                'title': 'ASIN-Specific Cart Abandonment Size',
                'description': 'Check audience size for specific products only',
                'sql_query': """/* ASIN-Filtered Cart Abandonment Audience Size */
-- Optional: Filter by specific ASINs for targeted campaigns

WITH asins (asin) AS (
  VALUES
    {{asin_list}}
),
purchase AS(
  SELECT
    user_id,
    MAX(event_dt_utc) AS purchase_dt_max
  FROM
    conversions
  WHERE
    event_subtype = 'order'
    AND tracked_item IN (SELECT asin FROM asins)
  GROUP BY user_id
),
atc AS (
  SELECT
    user_id,
    MAX(event_dt_utc) AS atc_dt_max,
    COUNT(DISTINCT tracked_item) as items_in_cart,
    SUM(product_value) as cart_value
  FROM
    conversions
  WHERE
    event_subtype = 'shoppingCart'
    AND tracked_item IN (SELECT asin FROM asins)
  GROUP BY user_id
)
SELECT
  COUNT(DISTINCT atc.user_id) as audience_size,
  AVG(items_in_cart) as avg_items_per_cart,
  AVG(cart_value) as avg_cart_value,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cart_value) as median_cart_value
FROM
  atc
  LEFT JOIN purchase ON atc.user_id = purchase.user_id
WHERE
  atc_dt_max > purchase_dt_max
  OR purchase_dt_max IS NULL""",
                'parameters_schema': {
                    'asin_list': {
                        'type': 'string',
                        'description': 'List of ASINs to filter, format: (\'B000XXX1\'), (\'B000XXX2\')',
                        'default': "('B000XXXXX1'), ('B000XXXXX2')"
                    }
                },
                'default_parameters': {
                    'asin_list': "('B000XXXXX1'), ('B000XXXXX2')"
                },
                'display_order': 2,
                'interpretation_notes': 'Check audience size for specific products. Useful for targeted campaigns.'
            },
            {
                'guide_id': guide_id,
                'query_type': 'main_analysis',
                'title': 'Create Basic Cart Abandonment Audience',
                'description': 'Create a rule-based audience of all cart abandoners',
                'sql_query': """/* Audience Instructional Query: Cart Abandonment Audience */
-- Creates audience of users who added to cart but didn't purchase

WITH purchase AS(
  SELECT
    user_id,
    MAX(event_dt_utc) AS purchase_dt_max
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'order'
  GROUP BY user_id
),
atc AS (
  SELECT
    user_id,
    MAX(event_dt_utc) AS atc_dt_max
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'shoppingCart'
  GROUP BY user_id
)
SELECT
  atc.user_id
FROM
  atc
  LEFT JOIN purchase ON atc.user_id = purchase.user_id
WHERE
  atc_dt_max > purchase_dt_max
  OR purchase_dt_max IS NULL""",
                'parameters_schema': {},
                'default_parameters': {},
                'display_order': 3,
                'interpretation_notes': 'Creates a broad audience of all cart abandoners. Use for general recovery campaigns.'
            },
            {
                'guide_id': guide_id,
                'query_type': 'main_analysis',
                'title': 'Create ASIN-Specific Cart Abandonment Audience',
                'description': 'Create audience for specific products with optional filters',
                'sql_query': """/* ASIN-Specific Cart Abandonment Audience */
-- Create audience filtered to specific products

WITH asins (asin) AS (
  VALUES
    {{asin_list}}
),
purchase AS(
  SELECT
    user_id,
    MAX(event_dt_utc) AS purchase_dt_max
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'order'
    AND tracked_item IN (SELECT asin FROM asins)
  GROUP BY user_id
),
atc AS (
  SELECT
    user_id,
    MAX(event_dt_utc) AS atc_dt_max
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'shoppingCart'
    AND tracked_item IN (SELECT asin FROM asins)
  GROUP BY user_id
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
                    'asin_list': {
                        'type': 'string',
                        'description': 'List of ASINs to filter',
                        'default': "('asin1'), ('asin2')"
                    }
                },
                'default_parameters': {
                    'asin_list': "('asin1'), ('asin2')"
                },
                'display_order': 4,
                'interpretation_notes': 'Target cart abandoners of specific products for focused recovery campaigns.'
            },
            {
                'guide_id': guide_id,
                'query_type': 'main_analysis',
                'title': 'Time-Segmented Cart Abandonment Audience',
                'description': 'Create audiences segmented by time since abandonment',
                'sql_query': """/* Time-Segmented Cart Abandonment Audience */
-- Segment abandoners by recency for graduated messaging

WITH purchase AS(
  SELECT
    user_id,
    MAX(event_dt_utc) AS purchase_dt_max
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'order'
  GROUP BY user_id
),
atc AS (
  SELECT
    user_id,
    MAX(event_dt_utc) AS atc_dt_max
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'shoppingCart'
  GROUP BY user_id
)
SELECT
  atc.user_id
FROM
  atc
  LEFT JOIN purchase ON atc.user_id = purchase.user_id
WHERE
  (atc_dt_max > purchase_dt_max OR purchase_dt_max IS NULL)
  AND atc_dt_max BETWEEN 
    CURRENT_TIMESTAMP - INTERVAL '{{max_days}}' DAY 
    AND CURRENT_TIMESTAMP - INTERVAL '{{min_days}}' DAY""",
                'parameters_schema': {
                    'min_days': {
                        'type': 'integer',
                        'description': 'Minimum days since abandonment',
                        'default': 1
                    },
                    'max_days': {
                        'type': 'integer',
                        'description': 'Maximum days since abandonment',
                        'default': 7
                    }
                },
                'default_parameters': {
                    'min_days': 1,
                    'max_days': 7
                },
                'display_order': 5,
                'interpretation_notes': 'Segment abandoners by recency for graduated messaging strategies.'
            },
            {
                'guide_id': guide_id,
                'query_type': 'main_analysis',
                'title': 'High-Value Cart Abandonment Audience',
                'description': 'Target abandoners with high cart values for premium recovery',
                'sql_query': """/* High-Value Cart Abandonment Audience */
-- Target users with high-value abandoned carts

WITH purchase AS(
  SELECT
    user_id,
    MAX(event_dt_utc) AS purchase_dt_max
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'order'
  GROUP BY user_id
),
atc AS (
  SELECT
    user_id,
    MAX(event_dt_utc) AS atc_dt_max,
    SUM(product_value) AS cart_value
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'shoppingCart'
  GROUP BY user_id
  HAVING SUM(product_value) >= {{min_cart_value}}
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
                    'min_cart_value': {
                        'type': 'number',
                        'description': 'Minimum cart value threshold',
                        'default': 100
                    }
                },
                'default_parameters': {
                    'min_cart_value': 100
                },
                'display_order': 6,
                'interpretation_notes': 'Focus on high-value carts that justify premium recovery efforts and incentives.'
            },
            {
                'guide_id': guide_id,
                'query_type': 'main_analysis',
                'title': 'Non-Ad-Attributed Cart Abandonment (FSI)',
                'description': 'Target organic cart abandoners using Flexible Shopping Insights',
                'sql_query': """/* Non-Ad-Attributed Cart Abandonment Audience */
-- Requires Flexible Shopping Insights subscription
-- Target users who added to cart through organic discovery

SELECT
  user_id
FROM
  conversions_all_for_audiences
WHERE
  exposure_type = 'non-ad-exposed'
  AND event_subtype = 'shoppingCart'
  AND user_id IN (
    SELECT DISTINCT user_id
    FROM conversions_all_for_audiences
    WHERE event_category = 'website'
    GROUP BY user_id
    HAVING COUNT(DISTINCT event_category) = 1
  )
  AND user_id NOT IN (
    SELECT DISTINCT user_id
    FROM conversions_all_for_audiences
    WHERE event_subtype = 'order'
    AND event_dt_utc >= (
      SELECT MAX(event_dt_utc)
      FROM conversions_all_for_audiences c2
      WHERE c2.user_id = conversions_all_for_audiences.user_id
      AND c2.event_subtype = 'shoppingCart'
    )
  )""",
                'parameters_schema': {},
                'default_parameters': {},
                'display_order': 7,
                'interpretation_notes': 'Requires FSI subscription. Target users who discovered products organically, not through ads.'
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add examples for main queries
                if query['query_type'] == 'main_analysis' and 'Basic' in query['title']:
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Sample Cart Abandonment Audience Results',
                        'sample_data': {
                            'rows': [
                                {'user_id': 'user_123abc', 'cart_value': 89.99, 'days_since': 2},
                                {'user_id': 'user_456def', 'cart_value': 149.50, 'days_since': 1},
                                {'user_id': 'user_789ghi', 'cart_value': 45.00, 'days_since': 5},
                                {'user_id': 'user_012jkl', 'cart_value': 299.99, 'days_since': 3},
                                {'user_id': 'user_345mno', 'cart_value': 75.25, 'days_since': 7}
                            ]
                        },
                        'interpretation_markdown': """This audience includes 5,234 users who have abandoned their carts in the last 28 days. Key insights:

- **Audience Size**: Sufficient for effective targeting (>1,000 minimum)
- **Average Cart Value**: $112.75 indicates high recovery potential
- **Recency Distribution**: 60% abandoned within last 3 days (prime for recovery)
- **Recovery Opportunity**: At 15% recovery rate, expect ~785 conversions

**Recommended Actions**:
1. Segment by recency for graduated messaging
2. Prioritize high-value carts (>$100) with stronger incentives
3. Launch immediate recovery campaign for recent abandoners
4. Test different discount levels by cart value tiers""",
                        'display_order': 1
                    }
                    
                    client.table('build_guide_examples').insert(example_data).execute()
        
        # Create metrics
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'cart_abandonment_rate',
                'display_name': 'Cart Abandonment Rate',
                'definition': 'Percentage of users who add to cart but don\'t purchase. Calculated as Cart Abandoners / Total Add to Cart Events. Industry average is 69.82% - lower is better.',
                'metric_type': 'metric',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'cart_recovery_rate',
                'display_name': 'Cart Recovery Rate',
                'definition': 'Percentage of abandoned carts that are recovered. Calculated as Recovered Carts / Total Abandoned Carts. Target 10-20% recovery rate for effective campaigns.',
                'metric_type': 'metric',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'average_cart_value',
                'display_name': 'Average Cart Value',
                'definition': 'Average value of abandoned carts. Calculated as SUM(cart_value) / COUNT(distinct user_id). Higher values justify stronger recovery incentives.',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'time_to_recovery',
                'display_name': 'Time to Recovery',
                'definition': 'Average days between abandonment and purchase. Calculated as AVG(purchase_date - abandonment_date). Faster recovery indicates effective messaging.',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'user_id',
                'display_name': 'User ID',
                'definition': 'Unique identifier for each user. Hashed user identifier from AMC. Required for audience creation.',
                'metric_type': 'dimension',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'event_subtype',
                'display_name': 'Event Subtype',
                'definition': 'Type of conversion event (shoppingCart, order, etc.). Event classification from pixel. Distinguishes cart adds from purchases.',
                'metric_type': 'dimension',
                'display_order': 6
            },
            {
                'guide_id': guide_id,
                'metric_name': 'tracked_item',
                'display_name': 'Tracked Item',
                'definition': 'ASIN of product in cart. Product identifier from event. Enables product-specific targeting.',
                'metric_type': 'dimension',
                'display_order': 7
            },
            {
                'guide_id': guide_id,
                'metric_name': 'product_value',
                'display_name': 'Product Value',
                'definition': 'Value of product added to cart. Price at time of cart addition. Used for value-based segmentation.',
                'metric_type': 'dimension',
                'display_order': 8
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if not response.data:
                logger.error(f"Failed to create metric: {metric['display_name']}")
        
        logger.info(f"Created {len(metrics)} metrics")
        
        logger.info("Successfully created Cart Abandonment Audience guide")
        return True
        
    except Exception as e:
        logger.error(f"Error creating guide: {e}")
        return False

if __name__ == "__main__":
    success = create_cart_abandonment_guide()
    if success:
        print("✅ Cart Abandonment Audience guide created successfully")
    else:
        print("❌ Failed to create Cart Abandonment Audience guide")
        sys.exit(1)