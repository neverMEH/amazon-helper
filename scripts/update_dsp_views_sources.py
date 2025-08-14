#!/usr/bin/env python3
"""
Update DSP Views data sources in AMC
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone
import uuid

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Define the DSP Views data sources
dsp_views_sources = [
    {
        "schema_id": "dsp_views",
        "name": "Amazon DSP Views",
        "description": "Analytics table that represents all view events and all measurable events. Measurable events are from impressions that were able to be measured. Viewable events represent events that met a viewable standard. The metric viewable_impressions is the count of viewable impressions using the IAB standard (50% of the impression's pixels were on screen for at least 1 second). Note the dsp_views table records a single impression more than one time if it is both measurable and viewable according to IAB's standards.",
        "category": "DSP",
        "table_type": "Analytics"
    },
    {
        "schema_id": "dsp_views_for_audiences",
        "name": "Amazon DSP Views for Audiences",
        "description": "Audience table that represents all view events and all measurable events. An impression that is both measurable and viewable according to IAB's standards is recorded in one row as a measurable event and in another row as a viewable event. Note that while all impression events from dsp_views are recorded in dsp_impressions, not all impression events from dsp_impressions are recorded in dsp_views because not all impression events can be categorized as viewable, measurable or unmeasurable.",
        "category": "DSP",
        "table_type": "Audience"
    }
]

# Define the fields for DSP views tables
dsp_views_fields = [
    # Dimensions
    {"name": "ad_slot_size", "data_type": "STRING", "field_type": "Dimension", "description": "Ad slot size in which the Amazon DSP ad was served, expressed as width x height in pixels. The dimensions indicate the space allocated for the ad on the page or app where the impression was served. Example values: '300x250', '728x90', '320x50'.", "aggregation_threshold": "LOW"},
    {"name": "advertiser", "data_type": "STRING", "field_type": "Dimension", "description": "Name of the business entity running advertising campaigns on Amazon DSP. Example value: 'Widgets Inc'.", "aggregation_threshold": "LOW"},
    {"name": "advertiser_account_frequency_group_ids", "data_type": "ARRAY", "field_type": "Dimension", "description": "An array of the advertiser-account-level frequency group IDs that were applicable for this impression event. Frequency groups created at the advertiser account level may operate across 1 or more campaigns within that advertiser account. Note that a single impression may be subject to multiple frequency groups.", "aggregation_threshold": "LOW"},
    {"name": "advertiser_country", "data_type": "STRING", "field_type": "Dimension", "description": "Country of the Amazon DSP advertiser. This value is based on the country setting configured in the advertiser's Amazon DSP account. Example value: 'US'.", "aggregation_threshold": "LOW"},
    {"name": "advertiser_id", "data_type": "LONG", "field_type": "Dimension", "description": "ID of the Amazon DSP advertiser associated with the view event. Example value: '123456789012345'.", "aggregation_threshold": "LOW"},
    {"name": "advertiser_timezone", "data_type": "STRING", "field_type": "Dimension", "description": "Advertiser timezone. This setting aligns with the advertiser timezone configuration in the connected Amazon DSP account. Example value: 'America/New_York'.", "aggregation_threshold": "LOW"},
    {"name": "app_bundle", "data_type": "STRING", "field_type": "Dimension", "description": "The app bundle ID associated with the Amazon DSP view event. App bundles follow different formatting conventions depending on the app store.", "aggregation_threshold": "LOW"},
    {"name": "campaign", "data_type": "STRING", "field_type": "Dimension", "description": "Name of the Amazon DSP campaign responsible for the view event. A campaign is a container that groups related advertising efforts with shared objectives, budget, and flight dates. Example value: 'Widgets_Q1_2024_Awareness_Display_US'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_end_date", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "End date and time of the Amazon DSP campaign in advertiser timezone. Example value: '2025-01-01T23:59:59.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_end_date_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "End date of the Amazon DSP campaign in Coordinated Universal Time (UTC). Example value: '2025-01-01T23:59:59.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_flight_id", "data_type": "LONG", "field_type": "Dimension", "description": "ID of the Amazon DSP campaign flight. A campaign flight represents a scheduled run period for an advertising campaign with defined start and end dates. Example value: '123456789012345'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_id", "data_type": "LONG", "field_type": "Dimension", "description": "The ID of the Amazon DSP campaign responsible for the view event. In this table, campaign_id and campaign_id_string fields will show the same value for a given event. Example value: '571234567890123456'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_id_string", "data_type": "STRING", "field_type": "Dimension", "description": "The ID of the Amazon DSP campaign responsible for the view event. In this table, campaign_id and campaign_id_string fields will show the same value for a given event. Example value: '571234567890123456'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_insertion_order_id", "data_type": "STRING", "field_type": "Dimension", "description": "ID of the insertion order associated with the Amazon DSP view event. An insertion order is a contractual agreement between an advertiser and Amazon Ads that outlines the specific details of a programmatic advertising campaign. Example value: '123456789'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_primary_goal", "data_type": "STRING", "field_type": "Dimension", "description": "Primary goal set for campaign optimization in Amazon DSP. Campaign goals determine how Amazon DSP optimizes delivery and measures success of the campaign. The goal selected during campaign setup influences bidding strategy and campaign optimization. Possible values include: 'ROAS', 'TOTAL_ROAS', 'REACH', 'CPVC', 'COMPLETION_RATE', 'CTR', 'CPC', 'DPVR', 'PAGE_VISIT', 'CPDPV', 'CPA' 'OTHER', and 'NONE'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_sales_type", "data_type": "STRING", "field_type": "Dimension", "description": "Billing classification of the Amazon DSP campaign, which distinguishes billable and non-billable campaigns. Possible values include: 'BILLABLE' and 'BONUS'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_source", "data_type": "STRING", "field_type": "Dimension", "description": "Campaign source.", "aggregation_threshold": "LOW"},
    {"name": "campaign_start_dt", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Start date and time of the Amazon DSP campaign in advertiser timezone. The campaign start date determines when a campaign begins serving impressions. Example value: '2025-01-01T00:00:00.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_start_date_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Start date and time of the Amazon DSP campaign in Coordinated Universal Time (UTC). The campaign start date determines when a campaign begins serving impressions. Example value: '2025-01-01T00:00:00.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_status", "data_type": "STRING", "field_type": "Dimension", "description": "Current status of the Amazon DSP campaign. Campaign status indicates whether a campaign is actively delivering ads, has completed its flight dates, or has been paused by the advertiser. Possible values include: 'ENDED', 'RUNNING', 'ENABLED', 'PAUSED', and 'ADS_NOT_RUNNING'.", "aggregation_threshold": "LOW"},
    {"name": "city_name", "data_type": "STRING", "field_type": "Dimension", "description": "City name where the Amazon DSP view event occurred, determined by signal available in the auction event. Example value: 'New York'.", "aggregation_threshold": "HIGH"},
    {"name": "creative", "data_type": "STRING", "field_type": "Dimension", "description": "Name of the Amazon DSP creative/ad. A creative represents the actual advertisement shown to customers. Example value: '2025_US_Widgets_Spring_Mobile_320x50'.", "aggregation_threshold": "LOW"},
    {"name": "creative_category", "data_type": "STRING", "field_type": "Dimension", "description": "Category of the Amazon DSP creative/ad. This field categorizes Amazon DSP ads into broad creative format types like display ads and video ads. Possible values include: 'Display', 'Video', and NULL.", "aggregation_threshold": "LOW"},
    {"name": "creative_duration", "data_type": "INTEGER", "field_type": "Dimension", "description": "Duration in seconds of the Amazon DSP creative asset, primarily used for video format ads. This field specifies the length of video creative assets delivered through Amazon DSP campaigns. For non-video creative formats like display ads, this field will be NULL. Example values include: '15', '30', '60', representing video durations in seconds.", "aggregation_threshold": "LOW"},
    {"name": "creative_id", "data_type": "LONG", "field_type": "Dimension", "description": "Unique identifier for the Amazon DSP creative/ad. A ad represents the actual advertisement shown to customers, which could be an image, video, or other ad format. Example value: '591234567890123456'.", "aggregation_threshold": "LOW"},
    {"name": "creative_is_link_in", "data_type": "STRING", "field_type": "Dimension", "description": "Boolean field indicating whether the Amazon DSP creative/ad directs to an Amazon destination (link in) versus an external destination (link out). A link in creative directs users to an Amazon destination like a product detail page, while a link out creative directs users to an external destination like an advertiser's website. Possible values for this field are: 'Y' (creative is link in), 'N' (creative is link out).", "aggregation_threshold": "LOW"},
    {"name": "creative_size", "data_type": "STRING", "field_type": "Dimension", "description": "Dimensions of the Amazon DSP creative/ad (width x height in pixels, or responsive format). Example values: '300x250', '320x50', 'Responsive'.", "aggregation_threshold": "LOW"},
    {"name": "creative_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of creative/ad.", "aggregation_threshold": "LOW"},
    {"name": "demand_channel_owner", "data_type": "STRING", "field_type": "Dimension", "description": "Demand channel owner.", "aggregation_threshold": "LOW"},
    {"name": "device_make", "data_type": "STRING", "field_type": "Dimension", "description": "Manufacturer or brand name of the device associated with the Amazon DSP view event, derived from user-agent in the impression auction. Values may appear in different formats or capitalizations for the same manufacturer. Example values: 'Apple', 'APPLE', 'Samsung', 'SAMSUNG', 'ROKU', 'Generic', 'UNKNOWN'.", "aggregation_threshold": "LOW"},
    {"name": "device_model", "data_type": "STRING", "field_type": "Dimension", "description": "Model of the device associated with the Amazon DSP view event, derived from user-agent in the impression auction. Values may appear in different formats or capitalizations for the same manufacturer. Example values: 'iPhone', 'GALAXY'.", "aggregation_threshold": "LOW"},
    {"name": "entity_id", "data_type": "DATE", "field_type": "Dimension", "description": "ID of the Amazon DSP entity (also known as seat) associated with the view event. An entity represents an Amazon DSP account, within which media is further organized by advertiser and by campaign. Example value: 'ENTITYABC123XYZ789'.", "aggregation_threshold": "LOW"},
    {"name": "environment_type", "data_type": "DATE", "field_type": "Dimension", "description": "Environment where the Amazon DSP view event occurred. This field distinguishes between web-based environments like desktop or mobile browsers, and app-based environments like mobile apps. If the environment type cannot be determined, this field will be NULL. Possible values include: 'Web', 'App', and NULL.", "aggregation_threshold": "LOW"},
    {"name": "event_date", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Date of the Amazon DSP view event in advertiser timezone. This field will be populated for conversion events that are attributed to an ad view. Example value: '2025-01-01'.", "aggregation_threshold": "LOW"},
    {"name": "event_date_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Date of the Amazon DSP view event in Coordinated Universal Time (UTC). This field will be populated for conversion events that are attributed to an ad view. Example value: '2025-01-01'", "aggregation_threshold": "LOW"},
    {"name": "event_dt", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the Amazon DSP view event in advertiser timezone. This field will be populated for conversion events that are attributed to an ad view. Example value: '2025-01-01T12:00:00.000Z'.", "aggregation_threshold": "MEDIUM"},
    {"name": "event_dt_hour", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the Amazon DSP view event in advertiser timezone, truncated to hour. This field will be populated for conversion events that are attributed to an ad view. Example value: '2025-01-01T12:00:00.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "event_dt_hour_utc", "data_type": "STRING", "field_type": "Dimension", "description": "Timestamp of the Amazon DSP view event in Coordinated Universal Time (UTC), truncated to hour. This field will be populated for conversion events that are attributed to an ad view. Example value: '2025-01-01T12:00:00.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "event_dt_utc", "data_type": "LONG", "field_type": "Metric", "description": "Timestamp of the Amazon DSP view event in Coordinated Universal Time (UTC). This field will be populated for conversion events that are attributed to an ad view. Example value: '2025-01-01T00:00:00.000Z'.", "aggregation_threshold": "MEDIUM"},
    {"name": "event_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of view event. There are four types of view events in AMC. Measurable impression events indicate that the Amazon Ads impression was able to be measured for viewability; these events can be summed using the measurable_impressions metric. Viewable impression events indicate Amazon Ads determined the impression met MRC viewability standards; these events can be summed using the viewable_impressions metric. Unmeasurable viewable and synthetic viewable impression events are estimated to be viewable; these events can be summed using the unmeasurable_viewable_impressions metric. Possible values include: 'MEASURABLE_IMP' (measurable impression), 'VIEW' (viewable impression), 'UNMEASURABLE_IMP' (unmeasurable viewable impression), and 'SYNTHETIC_VIEW' (synthetic view impression).", "aggregation_threshold": "LOW"},
    {"name": "events", "data_type": "STRING", "field_type": "Dimension", "description": "Count of Amazon DSP view events. When querying this table, remember that each record represents one Amazon DSP view event, and a single impression may have more than one view event. Therefore, this field will not represent the exact count of impressions served by your campaigns. Since this table only includes views events, this field will always have a value of '1' (the event was a view event).", "aggregation_threshold": "NONE"},
    {"name": "impression_id", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "ID that connects related impression, view, click, and conversion events. For example, if an impression served has a request_tag value of 'X', related view events will have have an impression_id value of 'X'. All view events for a single impression will share a common impression_id value. While this occurs infrequently, there are sometimes duplicate request_tag values. As a result, it is not recommended to use request_tag as a JOIN key without first grouping by it. Rather, it is a best practice to first consider using UNION ALL in a query instead of joining based on the request_tag to combine data sources. For insights that involve user-level ad exposure across tables, use user_id instead.", "aggregation_threshold": "VERY_HIGH"},
    {"name": "line_item", "data_type": "STRING", "field_type": "Dimension", "description": "Name of the Amazon DSP line item responsible for the view event. Attributes like ad format and targeting are defined at line item level within a campaign. Example value: 'Widgets - DISPLAY - O&O - RETARGETING'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_end_dt", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "End date and time of the Amazon DSP line item in advertiser timezone. Example value: '2025-01-01T23:59:59.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_end_dt_utc", "data_type": "STRING", "field_type": "Dimension", "description": "End date and time of the line item in Coordinated Universal Time (UTC). Example value: '2025-01-01T23:59:59.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_id", "data_type": "LONG", "field_type": "Dimension", "description": "ID of the Amazon DSP line item responsible for the view event. Attributes like ad format and targeting are defined at line item level within a campaign. Example value: '5812345678901234'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_price_type", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Pricing model used for the Amazon DSP line item. Line items can use different pricing models to determine how costs are calculated, with Cost Per Mille (CPM) being a common model where advertisers pay per thousand impressions. Example value: 'CPM'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_start_dt", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Start date and time of the Amazon DSP line item in advertiser timezone. Example value: '2025-01-01T23:59:59.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_start_dt_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Start date and time of the Amazon DSP line item in Coordinated Universal Time (UTC). Example value: '2025-01-01T23:59:59.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_status", "data_type": "STRING", "field_type": "Metric", "description": "Status of the Amazon DSP line item. The status indicates whether the line item is actively delivering ads, has been paused, or has completed its flight. Possible values include: 'ENDED', 'ENABLED', 'RUNNING', 'PAUSED_BY_USER', and 'SUSPENDED'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of Amazon DSP line item. Line item types indicate how ads are delivered and optimized. Example values include: 'AAP', 'AAP_DISPLAY', 'AAP_MOBILE', 'AAP_VIDEO_CPM'.", "aggregation_threshold": "LOW"},
    {"name": "manager_account_frequency_group_ids", "data_type": "ARRAY", "field_type": "Dimension", "description": "An array of the manager-account-level frequency group IDs that were applicable for this impression event. Frequency groups created at the manager account level may operate across 1 or more advertisers within that manager account. Note that a single impression may be subject to multiple frequency groups.", "aggregation_threshold": "LOW"},
    {"name": "measurable_impressions", "data_type": "LONG", "field_type": "Dimension", "description": "Count of impressions that could be measured for viewability. Measurable impression events indicate that the Amazon Ads impression was able to be measured for viewability. A single impression that is measurable could also be viewable, but not all measurable impressions are viewable. If an impression is both measurable and viewable, each event for the single impression is listed as a separate row. Possible values for this field are: '1' (if the record represents a measurable impression) or '0' (if the record does not represent a measurable impression).", "aggregation_threshold": "NONE"},
    {"name": "merchant_id", "data_type": "STRING", "field_type": "Dimension", "description": "Merchant ID.", "aggregation_threshold": "LOW"},
    {"name": "no_3p_trackers", "data_type": "STRING", "field_type": "Dimension", "description": "Boolean value indicating whether the event can be used for audience creation that is third-party tracking enabled (i.e. whether you can serve creative with third-party tracking when running media against the audience). Third-party tracking refers to measurement tags and pixels from external vendors that can be used to measure ad performance. Possible values for this field are: 'true', 'false'.", "aggregation_threshold": "NONE"},
    {"name": "operating_system", "data_type": "STRING", "field_type": "Dimension", "description": "Operating system of the device where the Amazon DSP view event occurred. Example values: 'iOS', 'Android', 'Windows', 'macOS', 'Roku OS'.", "aggregation_threshold": "LOW"},
    {"name": "os_version", "data_type": "STRING", "field_type": "Dimension", "description": "Operating system version of the device where the Amazon DSP view event occurred. The version format varies by operating system type. Example value: '17.5.1'.", "aggregation_threshold": "LOW"},
    {"name": "page_type", "data_type": "LONG", "field_type": "Dimension", "description": "Type of page where the Amazon DSP view event occurred. This grain of detail is primarily relevant to impressions served on Amazon sites. Example values: 'Search', 'Detail', 'CustomerReviews'.", "aggregation_threshold": "LOW"},
    {"name": "publisher_id", "data_type": "LONG", "field_type": "Metric", "description": "ID of the publisher where the Amazon DSP view event occurred. A publisher is the media owner (such as a website, app, or streaming service owner) that makes advertising inventory available for purchase through Amazon DSP.", "aggregation_threshold": "LOW"},
    {"name": "site", "data_type": "STRING", "field_type": "Dimension", "description": "The site descriptor where the Amazon DSP view event occurred. A site can be any digital property where ads are served, including websites, mobile apps, and streaming platforms.", "aggregation_threshold": "LOW"},
    {"name": "slot_position", "data_type": "LONG", "field_type": "Metric", "description": "Position of the ad on the page relative to the initial viewport. Above the fold (ATF) refers to the portion of the webpage visible without scrolling, while below the fold (BTF) refers to the portion that requires scrolling to view. This dimension helps measure where ad impressions were served on the page. Possible values include: 'ATF', 'BTF', and 'UNKNOWN'.", "aggregation_threshold": "LOW"},
    {"name": "supply_source_id", "data_type": "LONG", "field_type": "Metric", "description": "ID of the supply source from which the Amazon DSP impression was purchased. Supply sources can include Amazon-owned properties (like Amazon.com and Twitch), Amazon Publisher Services inventory, and third-party partners.", "aggregation_threshold": "LOW"},
    {"name": "unmeasurable_viewable_impressions", "data_type": "LONG", "field_type": "Metric", "description": "Count of unmeasurable viewable/synthetic view events. Unmeasurable viewable and synthetic viewable events are estimated to be viewable, but could not be measured for viewability. Possible values for this field are: '1' (if the record represents a unmeasurable viewable/synthetic view event) or '0' (if the record does not represent a unmeasurable viewable/synthetic view event).", "aggregation_threshold": "NONE"},
    {"name": "user_id", "data_type": "STRING", "field_type": "Dimension", "description": "Pseudonymous identifier that connects user activity across different events. The field can contain ad user IDs (representing Amazon accounts), device IDs, or browser IDs. NULL values appear when Amazon Ads is unable to resolve an identifier for an event. The field has a VERY_HIGH aggregation threshold, meaning it cannot be included in final SELECT statements but can be used within Common Table Expressions (CTEs) for aggregation purposes like COUNT(DISTINCT user_id).", "aggregation_threshold": "LOW"},
    {"name": "user_id_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of user ID value. AMC includes different types of user ID values, depending on whether the value represents a resolved Amazon account, a device, or a browser cookie. If Amazon Ads is unable to determine or provide an ID of any kind for a view event, the 'user_id' and 'user_id_type' values for that record will be NULL. Possible values include: 'adUserId', 'sisDeviceId', 'adBrowserId', and NULL.", "aggregation_threshold": "VERY_HIGH"},
    {"name": "view_definition", "data_type": "LONG", "field_type": "Metric", "description": "Type of viewability measurement definition used to classify the view event. This field will only be populated for viewable impressions (event_type = 'VIEW').", "aggregation_threshold": "LOW"},
    {"name": "viewable_impressions", "data_type": "LONG", "field_type": "Metric", "description": "The count of impressions that were considered viewable. An impression is considered viewable when at least 50% of the ad's pixels are in view for at least one continuous second for display ads, or two continuous seconds for video ads. This is the Media Rating Council's (MRC) definition of viewability. Note that a single impression that is viewable has two events: a viewable impression and a measurable impression. Each event for the single impression is listed as a separate row. Possible values for this field are: '1' (if the record represents a viewable impression) or '0' (if the record does not represent a viewable impression).", "aggregation_threshold": "NONE"}
]

def update_dsp_views():
    """Update DSP Views data sources"""
    
    print("\n=== Updating DSP Views Data Sources ===\n")
    
    # Update/Insert data sources
    for source in dsp_views_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            if existing.data:
                # Update existing
                result = supabase.table('amc_data_sources').update({
                    'name': source['name'],
                    'description': source['description'],
                    'category': source['category'],
                    'tags': [source.get('table_type')] if source.get('table_type') else [],
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).eq('schema_id', source['schema_id']).execute()
                print(f"✅ Updated data source: {source['schema_id']}")
                data_source_id = existing.data[0]['id']
            else:
                # Insert new
                result = supabase.table('amc_data_sources').insert({
                    'id': str(uuid.uuid4()),
                    'schema_id': source['schema_id'],
                    'name': source['name'],
                    'description': source['description'],
                    'category': source['category'],
                    'tags': [source.get('table_type')] if source.get('table_type') else [],
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).execute()
                print(f"✅ Created data source: {source['schema_id']}")
                data_source_id = result.data[0]['id']
            
            # Note: Field information is stored for reference but not inserted into a separate table
            # as the schema doesn't have a fields table
            print(f"  Documented {len(dsp_views_fields)} fields for {source['schema_id']}")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            continue
    
    print("\n=== DSP Views Update Complete ===")
    
    # Verify the update
    print("\n=== Verification ===")
    for schema_id in ['dsp_views', 'dsp_views_for_audiences']:
        result = supabase.table('amc_data_sources').select('name, description, tags').eq('schema_id', schema_id).execute()
        if result.data:
            print(f"\n{schema_id}:")
            print(f"  Name: {result.data[0]['name']}")
            print(f"  Description: {result.data[0]['description'][:100]}...")
            print(f"  Tags: {result.data[0].get('tags', [])}")

if __name__ == "__main__":
    update_dsp_views()