#!/usr/bin/env python3
"""
Seed script for Audience Overlap Analysis Build Guide
This creates a comprehensive guide for analyzing audience segment overlaps in DSP campaigns
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.build_guide_formatter import create_guide_from_dict
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

# Define the complete guide data
guide_data = {
    'guide': {
        'guide_id': 'guide_audience_overlap_analysis',
        'name': 'Audience Overlap Analysis',
        'category': 'Audience Analysis',
        'short_description': 'Assess which audience segments overlap with your targeted audiences to understand your audience composition and identify expansion opportunities',
        'difficulty_level': 'intermediate',
        'estimated_time_minutes': 45,
        'is_published': True,
        'display_order': 9,
        'tags': [
            'audience-analysis', 
            'segment-overlap', 
            'audience-expansion', 
            'dsp-targeting', 
            'performance-optimization'
        ],
        'prerequisites': [
            'Active DSP campaigns with audience targeting',
            'Multiple audience segments in AMC instance',
            'At least 30 days of campaign data',
            'Understanding of Amazon audience segments'
        ],
        'icon': '👥'
    },
    'sections': [
        {
            'section_id': 'introduction',
            'title': '1. Introduction',
            'display_order': 1,
            'is_collapsible': True,
            'default_expanded': True,
            'content_markdown': """## 1.1 Purpose

This analysis helps assess the audiences that overlapped with your targeted audiences. This will allow you to understand what other audience segments your targeted users belong to. Using these insights, you can better understand your targeted audiences and expand the reach of your campaign by incorporating high-performing overlapped audiences that were not originally targeted.

## 1.2 What You'll Learn

- **Segment Composition**: Which audience segments overlap with your targeted segments
- **Performance Metrics**: Conversion rates and purchase behavior for each overlapped segment
- **Expansion Opportunities**: High-performing segments to add to your campaigns
- **Optimization Insights**: Low-performing segments to potentially exclude
- **Audience Profile**: Complete behavioral and demographic profile of your target audience

## 1.3 Business Applications

### Audience Expansion
Identify high-performing segments that weren't originally targeted but show strong conversion rates. These segments represent immediate opportunities to expand campaign reach while maintaining performance.

### Audience Refinement
Remove or exclude low-performing overlapped segments to improve overall campaign efficiency and ROAS.

### Persona Development
Build comprehensive audience personas by understanding the complete profile of your target audience, including their interests, behaviors, and demographics.

### Budget Optimization
Allocate budget more effectively by focusing on segment combinations that drive the highest conversion rates and purchase values.

### Creative Personalization
Tailor creative messaging and offers based on the overlapped segment characteristics to improve relevance and engagement."""
        },
        {
            'section_id': 'data_query',
            'title': '2. Data Query Instructions',
            'display_order': 2,
            'is_collapsible': True,
            'default_expanded': True,
            'content_markdown': """## 2.1 Data Returned

This query returns segments that overlapped with your targeted segment, along with comprehensive performance metrics:

- **Overlapped segment names** and targeting status (matched/unmatched)
- **Reach metrics**: Unique users reached in each segment
- **Impression metrics**: Total impressions delivered to each segment
- **Conversion metrics**: Users that made purchases and purchase rates
- **Targeting indicator**: Whether the segment was actively targeted or not

## 2.2 Tables Used

### Primary Tables

- **dsp_impressions_by_user_segments**: Contains both targeted and untargeted segments with matching indicators
  - Provides user-level segment membership data
  - Includes behavior_segment_matched flag for targeting status
  
- **amazon_attributed_events_by_conversion_time**: Conversion events with 14-day attribution window
  - Tracks purchase events at the user level
  - Provides conversion timing and attribution data

## 2.3 Two-Part Query Process

### Part 1: Segment Discovery
Identify all available segments in your AMC instance and their characteristics. This exploratory query helps you:
- Understand what segments are available
- See segment sizes and impression volumes
- Identify your targeted segments for deeper analysis

### Part 2: Overlap Analysis
Analyze the overlap between your selected targeted segment and all other segments. This main analysis provides:
- Performance metrics for each overlapped segment
- Purchase rates for optimization decisions
- Comparison between targeted and untargeted segments

## 2.4 Important Considerations

### Data Duplication
- Impressions and conversions are duplicated across segments (users can belong to multiple segments)
- Focus on ratios and rates between segments, not absolute sums
- Use percentage metrics for fair comparison

### Attribution Window
- Wait 14 days after campaign end for complete attribution data
- Purchase events are tracked within 14-day post-impression window
- Consider seasonality when comparing different time periods

### Analysis Scope
- Analyze one targeted segment at a time for clarity
- Run separate analyses for each major targeted segment
- Consider segment size when evaluating performance"""
        },
        {
            'section_id': 'understanding_segments',
            'title': '3. Understanding Audience Segments',
            'display_order': 3,
            'is_collapsible': True,
            'default_expanded': True,
            'content_markdown': """## 3.1 Common Segment Prefixes

Understanding segment naming conventions helps interpret your results:

| Prefix | Segment Type | Description | Example |
|--------|-------------|-------------|---------|
| **IM-** | In-Market | Users actively shopping for specific products | IM - Mattresses, IM - Water bottles |
| **LS-** | Lifestyle | Behavioral and interest-based segments | LS - Heavy streamers, LS - Kindle shoppers |
| **Demo-** | Demographic | Age, gender, income demographics | Demo - Female, Demo - Age 25-35 |
| **DLX** | DataLogix (3P) | Third-party Oracle Data Cloud audiences | DLX - New parents |
| **LAL** | Lookalike | Similar audience modeling | LAL - Top customers |
| **Genre** | Streaming Preference | Content consumption patterns | Genre - Viewers of Travel TV Content |
| **ISP** | Internet Provider | Connection type segments | ISP - Comcast, ISP - Verizon |
| **AM-** | Amazon Marketing | Amazon-specific behavioral segments | AM - Prime members |
| **B2B-** | Business | Company and industry targeting | B2B - IT Decision Makers |

## 3.2 Segment Matching Indicator

The `behavior_segment_matched` field is critical for understanding overlap:

### behavior_segment_matched = 1
- **Meaning**: This segment was actively targeted by your campaign
- **Use case**: Understand performance of your targeted segments
- **Action**: Evaluate if the segment is meeting performance goals

### behavior_segment_matched = 0
- **Meaning**: Users belong to this segment but it wasn't targeted
- **Use case**: Discover expansion opportunities
- **Action**: Consider adding high-performing untargeted segments

### Filtering Strategy
- Remove filter to see both targeted and untargeted segments
- Filter to matched=0 to focus on expansion opportunities
- Filter to matched=1 to analyze targeted segment performance

## 3.3 Segment Categories and Use Cases

### Purchase Intent Segments (IM-)
Best for: Lower-funnel campaigns, direct response objectives
- High purchase intent
- Shorter consideration cycles
- Higher conversion rates typically

### Lifestyle Segments (LS-)
Best for: Brand awareness, lifestyle alignment
- Broader reach potential
- Good for cross-selling
- Lifestyle-based creative messaging

### Demographic Segments (Demo-)
Best for: Broad targeting, brand campaigns
- Stable audience sizes
- Predictable behavior patterns
- Good for layering with other segments"""
        },
        {
            'section_id': 'data_interpretation',
            'title': '4. Data Interpretation',
            'display_order': 4,
            'is_collapsible': True,
            'default_expanded': True,
            'content_markdown': """## 4.1 Example Query Results

### Sample Overlap Analysis Output

| targeted_segment | target_segment_size | behavior_segment_name | behavior_segment_matched | impression_reach | impressions | users_that_purchased | user_purchase_rate |
|-----------------|---------------------|----------------------|-------------------------|------------------|-------------|---------------------|-------------------|
| LS - Fashionistas | 124,729 | IM - Green Home and Garden | 0 | 96,320 | 219,064 | 778 | 0.81% |
| LS - Fashionistas | 124,729 | IM - Home & Kitchen | 0 | 96,328 | 218,987 | 699 | 0.73% |
| LS - Fashionistas | 124,729 | LS - Foodies | 0 | 84,295 | 190,495 | 528 | 0.63% |
| LS - Fashionistas | 124,729 | Demo - Income 100k-150k | 0 | 109,046 | 255,596 | 472 | 0.43% |
| LS - Fashionistas | 124,729 | LS - Bargain Hunters | 0 | 104,412 | 241,663 | 310 | 0.30% |
| LS - Fashionistas | 124,729 | LS - Fashionistas | 1 | 124,729 | 298,456 | 623 | 0.50% |

## 4.2 Key Insights from Example

### High-Performance Overlaps
The untargeted segments showing strongest performance:
- **IM - Green Home and Garden**: 0.81% purchase rate (62% higher than targeted segment)
- **IM - Home & Kitchen**: 0.73% purchase rate (46% higher than targeted segment)
- **LS - Foodies**: 0.63% purchase rate (26% higher than targeted segment)

### Audience Profile Insights
Your Fashionistas audience also shows:
- **Strong home interest**: High overlap with home and garden segments
- **Premium demographics**: Significant portion in $100k-150k income range
- **Food enthusiasm**: Notable overlap with Foodies segment
- **Value consciousness**: Overlap with Bargain Hunters (though lower converting)

### Performance Patterns
- **In-Market segments** (IM-) show highest purchase rates
- **Lifestyle segments** (LS-) show moderate performance
- **Demographic segments** show lowest conversion rates but highest reach

## 4.3 Strategic Recommendations

### Immediate Expansion Opportunities
1. **Add IM - Green Home and Garden** 
   - 0.81% purchase rate vs 0.50% baseline
   - Clear purchase intent signal
   - Immediate ROAS improvement potential

2. **Add IM - Home & Kitchen**
   - 0.73% purchase rate
   - Strong category alignment
   - High impression volume available

3. **Test LS - Foodies**
   - 0.63% purchase rate
   - Lifestyle alignment opportunity
   - Good for cross-selling food/kitchen products

### Optimization Actions

#### Bid Adjustments
- Increase bids +20-30% for high-performing overlaps
- Maintain current bids for baseline performance
- Decrease bids -20% for underperformers

#### Creative Personalization
- Develop home-focused creative for home segment overlaps
- Create food/lifestyle messaging for Foodie overlap
- Test value messaging for Bargain Hunter segment

#### Budget Allocation
- Shift 30% of budget to high-performing overlapped segments
- Maintain 50% on core targeted segment
- Reserve 20% for testing new segments"""
        },
        {
            'section_id': 'implementation',
            'title': '5. Implementation Strategy',
            'display_order': 5,
            'is_collapsible': True,
            'default_expanded': True,
            'content_markdown': """## 5.1 Segment Selection Process

### Step-by-Step Implementation

1. **Run Part 1 Query**: Identify all available segments in your AMC instance
2. **Select Primary Segment**: Choose your main targeted segment for analysis
3. **Execute Part 2 Query**: Run overlap analysis with selected segment
4. **Analyze Results**: Review performance metrics and overlap patterns
5. **Identify Opportunities**: Select segments for expansion and exclusion
6. **Implement Changes**: Update DSP campaigns with new targeting

### Decision Framework

```
For each overlapped segment:
├── If purchase_rate > targeted_segment_rate * 1.2
│   └── ADD to campaign (high performer)
├── If purchase_rate between 0.8x and 1.2x of targeted
│   └── TEST in separate campaign
└── If purchase_rate < targeted_segment_rate * 0.5
    └── EXCLUDE from targeting
```

## 5.2 Campaign Optimization Workflow

### Phase 1: Analysis (Week 1)
- Run overlap analysis for all targeted segments
- Document performance baselines
- Identify top 10 expansion opportunities
- Calculate potential reach increase

### Phase 2: Testing (Weeks 2-3)
- Create test campaigns with top 3-5 overlapped segments
- Set conservative budgets (10-20% of main campaign)
- Maintain same creative and landing pages
- Monitor daily performance

### Phase 3: Scaling (Week 4+)
- Scale budget to proven high-performers
- Expand to additional overlapped segments
- Implement bid adjustments based on performance
- Develop segment-specific creative

### Phase 4: Refinement (Ongoing)
- Monthly overlap analysis refresh
- Exclude consistently underperforming segments
- Test new segment combinations
- Optimize creative messaging

## 5.3 Performance Thresholds

### Segment Addition Criteria
**Immediate Add**: User purchase rate > targeted segment baseline × 1.2
**Test Campaign**: User purchase rate within 20% of baseline
**Consider for Niche**: High purchase rate but low reach (<10k users)

### Segment Exclusion Criteria
**Immediate Exclude**: User purchase rate < 50% of baseline
**Monitor Closely**: User purchase rate 50-80% of baseline
**Frequency Cap**: High impressions but low conversion

### Success Metrics
- **Primary KPI**: Incremental ROAS from added segments
- **Secondary KPIs**: 
  - Reach expansion percentage
  - Cost per acquisition change
  - Overall campaign conversion rate
  
## 5.4 Advanced Strategies

### Segment Layering
Combine multiple high-performing overlaps:
- Target: LS - Fashionistas AND IM - Home & Kitchen
- Expected: Higher precision, potentially higher CPMs
- Monitor: Reach limitations

### Lookalike Modeling
Create lookalikes from high-converting overlap combinations:
- Seed: Users in both targeted and high-performing overlaps
- Size: Start with 1-3% similarity
- Expand: Gradually increase to 5-10% if performing

### Sequential Messaging
Develop creative sequences based on overlap insights:
1. Awareness: Broad lifestyle messaging
2. Consideration: Category-specific benefits
3. Conversion: Product-focused with urgency"""
        },
        {
            'section_id': 'troubleshooting',
            'title': '6. Troubleshooting & Best Practices',
            'display_order': 6,
            'is_collapsible': True,
            'default_expanded': True,
            'content_markdown': """## 6.1 Common Issues and Solutions

### No Overlap Data Returned
**Issue**: Query returns empty results
**Solutions**:
- Verify targeted segment name exactly matches AMC data
- Check date range includes active campaign periods
- Ensure sufficient impression volume (minimum 10,000)
- Confirm segment_matched filter isn't too restrictive

### Low Purchase Rates Across All Segments
**Issue**: All segments show <0.1% purchase rates
**Solutions**:
- Extend attribution window to 14 or 28 days
- Verify conversion tracking is properly implemented
- Check if analysis period includes full purchase cycle
- Consider seasonal factors affecting purchase behavior

### Extremely High Overlap Percentages
**Issue**: 90%+ users in multiple segments
**Solutions**:
- This is normal for broad segments (e.g., Demographics)
- Focus on performance differences, not overlap size
- Consider using more specific segments for targeting

## 6.2 Best Practices

### Analysis Frequency
- **Monthly**: Full overlap analysis for optimization
- **Weekly**: Monitor new segment performance
- **Daily**: Track test campaign metrics
- **Quarterly**: Strategic segment planning

### Segment Testing Protocol
1. Never test more than 5 new segments simultaneously
2. Maintain control group with original targeting
3. Run tests for minimum 2 weeks for significance
4. Document learnings for future campaigns

### Data Quality Checks
- Verify sum of impressions aligns with campaign totals
- Check for data freshness (14-day attribution lag)
- Validate segment sizes match platform reporting
- Cross-reference conversion data with DSP reports

## 6.3 Optimization Tips

### For Better Performance
- Focus on segments with 50k+ available users
- Layer behavioral with demographic segments
- Test different attribution windows
- Combine with contextual targeting

### For Scale
- Start with broader lifestyle segments
- Gradually add in-market segments
- Use OR logic instead of AND for reach
- Consider day-parting for efficiency

### For Efficiency
- Exclude lowest 20% performing segments
- Set frequency caps by segment
- Adjust bids based on segment value
- Use negative targeting strategically

## 6.4 Advanced Considerations

### Privacy and Compliance
- Minimum audience size requirements (typically 1000+)
- Cannot identify individual users
- Aggregate reporting only
- Respect frequency caps and opt-outs

### Cross-Campaign Learning
- Apply learnings across similar products
- Build segment knowledge base
- Share insights across teams
- Document seasonal patterns

### Integration with Other Analyses
- Combine with frequency analysis for optimization
- Layer with creative performance data
- Integrate with path to conversion insights
- Align with brand lift studies"""
        }
    ],
    'queries': [
        {
            'title': 'Part 1: Segment Discovery',
            'description': 'Explore available audience segments in your AMC instance to identify targeted segments and understand the data landscape',
            'query_type': 'exploratory',
            'display_order': 1,
            'sql_query': """-- Part 1: Discover Available Segments and Targeting Status
-- This query helps identify which segments are available and which were targeted

WITH segment_summary AS (
    SELECT 
        behavior_segment_name,
        behavior_segment_matched,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(*) as total_impressions,
        MIN(impression_dt) as first_impression,
        MAX(impression_dt) as last_impression,
        COUNT(DISTINCT campaign) as campaigns_count,
        COUNT(DISTINCT advertiser) as advertisers_count
    FROM dsp_impressions_by_user_segments
    WHERE 
        impression_dt >= '{{start_date}}'
        AND impression_dt <= '{{end_date}}'
        AND behavior_segment_name IS NOT NULL
    GROUP BY 
        behavior_segment_name,
        behavior_segment_matched
)
SELECT 
    behavior_segment_name,
    CASE 
        WHEN behavior_segment_matched = 1 THEN 'Targeted'
        ELSE 'Not Targeted'
    END as targeting_status,
    unique_users,
    total_impressions,
    ROUND(CAST(total_impressions AS DOUBLE) / CAST(unique_users AS DOUBLE), 2) as avg_frequency,
    campaigns_count,
    first_impression,
    last_impression,
    DATEDIFF('day', first_impression, last_impression) + 1 as active_days
FROM segment_summary
ORDER BY 
    behavior_segment_matched DESC,
    unique_users DESC
LIMIT 500""",
            'parameters_schema': {
                'start_date': {
                    'type': 'string',
                    'description': 'Start date for analysis period (YYYY-MM-DD)',
                    'required': True,
                    'default': '2024-01-01'
                },
                'end_date': {
                    'type': 'string',
                    'description': 'End date for analysis period (YYYY-MM-DD)',
                    'required': True,
                    'default': '2024-01-31'
                }
            },
            'interpretation_notes': 'Review the segments marked as "Targeted" - these are your campaign\'s targeted segments. Note the unique_users count for each segment to understand reach potential. Use the behavior_segment_name exactly as shown when running Part 2.'
        },
        {
            'title': 'Part 2: Audience Overlap Analysis',
            'description': 'Analyze overlap between your targeted segment and all other segments, with performance metrics',
            'query_type': 'main_analysis',
            'display_order': 2,
            'sql_query': """-- Part 2: Analyze Audience Overlap and Performance
-- Evaluate which segments overlap with your targeted audience and their performance

WITH targeted_segment_base AS (
    -- Define the targeted segment being analyzed
    SELECT 
        '{{targeted_segment_name}}' as targeted_segment,
        COUNT(DISTINCT user_id) as target_segment_size
    FROM dsp_impressions_by_user_segments
    WHERE 
        behavior_segment_name = '{{targeted_segment_name}}'
        AND behavior_segment_matched = 1
        AND impression_dt >= '{{start_date}}'
        AND impression_dt <= '{{end_date}}'
),
overlapped_impressions AS (
    -- Get all segments for users who were in the targeted segment
    SELECT 
        dis1.user_id,
        dis2.behavior_segment_name,
        dis2.behavior_segment_matched,
        COUNT(dis2.*) as user_impressions
    FROM dsp_impressions_by_user_segments dis1
    INNER JOIN dsp_impressions_by_user_segments dis2
        ON dis1.user_id = dis2.user_id
        AND dis2.impression_dt >= '{{start_date}}'
        AND dis2.impression_dt <= '{{end_date}}'
    WHERE 
        dis1.behavior_segment_name = '{{targeted_segment_name}}'
        AND dis1.behavior_segment_matched = 1
        AND dis1.impression_dt >= '{{start_date}}'
        AND dis1.impression_dt <= '{{end_date}}'
    GROUP BY 
        dis1.user_id,
        dis2.behavior_segment_name,
        dis2.behavior_segment_matched
),
segment_performance AS (
    -- Calculate impression metrics for each overlapped segment
    SELECT 
        behavior_segment_name,
        behavior_segment_matched,
        COUNT(DISTINCT user_id) as impression_reach,
        SUM(user_impressions) as impressions
    FROM overlapped_impressions
    GROUP BY 
        behavior_segment_name,
        behavior_segment_matched
),
purchase_activity AS (
    -- Track purchases by users in overlapped segments
    SELECT 
        oi.behavior_segment_name,
        oi.behavior_segment_matched,
        COUNT(DISTINCT aae.user_id) as users_that_purchased,
        COUNT(aae.conversion_event) as total_purchases
    FROM overlapped_impressions oi
    INNER JOIN amazon_attributed_events_by_conversion_time aae
        ON oi.user_id = aae.user_id
        AND aae.conversion_dt >= '{{start_date}}'
        AND aae.conversion_dt <= (CAST('{{end_date}}' AS DATE) + INTERVAL '{{attribution_days}}' DAY)
    WHERE 
        aae.purchase_flag = 1
    GROUP BY 
        oi.behavior_segment_name,
        oi.behavior_segment_matched
)
-- Combine all metrics for final output
SELECT 
    tsb.targeted_segment,
    tsb.target_segment_size,
    sp.behavior_segment_name,
    CASE 
        WHEN sp.behavior_segment_matched = 1 THEN 'Yes'
        ELSE 'No'
    END as was_targeted,
    sp.impression_reach,
    sp.impressions,
    COALESCE(pa.users_that_purchased, 0) as users_that_purchased,
    COALESCE(pa.total_purchases, 0) as total_purchases,
    ROUND(
        CAST(COALESCE(pa.users_that_purchased, 0) AS DOUBLE) / 
        CAST(sp.impression_reach AS DOUBLE) * 100, 
        2
    ) as user_purchase_rate_pct,
    ROUND(
        CAST(sp.impression_reach AS DOUBLE) / 
        CAST(tsb.target_segment_size AS DOUBLE) * 100, 
        2
    ) as overlap_percentage
FROM targeted_segment_base tsb
CROSS JOIN segment_performance sp
LEFT JOIN purchase_activity pa
    ON sp.behavior_segment_name = pa.behavior_segment_name
    AND sp.behavior_segment_matched = pa.behavior_segment_matched
WHERE 
    sp.impression_reach >= {{min_reach_threshold}}
ORDER BY 
    COALESCE(pa.users_that_purchased, 0) DESC,
    sp.impression_reach DESC""",
            'parameters_schema': {
                'targeted_segment_name': {
                    'type': 'string',
                    'description': 'Exact name of the targeted segment to analyze (from Part 1)',
                    'required': True,
                    'example': 'LS - Fashionistas'
                },
                'start_date': {
                    'type': 'string',
                    'description': 'Start date for analysis period (YYYY-MM-DD)',
                    'required': True,
                    'default': '2024-01-01'
                },
                'end_date': {
                    'type': 'string',
                    'description': 'End date for analysis period (YYYY-MM-DD)',
                    'required': True,
                    'default': '2024-01-31'
                },
                'attribution_days': {
                    'type': 'integer',
                    'description': 'Attribution window in days after impression',
                    'required': False,
                    'default': 14
                },
                'min_reach_threshold': {
                    'type': 'integer',
                    'description': 'Minimum users reached to include segment',
                    'required': False,
                    'default': 100
                }
            },
            'interpretation_notes': 'Focus on segments where was_targeted = "No" with high user_purchase_rate_pct - these are expansion opportunities. Compare purchase rates to your targeted segment baseline to identify which segments to add or exclude.'
        }
    ],
    'examples': [
        {
            'query_index': 1,  # Links to Part 2 query
            'example_name': 'Fashion Campaign Overlap Analysis',
            'sample_data': {
                'rows': [
                    {
                        'targeted_segment': 'LS - Fashionistas',
                        'target_segment_size': 124729,
                        'behavior_segment_name': 'IM - Green Home and Garden',
                        'was_targeted': 'No',
                        'impression_reach': 96320,
                        'impressions': 219064,
                        'users_that_purchased': 778,
                        'total_purchases': 892,
                        'user_purchase_rate_pct': 0.81,
                        'overlap_percentage': 77.22
                    },
                    {
                        'targeted_segment': 'LS - Fashionistas',
                        'target_segment_size': 124729,
                        'behavior_segment_name': 'IM - Home & Kitchen',
                        'was_targeted': 'No',
                        'impression_reach': 96328,
                        'impressions': 218987,
                        'users_that_purchased': 699,
                        'total_purchases': 824,
                        'user_purchase_rate_pct': 0.73,
                        'overlap_percentage': 77.23
                    },
                    {
                        'targeted_segment': 'LS - Fashionistas',
                        'target_segment_size': 124729,
                        'behavior_segment_name': 'LS - Foodies',
                        'was_targeted': 'No',
                        'impression_reach': 84295,
                        'impressions': 190495,
                        'users_that_purchased': 528,
                        'total_purchases': 612,
                        'user_purchase_rate_pct': 0.63,
                        'overlap_percentage': 67.57
                    },
                    {
                        'targeted_segment': 'LS - Fashionistas',
                        'target_segment_size': 124729,
                        'behavior_segment_name': 'LS - Fashionistas',
                        'was_targeted': 'Yes',
                        'impression_reach': 124729,
                        'impressions': 298456,
                        'users_that_purchased': 623,
                        'total_purchases': 751,
                        'user_purchase_rate_pct': 0.50,
                        'overlap_percentage': 100.00
                    },
                    {
                        'targeted_segment': 'LS - Fashionistas',
                        'target_segment_size': 124729,
                        'behavior_segment_name': 'Demo - Income 100k-150k',
                        'was_targeted': 'No',
                        'impression_reach': 109046,
                        'impressions': 255596,
                        'users_that_purchased': 472,
                        'total_purchases': 531,
                        'user_purchase_rate_pct': 0.43,
                        'overlap_percentage': 87.43
                    },
                    {
                        'targeted_segment': 'LS - Fashionistas',
                        'target_segment_size': 124729,
                        'behavior_segment_name': 'LS - Bargain Hunters',
                        'was_targeted': 'No',
                        'impression_reach': 104412,
                        'impressions': 241663,
                        'users_that_purchased': 310,
                        'total_purchases': 342,
                        'user_purchase_rate_pct': 0.30,
                        'overlap_percentage': 83.71
                    }
                ]
            },
            'interpretation_markdown': """## Analysis Results

### Performance Summary
Your targeted segment **LS - Fashionistas** achieved a **0.50% purchase rate** baseline. Several untargeted segments show significantly higher performance:

### 🎯 High-Priority Expansion Opportunities

**1. IM - Green Home and Garden** (0.81% purchase rate)
- **62% higher performance** than targeted segment
- Strong purchase intent signal for home products
- Immediate expansion opportunity with 96k users overlap

**2. IM - Home & Kitchen** (0.73% purchase rate)  
- **46% higher performance** than targeted segment
- Clear category affinity with fashion audience
- Natural cross-sell opportunity

**3. LS - Foodies** (0.63% purchase rate)
- **26% higher performance** than targeted segment
- Lifestyle alignment with fashion interests
- Good for premium product positioning

### 📊 Audience Composition Insights

Your Fashionistas audience profile reveals:
- **77%** overlap with home interest segments (unexpected but valuable)
- **87%** fall into $100k-150k income bracket (premium demographic)
- **84%** are value-conscious (Bargain Hunters overlap)

### ⚡ Recommended Actions

**Immediate (Week 1)**
1. Add IM - Green Home and Garden to existing campaign
2. Increase bid modifier +25% for this segment
3. Monitor daily performance

**Testing Phase (Week 2-3)**
1. Create test campaign with IM - Home & Kitchen
2. Develop home-lifestyle creative variants
3. Set 20% of main campaign budget for test

**Optimization (Week 4+)**
1. Exclude LS - Bargain Hunters (40% below baseline)
2. Create lookalike from top 3 performing segments
3. Develop integrated fashion + home messaging

### 💡 Strategic Insights

The strong performance of home-related segments suggests your fashion audience values lifestyle and home aesthetics. Consider:
- Partnering with home décor brands
- Featuring lifestyle photography in creative
- Highlighting versatility and everyday use cases"""
        }
    ],
    'metrics': [
        {
            'metric_name': 'targeted_segment',
            'display_name': 'Targeted Segment',
            'definition': 'The primary audience segment that was actively targeted in your DSP campaign',
            'metric_type': 'dimension',
            'display_order': 1
        },
        {
            'metric_name': 'target_segment_size',
            'display_name': 'Target Segment Size',
            'definition': 'Total number of unique users in the targeted segment who received impressions',
            'metric_type': 'metric',
            'display_order': 2
        },
        {
            'metric_name': 'behavior_segment_name',
            'display_name': 'Overlapped Segment',
            'definition': 'Name of the audience segment that overlaps with your targeted segment',
            'metric_type': 'dimension',
            'display_order': 3
        },
        {
            'metric_name': 'behavior_segment_matched',
            'display_name': 'Targeting Status',
            'definition': 'Indicates whether the segment was actively targeted (1) or not targeted (0) in the campaign',
            'metric_type': 'dimension',
            'display_order': 4
        },
        {
            'metric_name': 'impression_reach',
            'display_name': 'Impression Reach',
            'definition': 'Number of unique users in the overlapped segment who received impressions',
            'metric_type': 'metric',
            'display_order': 5
        },
        {
            'metric_name': 'impressions',
            'display_name': 'Total Impressions',
            'definition': 'Total number of impressions delivered to users in the overlapped segment',
            'metric_type': 'metric',
            'display_order': 6
        },
        {
            'metric_name': 'users_that_purchased',
            'display_name': 'Users That Purchased',
            'definition': 'Number of unique users in the overlapped segment who made a purchase within the attribution window',
            'metric_type': 'metric',
            'display_order': 7
        },
        {
            'metric_name': 'total_purchases',
            'display_name': 'Total Purchases',
            'definition': 'Total number of purchase events from users in the overlapped segment',
            'metric_type': 'metric',
            'display_order': 8
        },
        {
            'metric_name': 'user_purchase_rate_pct',
            'display_name': 'User Purchase Rate %',
            'definition': 'Percentage of reached users in the segment who made a purchase (users_that_purchased / impression_reach × 100)',
            'metric_type': 'metric',
            'display_order': 9
        },
        {
            'metric_name': 'overlap_percentage',
            'display_name': 'Overlap %',
            'definition': 'Percentage of the targeted segment that also belongs to this overlapped segment',
            'metric_type': 'metric',
            'display_order': 10
        }
    ]
}

def main():
    """Execute the guide creation"""
    success = create_guide_from_dict(guide_data)
    if success:
        logger.info("✅ Successfully created Audience Overlap Analysis guide!")
    else:
        logger.error("❌ Failed to create guide")
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)