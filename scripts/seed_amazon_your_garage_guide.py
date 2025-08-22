#!/usr/bin/env python3
"""
Seed script for Amazon Your Garage build guide
Creates a comprehensive guide for automotive insights using Amazon Your Garage data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def seed_amazon_your_garage_guide():
    """Seed the Amazon Your Garage build guide"""
    
    client = SupabaseManager.get_client(use_service_role=True)
    
    # Guide metadata
    guide_data = {
        'guide_id': 'guide_amazon_your_garage',
        'name': 'Automotive insights with Amazon Your Garage',
        'category': 'Advanced Analytics',
        'short_description': 'Learn how to leverage Amazon Your Garage data to analyze vehicle ownership patterns, create targeted automotive audiences, and gain insights into customer vehicle preferences for optimized marketing campaigns.',
        'tags': ['automotive', 'vehicle', 'garage', 'audience', 'segmentation', 'conversion'],
        'icon': '🚗',
        'difficulty_level': 'advanced',
        'estimated_time_minutes': 90,
        'prerequisites': [
            'Enrollment (trial or subscription) to Amazon Your Garage is required',
            'AMC customer campaigns must have conversion events for conversion analysis',
            'AMC customers must have access to Audience Segment Insights within the amer region for segment decoration queries',
            'Understanding of SQL and AMC query structure'
        ],
        'is_published': True,
        'display_order': 10,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    # Check if guide already exists
    existing = client.table('build_guides').select('id').eq('guide_id', guide_data['guide_id']).execute()
    
    if existing.data:
        logger.info(f"Guide {guide_data['guide_id']} already exists, updating...")
        guide_response = client.table('build_guides').update(guide_data).eq('guide_id', guide_data['guide_id']).execute()
        guide_id = existing.data[0]['id']
        
        # Delete existing related data
        client.table('build_guide_sections').delete().eq('guide_id', guide_id).execute()
        client.table('build_guide_queries').delete().eq('guide_id', guide_id).execute()
        client.table('build_guide_metrics').delete().eq('guide_id', guide_id).execute()
    else:
        logger.info(f"Creating new guide: {guide_data['name']}")
        guide_response = client.table('build_guides').insert(guide_data).execute()
        guide_id = guide_response.data[0]['id']
    
    # Create sections
    sections = [
        {
            'guide_id': guide_id,
            'section_id': 'introduction',
            'title': 'Introduction',
            'content_markdown': """## What is Amazon Your Garage?

Amazon Your Garage is a virtual vehicle repository which allows customers to add their vehicle's make and model and quickly locate parts and accessories that fit their saved vehicles.

The AMC Amazon Your Garage (AYG) dataset allows you to tap into those user-to-vehicle association signals. When you enroll in Amazon Your Garage, you will have access to the amazon_your_garage dataset containing signals such as vehicle type, make, or engine type, which are updated daily with the most recent user-to-vehicle associations.

You can pair Amazon Your Garage signals with other signals available in AMC, such as conversion events housed within conversions_all or Amazon Ads segment membership signals (for example, audience_segments_amer_lifestyle) stored in region-specific tables. This instructional query guides you through decorating AMC conversion and segment membership signals with the Amazon automotive dataset by using the AMC user_id as the join key across tables.

### Which marketplaces is this available for?

The AMC Amazon Your Garage paid feature is available for enrollment within US and CA AMC account marketplaces. The AMC Your Garage dataset contains signals from US, CA, and MX.

### Requirements

- **Enrollment (trial or subscription) to Amazon Your Garage is required**. Amazon Your Garage paid feature is available for enrollment within US and CA AMC account marketplaces. If you're unable to see the Paid features tab, reach out to your AdTech Account Executive.
- **AMC customer campaigns must have conversion events** (the selected event subtype within the conversions query). For AMC Audience creation, there is no requirement of previous advertising activities (e.g. impressions or interactions).
- For some of the queries below, **AMC customers must have access to Audience Segment Insights within the amer region**.

### Tables used

- **amazon_your_garage**: This data source is an AMC paid feature and provides a dimensional dataset of the user to vehicle associations that are saved within the Your Garage service.
- **audience_segments_amer_{segment_category}**: Amazon Audience Segment Insights enable advertisers to conduct user-to-segment analysis within AMC for all Amazon Advertising customers across all datasets published into AMC as well as segment-level analysis for advertiser uploaded datasets.
- **conversions_all**: This data source is a paid feature dataset and provides a time-based recap of the user to event subtype data feed that describes Amazon Ads customer and their conversion events, both ad-exposed and non-ad-exposed.""",
            'display_order': 1,
            'is_collapsible': True,
            'default_expanded': True
        },
        {
            'guide_id': guide_id,
            'section_id': 'dataset_specifications',
            'title': 'Dataset Specifications and Schema',
            'content_markdown': """## Dataset: amazon_your_garage

Dataset description: Amazon Your Garage vehicle relationship attributes for users in the North America region.

### Data Schema

| column name | data type | aggregation threshold | description |
|-------------|-----------|----------------------|-------------|
| marketplace_name | string | low | Marketplace associated with the Amazon Garage record |
| user_id | string | very_high | User ID of the customer |
| user_id_type | string | low | User_id_type |
| creation_date | date | low | Creation date of the record |
| last_accessed_date | date | low | Last accessed date for a customer invoked interaction with Amazon Garage record |
| update_date | date | low | Update date for the most recent garage record edit |
| garage_year | string | low | Vehicle year attribute |
| vehicle_type | string | low | Vehicle vehicle type attribute |
| garage_make | string | low | Vehicle make attribute |
| garage_model | string | low | Vehicle model attribute |
| garage_submodel | string | low | Vehicle submodel (trim) attribute |
| garage_bodystyle | string | low | Vehicle body style attribute |
| garage_engine | string | low | Vehicle engine attribute |
| garage_transmission | string | low | Vehicle transmission attribute |
| garage_drivetype | string | low | Vehicle drive type attribute |
| garage_brakes | string | low | Vehicle brakes attribute |
| no_3p_trackers | boolean | none | Is this item not allowed to use 3P tracking |

### Sample Enumerated Values

**Marketplace names**: US, MX, CA

**Vehicle types**: Truck, Car, Utility Vehicle, ATV, Street Motorcycle, Van, Offroad Motorcycle, Scooter

**Engine types**: 2.0L L4 Gas, 3.5L V6 Gas, 2.5L L4 Gas, 1.5L L4 Gas, 5.7L V8 Gas, 3.6L V6 Gas, Battery Ev (Ev/Bev), 5.3L V8 Gas, 2.5L L4 Full Hybrid Ev-Gas (Fhev), 900CC""",
            'display_order': 2,
            'is_collapsible': True,
            'default_expanded': True
        },
        {
            'guide_id': guide_id,
            'section_id': 'use_cases_overview',
            'title': 'Use Cases Overview',
            'content_markdown': """## Use cases

This guide provides the following use cases:

- **Explore the Amazon Your Garage dataset**: Explore signals available in the amazon_your_garage dataset
- **Analyze past-purchasers**: Analyze Amazon Your Garage saved vehicle attributes in the context of recent purchasers
- **Segment data decoration**: Determine which Amazon DSP audiences index highly against specific vehicle ownership
- **Multiple vehicle analysis**: Explore users with multiple vehicle types
- **Create AMC Audiences**: Generate rule-based or lookalike audiences based on vehicle attributes

Each use case includes pre-built SQL queries that you can customize for your specific needs.""",
            'display_order': 3,
            'is_collapsible': True,
            'default_expanded': True
        },
        {
            'guide_id': guide_id,
            'section_id': 'best_practices',
            'title': 'Best Practices and Implementation Tips',
            'content_markdown': """## Data Quality Considerations

- Amazon Your Garage data is updated daily
- Consider recency of vehicle associations for campaign relevance
- Validate audience sizes before campaign activation

## Audience Strategy by Vehicle Type

- **Electric Vehicles**: Target with eco-friendly products and charging accessories
- **Trucks**: Focus on towing, hauling, and outdoor lifestyle products
- **Motorcycles**: Emphasize safety gear and performance parts
- **Multiple Vehicles**: Ideal for insurance bundling and maintenance products

## Segment Overlap Insights

- Use segment decoration to identify high-indexing lifestyle segments
- Combine vehicle data with shopping behavior for refined targeting
- Consider exclusion audiences for competitive conquesting

## Campaign Optimization Tips

- Start with exploratory queries to understand data distribution
- Test multiple vehicle attribute combinations
- Monitor performance by vehicle segment
- Use lookalike audiences for scale

## Common Use Cases

- **Auto Parts Retailers**: Target by specific make/model/year
- **Insurance Companies**: Bundle offers for multi-vehicle owners
- **Auto Services**: Target by vehicle age for maintenance campaigns
- **EV Charging**: Focus on electric vehicle owners

## Query Performance Best Practices

- Filter by marketplace when possible
- Use appropriate date ranges for vehicle year
- Consider aggregation thresholds for privacy compliance
- Test queries with small samples first""",
            'display_order': 4,
            'is_collapsible': True,
            'default_expanded': False
        }
    ]
    
    for section in sections:
        response = client.table('build_guide_sections').insert(section).execute()
        if response.data:
            logger.info(f"Created section: {section['title']}")
    
    # Create queries
    queries = [
        {
            'guide_id': guide_id,
            'title': 'Explore Amazon Your Garage data',
            'description': 'Use this query to explore some of the Amazon Your Garage signals, such as saved vehicle type, make, model, and engine configurations.',
            'sql_query': """-- Instructional Query: Exploratory Query for Amazon automotive insights in AMC --
-- Enrollment (trial or subscription) to Amazon Your Garage is required --
SELECT
  marketplace_name,
  vehicle_type,
  garage_make,
  garage_model,
  garage_submodel,
  garage_engine,
  COUNT(DISTINCT user_id) AS distinct_user_id,
  COUNT(user_id) AS count_user_id
FROM
  amazon_your_garage
WHERE
  garage_year >= 2020
  AND garage_year <= 2025
GROUP BY
  1,
  2,
  3,
  4,
  5,
  6""",
            'query_type': 'exploratory',
            'display_order': 1,
            'parameters_schema': {},
            'default_parameters': {},
            'interpretation_notes': 'This query provides a distribution of vehicle attributes in your Amazon Your Garage dataset. Look for popular vehicle types and makes to inform your targeting strategy.'
        },
        {
            'guide_id': guide_id,
            'title': 'Conversion overlap analysis',
            'description': 'This SQL query is designed to assess the overlap between product purchasers and Amazon Your Garage vehicle association signals.',
            'sql_query': """-- Instructional Query: Amazon automotive insights - Conversion overlap analysis --
-- Enrollment (trial or subscription) to Amazon Your Garage is required --
/*
 ------- Customization Instructions -------
 1) OPTIONAL UPDATE [1 of 3] and [3 OF 3]: Change event_subtype to another subtype. For example, use event_subtype = 'detailPagetype')
 2) OPTIONAL UPDATE [2 of 3]: Change conversions_all to conversions
 */
/* Generate a list of the user_ids, conversion count, 
 and sales metrics associated with a filtered business object such as 
 purchase conversion events 
 */
WITH conversion_event_actors AS (
  SELECT
    user_id,
    'purchasers' AS converters,
    -- OPTIONAL UPDATE [1 of 3]: If changing to a different event_subtype, update 'purchasers' to a relevant value
    SUM(total_units_sold) AS units_counter,
    SUM(total_product_sales) AS sales_counter,
    SUM(conversions) AS conversions_counter
  FROM
    conversions_all -- OPTIONAL UPDATE [2 of 3]: Change conversions_all to conversions
  WHERE
    event_subtype = 'order' -- OPTIONAL UPDATE [3 of 3]: change event_subtype to another subtype for example: event_subtype = 'detailPagetype'
  GROUP BY
    1,
    2
),
/* Use the list from conversion_event_actors table and join against the amazon_your_garage dataset, 
 bring in the saved vehicle attributes such as car make or model */
bundled AS (
  SELECT
    cea.user_id AS cea_user_id,
    ayg.user_id AS ayg_user_id,
    cea.converters,
    ayg.vehicle_type,
    ayg.garage_make,
    ayg.garage_model,
    cea.conversions_counter,
    cea.units_counter,
    cea.sales_counter
  FROM
    conversion_event_actors cea
    INNER JOIN amazon_your_garage ayg ON cea.user_id = ayg.user_id
)
/* After combining the conversion events and amazon_your_garage datasets, 
 calculate and aggregate the overlap metrics in order to associated sales metrics 
 with "vehicles in Your Garage" */
SELECT
  b.vehicle_type,
  b.garage_make,
  b.garage_model,
  b.converters,
  SUM(b.conversions_counter) AS sum_count_conversions,
  SUM(b.units_counter) AS sum_units_counter,
  SUM(b.sales_counter) AS sum_sales_counter,
  COUNT(DISTINCT b.cea_user_id) AS cd_cnv_user_id,
  COUNT(DISTINCT b.ayg_user_id) AS cd_ayg_user_id
FROM
  bundled b
GROUP BY
  1,
  2,
  3,
  4""",
            'query_type': 'main_analysis',
            'display_order': 2,
            'parameters_schema': {
                'event_subtype': {
                    'type': 'string',
                    'default': 'order',
                    'description': 'The conversion event subtype to analyze'
                }
            },
            'default_parameters': {
                'event_subtype': 'order'
            },
            'interpretation_notes': 'This query reveals which vehicle owners are converting on your products. High conversion rates for specific vehicle types indicate strong product-market fit.'
        },
        {
            'guide_id': guide_id,
            'title': 'Segment decoration for Amazon automotive',
            'description': 'This SQL query assesses the overlap between Amazon standard catalog audiences and Amazon Your Garage vehicle association signals.',
            'sql_query': """-- Instructional Query: Amazon automotive insights - Segment decoration for Amazon automotive --
-- Enrollment (trial or subscription) to Amazon Your Garage is required --
-- Enrollment in Audience Segments Insights is required (for audience_segments_amer_lifestyle) --
/*
 ------- Customization Instructions -------
 1) OPTIONAL UPDATE [1 of 2]: Change 'EV-associated' to another hardcoded value relevant to your use case
 2) OPTIONAL UPDATE [2 of 2]: Change garage_engine = 'Battery Ev (Ev/Bev)' to garage_make = '{garage_make-attribute}' or garage_model = '{garage_model-attribute}'
 */
 
/* Generate the list of user_id values associated with the conversion event for 
 the selected date range */
WITH ayg_user_list AS (
  SELECT
    user_id,
    'EV-associated' AS ayg_make -- OPTIONAL UPDATE [1 of 2]: Alternatively, 'EV-associated' can be changed to a hardcoded vehicle make/model name
  FROM
    amazon_your_garage
  WHERE
    garage_engine = 'Battery Ev (Ev/Bev)' -- OPTIONAL UPDATE [2 of 2]: Alternatively this can be garage_make = '{garage_make-attribute}' or garage_model = '{garage_model-attribute}'
),
/* Generate the count of users associated with the saved vehicle attribute 
 by using the ayg_user_list CTE  */
ayg_event_counter AS (
  SELECT
    ayg_make,
    COUNT(DISTINCT user_id) AS ayg_make_ceiling
  FROM
    ayg_user_list
  GROUP BY
    1
),
/* Use the list from ayg_user_list table and join against the regional 
 ASI table of choice (in-market or lifestyle) */
bundled AS (
  SELECT
    aul.user_id AS aul_user_id,
    asi.user_id AS asi_user_id,
    aul.ayg_make,
    asi.segment_marketplace_id,
    asi.segment_name,
    asi.segment_id
  FROM
    ayg_user_list aul
    LEFT JOIN audience_segments_amer_lifestyle asi ON aul.user_id = asi.user_id
),
/* With the segment and vehicle association data from the bundled CTE, 
 join and count the number of user_ids by audience segment object */
grouped AS (
  SELECT
    b.ayg_make,
    b.segment_marketplace_id,
    b.segment_name,
    b.segment_id,
    COUNT(DISTINCT b.aul_user_id) AS cd_aul_user_id,
    COUNT(DISTINCT b.asi_user_id) AS cd_asi_user_id
  FROM
    bundled b
  GROUP BY
    1,
    2,
    3,
    4
),
/* With the aggregated audience segment and vehicle association data from grouped 
 - join metadata about the count of saved vehicles so we can establish 
 the denominator for eventual percentage calculations */
joined AS (
  SELECT
    g.ayg_make,
    g.segment_marketplace_id,
    g.segment_name,
    g.segment_id,
    g.cd_aul_user_id,
    g.cd_asi_user_id,
    aec.ayg_make_ceiling
  FROM
    grouped g
    INNER JOIN ayg_event_counter aec ON g.ayg_make = aec.ayg_make
)
/* Print the same data as the output of joined from above - 
 but include the percentage metric to establish the segment overlap 
 with the saved vehicle records and number of distinct users associated with the overlap */
SELECT
  j.ayg_make,
  j.segment_marketplace_id,
  j.segment_name,
  j.segment_id,
  j.cd_aul_user_id,
  j.cd_asi_user_id,
  j.ayg_make_ceiling,
  (j.cd_asi_user_id / j.ayg_make_ceiling) * 100 AS perc_share_of_ayg_associated_users
FROM
  joined j""",
            'query_type': 'main_analysis',
            'display_order': 3,
            'parameters_schema': {
                'vehicle_filter': {
                    'type': 'string',
                    'default': 'Battery Ev (Ev/Bev)',
                    'description': 'Vehicle attribute to filter on (engine type, make, or model)'
                }
            },
            'default_parameters': {
                'vehicle_filter': 'Battery Ev (Ev/Bev)'
            },
            'interpretation_notes': 'This query identifies which lifestyle segments over-index for specific vehicle ownership. Use these insights to refine audience targeting and creative messaging.'
        },
        {
            'guide_id': guide_id,
            'title': 'Multiple vehicle type analysis',
            'description': 'Determine how many users are associated with one, two, or three types of vehicles.',
            'sql_query': """-- Instructional Query: Amazon automotive insights - Multiple vehicle type Amazon automotive analysis --
-- Enrollment (trial or subscription) to Amazon Your Garage is required --
/*
 ------- Customization Instructions -------
 1) OPTIONAL UPDATE [1 of 1]: The CASE statement and associated grouping logic can be updated to 
 reflect different grouping logic or even different columns for assessment, 
 example garage_engine for EV & combustion vehicle owners.
 */
/* Check what percentage of AYG customers have registered more than 1 grouped vehicle
 type for insurance bundler promotion. List all of the AYG user_ids and associated a "grouped" version of the 
 vehicle_type */
WITH table_1 AS (
  SELECT
    user_id,
    /* OPTIONAL UPDATE [1 of 1]: Change to different grouping logic and/or columns */
    CASE
      WHEN vehicle_type IN ('ATV', 'Utility Vehicle', 'Offroad Motorcycle') THEN 'offroad'
      WHEN vehicle_type IN ('Street Motorcycle', 'Scooter') THEN 'bike'
      WHEN vehicle_type IN ('Van', 'Truck', 'Car') THEN 'car'
      ELSE 'other'
    END AS bundled_vehicle_groups
  FROM
    amazon_your_garage
  WHERE
    vehicle_type IS NOT NULL
),
/* Fetch the list of user_ids from table_1 and then calculate the user_id to distinct "grouped" vehicle types */
table_2 AS (
  SELECT
    user_id,
    COUNT(DISTINCT bundled_vehicle_groups) AS bundle_input_counter
  FROM
    table_1
  GROUP BY
    1
)
/* Calculate the number of user_ids that are associated with each
 group of vehicle types */
SELECT
  bundle_input_counter,
  COUNT(DISTINCT user_id) AS count_distinct_user_id
FROM
  table_2
GROUP BY
  1""",
            'query_type': 'main_analysis',
            'display_order': 4,
            'parameters_schema': {},
            'default_parameters': {},
            'interpretation_notes': 'Users with multiple vehicle types are prime targets for bundled offers, insurance products, and cross-category promotions.'
        },
        {
            'guide_id': guide_id,
            'title': 'Create audience for multiple vehicle types',
            'description': 'Create an audience of users with more than 1 vehicle type.',
            'sql_query': """-- AMC Audience Query: Amazon automotive insights - Multiple vehicle type Amazon automotive analysis --
-- Enrollment (trial or subscription) to Amazon Your Garage is required

/* List all of the AYG user_ids and associated a "grouped" version of the vehicle_type */
WITH table_1 AS (
  SELECT
    user_id,
    CASE
      WHEN vehicle_type IN ('ATV','Utility Vehicle','Offroad Motorcycle') THEN 'offroad'
      WHEN vehicle_type IN ('Street Motorcycle','Scooter') THEN 'bike'
      WHEN vehicle_type IN ('Van','Truck','Car') THEN 'car'
      ELSE 'other'
    END AS bundled_vehicle_groups
  FROM amazon_your_garage_for_audiences 
  WHERE vehicle_type IS NOT NULL
),
/* For the user_ids within the first sub-query, calculate whether a user_id is 
associated with 1 or more distinct "grouped" vehicle types */
table_2 AS (
  SELECT
    user_id,
    COUNT(distinct bundled_vehicle_groups) AS bundle_input_counter
  FROM table_1
  GROUP BY 1
)
/* Because this query is for AMC audience creation, no grouping statement is required,
 just the list of user_id for association with the AMC audience object */
SELECT
  user_id
FROM table_2
WHERE bundle_input_counter > 1""",
            'query_type': 'main_analysis',
            'display_order': 5,
            'parameters_schema': {},
            'default_parameters': {},
            'interpretation_notes': 'This audience query creates a targetable segment of users who own multiple vehicle types, ideal for insurance bundling and multi-product offers.'
        },
        {
            'guide_id': guide_id,
            'title': 'Create audience based on vehicle attributes',
            'description': 'Create audiences based on various vehicle attributes like model year, make, engine type.',
            'sql_query': """-- AMC Audience Query: Amazon automotive insights - Audience of vehicle models between 2020 and 2025 
/*
 ------- Customization Instructions -------
 1a) OPTIONAL UPDATE [1 of 1]: Add one or more filters by uncommenting AND clauses below
 1b) Be sure to replace the values below with actual values from your signals.
*/

/* generate rule-based or lookalike AMC audiences based on saved vehicle attributes */
SELECT
 user_id
FROM amazon_your_garage_for_audiences
WHERE
 garage_year >= 2020 AND garage_year <= 2025 -- OPTIONAL UPDATE [1 of 1]: Uncomment one or more of the lines below.
 -- AND garage_model = 'Model 1'
 -- AND garage_make = 'Make 2'
 -- AND garage_engine = 'Battery Ev (Ev/Bev)'
 -- AND vehicle_type = 'Street Motorcycle'""",
            'query_type': 'main_analysis',
            'display_order': 6,
            'parameters_schema': {
                'start_year': {
                    'type': 'integer',
                    'default': 2020,
                    'description': 'Start year for vehicle model year range'
                },
                'end_year': {
                    'type': 'integer',
                    'default': 2025,
                    'description': 'End year for vehicle model year range'
                }
            },
            'default_parameters': {
                'start_year': 2020,
                'end_year': 2025
            },
            'interpretation_notes': 'This flexible audience query allows you to create custom audiences based on any combination of vehicle attributes.'
        }
    ]
    
    for query in queries:
        response = client.table('build_guide_queries').insert(query).execute()
        if response.data:
            query_id = response.data[0]['id']
            logger.info(f"Created query: {query['title']}")
            
            # Add examples for some queries
            if query['title'] == 'Explore Amazon Your Garage data':
                examples = [
                    {
                        'guide_query_id': query_id,
                        'example_name': 'Vehicle Distribution Analysis',
                        'sample_data': {
                            'rows': [
                                {
                                    'marketplace_name': 'US',
                                    'vehicle_type': 'Truck',
                                    'garage_make': 'Make 1',
                                    'garage_model': 'Model 1',
                                    'garage_submodel': 'Mid',
                                    'garage_engine': '6.2L V8 Flex',
                                    'distinct_user_id': 266,
                                    'count_user_id': 267
                                },
                                {
                                    'marketplace_name': 'US',
                                    'vehicle_type': 'Car',
                                    'garage_make': 'Make 1',
                                    'garage_model': 'Model 2',
                                    'garage_submodel': '',
                                    'garage_engine': '2.5L L4 Full Hybrid Ev-Gas (Fhev)',
                                    'distinct_user_id': 257,
                                    'count_user_id': 257
                                },
                                {
                                    'marketplace_name': 'MX',
                                    'vehicle_type': 'Truck',
                                    'garage_make': 'Make 2',
                                    'garage_model': 'Model 3',
                                    'garage_submodel': 'Mid',
                                    'garage_engine': '',
                                    'distinct_user_id': 5,
                                    'count_user_id': 5
                                },
                                {
                                    'marketplace_name': 'US',
                                    'vehicle_type': 'ATV',
                                    'garage_make': 'Make 3',
                                    'garage_model': 'Model 4',
                                    'garage_submodel': 'Base',
                                    'garage_engine': '233CC',
                                    'distinct_user_id': 314,
                                    'count_user_id': 318
                                },
                                {
                                    'marketplace_name': 'US',
                                    'vehicle_type': 'Car',
                                    'garage_make': 'Make 2',
                                    'garage_model': 'Model 5',
                                    'garage_submodel': 'Base',
                                    'garage_engine': 'Battery Ev (Ev/Bev)',
                                    'distinct_user_id': 316,
                                    'count_user_id': 317
                                }
                            ]
                        },
                        'interpretation_markdown': 'This result shows the distribution of vehicle types and models in your Amazon Your Garage dataset. Notice the presence of electric vehicles (Battery Ev) and hybrid vehicles (Fhev), which represent growing segments for eco-conscious marketing.',
                        'insights': [
                            'Trucks and Cars dominate the vehicle types in the US marketplace',
                            'Electric and hybrid vehicles are present, indicating opportunity for green product marketing',
                            'ATVs represent a niche segment that may be interested in outdoor and recreational products'
                        ],
                        'display_order': 1
                    }
                ]
                
                for example in examples:
                    client.table('build_guide_examples').insert(example).execute()
                    logger.info(f"Created example: {example['example_name']}")
            
            elif query['title'] == 'Conversion overlap analysis':
                examples = [
                    {
                        'guide_query_id': query_id,
                        'example_name': 'Conversion Overlap Results',
                        'sample_data': {
                            'rows': [
                                {
                                    'vehicle_type': 'Truck',
                                    'garage_make': 'Make 1',
                                    'garage_model': 'Model 1',
                                    'converters': 'purchasers',
                                    'sum_count_conversions': 64777,
                                    'sum_units_counter': 70358,
                                    'sum_sales_counter': 1808815.03,
                                    'cd_cnv_user_id': 40099,
                                    'cd_ayg_user_id': 40099
                                },
                                {
                                    'vehicle_type': 'Truck',
                                    'garage_make': 'Make 1',
                                    'garage_model': 'Model 2',
                                    'converters': 'purchasers',
                                    'sum_count_conversions': 46665,
                                    'sum_units_counter': 50204,
                                    'sum_sales_counter': 1240086.05,
                                    'cd_cnv_user_id': 29281,
                                    'cd_ayg_user_id': 29281
                                },
                                {
                                    'vehicle_type': 'Truck',
                                    'garage_make': 'Make 2',
                                    'garage_model': 'Model 3',
                                    'converters': 'purchasers',
                                    'sum_count_conversions': 38324,
                                    'sum_units_counter': 41755,
                                    'sum_sales_counter': 1171133.17,
                                    'cd_cnv_user_id': 24115,
                                    'cd_ayg_user_id': 24115
                                }
                            ]
                        },
                        'interpretation_markdown': 'This analysis shows which vehicle owners are converting on your products. Truck owners show significant purchasing power with high sales values, suggesting opportunity for premium product positioning.',
                        'insights': [
                            'Truck owners generate the highest sales volumes',
                            'Average order values vary by vehicle model',
                            'Focus on high-converting vehicle segments for campaign optimization'
                        ],
                        'display_order': 1
                    }
                ]
                
                for example in examples:
                    client.table('build_guide_examples').insert(example).execute()
                    logger.info(f"Created example: {example['example_name']}")
            
            elif query['title'] == 'Segment decoration for Amazon automotive':
                examples = [
                    {
                        'guide_query_id': query_id,
                        'example_name': 'Segment Overlap Analysis',
                        'sample_data': {
                            'rows': [
                                {
                                    'ayg_make': 'EV-associated',
                                    'segment_marketplace_id': 1,
                                    'segment_name': 'LS - B2B - Seller Central Lookalikes',
                                    'segment_id': 8578,
                                    'cd_aul_user_id': 480912,
                                    'cd_asi_user_id': 480912,
                                    'ayg_make_ceiling': 563455,
                                    'perc_share_of_ayg_associated_users': 85.40
                                },
                                {
                                    'ayg_make': 'EV-associated',
                                    'segment_marketplace_id': 1,
                                    'segment_name': 'LS - House Keeper',
                                    'segment_id': 964,
                                    'cd_aul_user_id': 455298,
                                    'cd_asi_user_id': 455298,
                                    'ayg_make_ceiling': 563455,
                                    'perc_share_of_ayg_associated_users': 80.80
                                },
                                {
                                    'ayg_make': 'EV-associated',
                                    'segment_marketplace_id': 1,
                                    'segment_name': 'LS - Digerati',
                                    'segment_id': 130,
                                    'cd_aul_user_id': 423826,
                                    'cd_asi_user_id': 423826,
                                    'ayg_make_ceiling': 563455,
                                    'perc_share_of_ayg_associated_users': 75.20
                                }
                            ]
                        },
                        'interpretation_markdown': 'EV owners over-index significantly with B2B and tech-savvy segments. This suggests they are business-oriented, early adopters who may be interested in innovative products and services.',
                        'insights': [
                            'EV owners have high overlap with B2B and business segments',
                            'Tech-savvy "Digerati" segment shows strong affinity with EV ownership',
                            'Use these segment overlaps to refine creative messaging and product selection'
                        ],
                        'display_order': 1
                    }
                ]
                
                for example in examples:
                    client.table('build_guide_examples').insert(example).execute()
                    logger.info(f"Created example: {example['example_name']}")
            
            elif query['title'] == 'Multiple vehicle type analysis':
                examples = [
                    {
                        'guide_query_id': query_id,
                        'example_name': 'Multiple Vehicle Type Distribution',
                        'sample_data': {
                            'rows': [
                                {
                                    'bundle_input_counter': 3,
                                    'count_distinct_user_id': 810714
                                },
                                {
                                    'bundle_input_counter': 2,
                                    'count_distinct_user_id': 7905119
                                },
                                {
                                    'bundle_input_counter': 1,
                                    'count_distinct_user_id': 109444563
                                }
                            ]
                        },
                        'interpretation_markdown': 'Most users have single vehicle types, but a significant segment owns multiple vehicle types. These multi-vehicle households represent premium targeting opportunities for bundled offers.',
                        'insights': [
                            'Over 8.7 million users own 2+ vehicle types',
                            'Multi-vehicle owners are prime targets for insurance bundling',
                            'Consider household-level marketing strategies for these segments'
                        ],
                        'display_order': 1
                    }
                ]
                
                for example in examples:
                    client.table('build_guide_examples').insert(example).execute()
                    logger.info(f"Created example: {example['example_name']}")
    
    # Create metrics
    metrics = [
        {
            'guide_id': guide_id,
            'metric_name': 'distinct_user_id',
            'display_name': 'Distinct User ID',
            'definition': 'Count of unique users with specific vehicle attributes',
            'metric_type': 'metric',
            'display_order': 1
        },
        {
            'guide_id': guide_id,
            'metric_name': 'sum_count_conversions',
            'display_name': 'Total Conversions',
            'definition': 'Total conversion events for vehicle owners',
            'metric_type': 'metric',
            'display_order': 2
        },
        {
            'guide_id': guide_id,
            'metric_name': 'sum_units_counter',
            'display_name': 'Total Units Sold',
            'definition': 'Total units sold to vehicle owners',
            'metric_type': 'metric',
            'display_order': 3
        },
        {
            'guide_id': guide_id,
            'metric_name': 'sum_sales_counter',
            'display_name': 'Total Sales Value',
            'definition': 'Total sales value from vehicle owners',
            'metric_type': 'metric',
            'display_order': 4
        },
        {
            'guide_id': guide_id,
            'metric_name': 'bundle_input_counter',
            'display_name': 'Vehicle Type Count',
            'definition': 'Number of distinct vehicle types per user',
            'metric_type': 'metric',
            'display_order': 5
        },
        {
            'guide_id': guide_id,
            'metric_name': 'perc_share_of_ayg_associated_users',
            'display_name': 'Segment Overlap Percentage',
            'definition': 'Percentage overlap with audience segments',
            'metric_type': 'metric',
            'display_order': 6
        },
        {
            'guide_id': guide_id,
            'metric_name': 'marketplace_name',
            'display_name': 'Marketplace',
            'definition': 'Marketplace (US, CA, MX)',
            'metric_type': 'dimension',
            'display_order': 7
        },
        {
            'guide_id': guide_id,
            'metric_name': 'vehicle_type',
            'display_name': 'Vehicle Type',
            'definition': 'Type of vehicle (Car, Truck, Motorcycle, etc.)',
            'metric_type': 'dimension',
            'display_order': 8
        },
        {
            'guide_id': guide_id,
            'metric_name': 'garage_make',
            'display_name': 'Vehicle Make',
            'definition': 'Vehicle manufacturer',
            'metric_type': 'dimension',
            'display_order': 9
        },
        {
            'guide_id': guide_id,
            'metric_name': 'garage_model',
            'display_name': 'Vehicle Model',
            'definition': 'Vehicle model name',
            'metric_type': 'dimension',
            'display_order': 10
        },
        {
            'guide_id': guide_id,
            'metric_name': 'garage_engine',
            'display_name': 'Engine Type',
            'definition': 'Engine type and specifications',
            'metric_type': 'dimension',
            'display_order': 11
        },
        {
            'guide_id': guide_id,
            'metric_name': 'garage_year',
            'display_name': 'Vehicle Year',
            'definition': 'Vehicle model year',
            'metric_type': 'dimension',
            'display_order': 12
        },
        {
            'guide_id': guide_id,
            'metric_name': 'garage_submodel',
            'display_name': 'Vehicle Trim',
            'definition': 'Vehicle trim level',
            'metric_type': 'dimension',
            'display_order': 13
        },
        {
            'guide_id': guide_id,
            'metric_name': 'segment_name',
            'display_name': 'Audience Segment',
            'definition': 'Amazon audience segment name',
            'metric_type': 'dimension',
            'display_order': 14
        }
    ]
    
    for metric in metrics:
        response = client.table('build_guide_metrics').insert(metric).execute()
        if response.data:
            logger.info(f"Created metric: {metric['display_name']}")
    
    logger.info(f"✅ Successfully seeded Amazon Your Garage build guide!")
    logger.info(f"Guide ID: {guide_data['guide_id']}")
    logger.info(f"Internal ID: {guide_id}")

if __name__ == "__main__":
    try:
        seed_amazon_your_garage_guide()
    except Exception as e:
        logger.error(f"Failed to seed guide: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)