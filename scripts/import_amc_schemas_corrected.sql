-- AMC Schema Import SQL (Fixed with proper escaping)
-- Generated: 2025-08-13T16:44:31.221227
-- Run this SQL in Supabase SQL Editor


-- Insert schema: Amazon Attributed Events Tables
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'amazon-attributed-events',
    'Amazon Attributed Events Tables',
    'Attribution Tables',
    'These tables both contain pairs of traffic and conversion events. "Traffic events" are impressions and clicks. "Conversion events" include purchases, various interactions with Amazon website, such as detailed page views and pixel fires. Each conversion event in the table is attributed to its corresponding traffic event.',
    '["amazon_attributed_events_by_conversion_time", "amazon_attributed_events_by_traffic_time"]',
    false,
    '["clicks", "conversion", "attribution", "impressions"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'ad_product_type', 'STRING', 'Dimension',
    'Type of Amazon Ads ad product responsible for the traffic event to which the conversion is attributed. This field helps distinguish between individual sponsored ads products and Amazon DSP. Possible values include: ''sponsored_products'', ''sponsored_brands'', ''sponsored_display'', ''sponsored_television'', and NULL (which represents Amazon DSP events).', 'LOW', 0
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversions', 'LONG', 'Dimension',
    'The count of conversion events. This field always contains a value of 1, allowing you to calculate conversion totals for the records selected in your query.', 'LOW', 1
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impressions', 'LONG', 'Dimension',
    'Count of impressions. For each conversion record, this field indicates whether the conversion was attributed to an ad view. Possible values: ''1'' (attributed to ad view) or ''0'' (not attributed to ad view).', 'LOW', 2
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'clicks', 'LONG', 'Metric',
    'Count of clicks. For each conversion record, this field indicates whether the conversion was attributed to an ad click. Possible values: ''1'' (attributed to ad click) or ''0'' (not attributed to ad click).', 'NONE', 3
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser', 'STRING', 'Dimension',
    'Name of the business entity running advertising campaigns on Amazon Ads.', 'LOW', 4
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign', 'STRING', 'Dimension',
    'Name of the Amazon Ads campaign to which the conversion event is attributed.', 'LOW', 5
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_id', 'LONG', 'Dimension',
    'The ID of the Amazon Ads campaign associated with the conversion event.', 'LOW', 6
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item', 'STRING', 'Dimension',
    'Name of the line item to which the conversion is attributed.', 'LOW', 7
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_id', 'LONG', 'Dimension',
    'ID of the line item to which the conversion is attributed.', 'LOW', 8
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_event_category', 'STRING', 'Dimension',
    'High-level category of the conversion event. Possible values include: ''website'' (browsing event on Amazon), ''purchase'' (purchase event on Amazon), and ''off-Amazon''.', 'LOW', 9
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_event_subtype', 'STRING', 'Dimension',
    'Subtype of the conversion event. For on-Amazon: ''detailPageView'', ''shoppingCart'', ''order'', etc. For off-Amazon: numeric values like ''134'', ''140'', ''141''.', 'LOW', 10
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_event_date', 'DATE', 'Dimension',
    'Date of the conversion event in advertiser timezone.', 'LOW', 11
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_event_dt', 'TIMESTAMP', 'Dimension',
    'Timestamp of the conversion event in advertiser timezone.', 'MEDIUM', 12
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'traffic_event_subtype', 'STRING', 'Dimension',
    'Type of traffic event that led to the conversion. Possible values include: ''AD_IMP'' (ad view event) and ''AD_CLICK'' (ad click event).', 'LOW', 13
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'traffic_event_date', 'DATE', 'Dimension',
    'Date of the traffic event in advertiser timezone.', 'NONE', 14
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'traffic_event_dt', 'TIMESTAMP', 'Dimension',
    'Timestamp of the traffic event in advertiser timezone.', 'MEDIUM', 15
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_date', 'DATE', 'Dimension',
    'Date of the impression event in advertiser timezone (populated for view-attributed conversions).', 'LOW', 16
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'click_date', 'DATE', 'Dimension',
    'Date of the click event in advertiser timezone (populated for click-attributed conversions).', 'LOW', 17
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'product_sales', 'DECIMAL(38, 4)', 'Metric',
    'The sales (in local currency) of promoted ASINs purchased on Amazon, attributed to an ad view or click.', 'LOW', 18
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'purchases', 'LONG', 'Metric',
    'The number of purchases of promoted ASINs on Amazon, attributed to an ad view or click.', 'NONE', 19
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'units_sold', 'LONG', 'Metric',
    'The quantity of promoted ASINs purchased on Amazon, attributed to an ad view or click.', 'NONE', 20
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'detail_page_view', 'LONG', 'Metric',
    'The number of detail page views on advertised ASINs, attributed to an ad view or click.', 'NONE', 21
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'add_to_cart', 'LONG', 'Metric',
    'The number of times a promoted ASIN was added to a customer''s cart on Amazon, attributed to an ad view or click.', 'NONE', 22
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'brand_halo_product_sales', 'DECIMAL(38, 4)', 'Metric',
    'The sales (in local currency) of brand halo ASINs purchased on Amazon, attributed to an ad view or click. Brand halo ASINs are products from the same brand as the ASINs promoted by the campaign.', 'NONE', 23
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'brand_halo_purchases', 'LONG', 'Metric',
    'The number of purchases of brand halo ASINs on Amazon, attributed to an ad view or click.', 'NONE', 24
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'brand_halo_units_sold', 'LONG', 'Metric',
    'The quantity of brand halo ASINs purchased on Amazon, attributed to an ad view or click.', 'NONE', 25
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'total_product_sales', 'DECIMAL(38, 4)', 'Dimension',
    'The sales (in local currency) of promoted and brand halo ASINs purchased on Amazon, attributed to an ad view or click. Note: total_product_sales = product_sales + brand_halo_product_sales.', 'LOW', 26
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'total_purchases', 'LONG', 'Dimension',
    'The number of purchases of promoted and brand halo ASINs on Amazon, attributed to an ad view or click. Note: total_purchases = purchases + brand_halo_purchases.', 'NONE', 27
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'total_units_sold', 'LONG', 'Dimension',
    'The quantity of promoted and brand halo ASINs purchased on Amazon, attributed to an ad view or click. Note: total_units_sold = units_sold + brand_halo_units_sold.', 'LOW', 28
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'new_to_brand', 'BOOLEAN', 'Metric',
    'Boolean value indicating whether the customer is new-to-brand (not purchased from brand in previous 12 months).', 'NONE', 29
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'new_to_brand_product_sales', 'DECIMAL(38, 4)', 'Metric',
    'The sales (in local currency) of promoted ASINs purchased by new-to-brand customers.', 'NONE', 30
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'new_to_brand_total_product_sales', 'DECIMAL(38, 4)', 'Metric',
    'The sales (in local currency) of promoted and brand halo ASINs purchased by new-to-brand customers.', 'NONE', 31
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'off_amazon_product_sales', 'LONG', 'Metric',
    'Product sales amount associated with the off-Amazon conversion event.', 'NONE', 32
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'off_amazon_conversion_value', 'LONG', 'Metric',
    'The non-monetary value assigned to non-purchase conversion events that occur off Amazon.', 'NONE', 33
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'combined_sales', 'LONG', 'Metric',
    'The total sales amount combining both on-Amazon product sales and off-Amazon product sales. combined_sales = total_product_sales + off_amazon_product_sales.', 'NONE', 34
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'customer_search_term', 'STRING', 'Dimension',
    'Search term entered by a shopper on Amazon that led to the traffic event.', 'LOW', 35
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'targeting', 'STRING', 'Dimension',
    'Keyword used by the advertiser for targeting on sponsored ads campaigns.', 'LOW', 36
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'match_type', 'STRING', 'Dimension',
    'Type of match between targeting keyword and customer search term. Possible values: ''BROAD'', ''PHRASE'', ''EXACT'', and NULL.', 'MEDIUM', 37
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Basic Attribution Analysis', '-- Conversion attribution breakdown
SELECT 
    campaign,
    SUM(CASE WHEN impressions = 1 THEN conversions ELSE 0 END) as view_conversions,
    SUM(CASE WHEN clicks = 1 THEN conversions ELSE 0 END) as click_conversions,
    SUM(conversions) as total_conversions
FROM amazon_attributed_events_by_conversion_time
GROUP BY campaign;', 'Attribution', 0
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Multi-Product Performance', '-- Performance by ad product type
SELECT 
    COALESCE(ad_product_type, ''Amazon DSP'') as product_type,
    SUM(total_purchases) as purchases,
    SUM(total_product_sales) as sales
FROM amazon_attributed_events_by_conversion_time
WHERE conversion_event_category = ''purchase''
GROUP BY ad_product_type;', 'Advanced', 1
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Brand Halo Analysis', '-- Direct vs Brand Halo performance
SELECT 
    campaign,
    SUM(product_sales) as direct_sales,
    SUM(brand_halo_product_sales) as halo_sales,
    SUM(total_product_sales) as total_sales,
    CASE 
        WHEN SUM(total_product_sales) > 0 
        THEN SUM(brand_halo_product_sales) * 100.0 / SUM(total_product_sales)
        ELSE 0 
    END as halo_percentage
FROM amazon_attributed_events_by_conversion_time
WHERE conversion_event_category = ''purchase''
GROUP BY campaign;', 'Basic', 2
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Time-to-Conversion Analysis', '-- Days between traffic and conversion
SELECT 
    campaign,
    DATE_DIFF(conversion_event_date, traffic_event_date, DAY) as days_to_conversion,
    COUNT(*) as conversions
FROM amazon_attributed_events_by_conversion_time
WHERE traffic_event_date IS NOT NULL 
    AND conversion_event_date IS NOT NULL
GROUP BY campaign, days_to_conversion
ORDER BY campaign, days_to_conversion;', 'Basic', 3
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'New-to-Brand Performance', '-- Customer acquisition analysis
SELECT 
    campaign,
    new_to_brand,
    SUM(total_purchases) as purchases,
    SUM(total_product_sales) as sales,
    AVG(purchase_unit_price) as avg_order_value
FROM amazon_attributed_events_by_conversion_time
WHERE conversion_event_category = ''purchase''
    AND new_to_brand IS NOT NULL
GROUP BY campaign, new_to_brand;', 'Performance', 4
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Sources:** 
- `amazon_attributed_events_by_conversion_time`
- `amazon_attributed_events_by_traffic_time`

These tables both contain pairs of traffic and conversion events. "Traffic events" are impressions and clicks. "Conversion events" include purchases, various interactions with Amazon website, such as detailed page views and pixel fires. Each conversion event in the table is attributed to its corresponding traffic event.', 0
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'differences', '⚠️ **Important**: While the tables include the same metrics and dimensions, they differ with respect to the set of events that are contained within.', 1
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'concepts', '### Attribution Framework
- **View Attribution**: Conversions credited to ad impressions (view-through conversions)
- **Click Attribution**: Conversions credited to ad clicks (click-through conversions)
- **Attribution Windows**: Determined by campaign settings, not modifiable in AMC
- **Cross-Product Attribution**: Single table covers DSP, Sponsored Products, Sponsored Brands, etc.', 3
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'query_patterns', '### Basic Attribution Analysis
```sql
-- Conversion attribution breakdown
SELECT 
    campaign,
    SUM(CASE WHEN impressions = 1 THEN conversions ELSE 0 END) as view_conversions,
    SUM(CASE WHEN clicks = 1 THEN conversions ELSE 0 END) as click_conversions,
    SUM(conversions) as total_conversions
FROM amazon_attributed_events_by_conversion_time
GROUP BY campaign;
```', 4
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'best_practices', '### Query Optimization
- **Filter by ad_product_type** early to focus on specific ad products
- **Use conversion_event_category** to separate purchase vs website events
- **Apply date filters** appropriate to your table choice
- **Consider modeled events** when interpreting user-level data', 5
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'selection_guidelines', '### Use amazon_attributed_events_by_conversion_time when:
- **Standard reporting**: Match Amazon DSP business logic
- **Conversion-focused analysis**: Want conversions from specific time period
- **Campaign performance review**: Measuring results for specific periods
- **Budget allocation**: Understanding conversion delivery by time period', 6
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'data_availability', '### Historical Data
- **Sponsored Brands**: Available from December 2, 2022
- **Backfill period**: 0-28 days before instance creation (varies by instance age)
- **Keywords and search terms**: 13 months or instance creation date, whichever is sooner', 7
FROM amc_data_sources 
WHERE schema_id = 'amazon-attributed-events'
ON CONFLICT DO NOTHING;

-- Insert schema: Amazon Brand Store Insights Tables
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'amazon-brand-store-insights',
    'Amazon Brand Store Insights Tables',
    'Core Tables',
    'Amazon Brand Store insights is a collection of two AMC datasets that represent Brand Store page renders and interactions. This is a **standalone AMC Paid Features resource** available for trial and subscription enrollments within the AMC Paid Features suite.',
    '["amazon_brand_store_page_views", "amazon_brand_store_engagement_events"]',
    true,
    '["clicks"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'ADVERTISER_ID', 'Dimension',
    'Dimension', 'ADVERTISER ID.', 0
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'CHANNEL', 'Dimension',
    'Dimension', 'CHANNEL TAG ID, REFERENCED AS QUERY STRING NAME.', 1
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'DEVICE_TYPE', 'Dimension',
    'Dimension', 'DEVICE TYPE THAT VIEWED THE STORE.', 2
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'DWELL_TIME', 'Dimension',
    'Dimension', 'DWELL TIME OF PAGE VIEW (IN SECONDS).', 3
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'EVENT_DATE_UTC', 'Dimension',
    'Dimension', 'DATE OF EVENT IN UTC.', 4
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'EVENT_DT_UTC', 'Dimension',
    'Dimension', 'TIMESTAMP OF EVENT IN UTC.', 5
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'INGRESS_TYPE', 'Dimension',
    'Dimension', 'ENUMERATED LIST OF STORE TRAFFIC SOURCE: 0 - UNCATEGORIZED/DEFAULT, 1 - SEARCH, 2 - DETAIL PAGE BYLINE, 4 - ADS, 6 - STORE RECOMMENDATIONS, 7-11 - EXPERIMENTATION', 6
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'MARKETPLACE_ID', 'Dimension',
    'Dimension', 'MARKETPLACE ID OF THE STORE.', 7
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'PAGE_ID', 'Dimension',
    'Dimension', 'STORE PAGE ID.', 8
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'PAGE_TITLE', 'Dimension',
    'Dimension', 'TITLE OF THE PAGE.', 9
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'REFERENCE_ID', 'Dimension',
    'Dimension', 'IDENTIFIER FOR THE AD CAMPAIGN ASSOCIATED WITH THE BRAND STORE PAGE VISIT (INGRESS_TYPE = 4).', 10
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'REFERRER_DOMAIN', 'Dimension',
    'Dimension', 'HTML REFERRER DOMAIN FROM WHICH USER ARRIVED (E.G., GOOGLE.COM EXTERNAL, AMAZON.COM INTERNAL).', 11
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'SESSION_ID', 'Dimension',
    'Dimension', 'STORE SESSION ID.', 12
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'STORE_NAME', 'Dimension',
    'Dimension', 'NAME OF THE STORE SET BY THE STORE OWNER.', 13
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'USER_ID', 'Dimension',
    'Dimension', 'USER ID THAT PERFORMED THE EVENT.', 14
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'USER_ID_TYPE', 'Dimension',
    'Dimension', 'TYPE OF USER ID.', 15
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'VISIT_ID', 'Dimension',
    'Dimension', 'STORE VISIT ID.', 16
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'NO_3P_TRACKERS', 'Dimension',
    'Dimension', 'INDICATES WHETHER THIS ITEM IS NOT ALLOWED TO USE 3P TRACKING.', 17
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'ADVERTISER_ID', 'Dimension',
    'Dimension', 'ADVERTISER ID.', 18
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'ASIN', 'Dimension',
    'Dimension', 'AMAZON STANDARD IDENTIFICATION NUMBER (ASIN).', 19
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'CHANNEL', 'Dimension',
    'Dimension', 'CHANNEL TAG ID, REFERENCED AS QUERY STRING NAME.', 20
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'DEVICE_TYPE', 'Dimension',
    'Dimension', 'DEVICE TYPE THAT VIEWED THE STORE.', 21
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'EVENT_DATE_UTC', 'Dimension',
    'Dimension', 'DATE OF EVENT IN UTC.', 22
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'EVENT_DT_UTC', 'Dimension',
    'Dimension', 'TIMESTAMP OF EVENT IN UTC.', 23
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'EVENT_SUB_TYPE', 'Dimension',
    'Dimension', 'SUB-TYPE OF EVENT - REFER TO SCHEMA FOR VALUES.', 24
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'EVENT_TYPE', 'Dimension',
    'Dimension', 'TYPE OF EVENT - REFER TO SCHEMA FOR VALUES.', 25
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'INGRESS_TYPE', 'Dimension',
    'Dimension', 'ENUMERATED LIST OF STORE TRAFFIC SOURCE: 0 - UNCATEGORIZED/DEFAULT, 1 - SEARCH, 2 - DETAIL PAGE BYLINE, 4 - ADS, 6 - STORE RECOMMENDATIONS, 7-11 - EXPERIMENTATION', 26
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'MARKETPLACE_ID', 'Dimension',
    'Dimension', 'MARKETPLACE ID OF THE STORE.', 27
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'PAGE_ID', 'Dimension',
    'Dimension', 'STORE PAGE ID.', 28
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'PAGE_TITLE', 'Dimension',
    'Dimension', 'TITLE OF THE PAGE.', 29
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'REFERENCE_ID', 'Dimension',
    'Dimension', 'IDENTIFIER FOR THE AD CAMPAIGN ASSOCIATED WITH THE BRAND STORE PAGE VISIT (INGRESS_TYPE = 4).', 30
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'REFERRER_DOMAIN', 'Dimension',
    'Dimension', 'HTML REFERRER DOMAIN FROM WHICH USER ARRIVED (E.G., GOOGLE.COM EXTERNAL, AMAZON.COM INTERNAL).', 31
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'SESSION_ID', 'Dimension',
    'Dimension', 'STORE SESSION ID.', 32
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'STORE_NAME', 'Dimension',
    'Dimension', 'NAME OF THE STORE SET BY THE STORE OWNER.', 33
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'USER_ID', 'Dimension',
    'Dimension', 'USER ID THAT PERFORMED THE EVENT.', 34
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'USER_ID_TYPE', 'Dimension',
    'Dimension', 'TYPE OF USER ID.', 35
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'WIDGET_SUB_TYPE', 'Dimension',
    'Dimension', 'SUB-TYPE OF WIDGET - REFER TO SCHEMA FOR VALUES.', 36
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'WIDGET_TYPE', 'Dimension',
    'Dimension', 'TYPE OF WIDGET - REFER TO SCHEMA FOR VALUES.', 37
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Brand Store Insights', 'NO_3P_TRACKERS', 'Dimension',
    'Dimension', 'INDICATES WHETHER THIS ITEM IS NOT ALLOWED TO USE 3P TRACKING.', 38
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Traffic Source Performance', '-- Analyze traffic sources and their performance
SELECT 
    ingress_type,
    CASE 
        WHEN ingress_type = ''0'' THEN ''Uncategorized''
        WHEN ingress_type = ''1'' THEN ''Search''
        WHEN ingress_type = ''2'' THEN ''Detail Page Byline''
        WHEN ingress_type = ''4'' THEN ''Ads''
        WHEN ingress_type = ''6'' THEN ''Store Recommendations''
        WHEN ingress_type BETWEEN ''7'' AND ''11'' THEN ''Experimentation''
        ELSE ''Other''
    END as traffic_source,
    COUNT(DISTINCT visit_id) as unique_visits,
    COUNT(DISTINCT session_id) as unique_sessions,
    AVG(dwell_time) as avg_dwell_time_seconds
FROM amazon_brand_store_page_views
WHERE event_date_utc >= ''2025-01-01''
GROUP BY ingress_type
ORDER BY unique_visits DESC;', 'Performance', 0
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Page Performance Analysis', '-- Analyze individual page performance
SELECT 
    page_title,
    page_id,
    COUNT(DISTINCT visit_id) as page_visits,
    AVG(dwell_time) as avg_dwell_time,
    COUNT(DISTINCT user_id) as unique_users
FROM amazon_brand_store_page_views
WHERE event_date_utc >= ''2025-01-01''
    AND dwell_time IS NOT NULL
GROUP BY page_title, page_id
ORDER BY page_visits DESC;', 'Performance', 1
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Device Type Analysis', '-- Compare performance across device types
SELECT 
    device_type,
    COUNT(DISTINCT visit_id) as visits,
    COUNT(DISTINCT session_id) as sessions,
    AVG(dwell_time) as avg_dwell_time,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dwell_time) as median_dwell_time
FROM amazon_brand_store_page_views
WHERE event_date_utc >= ''2025-01-01''
    AND dwell_time > 0
GROUP BY device_type
ORDER BY visits DESC;', 'Basic', 2
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Widget Engagement Analysis', '-- Analyze widget performance and engagement
SELECT 
    widget_type,
    widget_sub_type,
    event_type,
    event_sub_type,
    COUNT(*) as total_events,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT session_id) as unique_sessions
FROM amazon_brand_store_engagement_events
WHERE event_date_utc >= ''2025-01-01''
GROUP BY widget_type, widget_sub_type, event_type, event_sub_type
ORDER BY total_events DESC;', 'Basic', 3
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'ASIN Performance in Brand Store', '-- Analyze ASIN-level engagement within Brand Store
SELECT 
    asin,
    widget_type,
    event_type,
    COUNT(*) as interactions,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT visit_id) as unique_visits
FROM amazon_brand_store_engagement_events
WHERE event_date_utc >= ''2025-01-01''
    AND asin IS NOT NULL
GROUP BY asin, widget_type, event_type
ORDER BY interactions DESC;', 'Performance', 4
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Campaign Attribution Analysis', '-- Analyze campaign-driven Brand Store traffic
SELECT 
    reference_id as campaign_id,
    store_name,
    COUNT(DISTINCT visit_id) as campaign_visits,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(dwell_time) as avg_dwell_time
FROM amazon_brand_store_page_views
WHERE ingress_type = ''4''  -- Ads traffic
    AND reference_id IS NOT NULL
    AND event_date_utc >= ''2025-01-01''
GROUP BY reference_id, store_name
ORDER BY campaign_visits DESC;', 'Attribution', 5
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Session Journey Analysis', '-- Analyze user journey within Brand Store sessions
WITH session_journey AS (
    SELECT 
        session_id,
        COUNT(DISTINCT page_id) as pages_per_session,
        SUM(dwell_time) as total_session_time,
        MIN(event_dt_utc) as session_start,
        MAX(event_dt_utc) as session_end
    FROM amazon_brand_store_page_views
    WHERE event_date_utc >= ''2025-01-01''
        AND session_id IS NOT NULL
    GROUP BY session_id
)
SELECT 
    pages_per_session,
    COUNT(*) as session_count,
    AVG(total_session_time) as avg_session_duration,
    AVG(TIMESTAMP_DIFF(session_end, session_start, SECOND)) as avg_session_length_seconds
FROM session_journey
GROUP BY pages_per_session
ORDER BY pages_per_session;', 'Basic', 6
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Cross-Channel Analysis', '-- Analyze referrer domains and external traffic
SELECT 
    referrer_domain,
    CASE 
        WHEN referrer_domain LIKE ''%amazon.%'' THEN ''Internal Amazon''
        WHEN referrer_domain LIKE ''%google.%'' THEN ''Google''
        WHEN referrer_domain LIKE ''%facebook.%'' THEN ''Facebook''
        WHEN referrer_domain LIKE ''%instagram.%'' THEN ''Instagram''
        WHEN referrer_domain IS NULL THEN ''Direct''
        ELSE ''Other External''
    END as referrer_category,
    COUNT(DISTINCT visit_id) as visits,
    AVG(dwell_time) as avg_dwell_time
FROM amazon_brand_store_page_views
WHERE event_date_utc >= ''2025-01-01''
GROUP BY referrer_domain
ORDER BY visits DESC;', 'Basic', 7
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Engagement Funnel Analysis', '-- Create engagement funnel from page views to interactions
WITH page_views AS (
    SELECT DISTINCT 
        user_id,
        visit_id,
        session_id,
        event_date_utc
    FROM amazon_brand_store_page_views
    WHERE event_date_utc >= ''2025-01-01''
),
engagements AS (
    SELECT DISTINCT
        user_id,
        session_id,
        event_type,
        event_date_utc
    FROM amazon_brand_store_engagement_events
    WHERE event_date_utc >= ''2025-01-01''
)
SELECT 
    COUNT(DISTINCT pv.user_id) as total_visitors,
    COUNT(DISTINCT e.user_id) as engaged_visitors,
    COUNT(DISTINCT e.user_id) * 100.0 / COUNT(DISTINCT pv.user_id) as engagement_rate
FROM page_views pv
LEFT JOIN engagements e 
    ON pv.user_id = e.user_id 
    AND pv.session_id = e.session_id;', 'Basic', 8
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Conversion Attribution', '-- Connect Brand Store visits to conversions
WITH brand_store_visitors AS (
    SELECT DISTINCT 
        user_id,
        visit_id,
        session_id,
        event_date_utc as visit_date,
        ingress_type,
        reference_id
    FROM amazon_brand_store_page_views
    WHERE event_date_utc >= ''2025-01-01''
)
SELECT 
    bsv.ingress_type,
    COUNT(DISTINCT bsv.user_id) as store_visitors,
    COUNT(DISTINCT c.user_id) as converting_visitors,
    SUM(c.total_purchases) as total_purchases,
    SUM(c.total_product_sales) as total_sales,
    COUNT(DISTINCT c.user_id) * 100.0 / COUNT(DISTINCT bsv.user_id) as conversion_rate
FROM brand_store_visitors bsv
LEFT JOIN amazon_attributed_events_by_conversion_time c
    ON bsv.user_id = c.user_id
    AND c.conversion_event_date >= bsv.visit_date
    AND c.conversion_event_date <= DATE_ADD(bsv.visit_date, INTERVAL 7 DAY)
GROUP BY bsv.ingress_type
ORDER BY total_sales DESC;', 'Attribution', 9
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Cohort Analysis', '-- Analyze repeat visit behavior
WITH first_visits AS (
    SELECT 
        user_id,
        MIN(event_date_utc) as first_visit_date
    FROM amazon_brand_store_page_views
    WHERE event_date_utc >= ''2025-01-01''
    GROUP BY user_id
),
return_visits AS (
    SELECT 
        pv.user_id,
        fv.first_visit_date,
        DATE_DIFF(pv.event_date_utc, fv.first_visit_date, DAY) as days_since_first_visit
    FROM amazon_brand_store_page_views pv
    JOIN first_visits fv ON pv.user_id = fv.user_id
    WHERE pv.event_date_utc > fv.first_visit_date
)
SELECT 
    CASE 
        WHEN days_since_first_visit <= 7 THEN ''1 Week''
        WHEN days_since_first_visit <= 30 THEN ''1 Month''
        WHEN days_since_first_visit <= 90 THEN ''3 Months''
        ELSE ''3+ Months''
    END as return_timeframe,
    COUNT(DISTINCT user_id) as returning_users
FROM return_visits
GROUP BY 
    CASE 
        WHEN days_since_first_visit <= 7 THEN ''1 Week''
        WHEN days_since_first_visit <= 30 THEN ''1 Month''
        WHEN days_since_first_visit <= 90 THEN ''3 Months''
        ELSE ''3+ Months''
    END
ORDER BY returning_users DESC;', 'Basic', 10
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Audience Building', '-- Create audience of engaged Brand Store visitors
CREATE AUDIENCE engaged_brand_store_visitors AS
SELECT DISTINCT user_id
FROM amazon_brand_store_engagement_events
WHERE event_date_utc >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    AND event_type IN (''click'', ''interaction'')  -- Adjust based on available event types
    AND no_3p_trackers = false;', 'Basic', 11
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Sources:** 
- `amazon_brand_store_page_views` (and `_non_endemic` variant)
- `amazon_brand_store_engagement_events` (and `_non_endemic` variant)

Amazon Brand Store insights is a collection of two AMC datasets that represent Brand Store page renders and interactions. This is a **standalone AMC Paid Features resource** available for trial and subscription enrollments within the AMC Paid Features suite.', 0
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'differences', '### amazon_brand_store_page_views
- **Granularity**: Store page-level events
- **Primary focus**: Page view events and dwell time analysis
- **Use cases**: Traffic analysis, page performance, user journey mapping
- **Key metric**: Dwell time measurement', 1
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'availability', '### Subscription Requirements
- **AMC Paid Features enrollment**: Trial and subscription options available
- **Advertiser types**: Available to both endemic and non-endemic advertisers
- **Powered by**: Amazon Advertising', 2
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'query_patterns', '### Traffic Source Performance
```sql
-- Analyze traffic sources and their performance
SELECT 
    ingress_type,
    CASE 
        WHEN ingress_type = ''0'' THEN ''Uncategorized''
        WHEN ingress_type = ''1'' THEN ''Search''
        WHEN ingress_type = ''2'' THEN ''Detail Page Byline''
        WHEN ingress_type = ''4'' THEN ''Ads''
        WHEN ingress_type = ''6'' THEN ''Store Recommendations''
        WHEN ingress_type BETWEEN ''7'' AND ''11'' THEN ''Experimentation''
        ELSE ''Other''
    END as traffic_source,
    COUNT(DISTINCT visit_id) as unique_visits,
    COUNT(DISTINCT session_id) as unique_sessions,
    AVG(dwell_time) as avg_dwell_time_seconds
FROM amazon_brand_store_page_views
WHERE event_date_utc >= ''2025-01-01''
GROUP BY ingress_type
ORDER BY unique_visits DESC;
```', 4
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'best_practices', '### Query Optimization
- **Use CTEs for user_id**: Due to VERY_HIGH aggregation threshold, use user_id in Common Table Expressions
- **Filter by date ranges**: Always include event_date_utc filters for performance
- **Leverage specific dimensions**: Use page_id, widget_type, or ASIN for focused analysis
- **Join tables strategically**: Combine page views and engagement events for comprehensive analysis', 5
FROM amc_data_sources 
WHERE schema_id = 'amazon-brand-store-insights'
ON CONFLICT DO NOTHING;

-- Insert schema: amazon_retail_purchases Data Source
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'amazon-retail-purchases',
    'amazon_retail_purchases Data Source',
    'Retail Analytics',
    'The Amazon Retail Purchases (ARP) dataset enables advertisers to analyze **long-term (up to 60 months)** customer purchase behavior and create more comprehensive insights. This dataset provides retail purchase data sourced from Amazon''s retail data pipeline rather than advertising data pipeline.',
    '[]',
    true,
    '["clicks"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Customer Lifetime Value Analysis', '-- Calculate customer lifetime value over 5 years
WITH customer_purchases AS (
    SELECT 
        user_id,
        COUNT(DISTINCT purchase_id) as total_orders,
        SUM(purchase_units_sold) as total_units,
        SUM(unit_price * purchase_units_sold) as total_spend,
        MIN(purchase_date_utc) as first_purchase,
        MAX(purchase_date_utc) as last_purchase,
        DATE_DIFF(MAX(purchase_date_utc), MIN(purchase_date_utc), DAY) as customer_lifespan_days
    FROM amazon_retail_purchases
    WHERE purchase_date_utc >= ''2020-01-01''
    GROUP BY user_id
)
SELECT 
    CASE 
        WHEN total_spend >= 1000 THEN ''High Value''
        WHEN total_spend >= 500 THEN ''Medium Value''
        ELSE ''Low Value''
    END as customer_segment,
    COUNT(*) as customer_count,
    AVG(total_spend) as avg_lifetime_value,
    AVG(total_orders) as avg_orders,
    AVG(customer_lifespan_days) as avg_lifespan_days
FROM customer_purchases
GROUP BY 
    CASE 
        WHEN total_spend >= 1000 THEN ''High Value''
        WHEN total_spend >= 500 THEN ''Medium Value''
        ELSE ''Low Value''
    END;', 'Basic', 0
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Purchase Frequency and Retention', '-- Analyze purchase frequency patterns
WITH customer_metrics AS (
    SELECT 
        user_id,
        COUNT(DISTINCT purchase_id) as order_count,
        COUNT(DISTINCT DATE_TRUNC(''month'', purchase_date_utc)) as active_months,
        MIN(purchase_date_utc) as first_purchase,
        MAX(purchase_date_utc) as last_purchase
    FROM amazon_retail_purchases
    WHERE purchase_date_utc >= ''2020-01-01''
    GROUP BY user_id
    HAVING COUNT(DISTINCT purchase_id) > 1
)
SELECT 
    active_months,
    COUNT(*) as customer_count,
    AVG(order_count) as avg_orders_per_customer,
    AVG(DATE_DIFF(last_purchase, first_purchase, DAY)) as avg_customer_lifespan
FROM customer_metrics
GROUP BY active_months
ORDER BY active_months;', 'Basic', 1
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Brand Performance Over Time', '-- Analyze brand performance trends over 5 years
SELECT 
    asin_brand,
    EXTRACT(YEAR FROM purchase_date_utc) as purchase_year,
    COUNT(DISTINCT user_id) as unique_customers,
    COUNT(DISTINCT purchase_id) as total_orders,
    SUM(purchase_units_sold) as total_units,
    SUM(unit_price * purchase_units_sold) as total_revenue,
    AVG(unit_price) as avg_unit_price
FROM amazon_retail_purchases
WHERE asin_brand IS NOT NULL
    AND purchase_date_utc >= ''2020-01-01''
GROUP BY asin_brand, EXTRACT(YEAR FROM purchase_date_utc)
ORDER BY asin_brand, purchase_year;', 'Performance', 2
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Product Portfolio Analysis', '-- Analyze product performance and customer overlap
SELECT 
    asin,
    asin_name,
    asin_brand,
    COUNT(DISTINCT user_id) as unique_customers,
    COUNT(DISTINCT purchase_id) as total_orders,
    SUM(purchase_units_sold) as total_units_sold,
    SUM(unit_price * purchase_units_sold) as total_revenue,
    AVG(unit_price) as avg_unit_price,
    AVG(purchase_units_sold) as avg_units_per_order
FROM amazon_retail_purchases
WHERE purchase_date_utc >= ''2024-01-01''
GROUP BY asin, asin_name, asin_brand
ORDER BY total_revenue DESC;', 'Basic', 3
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Purchase Method and Prime Analysis', '-- Analyze purchase methods and Prime usage
SELECT 
    purchase_order_method,
    CASE 
        WHEN purchase_order_method = ''S'' THEN ''Shopping Cart''
        WHEN purchase_order_method = ''B'' THEN ''Buy Now''
        WHEN purchase_order_method = ''1'' THEN ''1-Click Buy''
        ELSE purchase_order_method
    END as method_description,
    purchase_order_type,
    COUNT(DISTINCT purchase_id) as orders,
    COUNT(DISTINCT user_id) as unique_customers,
    SUM(purchase_units_sold) as total_units,
    SUM(unit_price * purchase_units_sold) as total_revenue,
    AVG(unit_price * purchase_units_sold) as avg_order_value
FROM amazon_retail_purchases
WHERE purchase_date_utc >= ''2024-01-01''
GROUP BY purchase_order_method, purchase_order_type
ORDER BY orders DESC;', 'Basic', 4
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Gift and Business Purchase Analysis', '-- Analyze gift purchases and business orders
SELECT 
    is_gift_flag,
    is_business_flag,
    COUNT(DISTINCT purchase_id) as orders,
    COUNT(DISTINCT user_id) as unique_customers,
    SUM(unit_price * purchase_units_sold) as total_revenue,
    AVG(unit_price * purchase_units_sold) as avg_order_value,
    AVG(purchase_units_sold) as avg_units_per_order
FROM amazon_retail_purchases
WHERE purchase_date_utc >= ''2024-01-01''
GROUP BY is_gift_flag, is_business_flag
ORDER BY total_revenue DESC;', 'Basic', 5
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Seasonal Purchase Patterns', '-- Analyze seasonal trends over multiple years
SELECT 
    purchase_month_utc as month,
    EXTRACT(YEAR FROM purchase_date_utc) as year,
    COUNT(DISTINCT purchase_id) as orders,
    SUM(unit_price * purchase_units_sold) as revenue,
    COUNT(DISTINCT user_id) as unique_customers,
    AVG(unit_price * purchase_units_sold) as avg_order_value
FROM amazon_retail_purchases
WHERE purchase_date_utc >= ''2020-01-01''
GROUP BY purchase_month_utc, EXTRACT(YEAR FROM purchase_date_utc)
ORDER BY year, month;', 'Basic', 6
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Hour-of-Day Purchase Patterns', '-- Analyze purchase timing patterns
SELECT 
    purchase_hour_utc,
    purchase_order_method,
    COUNT(DISTINCT purchase_id) as orders,
    AVG(unit_price * purchase_units_sold) as avg_order_value,
    COUNT(DISTINCT user_id) as unique_customers
FROM amazon_retail_purchases
WHERE purchase_date_utc >= ''2024-01-01''
GROUP BY purchase_hour_utc, purchase_order_method
ORDER BY purchase_hour_utc, purchase_order_method;', 'Basic', 7
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Incremental Analysis with Advertising Data', '-- Compare retail purchases vs ad-attributed conversions
-- (Use appropriate time windows for each dataset)
WITH recent_retail AS (
    SELECT 
        user_id,
        asin,
        SUM(purchase_units_sold) as retail_units,
        SUM(unit_price * purchase_units_sold) as retail_revenue
    FROM amazon_retail_purchases
    WHERE purchase_date_utc >= ''2024-01-01''  -- Match advertising data window
    GROUP BY user_id, asin
),
ad_attributed AS (
    SELECT 
        user_id,
        tracked_asin as asin,
        SUM(total_units_sold) as attributed_units,
        SUM(total_product_sales) as attributed_revenue
    FROM amazon_attributed_events_by_conversion_time
    WHERE conversion_event_date >= ''2024-01-01''
        AND conversion_event_category = ''purchase''
    GROUP BY user_id, tracked_asin
)
SELECT 
    COALESCE(r.asin, a.asin) as asin,
    COUNT(DISTINCT COALESCE(r.user_id, a.user_id)) as total_customers,
    COUNT(DISTINCT r.user_id) as retail_customers,
    COUNT(DISTINCT a.user_id) as attributed_customers,
    SUM(COALESCE(r.retail_units, 0)) as total_retail_units,
    SUM(COALESCE(a.attributed_units, 0)) as total_attributed_units,
    SUM(COALESCE(r.retail_revenue, 0)) as total_retail_revenue,
    SUM(COALESCE(a.attributed_revenue, 0)) as total_attributed_revenue
FROM recent_retail r
FULL OUTER JOIN ad_attributed a 
    ON r.user_id = a.user_id AND r.asin = a.asin
GROUP BY COALESCE(r.asin, a.asin)
ORDER BY total_retail_revenue DESC;', 'Basic', 8
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Customer Journey Analysis', '-- Analyze customer purchase journey over time
WITH customer_journey AS (
    SELECT 
        user_id,
        purchase_date_utc,
        asin,
        asin_brand,
        unit_price * purchase_units_sold as order_value,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY purchase_date_utc) as purchase_sequence
    FROM amazon_retail_purchases
    WHERE purchase_date_utc >= ''2023-01-01''
)
SELECT 
    purchase_sequence,
    COUNT(DISTINCT user_id) as customers_at_stage,
    AVG(order_value) as avg_order_value,
    COUNT(DISTINCT asin_brand) as avg_brands_purchased
FROM customer_journey
WHERE purchase_sequence <= 10  -- First 10 purchases
GROUP BY purchase_sequence
ORDER BY purchase_sequence;', 'Basic', 9
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'High-Value Customer Segments', '-- Create audience of high-value customers (non-EU markets only)
CREATE AUDIENCE high_value_retail_customers AS
WITH customer_value AS (
    SELECT 
        user_id,
        SUM(unit_price * purchase_units_sold) as total_spend,
        COUNT(DISTINCT purchase_id) as order_count
    FROM amazon_retail_purchases
    WHERE purchase_date_utc >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
        AND marketplace_name NOT IN (''AMAZON.CO.UK'', ''AMAZON.FR'', ''AMAZON.DE'', ''AMAZON.IT'', ''AMAZON.ES'')  -- Exclude EU
    GROUP BY user_id
)
SELECT user_id
FROM customer_value
WHERE total_spend >= 1000
    AND order_count >= 5;', 'Basic', 10
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Brand Loyalty Segments', '-- Create audience of brand-loyal customers
CREATE AUDIENCE brand_loyal_customers AS
WITH brand_purchases AS (
    SELECT 
        user_id,
        asin_brand,
        COUNT(DISTINCT purchase_id) as brand_orders,
        SUM(unit_price * purchase_units_sold) as brand_spend
    FROM amazon_retail_purchases
    WHERE purchase_date_utc >= DATE_SUB(CURRENT_DATE(), INTERVAL 18 MONTH)
        AND marketplace_name = ''AMAZON.COM''  -- US market only
        AND asin_brand IS NOT NULL
    GROUP BY user_id, asin_brand
),
customer_brand_metrics AS (
    SELECT 
        user_id,
        MAX(brand_orders) as max_brand_orders,
        SUM(brand_orders) as total_orders
    FROM brand_purchases
    GROUP BY user_id
)
SELECT DISTINCT bp.user_id
FROM brand_purchases bp
JOIN customer_brand_metrics cbm ON bp.user_id = cbm.user_id
WHERE bp.brand_orders = cbm.max_brand_orders  -- Most purchased brand
    AND bp.brand_orders >= 3  -- At least 3 orders from the brand
    AND bp.brand_orders * 1.0 / cbm.total_orders >= 0.6;  -- 60%+ of orders from this brand', 'Basic', 11
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Purchase vs Event Relationship Analysis', '-- Understand purchase_id to event_id relationships
SELECT 
    COUNT(DISTINCT purchase_id) as unique_purchases,
    COUNT(DISTINCT event_id) as unique_events,
    COUNT(*) as total_rows,
    COUNT(*) * 1.0 / COUNT(DISTINCT purchase_id) as events_per_purchase,
    COUNT(*) * 1.0 / COUNT(DISTINCT event_id) as rows_per_event
FROM amazon_retail_purchases
WHERE purchase_date_utc >= ''2024-01-01'';', 'Basic', 12
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Data Completeness Analysis', '-- Analyze data completeness across key fields
SELECT 
    marketplace_name,
    COUNT(*) as total_records,
    COUNT(asin) as has_asin,
    COUNT(asin_brand) as has_brand,
    COUNT(asin_name) as has_name,
    COUNT(unit_price) as has_price,
    COUNT(user_id) as has_user_id,
    COUNT(asin_brand) * 100.0 / COUNT(*) as brand_completeness_pct,
    COUNT(unit_price) * 100.0 / COUNT(*) as price_completeness_pct
FROM amazon_retail_purchases
WHERE purchase_date_utc >= ''2024-01-01''
GROUP BY marketplace_name;', 'Basic', 13
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Source:** `amazon_retail_purchases`

The Amazon Retail Purchases (ARP) dataset enables advertisers to analyze **long-term (up to 60 months)** customer purchase behavior and create more comprehensive insights. This dataset provides retail purchase data sourced from Amazon''s retail data pipeline rather than advertising data pipeline.', 0
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'availability', '### Geographic Coverage
Available for measurement queries through Paid features subscription in:
- **United States**
- **Canada** 
- **Japan**
- **Australia**
- **United Kingdom**
- **France**
- **Germany**
- **Italy**
- **Spain**

⚠️ **Important**: Data from the United Kingdom and European Union (EU) regions will be **excluded from audience creation**.', 2
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'best_practices', '### Query Optimization
- **Use appropriate time windows**: Be mindful of 60-month vs 13-month data differences
- **Filter by marketplace**: Focus on relevant geographic markets
- **Leverage user_id in CTEs**: Due to VERY_HIGH aggregation threshold
- **Consider data volume**: 5 years of data requires efficient filtering', 5
FROM amc_data_sources 
WHERE schema_id = 'amazon-retail-purchases'
ON CONFLICT DO NOTHING;

-- Insert schema: Amazon Your Garage Tables
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'amazon-your-garage',
    'Amazon Your Garage Tables',
    'Core Tables',
    'Amazon Your Garage signals are available within an Amazon Marketing Cloud (AMC) account belonging to the **North America marketplaces** as an **AMC Paid Feature enrollment**. The Amazon Your Garage dataset includes signals across United States, Mexico, and Canada Amazon marketplaces.',
    '["amazon_your_garage", "amazon_your_garage_for_audiences"]',
    true,
    '[]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'MARKETPLACE_NAME', 'Dimension',
    'Dimension', 'THE MARKETPLACE ASSOCIATED WITH THE AMAZON GARAGE RECORD.', 0
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'USER_ID', 'Dimension',
    'Dimension', 'THE USER ID OF THE CUSTOMER OWNING THE VEHICLE.', 1
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'USER_ID_TYPE', 'Dimension',
    'Dimension', 'THE USER_ID TYPE.', 2
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'NO_3P_TRACKERS', 'Dimension',
    'Dimension', 'IS THIS ITEM NOT ALLOWED TO USE 3P TRACKING?', 3
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'CREATION_DATE', 'Dimension',
    'Dimension', 'CREATION DATE (IN UTC) OF THE RECORD.', 4
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'LAST_ACCESSED_DATE', 'Dimension',
    'Dimension', 'THE LAST ACCESSED DATE (IN UTC) FOR A CUSTOMER INVOKED INTERACTION WITH AN AMAZON GARAGE RECORD.', 5
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'UPDATE_DATE', 'Dimension',
    'Dimension', 'THE DATE (IN UTC) FOR THE MOST RECENT GARAGE RECORD EDIT.', 6
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'GARAGE_YEAR', 'Dimension',
    'Dimension', 'VEHICLE YEAR ATTRIBUTE.', 7
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'VEHICLE_TYPE', 'Dimension',
    'Dimension', 'VEHICLE TYPE ATTRIBUTE.', 8
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'GARAGE_MAKE', 'Dimension',
    'Dimension', 'VEHICLE MAKE ATTRIBUTE.', 9
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'GARAGE_MODEL', 'Dimension',
    'Dimension', 'VEHICLE MODEL ATTRIBUTE.', 10
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'GARAGE_SUBMODEL', 'Dimension',
    'Dimension', 'VEHICLE SUB-MODEL (TRIM) ATTRIBUTE.', 11
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'GARAGE_BODYSTYLE', 'Dimension',
    'Dimension', 'VEHICLE BODY STYLE ATTRIBUTE.', 12
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'GARAGE_ENGINE', 'Dimension',
    'Dimension', 'VEHICLE ENGINE ATTRIBUTE.', 13
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'GARAGE_TRANSMISSION', 'Dimension',
    'Dimension', 'VEHICLE TRANSMISSION ATTRIBUTE.', 14
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'GARAGE_DRIVETYPE', 'Dimension',
    'Dimension', 'VEHICLE DRIVE TYPE ATTRIBUTE.', 15
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Amazon Your Garage', 'GARAGE_BRAKES', 'Dimension',
    'Dimension', 'VEHICLE BRAKES ATTRIBUTE.', 16
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Vehicle Ownership Analysis', '-- Analyze vehicle distribution by make and model
SELECT 
    marketplace_name,
    garage_make,
    garage_model,
    garage_year,
    COUNT(DISTINCT user_id) as owner_count
FROM amazon_your_garage
WHERE marketplace_name = ''AMAZON.COM''
    AND garage_year >= ''2015''  -- Focus on newer vehicles
GROUP BY marketplace_name, garage_make, garage_model, garage_year
ORDER BY owner_count DESC;', 'Basic', 0
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Vehicle Type Segmentation', '-- Segment users by vehicle type and characteristics
SELECT 
    vehicle_type,
    garage_bodystyle,
    garage_drivetype,
    COUNT(DISTINCT user_id) as user_count
FROM amazon_your_garage
WHERE marketplace_name IN (''AMAZON.COM'', ''AMAZON_CA'')
GROUP BY vehicle_type, garage_bodystyle, garage_drivetype
ORDER BY user_count DESC;', 'Basic', 1
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Premium Vehicle Analysis', '-- Identify premium vehicle owners (example luxury brands)
SELECT 
    garage_make,
    garage_model,
    garage_submodel,
    garage_year,
    COUNT(DISTINCT user_id) as premium_owners
FROM amazon_your_garage
WHERE garage_make IN (''BMW'', ''Mercedes-Benz'', ''Audi'', ''Lexus'', ''Acura'')
    AND marketplace_name = ''AMAZON.COM''
GROUP BY garage_make, garage_model, garage_submodel, garage_year
ORDER BY premium_owners DESC;', 'Basic', 2
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Vehicle Age Analysis', '-- Analyze vehicle age distribution
WITH vehicle_age AS (
    SELECT 
        user_id,
        garage_make,
        garage_model,
        garage_year,
        CAST(EXTRACT(YEAR FROM CURRENT_DATE()) AS INT) - CAST(garage_year AS INT) as vehicle_age_years
    FROM amazon_your_garage
    WHERE garage_year IS NOT NULL
        AND garage_year != ''''
        AND marketplace_name = ''AMAZON.COM''
)
SELECT 
    CASE 
        WHEN vehicle_age_years <= 3 THEN ''0-3 years''
        WHEN vehicle_age_years <= 7 THEN ''4-7 years''
        WHEN vehicle_age_years <= 12 THEN ''8-12 years''
        ELSE ''13+ years''
    END as age_bracket,
    COUNT(DISTINCT user_id) as owner_count,
    COUNT(DISTINCT user_id) * 100.0 / SUM(COUNT(DISTINCT user_id)) OVER () as percentage
FROM vehicle_age
GROUP BY 
    CASE 
        WHEN vehicle_age_years <= 3 THEN ''0-3 years''
        WHEN vehicle_age_years <= 7 THEN ''4-7 years''
        WHEN vehicle_age_years <= 12 THEN ''8-12 years''
        ELSE ''13+ years''
    END;', 'Basic', 3
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'User Engagement Patterns', '-- Analyze user engagement with garage records
SELECT 
    marketplace_name,
    DATE_DIFF(CURRENT_DATE(), last_accessed_date, DAY) as days_since_access,
    COUNT(DISTINCT user_id) as users
FROM amazon_your_garage
WHERE last_accessed_date IS NOT NULL
GROUP BY marketplace_name, DATE_DIFF(CURRENT_DATE(), last_accessed_date, DAY)
HAVING days_since_access <= 365  -- Last year
ORDER BY marketplace_name, days_since_access;', 'Basic', 4
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Automotive Campaign Performance', '-- Analyze campaign performance for vehicle owners
-- (Using CTE for user_id due to VERY_HIGH aggregation threshold)
WITH garage_users AS (
    SELECT DISTINCT 
        user_id,
        garage_make,
        vehicle_type
    FROM amazon_your_garage
    WHERE marketplace_name = ''AMAZON.COM''
        AND garage_make IN (''Ford'', ''Chevrolet'', ''Toyota'', ''Honda'')
)
SELECT 
    g.garage_make,
    g.vehicle_type,
    SUM(a.total_purchases) as attributed_purchases,
    SUM(a.total_product_sales) as attributed_sales,
    COUNT(DISTINCT a.user_id) as converting_users
FROM garage_users g
JOIN amazon_attributed_events_by_conversion_time a
    ON g.user_id = a.user_id
WHERE a.conversion_event_date >= ''2025-01-01''
    AND a.conversion_event_category = ''purchase''
GROUP BY g.garage_make, g.vehicle_type
ORDER BY attributed_sales DESC;', 'Performance', 5
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Cross-Category Purchase Analysis', '-- Analyze purchase patterns by vehicle characteristics
WITH vehicle_owners AS (
    SELECT DISTINCT 
        user_id,
        garage_make,
        garage_bodystyle,
        garage_year
    FROM amazon_your_garage
    WHERE marketplace_name = ''AMAZON.COM''
        AND garage_year >= ''2020''
)
SELECT 
    v.garage_make,
    v.garage_bodystyle,
    COUNT(DISTINCT c.conversion_id) as total_conversions,
    SUM(c.total_product_sales) as total_sales
FROM vehicle_owners v
JOIN conversions c
    ON v.user_id = c.user_id
WHERE c.event_date_utc >= ''2025-01-01''
    AND c.event_category = ''purchase''
GROUP BY v.garage_make, v.garage_bodystyle
ORDER BY total_sales DESC;', 'Basic', 6
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Vehicle-Based Audience Segments', '-- Create audience of luxury vehicle owners
CREATE AUDIENCE luxury_vehicle_owners AS
SELECT DISTINCT user_id
FROM amazon_your_garage_for_audiences
WHERE garage_make IN (''BMW'', ''Mercedes-Benz'', ''Audi'', ''Lexus'', ''Infiniti'', ''Cadillac'')
    AND marketplace_name = ''AMAZON.COM''
    AND last_accessed_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY);

-- Create audience of truck owners
CREATE AUDIENCE truck_owners AS
SELECT DISTINCT user_id
FROM amazon_your_garage_for_audiences
WHERE vehicle_type = ''Truck''
    AND marketplace_name IN (''AMAZON.COM'', ''AMAZON_CA'')
    AND garage_year >= ''2018'';

-- Create audience of electric vehicle owners
CREATE AUDIENCE ev_owners AS
SELECT DISTINCT user_id
FROM amazon_your_garage_for_audiences
WHERE garage_make IN (''Tesla'', ''Rivian'', ''Lucid'')
    OR (garage_make = ''Chevrolet'' AND garage_model = ''Bolt'')
    OR (garage_make = ''Nissan'' AND garage_model = ''Leaf'')
    OR (garage_engine LIKE ''%Electric%'' OR garage_engine LIKE ''%EV%'');', 'Basic', 7
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Seasonal Campaign Targeting', '-- Create audience for winter tire campaign
CREATE AUDIENCE winter_driving_audience AS
SELECT DISTINCT user_id
FROM amazon_your_garage_for_audiences
WHERE marketplace_name IN (''AMAZON.COM'', ''AMAZON_CA'')  -- Cold weather markets
    AND garage_drivetype IN (''AWD'', ''4WD'', ''All-Wheel Drive'', ''Four-Wheel Drive'')
    AND last_accessed_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 180 DAY);', 'Basic', 8
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Make and Model Distribution', '-- Top vehicle makes and models
SELECT 
    garage_make,
    garage_model,
    COUNT(DISTINCT user_id) as owner_count,
    COUNT(DISTINCT user_id) * 100.0 / SUM(COUNT(DISTINCT user_id)) OVER () as market_share_percent
FROM amazon_your_garage
WHERE marketplace_name = ''AMAZON.COM''
GROUP BY garage_make, garage_model
ORDER BY owner_count DESC
LIMIT 50;', 'Basic', 9
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Feature Analysis', '-- Analyze vehicle features distribution
SELECT 
    garage_transmission,
    garage_drivetype,
    garage_bodystyle,
    COUNT(DISTINCT user_id) as users
FROM amazon_your_garage
WHERE marketplace_name = ''AMAZON.COM''
    AND garage_transmission IS NOT NULL
    AND garage_drivetype IS NOT NULL
    AND garage_bodystyle IS NOT NULL
GROUP BY garage_transmission, garage_drivetype, garage_bodystyle
ORDER BY users DESC;', 'Basic', 10
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Record Completeness Analysis', '-- Analyze data completeness across fields
SELECT 
    marketplace_name,
    COUNT(*) as total_records,
    COUNT(garage_year) as has_year,
    COUNT(garage_make) as has_make,
    COUNT(garage_model) as has_model,
    COUNT(garage_submodel) as has_submodel,
    COUNT(garage_engine) as has_engine,
    COUNT(garage_transmission) as has_transmission
FROM amazon_your_garage
GROUP BY marketplace_name;', 'Basic', 11
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'User Activity Analysis', '-- Analyze user engagement with garage records
SELECT 
    marketplace_name,
    DATE_DIFF(CURRENT_DATE(), creation_date, DAY) as days_since_creation,
    DATE_DIFF(CURRENT_DATE(), last_accessed_date, DAY) as days_since_access,
    DATE_DIFF(CURRENT_DATE(), update_date, DAY) as days_since_update,
    COUNT(DISTINCT user_id) as users
FROM amazon_your_garage
WHERE creation_date IS NOT NULL
    AND last_accessed_date IS NOT NULL
    AND update_date IS NOT NULL
GROUP BY marketplace_name, days_since_creation, days_since_access, days_since_update
ORDER BY marketplace_name, days_since_creation;', 'Basic', 12
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Sources:** 
- `amazon_your_garage`
- `amazon_your_garage_for_audiences`

Amazon Your Garage signals are available within an Amazon Marketing Cloud (AMC) account belonging to the **North America marketplaces** as an **AMC Paid Feature enrollment**. The Amazon Your Garage dataset includes signals across United States, Mexico, and Canada Amazon marketplaces.

**Dataset Type**: DIMENSION (not FACT) - no associated lookback, provides most recent user-to-vehicle associations only.', 0
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'query_patterns', '### Vehicle Ownership Analysis
```sql
-- Analyze vehicle distribution by make and model
SELECT 
    marketplace_name,
    garage_make,
    garage_model,
    garage_year,
    COUNT(DISTINCT user_id) as owner_count
FROM amazon_your_garage
WHERE marketplace_name = ''AMAZON.COM''
    AND garage_year >= ''2015''  -- Focus on newer vehicles
GROUP BY marketplace_name, garage_make, garage_model, garage_year
ORDER BY owner_count DESC;
```', 4
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'best_practices', '### Query Optimization
- **Use CTEs for user_id**: Due to VERY_HIGH aggregation threshold, use user_id in Common Table Expressions
- **Filter by marketplace**: Always include marketplace_name filtering for performance
- **Leverage recent activity**: Use last_accessed_date or update_date to focus on active users
- **Specific vehicle targeting**: Use detailed attributes for precise audience segmentation', 5
FROM amc_data_sources 
WHERE schema_id = 'amazon-your-garage'
ON CONFLICT DO NOTHING;

-- Insert schema: Amazon Audience Segment Membership Tables
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'audience-segments',
    'Amazon Audience Segment Membership Tables',
    'Audience Tables',
    '⚠️ **Important Performance Warning**: Workflows that use these tables will time out when run over extended periods of time.',
    '["audience_segments_amer_inmarket", "audience_segments_amer_lifestyle", "audience_segments_apac_inmarket", "audience_segments_apac_lifestyle", "audience_segments_eu_inmarket", "audience_segments_eu_lifestyle", "audience_segments_amer_inmarket_snapshot", "audience_segments_amer_lifestyle_snapshot", "audience_segments_apac_inmarket_snapshot", "audience_segments_apac_lifestyle_snapshot", "audience_segments_eu_inmarket_snapshot", "audience_segments_eu_lifestyle_snapshot", "segment_metadata"]',
    false,
    '["targeting", "audience", "segments"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Membership', 'NO_3P_TRACKERS', 'Dimension',
    'Dimension', 'IS THIS ITEM NOT ALLOWED TO USE 3P TRACKING?', 0
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Membership', 'SEGMENT_ID', 'Dimension',
    'Dimension', 'IDENTIFICATION CODE FOR THE SEGMENT. NOT GLOBALLY UNIQUE, BUT UNIQUE PER SEGMENT_MARKETPLACE_ID.', 1
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Membership', 'SEGMENT_MARKETPLACE_ID', 'Dimension',
    'Dimension', 'MARKETPLACE THE SEGMENT BELONGS TO; SEGMENTS CAN BELONG TO MULTIPLE MARKETPLACES.', 2
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Membership', 'SEGMENT_NAME', 'Dimension',
    'Dimension', 'NAME OF THE SEGMENT THE USER_ID IS TAGGED TO.', 3
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Membership', 'USER_ID', 'Dimension',
    'Dimension', 'USER ID OF THE CUSTOMER.', 4
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Membership', 'USER_ID_TYPE', 'Dimension',
    'Dimension', 'TYPE OF USER ID.', 5
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Membership', 'SNAPSHOT_DATETIME', 'Dimension',
    'Dimension', 'THE DATE WHEN SNAPSHOT WAS TAKEN (FIRST THURSDAY OF CALENDAR MONTH).', 6
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Metadata', 'CATEGORY_LEVEL_1', 'Dimension',
    'Dimension', 'TOP LEVEL OF THE AUDIENCE SEGMENT TAXONOMY.', 7
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Metadata', 'CATEGORY_LEVEL_2', 'Dimension',
    'Dimension', 'SECOND LEVEL OF THE AUDIENCE SEGMENT TAXONOMY.', 8
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Metadata', 'CATEGORY_PATH', 'Dimension',
    'Dimension', 'FULL PATH OF THE AUDIENCE SEGMENT TAXONOMY.', 9
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Metadata', 'NO_3P_TRACKERS', 'Dimension',
    'Dimension', 'IS THIS ITEM NOT ALLOWED TO USE 3P TRACKING?', 10
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Metadata', 'SEGMENT_DESCRIPTION', 'Dimension',
    'Dimension', 'DESCRIPTION OF THE SEGMENT.', 11
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Metadata', 'SEGMENT_ID', 'Dimension',
    'Dimension', 'IDENTIFICATION CODE FOR THE SEGMENT.', 12
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Metadata', 'SEGMENT_MARKETPLACE_ID', 'Dimension',
    'Dimension', 'THE MARKETPLACE THE SEGMENT BELONGS TO; SEGMENTS CAN BELONG TO MULTIPLE MARKETPLACES.', 13
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Audience Segment Metadata', 'SEGMENT_NAME', 'Dimension',
    'Dimension', 'NAME OF THE SEGMENT.', 14
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Basic Segment Membership Analysis', '-- Analyze current segment membership for AMER lifestyle segments
SELECT 
    s.segment_name,
    s.segment_description,
    COUNT(DISTINCT a.user_id) as member_count
FROM audience_segments_amer_lifestyle a
JOIN segment_metadata s 
    ON a.segment_id = s.segment_id 
    AND a.segment_marketplace_id = s.segment_marketplace_id
WHERE a.segment_marketplace_id = 1  -- Filter by marketplace
GROUP BY s.segment_name, s.segment_description
ORDER BY member_count DESC;', 'Basic', 0
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Segment Overlap Analysis', '-- Analyze overlap between specific segments (single region only)
WITH segment_users AS (
    SELECT 
        a.user_id,
        a.segment_id,
        s.segment_name
    FROM audience_segments_amer_inmarket a
    JOIN segment_metadata s 
        ON a.segment_id = s.segment_id 
        AND a.segment_marketplace_id = s.segment_marketplace_id
    WHERE a.segment_marketplace_id = 1
        AND a.segment_id IN (12345, 67890)  -- Specific segments
)
SELECT 
    COUNT(DISTINCT CASE WHEN segment_id = 12345 THEN user_id END) as segment_1_users,
    COUNT(DISTINCT CASE WHEN segment_id = 67890 THEN user_id END) as segment_2_users,
    COUNT(DISTINCT user_id) as total_unique_users
FROM segment_users;', 'Basic', 1
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Historical Trend Analysis', '-- Historical segment growth using snapshot data
SELECT 
    a.snapshot_datetime,
    s.segment_name,
    COUNT(DISTINCT a.user_id) as member_count
FROM audience_segments_eu_lifestyle_snapshot a
JOIN segment_metadata s 
    ON a.segment_id = s.segment_id 
    AND a.segment_marketplace_id = s.segment_marketplace_id
WHERE a.segment_marketplace_id = 3  -- EU marketplace
    AND a.segment_id = 98765  -- Specific segment
    AND a.snapshot_datetime >= ''2024-01-01''
    AND a.snapshot_datetime <= ''2024-12-31''
GROUP BY a.snapshot_datetime, s.segment_name
ORDER BY a.snapshot_datetime;', 'Basic', 2
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Campaign Performance by Segment', '-- Join segment membership with attributed conversions
-- (Example using single snapshot for performance)
SELECT 
    s.category_level_1,
    s.segment_name,
    COUNT(DISTINCT seg.user_id) as segment_members,
    SUM(conv.total_purchases) as attributed_purchases,
    SUM(conv.total_product_sales) as attributed_sales
FROM audience_segments_amer_inmarket seg
JOIN segment_metadata s 
    ON seg.segment_id = s.segment_id 
    AND seg.segment_marketplace_id = s.segment_marketplace_id
LEFT JOIN amazon_attributed_events_by_conversion_time conv
    ON seg.user_id = conv.user_id
WHERE seg.segment_marketplace_id = 1
    AND seg.segment_id IN (11111, 22222, 33333)  -- Specific segments
    AND conv.conversion_event_date >= ''2025-01-01''
    AND conv.conversion_event_date <= ''2025-01-31''
GROUP BY s.category_level_1, s.segment_name;', 'Performance', 3
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Example Category Structure', '-- Explore segment taxonomy
SELECT 
    category_level_1,
    category_level_2,
    category_path,
    COUNT(DISTINCT segment_id) as segment_count
FROM segment_metadata
WHERE segment_marketplace_id = 1  -- US marketplace
GROUP BY category_level_1, category_level_2, category_path
ORDER BY category_level_1, category_level_2;', 'Basic', 4
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Join Optimization', '-- Efficient join pattern
SELECT ...
FROM audience_segments_amer_lifestyle a
JOIN segment_metadata s 
    ON a.segment_id = s.segment_id 
    AND a.segment_marketplace_id = s.segment_marketplace_id
WHERE a.segment_marketplace_id = 1  -- Filter early
    AND a.segment_id IN (1001, 1002, 1003)  -- Specific segments', 'Basic', 5
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '⚠️ **Important Performance Warning**: Workflows that use these tables will time out when run over extended periods of time.

Amazon audience segment membership is presented across multiple data views with two distinct dataset types:
- **Default data views** (DIMENSION type): Most recent user-to-segment associations, refreshed daily
- **Historical snapshots** (FACT type): User-to-segment associations recorded on the first Thursday of each calendar month', 0
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'query_patterns', '### Basic Segment Membership Analysis
```sql
-- Analyze current segment membership for AMER lifestyle segments
SELECT 
    s.segment_name,
    s.segment_description,
    COUNT(DISTINCT a.user_id) as member_count
FROM audience_segments_amer_lifestyle a
JOIN segment_metadata s 
    ON a.segment_id = s.segment_id 
    AND a.segment_marketplace_id = s.segment_marketplace_id
WHERE a.segment_marketplace_id = 1  -- Filter by marketplace
GROUP BY s.segment_name, s.segment_description
ORDER BY member_count DESC;
```', 4
FROM amc_data_sources 
WHERE schema_id = 'audience-segments'
ON CONFLICT DO NOTHING;

-- Insert schema: conversions_all Data Source
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'conversions-all',
    'conversions_all Data Source',
    'Conversion Tables',
    'Contains both ad-exposed and non-ad-exposed conversions for tracked ASINs. Conversions are ad-exposed if a user was served a traffic event within the **28-day period** prior to the conversion event.',
    '[]',
    true,
    '["purchase", "conversion"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_id', 'STRING', 'Dimension',
    'Unique identifier of the conversion event. Each row has a unique conversion_id.', 'VERY_HIGH', 0
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversions', 'LONG', 'Metric',
    'Conversion count.', 'NONE', 1
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'exposure_type', 'STRING', 'Dimension',
    'Attribution of the conversion. For website and purchase conversions: ''ad-exposed'' if conversion happened within 28-days after a traffic event, else ''non-ad-exposed''. For pixel conversions, this field is always ''pixel''.', 'LOW', 2
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_category', 'STRING', 'Dimension',
    'For ASIN conversions: ''purchase'' or ''website''. For search conversions: always ''website''. For pixel conversions: always ''pixel''.', 'LOW', 3
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_date_utc', 'DATE', 'Dimension',
    'Date of the conversion event in UTC.', 'LOW', 4
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_day_utc', 'INTEGER', 'Dimension',
    'Day of the month of the conversion event in UTC.', 'LOW', 5
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt_hour_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the conversion event in UTC truncated to the hour.', 'LOW', 6
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the conversion event in UTC.', 'MEDIUM', 7
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_hour_utc', 'INTEGER', 'Dimension',
    'Hour of the day of the conversion event in UTC.', 'LOW', 8
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_source', 'STRING', 'Dimension',
    'System that generated the conversion event.', 'VERY_HIGH', 9
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_subtype', 'STRING', 'Dimension',
    'Subtype of conversion event. For ASIN conversions: ''alexaSkillEnable'', ''babyRegistry'', ''customerReview'', ''detailPageView'', ''order'', ''shoppingCart'', ''snsSubscription'', ''weddingRegistry'', ''wishList''. For search conversions: ''searchConversion''. For pixel conversions: numeric ID.', 'LOW', 10
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_type', 'STRING', 'Dimension',
    'Type of the conversion event.', 'LOW', 11
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_type_class', 'STRING', 'Dimension',
    'High level classification: ''consideration'', ''conversion'', etc. Blank for pixel and search conversions.', 'LOW', 12
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_type_description', 'STRING', 'Dimension',
    'Human-readable description of conversion event. Examples: ''Add to Shopping Cart'', ''Product purchased'', ''Product detail page viewed''. Blank for search conversions.', 'LOW', 13
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'marketplace_id', 'INTEGER', 'Dimension',
    'Marketplace ID where conversion occurred.', 'INTERNAL', 14
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'marketplace_name', 'STRING', 'Dimension',
    'Marketplace name (e.g., ''AMAZON.COM'', ''AMAZON.CO.UK'', ''WHOLE_FOODS_MARKET_US'').', 'LOW', 15
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'new_to_brand', 'BOOLEAN', 'Dimension',
    'True if the user was new to the brand (no purchase in previous 12 months).', 'LOW', 16
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'tracked_asin', 'STRING', 'Dimension',
    'The tracked ASIN (promoted or brand halo). Only populated for purchase events (event_category = ''purchase'').', 'LOW', 17
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'tracked_item', 'STRING', 'Dimension',
    'Identifier for conversion event item. Can be ASIN, pixel ID, branded search keyword, or app. When tracked_asin is populated, tracked_item has the same value.', 'LOW', 18
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_id', 'STRING', 'Dimension',
    'Pseudonymous user identifier. VERY_HIGH aggregation threshold - use in CTEs only.', 'VERY_HIGH', 19
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_event_source', 'STRING', 'Dimension',
    'Source through which conversion event was sent to Amazon DSP.', 'LOW', 20
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_event_name', 'STRING', 'Dimension',
    'Advertiser defined name for the conversion event.', 'LOW', 21
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'sns_subscription_id', 'STRING', 'Dimension',
    'Subscribe-and-save subscription ID.', 'INTERNAL', 22
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'purchase_currency', 'STRING', 'Dimension',
    'ISO currency code of the purchase order.', 'LOW', 23
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'purchase_unit_price', 'DECIMAL', 'Metric',
    'Unit price of the product sold.', 'NONE', 24
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'total_product_sales', 'DECIMAL', 'Metric',
    'Total sales (in local currency) of promoted ASINs and ASINs from the same brands as promoted ASINs purchased by customers on Amazon.', 'NONE', 25
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'total_units_sold', 'LONG', 'Metric',
    'Total quantity of promoted products and products from the same brand as promoted products purchased by customers on Amazon.', 'NONE', 26
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'off_amazon_product_sales', 'LONG', 'Metric',
    'Sales amount for off-Amazon purchase conversions.', 'NONE', 27
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'off_amazon_conversion_value', 'LONG', 'Metric',
    'Value of off Amazon non-purchase conversions. Value is unitless and advertiser defined.', 'NONE', 28
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'combined_sales', 'LONG', 'Metric',
    'Sum of total_product_sales (Amazon product sales) and off_amazon_product_sales.', 'NONE', 29
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Incrementality Calculation', '-- Basic incrementality analysis
SELECT 
    tracked_asin,
    SUM(CASE WHEN exposure_type = ''ad-exposed'' THEN conversions ELSE 0 END) as ad_exposed_conversions,
    SUM(CASE WHEN exposure_type = ''non-ad-exposed'' THEN conversions ELSE 0 END) as non_ad_exposed_conversions,
    SUM(CASE WHEN exposure_type = ''ad-exposed'' THEN total_product_sales ELSE 0 END) as ad_exposed_sales,
    SUM(CASE WHEN exposure_type = ''non-ad-exposed'' THEN total_product_sales ELSE 0 END) as non_ad_exposed_sales
FROM conversions_all
WHERE event_category = ''purchase''
    AND tracked_asin IS NOT NULL
GROUP BY tracked_asin;', 'Basic', 0
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Conversion Rate Impact', '-- Compare conversion rates by exposure type
SELECT 
    exposure_type,
    event_type_class,
    COUNT(*) as total_events,
    SUM(CASE WHEN event_category = ''purchase'' THEN conversions ELSE 0 END) as purchases,
    CASE 
        WHEN COUNT(*) > 0 
        THEN SUM(CASE WHEN event_category = ''purchase'' THEN conversions ELSE 0 END) * 100.0 / COUNT(*)
        ELSE 0 
    END as purchase_conversion_rate
FROM conversions_all
WHERE exposure_type IN (''ad-exposed'', ''non-ad-exposed'')
GROUP BY exposure_type, event_type_class;', 'Basic', 1
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'New-to-Brand Impact', '-- New-to-brand acquisition by exposure type
SELECT 
    exposure_type,
    new_to_brand,
    COUNT(*) as conversions,
    SUM(total_product_sales) as sales,
    AVG(purchase_unit_price) as avg_order_value
FROM conversions_all
WHERE event_category = ''purchase''
    AND new_to_brand IS NOT NULL
    AND exposure_type IN (''ad-exposed'', ''non-ad-exposed'')
GROUP BY exposure_type, new_to_brand;', 'Basic', 2
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Marketplace Performance', '-- Cross-marketplace exposure impact
SELECT 
    marketplace_name,
    exposure_type,
    SUM(conversions) as total_conversions,
    SUM(total_product_sales) as total_sales
FROM conversions_all
WHERE event_category = ''purchase''
GROUP BY marketplace_name, exposure_type
ORDER BY marketplace_name, total_sales DESC;', 'Performance', 3
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Time-Based Exposure Patterns', '-- Daily exposure type breakdown
SELECT 
    event_date_utc,
    exposure_type,
    SUM(conversions) as conversions,
    SUM(combined_sales) as total_sales
FROM conversions_all
WHERE event_category = ''purchase''
GROUP BY event_date_utc, exposure_type
ORDER BY event_date_utc, exposure_type;', 'Basic', 4
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Hour-of-Day Analysis', '-- Conversion patterns by hour and exposure
SELECT 
    event_hour_utc,
    exposure_type,
    COUNT(*) as conversion_events,
    AVG(total_product_sales) as avg_sales_per_conversion
FROM conversions_all
WHERE event_category = ''purchase''
    AND exposure_type IN (''ad-exposed'', ''non-ad-exposed'')
GROUP BY event_hour_utc, exposure_type
ORDER BY event_hour_utc, exposure_type;', 'Basic', 5
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'On-Amazon vs Off-Amazon', '-- Compare on-Amazon vs off-Amazon conversion patterns
SELECT 
    CASE 
        WHEN event_category IN (''purchase'', ''website'') THEN ''On-Amazon''
        WHEN event_category = ''pixel'' THEN ''Off-Amazon''
        ELSE ''Other''
    END as channel,
    exposure_type,
    SUM(conversions) as total_conversions,
    SUM(COALESCE(total_product_sales, 0)) as amazon_sales,
    SUM(COALESCE(off_amazon_product_sales, 0)) as off_amazon_sales
FROM conversions_all
GROUP BY 
    CASE 
        WHEN event_category IN (''purchase'', ''website'') THEN ''On-Amazon''
        WHEN event_category = ''pixel'' THEN ''Off-Amazon''
        ELSE ''Other''
    END,
    exposure_type;', 'Basic', 6
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Validation Queries', '-- Validate exposure type distribution
SELECT 
    exposure_type,
    COUNT(*) as conversion_count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
FROM conversions_all
GROUP BY exposure_type;

-- Check for data completeness
SELECT 
    event_date_utc,
    COUNT(CASE WHEN exposure_type = ''ad-exposed'' THEN 1 END) as ad_exposed,
    COUNT(CASE WHEN exposure_type = ''non-ad-exposed'' THEN 1 END) as non_ad_exposed,
    COUNT(CASE WHEN exposure_type = ''pixel'' THEN 1 END) as pixel
FROM conversions_all
WHERE event_date_utc >= ''2025-01-01''
GROUP BY event_date_utc
ORDER BY event_date_utc;', 'Basic', 7
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Source:** `conversions_all`

Contains both ad-exposed and non-ad-exposed conversions for tracked ASINs. Conversions are ad-exposed if a user was served a traffic event within the **28-day period** prior to the conversion event.

⚠️ **Important**: This data source is only available for measurement queries through **Paid feature subscription**. However, this data source can be used for AMC Audience creation without a Paid feature subscription.', 0
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'best_practices', '### Analysis Guidelines
- **Control for external factors** when comparing exposure types
- **Account for user selection bias** between exposed and non-exposed groups
- **Consider incrementality holistically** across the entire customer journey
- **Validate findings** with other measurement approaches when possible', 5
FROM amc_data_sources 
WHERE schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

-- Insert schema: conversions Data Source
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'conversions',
    'conversions Data Source',
    'Conversion Tables',
    'The conversions table contains AMC conversion events. Ad-attributed conversions for ASINs tracked to an Amazon DSP or sponsored ads campaigns and pixel conversions are included. Conversions are ad-attributed if a user was served a traffic event within the **28-day period** prior to the conversion event.',
    '[]',
    false,
    '["purchase", "conversion"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'combined_sales', 'LONG', 'Metric',
    'Sum of total_product_sales + off_Amazon_product_sales', 'NONE', 0
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversions', 'LONG', 'Metric',
    'The count of conversion events. This field always contains a value of 1, allowing you to calculate conversion totals for the records selected in your query. Conversion events can include on-Amazon activities like purchases and detail page views, as well as off-Amazon events measured through Events Manager. Possible values for this field are: ''1'' (the record represents a conversion event).', 'NONE', 1
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_event_name', 'STRING', 'Dimension',
    'The advertiser''s name of the conversion definition.', 'LOW', 2
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_event_source_name', 'STRING', 'Dimension',
    'The source of the advertiser-provided conversion data.', 'LOW', 3
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_id', 'STRING', 'Dimension',
    'Unique identifier of the conversion event. In the conversions table, each row has a unique conversion_id value.', 'VERY_HIGH', 4
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_category', 'STRING', 'Dimension',
    'High-level category of the conversion event. For ASIN conversions, this categorizes whether the event was a purchase or website browsing interaction. Website events include activities like detail page views, add to wishlist actions, and first Subscribe and Save orders. For conversions measured through Events Manager, this field is always ''off-Amazon''. Possible values include: ''purchase'', ''website'', and ''off-Amazon''.', 'LOW', 5
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_date_utc', 'DATE', 'Dimension',
    'Date of the conversion event in Coordinated Universal Time (UTC) timezone. Example value: ''2025-01-01''.', 'LOW', 6
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_day_utc', 'INTEGER', 'Dimension',
    'Day of month when the conversion event occurred in Coordinated Universal Time (UTC). Example value: ''1''.', 'LOW', 7
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt_hour_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the conversion event in Coordinated Universal Time (UTC) truncated to hour. Example value: ''2025-01-01T00:00:00.000Z''.', 'LOW', 8
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the conversion event in Coordinated Universal Time (UTC). Example value: ''2025-01-01T00:00:00.000Z''.', 'MEDIUM', 9
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_hour_utc', 'INTEGER', 'Dimension',
    'Hour of the day (0-23) when the conversion event occurred in Coordinated Universal Time (UTC) timezone. Example value: ''0''.', 'LOW', 10
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_subtype', 'STRING', 'Dimension',
    'Subtype of the conversion event. This field provides additional detail about the subtype of conversion event that occurred, such as whether it represents viewing a product''s detail page on Amazon.com or completing a purchase on an advertiser''s website. For on-Amazon conversion events, this field contains human-readable values, while off-Amazon events measured via Events Manager are represented by numeric values. Possible values include: ''detailPageView'', ''shoppingCart'', ''order'', ''searchConversion'', ''wishList'', ''babyRegistry'', ''weddingRegistry'', ''customerReview'' for on-Amazon events, and numeric values like ''134'', ''140'', ''141'' for off-Amazon events.', 'LOW', 11
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_type', 'STRING', 'Dimension',
    'Type of conversion event. Conversion events in AMC can include both on-Amazon events (like purchases and detail page views) and off-Amazon events (like website visits and app installs measured through Events Manager). This field will always have a value of ''CONVERSION''.', 'LOW', 12
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_type_class', 'STRING', 'Dimension',
    'Classification of conversion events based on customer behavior. This field categorizes conversion events into consideration events (like detail page views) versus actual conversion events (like purchases). Possible values include: ''consideration'', ''conversion'', and NULL.', 'LOW', 13
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_type_description', 'STRING', 'Dimension',
    'Human-readable description of the conversion event type. Conversion events can occur on Amazon (like product purchases or detail page views) or off Amazon (like brand site page views or in-store transactions measured via Events Manager). Example values: ''Product purchased'', ''Add to Shopping Cart'', ''Product detail page viewed''.', 'LOW', 14
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'marketplace_id', 'INTEGER', 'Dimension',
    'ID of the marketplace where the conversion event occurred. A marketplace represents a regional Amazon storefront where customers can make purchases (for example, Amazon.com, Amazon.co.uk).', 'LOW', 15
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'marketplace_name', 'STRING', 'Dimension',
    'Name of the marketplace where the conversion event occurred. A marketplace can be an online shopping site (like Amazon.com) or a physical retail location (like Amazon Fresh stores). This field helps distinguish between conversions that happen on different Amazon online marketplaces versus those that occur in Amazon''s physical retail locations. Example values include: ''AMAZON.COM'', ''AMAZON.CO.UK'', ''WHOLE_FOODS_MARKET_US'', and ''AMAZON_FRESH_STORES_US''.', 'LOW', 16
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'new_to_brand', 'BOOLEAN', 'Dimension',
    'Boolean value indicating whether the customer associated with a purchase event is new-to-brand. A customer is considered new-to-brand if they have not purchased from the brand in the previous 12 months. This field is only applicable for purchase events. Possible values for this field are: ''true'', ''false''.', 'LOW', 17
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'no_3p_trackers', 'BOOLEAN', 'Dimension',
    'Boolean value indicating whether the event can be used for audience creation that is third-party tracking enabled (i.e. whether you can serve creative with third-party tracking when running media against the audience). Third-party tracking refers to measurement tags and pixels from external vendors that can be used to measure ad performance. Possible values for this field are: ''true'', ''false''.', 'NONE', 18
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'off_amazon_conversion_value', 'LONG', 'Metric',
    'Non monetary "value" of conversion for non-purchase conversions', 'NONE', 19
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'off_amazon_product_sales', 'LONG', 'Metric',
    '"Value" of purchase conversions provided via Conversion Builder', 'NONE', 20
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'purchase_currency', 'STRING', 'Dimension',
    'ISO currency code of the purchase. Currency codes follow the ISO 4217 standard for representing currencies (e.g., USD for US Dollar). Example value: ''USD''.', 'LOW', 21
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'purchase_unit_price', 'STRING', 'Dimension',
    'The unit price of the product sold for on-Amazon purchase events, in local currency. This field represents the price per individual unit, not the total purchase price which may include multiple units. Example value: ''29.99''.', 'NONE', 22
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'total_product_sales', 'DECIMAL', 'Metric',
    'Product sales (in local currency) for on-Amazon purchase events. Example value: ''12.99''.', 'NONE', 23
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'total_units_sold', 'LONG', 'Metric',
    'Units sold for on-Amazon purchase events. Example value: ''3''.', 'NONE', 24
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'tracked_asin', 'STRING', 'Dimension',
    'The ASIN of the conversion event. An ASIN (Amazon Standard Identification Number) is a unique 10-character identifier assigned to products sold on Amazon. ASINs that appear in this field were either directly promoted by the campaign or are products from the same brand as the promoted ASINs. This field will only be for on-Amazon purchases (event_category = ''purchase''); for other conversion types, this field will be NULL. When this field is populated, tracked_item will have the same value. Example value: ''B01234ABCD''.', 'LOW', 25
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'tracked_item', 'STRING', 'Dimension',
    'Identifier for the conversion event item. The value in this field depends on the subtype of the conversion event. For ASIN-related conversions on Amazon such as purchases, detail page views, add to cart events, this field will contain the ASIN of the product. For branded search conversions on Amazon, this field will contain the ad-attributed branded search keyword. For off-Amazon conversions, this field will contain the ID of the conversion definition. Note that when tracked_asin is populated, the same value will appear in tracked_item.', 'LOW', 26
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_id', 'STRING', 'Dimension',
    'Pseudonymous identifier that connects user activity across different events. The field can contain ad user IDs (representing Amazon accounts), device IDs, or browser IDs. NULL values appear when Amazon Ads is unable to resolve an identifier for an event. The field has a VERY_HIGH aggregation threshold, meaning it cannot be included in final SELECT statements but can be used within Common Table Expressions (CTEs) for aggregation purposes like COUNT(DISTINCT user_id).', 'VERY_HIGH', 27
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_id_type', 'STRING', 'Dimension',
    'Type of user ID value. AMC includes different types of user ID values, depending on whether the value represents a resolved Amazon account, a device, or a browser cookie. If Amazon Ads is unable to determine or provide an ID of any kind for a conversion event, the ''user_id'' and ''user_id_type'' values for that record will be NULL. Possible values include: ''adUserId'', ''sisDeviceId'', ''adBrowserId'', and NULL.', 'LOW', 28
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Purchase Analysis', '-- Purchase conversions with sales data
SELECT 
    event_date_utc,
    COUNT(*) as purchase_conversions,
    SUM(total_product_sales) as total_sales,
    SUM(total_units_sold) as total_units,
    AVG(purchase_unit_price) as avg_unit_price
FROM conversions
WHERE event_category = ''purchase''
GROUP BY event_date_utc;', 'Basic', 0
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'New-to-Brand Analysis', '-- New vs existing customer purchases
SELECT 
    new_to_brand,
    COUNT(*) as conversions,
    SUM(total_product_sales) as sales
FROM conversions
WHERE event_category = ''purchase''
    AND new_to_brand IS NOT NULL
GROUP BY new_to_brand;', 'Basic', 1
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Conversion Funnel Analysis', '-- Conversion funnel by event type
SELECT 
    event_subtype,
    event_type_class,
    COUNT(*) as events,
    COUNT(DISTINCT user_id) as unique_users
FROM conversions
WHERE event_category IN (''website'', ''purchase'')
GROUP BY event_subtype, event_type_class
ORDER BY events DESC;', 'Basic', 2
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Cross-Channel Performance', '-- On-Amazon vs Off-Amazon conversions
SELECT 
    event_category,
    COUNT(*) as conversions,
    SUM(COALESCE(total_product_sales, 0)) as amazon_sales,
    SUM(COALESCE(off_amazon_product_sales, 0)) as off_amazon_sales
FROM conversions
GROUP BY event_category;', 'Performance', 3
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Source:** `conversions`

The conversions table contains AMC conversion events. Ad-attributed conversions for ASINs tracked to an Amazon DSP or sponsored ads campaigns and pixel conversions are included. Conversions are ad-attributed if a user was served a traffic event within the **28-day period** prior to the conversion event.', 0
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'concepts', '### Attribution Window
- **28-day attribution**: Conversions are attributed to ads if user was served a traffic event within 28 days prior to conversion
- **Cross-channel attribution**: Includes both Amazon DSP and Sponsored Ads campaigns', 3
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'query_patterns', '### Purchase Analysis
```sql
-- Purchase conversions with sales data
SELECT 
    event_date_utc,
    COUNT(*) as purchase_conversions,
    SUM(total_product_sales) as total_sales,
    SUM(total_units_sold) as total_units,
    AVG(purchase_unit_price) as avg_unit_price
FROM conversions
WHERE event_category = ''purchase''
GROUP BY event_date_utc;
```', 4
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'best_practices', '### Attribution Analysis
- Use `user_id` in CTEs for cross-event user journey analysis
- Consider 28-day attribution window when analyzing conversion timing
- Account for both direct and brand halo effects', 5
FROM amc_data_sources 
WHERE schema_id = 'conversions'
ON CONFLICT DO NOTHING;

-- Insert schema: conversions_with_relevance Data Source
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'conversions-with-relevance',
    'conversions_with_relevance Data Source',
    'Conversion Tables',
    'The data sources `conversions` and `conversions_with_relevance` are used to create custom attribution models both for ASIN conversions (purchases) and pixel conversions. This table extends the base conversions data with campaign attribution information.',
    '[]',
    true,
    '["purchase", "conversion"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser', 'STRING', 'Dimension',
    'Advertiser name.', 'LOW', 0
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_id', 'LONG', 'Dimension',
    'Advertiser ID.', 'LOW', 1
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_timezone', 'STRING', 'Dimension',
    'Time zone of the advertiser.', 'LOW', 2
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign', 'STRING', 'Dimension',
    'Campaign name.', 'LOW', 3
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_budget_amount', 'LONG', 'Dimension',
    'Campaign budget amount (millicents).', 'LOW', 4
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_end_date', 'DATE', 'Dimension',
    'Campaign end date in the advertiser time zone.', 'LOW', 5
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_end_date_utc', 'DATE', 'Dimension',
    'Campaign end date in UTC', 'LOW', 6
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_end_dt', 'TIMESTAMP', 'Dimension',
    'Campaign end timestamp in the advertiser time zone.', 'LOW', 7
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_end_dt_utc', 'TIMESTAMP', 'Dimension',
    'Campaign end timestamp in UTC', 'LOW', 8
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_id', 'LONG', 'Dimension',
    'Campaign ID.', 'LOW', 9
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_id_internal', 'LONG', 'Dimension',
    'The globally unique internal campaign ID.', 'INTERNAL', 10
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_id_string', 'STRING', 'Dimension',
    'Campaign ID as a string data_type, covers DSP and Sponsored Advertising campaign objects.', 'LOW', 11
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_sales_type', 'STRING', 'Dimension',
    'Campaign sales type', 'LOW', 12
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_source', 'STRING', 'Dimension',
    'Campaign source.', 'LOW', 13
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_start_date', 'DATE', 'Dimension',
    'Campaign start date in the advertiser time zone.', 'LOW', 14
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_start_date_utc', 'DATE', 'Dimension',
    'Campaign start date in UTC.', 'LOW', 15
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_start_dt', 'TIMESTAMP', 'Dimension',
    'Campaign start timestamp in the advertiser time zone.', 'LOW', 16
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_start_dt_utc', 'TIMESTAMP', 'Dimension',
    'Campaign start timestamp in UTC.', 'LOW', 17
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'targeting', 'STRING', 'Dimension',
    'The keyword used by advertiser for targeting.', 'LOW', 18
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_id', 'STRING', 'Dimension',
    'Unique identifier of the conversion event. In the dataset conversions, each row has a unique conversion_id. In the dataset conversions_with_relevance, the same conversion event will appear multiple times if a conversion is determined to be relevant to multiple campaigns, engagement scopes, or brand halo types.', 'VERY_HIGH', 19
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversions', 'LONG', 'Metric',
    'Conversion count.', 'NONE', 20
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'engagement_scope', 'STRING', 'Dimension',
    'The engagement scope between the campaign setup and the conversion. Possible values for this column are PROMOTED, BRAND_HALO, and null. See also the definition for halo_code. The engagement_scope will always be ''PROMOTED'' for pixel conversions (when event_category = ''pixel'').', 'LOW', 21
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_category', 'STRING', 'Dimension',
    'For ASIN conversions, the event_category is the high level category of the conversion event, either ''purchase'' or ''website''. Examples of ASIN conversions when event_category = ''website'' include: detail page views, add to wishlist, or the first Subscribe and Save order. For search conversions (when event_subtype = ''searchConversion''), the event_category is always ''website''. For pixel conversions, this field is always ''pixel''.', 'LOW', 22
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_date', 'DATE', 'Dimension',
    'Date of the conversion event in the advertiser time zone.', 'LOW', 23
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_date_utc', 'DATE', 'Dimension',
    'Date of the conversion event in UTC.', 'LOW', 24
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_day', 'INTEGER', 'Dimension',
    'Day of the month of the conversion event in the advertiser time zone.', 'LOW', 25
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_day_utc', 'INTEGER', 'Dimension',
    'Day of the month of the conversion event in UTC.', 'LOW', 26
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt', 'TIMESTAMP', 'Dimension',
    'Timestamp of the conversion event in the advertiser time zone.', 'MEDIUM', 27
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt_hour', 'TIMESTAMP', 'Dimension',
    'Timestamp of the conversion event in the advertiser time zone truncated to the hour.', 'LOW', 28
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt_hour_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the conversion event in UTC truncated to the hour.', 'LOW', 29
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the conversion event in UTC.', 'MEDIUM', 30
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_hour', 'INTEGER', 'Dimension',
    'Hour of the day of the conversion event in the advertiser time zone.', 'LOW', 31
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_hour_utc', 'INTEGER', 'Dimension',
    'Hour of the day of the conversion event in UTC.', 'LOW', 32
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_source', 'STRING', 'Dimension',
    'System that generated the conversion event.', 'VERY_HIGH', 33
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_subtype', 'STRING', 'Dimension',
    'Subtype of the conversion event. For ASIN conversions, the examples of event_subtype include: ''alexaSkillEnable'', ''babyRegistry'', ''customerReview'', ''detailPageView'', ''order'', ''shoppingCart'', ''snsSubscription'', ''weddingRegistry'', ''wishList''. For search conversions, event_subtype is always ''searchConversion''. For pixel conversions, the numeric ID of the event_subtype is provided.', 'LOW', 34
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_type', 'STRING', 'Dimension',
    'Type of the conversion event.', 'LOW', 35
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_type_class', 'STRING', 'Dimension',
    'For ASIN conversions, the event_type_class is the High level classification of the event type, e.g. consideration, conversion, etc. This field will be blank for pixel conversions (when event_category = ''pixel'') and search conversions (when event_subtype = ''searchConversion'').', 'LOW', 36
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_type_description', 'STRING', 'Dimension',
    'Human-readable description of the conversion event. For ASIN conversions, examples include: ''add to baby registry'', ''Add to Shopping Cart'', ''add to wedding registry'', ''add to wishlist'', ''Customer Reviews Page'', ''New SnS Subscription'', ''Product detail page viewed'', ''Product purchased''. This field will be blank for search conversions (when event_subtype = ''searchConversion''). For pixel conversions (when event_category = ''pixel''), the event_type_description will include additional information about the pixel based on information provided as part of the campaign setup.', 'LOW', 37
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'halo_code', 'STRING', 'Dimension',
    'The halo code between the campaign and conversion. Possible values for this column are TRACKED_ASIN, VARIATIONAL_ASIN, BRAND_KEYWORD, CATEGORY_KEYWORD, BRAND_MARKETPLACE, BRAND_GL_PRODUCT, BRAND_CATEGORY, BRAND_SUBCATEGORY, and null. See also the definition for engagement_scope. The halo_code will be NULL for pixel conversions (when event_category = ''pixel'').', 'LOW', 38
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'marketplace_id', 'INTEGER', 'Dimension',
    'Marketplace ID of where the conversion event occurred.', 'INTERNAL', 39
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'marketplace_name', 'STRING', 'Dimension',
    'Name of the marketplace where the conversion event occurred. Example values are online marketplaces such as AMAZON.COM, AMAZON.CO.UK. Or in-store marketplaces, such as WHOLE_FOODS_MARKET_US or AMAZON_FRESH_STORES_US.', 'LOW', 40
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'new_to_brand', 'BOOLEAN', 'Dimension',
    'True if the user was new to the brand.', 'LOW', 41
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'tracked_asin', 'STRING', 'Dimension',
    'The dimension tracked_asin is the tracked Amazon Standard Identification Number, which is either the promoted or brand halo ASIN. When the tracked_item results in a purchase conversion, the tracked_asin will be populated in this column, in addition to being tracked in the tracked_item column with the same ASIN value. The tracked_asin is populated only if the event_category = ''purchase''.', 'LOW', 42
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'tracked_item', 'STRING', 'Dimension',
    'Each campaign can track zero or more items. Depending on the type of campaign, these items might be ASINs, pixel IDs, DSP ad-attributed branded search keywords or apps. The tracked items for a campaign are the basis for which we determine which conversion events are sent to each AMC instance.', 'LOW', 43
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_id', 'STRING', 'Dimension',
    'User ID.', 'VERY_HIGH', 44
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_event_source', 'STRING', 'Dimension',
    'Source through which the conversion event was sent to Amazon DSP', 'LOW', 45
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'conversion_event_name', 'STRING', 'Dimension',
    'Advertiser defined name for the conversion event', 'LOW', 46
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'off_amazon_conversion_value', 'LONG', 'Metric',
    'Value of off Amazon non-purchase conversions. Value is unitless and advertiser defined.', 'NONE', 47
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'purchase_currency', 'STRING', 'Dimension',
    'ISO currency code of the purchase order.', 'LOW', 48
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'purchase_unit_price', 'DECIMAL', 'Metric',
    'Unit price of the product sold.', 'NONE', 49
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'total_product_sales', 'DECIMAL', 'Metric',
    'Total sales (in local currency) of promoted ASINs and ASINs from the same brands as promoted ASINs purchased by customers on Amazon.', 'NONE', 50
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'total_units_sold', 'LONG', 'Metric',
    'Total quantity of promoted products and products from the same brand as promoted products purchased by customers on Amazon. A campaign can have multiple units sold in a single purchase event.', 'NONE', 51
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'off_amazon_product_sales', 'LONG', 'Metric',
    'Sales amount for off-Amazon purchase conversions', 'NONE', 52
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'combined_sales', 'LONG', 'Metric',
    'Sum of total_product_sales (Amazon product sales) and off_amazon_product_sales', 'NONE', 53
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Campaign Attribution Analysis', '-- Attribution breakdown by engagement scope
SELECT 
    campaign,
    engagement_scope,
    COUNT(*) as conversions,
    SUM(total_product_sales) as attributed_sales
FROM conversions_with_relevance
WHERE event_category = ''purchase''
GROUP BY campaign, engagement_scope;', 'Attribution', 0
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Brand Halo Analysis', '-- Detailed halo effect breakdown
SELECT 
    campaign,
    halo_code,
    COUNT(*) as conversions,
    SUM(combined_sales) as total_sales,
    AVG(purchase_unit_price) as avg_unit_price
FROM conversions_with_relevance
WHERE event_category = ''purchase''
    AND engagement_scope = ''BRAND_HALO''
GROUP BY campaign, halo_code;', 'Basic', 1
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Cross-Campaign Attribution', '-- Find conversions attributed to multiple campaigns
WITH conversion_campaigns AS (
    SELECT 
        conversion_id,
        COUNT(DISTINCT campaign_id) as campaign_count,
        STRING_AGG(DISTINCT campaign, '', '') as attributed_campaigns
    FROM conversions_with_relevance
    GROUP BY conversion_id
)
SELECT * FROM conversion_campaigns
WHERE campaign_count > 1;', 'Attribution', 2
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Pixel vs ASIN Performance', '-- Compare pixel vs ASIN conversion performance
SELECT 
    event_category,
    COUNT(*) as conversions,
    SUM(COALESCE(combined_sales, off_amazon_conversion_value)) as total_value
FROM conversions_with_relevance
GROUP BY event_category;', 'Performance', 3
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Deduplication Considerations', '-- Count unique conversions (avoid double-counting)
SELECT 
    COUNT(DISTINCT conversion_id) as unique_conversions,
    COUNT(*) as total_attribution_records
FROM conversions_with_relevance;

-- Campaign-level unique conversions
SELECT 
    campaign,
    COUNT(DISTINCT conversion_id) as unique_conversions
FROM conversions_with_relevance
GROUP BY campaign;', 'Basic', 4
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Attribution Weight Distribution', '-- Understand attribution distribution per conversion
WITH attribution_depth AS (
    SELECT 
        conversion_id,
        COUNT(*) as attribution_count,
        STRING_AGG(DISTINCT engagement_scope, '', '') as scopes,
        STRING_AGG(DISTINCT halo_code, '', '') as halo_types
    FROM conversions_with_relevance
    GROUP BY conversion_id
)
SELECT 
    attribution_count,
    COUNT(*) as conversions_with_this_depth,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM attribution_depth
GROUP BY attribution_count
ORDER BY attribution_count;', 'Attribution', 5
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Source:** `conversions_with_relevance`

The data sources `conversions` and `conversions_with_relevance` are used to create custom attribution models both for ASIN conversions (purchases) and pixel conversions. This table extends the base conversions data with campaign attribution information.

**Key Difference from `conversions` table**: In `conversions_with_relevance`, **the same conversion event will appear multiple times** if a conversion is determined to be relevant to multiple campaigns, engagement scopes, or brand halo types.', 0
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'concepts', '### Record Multiplication
**Critical Understanding**: Unlike the base `conversions` table where each conversion appears once, in `conversions_with_relevance`:
- **Same conversion = Multiple rows** if relevant to multiple campaigns
- **Same conversion = Multiple rows** if has different engagement scopes (PROMOTED vs BRAND_HALO)
- **Same conversion = Multiple rows** if matches different halo codes', 3
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'query_patterns', '### Campaign Attribution Analysis
```sql
-- Attribution breakdown by engagement scope
SELECT 
    campaign,
    engagement_scope,
    COUNT(*) as conversions,
    SUM(total_product_sales) as attributed_sales
FROM conversions_with_relevance
WHERE event_category = ''purchase''
GROUP BY campaign, engagement_scope;
```', 4
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'best_practices', '### Query Performance
- **Filter early**: Use campaign_id, event_category, or date filters in WHERE clauses
- **Understand multiplicity**: Account for record multiplication in aggregations
- **Use DISTINCT**: Apply DISTINCT conversion_id when counting unique conversions', 5
FROM amc_data_sources 
WHERE schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;

-- Insert schema: dsp_clicks Data Source
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'dsp-clicks',
    'dsp_clicks Data Source',
    'DSP Tables',
    'The dsp_clicks table is a subset of the dsp_impressions information that captures the details impressions that were clicked and the associated click related information.',
    '[]',
    false,
    '["dsp", "impressions", "programmatic", "display", "clicks"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser', 'STRING', 'Dimension',
    'Name of the business entity running advertising campaigns on Amazon DSP. Example value: ''Widgets Inc''.', 'LOW', 0
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_account_frequency_group_ids', 'ARRAY', 'Dimension',
    'An array of the advertiser-account-level frequency group IDs that were applicable for this impression event. Frequency groups created at the advertiser account level may operate across 1 or more campaigns within that advertiser account. Note that a single impression may be subject to multiple frequency groups.', 'LOW', 1
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_country', 'STRING', 'Dimension',
    'Country of the Amazon DSP advertiser. This value is based on the country setting configured in the advertiser''s Amazon DSP account. Example value: ''US''.', 'LOW', 2
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_id', 'LONG', 'Dimension',
    'ID of the Amazon DSP advertiser associated with the click event. Example value: ''123456789012345''.', 'LOW', 3
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_timezone', 'STRING', 'Dimension',
    'Advertiser timezone. This setting aligns with the advertiser timezone configuration in the connected Amazon DSP account. Example value: ''America/New_York''.', 'LOW', 4
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'ad_slot_size', 'STRING', 'Dimension',
    'Ad slot size in which the Amazon DSP ad was served, expressed as width x height in pixels. The dimensions indicate the space allocated for the ad on the page or app where the impression was served. Example values: ''300x250'', ''728x90'', ''320x50''.', 'LOW', 5
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'app_bundle', 'STRING', 'Dimension',
    'The app bundle ID associated with the Amazon DSP click event. App bundles follow different formatting conventions depending on the app store.', 'LOW', 6
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'audience_fee', 'LONG', 'Metric',
    'The fee (in microcents) that Amazon DSP charges to customers to utilize Amazon audiences. Audience fees are typically charged on a cost-per-thousand impressions (CPM) basis when using audience segments for campaign targeting. To convert to dollars/your currency, divide by 100,000,000 (e.g., 100,000,000 microcents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: ''25000''.', 'NONE', 7
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'bid_price', 'LONG', 'Metric',
    'The bid price (in microcents) for the Amazon DSP impression. To convert to dollars/your currency, divide by 100,000,000 (e.g., 500,000 microcents = $0.005). Refer to the currency_name field for the currency in which the impression was purchased. Example value: ''500000''.', 'MEDIUM', 8
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'browser_family', 'STRING', 'Dimension',
    'Browser family used when viewing the Amazon DSP ad. Browser family represents a high-level grouping of web browsers and app contexts through which ads can be served, such as mobile browsers, desktop browsers, and application environments. Example values include: ''Chrome'', ''Safari'', ''Mobile Safari'', ''Android App'', ''iOS WebView'', and ''Roku App''.', 'LOW', 9
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign', 'STRING', 'Dimension',
    'Name of the Amazon DSP campaign responsible for the click event. A campaign is a container that groups related advertising efforts with shared objectives, budget, and flight dates. Example value: ''Widgets_Q1_2024_Awareness_Display_US''.', 'LOW', 10
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_budget_amount', 'LONG', 'Dimension',
    'The total budget allocated to the Amazon DSP campaign, stored in millicents. To convert to dollars/local currency, divide by 100,000 (e.g., 100,000 millicents = $1.00). Refer to the currency_name field for the budget currency. Example value: 100000000.', 'LOW', 11
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_end_date', 'TIMESTAMP', 'Dimension',
    'End date and time of the Amazon DSP campaign in advertiser timezone. Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 12
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_end_date_utc', 'TIMESTAMP', 'Dimension',
    'End date of the Amazon DSP campaign in Coordinated Universal Time (UTC). Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 13
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_flight_id', 'LONG', 'Dimension',
    'ID of the Amazon DSP campaign flight. A campaign flight represents a scheduled run period for an advertising campaign with defined start and end dates. Example value: ''123456789012345''.', 'LOW', 14
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_id', 'LONG', 'Dimension',
    'The ID of the Amazon DSP campaign responsible for the click event. In this table, campaign_id and campaign_id_string fields will show the same value for a given event. Example value: ''571234567890123456''.', 'LOW', 15
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_id_string', 'STRING', 'Dimension',
    'The ID of the Amazon DSP campaign responsible for the click event. In this table, campaign_id and campaign_id_string fields will show the same value for a given event. Example value: ''571234567890123456''.', 'LOW', 16
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_insertion_order_id', 'STRING', 'Dimension',
    'ID of the insertion order associated with the Amazon DSP click event. An insertion order is a contractual agreement between an advertiser and Amazon Ads that outlines the specific details of a programmatic advertising campaign. Example value: ''123456789''.', 'LOW', 17
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_primary_goal', 'STRING', 'Dimension',
    'Primary goal set for campaign optimization in Amazon DSP. Campaign goals determine how Amazon DSP optimizes delivery and measures success of the campaign. The goal selected during campaign setup influences bidding strategy and campaign optimization. Example values include: ''ROAS'', ''TOTAL_ROAS'', ''REACH'', ''CPVC'', ''COMPLETION_RATE'', ''CTR'', ''CPC'', ''DPVR'', ''PAGE_VISIT'', ''CPDPV'', ''CPA'' ''OTHER'', and ''NONE''.', 'LOW', 18
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_sales_type', 'STRING', 'Dimension',
    'Billing classification of the Amazon DSP campaign, which distinguishes billable and non-billable campaigns. Example values include: ''BILLABLE'' and ''BONUS''.', 'LOW', 19
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_source', 'STRING', 'Dimension',
    'Campaign source.', 'LOW', 20
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_start_date', 'TIMESTAMP', 'Dimension',
    'Start date and time of the Amazon DSP campaign in advertiser timezone. The campaign start date determines when a campaign begins serving impressions. Example value: ''2025-01-01T00:00:00.000Z''.', 'LOW', 21
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_start_date_utc', 'TIMESTAMP', 'Dimension',
    'Start date and time of the Amazon DSP campaign in Coordinated Universal Time (UTC). The campaign start date determines when a campaign begins serving impressions. Example value: ''2025-01-01T00:00:00.000Z''.', 'LOW', 22
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_status', 'STRING', 'Dimension',
    'Current status of the Amazon DSP campaign. Campaign status indicates whether a campaign is actively delivering ads, has completed its flight dates, or has been paused by the advertiser. Example values include: ''ENDED'', ''RUNNING'', ''ENABLED'', ''PAUSED'', and ''ADS_NOT_RUNNING''.', 'LOW', 23
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'city_name', 'STRING', 'Dimension',
    'City name where the Amazon DSP click event occurred, determined by signal available in the auction event. Example value: ''New York''.', 'HIGH', 24
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'clicks', 'LONG', 'Metric',
    'Count of Amazon DSP clicks. When querying this table, remember that each record represents one Amazon DSP click, so you can use this field to calculate accurate click totals. Since this table only includes click events, this field will always have a value of ''1'' (the event was a click event).', 'LOW', 25
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'click_cost', 'LONG', 'Metric',
    'Click cost (in millicents). To convert to dollars/local currency, divide by 100,000 (e.g., 100,000 millicents = $1.00). Refer to the currency_name field for the currency in which the click cost is reported. Example value: 300 (equivalent to $0.003).', 'MEDIUM', 26
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'click_date', 'DATE', 'Dimension',
    'Date of the Amazon DSP click event in advertiser timezone. This field will be populated for conversion events that are attributed to an ad view. Example value: ''2025-01-01''.', 'LOW', 27
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'click_date_utc', 'DATE', 'Dimension',
    'Date of the Amazon DSP click event in Coordinated Universal Time (UTC). This field will be populated for conversion events that are attributed to an ad view. Example value: ''2025-01-01''', 'LOW', 28
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'click_day', 'INTEGER', 'Dimension',
    'Day of month when the Amazon DSP click event occurred in advertiser timezone. Example value: ''1''.', 'LOW', 29
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'click_day_utc', 'INTEGER', 'Dimension',
    'Day of month when the Amazon DSP click event occurred in Coordinated Universal Time (UTC). Example value: ''1''.', 'LOW', 30
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'click_dt', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP click event in advertiser timezone. This field will be populated for conversion events that are attributed to an ad view. Example value: ''2025-01-01T12:00:00.000Z''.', 'MEDIUM', 31
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'click_dt_hour', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP click event in advertiser timezone, truncated to hour. This field will be populated for conversion events that are attributed to an ad view. Example value: ''2025-01-01T12:00:00.000Z''.', 'LOW', 32
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'click_dt_hour_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP click event in Coordinated Universal Time (UTC), truncated to hour. This field will be populated for conversion events that are attributed to an ad view. Example value: ''2025-01-01T12:00:00.000Z''.', 'LOW', 33
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'click_dt_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP click event in Coordinated Universal Time (UTC). This field will be populated for conversion events that are attributed to an ad view. Example value: ''2025-01-01T00:00:00.000Z''.', 'MEDIUM', 34
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'click_hour', 'INTEGER', 'Dimension',
    'Hour of day when the Amazon DSP click event occurred, in advertiser timezone. Values range from 0-23 representing 24-hour time. Example value: ''14'' (represents 2:00 PM in 24-hour time).', 'LOW', 35
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'click_hour_utc', 'INTEGER', 'Dimension',
    'Hour of day when the Amazon DSP click event occurred, in Coordinated Universal Time (UTC). Values range from 0-23 representing 24-hour time. Example value: ''14'' (represents 2:00 PM in 24-hour time).', 'LOW', 36
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative', 'STRING', 'Dimension',
    'Name of the Amazon DSP creative/ad. A creative represents the actual advertisement shown to customers. Example value: ''2025_US_Widgets_Spring_Mobile_320x50''.', 'LOW', 37
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_category', 'STRING', 'Dimension',
    'Category of the Amazon DSP creative/ad. This field categorizes Amazon DSP ads into broad creative format types like display ads and video ads. Possible values include: ''Display'', ''Video'', and NULL.', 'LOW', 38
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_duration', 'INTEGER', 'Dimension',
    'Duration in seconds of the Amazon DSP creative asset, primarily used for video format ads. This field specifies the length of video creative assets delivered through Amazon DSP campaigns. For non-video creative formats like display ads, this field will be NULL. Example values include: ''15'', ''30'', ''60'', representing video durations in seconds.', 'LOW', 39
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_id', 'LONG', 'Dimension',
    'Unique identifier for the Amazon DSP creative/ad. A ad represents the actual advertisement shown to customers, which could be an image, video, or other ad format. Example value: ''591234567890123456''.', 'LOW', 40
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_is_link_in', 'STRING', 'Dimension',
    'Boolean field indicating whether the Amazon DSP creative/ad directs to an Amazon destination (link in) versus an external destination (link out). A link in creative directs users to an Amazon destination like a product detail page, while a link out creative directs users to an external destination like an advertiser''s website. Example values for this field are: ''Y'' (creative is link in), ''N'' (creative is link out).', 'LOW', 41
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_size', 'STRING', 'Dimension',
    'Dimensions of the Amazon DSP creative/ad (width x height in pixels, or responsive format). Example values: ''300x250'', ''320x50'', ''Responsive''.', 'LOW', 42
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_type', 'STRING', 'Dimension',
    'Type of creative/ad.', 'LOW', 43
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'currency_iso_code', 'STRING', 'Dimension',
    'Currency ISO code associated with the monetary values in the table. The three-letter currency code follows the ISO 4217 standard format and is determined by the currency setting in the connected Amazon DSP account. Example value: ''USD''.', 'LOW', 44
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'currency_name', 'STRING', 'Dimension',
    'Currency name associated with the monetary values in the table. Currency is determined by the currency setting in the connected Amazon DSP account. Example value: ''Dollar (USA)''.', 'LOW', 45
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'deal_id', 'STRING', 'Dimension',
    'ID of the deal between the publisher and advertiser, for Amazon DSP impressions purchased via private deal (e.g. Private Marketplace or Programmatic Guaranteed deals). Deals represent agreements for access to specific ad inventory with pre-negotiated terms. This field will be NULL for traffic events purchased via open aution. Example value: ''DEAL123456''.', 'LOW', 46
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'deal_name', 'STRING', 'Dimension',
    'Name of the deal between the publisher and advertiser, for Amazon DSP impressions purchased via private deal e.g. Private Marketplace or Programmatic Guaranteed deals). Deals represent agreements for access to specific ad inventory with pre-negotiated terms. This field will be NULL for traffic events purchased via open aution. versus open auction inventory. Example value: ''Widgets_Premium_Video_Deal''.', 'LOW', 47
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'demand_channel', 'STRING', 'Dimension',
    'Demand channel name.', 'LOW', 48
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'demand_channel_owner', 'STRING', 'Dimension',
    'Demand channel owner.', 'LOW', 49
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'device_id', 'STRING', 'Dimension',
    'Pseudonymized ID representing the device associated with the Amazon DSP click event.', 'VERY_HIGH', 50
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'device_make', 'STRING', 'Dimension',
    'Manufacturer or brand name of the device associated with the Amazon DSP click event, derived from user-agent in the auction. Values may appear in different formats or capitalizations for the same manufacturer. Example values: ''Apple'', ''APPLE'', ''Samsung'', ''SAMSUNG'', ''ROKU'', ''Generic'', ''UNKNOWN''.', 'LOW', 51
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'device_model', 'STRING', 'Dimension',
    'Model of the device associated with the Amazon DSP click event, derived from user-agent in the auction. Values may appear in different formats or capitalizations for the same manufacturer. Example values: ''iPhone'', ''GALAXY''.', 'LOW', 52
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'device_type', 'STRING', 'Dimension',
    'Type of the device associated with the Amazon DSP click event. Possible values include: ''Tablet'', ''Phone'', ''TV'', ''PC'', ''ConnectedDevice'', ''Unknown'', and NULL.', 'LOW', 53
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'dma_code', 'STRING', 'Dimension',
    'Designated Market Area (DMA) code where the Amazon DSP click event occurred. DMA codes are geographic regions defined by Nielsen that identify specific broadcast TV markets in the United States. The field uses a standardized format combining "US-DMA" prefix with a numeric market identifier. Example value: ''US-DMA518''.', 'LOW', 54
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'entity_id', 'STRING', 'Dimension',
    'ID of the Amazon DSP entity (also known as seat) associated with the click. An entity represents an Amazon DSP account, within which media is further organized by advertiser and by campaign. Example value: ''ENTITYABC123XYZ789''.', 'LOW', 55
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'environment_type', 'STRING', 'Dimension',
    'Environment where the Amazon DSP click event occurred. This field distinguishes between web-based environments like desktop or mobile browsers, and app-based environments like mobile apps. If the environment type cannot be determined, this field will be NULL. Example values include: ''Web'', ''App'', and NULL.', 'LOW', 56
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_date', 'DATE', 'Dimension',
    'Date of the Amazon DSP impression event in advertiser timezone. Example value: ''2025-01-01''.', 'LOW', 57
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_date_utc', 'DATE', 'Dimension',
    'Date of the Amazon DSP impression event in Coordinated Universal Time (UTC). Example value: ''2025-01-01''', 'LOW', 58
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_day', 'INTEGER', 'Dimension',
    'Day of month when the Amazon DSP impression event occurred in advertiser timezone. Example value: ''1''.', 'LOW', 59
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_day_utc', 'INTEGER', 'Dimension',
    'Day of month when the Amazon DSP impression event occurred in Coordinated Universal Time (UTC). Example value: ''1''.', 'LOW', 60
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_dt', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP impression event in advertiser timezone. Example value: ''2025-01-01T12:00:00.000Z''.', 'MEDIUM', 61
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_dt_hour', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP impression event in advertiser timezone, truncated to hour. Example value: ''2025-01-01T12:00:00.000Z''.', 'LOW', 62
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_dt_hour_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP impression event in Coordinated Universal Time (UTC), truncated to hour. Example value: ''2025-01-01T12:00:00.000Z''.', 'LOW', 63
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_dt_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP impression event in Coordinated Universal Time (UTC). Example value: ''2025-01-01T00:00:00.000Z''.', 'MEDIUM', 64
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_hour', 'INTEGER', 'Dimension',
    'Hour of day when the Amazon DSP impression event occurred, in advertiser timezone. Values range from 0-23 representing 24-hour time. Example value: ''14'' (represents 2:00 PM in 24-hour time).', 'LOW', 65
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_hour_utc', 'INTEGER', 'Dimension',
    'Hour of day when the Amazon DSP impression event occurred, in Coordinated Universal Time (UTC). Values range from 0-23 representing 24-hour time. Example value: ''14'' (represents 2:00 PM in 24-hour time).', 'LOW', 66
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'iso_country_code', 'STRING', 'Dimension',
    'ISO 3166 Alpha-2 country code where the Amazon DSP click event occurred, based on the user''s IP address. Example value: ''US''.', 'LOW', 67
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'iso_state_province_code', 'STRING', 'Dimension',
    'ISO state/province code where the Amazon DSP click event occurred. The code follows the ISO 3166-2 standard format which combines the country code and state/province subdivision (e.g., ''US-CA'' for California, United States). Example value: ''US-CA''.', 'LOW', 68
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'is_amazon_owned', 'BOOLEAN', 'Dimension',
    'Boolean value indicating whether or not the Amazon DSP click occurred on Amazon-owned inventory. Amazon-owned inventory includes media such as Prime Video, IMDb, and Twitch. Example values for this field are: ''true'', ''false''.', 'LOW', 69
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item', 'STRING', 'Dimension',
    'Name of the Amazon DSP line item responsible for the click event. Attributes like ad format and targeting are defined at line item level within a campaign. Example value: ''Widgets - DISPLAY - O&O - RETARGETING''.', 'LOW', 70
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_budget_amount', 'LONG', 'Dimension',
    'The total budget allocated to the Amazon DSP line item, stored in millicents. To convert to dollars/local currency, divide by 100,000 (e.g., 100,000 millicents = $1.00). Refer to the currency_name field for the budget currency. Example value: ''100000000''.', 'LOW', 71
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_end_date', 'TIMESTAMP', 'Dimension',
    'End date and time of the Amazon DSP line item in advertiser timezone. Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 72
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_end_date_utc', 'TIMESTAMP', 'Dimension',
    'End date and time of the line item in Coordinated Universal Time (UTC). Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 73
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_id', 'LONG', 'Dimension',
    'ID of the Amazon DSP line item responsible for the click event. Attributes like ad format and targeting are defined at line item level within a campaign. Example value: ''5812345678901234''.', 'LOW', 74
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_price_type', 'STRING', 'Dimension',
    'Pricing model used for the Amazon DSP line item. Line items can use different pricing models to determine how costs are calculated, with Cost Per Mille (CPM) being a common model where advertisers pay per thousand impressions. Example value: ''CPM''.', 'LOW', 75
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_start_date', 'TIMESTAMP', 'Dimension',
    'Start date and time of the Amazon DSP line item in advertiser timezone. Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 76
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_start_date_utc', 'TIMESTAMP', 'Dimension',
    'Start date and time of the Amazon DSP line item in Coordinated Universal Time (UTC). Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 77
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_status', 'STRING', 'Dimension',
    'Status of the Amazon DSP line item. The status indicates whether the line item is actively delivering ads, has been paused, or has completed its flight. Example values include: ''ENDED'', ''ENABLED'', ''RUNNING'', ''PAUSED_BY_USER'', and ''SUSPENDED''.', 'LOW', 78
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_type', 'STRING', 'Dimension',
    'Type of Amazon DSP line item. Line item types indicate how ads are delivered and optimized. Example values include: ''AAP'', ''AAP_DISPLAY'', ''AAP_MOBILE'', ''AAP_VIDEO_CPM''.', 'LOW', 79
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'manager_account_frequency_group_ids', 'ARRAY', 'Dimension',
    'An array of the manager-account-level frequency group IDs that were applicable for this impression event. Frequency groups created at the manager account level may operate across 1 or more advertisers within that manager account. Note that a single impression may be subject to multiple frequency groups.', 'LOW', 80
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'merchant_id', 'LONG', 'Dimension',
    'Merchant ID.', 'LOW', 81
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'no_3p_trackers', 'BOOLEAN', 'Dimension',
    'Boolean value indicating whether the event can be used for audience creation that is third-party tracking enabled (i.e. whether you can serve creative with third-party tracking when running media against the audience). Third-party tracking refers to measurement tags and pixels from external vendors that can be used to measure ad performance. Example values for this field are: ''true'', ''false''.', 'NONE', 82
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'operating_system', 'STRING', 'Dimension',
    'Operating system of the device where the Amazon DSP click event occurred. Example values: ''iOS'', ''Android'', ''Windows'', ''macOS'', ''Roku OS''.', 'LOW', 83
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'os_version', 'STRING', 'Dimension',
    'Operating system version of the device where the Amazon DSP click event occurred. The version format varies by operating system type. Example value: ''17.5.1''.', 'LOW', 84
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'page_type', 'STRING', 'Dimension',
    'Type of page where the Amazon DSP click event occurred. This grain of detail is primarily relevant to impressions served on Amazon sites. Example values: ''Search'', ''Detail'', ''CustomerReviews''.', 'LOW', 85
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'platform_fee', 'LONG', 'Metric',
    'The fee (in microcents) that Amazon DSP charges to customers to access and use Amazon DSP. The platform fee (also known as the technology fee or console fee in other contexts) is calculated as a percentage of the supply cost. To convert to dollars/your currency, divide by 100,000,000 (e.g., 100,000,000 microcents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: ''25000''.', 'LOW', 86
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'postal_code', 'STRING', 'Dimension',
    'Postal code in which the Amazon DSP click event occurred, based on the user''s IP address. Postal code is also referred to as "zip code" in the US. The postal code is prepended with the iso_country_code value (e.g. ''US''). If the country is known, but the postal code is unknown, only the country code will be populated in postal_code. Example value: ''US-12345''.', 'HIGH', 87
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'product_line', 'STRING', 'Dimension',
    'Campaign product line.', 'LOW', 88
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'publisher_id', 'STRING', 'Dimension',
    'ID of the publisher on which the Amazon DSP click event occurred. A publisher is the media owner (such as a website, app, or streaming service owner) that makes advertising inventory available for purchase through Amazon DSP.', 'LOW', 89
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'request_dt', 'TIMESTAMP', 'Dimension',
    'Timestamp of the request event in advertiser timezone. Example value: ''2025-01-01T00:00:00.000Z''.', 'MEDIUM', 90
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'request_dt_hour', 'TIMESTAMP', 'Dimension',
    'Timestamp of the request event in advertiser timezone, truncated to hour. Example value: ''2025-01-01T12:00:00.000Z''.', 'LOW', 91
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'request_dt_hour_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the request event in Coordinated Universal Time (UTC), truncated to hour. Example value: ''2025-01-01T12:00:00.000Z''.', 'LOW', 92
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'request_dt_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the request event in Coordinated Universal Time (UTC). Example value: ''2025-01-01T00:00:00.000Z''.', 'MEDIUM', 93
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'request_tag', 'STRING', 'Dimension',
    'ID that connects related impression, view, click, and conversion events. For example, if an impression served has a request_tag value of ''X'', related conversion events will have have an impression_id value of ''X''. While this occurs infrequently, there are sometimes duplicate request_tag values. As a result, it is not recommended to use request_tag as a JOIN key without first grouping by it. Rather, it is a best practice to first consider using UNION ALL in a query instead of joining based on the request_tag to combine data sources. For insights that involve user-level ad exposure across tables, use user_id instead.', 'VERY_HIGH', 94
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'site', 'STRING', 'Dimension',
    'The site descriptor where the Amazon DSP click event occurred. A site can be any digital property where ads are served, including websites, mobile apps, and streaming platforms.', 'LOW', 95
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'slot_position', 'LONG', 'Metric',
    'Position of the ad on the page relative to the initial viewport. Above the fold (ATF) refers to the portion of the webpage visible without scrolling, while below the fold (BTF) refers to the portion that requires scrolling to view. This dimension helps measure where ad impressions were served on the page. Possible values include: ''ATF'', ''BTF'', and ''UNKNOWN''.', 'LOW', 96
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'supply_cost', 'STRING', 'Dimension',
    'The cost (in microcents) that Amazon DSP pays a publisher or publisher ad tech platform (such as an SSP or exchange) for an impression. To convert supply_cost to dollars/your local currency, divide by 100,000,000 (e.g., 100,000,000 microcents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: ''5000''.', 'LOW', 97
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'supply_source', 'STRING', 'Dimension',
    'Supply source from which the Amazon DSP impression was purchased. Supply sources can include Amazon-owned properties (like Amazon.com and Twitch), Amazon Publisher Services inventory, and third-party partners. Example values: ''AMAZON.COM'', ''TWITCH WEB VIDEO'', ''PUBMATIC WEB DISPLAY''.', 'LOW', 98
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'supply_source_id', 'LONG', 'Dimension',
    'ID of the supply source from which the Amazon DSP impression was purchased. Supply sources can include Amazon-owned properties (like Amazon.com and Twitch), Amazon Publisher Services inventory, and third-party partners.', 'LOW', 99
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_id', 'STRING', 'Dimension',
    'Pseudonymous identifier that connects user activity across different events. The field can contain ad user IDs (representing Amazon accounts), device IDs, or browser IDs. NULL values appear when Amazon Ads is unable to resolve an identifier for an event. The field has a VERY_HIGH aggregation threshold, meaning it cannot be included in final SELECT statements but can be used within Common Table Expressions (CTEs) for aggregation purposes like COUNT(DISTINCT user_id).', 'VERY_HIGH', 100
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_id_type', 'STRING', 'Dimension',
    'Type of user ID value. AMC includes different types of user ID values, depending on whether the value represents a resolved Amazon account, a device, or a browser cookie. If Amazon Ads is unable to determine or provide an ID of any kind for a click event, the ''user_id'' and ''user_id_type'' values for that record will be NULL. Example values include: ''adUserId'', ''sisDeviceId'', ''adBrowserId'', and NULL.', 'LOW', 101
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Source:** `dsp_clicks`

The dsp_clicks table is a subset of the dsp_impressions information that captures the details impressions that were clicked and the associated click related information.', 0
FROM amc_data_sources 
WHERE schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

-- Insert schema: dsp_impressions Data Source
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'dsp-impressions',
    'dsp_impressions Data Source',
    'DSP Tables',
    'Records of all impressions delivered to viewers. This table contains the most granular record of every impression delivered, allowing you to query all viewers reached through an Amazon DSP campaign.',
    '[]',
    false,
    '["dsp", "impressions", "programmatic", "display", "clicks"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'ad_slot_size', 'STRING', 'Dimension',
    'Ad slot size in which the Amazon DSP ad was served, expressed as width x height in pixels. The dimensions indicate the space allocated for the ad on the page or app where the impression was served. Example values: ''300x250'', ''728x90'', ''320x50''.', 'LOW', 0
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser', 'STRING', 'Dimension',
    'Name of the business entity running advertising campaigns on Amazon DSP. Example value: ''Widgets Inc''.', 'LOW', 1
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_account_frequency_group_ids', 'ARRAY', 'Dimension',
    'An array of the advertiser-account-level frequency group IDs that were applicable for this impression event. Frequency groups created at the advertiser account level may operate across 1 or more campaigns within that advertiser account. Note that a single impression may be subject to multiple frequency groups.', 'LOW', 2
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_country', 'STRING', 'Dimension',
    'Country of the Amazon DSP advertiser. This value is based on the country setting configured in the advertiser''s Amazon DSP account. Example value: ''US''.', 'LOW', 3
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_id', 'LONG', 'Dimension',
    'ID of the Amazon DSP advertiser associated with the impression event. Example value: ''123456789012345''.', 'LOW', 4
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_timezone', 'STRING', 'Dimension',
    'Advertiser timezone. This setting aligns with the advertiser timezone configuration in the connected Amazon DSP account. Example value: ''America/New_York''.', 'LOW', 5
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'app_bundle', 'STRING', 'Dimension',
    'The app bundle ID associated with the Amazon DSP impression. App bundles follow different formatting conventions depending on the app store.', 'LOW', 6
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'audience_fee', 'LONG', 'Metric',
    'The fee (in microcents) that Amazon DSP charges to customers to utilize Amazon audiences. Audience fees are typically charged on a cost-per-thousand impressions (CPM) basis when using audience segments for campaign targeting. To convert to dollars/your currency, divide by 100,000,000 (e.g., 100,000,000 microcents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: ''25000''.', 'NONE', 7
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'bid_price', 'LONG', 'Metric',
    'The bid price (in microcents) for the Amazon DSP impression. To convert to dollars/your currency, divide by 100,000,000 (e.g., 500,000 microcents = $0.005). Refer to the currency_name field for the currency in which the impression was purchased. Example value: ''500000''.', 'MEDIUM', 8
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'browser_family', 'STRING', 'Dimension',
    'Browser family used when viewing the Amazon DSP ad. Browser family represents a high-level grouping of web browsers and app contexts through which ads can be served, such as mobile browsers, desktop browsers, and application environments. Example values include: ''Chrome'', ''Safari'', ''Mobile Safari'', ''Android App'', ''iOS WebView'', and ''Roku App''.', 'LOW', 9
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign', 'STRING', 'Dimension',
    'Name of the Amazon DSP campaign responsible for the impression event. A campaign is a container that groups related advertising efforts with shared objectives, budget, and flight dates. Example value: ''Widgets_Q1_2024_Awareness_Display_US''.', 'LOW', 10
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_budget_amount', 'LONG', 'Dimension',
    'The total budget allocated to the Amazon DSP campaign, stored in millicents. To convert to dollars/local currency, divide by 100,000 (e.g., 100,000 millicents = $1.00). Refer to the currency_name field for the budget currency. Example value: 100000000.', 'LOW', 11
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_end_date', 'TIMESTAMP', 'Dimension',
    'End date and time of the Amazon DSP campaign in advertiser timezone. Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 12
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_end_date_utc', 'TIMESTAMP', 'Dimension',
    'End date of the Amazon DSP campaign in Coordinated Universal Time (UTC). Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 13
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_flight_id', 'LONG', 'Dimension',
    'ID of the Amazon DSP campaign flight. A campaign flight represents a scheduled run period for an advertising campaign with defined start and end dates. Example value: ''123456789012345''.', 'LOW', 14
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_id', 'LONG', 'Dimension',
    'The ID of the Amazon DSP campaign responsible for the impression event. In this table, campaign_id and campaign_id_string fields will show the same value for a given event. Example value: ''571234567890123456''.', 'LOW', 15
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_id_string', 'STRING', 'Dimension',
    'The ID of the Amazon DSP campaign responsible for the impression event. In this table, campaign_id and campaign_id_string fields will show the same value for a given event. Example value: ''571234567890123456''.', 'LOW', 16
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_insertion_order_id', 'STRING', 'Dimension',
    'ID of the insertion order associated with the Amazon DSP impression event. An insertion order is a contractual agreement between an advertiser and Amazon Ads that outlines the specific details of a programmatic advertising campaign. Example value: ''123456789''.', 'LOW', 17
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_primary_goal', 'STRING', 'Dimension',
    'Primary goal set for campaign optimization in Amazon DSP. Campaign goals determine how Amazon DSP optimizes delivery and measures success of the campaign. The goal selected during campaign setup influences bidding strategy and campaign optimization. Possible values include: ''ROAS'', ''TOTAL_ROAS'', ''REACH'', ''CPVC'', ''COMPLETION_RATE'', ''CTR'', ''CPC'', ''DPVR'', ''PAGE_VISIT'', ''CPDPV'', ''CPA'' ''OTHER'', and ''NONE''.', 'LOW', 18
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_sales_type', 'STRING', 'Dimension',
    'Billing classification of the Amazon DSP campaign, which distinguishes billable and non-billable campaigns. Possible values include: ''BILLABLE'' and ''BONUS''.', 'LOW', 19
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_source', 'STRING', 'Dimension',
    'Campaign source.', 'LOW', 20
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_start_date', 'TIMESTAMP', 'Dimension',
    'Start date and time of the Amazon DSP campaign in advertiser timezone. The campaign start date determines when a campaign begins serving impressions. Example value: ''2025-01-01T00:00:00.000Z''.', 'LOW', 21
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_start_date_utc', 'TIMESTAMP', 'Dimension',
    'Start date and time of the Amazon DSP campaign in Coordinated Universal Time (UTC). The campaign start date determines when a campaign begins serving impressions. Example value: ''2025-01-01T00:00:00.000Z''.', 'LOW', 22
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_status', 'STRING', 'Dimension',
    'Current status of the Amazon DSP campaign. Campaign status indicates whether a campaign is actively delivering ads, has completed its flight dates, or has been paused by the advertiser. Possible values include: ''ENDED'', ''RUNNING'', ''ENABLED'', ''PAUSED'', and ''ADS_NOT_RUNNING''.', 'LOW', 23
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'city_name', 'STRING', 'Dimension',
    'City name where the Amazon DSP impression event occurred, determined by signal available in the auction event. Example value: ''New York''.', 'HIGH', 24
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative', 'STRING', 'Dimension',
    'Name of the Amazon DSP creative/ad. A creative represents the actual advertisement shown to customers. Example value: ''2025_US_Widgets_Spring_Mobile_320x50''.', 'LOW', 25
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_category', 'STRING', 'Dimension',
    'Category of the Amazon DSP creative/ad. This field categorizes Amazon DSP ads into broad creative format types like display ads and video ads. Possible values include: ''Display'', ''Video'', and NULL.', 'LOW', 26
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_duration', 'INTEGER', 'Dimension',
    'Duration in seconds of the Amazon DSP creative asset, primarily used for video format ads. This field specifies the length of video creative assets delivered through Amazon DSP campaigns. For non-video creative formats like display ads, this field will be NULL. Example values include: ''15'', ''30'', ''60'', representing video durations in seconds.', 'LOW', 27
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_id', 'LONG', 'Dimension',
    'Unique identifier for the Amazon DSP creative/ad. A ad represents the actual advertisement shown to customers, which could be an image, video, or other ad format. Example value: ''591234567890123456''.', 'LOW', 28
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_is_link_in', 'STRING', 'Dimension',
    'Boolean field indicating whether the Amazon DSP creative/ad directs to an Amazon destination (link in) versus an external destination (link out). A link in creative directs users to an Amazon destination like a product detail page, while a link out creative directs users to an external destination like an advertiser''s website. Possible values for this field are: ''Y'' (creative is link in), ''N'' (creative is link out).', 'LOW', 29
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_size', 'STRING', 'Dimension',
    'Dimensions of the Amazon DSP creative/ad (width x height in pixels, or responsive format). Example values: ''300x250'', ''320x50'', ''Responsive''.', 'LOW', 30
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_type', 'STRING', 'Dimension',
    'Type of creative/ad.', 'LOW', 31
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'currency_iso_code', 'STRING', 'Dimension',
    'Currency ISO code associated with the monetary values in the table. The three-letter currency code follows the ISO 4217 standard format and is determined by the currency setting in the connected Amazon DSP account. Example value: ''USD''.', 'LOW', 32
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'currency_name', 'STRING', 'Dimension',
    'Currency name associated with the monetary values in the table. Currency is determined by the currency setting in the connected Amazon DSP account. Example value: ''Dollar (USA)''.', 'LOW', 33
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'deal_id', 'STRING', 'Dimension',
    'ID of the deal between the publisher and advertiser, for Amazon DSP impressions purchased via private deal (e.g. Private Marketplace or Programmatic Guaranteed deals). Deals represent agreements for access to specific ad inventory with pre-negotiated terms. This field will be NULL for traffic events purchased via open aution. Example value: ''DEAL123456''.', 'LOW', 34
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'deal_name', 'STRING', 'Dimension',
    'Name of the deal between the publisher and advertiser, for Amazon DSP impressions purchased via private deal e.g. Private Marketplace or Programmatic Guaranteed deals). Deals represent agreements for access to specific ad inventory with pre-negotiated terms. This field will be NULL for traffic events purchased via open aution. versus open auction inventory. Example value: ''Widgets_Premium_Video_Deal''.', 'LOW', 35
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'demand_channel', 'STRING', 'Dimension',
    'Demand channel name.', 'VERY_HIGH', 36
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'demand_channel_owner', 'STRING', 'Dimension',
    'Demand channel owner.', 'LOW', 37
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'device_id', 'STRING', 'Dimension',
    'Pseudonymized ID representing the device associated with the Amazon DSP impression event.', 'LOW', 38
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'device_make', 'STRING', 'Dimension',
    'Manufacturer or brand name of the device associated with the Amazon DSP impression event, derived from user-agent in the auction. Values may appear in different formats or capitalizations for the same manufacturer. Example values: ''Apple'', ''APPLE'', ''Samsung'', ''SAMSUNG'', ''ROKU'', ''Generic'', ''UNKNOWN''.', 'LOW', 39
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'device_model', 'STRING', 'Dimension',
    'Model of the device associated with the Amazon DSP impression event, derived from user-agent in the auction. Values may appear in different formats or capitalizations for the same manufacturer. Example values: ''iPhone'', ''GALAXY''.', 'LOW', 40
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'device_type', 'STRING', 'Dimension',
    'Type of the device associated with the Amazon DSP impression event. Possible values include: ''Tablet'', ''Phone'', ''TV'', ''PC'', ''ConnectedDevice'', ''Unknown'', and NULL.', 'LOW', 41
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'dma_code', 'STRING', 'Dimension',
    'Designated Market Area (DMA) code where the Amazon DSP impression event occurred. DMA codes are geographic regions defined by Nielsen that identify specific broadcast TV markets in the United States. The field uses a standardized format combining "US-DMA" prefix with a numeric market identifier. Example value: ''US-DMA518''.', 'LOW', 42
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'entity_id', 'STRING', 'Dimension',
    'ID of the Amazon DSP entity (also known as seat) associated with the impression. An entity represents an Amazon DSP account, within which media is further organized by advertiser and by campaign. Example value: ''ENTITYABC123XYZ789''.', 'NONE', 43
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'environment_type', 'STRING', 'Dimension',
    'Environment where the Amazon DSP impression event occurred. This field distinguishes between web-based environments like desktop or mobile browsers, and app-based environments like mobile apps. If the environment type cannot be determined, this field will be NULL. Possible values include: ''Web'', ''App'', and NULL.', 'LOW', 44
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_cost', 'LONG', 'Metric',
    'The cost of the Amazon DSP impression event in millicents (where 100,000 millicents = $1.00). To convert to dollars/your currency, divide by 100,000. Refer to the currency_name field for the currency in which the impression was purchased. Example value: 300 (equivalent to $0.003).', 'LOW', 45
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_date', 'DATE', 'Dimension',
    'Date of the Amazon DSP impression event in advertiser timezone. Example value: ''2025-01-01''.', 'LOW', 46
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_date_utc', 'DATE', 'Dimension',
    'Date of the Amazon DSP impression event in Coordinated Universal Time (UTC). Example value: ''2025-01-01''', 'LOW', 47
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_day', 'INTEGER', 'Dimension',
    'Day of month when the Amazon DSP impression event occurred in advertiser timezone. Example value: ''1''.', 'MEDIUM', 48
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_day_utc', 'INTEGER', 'Dimension',
    'Day of month when the Amazon DSP impression event occurred in Coordinated Universal Time (UTC). Example value: ''1''.', 'LOW', 49
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_dt', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP impression event in advertiser timezone. Example value: ''2025-01-01T12:00:00.000Z''.', 'LOW', 50
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_dt_hour', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP impression event in advertiser timezone, truncated to hour. Example value: ''2025-01-01T12:00:00.000Z''.', 'MEDIUM', 51
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_dt_hour_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP impression event in Coordinated Universal Time (UTC), truncated to hour. Example value: ''2025-01-01T12:00:00.000Z''.', 'LOW', 52
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_dt_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP impression event in Coordinated Universal Time (UTC). Example value: ''2025-01-01T00:00:00.000Z''.', 'LOW', 53
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_hour', 'INTEGER', 'Dimension',
    'Hour of day when the Amazon DSP impression event occurred, in advertiser timezone. Values range from 0-23 representing 24-hour time. Example value: ''14'' (represents 2:00 PM in 24-hour time).', 'NONE', 54
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_hour_utc', 'INTEGER', 'Dimension',
    'Hour of day when the Amazon DSP impression event occurred, in Coordinated Universal Time (UTC). Values range from 0-23 representing 24-hour time. Example value: ''14'' (represents 2:00 PM in 24-hour time).', 'LOW', 55
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impressions', 'LONG', 'Metric',
    'Count of Amazon DSP impressions. When querying this table, remember that each record represents one Amazon DSP impression, so you can use this field to calculate accurate impression totals. Since this table only includes impression events, this field will always have a value of ''1'' (the event was an impression event).', 'LOW', 56
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'is_amazon_owned', 'BOOLEAN', 'Dimension',
    'Boolean value indicating whether or not the Amazon DSP impression appeared on Amazon-owned inventory. Amazon-owned inventory includes media such as Prime Video, IMDb, and Twitch. Possible values for this field are: ''true'', ''false''.', 'LOW', 57
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'iso_country_code', 'STRING', 'Dimension',
    'ISO 3166 Alpha-2 country code where the Amazon DSP impression event occurred, based on the user''s IP address. Example value: ''US''.', 'LOW', 58
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'iso_state_province_code', 'STRING', 'Dimension',
    'ISO state/province code where the Amazon DSP impression event occurred. The code follows the ISO 3166-2 standard format which combines the country code and state/province subdivision (e.g., ''US-CA'' for California, United States). Example value: ''US-CA''.', 'LOW', 59
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item', 'STRING', 'Dimension',
    'Name of the Amazon DSP line item responsible for the impression event. Attributes like ad format and targeting are defined at line item level within a campaign. Example value: ''Widgets - DISPLAY - O&O - RETARGETING''.', 'LOW', 60
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_budget_amount', 'LONG', 'Dimension',
    'The total budget allocated to the Amazon DSP line item, stored in millicents. To convert to dollars/local currency, divide by 100,000 (e.g., 100,000 millicents = $1.00). Refer to the currency_name field for the budget currency. Example value: ''100000000''.', 'LOW', 61
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_end_date', 'TIMESTAMP', 'Dimension',
    'End date and time of the Amazon DSP line item in advertiser timezone. Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 62
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_end_date_utc', 'TIMESTAMP', 'Dimension',
    'End date and time of the Amazon DSP line item in Coordinated Universal Time (UTC). Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 63
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_id', 'LONG', 'Dimension',
    'ID of the Amazon DSP line item responsible for the impression event. Attributes like ad format and targeting are defined at line item level within a campaign. Example value: ''5812345678901234''.', 'LOW', 64
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_price_type', 'STRING', 'Dimension',
    'Pricing model used for the Amazon DSP line item. Line items can use different pricing models to determine how costs are calculated, with Cost Per Mille (CPM) being a common model where advertisers pay per thousand impressions. Example value: ''CPM''.', 'LOW', 65
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_start_date', 'TIMESTAMP', 'Dimension',
    'Start date and time of the Amazon DSP line item in advertiser timezone. Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 66
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_start_date_utc', 'TIMESTAMP', 'Dimension',
    'Start date and time of the Amazon DSP line item in Coordinated Universal Time (UTC). Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 67
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_status', 'STRING', 'Dimension',
    'Status of the Amazon DSP line item. The status indicates whether the line item is actively delivering ads, has been paused, or has completed its flight. Possible values include: ''ENDED'', ''ENABLED'', ''RUNNING'', ''PAUSED_BY_USER'', and ''SUSPENDED''.', 'NONE', 68
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_type', 'STRING', 'Dimension',
    'Type of Amazon DSP line item. Line item types indicate how ads are delivered and optimized. Example values include: ''AAP'', ''AAP_DISPLAY'', ''AAP_MOBILE'', ''AAP_VIDEO_CPM''.', 'LOW', 69
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'managed_service_fee', 'LONG', 'Metric',
    'The fee (in microcents) that Amazon DSP charges to customers for campaign management services provided by Amazon''s in-house service team. The managed service fee is calculated as a percentage of the supply cost. To convert from microcents to dollars/your currency, divide by 100,000,000 (e.g., 5,000,000 microcents = $0.05). Refer to the currency_name field for the currency in which the impression was purchased. Example value: ''5000000''.', 'LOW', 70
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'manager_account_frequency_group_ids', 'ARRAY', 'Dimension',
    'An array of the manager-account-level frequency group IDs that were applicable for this impression event. Frequency groups created at the manager account level may operate across 1 or more advertisers within that manager account. Note that a single impression may be subject to multiple frequency groups.', 'LOW', 71
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'matched_behavior_segment_ids', 'ARRAY', 'Metric',
    'Array of behavior segment IDs that were both targeted by the Amazon DSP line item and matched to the user at the time of impression. Each ID in the array corresponds to a distinct audience segment. Example value: ''[123456, 234567, 345678]''.', 'LOW', 72
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'merchant_id', 'LONG', 'Dimension',
    'Merchant ID.', 'LOW', 73
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'no_3p_trackers', 'STRING', 'Dimension',
    'Boolean value indicating whether the event can be used for audience creation that is third-party tracking enabled (i.e. whether you can serve creative with third-party tracking when running media against the audience). Third-party tracking refers to measurement tags and pixels from external vendors that can be used to measure ad performance. Possible values for this field are: ''true'', ''false''.', 'LOW', 74
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'ocm_fee', 'LONG', 'Metric',
    'The fee (in microcents) that Amazon DSP charges for the use of omnichannel measurement studies. The omnichannel metrics fee is calculated as a percentage of the supply cost. To convert to dollars, divide by 100,000,000 (e.g., 500,000 microcents = $0.005). Refer to the currency_name field for the currency in which the impression was purchased. Example value: 500000.', 'LOW', 75
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'operating_system', 'STRING', 'Dimension',
    'Operating system of the device where the Amazon DSP impression event occurred. Example values: ''iOS'', ''Android'', ''Windows'', ''macOS'', ''Roku OS''.', 'LOW', 76
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'os_version', 'STRING', 'Dimension',
    'Operating system version of the device where the Amazon DSP impression event occurred. The version format varies by operating system type. Example value: ''17.5.1''.', 'LOW', 77
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'page_type', 'STRING', 'Dimension',
    'Type of page where the Amazon DSP impression event occurred. This grain of detail is primarily relevant to impressions served on Amazon sites. Example values: ''Search'', ''Detail'', ''CustomerReviews''.', 'LOW', 78
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'placement_is_view_aware', 'BOOLEAN', 'Dimension',
    'Boolean value indicating whether or not the Amazon DSP impression occurred in a placement that supports viewability measurement. Possible values for this field are: ''true'', ''false''.', 'LOW', 79
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'placement_view_rate', 'DECIMAL', 'Dimension',
    'The view rate of the placement, expressed as a decimal between 0.0 and 1.0. Viewability is measured according to Media Rating Council (MRC) standards, which require 50% of pixels to be in view for at least 1 second for display ads and 2 seconds for video ads. Example value: 0.75', 'HIGH', 80
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'platform_fee', 'LONG', 'Metric',
    'The fee (in microcents) that Amazon DSP charges to customers to access and use Amazon DSP. The platform fee (also known as the technology fee or console fee in other contexts) is calculated as a percentage of the supply cost. To convert to dollars/your currency, divide by 100,000,000 (e.g., 100,000,000 microcents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: ''25000''.', 'LOW', 81
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'postal_code', 'STRING', 'Dimension',
    'Postal code in which the Amazon DSP impression event occurred, based on the user''s IP address. Postal code is also referred to as "zip code" in the US. The postal code is prepended with the iso_country_code value (e.g. ''US-12345''). If the country is known, but the postal code is unknown, only the country code will be populated in postal_code. Example value: ''US-12345''.', 'LOW', 82
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'product_line', 'STRING', 'Dimension',
    'Campaign product line.', 'MEDIUM', 83
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'publisher_id', 'STRING', 'Dimension',
    'ID of the publisher where the Amazon DSP impression was served. A publisher is the media owner (such as a website, app, or streaming service owner) that makes advertising inventory available for purchase through Amazon DSP.', 'LOW', 84
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'request_dt', 'TIMESTAMP', 'Dimension',
    'Timestamp of the request event in advertiser timezone. Example value: ''2025-01-01T00:00:00.000Z''.', 'LOW', 85
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'request_dt_hour', 'TIMESTAMP', 'Dimension',
    'Timestamp of the request event in advertiser timezone, truncated to hour. Example value: ''2025-01-01T12:00:00.000Z''.', 'MEDIUM', 86
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'request_dt_hour_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the request event in Coordinated Universal Time (UTC), truncated to hour. Example value: ''2025-01-01T12:00:00.000Z''.', 'VERY_HIGH', 87
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'request_dt_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the request event in Coordinated Universal Time (UTC). Example value: ''2025-01-01T00:00:00.000Z''.', 'LOW', 88
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'request_tag', 'STRING', 'Dimension',
    'ID that connects related impression, view, click, and conversion events. For example, if an impression served has a request_tag value of ''X'', related conversion events will have have an impression_id value of ''X''. While this occurs infrequently, there are sometimes duplicate request_tag values. As a result, it is not recommended to use request_tag as a JOIN key without first grouping by it. Rather, it is a best practice to first consider using UNION ALL in a query instead of joining based on the request_tag to combine data sources. For insights that involve user-level ad exposure across tables, use user_id instead.', 'VERY_HIGH', 89
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'segment_marketplace_id', 'INTEGER', 'Metric',
    'ID of the marketplace associated with an audience segment. A marketplace represents a specific region where advertising can be delivered.', 'LOW', 90
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'site', 'STRING', 'Dimension',
    'The site descriptor where the Amazon DSP impression event occurred. A site can be any digital property where ads are served, including websites, mobile apps, and streaming platforms.', 'LOW', 91
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'slot_position', 'STRING', 'Dimension',
    'Position of the ad on the page relative to the initial viewport. Above the fold (ATF) refers to the portion of the webpage visible without scrolling, while below the fold (BTF) refers to the portion that requires scrolling to view. This dimension helps measure where ad impressions were served on the page. Possible values include: ''ATF'', ''BTF'', and ''UNKNOWN''.', 'LOW', 92
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'supply_cost', 'LONG', 'Metric',
    'The cost (in microcents) that Amazon DSP pays a publisher or publisher ad tech platform (such as an SSP or exchange) for an impression. To convert supply_cost to dollars/your local currency, divide by 100,000,000 (e.g., 100,000,000 microcents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: ''5000''.', 'LOW', 93
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'supply_source', 'STRING', 'Dimension',
    'Supply source from which the Amazon DSP impression was purchased. Supply sources can include Amazon-owned properties (like Amazon.com and Twitch), Amazon Publisher Services inventory, and third-party partners. Example values: ''AMAZON.COM'', ''TWITCH WEB VIDEO'', ''PUBMATIC WEB DISPLAY''.', 'LOW', 94
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'supply_source_id', 'LONG', 'Dimension',
    'ID of the supply source from which the Amazon DSP impression was purchased. Supply sources can include Amazon-owned properties (like Amazon.com and Twitch), Amazon Publisher Services inventory, and third-party partners.', 'LOW', 95
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'supply_source_is_view_aware', 'BOOLEAN', 'Dimension',
    'Boolean value indicating whether or not the supply source can measure viewability. Possible values for this field are: ''true'', ''false''.', 'NONE', 96
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'supply_source_view_rate', 'DECIMAL', 'Dimension',
    'The view rate of the supply source, expressed as a decimal between 0.0 and 1.0. View rate represents the percentage of impressions that met viewability standards, which require at least 50% of the ad''s pixels to be visible for a minimum of one second for display ads or two seconds for video ads. Example value: ''0.75''.', 'NONE', 97
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'third_party_fees', 'LONG', 'Metric',
    'The sum of all third-party fees charged for the impression (in microcents). Third-party fees represent charges from external data and technology providers used in the delivery and measurement of the impression. Since this field is in microcents, divide by 100,000,000 to convert to dollars/your local currency (e.g., 500,000,000 microcents = $5.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: ''25000''.', 'LOW', 98
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'total_cost', 'LONG', 'Metric',
    'The total cost of the Amazon DSP impression in millicents, inclusive of all applicable fees (supply cost, audience fees, platform fees, and third-party fees). Since this field is in millicents, divide by 100,000 to convert to dollars/your local currency (e.g., 100,000 millicents = $1.00). Refer to the currency_name field for the currency in which the impression was purchased. Example value: ''300''.', 'VERY_HIGH', 99
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_behavior_segment_ids', 'ARRAY', 'Metric',
    'Array of behavior segment IDs that the user belonged to at the time of impression. Each ID in the array corresponds to a distinct audience segment. Example value: ''[123456, 234567, 345678]''.', 'MEDIUM', 100
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_id', 'STRING', 'Dimension',
    'Pseudonymous identifier that connects user activity across different events. The field can contain ad user IDs (representing Amazon accounts), device IDs, or browser IDs. NULL values appear when Amazon Ads is unable to resolve an identifier for an event. The field has a VERY_HIGH aggregation threshold, meaning it cannot be included in final SELECT statements but can be used within Common Table Expressions (CTEs) for aggregation purposes like COUNT(DISTINCT user_id).', 'VERY_HIGH', 101
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_id_type', 'STRING', 'Dimension',
    'Type of user ID value. AMC includes different types of user ID values, depending on whether the value represents a resolved Amazon account, a device, or a browser cookie. If Amazon Ads is unable to determine or provide an ID of any kind for an impression event, the ''user_id'' and ''user_id_type'' values for that record will be NULL. Possible values include: ''adUserId'', ''sisDeviceId'', ''adBrowserId'', and NULL.', 'LOW', 102
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Source:** `dsp_impressions`

Records of all impressions delivered to viewers. This table contains the most granular record of every impression delivered, allowing you to query all viewers reached through an Amazon DSP campaign.', 0
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions'
ON CONFLICT DO NOTHING;

-- Insert schema: dsp_impressions Segment Tables
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'dsp-impressions-segment-tables',
    'dsp_impressions Segment Tables',
    'DSP Tables',
    '⚠️ **Important Performance Warning**: Workflows that use these tables will time out when run over extended periods of time.',
    '["dsp_impressions_by_matched_segments", "dsp_impressions_by_user_segments"]',
    false,
    '["dsp", "display", "impressions", "programmatic"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'behavior_segment_description', 'STRING', 'Dimension',
    'Description of the audience segment, for segments both targeted by the Amazon DSP line item and matched to the user at the time of impression. This field contains explanations of the characteristics that define each segment, such as shopping behaviors, demographics, and interests.', 'LOW', 0
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions-segment-tables'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'behavior_segment_id', 'INTEGER', 'Dimension',
    'Unique identifier for the audience segment, for segments both targeted by the Amazon DSP line item and matched to the user at the time of impression. Example value: ''123456''.', 'LOW', 1
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions-segment-tables'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'behavior_segment_matched', 'LONG', 'Metric',
    'Indicator of whether the behavior segment was targeted by the Amazon DSP line item and matched to the user at the time of impression. **For dsp_impressions_by_matched_segments**: Always ''1'' (segment was targeted and matched). **For dsp_impressions_by_user_segments**: ''1'' if targeted, ''0'' if not targeted.', 'LOW', 2
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions-segment-tables'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'behavior_segment_name', 'STRING', 'Dimension',
    'Name of the audience segment, for segments both targeted by the Amazon DSP line item and matched to the user at the time of impression.', 'LOW', 3
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions-segment-tables'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Counting Impressions', '-- Correct way to count unique impressions
SELECT COUNT(DISTINCT request_tag) as unique_impressions
FROM dsp_impressions_by_matched_segments

-- Incorrect - will overcount due to segment multiplication
SELECT SUM(impressions) as total_impressions  
FROM dsp_impressions_by_matched_segments', 'Basic', 0
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions-segment-tables'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Filtering by Segment Targeting', '-- For dsp_impressions_by_user_segments only
-- Get only targeted segments
WHERE behavior_segment_matched = 1

-- Get non-targeted segments user belongs to
WHERE behavior_segment_matched = 0', 'Basic', 1
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions-segment-tables'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Sources:** 
- `dsp_impressions_by_matched_segments`
- `dsp_impressions_by_user_segments`

⚠️ **Important Performance Warning**: Workflows that use these tables will time out when run over extended periods of time.

These two tables have exactly the same basic structure as `dsp_impressions` table but in addition to that they provide segment level information for each of the segments that was either targeted by the ad or included the user that received the impression. This means that **each impression appears multiple times in these tables**.', 0
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions-segment-tables'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'differences', '### dsp_impressions_by_matched_segments
Shows only the segments that included the user **AND** were targeted by the ad at the time of the impression.', 1
FROM amc_data_sources 
WHERE schema_id = 'dsp-impressions-segment-tables'
ON CONFLICT DO NOTHING;

-- Insert schema: dsp_video_events_feed Data Source
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'dsp-video-events',
    'dsp_video_events_feed Data Source',
    'DSP Tables',
    '⚠️ **Important Performance Warning**: Workflows that use this table will time out when run over extended periods of time.',
    '[]',
    false,
    '["dsp", "impressions", "programmatic", "display", "clicks"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_click', 'LONG', 'Metric',
    'The number of Amazon DSP video clicks. Possible values for this field are: ''1'' (if the video was clicked) or ''0'' (if the video was not clicked). This field will always be ''0'' for non-video impressions.', 'NONE', 0
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_complete', 'LONG', 'Metric',
    'The number of Amazon DSP video impressions where the video was viewed to completion (100%). Possible values for this field are: ''1'' (if the video was viewed to completion) or ''0'' (if the video was not viewed to completion). This field will always be ''0'' for non-video impressions.', 'NONE', 1
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_creative_view', 'LONG', 'Metric',
    'The number of Amazon DSP video impressions where an additional ad element, such as the video companion ad or VPAID overlay, was viewed. Possible values for this field are: ''1'' (if the additional ad element was viewed) or ''0'' (if the additional ad element was not viewed). This field will always be ''0'' for non-video impressions.', 'NONE', 2
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_first_quartile', 'LONG', 'Metric',
    'The number of Amazon DSP video impressions where the video was viewed to the first quartile (at least 25% completion). Possible values for this field are: ''1'' (if the video was viewed to at least 25% completion) or ''0'' (if the video was not viewed to 25% completion). This field will always be ''0'' for non-video impressions.', 'NONE', 3
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_impression', 'LONG', 'Metric',
    'The number of Amazon DSP video impressions where the first frame of the ad was shown. Possible values for this field are: ''1'' (if the first frame of the video was shown) or ''0'' (if the first frame of the video was not shown). This field will always be ''0'' for non-video impressions.', 'NONE', 4
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_midpoint', 'LONG', 'Metric',
    'The number of Amazon DSP video impressions where the video was viewed to the midpoint (at least 50% completion). Possible values for this field are: ''1'' (if the video was viewed to at least 50% completion) or ''0'' (if the video was not viewed to 50% completion). This field will always be ''0'' for non-video impressions.', 'NONE', 5
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_mute', 'LONG', 'Metric',
    'The number of Amazon DSP video mutes. Possible values for this field are: ''1'' (if the user muted the video) or ''0'' (if the user did not mute the video). This field will always be ''0'' for non-video impressions.', 'NONE', 6
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_pause', 'LONG', 'Metric',
    'The number of Amazon DSP video pauses. Possible values for this field are: ''1'' (if the user paused the video) or ''0'' (if the user did not pause the video). This field will always be ''0'' for non-video impressions.', 'NONE', 7
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_replay', 'LONG', 'Metric',
    'The number of Amazon DSP video impressions where the ad was replayed again after it completed. Possible values for this field are: ''1'' (if the user replayed the video after completion) or ''0'' (if the video was not replayed after completion). This field will always be ''0'' for non-video impressions.', 'NONE', 8
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_resume', 'LONG', 'Metric',
    'The number of Amazon DSP video impressions where the video was resumed after a pause. Possible values for this field are: ''1'' (if the video was resumed after a pause) or ''0'' (if the video was not resumed after a pause). This field will always be ''0'' for non-video impressions.', 'NONE', 9
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_skip_backward', 'LONG', 'Metric',
    'The number of Amazon DSP video impressions that had backward skips. Possible values for this field are: ''1'' (if the user skipped the video backward) or ''0'' (if the user did not skip the video backward). This field will always be ''0'' for non-video impressions.', 'NONE', 10
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_skip_forward', 'LONG', 'Metric',
    'The number of Amazon DSP video impressions that had forward skips. Possible values for this field are: ''1'' (if the user skipped the video forward) or ''0'' (if the user did not skip the video forward). This field will always be ''0'' for non-video impressions.', 'NONE', 11
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_start', 'LONG', 'Metric',
    'The number of Amazon DSP video impression starts. Possible values for this field are: ''1'' (if the user started the video) or ''0'' (if the user did not start the video). This field will always be ''0'' for non-video impressions.', 'NONE', 12
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_third_quartile', 'LONG', 'Metric',
    'The number of Amazon DSP video impressions where the video was viewed to the third quartile (at least 75% completion). Possible values for this field are: ''1'' (if the video was viewed to at least 75% completion) or ''0'' (if the video was not viewed to 75% completion). This field will always be ''0'' for non-video impressions.', 'NONE', 13
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_unmute', 'LONG', 'Metric',
    'The number of Amazon DSP video unmutes. Possible values for this field are: ''1'' (if the video was unmuted) or ''0'' (if the video was not unmuted). This field will always be ''0'' for non-video impressions.', 'NONE', 14
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Filtering Video Content', '-- Get only video impressions
SELECT * FROM dsp_video_events_feed 
WHERE creative_category = ''Video''

-- Get impressions where video was started
SELECT * FROM dsp_video_events_feed 
WHERE video_start = 1

-- Get completed video views
SELECT * FROM dsp_video_events_feed 
WHERE video_complete = 1', 'Basic', 0
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Calculating Engagement Rates', '-- Video completion rate
SELECT 
    campaign,
    SUM(video_start) as video_starts,
    SUM(video_complete) as video_completions,
    CASE 
        WHEN SUM(video_start) > 0 
        THEN SUM(video_complete) * 100.0 / SUM(video_start) 
        ELSE 0 
    END as completion_rate_percent
FROM dsp_video_events_feed
WHERE creative_category = ''Video''
GROUP BY campaign;

-- Quartile drop-off analysis
SELECT 
    campaign,
    SUM(video_start) as starts,
    SUM(video_first_quartile) as q1,
    SUM(video_midpoint) as q2,
    SUM(video_third_quartile) as q3,
    SUM(video_complete) as completions
FROM dsp_video_events_feed
WHERE creative_category = ''Video''
GROUP BY campaign;', 'Basic', 1
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Source:** `dsp_video_events_feed`

⚠️ **Important Performance Warning**: Workflows that use this table will time out when run over extended periods of time.

This table has the exact same basic structure as `dsp_impressions` table but in addition to that, the table provides video metrics for each of the video creative events triggered by the video player and associated with the impression event.', 0
FROM amc_data_sources 
WHERE schema_id = 'dsp-video-events'
ON CONFLICT DO NOTHING;

-- Insert schema: dsp_views Data Source
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'dsp-views',
    'dsp_views Data Source',
    'DSP Tables',
    'Represents all view events and all measurable events. Measurable events are from impression that were able to be measured. Viewable events represent events that met a viewable standard. The metric viewable_impressions is the count of viewable impressions using the IAB standard (50% of the impression''s pixels were on screen for at least 1 second).',
    '[]',
    false,
    '["dsp", "impressions", "programmatic", "display", "clicks"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'ad_slot_size', 'STRING', 'Dimension',
    'Ad slot size in which the Amazon DSP ad was served, expressed as width x height in pixels. The dimensions indicate the space allocated for the ad on the page or app where the impression was served. Example values: ''300x250'', ''728x90'', ''320x50''.', 'LOW', 0
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser', 'STRING', 'Dimension',
    'Name of the business entity running advertising campaigns on Amazon DSP. Example value: ''Widgets Inc''.', 'LOW', 1
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_account_frequency_group_ids', 'ARRAY', 'Dimension',
    'An array of the advertiser-account-level frequency group IDs that were applicable for this impression event. Frequency groups created at the advertiser account level may operate across 1 or more campaigns within that advertiser account. Note that a single impression may be subject to multiple frequency groups.', 'LOW', 2
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_country', 'STRING', 'Dimension',
    'Country of the Amazon DSP advertiser. This value is based on the country setting configured in the advertiser''s Amazon DSP account. Example value: ''US''.', 'LOW', 3
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_id', 'LONG', 'Dimension',
    'ID of the Amazon DSP advertiser associated with the view event. Example value: ''123456789012345''.', 'LOW', 4
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser_timezone', 'STRING', 'Dimension',
    'Advertiser timezone. This setting aligns with the advertiser timezone configuration in the connected Amazon DSP account. Example value: ''America/New_York''.', 'LOW', 5
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'app_bundle', 'STRING', 'Dimension',
    'The app bundle ID associated with the Amazon DSP view event. App bundles follow different formatting conventions depending on the app store.', 'LOW', 6
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign', 'STRING', 'Dimension',
    'Name of the Amazon DSP campaign responsible for the view event. A campaign is a container that groups related advertising efforts with shared objectives, budget, and flight dates. Example value: ''Widgets_Q1_2024_Awareness_Display_US''.', 'LOW', 7
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_end_date', 'TIMESTAMP', 'Dimension',
    'End date and time of the Amazon DSP campaign in advertiser timezone. Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 8
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_end_date_utc', 'TIMESTAMP', 'Dimension',
    'End date of the Amazon DSP campaign in Coordinated Universal Time (UTC). Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 9
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_flight_id', 'LONG', 'Dimension',
    'ID of the Amazon DSP campaign flight. A campaign flight represents a scheduled run period for an advertising campaign with defined start and end dates. Example value: ''123456789012345''.', 'LOW', 10
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_id', 'LONG', 'Dimension',
    'The ID of the Amazon DSP campaign responsible for the view event. In this table, campaign_id and campaign_id_string fields will show the same value for a given event. Example value: ''571234567890123456''.', 'LOW', 11
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_id_string', 'STRING', 'Dimension',
    'The ID of the Amazon DSP campaign responsible for the view event. In this table, campaign_id and campaign_id_string fields will show the same value for a given event. Example value: ''571234567890123456''.', 'LOW', 12
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_insertion_order_id', 'STRING', 'Dimension',
    'ID of the insertion order associated with the Amazon DSP view event. An insertion order is a contractual agreement between an advertiser and Amazon Ads that outlines the specific details of a programmatic advertising campaign. Example value: ''123456789''.', 'LOW', 13
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_primary_goal', 'STRING', 'Dimension',
    'Primary goal set for campaign optimization in Amazon DSP. Campaign goals determine how Amazon DSP optimizes delivery and measures success of the campaign. The goal selected during campaign setup influences bidding strategy and campaign optimization. Possible values include: ''ROAS'', ''TOTAL_ROAS'', ''REACH'', ''CPVC'', ''COMPLETION_RATE'', ''CTR'', ''CPC'', ''DPVR'', ''PAGE_VISIT'', ''CPDPV'', ''CPA'' ''OTHER'', and ''NONE''.', 'LOW', 14
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_sales_type', 'STRING', 'Dimension',
    'Billing classification of the Amazon DSP campaign, which distinguishes billable and non-billable campaigns. Possible values include: ''BILLABLE'' and ''BONUS''.', 'LOW', 15
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_source', 'STRING', 'Dimension',
    'Campaign source.', 'LOW', 16
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_start_dt', 'TIMESTAMP', 'Dimension',
    'Start date and time of the Amazon DSP campaign in advertiser timezone. The campaign start date determines when a campaign begins serving impressions. Example value: ''2025-01-01T00:00:00.000Z''.', 'LOW', 17
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_start_date_utc', 'TIMESTAMP', 'Dimension',
    'Start date and time of the Amazon DSP campaign in Coordinated Universal Time (UTC). The campaign start date determines when a campaign begins serving impressions. Example value: ''2025-01-01T00:00:00.000Z''.', 'LOW', 18
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_status', 'STRING', 'Dimension',
    'Current status of the Amazon DSP campaign. Campaign status indicates whether a campaign is actively delivering ads, has completed its flight dates, or has been paused by the advertiser. Possible values include: ''ENDED'', ''RUNNING'', ''ENABLED'', ''PAUSED'', and ''ADS_NOT_RUNNING''.', 'LOW', 19
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'city_name', 'STRING', 'Dimension',
    'City name where the Amazon DSP view event occurred, determined by signal available in the auction event. Example value: ''New York''.', 'HIGH', 20
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative', 'STRING', 'Dimension',
    'Name of the Amazon DSP creative/ad. A creative represents the actual advertisement shown to customers. Example value: ''2025_US_Widgets_Spring_Mobile_320x50''.', 'LOW', 21
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_category', 'STRING', 'Dimension',
    'Category of the Amazon DSP creative/ad. This field categorizes Amazon DSP ads into broad creative format types like display ads and video ads. Possible values include: ''Display'', ''Video'', and NULL.', 'LOW', 22
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_duration', 'INTEGER', 'Dimension',
    'Duration in seconds of the Amazon DSP creative asset, primarily used for video format ads. This field specifies the length of video creative assets delivered through Amazon DSP campaigns. For non-video creative formats like display ads, this field will be NULL. Example values include: ''15'', ''30'', ''60'', representing video durations in seconds.', 'LOW', 23
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_id', 'LONG', 'Dimension',
    'Unique identifier for the Amazon DSP creative/ad. A ad represents the actual advertisement shown to customers, which could be an image, video, or other ad format. Example value: ''591234567890123456''.', 'LOW', 24
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_is_link_in', 'STRING', 'Dimension',
    'Boolean field indicating whether the Amazon DSP creative/ad directs to an Amazon destination (link in) versus an external destination (link out). A link in creative directs users to an Amazon destination like a product detail page, while a link out creative directs users to an external destination like an advertiser''s website. Possible values for this field are: ''Y'' (creative is link in), ''N'' (creative is link out).', 'LOW', 25
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_size', 'STRING', 'Dimension',
    'Dimensions of the Amazon DSP creative/ad (width x height in pixels, or responsive format). Example values: ''300x250'', ''320x50'', ''Responsive''.', 'LOW', 26
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_type', 'STRING', 'Dimension',
    'Type of creative/ad.', 'LOW', 27
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'demand_channel_owner', 'STRING', 'Dimension',
    'Demand channel owner.', 'LOW', 28
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'device_make', 'STRING', 'Dimension',
    'Manufacturer or brand name of the device associated with the Amazon DSP view event, derived from user-agent in the impression auction. Values may appear in different formats or capitalizations for the same manufacturer. Example values: ''Apple'', ''APPLE'', ''Samsung'', ''SAMSUNG'', ''ROKU'', ''Generic'', ''UNKNOWN''.', 'LOW', 29
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'device_model', 'STRING', 'Dimension',
    'Model of the device associated with the Amazon DSP view event, derived from user-agent in the impression auction. Values may appear in different formats or capitalizations for the same manufacturer. Example values: ''iPhone'', ''GALAXY''.', 'LOW', 30
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'entity_id', 'STRING', 'Dimension',
    'ID of the Amazon DSP entity (also known as seat) associated with the view event. An entity represents an Amazon DSP account, within which media is further organized by advertiser and by campaign. Example value: ''ENTITYABC123XYZ789''.', 'LOW', 31
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'environment_type', 'STRING', 'Dimension',
    'Environment where the Amazon DSP view event occurred. This field distinguishes between web-based environments like desktop or mobile browsers, and app-based environments like mobile apps. If the environment type cannot be determined, this field will be NULL. Possible values include: ''Web'', ''App'', and NULL.', 'LOW', 32
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_date', 'DATE', 'Dimension',
    'Date of the Amazon DSP view event in advertiser timezone. This field will be populated for conversion events that are attributed to an ad view. Example value: ''2025-01-01''.', 'LOW', 33
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_date_utc', 'DATE', 'Dimension',
    'Date of the Amazon DSP view event in Coordinated Universal Time (UTC). This field will be populated for conversion events that are attributed to an ad view. Example value: ''2025-01-01''', 'LOW', 34
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP view event in advertiser timezone. This field will be populated for conversion events that are attributed to an ad view. Example value: ''2025-01-01T12:00:00.000Z''.', 'MEDIUM', 35
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt_hour', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP view event in advertiser timezone, truncated to hour. This field will be populated for conversion events that are attributed to an ad view. Example value: ''2025-01-01T12:00:00.000Z''.', 'LOW', 36
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt_hour_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP view event in Coordinated Universal Time (UTC), truncated to hour. This field will be populated for conversion events that are attributed to an ad view. Example value: ''2025-01-01T12:00:00.000Z''.', 'LOW', 37
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the Amazon DSP view event in Coordinated Universal Time (UTC). This field will be populated for conversion events that are attributed to an ad view. Example value: ''2025-01-01T00:00:00.000Z''.', 'MEDIUM', 38
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_type', 'STRING', 'Dimension',
    'Type of view event. There are four types of view events in AMC. Measurable impression events indicate that the Amazon Ads impression was able to be measured for viewability; these events can be summed using the measurable_impressions metric. Viewable impression events indicate Amazon Ads determined the impression met MRC viewability standards; these events can be summed using the viewable_impressions metric. Unmeasurable viewable and synthetic viewable impression events are estimated to be viewable; these events can be summed using the unmeasurable_viewable_impressions metric. Possible values include: ''MEASURABLE_IMP'' (measurable impression), ''VIEW'' (viewable impression), ''UNMEASURABLE_IMP'' (unmeasurable viewable impression), and ''SYNTHETIC_VIEW'' (synthetic view impression).', 'LOW', 39
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'events', 'LONG', 'Metric',
    'Count of Amazon DSP view events. When querying this table, remember that each record represents one Amazon DSP view event, and a single impression may have more than one view event. Therefore, this field will not represent the exact count of impressions served by your campaigns. Since this table only includes views events, this field will always have a value of ''1'' (the event was a view event).', 'NONE', 40
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impression_id', 'STRING', 'Dimension',
    'ID that connects related impression, view, click, and conversion events. For example, if an impression served has a request_tag value of ''X'', related view events will have have an impression_id value of ''X''. All view events for a single impression will share a common impression_id value. While this occurs infrequently, there are sometimes duplicate request_tag values. As a result, it is not recommended to use request_tag as a JOIN key without first grouping by it. Rather, it is a best practice to first consider using UNION ALL in a query instead of joining based on the request_tag to combine data sources. For insights that involve user-level ad exposure across tables, use user_id instead.', 'VERY_HIGH', 41
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item', 'STRING', 'Dimension',
    'Name of the Amazon DSP line item responsible for the view event. Attributes like ad format and targeting are defined at line item level within a campaign. Example value: ''Widgets - DISPLAY - O&O - RETARGETING''.', 'LOW', 42
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_end_dt', 'TIMESTAMP', 'Dimension',
    'End date and time of the Amazon DSP line item in advertiser timezone. Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 43
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_end_dt_utc', 'TIMESTAMP', 'Dimension',
    'End date and time of the line item in Coordinated Universal Time (UTC). Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 44
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_id', 'LONG', 'Dimension',
    'ID of the Amazon DSP line item responsible for the view event. Attributes like ad format and targeting are defined at line item level within a campaign. Example value: ''5812345678901234''.', 'LOW', 45
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_price_type', 'STRING', 'Dimension',
    'Pricing model used for the Amazon DSP line item. Line items can use different pricing models to determine how costs are calculated, with Cost Per Mille (CPM) being a common model where advertisers pay per thousand impressions. Example value: ''CPM''.', 'LOW', 46
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_start_dt', 'TIMESTAMP', 'Dimension',
    'Start date and time of the Amazon DSP line item in advertiser timezone. Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 47
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_start_dt_utc', 'TIMESTAMP', 'Dimension',
    'Start date and time of the Amazon DSP line item in Coordinated Universal Time (UTC). Example value: ''2025-01-01T23:59:59.000Z''.', 'LOW', 48
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_status', 'STRING', 'Dimension',
    'Status of the Amazon DSP line item. The status indicates whether the line item is actively delivering ads, has been paused, or has completed its flight. Possible values include: ''ENDED'', ''ENABLED'', ''RUNNING'', ''PAUSED_BY_USER'', and ''SUSPENDED''.', 'LOW', 49
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item_type', 'STRING', 'Dimension',
    'Type of Amazon DSP line item. Line item types indicate how ads are delivered and optimized. Example values include: ''AAP'', ''AAP_DISPLAY'', ''AAP_MOBILE'', ''AAP_VIDEO_CPM''.', 'LOW', 50
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'manager_account_frequency_group_ids', 'ARRAY', 'Dimension',
    'An array of the manager-account-level frequency group IDs that were applicable for this impression event. Frequency groups created at the manager account level may operate across 1 or more advertisers within that manager account. Note that a single impression may be subject to multiple frequency groups.', 'LOW', 51
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'measurable_impressions', 'LONG', 'Metric',
    'Count of impressions that could be measured for viewability. Measurable impression events indicate that the Amazon Ads impression was able to be measured for viewability. A single impression that is measurable could also be viewable, but not all measurable impressions are viewable. If an impression is both measurable and viewable, each event for the single impression is listed as a separate row. Possible values for this field are: ''1'' (if the record represents a measurable impression) or ''0'' (if the record does not represent a measurable impression).', 'NONE', 52
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'merchant_id', 'LONG', 'Dimension',
    'Merchant ID.', 'LOW', 53
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'no_3p_trackers', 'STRING', 'Dimension',
    'Boolean value indicating whether the event can be used for audience creation that is third-party tracking enabled (i.e. whether you can serve creative with third-party tracking when running media against the audience). Third-party tracking refers to measurement tags and pixels from external vendors that can be used to measure ad performance. Possible values for this field are: ''true'', ''false''.', 'NONE', 54
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'operating_system', 'STRING', 'Dimension',
    'Operating system of the device where the Amazon DSP view event occurred. Example values: ''iOS'', ''Android'', ''Windows'', ''macOS'', ''Roku OS''.', 'LOW', 55
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'os_version', 'STRING', 'Dimension',
    'Operating system version of the device where the Amazon DSP view event occurred. The version format varies by operating system type. Example value: ''17.5.1''.', 'LOW', 56
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'page_type', 'STRING', 'Dimension',
    'Type of page where the Amazon DSP view event occurred. This grain of detail is primarily relevant to impressions served on Amazon sites. Example values: ''Search'', ''Detail'', ''CustomerReviews''.', 'LOW', 57
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'publisher_id', 'LONG', 'Dimension',
    'ID of the publisher where the Amazon DSP view event occurred. A publisher is the media owner (such as a website, app, or streaming service owner) that makes advertising inventory available for purchase through Amazon DSP.', 'LOW', 58
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'site', 'STRING', 'Dimension',
    'The site descriptor where the Amazon DSP view event occurred. A site can be any digital property where ads are served, including websites, mobile apps, and streaming platforms.', 'LOW', 59
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'slot_position', 'STRING', 'Dimension',
    'Position of the ad on the page relative to the initial viewport. Above the fold (ATF) refers to the portion of the webpage visible without scrolling, while below the fold (BTF) refers to the portion that requires scrolling to view. This dimension helps measure where ad impressions were served on the page. Possible values include: ''ATF'', ''BTF'', and ''UNKNOWN''.', 'LOW', 60
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'supply_source_id', 'LONG', 'Dimension',
    'ID of the supply source from which the Amazon DSP impression was purchased. Supply sources can include Amazon-owned properties (like Amazon.com and Twitch), Amazon Publisher Services inventory, and third-party partners.', 'LOW', 61
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'unmeasurable_viewable_impressions', 'LONG', 'Metric',
    'Count of unmeasurable viewable/synthetic view events. Unmeasurable viewable and synthetic viewable events are estimated to be viewable, but could not be measured for viewability. Possible values for this field are: ''1'' (if the record represents a unmeasurable viewable/synthetic view event) or ''0'' (if the record does not represent a unmeasurable viewable/synthetic view event).', 'NONE', 62
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_id', 'STRING', 'Dimension',
    'Pseudonymous identifier that connects user activity across different events. The field can contain ad user IDs (representing Amazon accounts), device IDs, or browser IDs. NULL values appear when Amazon Ads is unable to resolve an identifier for an event. The field has a VERY_HIGH aggregation threshold, meaning it cannot be included in final SELECT statements but can be used within Common Table Expressions (CTEs) for aggregation purposes like COUNT(DISTINCT user_id).', 'VERY_HIGH', 63
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_id_type', 'STRING', 'Dimension',
    'Type of user ID value. AMC includes different types of user ID values, depending on whether the value represents a resolved Amazon account, a device, or a browser cookie. If Amazon Ads is unable to determine or provide an ID of any kind for a view event, the ''user_id'' and ''user_id_type'' values for that record will be NULL. Possible values include: ''adUserId'', ''sisDeviceId'', ''adBrowserId'', and NULL.', 'LOW', 64
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'view_definition', 'STRING', 'Dimension',
    'Type of viewability measurement definition used to classify the view event. This field will only be populated for viewable impressions (event_type = ''VIEW'').', 'LOW', 65
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'viewable_impressions', 'LONG', 'Metric',
    'The count of impressions that were considered viewable. An impression is considered viewable when at least 50% of the ad''s pixels are in view for at least one continuous second for display ads, or two continuous seconds for video ads. This is the Media Rating Council''s (MRC) definition of viewability. Note that a single impression that is viewable has two events: a viewable impression and a measurable impression. Each event for the single impression is listed as a separate row. Possible values for this field are: ''1'' (if the record represents a viewable impression) or ''0'' (if the record does not represent a viewable impression).', 'NONE', 66
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Source:** `dsp_views`

Represents all view events and all measurable events. Measurable events are from impression that were able to be measured. Viewable events represent events that met a viewable standard. The metric viewable_impressions is the count of viewable impressions using the IAB standard (50% of the impression''s pixels were on screen for at least 1 second). 

**Important Note:** The dsp_views table records a single impression more than one time if it is both measurable and viewable according to IAB''s standards. An impression that is both measurable and viewable according to IAB''s standards is recorded in one row as a measurable event and in another row as a viewable event. Note that while all impression events from dsp_views are recorded in dsp_impressions, not all impression events from dsp_impressions are recorded in dsp_views because not all impression events can be categorized as viewable, measurable or unmeasurable.', 0
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'concepts', '### Event Types
The `event_type` field is crucial for understanding this table:
- **MEASURABLE_IMP**: Measurable impression - could be measured for viewability
- **VIEW**: Viewable impression - met MRC viewability standards  
- **UNMEASURABLE_IMP**: Unmeasurable viewable impression - estimated to be viewable
- **SYNTHETIC_VIEW**: Synthetic view impression - estimated to be viewable', 3
FROM amc_data_sources 
WHERE schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

-- Insert schema: Amazon Prime Video Channel Insights
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'pvc-insights',
    'Amazon Prime Video Channel Insights',
    'Premium Video Content',
    '⚠️ **Important Availability Notice**: Amazon Prime Video Channel Insights is a standalone AMC Paid Features resource available for trial and subscription enrollments within the AMC Paid Features suite of insight expansion options, powered by Amazon Advertising.',
    '["amazon_pvc_enrollments", "amazon_pvc_streaming_events_feed"]',
    true,
    '["impressions"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Core Identifiers', 'MARKETPLACE_ID', 'Dimension',
    'Dimension', 'ID OF THE MARKETPLACE WHERE THE AMAZON PRIME VIDEO CHANNEL ENROLLMENT EVENT OCCURRED.', 0
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Core Identifiers', 'MARKETPLACE_NAME', 'Dimension',
    'Dimension', 'THE MARKETPLACE ASSOCIATED WITH THE AMAZON PRIME VIDEO CHANNEL RECORD', 1
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Core Identifiers', 'PV_BENEFIT_ID', 'Dimension',
    'Dimension', 'AMAZON PRIME VIDEO SUBSCRIPTION BENEFIT IDENTIFIER', 2
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Core Identifiers', 'PV_SUBSCRIPTION_ID', 'Dimension',
    'Dimension', 'AMAZON PRIME VIDEO SUBSCRIPTION ID', 3
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Core Identifiers', 'PV_SUB_EVENT_PRIMARY_KEY', 'Dimension',
    'Dimension', 'UNIQUE IDENTIFIER FOR THE PVC ENROLLMENT EVENT', 4
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Subscription Details', 'PV_BENEFIT_NAME', 'Dimension',
    'Dimension', 'AMAZON PRIME VIDEO SUBSCRIPTION BENEFIT NAME', 5
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Subscription Details', 'PV_BILLING_TYPE', 'Dimension',
    'Dimension', 'AMAZON PRIME VIDEO BILLING TYPE FOR THE ENROLLMENT RECORD', 6
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Subscription Details', 'PV_SUBSCRIPTION_NAME', 'Dimension',
    'Dimension', 'AMAZON PRIME VIDEO SUBSCRIPTION NAME', 7
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Subscription Details', 'PV_SUBSCRIPTION_PRODUCT_ID', 'Dimension',
    'Dimension', 'AMAZON PRIME VIDEO SUBSCRIPTION PRODUCT IDENTIFIER', 8
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Subscription Details', 'PV_OFFER_NAME', 'Dimension',
    'Dimension', 'AMAZON PRIME VIDEO SUBSCRIPTION OFFER NAME', 9
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Subscription Details', 'PV_UNIT_PRICE', 'Dimension',
    'Dimension', 'UNIT PRICE FOR THE PVC ENROLLMENT RECORD', 10
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Temporal Data', 'PV_START_DATE', 'Dimension',
    'Dimension', 'INTERVAL-SPECIFIC START DATE ASSOCIATED WITH THE PVC ENROLLMENT RECORD', 11
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Temporal Data', 'PV_END_DATE', 'Dimension',
    'Dimension', 'INTERVAL-SPECIFIC END DATE ASSOCIATED WITH THE PVC ENROLLMENT RECORD', 12
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Status Indicators', 'PV_ENROLLMENT_STATUS', 'Dimension',
    'Dimension', 'STATUS FOR THE PVC ENROLLMENT RECORD', 13
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Status Indicators', 'PV_IS_LATEST_RECORD', 'Dimension',
    'Dimension', 'INDICATOR OF WHETHER THE PVC ENROLLMENT RECORD IS THE MOST RECENT RECORD WITHIN THE TABLE', 14
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Status Indicators', 'PV_IS_PLAN_CONVERSION', 'Dimension',
    'Dimension', 'INDICATES WHETHER THE PVC ENROLLMENT RECORD HAS CONVERTED FROM FREE TRIAL TO A SUBSCRIPTION. THIS IS OFTEN ASSOCIATED WITH A CHANGE IN THE BILLING TYPE FOR THE PVC SUBSCRIPTION', 15
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Status Indicators', 'PV_IS_PLAN_START', 'Dimension',
    'Dimension', 'INDICATES WHETHER THE PVC ENROLLMENT RECORD IS THE START OF A ENROLLMENT. THIS IS OFTEN THE OPENING OF A FREE TRIAL OR THE FIRST SUBSCRIPTION RECORD FOR THE PV SUBSCRIPTION ID', 16
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Status Indicators', 'PV_IS_PROMO', 'Dimension',
    'Dimension', 'INDICATOR OF WHETHER THE PVC ENROLLMENT RECORD IS ASSOCIATED WITH A PROMOTIONAL OFFER', 17
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'User Data', 'USER_ID', 'Dimension',
    'Dimension', 'PSEUDONYMOUS IDENTIFIER THAT CONNECTS USER ACTIVITY ACROSS DIFFERENT EVENTS. THE FIELD CAN CONTAIN AD USER IDS (REPRESENTING AMAZON ACCOUNTS), DEVICE IDS, OR BROWSER IDS. NULL VALUES APPEAR WHEN AMAZON ADS IS UNABLE TO RESOLVE AN IDENTIFIER FOR AN EVENT. THE FIELD HAS A VERYHIGH AGGREGATION THRESHOLD, MEANING IT CANNOT BE INCLUDED IN FINAL SELECT STATEMENTS BUT CAN BE USED WITHIN COMMON TABLE EXPRESSIONS (CTES) FOR AGGREGATION PURPOSES LIKE COUNT(DISTINCT USERID).', 18
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'User Data', 'USER_ID_TYPE', 'Dimension',
    'Dimension', 'TYPE OF USER ID VALUE. AMC INCLUDES DIFFERENT TYPES OF USER ID VALUES, DEPENDING ON WHETHER THE VALUE REPRESENTS A RESOLVED AMAZON ACCOUNT, A DEVICE, OR A BROWSER COOKIE. IF AMAZON ADS IS UNABLE TO DETERMINE OR PROVIDE AN ID OF ANY KIND FOR AN IMPRESSION EVENT, THE USER_ID AND USER_ID_TYPE VALUES FOR THAT RECORD WILL BE NULL. POSSIBLE VALUES INCLUDE: ''ADUSERID'', ''SISDEVICEID'', ''ADBROWSERID'', AND NULL.', 19
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Privacy Controls', 'NO_3P_TRACKERS', 'Dimension',
    'Dimension', 'BOOLEAN VALUE INDICATING WHETHER THE EVENT CAN BE USED FOR AUDIENCE CREATION THAT IS THIRD-PARTY TRACKING ENABLED (I.E. WHETHER YOU CAN SERVE CREATIVE WITH THIRD-PARTY TRACKING WHEN RUNNING MEDIA AGAINST THE AUDIENCE). THIRD-PARTY TRACKING REFERS TO MEASUREMENT TAGS AND PIXELS FROM EXTERNAL VENDORS THAT CAN BE USED TO MEASURE AD PERFORMANCE. POSSIBLE VALUES FOR THIS FIELD ARE: ''TRUE'', ''FALSE''.', 20
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Core Identifiers', 'MARKETPLACE_ID', 'Dimension',
    'Dimension', 'MARKETPLACE ID OF THE EVENT', 21
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Core Identifiers', 'MARKETPLACE_NAME', 'Dimension',
    'Dimension', 'MARKETPLACE NAME OF THE EVENT', 22
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Core Identifiers', 'PV_SESSION_ID', 'Dimension',
    'Dimension', 'UNIQUE IDENTIFIER FOR STREAMING SESSION', 23
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Core Identifiers', 'PV_STREAMING_ASIN', 'Dimension',
    'Dimension', 'AMAZON STANDARD IDENTIFICATION NUMBER (ASIN)', 24
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Core Identifiers', 'PV_STREAMING_GTI', 'Dimension',
    'Dimension', 'GLOBAL TITLE INFORMATION', 25
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Temporal Data', 'PV_PLAYBACK_DATE_UTC', 'Dimension',
    'Dimension', 'DATE OF THE EVENT IN UTC', 26
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Temporal Data', 'PV_PLAYBACK_DT_UTC', 'Dimension',
    'Dimension', 'TIMESTAMP OF THE EVENT IN UTC', 27
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Engagement Metrics', 'PV_SECONDS_VIEWED', 'Dimension',
    'Metric', 'SECONDS OF VIEW TIME ASSOCIATED WITH STREAMING EVENT', 28
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Metadata', 'PV_GTI_SERIES_OR_MOVIE_NAME', 'Dimension',
    'Dimension', 'SERIES OR MOVIE NAME', 29
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Metadata', 'PV_GTI_TITLE_NAME', 'Dimension',
    'Dimension', 'CONTENT TITLE (E.G., EPISODE NAME)', 30
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Metadata', 'PV_GTI_CONTENT_TYPE', 'Dimension',
    'Dimension', 'CONTENT TYPE (E.G., TV EPISODE, MOVIE, PROMOTION)', 31
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Metadata', 'PV_GTI_CONTENT_ENTITY_TYPE', 'Dimension',
    'Dimension', 'CONTENT ENTITY TYPE (E.G., SHORT FILM, EDUCATIONAL)', 32
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Metadata', 'PV_GTI_CONTENT_RATING', 'Dimension',
    'Dimension', 'CONTENT RATING', 33
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Metadata', 'PV_GTI_GENRE', 'Dimension',
    'Dimension', 'CONTENT GENRE', 34
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Metadata', 'PV_GTI_STUDIO', 'Dimension',
    'Dimension', 'CONTENT STUDIO', 35
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Metadata', 'PV_GTI_RELEASE_DATE', 'Dimension',
    'Dimension', 'CONTENT RELEASE DATE', 36
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Series Information', 'PV_GTI_SEASON', 'Dimension',
    'Dimension', 'SERIES SEASON', 37
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Series Information', 'PV_GTI_EPISODE', 'Dimension',
    'Dimension', 'SERIES EPISODE', 38
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Personnel', 'PV_GTI_CAST', 'Dimension',
    'Dimension', 'CONTENT CAST MEMBERS', 39
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Personnel', 'PV_GTI_DIRECTOR', 'Dimension',
    'Dimension', 'CONTENT DIRECTORS', 40
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Event Context', 'PV_GTI_EVENT_NAME', 'Dimension',
    'Dimension', 'CONTENT EVENT NAME', 41
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Event Context', 'PV_GTI_EVENT_CONTEXT', 'Dimension',
    'Dimension', 'CONTENT EVENT CONTEXT', 42
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Event Context', 'PV_GTI_EVENT_ITEM', 'Dimension',
    'Dimension', 'CONTENT EVENT ITEM', 43
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Event Context', 'PV_GTI_EVENT_LEAGUE', 'Dimension',
    'Dimension', 'CONTENT EVENT LEAGUE', 44
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Event Context', 'PV_GTI_EVENT_SPORT', 'Dimension',
    'Dimension', 'CONTENT EVENT SPORT', 45
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Stream Properties', 'PV_STREAM_TYPE', 'Dimension',
    'Dimension', 'TYPE OF STREAM CONTENT (E.G., LINEAR TV, LIVE-EVENT, VOD)', 46
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Stream Properties', 'PV_MATERIAL_TYPE', 'Dimension',
    'Dimension', 'VIDEO MATERIAL TYPE (E.G., FULL, LIVE, PROMO, TRAILER)', 47
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Stream Properties', 'PV_ACCESS_TYPE', 'Dimension',
    'Dimension', 'CONTENT ACCESS TYPE (E.G., FREE, PRIME SUBSCRIPTION, RENTAL, PURCHASE)', 48
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Stream Properties', 'PV_OFFER_GROUP', 'Dimension',
    'Dimension', 'CONTENT OFFER GROUP (E.G., FREE, PRIME, RENTAL, PURCHASE)', 49
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Flags', 'PV_GTI_IS_LIVE', 'Dimension',
    'Dimension', 'INDICATES IF CONTENT IS LIVE', 50
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Flags', 'PV_IS_AVOD', 'Dimension',
    'Dimension', 'INDICATES IF CONTENT IS ADVERTISER-SUPPORTED VOD', 51
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Flags', 'PV_IS_CHANNELS', 'Dimension',
    'Dimension', 'INDICATES IF CONTENT IS A CHANNEL', 52
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Flags', 'PV_IS_SVOD', 'Dimension',
    'Dimension', 'INDICATES IF CONTENT IS SUBSCRIPTION VOD', 53
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Flags', 'PV_IS_USER_INITIATED', 'Dimension',
    'Dimension', 'INDICATES IF CONTENT PLAYBACK WAS USER-INITIATED', 54
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Content Flags', 'PV_IS_HH_SHARE', 'Dimension',
    'Dimension', 'INDICATES IF CONTENT IS SHARED WITHIN HOUSEHOLD', 55
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Geographic Data', 'PV_STREAMING_GEO_COUNTRY', 'Dimension',
    'Dimension', 'COUNTRY WHERE EVENT WAS ACCESSED', 56
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Geographic Data', 'PV_STREAMING_LANGUAGE', 'Dimension',
    'Dimension', 'LANGUAGE OF THE EVENT', 57
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'User Data', 'USER_ID', 'Dimension',
    'Dimension', 'PSEUDONYMOUS IDENTIFIER THAT CONNECTS USER ACTIVITY ACROSS DIFFERENT EVENTS. THE FIELD CAN CONTAIN AD USER IDS (REPRESENTING AMAZON ACCOUNTS), DEVICE IDS, OR BROWSER IDS. NULL VALUES APPEAR WHEN AMAZON ADS IS UNABLE TO RESOLVE AN IDENTIFIER FOR AN EVENT. THE FIELD HAS A VERYHIGH AGGREGATION THRESHOLD, MEANING IT CANNOT BE INCLUDED IN FINAL SELECT STATEMENTS BUT CAN BE USED WITHIN COMMON TABLE EXPRESSIONS (CTES) FOR AGGREGATION PURPOSES LIKE COUNT(DISTINCT USERID).', 58
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'User Data', 'USER_ID_TYPE', 'Dimension',
    'Dimension', 'TYPE OF USER ID VALUE. AMC INCLUDES DIFFERENT TYPES OF USER ID VALUES, DEPENDING ON WHETHER THE VALUE REPRESENTS A RESOLVED AMAZON ACCOUNT, A DEVICE, OR A BROWSER COOKIE. IF AMAZON ADS IS UNABLE TO DETERMINE OR PROVIDE AN ID OF ANY KIND FOR AN IMPRESSION EVENT, THE USER_ID AND USER_ID_TYPE VALUES FOR THAT RECORD WILL BE NULL. POSSIBLE VALUES INCLUDE: ''ADUSERID'', ''SISDEVICEID'', ''ADBROWSERID'', AND NULL.', 59
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'Privacy Controls', 'NO_3P_TRACKERS', 'Dimension',
    'Dimension', 'BOOLEAN VALUE INDICATING WHETHER THE EVENT CAN BE USED FOR AUDIENCE CREATION THAT IS THIRD-PARTY TRACKING ENABLED (I.E. WHETHER YOU CAN SERVE CREATIVE WITH THIRD-PARTY TRACKING WHEN RUNNING MEDIA AGAINST THE AUDIENCE). THIRD-PARTY TRACKING REFERS TO MEASUREMENT TAGS AND PIXELS FROM EXTERNAL VENDORS THAT CAN BE USED TO MEASURE AD PERFORMANCE. POSSIBLE VALUES FOR THIS FIELD ARE: ''TRUE'', ''FALSE''.', 60
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Subscription Lifecycle Analysis', '-- Analyze subscription conversion funnel
SELECT 
    pv_benefit_name,
    pv_billing_type,
    COUNT(DISTINCT pv_subscription_id) as subscription_count,
    COUNT(DISTINCT CASE WHEN pv_is_plan_start = true THEN pv_subscription_id END) as plan_starts,
    COUNT(DISTINCT CASE WHEN pv_is_plan_conversion = true THEN pv_subscription_id END) as conversions,
    AVG(pv_unit_price) as avg_unit_price
FROM amazon_pvc_enrollments
WHERE marketplace_id = 1  -- US marketplace
    AND pv_is_latest_record = true
    AND pv_start_date >= ''2025-01-01''
GROUP BY pv_benefit_name, pv_billing_type
ORDER BY subscription_count DESC;', 'Basic', 0
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Content Performance Analysis', '-- Top performing content by viewing time
SELECT 
    pv_gti_series_or_movie_name,
    pv_gti_content_type,
    pv_gti_genre,
    COUNT(DISTINCT pv_session_id) as total_sessions,
    SUM(pv_seconds_viewed) as total_viewing_seconds,
    AVG(pv_seconds_viewed) as avg_session_duration
FROM amazon_pvc_streaming_events_feed
WHERE marketplace_id = 1
    AND pv_playback_date_utc >= ''2025-01-01''
    AND pv_playback_date_utc <= ''2025-01-31''
    AND pv_is_user_initiated = true
GROUP BY pv_gti_series_or_movie_name, pv_gti_content_type, pv_gti_genre
HAVING total_sessions >= 100  -- Filter for statistically significant content
ORDER BY total_viewing_seconds DESC
LIMIT 50;', 'Performance', 1
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Cross-Platform Engagement Analysis', '-- User engagement across subscription and streaming
WITH subscription_users AS (
    SELECT DISTINCT 
        user_id,
        pv_benefit_name,
        pv_billing_type
    FROM amazon_pvc_enrollments
    WHERE marketplace_id = 1
        AND pv_is_latest_record = true
        AND pv_enrollment_status = ''ACTIVE''
),
streaming_summary AS (
    SELECT 
        user_id,
        COUNT(DISTINCT pv_session_id) as streaming_sessions,
        SUM(pv_seconds_viewed) as total_viewing_time,
        COUNT(DISTINCT pv_gti_series_or_movie_name) as unique_content_consumed
    FROM amazon_pvc_streaming_events_feed
    WHERE marketplace_id = 1
        AND pv_playback_date_utc >= ''2025-01-01''
        AND pv_playback_date_utc <= ''2025-01-31''
    GROUP BY user_id
)
SELECT 
    s.pv_benefit_name,
    s.pv_billing_type,
    COUNT(DISTINCT s.user_id) as total_subscribers,
    COUNT(DISTINCT st.user_id) as active_viewers,
    AVG(st.streaming_sessions) as avg_sessions_per_user,
    AVG(st.total_viewing_time) as avg_viewing_time_per_user,
    AVG(st.unique_content_consumed) as avg_unique_content_per_user
FROM subscription_users s
LEFT JOIN streaming_summary st ON s.user_id = st.user_id
GROUP BY s.pv_benefit_name, s.pv_billing_type
ORDER BY total_subscribers DESC;', 'Basic', 2
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Live Content Engagement', '-- Live content streaming analysis
SELECT 
    pv_gti_event_sport,
    pv_gti_event_league,
    pv_gti_event_name,
    COUNT(DISTINCT pv_session_id) as live_sessions,
    SUM(pv_seconds_viewed) as total_live_viewing,
    AVG(pv_seconds_viewed) as avg_session_duration,
    COUNT(DISTINCT CASE WHEN pv_streaming_geo_country = ''US'' THEN pv_session_id END) as us_sessions
FROM amazon_pvc_streaming_events_feed
WHERE marketplace_id = 1
    AND pv_gti_is_live = true
    AND pv_stream_type = ''live-event''
    AND pv_playback_date_utc >= ''2025-01-01''
    AND pv_playback_date_utc <= ''2025-01-31''
GROUP BY pv_gti_event_sport, pv_gti_event_league, pv_gti_event_name
HAVING live_sessions >= 50  -- Focus on popular events
ORDER BY total_live_viewing DESC;', 'Basic', 3
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Promotional Offer Performance', '-- Analyze promotional subscription performance
SELECT 
    pv_offer_name,
    pv_billing_type,
    COUNT(DISTINCT pv_subscription_id) as promo_subscriptions,
    COUNT(DISTINCT CASE WHEN pv_is_plan_conversion = true THEN pv_subscription_id END) as promo_conversions,
    SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN pv_is_plan_conversion = true THEN pv_subscription_id END),
        COUNT(DISTINCT pv_subscription_id)
    ) * 100 as conversion_rate_percent,
    AVG(pv_unit_price) as avg_promo_price
FROM amazon_pvc_enrollments
WHERE marketplace_id = 1
    AND pv_is_promo = true
    AND pv_start_date >= ''2025-01-01''
GROUP BY pv_offer_name, pv_billing_type
HAVING promo_subscriptions >= 10
ORDER BY conversion_rate_percent DESC;', 'Performance', 4
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Data Volume Management', '-- Efficient large-scale content analysis pattern
WITH content_sessions AS (
    SELECT 
        pv_gti_series_or_movie_name,
        pv_gti_content_type,
        COUNT(DISTINCT pv_session_id) as session_count,
        SUM(pv_seconds_viewed) as total_seconds
    FROM amazon_pvc_streaming_events_feed
    WHERE marketplace_id = 1
        AND pv_playback_date_utc = ''2025-01-15''  -- Single day analysis
        AND pv_gti_content_type IN (''Movie'', ''TV Episode'')  -- Specific content types
        AND pv_is_user_initiated = true  -- User-driven sessions only
    GROUP BY pv_gti_series_or_movie_name, pv_gti_content_type
    HAVING session_count >= 10  -- Filter low-volume content
)
SELECT 
    pv_gti_content_type,
    COUNT(*) as content_titles,
    SUM(session_count) as total_sessions,
    SUM(total_seconds) as total_viewing_seconds,
    AVG(total_seconds) as avg_seconds_per_title
FROM content_sessions
GROUP BY pv_gti_content_type
ORDER BY total_viewing_seconds DESC;', 'Basic', 5
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Genre Analysis', '-- Handling array-type genre data
SELECT 
    genre_element,
    COUNT(DISTINCT pv_session_id) as sessions_with_genre,
    SUM(pv_seconds_viewed) as total_viewing_time
FROM amazon_pvc_streaming_events_feed,
UNNEST(pv_gti_genre) as genre_element
WHERE marketplace_id = 1
    AND pv_playback_date_utc >= ''2025-01-01''
    AND pv_playback_date_utc <= ''2025-01-31''
GROUP BY genre_element
ORDER BY total_viewing_time DESC;', 'Basic', 6
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '⚠️ **Important Availability Notice**: Amazon Prime Video Channel Insights is a standalone AMC Paid Features resource available for trial and subscription enrollments within the AMC Paid Features suite of insight expansion options, powered by Amazon Advertising.

**Eligibility Requirements**: This resource is available to Amazon Advertisers that operate Prime Video Channels within the supported AMC Paid Features account marketplaces (US/CA/JP/AU/FR/IT/ES/UK/DE).

Amazon Prime Video Channel Insights is a collection of two AMC data views that represent Prime Video Channel subscriptions and streaming signals, providing comprehensive analytics for Prime Video Channel performance and user engagement.', 0
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'query_patterns', '### Subscription Lifecycle Analysis
```sql
-- Analyze subscription conversion funnel
SELECT 
    pv_benefit_name,
    pv_billing_type,
    COUNT(DISTINCT pv_subscription_id) as subscription_count,
    COUNT(DISTINCT CASE WHEN pv_is_plan_start = true THEN pv_subscription_id END) as plan_starts,
    COUNT(DISTINCT CASE WHEN pv_is_plan_conversion = true THEN pv_subscription_id END) as conversions,
    AVG(pv_unit_price) as avg_unit_price
FROM amazon_pvc_enrollments
WHERE marketplace_id = 1  -- US marketplace
    AND pv_is_latest_record = true
    AND pv_start_date >= ''2025-01-01''
GROUP BY pv_benefit_name, pv_billing_type
ORDER BY subscription_count DESC;
```', 4
FROM amc_data_sources 
WHERE schema_id = 'pvc-insights'
ON CONFLICT DO NOTHING;

-- Insert schema: sponsored_ads_traffic Data Source
INSERT INTO amc_data_sources (
    schema_id, name, category, description, data_sources, 
    is_paid_feature, tags, version
) VALUES (
    'sponsored-ads-traffic',
    'sponsored_ads_traffic Data Source',
    'Sponsored Ads Tables',
    'This table contains impression events, click events, and video creative messages from Sponsored Products, Sponsored Brands, Sponsored Display, and Sponsored TV campaigns. There will be 1 record per sponsored ads impression event and 1 record per click event originated from a sponsored ads campaign.',
    '[]',
    false,
    '["search-ads", "clicks", "sponsored-ads", "impressions"]',
    '1.0.0'
) ON CONFLICT (schema_id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    data_sources = EXCLUDED.data_sources,
    tags = EXCLUDED.tags,
    updated_at = CURRENT_TIMESTAMP;


INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'impressions', 'LONG', 'Metric',
    'Count of sponsored ads impressions. Possible values: ''1'' (if the record represents a sponsored ads impression) or ''0'' (if not).', 'NONE', 0
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'clicks', 'LONG', 'Metric',
    'Count of sponsored ads clicks. Possible values: ''1'' (if the record represents a click event) or ''0'' (if not).', 'NONE', 1
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'spend', 'LONG', 'Metric',
    'The total advertising cost in microcents for the sponsored ads traffic event. Note that some ad products, such as Sponsored Products, only incur costs for click events. Divide by 100,000,000 to convert to dollars (e.g., 100,000,000 microcents = $1.00). Example value: ''325000''.', 'LOW', 2
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'ad_product_type', 'STRING', 'Dimension',
    'Type of sponsored ads campaign that generated the traffic event. Possible values include: ''sponsored_products'', ''sponsored_brands'', ''sponsored_display'', and ''sponsored_television''.', 'LOW', 3
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'advertiser', 'STRING', 'Dimension',
    'Name of the business entity running advertising campaigns on sponsored ads. Example value: ''Widgets Inc''.', 'LOW', 4
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign', 'STRING', 'Dimension',
    'Name of the sponsored ads campaign responsible for the traffic event. Example value: ''Widgets_Q1_2024_Keywords_US''.', 'LOW', 5
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_id', 'LONG', 'Dimension',
    'The ID of the sponsored ads campaign associated with the traffic event. This campaign ID can be used in the Ads API, and may differ from the campaign ID shown in the ads console (found in campaign_id_string).', 'LOW', 6
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_id_string', 'STRING', 'Dimension',
    'The ID of the sponsored ads campaign associated with the traffic event. This is the campaign ID shown in the ads console, and may differ from the campaign ID used in the Ads API (found in campaign_id).', 'LOW', 7
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'campaign_budget_type', 'STRING', 'Dimension',
    'Type of budget allocation for a sponsored ads campaign. Possible values include: ''DAILY_BUDGET'' and ''LIFETIME_BUDGET''.', 'LOW', 8
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'ad_group', 'STRING', 'Dimension',
    'Name of the sponsored ads ad group. Values will match the line_item field. Example value: ''SP_Widgets_Spring_2025''.', 'LOW', 9
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'line_item', 'STRING', 'Dimension',
    'Name of the sponsored ads ad group. Values will match the ad_group field. Example value: ''SP_Widgets_Spring_2025''.', 'LOW', 10
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'ad_group_id / line_item_id', 'LONG', 'Dimension',
    'ID of the sponsored ads ad group.', 'LOW', 11
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'ad_group_status / line_item_status', 'STRING', 'Dimension',
    'Status of the sponsored ads ad group. Possible values include: ''ENABLED'', ''PAUSED'', and ''ARCHIVED''.', 'LOW', 12
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'ad_group_type', 'STRING', 'Dimension',
    'Type of sponsored ads ad group.', 'LOW', 13
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'porfolio_id', 'STRING', 'Dimension',
    'The ID of the portfolio that the campaign belongs to. Portfolios are groups of campaigns organized by brand, product category, or season.', 'LOW', 14
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'portfolio_name', 'STRING', 'Dimension',
    'The name of the portfolio that the campaign belongs to.', 'LOW', 15
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative', 'STRING', 'Dimension',
    'Name of the sponsored ads creative/ad. Example value: ''2025_US_Widgets_B01234ABC''.', 'LOW', 16
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_asin', 'STRING', 'Dimension',
    'The ASIN that appears in the ad. Note: Only populated for a subset of Sponsored Products and Sponsored Display events. For other ad products, this will be NULL.', 'LOW', 17
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'creative_type', 'STRING', 'Dimension',
    'Type of creative/ad. Possible values include: ''static_image'', ''video'', ''third_party_creative''.', 'LOW', 18
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'customer_search_term', 'STRING', 'Dimension',
    'Search term entered by a shopper on Amazon that led to the traffic event. Represents actual text shoppers type into search bar. Example value: ''blue widgets 3 pack''.', 'LOW', 19
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'targeting', 'STRING', 'Dimension',
    'Keyword used by the advertiser for targeting. Example value: ''premium widgets''.', 'LOW', 20
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'match_type', 'STRING', 'Dimension',
    'Type of match between targeting keyword and customer search term. Possible values: ''BROAD'', ''PHRASE'', ''EXACT'', and NULL (for non-keyword-targeted media).', 'LOW', 21
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'placement_type', 'STRING', 'Dimension',
    'Location where the sponsored ad appeared. Example values: ''Top of Search on-Amazon'', ''Detail Page on-Amazon'', ''Homepage on-Amazon'', ''Off Amazon''.', 'LOW', 22
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_date', 'DATE', 'Dimension',
    'Date of the sponsored ads traffic event in advertiser timezone. Example value: ''2025-01-01''.', 'LOW', 23
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_date_utc', 'DATE', 'Dimension',
    'Date of the sponsored ads traffic event in Coordinated Universal Time (UTC).', 'LOW', 24
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt', 'TIMESTAMP', 'Dimension',
    'Timestamp of the sponsored ads traffic event in advertiser timezone.', 'MEDIUM', 25
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_dt_utc', 'TIMESTAMP', 'Dimension',
    'Timestamp of the sponsored ads traffic event in Coordinated Universal Time (UTC).', 'MEDIUM', 26
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_hour', 'INTEGER', 'Dimension',
    'Hour of day when the traffic event occurred (0-23) in advertiser timezone.', 'LOW', 27
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_hour_utc', 'INTEGER', 'Dimension',
    'Hour of day when the traffic event occurred (0-23) in UTC.', 'LOW', 28
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'five_sec_views', 'LONG', 'Metric',
    'Count of video impressions where video was viewed for at least five seconds. For videos shorter than 5 seconds, this is always ''1''. Values: ''1'' (qualifying view) or ''0'' (not qualifying).', 'NONE', 29
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_first_quartile_views', 'LONG', 'Metric',
    'Count of video impressions where video was viewed to first quartile (25% completion). Values: ''1'' (reached 25%) or ''0'' (did not reach 25%).', 'NONE', 30
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_midpoint_views', 'LONG', 'Metric',
    'Count of video impressions where video was viewed to midpoint (50% completion). Values: ''1'' (reached 50%) or ''0'' (did not reach 50%).', 'NONE', 31
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_third_quartile_views', 'LONG', 'Metric',
    'Count of video impressions where video was viewed to third quartile (75% completion). Values: ''1'' (reached 75%) or ''0'' (did not reach 75%).', 'NONE', 32
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_complete_views', 'LONG', 'Metric',
    'Count of video impressions where video was viewed to completion (100%). Values: ''1'' (completed) or ''0'' (not completed).', 'NONE', 33
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'video_unmutes', 'LONG', 'Metric',
    'Count of video impressions where shopper unmuted the video. Values: ''1'' (unmuted) or ''0'' (not unmuted).', 'NONE', 34
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'viewable_impressions', 'LONG', 'Metric',
    'Count of impressions considered viewable per MRC standards (50% pixels visible for 1+ seconds for display, 2+ seconds for video). Values: ''1'' (viewable) or ''0'' (not viewable).', 'NONE', 35
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'unmeasurable_viewable_impressions', 'LONG', 'Metric',
    'Count of unmeasurable viewable/synthetic view events estimated to be viewable but couldn''t be measured. Values: ''1'' (unmeasurable viewable) or ''0'' (not unmeasurable viewable).', 'NONE', 36
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'view_definition', 'STRING', 'Dimension',
    'Type of viewability measurement definition used to classify the view event. NULL for non-view events.', 'LOW', 37
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'matched_behavior_segment_ids', 'ARRAY', 'Metric',
    'For impressions subject to audience bid multiplier, the segment ID for the matched audience. May include first-party segments or Amazon-created segments.', 'LOW', 38
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_id', 'STRING', 'Dimension',
    'Pseudonymous identifier connecting user activity across events. VERY_HIGH aggregation threshold - use in CTEs only.', 'VERY_HIGH', 39
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'user_id_type', 'STRING', 'Dimension',
    'Type of user ID value: ''adUserId'', ''sisDeviceId'', ''adBrowserId'', or NULL.', 'LOW', 40
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'event_id', 'STRING', 'Dimension',
    'Internal event ID that uniquely identifies sponsored ads traffic events. Use to join with amazon_attributed_* tables (traffic_event_id).', 'VERY_HIGH', 41
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'entity_id', 'STRING', 'Dimension',
    'ID of the Amazon Ads entity (seat) associated with the traffic event.', 'LOW', 42
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'marketplace_name', 'STRING', 'Dimension',
    'Marketplace name where event occurred.', 'LOW', 43
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'currency_iso_code', 'STRING', 'Dimension',
    'Currency ISO code for monetary values (e.g., ''USD'').', 'LOW', 44
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'currency_name', 'STRING', 'Dimension',
    'Currency name for monetary values (e.g., ''Dollar (USA)'').', 'LOW', 45
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'operating_system', 'STRING', 'Dimension',
    'Operating system of device where event occurred. Example values: ''iOS'', ''Android'', ''Windows'', ''macOS'', ''Roku OS''.', 'LOW', 46
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'os_version', 'STRING', 'Dimension',
    'Operating system version. Format varies by OS type. Example: ''17.5.1''.', 'LOW', 47
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_fields (
    data_source_id, field_name, data_type, dimension_or_metric,
    description, aggregation_threshold, field_order
) SELECT 
    id, 'no_3p_trackers', 'BOOLEAN', 'Dimension',
    'Whether event can be used for third-party tracking enabled audience creation. Values: ''true'', ''false''.', 'NONE', 48
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Traffic Overview by Product Type', 'SELECT 
    ad_product_type,
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    SUM(spend) / 100000000.0 as total_spend_dollars,
    CASE 
        WHEN SUM(impressions) > 0 
        THEN SUM(clicks) * 100.0 / SUM(impressions) 
        ELSE 0 
    END as ctr_percent
FROM sponsored_ads_traffic
GROUP BY ad_product_type;', 'Basic', 0
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Video Performance Analysis', 'SELECT 
    campaign,
    SUM(impressions) as video_impressions,
    SUM(five_sec_views) as five_sec_views,
    SUM(video_first_quartile_views) as q1_views,
    SUM(video_midpoint_views) as q2_views,
    SUM(video_third_quartile_views) as q3_views,
    SUM(video_complete_views) as completed_views,
    CASE 
        WHEN SUM(impressions) > 0 
        THEN SUM(video_complete_views) * 100.0 / SUM(impressions)
        ELSE 0 
    END as completion_rate_percent
FROM sponsored_ads_traffic
WHERE creative_type = ''video''
    AND impressions = 1
GROUP BY campaign;', 'Performance', 1
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Search Performance Analysis', '-- Search term performance
SELECT 
    customer_search_term,
    targeting as keyword,
    match_type,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks,
    SUM(spend) / 100000000.0 as spend_dollars
FROM sponsored_ads_traffic
WHERE customer_search_term IS NOT NULL
GROUP BY customer_search_term, targeting, match_type
ORDER BY SUM(spend) DESC;', 'Performance', 2
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Portfolio Performance', '-- Portfolio-level analysis
SELECT 
    portfolio_name,
    campaign,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks,
    SUM(spend) / 100000000.0 as spend_dollars,
    CASE 
        WHEN SUM(clicks) > 0 
        THEN SUM(spend) / 100000000.0 / SUM(clicks)
        ELSE 0 
    END as avg_cpc
FROM sponsored_ads_traffic
WHERE portfolio_name IS NOT NULL
GROUP BY portfolio_name, campaign
ORDER BY portfolio_name, SUM(spend) DESC;', 'Performance', 3
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Placement Performance', '-- Performance by ad placement
SELECT 
    placement_type,
    ad_product_type,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks,
    SUM(viewable_impressions) as viewable_impressions,
    CASE 
        WHEN SUM(impressions) > 0 
        THEN SUM(viewable_impressions) * 100.0 / SUM(impressions)
        ELSE 0 
    END as viewability_rate_percent
FROM sponsored_ads_traffic
WHERE impressions = 1
GROUP BY placement_type, ad_product_type;', 'Performance', 4
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Hourly Performance Patterns', '-- Traffic patterns by hour of day
SELECT 
    event_hour,
    ad_product_type,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks,
    AVG(CASE WHEN clicks > 0 THEN spend / 100000000.0 ELSE NULL END) as avg_cpc
FROM sponsored_ads_traffic
GROUP BY event_hour, ad_product_type
ORDER BY event_hour, ad_product_type;', 'Performance', 5
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_query_examples (
    data_source_id, title, sql_query, category, example_order
) SELECT 
    id, 'Connecting to Conversion Data', '-- Join traffic to attributed conversions
SELECT 
    t.campaign,
    t.customer_search_term,
    SUM(t.clicks) as traffic_clicks,
    SUM(a.total_purchases) as attributed_purchases
FROM sponsored_ads_traffic t
LEFT JOIN amazon_attributed_events_by_conversion_time a
    ON t.event_id = a.traffic_event_id
WHERE t.ad_product_type = ''sponsored_products''
GROUP BY t.campaign, t.customer_search_term;', 'Basic', 6
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'overview', '**Data Source:** `sponsored_ads_traffic`

This table contains impression events, click events, and video creative messages from Sponsored Products, Sponsored Brands, Sponsored Display, and Sponsored TV campaigns. There will be 1 record per sponsored ads impression event and 1 record per click event originated from a sponsored ads campaign.', 0
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'concepts', '### Record Structure
- **One record per event**: Separate records for impressions and clicks
- **Event identification**: Use `impressions = 1` for impression events, `clicks = 1` for click events
- **Cost model varies**: Some products (like Sponsored Products) only charge for clicks', 3
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'query_patterns', '### Traffic Overview by Product Type
```sql
SELECT 
    ad_product_type,
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    SUM(spend) / 100000000.0 as total_spend_dollars,
    CASE 
        WHEN SUM(impressions) > 0 
        THEN SUM(clicks) * 100.0 / SUM(impressions) 
        ELSE 0 
    END as ctr_percent
FROM sponsored_ads_traffic
GROUP BY ad_product_type;
```', 4
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'best_practices', '### Query Performance
- **Filter by ad_product_type** early to focus on specific sponsored ads products
- **Use event date filters** to limit time ranges for better performance
- **Consider impressions vs clicks** - filter appropriately for your analysis needs', 5
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_sections (
    data_source_id, section_type, content_markdown, section_order
) SELECT 
    id, 'data_availability', '- **Sponsored Brands**: Available from December 2, 2022
- **Keywords and search terms**: 13 months historical or instance creation date, whichever is sooner
- **Video metrics**: Only populated for video creative types
- **ASIN data**: creative_asin only available for subset of Sponsored Products and Display', 7
FROM amc_data_sources 
WHERE schema_id = 'sponsored-ads-traffic'
ON CONFLICT DO NOTHING;

-- Create schema relationships

INSERT INTO amc_schema_relationships (
    source_schema_id, target_schema_id, relationship_type, description
) SELECT 
    s.id, t.id, 'variant', 'Traffic-time variant of the same attribution data'
FROM amc_data_sources s, amc_data_sources t
WHERE s.schema_id = 'amazon-attributed-events' AND t.schema_id = 'amazon-attributed-events-by-traffic-time'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_relationships (
    source_schema_id, target_schema_id, relationship_type, description
) SELECT 
    s.id, t.id, 'related', 'Clicks are a subset of impressions'
FROM amc_data_sources s, amc_data_sources t
WHERE s.schema_id = 'dsp-impressions' AND t.schema_id = 'dsp-clicks'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_relationships (
    source_schema_id, target_schema_id, relationship_type, description
) SELECT 
    s.id, t.id, 'related', 'Views are viewable impressions'
FROM amc_data_sources s, amc_data_sources t
WHERE s.schema_id = 'dsp-impressions' AND t.schema_id = 'dsp-views'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_relationships (
    source_schema_id, target_schema_id, relationship_type, description
) SELECT 
    s.id, t.id, 'extends', 'All conversions including modeled data'
FROM amc_data_sources s, amc_data_sources t
WHERE s.schema_id = 'conversions' AND t.schema_id = 'conversions-all'
ON CONFLICT DO NOTHING;

INSERT INTO amc_schema_relationships (
    source_schema_id, target_schema_id, relationship_type, description
) SELECT 
    s.id, t.id, 'extends', 'Conversions with relevance scoring'
FROM amc_data_sources s, amc_data_sources t
WHERE s.schema_id = 'conversions' AND t.schema_id = 'conversions-with-relevance'
ON CONFLICT DO NOTHING;