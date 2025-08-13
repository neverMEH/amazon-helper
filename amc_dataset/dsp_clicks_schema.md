# dsp_clicks Data Source Schema

## Overview

**Data Source:** `dsp_clicks`

The dsp_clicks table is a subset of the dsp_impressions information that captures the details impressions that were clicked and the associated click related information.

## Table Schema

| Name | Data Type | Metric / Dimension | Description | Aggregation Threshold |
|------|-----------|-------------------|-------------|----------------------|
| advertiser | STRING | Dimension | Name of the business entity running advertising campaigns on Amazon DSP. Example value: 'Widgets Inc'. | LOW |
| advertiser_account_frequency_group_ids | ARRAY | Dimension | An array of the advertiser-account-level frequency group IDs that were applicable for this impression event. Frequency groups created at the advertiser account level may operate across 1 or more campaigns within that advertiser account. Note that a single impression may be subject to multiple frequency groups. | LOW |
| advertiser_country | STRING | Dimension | Country of the Amazon DSP advertiser. This value is based on the country setting configured in the advertiser's Amazon DSP account. Example value: 'US'. | LOW |
| advertiser_id | LONG | Dimension | ID of the Amazon DSP advertiser associated with the click event. Example value: '123456789012345'. | LOW |
| advertiser_timezone | STRING | Dimension | Advertiser timezone. This setting aligns with the advertiser timezone configuration in the connected Amazon DSP account. Example value: 'America/New_York'. | LOW |
| ad_slot_size | STRING | Dimension | Ad slot size in which the Amazon DSP ad was served, expressed as width x height in pixels. The dimensions indicate the space allocated for the ad on the page or app where the impression was served. Example values: '300x250', '728x90', '320x50'. | LOW |
| app_bundle | STRING | Dimension | The app bundle ID associated with the Amazon DSP click event. App bundles follow different formatting conventions depending on the app store. | LOW |
| audience_fee | LONG | Metric | The fee (in microcents) that Amazon DSP charges to customers to utilize Amazon audiences. Audience fees are typically charged on a cost-per-thousand impressions (CPM) basis when using audience segments for campaign targeting. To convert to dollars/your currency, divide by 100,000,000 (e.g., 100,000,000 microcents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: '25000'. | NONE |
| bid_price | LONG | Metric | The bid price (in microcents) for the Amazon DSP impression. To convert to dollars/your currency, divide by 100,000,000 (e.g., 500,000 microcents = $0.005). Refer to the currency_name field for the currency in which the impression was purchased. Example value: '500000'. | MEDIUM |
| browser_family | STRING | Dimension | Browser family used when viewing the Amazon DSP ad. Browser family represents a high-level grouping of web browsers and app contexts through which ads can be served, such as mobile browsers, desktop browsers, and application environments. Example values include: 'Chrome', 'Safari', 'Mobile Safari', 'Android App', 'iOS WebView', and 'Roku App'. | LOW |
| campaign | STRING | Dimension | Name of the Amazon DSP campaign responsible for the click event. A campaign is a container that groups related advertising efforts with shared objectives, budget, and flight dates. Example value: 'Widgets_Q1_2024_Awareness_Display_US'. | LOW |
| campaign_budget_amount | LONG | Dimension | The total budget allocated to the Amazon DSP campaign, stored in millicents. To convert to dollars/local currency, divide by 100,000 (e.g., 100,000 millicents = $1.00). Refer to the currency_name field for the budget currency. Example value: 100000000. | LOW |
| campaign_end_date | TIMESTAMP | Dimension | End date and time of the Amazon DSP campaign in advertiser timezone. Example value: '2025-01-01T23:59:59.000Z'. | LOW |
| campaign_end_date_utc | TIMESTAMP | Dimension | End date of the Amazon DSP campaign in Coordinated Universal Time (UTC). Example value: '2025-01-01T23:59:59.000Z'. | LOW |
| campaign_flight_id | LONG | Dimension | ID of the Amazon DSP campaign flight. A campaign flight represents a scheduled run period for an advertising campaign with defined start and end dates. Example value: '123456789012345'. | LOW |
| campaign_id | LONG | Dimension | The ID of the Amazon DSP campaign responsible for the click event. In this table, campaign_id and campaign_id_string fields will show the same value for a given event. Example value: '571234567890123456'. | LOW |
| campaign_id_string | STRING | Dimension | The ID of the Amazon DSP campaign responsible for the click event. In this table, campaign_id and campaign_id_string fields will show the same value for a given event. Example value: '571234567890123456'. | LOW |
| campaign_insertion_order_id | STRING | Dimension | ID of the insertion order associated with the Amazon DSP click event. An insertion order is a contractual agreement between an advertiser and Amazon Ads that outlines the specific details of a programmatic advertising campaign. Example value: '123456789'. | LOW |
| campaign_primary_goal | STRING | Dimension | Primary goal set for campaign optimization in Amazon DSP. Campaign goals determine how Amazon DSP optimizes delivery and measures success of the campaign. The goal selected during campaign setup influences bidding strategy and campaign optimization. Example values include: 'ROAS', 'TOTAL_ROAS', 'REACH', 'CPVC', 'COMPLETION_RATE', 'CTR', 'CPC', 'DPVR', 'PAGE_VISIT', 'CPDPV', 'CPA' 'OTHER', and 'NONE'. | LOW |
| campaign_sales_type | STRING | Dimension | Billing classification of the Amazon DSP campaign, which distinguishes billable and non-billable campaigns. Example values include: 'BILLABLE' and 'BONUS'. | LOW |
| campaign_source | STRING | Dimension | Campaign source. | LOW |
| campaign_start_date | TIMESTAMP | Dimension | Start date and time of the Amazon DSP campaign in advertiser timezone. The campaign start date determines when a campaign begins serving impressions. Example value: '2025-01-01T00:00:00.000Z'. | LOW |
| campaign_start_date_utc | TIMESTAMP | Dimension | Start date and time of the Amazon DSP campaign in Coordinated Universal Time (UTC). The campaign start date determines when a campaign begins serving impressions. Example value: '2025-01-01T00:00:00.000Z'. | LOW |
| campaign_status | STRING | Dimension | Current status of the Amazon DSP campaign. Campaign status indicates whether a campaign is actively delivering ads, has completed its flight dates, or has been paused by the advertiser. Example values include: 'ENDED', 'RUNNING', 'ENABLED', 'PAUSED', and 'ADS_NOT_RUNNING'. | LOW |
| city_name | STRING | Dimension | City name where the Amazon DSP click event occurred, determined by signal available in the auction event. Example value: 'New York'. | HIGH |
| clicks | LONG | Metric | Count of Amazon DSP clicks. When querying this table, remember that each record represents one Amazon DSP click, so you can use this field to calculate accurate click totals. Since this table only includes click events, this field will always have a value of '1' (the event was a click event). | LOW |
| click_cost | LONG | Metric | Click cost (in millicents). To convert to dollars/local currency, divide by 100,000 (e.g., 100,000 millicents = $1.00). Refer to the currency_name field for the currency in which the click cost is reported. Example value: 300 (equivalent to $0.003). | MEDIUM |
| click_date | DATE | Dimension | Date of the Amazon DSP click event in advertiser timezone. This field will be populated for conversion events that are attributed to an ad view. Example value: '2025-01-01'. | LOW |
| click_date_utc | DATE | Dimension | Date of the Amazon DSP click event in Coordinated Universal Time (UTC). This field will be populated for conversion events that are attributed to an ad view. Example value: '2025-01-01' | LOW |
| click_day | INTEGER | Dimension | Day of month when the Amazon DSP click event occurred in advertiser timezone. Example value: '1'. | LOW |
| click_day_utc | INTEGER | Dimension | Day of month when the Amazon DSP click event occurred in Coordinated Universal Time (UTC). Example value: '1'. | LOW |
| click_dt | TIMESTAMP | Dimension | Timestamp of the Amazon DSP click event in advertiser timezone. This field will be populated for conversion events that are attributed to an ad view. Example value: '2025-01-01T12:00:00.000Z'. | MEDIUM |
| click_dt_hour | TIMESTAMP | Dimension | Timestamp of the Amazon DSP click event in advertiser timezone, truncated to hour. This field will be populated for conversion events that are attributed to an ad view. Example value: '2025-01-01T12:00:00.000Z'. | LOW |
| click_dt_hour_utc | TIMESTAMP | Dimension | Timestamp of the Amazon DSP click event in Coordinated Universal Time (UTC), truncated to hour. This field will be populated for conversion events that are attributed to an ad view. Example value: '2025-01-01T12:00:00.000Z'. | LOW |
| click_dt_utc | TIMESTAMP | Dimension | Timestamp of the Amazon DSP click event in Coordinated Universal Time (UTC). This field will be populated for conversion events that are attributed to an ad view. Example value: '2025-01-01T00:00:00.000Z'. | MEDIUM |
| click_hour | INTEGER | Dimension | Hour of day when the Amazon DSP click event occurred, in advertiser timezone. Values range from 0-23 representing 24-hour time. Example value: '14' (represents 2:00 PM in 24-hour time). | LOW |
| click_hour_utc | INTEGER | Dimension | Hour of day when the Amazon DSP click event occurred, in Coordinated Universal Time (UTC). Values range from 0-23 representing 24-hour time. Example value: '14' (represents 2:00 PM in 24-hour time). | LOW |
| creative | STRING | Dimension | Name of the Amazon DSP creative/ad. A creative represents the actual advertisement shown to customers. Example value: '2025_US_Widgets_Spring_Mobile_320x50'. | LOW |
| creative_category | STRING | Dimension | Category of the Amazon DSP creative/ad. This field categorizes Amazon DSP ads into broad creative format types like display ads and video ads. Possible values include: 'Display', 'Video', and NULL. | LOW |
| creative_duration | INTEGER | Dimension | Duration in seconds of the Amazon DSP creative asset, primarily used for video format ads. This field specifies the length of video creative assets delivered through Amazon DSP campaigns. For non-video creative formats like display ads, this field will be NULL. Example values include: '15', '30', '60', representing video durations in seconds. | LOW |
| creative_id | LONG | Dimension | Unique identifier for the Amazon DSP creative/ad. A ad represents the actual advertisement shown to customers, which could be an image, video, or other ad format. Example value: '591234567890123456'. | LOW |
| creative_is_link_in | STRING | Dimension | Boolean field indicating whether the Amazon DSP creative/ad directs to an Amazon destination (link in) versus an external destination (link out). A link in creative directs users to an Amazon destination like a product detail page, while a link out creative directs users to an external destination like an advertiser's website. Example values for this field are: 'Y' (creative is link in), 'N' (creative is link out). | LOW |
| creative_size | STRING | Dimension | Dimensions of the Amazon DSP creative/ad (width x height in pixels, or responsive format). Example values: '300x250', '320x50', 'Responsive'. | LOW |
| creative_type | STRING | Dimension | Type of creative/ad. | LOW |
| currency_iso_code | STRING | Dimension | Currency ISO code associated with the monetary values in the table. The three-letter currency code follows the ISO 4217 standard format and is determined by the currency setting in the connected Amazon DSP account. Example value: 'USD'. | LOW |
| currency_name | STRING | Dimension | Currency name associated with the monetary values in the table. Currency is determined by the currency setting in the connected Amazon DSP account. Example value: 'Dollar (USA)'. | LOW |
| deal_id | STRING | Dimension | ID of the deal between the publisher and advertiser, for Amazon DSP impressions purchased via private deal (e.g. Private Marketplace or Programmatic Guaranteed deals). Deals represent agreements for access to specific ad inventory with pre-negotiated terms. This field will be NULL for traffic events purchased via open aution. Example value: 'DEAL123456'. | LOW |
| deal_name | STRING | Dimension | Name of the deal between the publisher and advertiser, for Amazon DSP impressions purchased via private deal e.g. Private Marketplace or Programmatic Guaranteed deals). Deals represent agreements for access to specific ad inventory with pre-negotiated terms. This field will be NULL for traffic events purchased via open aution. versus open auction inventory. Example value: 'Widgets_Premium_Video_Deal'. | LOW |
| demand_channel | STRING | Dimension | Demand channel name. | LOW |
| demand_channel_owner | STRING | Dimension | Demand channel owner. | LOW |
| device_id | STRING | Dimension | Pseudonymized ID representing the device associated with the Amazon DSP click event. | VERY_HIGH |
| device_make | STRING | Dimension | Manufacturer or brand name of the device associated with the Amazon DSP click event, derived from user-agent in the auction. Values may appear in different formats or capitalizations for the same manufacturer. Example values: 'Apple', 'APPLE', 'Samsung', 'SAMSUNG', 'ROKU', 'Generic', 'UNKNOWN'. | LOW |
| device_model | STRING | Dimension | Model of the device associated with the Amazon DSP click event, derived from user-agent in the auction. Values may appear in different formats or capitalizations for the same manufacturer. Example values: 'iPhone', 'GALAXY'. | LOW |
| device_type | STRING | Dimension | Type of the device associated with the Amazon DSP click event. Possible values include: 'Tablet', 'Phone', 'TV', 'PC', 'ConnectedDevice', 'Unknown', and NULL. | LOW |
| dma_code | STRING | Dimension | Designated Market Area (DMA) code where the Amazon DSP click event occurred. DMA codes are geographic regions defined by Nielsen that identify specific broadcast TV markets in the United States. The field uses a standardized format combining "US-DMA" prefix with a numeric market identifier. Example value: 'US-DMA518'. | LOW |
| entity_id | STRING | Dimension | ID of the Amazon DSP entity (also known as seat) associated with the click. An entity represents an Amazon DSP account, within which media is further organized by advertiser and by campaign. Example value: 'ENTITYABC123XYZ789'. | LOW |
| environment_type | STRING | Dimension | Environment where the Amazon DSP click event occurred. This field distinguishes between web-based environments like desktop or mobile browsers, and app-based environments like mobile apps. If the environment type cannot be determined, this field will be NULL. Example values include: 'Web', 'App', and NULL. | LOW |
| impression_date | DATE | Dimension | Date of the Amazon DSP impression event in advertiser timezone. Example value: '2025-01-01'. | LOW |
| impression_date_utc | DATE | Dimension | Date of the Amazon DSP impression event in Coordinated Universal Time (UTC). Example value: '2025-01-01' | LOW |
| impression_day | INTEGER | Dimension | Day of month when the Amazon DSP impression event occurred in advertiser timezone. Example value: '1'. | LOW |
| impression_day_utc | INTEGER | Dimension | Day of month when the Amazon DSP impression event occurred in Coordinated Universal Time (UTC). Example value: '1'. | LOW |
| impression_dt | TIMESTAMP | Dimension | Timestamp of the Amazon DSP impression event in advertiser timezone. Example value: '2025-01-01T12:00:00.000Z'. | MEDIUM |
| impression_dt_hour | TIMESTAMP | Dimension | Timestamp of the Amazon DSP impression event in advertiser timezone, truncated to hour. Example value: '2025-01-01T12:00:00.000Z'. | LOW |
| impression_dt_hour_utc | TIMESTAMP | Dimension | Timestamp of the Amazon DSP impression event in Coordinated Universal Time (UTC), truncated to hour. Example value: '2025-01-01T12:00:00.000Z'. | LOW |
| impression_dt_utc | TIMESTAMP | Dimension | Timestamp of the Amazon DSP impression event in Coordinated Universal Time (UTC). Example value: '2025-01-01T00:00:00.000Z'. | MEDIUM |
| impression_hour | INTEGER | Dimension | Hour of day when the Amazon DSP impression event occurred, in advertiser timezone. Values range from 0-23 representing 24-hour time. Example value: '14' (represents 2:00 PM in 24-hour time). | LOW |
| impression_hour_utc | INTEGER | Dimension | Hour of day when the Amazon DSP impression event occurred, in Coordinated Universal Time (UTC). Values range from 0-23 representing 24-hour time. Example value: '14' (represents 2:00 PM in 24-hour time). | LOW |
| iso_country_code | STRING | Dimension | ISO 3166 Alpha-2 country code where the Amazon DSP click event occurred, based on the user's IP address. Example value: 'US'. | LOW |
| iso_state_province_code | STRING | Dimension | ISO state/province code where the Amazon DSP click event occurred. The code follows the ISO 3166-2 standard format which combines the country code and state/province subdivision (e.g., 'US-CA' for California, United States). Example value: 'US-CA'. | LOW |
| is_amazon_owned | BOOLEAN | Dimension | Boolean value indicating whether or not the Amazon DSP click occurred on Amazon-owned inventory. Amazon-owned inventory includes media such as Prime Video, IMDb, and Twitch. Example values for this field are: 'true', 'false'. | LOW |
| line_item | STRING | Dimension | Name of the Amazon DSP line item responsible for the click event. Attributes like ad format and targeting are defined at line item level within a campaign. Example value: 'Widgets - DISPLAY - O&O - RETARGETING'. | LOW |
| line_item_budget_amount | LONG | Dimension | The total budget allocated to the Amazon DSP line item, stored in millicents. To convert to dollars/local currency, divide by 100,000 (e.g., 100,000 millicents = $1.00). Refer to the currency_name field for the budget currency. Example value: '100000000'. | LOW |
| line_item_end_date | TIMESTAMP | Dimension | End date and time of the Amazon DSP line item in advertiser timezone. Example value: '2025-01-01T23:59:59.000Z'. | LOW |
| line_item_end_date_utc | TIMESTAMP | Dimension | End date and time of the line item in Coordinated Universal Time (UTC). Example value: '2025-01-01T23:59:59.000Z'. | LOW |
| line_item_id | LONG | Dimension | ID of the Amazon DSP line item responsible for the click event. Attributes like ad format and targeting are defined at line item level within a campaign. Example value: '5812345678901234'. | LOW |
| line_item_price_type | STRING | Dimension | Pricing model used for the Amazon DSP line item. Line items can use different pricing models to determine how costs are calculated, with Cost Per Mille (CPM) being a common model where advertisers pay per thousand impressions. Example value: 'CPM'. | LOW |
| line_item_start_date | TIMESTAMP | Dimension | Start date and time of the Amazon DSP line item in advertiser timezone. Example value: '2025-01-01T23:59:59.000Z'. | LOW |
| line_item_start_date_utc | TIMESTAMP | Dimension | Start date and time of the Amazon DSP line item in Coordinated Universal Time (UTC). Example value: '2025-01-01T23:59:59.000Z'. | LOW |
| line_item_status | STRING | Dimension | Status of the Amazon DSP line item. The status indicates whether the line item is actively delivering ads, has been paused, or has completed its flight. Example values include: 'ENDED', 'ENABLED', 'RUNNING', 'PAUSED_BY_USER', and 'SUSPENDED'. | LOW |
| line_item_type | STRING | Dimension | Type of Amazon DSP line item. Line item types indicate how ads are delivered and optimized. Example values include: 'AAP', 'AAP_DISPLAY', 'AAP_MOBILE', 'AAP_VIDEO_CPM'. | LOW |
| manager_account_frequency_group_ids | ARRAY | Dimension | An array of the manager-account-level frequency group IDs that were applicable for this impression event. Frequency groups created at the manager account level may operate across 1 or more advertisers within that manager account. Note that a single impression may be subject to multiple frequency groups. | LOW |
| merchant_id | LONG | Dimension | Merchant ID. | LOW |
| no_3p_trackers | BOOLEAN | Dimension | Boolean value indicating whether the event can be used for audience creation that is third-party tracking enabled (i.e. whether you can serve creative with third-party tracking when running media against the audience). Third-party tracking refers to measurement tags and pixels from external vendors that can be used to measure ad performance. Example values for this field are: 'true', 'false'. | NONE |
| operating_system | STRING | Dimension | Operating system of the device where the Amazon DSP click event occurred. Example values: 'iOS', 'Android', 'Windows', 'macOS', 'Roku OS'. | LOW |
| os_version | STRING | Dimension | Operating system version of the device where the Amazon DSP click event occurred. The version format varies by operating system type. Example value: '17.5.1'. | LOW |
| page_type | STRING | Dimension | Type of page where the Amazon DSP click event occurred. This grain of detail is primarily relevant to impressions served on Amazon sites. Example values: 'Search', 'Detail', 'CustomerReviews'. | LOW |
| platform_fee | LONG | Metric | The fee (in microcents) that Amazon DSP charges to customers to access and use Amazon DSP. The platform fee (also known as the technology fee or console fee in other contexts) is calculated as a percentage of the supply cost. To convert to dollars/your currency, divide by 100,000,000 (e.g., 100,000,000 microcents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: '25000'. | LOW |
| postal_code | STRING | Dimension | Postal code in which the Amazon DSP click event occurred, based on the user's IP address. Postal code is also referred to as "zip code" in the US. The postal code is prepended with the iso_country_code value (e.g. 'US'). If the country is known, but the postal code is unknown, only the country code will be populated in postal_code. Example value: 'US-12345'. | HIGH |
| product_line | STRING | Dimension | Campaign product line. | LOW |
| publisher_id | STRING | Dimension | ID of the publisher on which the Amazon DSP click event occurred. A publisher is the media owner (such as a website, app, or streaming service owner) that makes advertising inventory available for purchase through Amazon DSP. | LOW |
| request_dt | TIMESTAMP | Dimension | Timestamp of the request event in advertiser timezone. Example value: '2025-01-01T00:00:00.000Z'. | MEDIUM |
| request_dt_hour | TIMESTAMP | Dimension | Timestamp of the request event in advertiser timezone, truncated to hour. Example value: '2025-01-01T12:00:00.000Z'. | LOW |
| request_dt_hour_utc | TIMESTAMP | Dimension | Timestamp of the request event in Coordinated Universal Time (UTC), truncated to hour. Example value: '2025-01-01T12:00:00.000Z'. | LOW |
| request_dt_utc | TIMESTAMP | Dimension | Timestamp of the request event in Coordinated Universal Time (UTC). Example value: '2025-01-01T00:00:00.000Z'. | MEDIUM |
| request_tag | STRING | Dimension | ID that connects related impression, view, click, and conversion events. For example, if an impression served has a request_tag value of 'X', related conversion events will have have an impression_id value of 'X'. While this occurs infrequently, there are sometimes duplicate request_tag values. As a result, it is not recommended to use request_tag as a JOIN key without first grouping by it. Rather, it is a best practice to first consider using UNION ALL in a query instead of joining based on the request_tag to combine data sources. For insights that involve user-level ad exposure across tables, use user_id instead. | VERY_HIGH |
| site | STRING | Dimension | The site descriptor where the Amazon DSP click event occurred. A site can be any digital property where ads are served, including websites, mobile apps, and streaming platforms. | LOW |
| slot_position | LONG | Metric | Position of the ad on the page relative to the initial viewport. Above the fold (ATF) refers to the portion of the webpage visible without scrolling, while below the fold (BTF) refers to the portion that requires scrolling to view. This dimension helps measure where ad impressions were served on the page. Possible values include: 'ATF', 'BTF', and 'UNKNOWN'. | LOW |
| supply_cost | STRING | Dimension | The cost (in microcents) that Amazon DSP pays a publisher or publisher ad tech platform (such as an SSP or exchange) for an impression. To convert supply_cost to dollars/your local currency, divide by 100,000,000 (e.g., 100,000,000 microcents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: '5000'. | LOW |
| supply_source | STRING | Dimension | Supply source from which the Amazon DSP impression was purchased. Supply sources can include Amazon-owned properties (like Amazon.com and Twitch), Amazon Publisher Services inventory, and third-party partners. Example values: 'AMAZON.COM', 'TWITCH WEB VIDEO', 'PUBMATIC WEB DISPLAY'. | LOW |
| supply_source_id | LONG | Dimension | ID of the supply source from which the Amazon DSP impression was purchased. Supply sources can include Amazon-owned properties (like Amazon.com and Twitch), Amazon Publisher Services inventory, and third-party partners. | LOW |
| user_id | STRING | Dimension | Pseudonymous identifier that connects user activity across different events. The field can contain ad user IDs (representing Amazon accounts), device IDs, or browser IDs. NULL values appear when Amazon Ads is unable to resolve an identifier for an event. The field has a VERY_HIGH aggregation threshold, meaning it cannot be included in final SELECT statements but can be used within Common Table Expressions (CTEs) for aggregation purposes like COUNT(DISTINCT user_id). | VERY_HIGH |
| user_id_type | STRING | Dimension | Type of user ID value. AMC includes different types of user ID values, depending on whether the value represents a resolved Amazon account, a device, or a browser cookie. If Amazon Ads is unable to determine or provide an ID of any kind for a click event, the 'user_id' and 'user_id_type' values for that record will be NULL. Example values include: 'adUserId', 'sisDeviceId', 'adBrowserId', and NULL. | LOW |

## Key Differences from dsp_impressions

This table is a **subset** of the `dsp_impressions` data that includes only impressions that were clicked, plus additional click-specific fields:

### Click-Specific Fields
- **clicks**: Always '1' since each record represents a click event
- **click_cost**: Cost of the click in millicents
- **click_date**, **click_date_utc**: Date of the click event
- **click_day**, **click_day_utc**: Day of month when click occurred
- **click_dt**, **click_dt_utc**: Timestamp of the click event
- **click_dt_hour**, **click_dt_hour_utc**: Click timestamp truncated to hour
- **click_hour**, **click_hour_utc**: Hour of day when click occurred

## Aggregation Threshold Notes

- **NONE**: No aggregation threshold restrictions
- **LOW**: Standard low threshold applies
- **MEDIUM**: Medium aggregation threshold - use caution in small segments
- **HIGH**: High aggregation threshold - significant restrictions on granular queries
- **VERY_HIGH**: Very high threshold - cannot be included in final SELECT statements but can be used in CTEs for aggregation

## Currency Conversion Notes

- **Microcents**: Divide by 100,000,000 to convert to dollars (e.g., 100,000,000 microcents = $1.00)
- **Millicents**: Divide by 100,000 to convert to dollars (e.g., 100,000 millicents = $1.00)

Refer to the `currency_name` field for the specific currency of monetary values.