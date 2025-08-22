#!/usr/bin/env python3
"""
Seed script for List and Registry Audience Build Guide
Creates a comprehensive guide for building audiences from wishlist and registry users
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def create_list_registry_guide():
    """Create the List and Registry Audience guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Delete existing guide if it exists
        guide_id_str = 'guide_list_registry_audience'
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
            'guide_id': 'guide_list_registry_audience',
            'name': 'Audience Creation - List and Registry Users',
            'category': 'Audience Creation',
            'short_description': 'Create rule-based audiences of users who have added products to wishlists, baby registries, or wedding registries for targeted remarketing campaigns',
            'tags': [
                'Audience creation',
                'Wishlist targeting',
                'Registry targeting',
                'Rule-based audiences',
                'Remarketing',
                'Customer engagement'
            ],
            'icon': 'Users',
            'difficulty_level': 'beginner',
            'estimated_time_minutes': 20,
            'prerequisites': [
                'AMC instance with rule-based audience capabilities',
                'Active products with wishlist/registry functionality',
                'Amazon DSP access for audience activation',
                'Understanding of AMC audience tables'
            ],
            'is_published': True,
            'display_order': 5,
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
                'title': '1. Introduction',
                'content_markdown': """## Purpose

This guide helps you create audiences of users who have shown high purchase intent by adding your products to wishlists or registries. These audiences represent engaged customers who are actively considering your products for future purchases, making them valuable targets for remarketing campaigns.

## What You'll Learn

- How to create rule-based audiences for list and registry users
- Different types of lists and registries available for targeting
- Customization options for ASIN-specific audiences
- Best practices for audience sizing and activation
- Strategic applications for registry-based audiences

## Business Applications

**Remarketing Campaigns**: Target users who saved products but haven't purchased

**Event-Based Marketing**: Reach registry creators before key dates (weddings, baby arrivals)

**Abandoned Browse Recovery**: Re-engage users who showed interest but didn't convert

**Cross-Sell Opportunities**: Promote complementary products to registry users

**Seasonal Campaigns**: Target wishlist users during gift-giving seasons

## Types of Lists and Registries

- **Wishlist**: General saved items for future purchase consideration
- **Baby Registry**: Products selected for baby showers and new arrivals
- **Wedding Registry**: Items chosen for wedding gifts
- **Custom Lists**: User-created collections for various purposes""",
                'display_order': 1,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'understanding_amc_audiences',
                'title': '2. Understanding AMC Audience Queries',
                'content_markdown': """## How Rule-Based Audiences Work

AMC audience queries differ from standard measurement queries:
- Select user_id values to create Amazon DSP audiences
- Audiences sent directly to DSP for activation
- No downloadable results returned
- Require minimum audience size thresholds
- Use special "_for_audiences" table variants

## Tables Used

**conversions_all_for_audiences**: 
- Contains both ad-exposed and non-ad-exposed conversion events
- Includes all list and registry addition events
- Uses 28-day attribution window for ad exposure
- Tracks all ASINs associated with your campaigns

## Event Types Available

| event_subtype | Description | Use Case |
|---------------|-------------|-----------|
| wishList | General saved items | Year-round remarketing |
| babyRegistry | Baby shower items | New parent targeting |
| weddingRegistry | Wedding gift items | Engaged couple targeting |

## Attribution Windows

- **Default**: 28-day window for conversions_all_for_audiences
- **Alternative**: 14-day window using amazon_attributed_events_* tables
- Choose based on your product consideration cycle

## Important Considerations

1. **Minimum Audience Size**: Audiences typically need at least 1,000 users to be activated
2. **Privacy Protection**: User IDs are hashed and anonymized
3. **Refresh Frequency**: Audiences can be refreshed daily, weekly, or monthly
4. **DSP Integration**: Audiences are automatically available in Amazon DSP after creation""",
                'display_order': 2,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'query_implementation',
                'title': '3. Query Implementation',
                'content_markdown': """## Exploratory Query - Check Audience Size

Before creating an audience, estimate its size to ensure it meets minimum thresholds:

```sql
-- Measurement query to check audience size
SELECT 
    event_subtype,
    COUNT(DISTINCT user_id) as audience_size,
    COUNT(*) as total_events
FROM conversions_all
WHERE 
    user_id IS NOT NULL
    AND event_subtype IN ('wishList', 'babyRegistry', 'weddingRegistry')
    AND event_dt >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY event_subtype
ORDER BY audience_size DESC
```

## Main Audience Creation Query

The primary query creates an audience of all users who added to any list or registry:

```sql
/* Audience Instructional Query: Audience that added to list or registry */
-- Optional update: To filter by ASINs, uncomment and add ASINs below
SELECT
  user_id
FROM
  conversions_all_for_audiences
WHERE
  user_id IS NOT NULL
  AND event_subtype IN ('wishList', 'babyRegistry', 'weddingRegistry')
  /* AND tracked_asin IN ('ASIN1','ASIN2','ASIN3') */
GROUP BY
  user_id
```

## Customization Options

### Filter by Specific List Types

```sql
-- Only wishlist users
AND event_subtype = 'wishList'

-- Only registry users (baby or wedding)
AND event_subtype IN ('babyRegistry', 'weddingRegistry')
```

### Filter by Specific ASINs

```sql
-- Target users who saved specific high-value products
AND tracked_asin IN ('B000XXXXX1', 'B000XXXXX2')
```

### Add Time Constraints

```sql
-- Only recent additions (last 7 days)
AND event_dt >= CURRENT_DATE - INTERVAL '7' DAY
```

### Exclude Recent Purchasers

```sql
-- Add to main query to exclude those who already purchased
AND user_id NOT IN (
    SELECT DISTINCT user_id 
    FROM conversions_all_for_audiences 
    WHERE purchases > 0
    AND event_dt >= CURRENT_DATE - INTERVAL '30' DAY
)
```""",
                'display_order': 3,
                'is_collapsible': True,
                'default_expanded': True
            },
            {
                'guide_id': guide_id,
                'section_id': 'strategic_implementation',
                'title': '4. Strategic Implementation',
                'content_markdown': """## Audience Activation Strategy

### Immediate Activation (0-7 days)
- High urgency messaging
- Limited-time offers
- Stock availability alerts
- Price drop notifications

### Medium-Term Nurturing (7-30 days)
- Product education content
- Customer reviews and testimonials
- Comparison guides
- Bundle offers

### Long-Term Engagement (30+ days)
- Seasonal reminders
- New product launches
- Loyalty program invitations
- Category expansions

## Campaign Segmentation

### By Registry Type

**Wedding Registry**: Target 2-6 months before wedding date
- Focus on gift-givers and the couple
- Highlight popular registry items
- Offer registry completion discounts

**Baby Registry**: Focus on third trimester through first year
- Target expectant parents and gift-givers
- Promote essentials and must-haves
- Bundle complementary products

**Wishlist**: Year-round with seasonal peaks
- General remarketing approach
- Price drop alerts
- Back-in-stock notifications

### Message Personalization

**Wishlist Users**:
- "Still thinking about [Product]?"
- "Your saved item is on sale"
- "Complete your collection"

**Registry Users**:
- "Complete your registry before the big day"
- "Popular registry items from other parents"
- "Registry completion discount available""",
                'display_order': 4,
                'is_collapsible': True,
                'default_expanded': False
            },
            {
                'guide_id': guide_id,
                'section_id': 'performance_optimization',
                'title': '5. Performance Optimization',
                'content_markdown': """## Audience Refresh Strategy

### Refresh Frequency

**Daily Refresh**: For high-velocity products
- Fast-moving consumer goods
- Limited-time offers
- Flash sales and daily deals

**Weekly Refresh**: Standard refresh cycle
- Most product categories
- Balanced freshness vs. processing costs
- Optimal for steady-state campaigns

**Monthly Refresh**: For luxury/considered purchases
- High-value items
- Long consideration cycles
- B2B products

## Success Metrics

### Primary KPIs
- **Conversion Rate**: From list/registry to purchase
- **Time to Conversion**: Days from addition to purchase
- **Average Order Value**: From audience members
- **Registry Completion Rate**: Percentage of registry fulfilled

### Secondary Metrics
- **Audience Growth Rate**: New additions over time
- **Cross-Category Additions**: Products added across categories
- **Repeat List Usage**: Users with multiple list additions
- **Share of Voice**: Your products in category registries

### Performance Benchmarks

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| Conversion Rate | <2% | 2-5% | 5-10% | >10% |
| Time to Convert | >60 days | 30-60 days | 14-30 days | <14 days |
| AOV vs. Baseline | <1x | 1-1.2x | 1.2-1.5x | >1.5x |
| Registry Completion | <20% | 20-40% | 40-60% | >60% |

## Testing Framework

### A/B Testing Opportunities

**Message Testing**
- Urgency levels (high/medium/low)
- Discount vs. non-discount offers
- Feature vs. benefit messaging

**Offer Testing**
- Percentage discounts vs. dollar off
- Free shipping thresholds
- Bundle configurations

**Creative Testing**
- Single product vs. carousel
- Static vs. video creative
- Lifestyle vs. product shots""",
                'display_order': 5,
                'is_collapsible': True,
                'default_expanded': False
            },
            {
                'guide_id': guide_id,
                'section_id': 'advanced_techniques',
                'title': '6. Advanced Techniques',
                'content_markdown': """## Lookalike Audience Creation

### Using List/Registry Users as Seeds

**High-Value Lookalikes**
- Seed with users who completed high-value registries
- Find similar high-intent shoppers
- Expand reach while maintaining quality

**Category Lookalikes**
- Create category-specific seed audiences
- Target users with similar shopping behaviors
- Improve relevance and conversion rates

## Sequential Messaging Strategy

### Journey-Based Campaign Flow

**Day 0-3: Gentle Reminder**
- "We saved your spot"
- Show saved items
- No pressure messaging

**Day 4-7: Social Proof**
- Customer reviews
- "Others also bought"
- Popularity indicators

**Day 8-14: Incentive Introduction**
- Limited-time offer
- Exclusive discount
- Free shipping threshold

**Day 15-30: Alternative Options**
- Similar products
- Bundle suggestions
- Category recommendations

**Day 30+: Re-engagement**
- Price drop alerts
- Back in stock notifications
- New arrival announcements

## Cross-Channel Integration

### Combining Data Signals

**Email + List Data**
- Target email subscribers with list additions
- Higher engagement potential
- Coordinated messaging

**Browse + Registry**
- Users who browsed and added to registry
- Strong purchase intent signals
- Personalized product recommendations

## Machine Learning Applications

### Predictive Scoring

**Purchase Probability**
- Score users based on list behavior
- Prioritize high-probability converters
- Optimize bid strategies

**Lifetime Value Prediction**
- Identify high-value registry creators
- Invest more in quality audiences
- Long-term ROI optimization""",
                'display_order': 6,
                'is_collapsible': True,
                'default_expanded': False
            },
            {
                'guide_id': guide_id,
                'section_id': 'troubleshooting',
                'title': '7. Troubleshooting Guide',
                'content_markdown': """## Common Issues and Solutions

### Issue: Audience Too Small

**Symptoms**
- Audience below 1,000 users
- Cannot activate in DSP
- Limited reach potential

**Solutions**
- Expand time window (30 to 60 days)
- Combine all list types
- Remove ASIN filters
- Include broader product categories
- Consider lookalike expansion

### Issue: Low Conversion Rates

**Symptoms**
- Conversion rate below 2%
- High cost per acquisition
- Poor ROI on campaigns

**Solutions**
- Exclude recent purchasers
- Refine targeting parameters
- Test different messaging approaches
- Adjust frequency caps
- Review creative relevance

### Issue: High Frequency Complaints

**Symptoms**
- User feedback about too many ads
- Increasing opt-outs
- Declining engagement rates

**Solutions**
- Implement stricter frequency caps
- Extend refresh cycles
- Diversify creative rotation
- Add suppression lists
- Use sequential messaging

## Best Practices Checklist

### Pre-Launch
- [ ] Check audience size meets minimums
- [ ] Verify ASIN tracking is active
- [ ] Test query in measurement mode first
- [ ] Document query parameters
- [ ] Set up performance tracking

### Launch Phase
- [ ] Start with broader targeting
- [ ] Monitor initial performance daily
- [ ] Document successful configurations
- [ ] Track audience growth trends
- [ ] Implement A/B testing

### Optimization Phase
- [ ] Refine based on performance data
- [ ] Test one variable at a time
- [ ] Scale successful segments
- [ ] Implement learnings across campaigns
- [ ] Regular performance reviews

## Support Resources

### Documentation
- AMC Audience Query Guide
- DSP Activation Documentation
- Best Practices Library

### Tools
- AMC Query Builder
- Audience Size Estimator
- Performance Dashboard""",
                'display_order': 7,
                'is_collapsible': True,
                'default_expanded': False
            }
        ]
        
        # Insert sections
        for section in sections:
            response = client.table('build_guide_sections').insert(section).execute()
            if response.data:
                logger.info(f"Created section: {section['title']}")
        
        # Create queries
        queries = [
            {
                'guide_id': guide_id,
                'title': 'Check Audience Size by List Type',
                'description': 'Measurement query to check potential audience sizes before creating the actual audience',
                'sql_query': """-- Measurement query to check audience size by list type
SELECT 
    event_subtype,
    COUNT(DISTINCT user_id) as audience_size,
    COUNT(*) as total_events,
    COUNT(DISTINCT tracked_asin) as unique_products
FROM conversions_all
WHERE 
    user_id IS NOT NULL
    AND event_subtype IN ('wishList', 'babyRegistry', 'weddingRegistry')
    AND event_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
GROUP BY event_subtype
ORDER BY audience_size DESC""",
                'parameters_schema': {
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Number of days to look back for list additions'
                    }
                },
                'default_parameters': {
                    'lookback_days': 30
                },
                'display_order': 1,
                'query_type': 'exploratory',
                'interpretation_notes': 'Use this query to understand the size of potential audiences before creating them. Ensure each segment exceeds minimum thresholds.'
            },
            {
                'guide_id': guide_id,
                'title': 'Basic List and Registry Audience',
                'description': 'Create an audience of all users who added items to any list or registry',
                'sql_query': """/* Audience Instructional Query: Audience that added to list or registry */
-- Creates an audience of users who added items to wishlists or registries
SELECT
  user_id
FROM
  conversions_all_for_audiences
WHERE
  user_id IS NOT NULL
  AND event_subtype IN ('wishList', 'babyRegistry', 'weddingRegistry')
GROUP BY
  user_id""",
                'parameters_schema': {},
                'default_parameters': {},
                'display_order': 2,
                'query_type': 'main_analysis',
                'interpretation_notes': 'This creates a broad audience of all list and registry users. Use for general remarketing campaigns.'
            },
            {
                'guide_id': guide_id,
                'title': 'Wishlist-Only Audience',
                'description': 'Target users who specifically added items to their wishlist',
                'sql_query': """/* Audience Query: Wishlist Users Only */
-- Creates an audience of users who added items to wishlists
SELECT
  user_id
FROM
  conversions_all_for_audiences
WHERE
  user_id IS NOT NULL
  AND event_subtype = 'wishList'
  {{asin_filter}}
GROUP BY
  user_id""",
                'parameters_schema': {
                    'asin_filter': {
                        'type': 'string',
                        'default': '',
                        'description': 'Optional ASIN filter (e.g., AND tracked_asin IN (\'ASIN1\', \'ASIN2\'))'
                    }
                },
                'default_parameters': {
                    'asin_filter': ''
                },
                'display_order': 3,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Wishlist users show general purchase intent. Good for year-round remarketing.'
            },
            {
                'guide_id': guide_id,
                'title': 'Registry-Only Audience',
                'description': 'Focus on users who created baby or wedding registries',
                'sql_query': """/* Audience Query: Registry Users (Baby & Wedding) */
-- Creates an audience of users who added items to registries
SELECT
  user_id
FROM
  conversions_all_for_audiences
WHERE
  user_id IS NOT NULL
  AND event_subtype IN ('babyRegistry', 'weddingRegistry')
  {{time_filter}}
GROUP BY
  user_id""",
                'parameters_schema': {
                    'time_filter': {
                        'type': 'string',
                        'default': '',
                        'description': 'Optional time constraint (e.g., AND event_dt >= CURRENT_DATE - INTERVAL \'30\' DAY)'
                    }
                },
                'default_parameters': {
                    'time_filter': ''
                },
                'display_order': 4,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Registry users have specific event-driven needs. Target with time-sensitive messaging.'
            },
            {
                'guide_id': guide_id,
                'title': 'Advanced Audience with Purchase Exclusion',
                'description': 'Create audience excluding users who already purchased',
                'sql_query': """/* Advanced Audience Query: List/Registry Users Without Recent Purchases */
-- Creates an audience excluding those who already purchased
SELECT
  user_id
FROM
  conversions_all_for_audiences
WHERE
  user_id IS NOT NULL
  AND event_subtype IN ({{list_types}})
  AND event_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
  AND user_id NOT IN (
    SELECT DISTINCT user_id 
    FROM conversions_all_for_audiences 
    WHERE purchases > 0
    AND event_dt >= CURRENT_DATE - INTERVAL '{{purchase_lookback}}' DAY
  )
GROUP BY
  user_id""",
                'parameters_schema': {
                    'list_types': {
                        'type': 'string',
                        'default': "'wishList', 'babyRegistry', 'weddingRegistry'",
                        'description': 'Types of lists to include'
                    },
                    'lookback_days': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Days to look back for list additions'
                    },
                    'purchase_lookback': {
                        'type': 'integer',
                        'default': 30,
                        'description': 'Days to look back for purchases to exclude'
                    }
                },
                'default_parameters': {
                    'list_types': "'wishList', 'babyRegistry', 'weddingRegistry'",
                    'lookback_days': 30,
                    'purchase_lookback': 30
                },
                'display_order': 5,
                'query_type': 'main_analysis',
                'interpretation_notes': 'Excludes recent purchasers to focus on users still in consideration phase.'
            }
        ]
        
        # Insert queries
        for query in queries:
            response = client.table('build_guide_queries').insert(query).execute()
            if response.data:
                query_id = response.data[0]['id']
                logger.info(f"Created query: {query['title']}")
                
                # Add example results for key queries
                if query['title'] == 'Check Audience Size by List Type':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Audience Size Check Results',
                        'sample_data': {
                            'rows': [
                                {
                                    'event_subtype': 'wishList',
                                    'audience_size': 45678,
                                    'total_events': 125432,
                                    'unique_products': 892
                                },
                                {
                                    'event_subtype': 'babyRegistry',
                                    'audience_size': 8234,
                                    'total_events': 15678,
                                    'unique_products': 234
                                },
                                {
                                    'event_subtype': 'weddingRegistry',
                                    'audience_size': 3456,
                                    'total_events': 7890,
                                    'unique_products': 156
                                }
                            ]
                        },
                        'interpretation_markdown': """## Audience Size Analysis

This exploratory query reveals:

- **Wishlist**: Largest audience with 45,678 users, indicating broad appeal
- **Baby Registry**: Medium-sized audience of 8,234 expectant parents
- **Wedding Registry**: Smaller but highly engaged audience of 3,456 users

### Key Insights:
1. All segments exceed the 1,000 user minimum for activation
2. Wishlist users show highest engagement (2.7 events per user average)
3. 892 unique products in wishlists suggests diverse product interest

### Recommendations:
- Start with wishlist audience for maximum reach
- Create separate campaigns for registry types due to different use cases
- Consider ASIN-specific audiences for top products""",
                        'insights': [
                            'Wishlist audience is largest with 45,678 users',
                            'All segments exceed 1,000 user minimum for activation',
                            '892 unique products in wishlists suggests diverse interest',
                            'Registry audiences are smaller but more targeted'
                        ],
                        'display_order': 1
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info(f"Created example: {example_data['example_name']}")
                
                elif query['title'] == 'Basic List and Registry Audience':
                    example_data = {
                        'guide_query_id': query_id,
                        'example_name': 'Campaign Performance Metrics',
                        'sample_data': {
                            'rows': [
                                {
                                    'audience_type': 'Wishlist',
                                    'audience_size': 45678,
                                    'impressions': 2345678,
                                    'clicks': 45678,
                                    'conversions': 3456,
                                    'conversion_rate': '7.56%',
                                    'roas': 4.23
                                },
                                {
                                    'audience_type': 'Baby Registry',
                                    'audience_size': 8234,
                                    'impressions': 456789,
                                    'clicks': 12345,
                                    'conversions': 1234,
                                    'conversion_rate': '14.99%',
                                    'roas': 6.78
                                },
                                {
                                    'audience_type': 'Wedding Registry',
                                    'audience_size': 3456,
                                    'impressions': 234567,
                                    'clicks': 5678,
                                    'conversions': 567,
                                    'conversion_rate': '16.41%',
                                    'roas': 7.89
                                }
                            ]
                        },
                        'interpretation_markdown': """## Campaign Performance Analysis

### Performance Highlights:
- **Registry audiences show 2x higher conversion rates** than wishlist audiences
- **ROAS ranges from 4.23x to 7.89x**, exceeding industry benchmarks
- **Wedding registry** has the highest conversion rate at 16.41%

### Strategic Insights:
1. Registry users demonstrate higher purchase intent
2. Smaller, more targeted audiences (registries) outperform larger ones
3. All segments show positive ROAS, validating the strategy

### Optimization Opportunities:
- Increase investment in registry audiences given higher ROAS
- Test premium messaging for high-converting wedding registry segment
- Implement frequency optimization for wishlist audience""",
                        'insights': [
                            'Registry audiences show 2x higher conversion rates',
                            'ROAS ranges from 4.23x to 7.89x across segments',
                            'Wedding registry has highest conversion rate at 16.41%',
                            'All segments profitable with positive ROAS'
                        ],
                        'display_order': 2
                    }
                    
                    example_response = client.table('build_guide_examples').insert(example_data).execute()
                    if example_response.data:
                        logger.info(f"Created example: {example_data['example_name']}")
        
        # Create metrics
        metrics = [
            {
                'guide_id': guide_id,
                'metric_name': 'audience_size',
                'display_name': 'Audience Size',
                'definition': 'Count of unique users in the audience',
                'metric_type': 'metric',
                'display_order': 1
            },
            {
                'guide_id': guide_id,
                'metric_name': 'event_subtype',
                'display_name': 'List/Registry Type',
                'definition': 'Type of list or registry (wishList, babyRegistry, weddingRegistry)',
                'metric_type': 'dimension',
                'display_order': 2
            },
            {
                'guide_id': guide_id,
                'metric_name': 'total_events',
                'display_name': 'Total List Addition Events',
                'definition': 'Total number of items added to lists/registries',
                'metric_type': 'metric',
                'display_order': 3
            },
            {
                'guide_id': guide_id,
                'metric_name': 'unique_products',
                'display_name': 'Unique Products',
                'definition': 'Count of distinct ASINs added to lists/registries',
                'metric_type': 'metric',
                'display_order': 4
            },
            {
                'guide_id': guide_id,
                'metric_name': 'conversion_rate',
                'display_name': 'Conversion Rate',
                'definition': 'Percentage of audience that made a purchase',
                'metric_type': 'metric',
                'display_order': 5
            },
            {
                'guide_id': guide_id,
                'metric_name': 'avg_time_to_purchase',
                'display_name': 'Average Time to Purchase',
                'definition': 'Average days between list addition and purchase',
                'metric_type': 'metric',
                'display_order': 6
            }
        ]
        
        # Insert metrics
        for metric in metrics:
            response = client.table('build_guide_metrics').insert(metric).execute()
            if response.data:
                logger.info(f"Created metric: {metric['display_name']}")
        
        logger.info("Successfully created List and Registry Audience guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create guide: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_list_registry_guide()
    if success:
        print("✅ List and Registry Audience guide created successfully!")
    else:
        print("❌ Failed to create guide. Check logs for details.")
        sys.exit(1)