#!/usr/bin/env python3
"""
Update DSP Impressions data sources in AMC
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
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

# Define the DSP Impressions data sources
dsp_impressions_sources = [
    {
        "schema_id": "dsp_impressions",
        "name": "Amazon DSP Impressions",
        "description": "Analytics table containing records of all impressions delivered to viewers. This table contains the most granular record of every impression delivered, allowing you to query all viewers reached through an Amazon DSP campaign.",
        "category": "DSP",
        "table_type": "Analytics"
    },
    {
        "schema_id": "dsp_impressions_for_audiences",
        "name": "Amazon DSP Impressions for Audiences",
        "description": "Audience table containing records of all impressions delivered to viewers. This table contains the most granular record of every impression delivered, allowing you to query all viewers reached through an Amazon DSP campaign.",
        "category": "DSP",
        "table_type": "Audience"
    }
]

# Define the fields for DSP impressions tables
dsp_impressions_fields = [
    # Dimensions
    {"name": "ad_slot_size", "data_type": "STRING", "field_type": "Dimension", "description": "Ad slot size in which the Amazon DSP ad was served, expressed as width x height in pixels. The dimensions indicate the space allocated for the ad on the page or app where the impression was served. Example values: '300x250', '728x90', '320x50'.", "aggregation_threshold": "LOW"},
    {"name": "advertiser", "data_type": "STRING", "field_type": "Dimension", "description": "Name of the business entity running advertising campaigns on Amazon DSP. Example value: 'Widgets Inc'.", "aggregation_threshold": "LOW"},
    {"name": "advertiser_account_frequency_group_ids", "data_type": "ARRAY", "field_type": "Dimension", "description": "An array of the advertiser-account-level frequency group IDs that were applicable for this impression event. Frequency groups created at the advertiser account level may operate across 1 or more campaigns within that advertiser account. Note that a single impression may be subject to multiple frequency groups.", "aggregation_threshold": "LOW"},
    {"name": "advertiser_country", "data_type": "STRING", "field_type": "Dimension", "description": "Country of the Amazon DSP advertiser. This value is based on the country setting configured in the advertiser's Amazon DSP account. Example value: 'US'.", "aggregation_threshold": "LOW"},
    {"name": "advertiser_id", "data_type": "LONG", "field_type": "Dimension", "description": "ID of the Amazon DSP advertiser associated with the impression event. Example value: '123456789012345'.", "aggregation_threshold": "LOW"},
    {"name": "advertiser_timezone", "data_type": "STRING", "field_type": "Dimension", "description": "Advertiser timezone. This setting aligns with the advertiser timezone configuration in the connected Amazon DSP account. Example value: 'America/New_York'.", "aggregation_threshold": "LOW"},
    {"name": "app_bundle", "data_type": "STRING", "field_type": "Dimension", "description": "The app bundle ID associated with the Amazon DSP impression. App bundles follow different formatting conventions depending on the app store.", "aggregation_threshold": "LOW"},
    {"name": "browser_family", "data_type": "STRING", "field_type": "Dimension", "description": "Browser family used when viewing the Amazon DSP ad. Browser family represents a high-level grouping of web browsers and app contexts through which ads can be served, such as mobile browsers, desktop browsers, and application environments. Example values include: 'Chrome', 'Safari', 'Mobile Safari', 'Android App', 'iOS WebView', and 'Roku App'.", "aggregation_threshold": "LOW"},
    {"name": "campaign", "data_type": "STRING", "field_type": "Dimension", "description": "Name of the Amazon DSP campaign responsible for the impression event. A campaign is a container that groups related advertising efforts with shared objectives, budget, and flight dates. Example value: 'Widgets_Q1_2024_Awareness_Display_US'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_budget_amount", "data_type": "LONG", "field_type": "Dimension", "description": "The total budget allocated to the Amazon DSP campaign, stored in millicents. To convert to dollars/local currency, divide by 100,000 (e.g., 100,000 millicents = $1.00). Refer to the currency_name field for the budget currency. Example value: 100000000.", "aggregation_threshold": "LOW"},
    {"name": "campaign_end_date", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "End date and time of the Amazon DSP campaign in advertiser timezone. Example value: '2025-01-01T23:59:59.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_end_date_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "End date of the Amazon DSP campaign in Coordinated Universal Time (UTC). Example value: '2025-01-01T23:59:59.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_flight_id", "data_type": "LONG", "field_type": "Dimension", "description": "ID of the Amazon DSP campaign flight. A campaign flight represents a scheduled run period for an advertising campaign with defined start and end dates. Example value: '123456789012345'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_id", "data_type": "LONG", "field_type": "Dimension", "description": "The ID of the Amazon DSP campaign responsible for the impression event. In this table, campaign_id and campaign_id_string fields will show the same value for a given event. Example value: '571234567890123456'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_id_string", "data_type": "STRING", "field_type": "Dimension", "description": "The ID of the Amazon DSP campaign responsible for the impression event. In this table, campaign_id and campaign_id_string fields will show the same value for a given event. Example value: '571234567890123456'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_insertion_order_id", "data_type": "STRING", "field_type": "Dimension", "description": "ID of the insertion order associated with the Amazon DSP impression event. An insertion order is a contractual agreement between an advertiser and Amazon Ads that outlines the specific details of a programmatic advertising campaign. Example value: '123456789'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_primary_goal", "data_type": "STRING", "field_type": "Dimension", "description": "Primary goal set for campaign optimization in Amazon DSP. Campaign goals determine how Amazon DSP optimizes delivery and measures success of the campaign. The goal selected during campaign setup influences bidding strategy and campaign optimization. Possible values include: 'ROAS', 'TOTAL_ROAS', 'REACH', 'CPVC', 'COMPLETION_RATE', 'CTR', 'CPC', 'DPVR', 'PAGE_VISIT', 'CPDPV', 'CPA' 'OTHER', and 'NONE'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_sales_type", "data_type": "STRING", "field_type": "Dimension", "description": "Billing classification of the Amazon DSP campaign, which distinguishes billable and non-billable campaigns. Possible values include: 'BILLABLE' and 'BONUS'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_source", "data_type": "STRING", "field_type": "Dimension", "description": "Campaign source.", "aggregation_threshold": "LOW"},
    {"name": "campaign_start_date", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Start date and time of the Amazon DSP campaign in advertiser timezone. The campaign start date determines when a campaign begins serving impressions. Example value: '2025-01-01T00:00:00.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_start_date_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Start date and time of the Amazon DSP campaign in Coordinated Universal Time (UTC). The campaign start date determines when a campaign begins serving impressions. Example value: '2025-01-01T00:00:00.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "campaign_status", "data_type": "STRING", "field_type": "Dimension", "description": "Current status of the Amazon DSP campaign. Campaign status indicates whether a campaign is actively delivering ads, has completed its flight dates, or has been paused by the advertiser. Possible values include: 'ENDED', 'RUNNING', 'ENABLED', 'PAUSED', and 'ADS_NOT_RUNNING'.", "aggregation_threshold": "LOW"},
    {"name": "city_name", "data_type": "STRING", "field_type": "Dimension", "description": "City name where the Amazon DSP impression event occurred, determined by signal available in the auction event. Example value: 'New York'.", "aggregation_threshold": "HIGH"},
    {"name": "creative", "data_type": "STRING", "field_type": "Dimension", "description": "Name of the Amazon DSP creative/ad. A creative represents the actual advertisement shown to customers. Example value: '2025_US_Widgets_Spring_Mobile_320x50'.", "aggregation_threshold": "LOW"},
    {"name": "creative_category", "data_type": "STRING", "field_type": "Dimension", "description": "Category of the Amazon DSP creative/ad. This field categorizes Amazon DSP ads into broad creative format types like display ads and video ads. Possible values include: 'Display', 'Video', and NULL.", "aggregation_threshold": "LOW"},
    {"name": "creative_duration", "data_type": "INTEGER", "field_type": "Dimension", "description": "Duration in seconds of the Amazon DSP creative asset, primarily used for video format ads. This field specifies the length of video creative assets delivered through Amazon DSP campaigns. For non-video creative formats like display ads, this field will be NULL. Example values include: '15', '30', '60', representing video durations in seconds.", "aggregation_threshold": "LOW"},
    {"name": "creative_id", "data_type": "LONG", "field_type": "Dimension", "description": "Unique identifier for the Amazon DSP creative/ad. A ad represents the actual advertisement shown to customers, which could be an image, video, or other ad format. Example value: '591234567890123456'.", "aggregation_threshold": "LOW"},
    {"name": "creative_is_link_in", "data_type": "STRING", "field_type": "Dimension", "description": "Boolean field indicating whether the Amazon DSP creative/ad directs to an Amazon destination (link in) versus an external destination (link out). A link in creative directs users to an Amazon destination like a product detail page, while a link out creative directs users to an external destination like an advertiser's website. Possible values for this field are: 'Y' (creative is link in), 'N' (creative is link out).", "aggregation_threshold": "LOW"},
    {"name": "creative_size", "data_type": "STRING", "field_type": "Dimension", "description": "Dimensions of the Amazon DSP creative/ad (width x height in pixels, or responsive format). Example values: '300x250', '320x50', 'Responsive'.", "aggregation_threshold": "LOW"},
    {"name": "creative_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of creative/ad.", "aggregation_threshold": "LOW"},
    {"name": "currency_iso_code", "data_type": "STRING", "field_type": "Dimension", "description": "Currency ISO code associated with the monetary values in the table. The three-letter currency code follows the ISO 4217 standard format and is determined by the currency setting in the connected Amazon DSP account. Example value: 'USD'.", "aggregation_threshold": "LOW"},
    {"name": "currency_name", "data_type": "STRING", "field_type": "Dimension", "description": "Currency name associated with the monetary values in the table. Currency is determined by the currency setting in the connected Amazon DSP account. Example value: 'Dollar (USA)'.", "aggregation_threshold": "LOW"},
    {"name": "deal_id", "data_type": "STRING", "field_type": "Dimension", "description": "ID of the deal between the publisher and advertiser, for Amazon DSP impressions purchased via private deal (e.g. Private Marketplace or Programmatic Guaranteed deals). Deals represent agreements for access to specific ad inventory with pre-negotiated terms. This field will be NULL for traffic events purchased via open auction. Example value: 'DEAL123456'.", "aggregation_threshold": "LOW"},
    {"name": "deal_name", "data_type": "STRING", "field_type": "Dimension", "description": "Name of the deal between the publisher and advertiser, for Amazon DSP impressions purchased via private deal e.g. Private Marketplace or Programmatic Guaranteed deals. Deals represent agreements for access to specific ad inventory with pre-negotiated terms. This field will be NULL for traffic events purchased via open auction. Example value: 'Widgets_Premium_Video_Deal'.", "aggregation_threshold": "LOW"},
    {"name": "demand_channel", "data_type": "STRING", "field_type": "Dimension", "description": "Demand channel name.", "aggregation_threshold": "VERY_HIGH"},
    {"name": "demand_channel_owner", "data_type": "STRING", "field_type": "Dimension", "description": "Demand channel owner.", "aggregation_threshold": "LOW"},
    {"name": "device_id", "data_type": "STRING", "field_type": "Dimension", "description": "Pseudonymized ID representing the device associated with the Amazon DSP impression event.", "aggregation_threshold": "LOW"},
    {"name": "device_make", "data_type": "STRING", "field_type": "Dimension", "description": "Manufacturer or brand name of the device associated with the Amazon DSP impression event, derived from user-agent in the auction. Values may appear in different formats or capitalizations for the same manufacturer. Example values: 'Apple', 'APPLE', 'Samsung', 'SAMSUNG', 'ROKU', 'Generic', 'UNKNOWN'.", "aggregation_threshold": "LOW"},
    {"name": "device_model", "data_type": "STRING", "field_type": "Dimension", "description": "Model of the device associated with the Amazon DSP impression event, derived from user-agent in the auction. Values may appear in different formats or capitalizations for the same manufacturer. Example values: 'iPhone', 'GALAXY'.", "aggregation_threshold": "LOW"},
    {"name": "device_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of the device associated with the Amazon DSP impression event. Possible values include: 'Tablet', 'Phone', 'TV', 'PC', 'ConnectedDevice', 'Unknown', and NULL.", "aggregation_threshold": "LOW"},
    {"name": "dma_code", "data_type": "STRING", "field_type": "Dimension", "description": "Designated Market Area (DMA) code where the Amazon DSP impression event occurred. DMA codes are geographic regions defined by Nielsen that identify specific broadcast TV markets in the United States. The field uses a standardized format combining \"US-DMA\" prefix with a numeric market identifier. Example value: 'US-DMA518'.", "aggregation_threshold": "LOW"},
    {"name": "entity_id", "data_type": "STRING", "field_type": "Dimension", "description": "ID of the Amazon DSP entity (also known as seat) associated with the impression. An entity represents an Amazon DSP account, within which media is further organized by advertiser and by campaign. Example value: 'ENTITYABC123XYZ789'.", "aggregation_threshold": "NONE"},
    {"name": "environment_type", "data_type": "STRING", "field_type": "Dimension", "description": "Environment where the Amazon DSP impression event occurred. This field distinguishes between web-based environments like desktop or mobile browsers, and app-based environments like mobile apps. If the environment type cannot be determined, this field will be NULL. Possible values include: 'Web', 'App', and NULL.", "aggregation_threshold": "LOW"},
    {"name": "impression_date", "data_type": "DATE", "field_type": "Dimension", "description": "Date of the Amazon DSP impression event in advertiser timezone. Example value: '2025-01-01'.", "aggregation_threshold": "LOW"},
    {"name": "impression_date_utc", "data_type": "DATE", "field_type": "Dimension", "description": "Date of the Amazon DSP impression event in Coordinated Universal Time (UTC). Example value: '2025-01-01'", "aggregation_threshold": "LOW"},
    {"name": "impression_day", "data_type": "INTEGER", "field_type": "Dimension", "description": "Day of month when the Amazon DSP impression event occurred in advertiser timezone. Example value: '1'.", "aggregation_threshold": "MEDIUM"},
    {"name": "impression_day_utc", "data_type": "INTEGER", "field_type": "Dimension", "description": "Day of month when the Amazon DSP impression event occurred in Coordinated Universal Time (UTC). Example value: '1'.", "aggregation_threshold": "LOW"},
    {"name": "impression_dt", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the Amazon DSP impression event in advertiser timezone. Example value: '2025-01-01T12:00:00.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "impression_dt_hour", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the Amazon DSP impression event in advertiser timezone, truncated to hour. Example value: '2025-01-01T12:00:00.000Z'.", "aggregation_threshold": "MEDIUM"},
    {"name": "impression_dt_hour_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the Amazon DSP impression event in Coordinated Universal Time (UTC), truncated to hour. Example value: '2025-01-01T12:00:00.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "impression_dt_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the Amazon DSP impression event in Coordinated Universal Time (UTC). Example value: '2025-01-01T00:00:00.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "impression_hour", "data_type": "INTEGER", "field_type": "Dimension", "description": "Hour of day when the Amazon DSP impression event occurred, in advertiser timezone. Values range from 0-23 representing 24-hour time. Example value: '14' (represents 2:00 PM in 24-hour time).", "aggregation_threshold": "NONE"},
    {"name": "impression_hour_utc", "data_type": "INTEGER", "field_type": "Dimension", "description": "Hour of day when the Amazon DSP impression event occurred, in Coordinated Universal Time (UTC). Values range from 0-23 representing 24-hour time. Example value: '14' (represents 2:00 PM in 24-hour time).", "aggregation_threshold": "LOW"},
    {"name": "is_amazon_owned", "data_type": "BOOLEAN", "field_type": "Dimension", "description": "Boolean value indicating whether or not the Amazon DSP impression appeared on Amazon-owned inventory. Amazon-owned inventory includes media such as Prime Video, IMDb, and Twitch. Possible values for this field are: 'true', 'false'.", "aggregation_threshold": "LOW"},
    {"name": "iso_country_code", "data_type": "STRING", "field_type": "Dimension", "description": "ISO 3166 Alpha-2 country code where the Amazon DSP impression event occurred, based on the user's IP address. Example value: 'US'.", "aggregation_threshold": "LOW"},
    {"name": "iso_state_province_code", "data_type": "STRING", "field_type": "Dimension", "description": "ISO state/province code where the Amazon DSP impression event occurred. The code follows the ISO 3166-2 standard format which combines the country code and state/province subdivision (e.g., 'US-CA' for California, United States). Example value: 'US-CA'.", "aggregation_threshold": "LOW"},
    {"name": "line_item", "data_type": "STRING", "field_type": "Dimension", "description": "Name of the Amazon DSP line item responsible for the impression event. Attributes like ad format and targeting are defined at line item level within a campaign. Example value: 'Widgets - DISPLAY - O&O - RETARGETING'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_budget_amount", "data_type": "LONG", "field_type": "Dimension", "description": "The total budget allocated to the Amazon DSP line item, stored in millicents. To convert to dollars/local currency, divide by 100,000 (e.g., 100,000 millicents = $1.00). Refer to the currency_name field for the budget currency. Example value: '100000000'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_end_date", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "End date and time of the Amazon DSP line item in advertiser timezone. Example value: '2025-01-01T23:59:59.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_end_date_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "End date and time of the Amazon DSP line item in Coordinated Universal Time (UTC). Example value: '2025-01-01T23:59:59.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_id", "data_type": "LONG", "field_type": "Dimension", "description": "ID of the Amazon DSP line item responsible for the impression event. Attributes like ad format and targeting are defined at line item level within a campaign. Example value: '5812345678901234'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_price_type", "data_type": "STRING", "field_type": "Dimension", "description": "Pricing model used for the Amazon DSP line item. Line items can use different pricing models to determine how costs are calculated, with Cost Per Mille (CPM) being a common model where advertisers pay per thousand impressions. Example value: 'CPM'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_start_date", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Start date and time of the Amazon DSP line item in advertiser timezone. Example value: '2025-01-01T23:59:59.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_start_date_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Start date and time of the Amazon DSP line item in Coordinated Universal Time (UTC). Example value: '2025-01-01T23:59:59.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "line_item_status", "data_type": "STRING", "field_type": "Dimension", "description": "Status of the Amazon DSP line item. The status indicates whether the line item is actively delivering ads, has been paused, or has completed its flight. Possible values include: 'ENDED', 'ENABLED', 'RUNNING', 'PAUSED_BY_USER', and 'SUSPENDED'.", "aggregation_threshold": "NONE"},
    {"name": "line_item_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of Amazon DSP line item. Line item types indicate how ads are delivered and optimized. Example values include: 'AAP', 'AAP_DISPLAY', 'AAP_MOBILE', 'AAP_VIDEO_CPM'.", "aggregation_threshold": "LOW"},
    {"name": "manager_account_frequency_group_ids", "data_type": "ARRAY", "field_type": "Dimension", "description": "An array of the manager-account-level frequency group IDs that were applicable for this impression event. Frequency groups created at the manager account level may operate across 1 or more advertisers within that manager account. Note that a single impression may be subject to multiple frequency groups.", "aggregation_threshold": "LOW"},
    {"name": "merchant_id", "data_type": "LONG", "field_type": "Dimension", "description": "Merchant ID.", "aggregation_threshold": "LOW"},
    {"name": "no_3p_trackers", "data_type": "STRING", "field_type": "Dimension", "description": "Boolean value indicating whether the event can be used for audience creation that is third-party tracking enabled (i.e. whether you can serve creative with third-party tracking when running media against the audience). Third-party tracking refers to measurement tags and pixels from external vendors that can be used to measure ad performance. Possible values for this field are: 'true', 'false'.", "aggregation_threshold": "LOW"},
    {"name": "operating_system", "data_type": "STRING", "field_type": "Dimension", "description": "Operating system of the device where the Amazon DSP impression event occurred. Example values: 'iOS', 'Android', 'Windows', 'macOS', 'Roku OS'.", "aggregation_threshold": "LOW"},
    {"name": "os_version", "data_type": "STRING", "field_type": "Dimension", "description": "Operating system version of the device where the Amazon DSP impression event occurred. The version format varies by operating system type. Example value: '17.5.1'.", "aggregation_threshold": "LOW"},
    {"name": "page_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of page where the Amazon DSP impression event occurred. This grain of detail is primarily relevant to impressions served on Amazon sites. Example values: 'Search', 'Detail', 'CustomerReviews'.", "aggregation_threshold": "LOW"},
    {"name": "placement_is_view_aware", "data_type": "BOOLEAN", "field_type": "Dimension", "description": "Boolean value indicating whether or not the Amazon DSP impression occurred in a placement that supports viewability measurement. Possible values for this field are: 'true', 'false'.", "aggregation_threshold": "LOW"},
    {"name": "placement_view_rate", "data_type": "DECIMAL", "field_type": "Dimension", "description": "The view rate of the placement, expressed as a decimal between 0.0 and 1.0. Viewability is measured according to Media Rating Council (MRC) standards, which require 50% of pixels to be in view for at least 1 second for display ads and 2 seconds for video ads. Example value: 0.75", "aggregation_threshold": "HIGH"},
    {"name": "postal_code", "data_type": "STRING", "field_type": "Dimension", "description": "Postal code in which the Amazon DSP impression event occurred, based on the user's IP address. Postal code is also referred to as \"zip code\" in the US. The postal code is prepended with the iso_country_code value (e.g. 'US'). If the country is known, but the postal code is unknown, only the country code will be populated in postal_code. Example value: 'US-12345'.", "aggregation_threshold": "LOW"},
    {"name": "product_line", "data_type": "STRING", "field_type": "Dimension", "description": "Campaign product line.", "aggregation_threshold": "MEDIUM"},
    {"name": "publisher_id", "data_type": "STRING", "field_type": "Dimension", "description": "ID of the publisher where the Amazon DSP impression was served. A publisher is the media owner (such as a website, app, or streaming service owner) that makes advertising inventory available for purchase through Amazon DSP.", "aggregation_threshold": "LOW"},
    {"name": "request_dt", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the request event in advertiser timezone. Example value: '2025-01-01T00:00:00.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "request_dt_hour", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the request event in advertiser timezone, truncated to hour. Example value: '2025-01-01T12:00:00.000Z'.", "aggregation_threshold": "MEDIUM"},
    {"name": "request_dt_hour_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the request event in Coordinated Universal Time (UTC), truncated to hour. Example value: '2025-01-01T12:00:00.000Z'.", "aggregation_threshold": "VERY_HIGH"},
    {"name": "request_dt_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the request event in Coordinated Universal Time (UTC). Example value: '2025-01-01T00:00:00.000Z'.", "aggregation_threshold": "LOW"},
    {"name": "request_tag", "data_type": "STRING", "field_type": "Dimension", "description": "ID that connects related impression, view, click, and conversion events. For example, if an impression served has a request_tag value of 'X', related conversion events will have have an impression_id value of 'X'. While this occurs infrequently, there are sometimes duplicate request_tag values. As a result, it is not recommended to use request_tag as a JOIN key without first grouping by it. Rather, it is a best practice to first consider using UNION ALL in a query instead of joining based on the request_tag to combine data sources. For insights that involve user-level ad exposure across tables, use user_id instead.", "aggregation_threshold": "VERY_HIGH"},
    {"name": "site", "data_type": "STRING", "field_type": "Dimension", "description": "The site descriptor where the Amazon DSP impression event occurred. A site can be any digital property where ads are served, including websites, mobile apps, and streaming platforms.", "aggregation_threshold": "LOW"},
    {"name": "slot_position", "data_type": "STRING", "field_type": "Dimension", "description": "Position of the ad on the page relative to the initial viewport. Above the fold (ATF) refers to the portion of the webpage visible without scrolling, while below the fold (BTF) refers to the portion that requires scrolling to view. This dimension helps measure where ad impressions were served on the page. Possible values include: 'ATF', 'BTF', and 'UNKNOWN'.", "aggregation_threshold": "LOW"},
    {"name": "supply_source", "data_type": "STRING", "field_type": "Dimension", "description": "Supply source from which the Amazon DSP impression was purchased. Supply sources can include Amazon-owned properties (like Amazon.com and Twitch), Amazon Publisher Services inventory, and third-party partners. Example values: 'AMAZON.COM', 'TWITCH WEB VIDEO', 'PUBMATIC WEB DISPLAY'.", "aggregation_threshold": "LOW"},
    {"name": "supply_source_id", "data_type": "LONG", "field_type": "Dimension", "description": "ID of the supply source from which the Amazon DSP impression was purchased. Supply sources can include Amazon-owned properties (like Amazon.com and Twitch), Amazon Publisher Services inventory, and third-party partners.", "aggregation_threshold": "LOW"},
    {"name": "supply_source_is_view_aware", "data_type": "BOOLEAN", "field_type": "Dimension", "description": "Boolean value indicating whether or not the supply source can measure viewability. Possible values for this field are: 'true', 'false'.", "aggregation_threshold": "NONE"},
    {"name": "supply_source_view_rate", "data_type": "DECIMAL", "field_type": "Dimension", "description": "The view rate of the supply source, expressed as a decimal between 0.0 and 1.0. View rate represents the percentage of impressions that met viewability standards, which require at least 50% of the ad's pixels to be visible for a minimum of one second for display ads or two seconds for video ads. Example value: '0.75'.", "aggregation_threshold": "NONE"},
    {"name": "user_behavior_segment_ids", "data_type": "ARRAY", "field_type": "Metric", "description": "Array of behavior segment IDs that the user belonged to at the time of impression. Each ID in the array corresponds to a distinct audience segment. Example value: '[123456, 234567, 345678]'.", "aggregation_threshold": "MEDIUM"},
    {"name": "user_id", "data_type": "STRING", "field_type": "Dimension", "description": "Pseudonymous identifier that connects user activity across different events. The field can contain ad user IDs (representing Amazon accounts), device IDs, or browser IDs. NULL values appear when Amazon Ads is unable to resolve an identifier for an event. The field has a VERY_HIGH aggregation threshold, meaning it cannot be included in final SELECT statements but can be used within Common Table Expressions (CTEs) for aggregation purposes like COUNT(DISTINCT user_id).", "aggregation_threshold": "VERY_HIGH"},
    {"name": "user_id_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of user ID value. AMC includes different types of user ID values, depending on whether the value represents a resolved Amazon account, a device, or a browser cookie. If Amazon Ads is unable to determine or provide an ID of any kind for an impression event, the 'user_id' and 'user_id_type' values for that record will be NULL. Possible values include: 'adUserId', 'sisDeviceId', 'adBrowserId', and NULL.", "aggregation_threshold": "LOW"},
    
    # Metrics
    {"name": "audience_fee", "data_type": "LONG", "field_type": "Metric", "description": "The fee (in microcents) that Amazon DSP charges to customers to utilize Amazon audiences. Audience fees are typically charged on a cost-per-thousand impressions (CPM) basis when using audience segments for campaign targeting. To convert to dollars/your currency, divide by 100,000,000 (e.g., 100,000,000 microcents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: '25000'.", "aggregation_threshold": "NONE"},
    {"name": "bid_price", "data_type": "LONG", "field_type": "Metric", "description": "The bid price (in microcents) for the Amazon DSP impression. To convert to dollars/your currency, divide by 100,000,000 (e.g., 500,000 microcents = $0.005). Refer to the currency_name field for the currency in which the impression was purchased. Example value: '500000'.", "aggregation_threshold": "MEDIUM"},
    {"name": "impression_cost", "data_type": "LONG", "field_type": "Metric", "description": "The cost of the Amazon DSP impression event in millicents (where 100,000 millicents = $1.00). To convert to dollars/your currency, divide by 100,000. Refer to the currency_name field for the currency in which the impression was purchased. Example value: 300 (equivalent to $0.003).", "aggregation_threshold": "LOW"},
    {"name": "impressions", "data_type": "LONG", "field_type": "Metric", "description": "Count of Amazon DSP impressions. When querying this table, remember that each record represents one Amazon DSP impression, so you can use this field to calculate accurate impression totals. Since this table only includes impression events, this field will always have a value of '1' (the event was an impression event).", "aggregation_threshold": "LOW"},
    {"name": "managed_service_fee", "data_type": "LONG", "field_type": "Metric", "description": "The fee (in microcents) that Amazon DSP charges to customers for campaign management services provided by Amazon's in-house service team. The managed service fee is calculated as a percentage of the supply cost. To convert from microcents to dollars/your currency, divide by 100,000,000 (e.g., 5,000,000 microcents = $0.05). Refer to the currency_name field for the currency in which the impression was purchased. Example value: '5000000'.", "aggregation_threshold": "LOW"},
    {"name": "matched_behavior_segment_ids", "data_type": "ARRAY", "field_type": "Metric", "description": "Array of behavior segment IDs that were both targeted by the Amazon DSP line item and matched to the user at the time of impression. Each ID in the array corresponds to a distinct audience segment. Example value: '[123456, 234567, 345678]'.", "aggregation_threshold": "LOW"},
    {"name": "ocm_fee", "data_type": "LONG", "field_type": "Metric", "description": "The fee (in microcents) that Amazon DSP charges for the use of omnichannel measurement studies. The omnichannel metrics fee is calculated as a percentage of the supply cost. To convert to dollars, divide by 100,000,000 (e.g., 500,000 microcents = $0.005). Refer to the currency_name field for the currency in which the impression was purchased. Example value: 500000.", "aggregation_threshold": "LOW"},
    {"name": "platform_fee", "data_type": "LONG", "field_type": "Metric", "description": "The fee (in microcents) that Amazon DSP charges to customers to access and use Amazon DSP. The platform fee (also known as the technology fee or console fee in other contexts) is calculated as a percentage of the supply cost. To convert to dollars/your currency, divide by 100,000,000 (e.g., 100,000,000 microcents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: '25000'.", "aggregation_threshold": "LOW"},
    {"name": "segment_marketplace_id", "data_type": "INTEGER", "field_type": "Metric", "description": "ID of the marketplace associated with an audience segment. A marketplace represents a specific region where advertising can be delivered.", "aggregation_threshold": "LOW"},
    {"name": "supply_cost", "data_type": "LONG", "field_type": "Metric", "description": "The cost (in microcents) that Amazon DSP pays a publisher or publisher ad tech platform (such as an SSP or exchange) for an impression. To convert supply_cost to dollars/your local currency, divide by 100,000,000 (e.g., 100,000,000 microcents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: '5000'.", "aggregation_threshold": "LOW"},
    {"name": "third_party_fees", "data_type": "LONG", "field_type": "Metric", "description": "The sum of all third-party fees charged for the impression (in microcents). Third-party fees represent charges from external data and technology providers used in the delivery and measurement of the impression. Since this field is in microcents, divide by 100,000,000 to convert to dollars/your local currency (e.g., 500,000,000 microcents = $5.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: '25000'.", "aggregation_threshold": "LOW"},
    {"name": "total_cost", "data_type": "LONG", "field_type": "Metric", "description": "The total cost of the Amazon DSP impression in millicents, inclusive of all applicable fees (supply cost, audience fees, platform fees, and third-party fees). Since this field is in millicents, divide by 100,000 to convert to dollars/your local currency (e.g., 100,000 millicents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: '300'.", "aggregation_threshold": "VERY_HIGH"}
]

def update_dsp_impressions():
    """Update DSP Impressions data sources"""
    
    print("\n=== Updating DSP Impressions Data Sources ===\n")
    
    # Update/Insert data sources
    for source in dsp_impressions_sources:
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
                    'updated_at': datetime.utcnow().isoformat()
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
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }).execute()
                print(f"✅ Created data source: {source['schema_id']}")
                data_source_id = result.data[0]['id']
            
            # Delete existing fields for this data source
            supabase.table('amc_schema_fields').delete().eq('data_source_id', data_source_id).execute()
            print(f"  Cleared existing fields for {source['schema_id']}")
            
            # Insert fields
            fields_to_insert = []
            for field in dsp_impressions_fields:
                fields_to_insert.append({
                    'id': str(uuid.uuid4()),
                    'data_source_id': data_source_id,
                    'field_name': field['name'],
                    'data_type': field['data_type'],
                    'dimension_or_metric': field['field_type'],
                    'description': field['description'],
                    'aggregation_threshold': field.get('aggregation_threshold')
                })
            
            # Insert in batches of 50 to avoid size limits
            batch_size = 50
            for i in range(0, len(fields_to_insert), batch_size):
                batch = fields_to_insert[i:i+batch_size]
                supabase.table('amc_schema_fields').insert(batch).execute()
                print(f"  Inserted {len(batch)} fields (batch {i//batch_size + 1})")
            
            print(f"✅ Inserted {len(fields_to_insert)} fields for {source['schema_id']}\n")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            continue
    
    print("\n=== DSP Impressions Update Complete ===")
    
    # Verify the update
    print("\n=== Verification ===")
    for schema_id in ['dsp_impressions', 'dsp_impressions_for_audiences']:
        result = supabase.table('amc_data_sources').select('name, description').eq('schema_id', schema_id).execute()
        if result.data:
            print(f"\n{schema_id}:")
            print(f"  Name: {result.data[0]['name']}")
            print(f"  Description: {result.data[0]['description'][:100]}...")
            
            # Count fields
            ds_result = supabase.table('amc_data_sources').select('id').eq('schema_id', schema_id).execute()
            if ds_result.data:
                fields = supabase.table('amc_schema_fields').select('id').eq('data_source_id', ds_result.data[0]['id']).execute()
                print(f"  Field count: {len(fields.data)}")

if __name__ == "__main__":
    update_dsp_impressions()