#!/usr/bin/env python3
"""
Seed script for "Audience based on sponsored ads keywords" build guide
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.build_guide_formatter import create_guide_from_dict

# Define the complete build guide
guide_data = {
    "guide": {
        "guide_id": "guide_audience_sponsored_ads_keywords",
        "name": "Audience based on sponsored ads keywords",
        "category": "Audience Building",
        "short_description": "Learn how to build targeted audiences based on keywords from Sponsored Ads campaigns, enabling you to reach users who searched for specific terms but haven't yet converted.",
        "difficulty_level": "intermediate",
        "estimated_time_minutes": 45,
        "tags": ["audience", "sponsored-ads", "keywords", "dsp", "remarketing"],
        "prerequisites": [
            "Active Sponsored Brands or Sponsored Products campaigns with keyword targeting",
            "Access to Amazon DSP for audience activation",
            "Basic understanding of SQL and regular expressions"
        ],
        "is_published": True,
        "display_order": 40
    },
    "sections": [
        {
            "section_id": "audience_query_instructions",
            "title": "Audience query instructions",
            "display_order": 1,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## About rule-based audience queries

Unlike standard AMC queries, AMC Audience queries do not return visible results that you can download. Instead, the audience defined by the query is pushed directly to Amazon DSP. AMC rule-based audience queries require selecting a set of user_id values to create the Amazon DSP audience.

### Tables used

Note: AMC rule-based queries use a unique set of tables that contain the `_for_audiences` suffix in the names.

**Keywords and search terms** are available as dimensions for traffic events in the table `sponsored_ads_traffic_for_audiences`. Both dimensions are provided for all impression events, including impressions from users who clicked and did not click the sponsored ad. AMC does not include the set of keywords and search terms from events that did not trigger an impression on one of the sponsored ads campaigns in the instance.

**Conversion events** are included in `conversions_for_audiences`.

### Requirements

To use this Instructional Query (IQ), advertisers who sell products on Amazon must invest in Sponsored Brands or Sponsored Products campaigns and use keyword targeting."""
        },
        {
            "section_id": "exploratory_analysis",
            "title": "Exploratory Analysis",
            "display_order": 2,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Identifying keyword opportunities

The first step in the process of building an audience based on keywords is to identify high traffic keywords that may be predictive of product interest. The IQ **How to query Sponsored Ads Keywords** provides an introduction to keyword analysis.

### Key considerations for keyword selection:

1. **Volume**: Keywords should have sufficient search volume to create meaningful audiences
2. **Relevance**: Keywords should be closely related to your products and brand
3. **Intent**: Focus on keywords that indicate purchase intent
4. **Competition**: Consider keywords where you have room to improve market share

### Using exploratory queries:

Before building your audience, run exploratory queries to:
- Identify top-performing keywords by impressions and clicks
- Analyze conversion rates for different keyword groups
- Understand seasonal patterns in keyword searches
- Compare brand vs. non-brand keyword performance"""
        },
        {
            "section_id": "single_keyword_audience",
            "title": "Single Keyword Audience",
            "display_order": 3,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Building a single keyword audience

After you have used an exploratory query to identify keyword opportunities, you can craft an audience of consumers that have used that keyword or related keywords.

The most simple version of this query uses `sponsored_ads_traffic_for_audiences` to select an audience that has searched for a specific keyword. These queries rely on the combination of SQL and regular expression:

```sql
SIMILAR TO '(?i)keyword'
```

### Regular expression components:

- `SIMILAR TO`: SQL pattern matching operator
- `(?i)`: Makes the pattern case-insensitive
- `keyword`: Your target keyword

The SIMILAR TO phrase will match the exact keyword you have included, while the addition of the `(?i)` at the beginning of the keyword allows it to match even if the case of the keyword is changed. As the AMC documentation notes, you could adjust these regular expressions to make them more flexible as appropriate.

### Extending to multiple keywords:

If the audience is small, or you want to select one keyword from multiple keywords, you can use the OR operator combined with the SIMILAR TO clause to extend your query:

```sql
AND (customer_search_term SIMILAR TO '(?i)keyword'
    OR customer_search_term SIMILAR TO '(?i)keyword2'
    OR customer_search_term SIMILAR TO '(?i)keyword3'
)
```"""
        },
        {
            "section_id": "searched_not_purchased",
            "title": "Searched but Did Not Purchase",
            "display_order": 4,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Advanced audience: Searched but did not purchase

While the initial query illustrates how to create an audience of people that searched a keyword, a more effective audience might exclude the consumers that already purchased to focus on most likely to purchase consumers. 

### Query logic:

1. **Identify searchers**: Find users who searched for your target keywords
2. **Identify purchasers**: Find users who made purchases of specific ASINs
3. **Exclude converters**: Remove users who purchased after searching
4. **Result**: Audience of users with demonstrated interest but no conversion

### Implementation approach:

We can add to the query an additional set of parameters to acquire customers that placed orders and then left. Join those two audiences (searched a keyword and placed an order and then left) together to eliminate from the search audience people that completed their order process. This leaves us with an audience that searched but did not complete the purchase process.

### ASIN filtering considerations:

This query includes an ASIN filter. If your ASINs are undifferentiated, or you have very few, you could choose to remove this constraint.

### Time-based logic:

The query compares the most recent search date (`traffic_dt_max`) with the most recent purchase date (`conv_dt_max`) to ensure we're only targeting users who either:
- Searched more recently than they purchased
- Never purchased at all"""
        },
        {
            "section_id": "best_practices",
            "title": "Best Practices and Tips",
            "display_order": 5,
            "is_collapsible": True,
            "default_expanded": True,
            "content_markdown": """## Best practices for keyword-based audiences

### 1. Keyword Selection Strategy

- **Start with high-volume, high-relevance keywords**: Focus on keywords with proven search volume
- **Use exploratory queries to validate keyword volume**: Test audience sizes before deployment
- **Consider keyword variations and common misspellings**: Capture all relevant search variations
- **Group semantically related keywords**: Combine similar intent keywords for larger audiences

### 2. Regular Expression Tips

- **Use `(?i)` for case-insensitive matching**: Ensures you capture all case variations
- **Consider using `SIMILAR TO '(?i)%keyword%'` for partial matches**: Captures broader variations
- **Test regex patterns with small audiences first**: Validate pattern accuracy before scaling
- **Document your regex patterns**: Maintain clear documentation for future reference

### 3. Audience Size Optimization

- **Minimum audience size is typically 1000 users**: Ensure audiences meet DSP minimum requirements
- **Combine related keywords to increase audience size**: Build larger, more actionable audiences
- **Balance specificity with reach**: Find the right balance for your campaign goals
- **Monitor audience refresh rates**: Ensure audiences remain fresh and relevant

### 4. Performance Considerations

- **Filter by ad_product_type to improve query performance**: Reduce unnecessary data processing
- **Use date ranges to focus on recent searchers**: Improve relevance and reduce processing time
- **Consider seasonality in keyword searches**: Adjust lookback windows based on product cycles
- **Implement incremental refresh strategies**: Update audiences efficiently

### 5. Advanced Segmentation

- **Exclude recent purchasers for remarketing efficiency**: Focus budget on non-converters
- **Layer on additional behavioral signals**: Combine with browsing or engagement data
- **Consider search recency for audience freshness**: Weight recent searches more heavily
- **Create tiered audiences based on engagement levels**: Different strategies for different engagement levels"""
        }
    ],
    "queries": [
        {
            "title": "Exploratory: Keyword Volume Analysis",
            "description": "Analyze keyword search volume to identify high-opportunity keywords for audience building",
            "sql_query": """/* Exploratory Query: Analyze keyword volume and performance */
SELECT
  customer_search_term,
  ad_product_type,
  COUNT(DISTINCT user_id) as unique_searchers,
  COUNT(*) as total_impressions,
  SUM(clicks) as total_clicks,
  ROUND(SUM(clicks) * 1.0 / NULLIF(COUNT(*), 0), 4) as ctr
FROM
  sponsored_ads_traffic
WHERE
  event_dt >= CURRENT_DATE - INTERVAL '{{lookback_days}}' DAY
  AND ad_product_type IN ({{ad_types}})
  AND customer_search_term IS NOT NULL
GROUP BY
  customer_search_term,
  ad_product_type
HAVING
  COUNT(DISTINCT user_id) >= {{min_searchers}}
ORDER BY
  unique_searchers DESC
LIMIT {{limit}}""",
            "parameters_schema": {
                "lookback_days": {
                    "type": "integer",
                    "default": 30,
                    "description": "Number of days to look back"
                },
                "ad_types": {
                    "type": "array",
                    "default": ["'sponsored_brands'", "'sponsored_products'"],
                    "description": "Types of sponsored ads to include"
                },
                "min_searchers": {
                    "type": "integer",
                    "default": 100,
                    "description": "Minimum number of unique searchers"
                },
                "limit": {
                    "type": "integer",
                    "default": 100,
                    "description": "Number of keywords to return"
                }
            },
            "display_order": 1,
            "query_type": "exploratory"
        },
        {
            "title": "Single Keyword Audience",
            "description": "Create an audience based on a single keyword search",
            "sql_query": """/* Audience Instructional Query: Create an audience based on Sponsored Ads keywords */
SELECT
  user_id
FROM
  sponsored_ads_traffic_for_audiences
WHERE
  /* Optional update: Delete 'sponsored_brands' or 'sponsored_products' if you are focusing on only one */
  ad_product_type IN ('sponsored_brands', 'sponsored_products')
  /* Update: Replace keyword with the customer_search_term you wish to reach */
  AND (customer_search_term SIMILAR TO '(?i){{keyword}}')""",
            "parameters_schema": {
                "keyword": {
                    "type": "string",
                    "default": "wireless headphones",
                    "description": "The keyword to target for audience creation"
                }
            },
            "display_order": 2,
            "query_type": "main_analysis"
        },
        {
            "title": "Multiple Keywords Audience",
            "description": "Create an audience based on multiple related keywords",
            "sql_query": """/* Audience Instructional Query: Create audience from multiple keywords */
SELECT
  user_id
FROM
  sponsored_ads_traffic_for_audiences
WHERE
  ad_product_type IN ({{ad_types}})
  AND (
    customer_search_term SIMILAR TO '(?i){{keyword1}}'
    OR customer_search_term SIMILAR TO '(?i){{keyword2}}'
    OR customer_search_term SIMILAR TO '(?i){{keyword3}}'
    {{additional_keywords}}
  )""",
            "parameters_schema": {
                "ad_types": {
                    "type": "array",
                    "default": ["'sponsored_brands'", "'sponsored_products'"],
                    "description": "Types of sponsored ads to include"
                },
                "keyword1": {
                    "type": "string",
                    "default": "wireless headphones",
                    "description": "First keyword to target"
                },
                "keyword2": {
                    "type": "string",
                    "default": "bluetooth headphones",
                    "description": "Second keyword to target"
                },
                "keyword3": {
                    "type": "string",
                    "default": "noise cancelling headphones",
                    "description": "Third keyword to target"
                },
                "additional_keywords": {
                    "type": "string",
                    "default": "",
                    "description": "Additional OR clauses for more keywords"
                }
            },
            "display_order": 3,
            "query_type": "main_analysis"
        },
        {
            "title": "Searched but Did Not Purchase",
            "description": "Create an audience of users who searched keywords but did not purchase specific ASINs",
            "sql_query": """/* Audience Instructional Query: Create audience that searched for keywords but did not purchase */
WITH traffic AS (
  SELECT
    user_id,
    MAX(event_dt_utc) AS traffic_dt_max
  FROM
    sponsored_ads_traffic_for_audiences
  WHERE
    /* Optional update: Delete 'sponsored_brands' or 'sponsored_products' if you are focusing on only one */
    ad_product_type IN ({{ad_types}})
    /* Update: Add one or more keywords that you are targeting here */
    AND (
      customer_search_term SIMILAR TO '(?i){{keyword1}}'
      OR customer_search_term SIMILAR TO '(?i){{keyword2}}'
      OR customer_search_term SIMILAR TO '(?i){{keyword3}}'
      {{additional_keywords}}
    )
  GROUP BY
    user_id
),
conv AS (
  SELECT
    user_id,
    MAX(event_dt_utc) AS conv_dt_max
  FROM
    conversions_for_audiences
  WHERE
    event_subtype = 'order'
    /* Update: Delete the tracked_asin filter if you want every conversion or 
     edit the asin filter to capture appropriate asins related to your keyword */
    AND tracked_asin IN ({{asins}})
  GROUP BY
    1
)
SELECT
  t.user_id
FROM
  traffic t
  LEFT JOIN conv c ON c.user_id = t.user_id
WHERE
  /* List of people that searched more recently than they purchased or never purchased */
  traffic_dt_max > conv_dt_max
  OR conv_dt_max IS NULL""",
            "parameters_schema": {
                "ad_types": {
                    "type": "array",
                    "default": ["'sponsored_brands'", "'sponsored_products'"],
                    "description": "Types of sponsored ads to include"
                },
                "keyword1": {
                    "type": "string",
                    "default": "wireless headphones",
                    "description": "First keyword to target"
                },
                "keyword2": {
                    "type": "string",
                    "default": "bluetooth headphones",
                    "description": "Second keyword to target"
                },
                "keyword3": {
                    "type": "string",
                    "default": "noise cancelling headphones",
                    "description": "Third keyword to target"
                },
                "additional_keywords": {
                    "type": "string",
                    "default": "",
                    "description": "Additional OR clauses for more keywords"
                },
                "asins": {
                    "type": "array",
                    "default": ["'B08PZHYWJS'", "'B08WM3LMJF'", "'B09JQL3NWT'"],
                    "description": "ASINs to check for conversions"
                }
            },
            "display_order": 4,
            "query_type": "main_analysis",
            "examples": [
                {
                    "example_name": "Single Keyword Audience Size",
                    "sample_data": {
                        "rows": [
                            {"keyword": "wireless headphones", "user_count": 87234}
                        ]
                    },
                    "interpretation_markdown": "This exploratory query shows that 'wireless headphones' has a substantial audience of 87,234 unique users, making it a viable keyword for audience targeting.",
                    "display_order": 1
                },
                {
                    "example_name": "Multiple Keywords Combined",
                    "sample_data": {
                        "rows": [
                            {"keyword_group": "wireless headphones, bluetooth headphones, noise cancelling headphones", "user_count": 245678}
                        ]
                    },
                    "interpretation_markdown": "Combining related keywords significantly increases audience size to 245,678 users, providing better reach while maintaining relevance.",
                    "display_order": 2
                },
                {
                    "example_name": "Searched but Not Purchased Analysis",
                    "sample_data": {
                        "rows": [
                            {"search_users": 245678, "purchase_users": 45123, "non_purchasers": 200555}
                        ]
                    },
                    "interpretation_markdown": "Of the 245,678 users who searched for the target keywords, 200,555 (82%) have not yet purchased the specified ASINs, representing a high-value remarketing opportunity.",
                    "display_order": 3
                }
            ]
        }
    ],
    "metrics": [
        {
            "metric_name": "user_count",
            "display_name": "User Count",
            "definition": "Count of unique users matching the audience criteria",
            "metric_type": "metric",
            "display_order": 1
        },
        {
            "metric_name": "traffic_dt_max",
            "display_name": "Most Recent Search Date",
            "definition": "The most recent date a user searched for the target keyword",
            "metric_type": "dimension",
            "display_order": 2
        },
        {
            "metric_name": "conv_dt_max",
            "display_name": "Most Recent Purchase Date",
            "definition": "The most recent date a user made a purchase of tracked ASINs",
            "metric_type": "dimension",
            "display_order": 3
        },
        {
            "metric_name": "user_id",
            "display_name": "User ID",
            "definition": "Unique identifier for a user (only available in audience queries)",
            "metric_type": "dimension",
            "display_order": 4
        },
        {
            "metric_name": "customer_search_term",
            "display_name": "Customer Search Term",
            "definition": "The actual search term used by the customer on Amazon",
            "metric_type": "dimension",
            "display_order": 5
        },
        {
            "metric_name": "ad_product_type",
            "display_name": "Ad Product Type",
            "definition": "Type of sponsored ad (sponsored_brands, sponsored_products)",
            "metric_type": "dimension",
            "display_order": 6
        },
        {
            "metric_name": "tracked_asin",
            "display_name": "Tracked ASIN",
            "definition": "ASIN that was involved in the conversion event",
            "metric_type": "dimension",
            "display_order": 7
        },
        {
            "metric_name": "event_subtype",
            "display_name": "Event Subtype",
            "definition": "Type of conversion event (order, shoppingCart, etc.)",
            "metric_type": "dimension",
            "display_order": 8
        }
    ]
}

def main():
    """Main function to seed the build guide"""
    print("Seeding 'Audience based on sponsored ads keywords' build guide...")
    
    try:
        success = create_guide_from_dict(guide_dict=guide_data, update_existing=True)
        
        if success:
            print("✅ Successfully seeded the build guide!")
            print(f"Guide ID: {guide_data['guide']['guide_id']}")
            print(f"Name: {guide_data['guide']['name']}")
            print(f"Category: {guide_data['guide']['category']}")
            print(f"Sections: {len(guide_data['sections'])}")
            print(f"Queries: {len(guide_data['queries'])}")
            print(f"Metrics: {len(guide_data['metrics'])}")
        else:
            print("❌ Failed to seed the build guide. Check logs for details.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error seeding guide: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()