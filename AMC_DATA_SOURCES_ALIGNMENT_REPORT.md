# AMC Data Sources Alignment Report

**Date:** August 14, 2025  
**Project:** RecomAMP - Amazon Marketing Cloud Query Platform

## Executive Summary

Successfully aligned the application's AMC data sources with Amazon's official AMC documentation. The cleanup removed 38 duplicate/legacy entries and ensured all 44 official data sources are properly configured with complete field metadata.

## Initial State Analysis

### Problems Identified
1. **82 total data sources** in database (38 more than official)
2. **Duplicate entries** with different naming conventions:
   - Hyphenated schema IDs (e.g., `dsp-clicks` vs `dsp_clicks`)
   - Legacy "Tables" entries
   - Regional audience segment variants (AMER, APAC, EU)
3. **Missing field data** for most data sources
4. **Inconsistent categorization**

### Duplicate Sources Removed (38 total)

#### Legacy Hyphenated Entries (7)
- `amazon-attributed-events`
- `amazon-brand-store-insights`
- `amazon-retail-purchases`
- `amazon-your-garage`
- `audience-segments`
- `conversions-all`
- `conversions-with-relevance`
- `dsp-clicks`
- `dsp-impressions`
- `dsp-impressions-segment-tables`
- `dsp-video-events`
- `dsp-views`
- `pvc-insights`
- `sponsored-ads-traffic`

#### Regional Audience Segments (24)
- All AMER variants (8 sources)
- All APAC variants (8 sources)
- All EU variants (8 sources)

These regional segments were consolidated into the base segment metadata sources.

## Actions Taken

### 1. Database Cleanup
- Created `cleanup_duplicate_data_sources.py` script
- Removed 38 duplicate/legacy data sources
- Preserved all official data sources with correct schema IDs

### 2. Data Population
- Fixed table naming issues in update scripts
- Ran all 17 update scripts to populate field metadata
- Successfully added field definitions for all data sources

### 3. Code Fixes Applied
- Fixed `update_dsp_impressions_sources.py`:
  - Changed `schema_fields` → `amc_schema_fields`
  - Fixed field column mappings
  - Removed non-existent `updated_at` column references

## Final State

### Official Data Sources by Category (44 total)

#### Attribution (4 sources)
- `amazon_attributed_events_by_conversion_time`
- `amazon_attributed_events_by_conversion_time_for_audiences`
- `amazon_attributed_events_by_traffic_time`
- `amazon_attributed_events_by_traffic_time_for_audiences`

#### Audience Segments (2 sources)
- `segment_metadata`
- `segment_metadata_for_audiences`

#### Brand Store (8 sources)
- `amazon_brand_store_engagement_events`
- `amazon_brand_store_engagement_events_for_audiences`
- `amazon_brand_store_engagement_events_non_endemic`
- `amazon_brand_store_engagement_events_non_endemic_for_audiences`
- `amazon_brand_store_page_views`
- `amazon_brand_store_page_views_for_audiences`
- `amazon_brand_store_page_views_non_endemic`
- `amazon_brand_store_page_views_non_endemic_for_audiences`

#### Conversions (6 sources)
- `conversions` (29 fields)
- `conversions_for_audiences`
- `conversions_all`
- `conversions_all_for_audiences`
- `conversions_with_relevance`
- `conversions_with_relevance_for_audiences`

#### DSP (12 sources)
- `dsp_clicks`
- `dsp_clicks_for_audiences`
- `dsp_impressions` (103 fields)
- `dsp_impressions_for_audiences` (103 fields)
- `dsp_impressions_by_matched_segments`
- `dsp_impressions_by_matched_segments_for_audiences`
- `dsp_impressions_by_user_segments`
- `dsp_impressions_by_user_segments_for_audiences`
- `dsp_video_events_feed`
- `dsp_video_events_feed_for_audiences`
- `dsp_views`
- `dsp_views_for_audiences`

#### Prime Video Channels (4 sources)
- `amazon_pvc_enrollments`
- `amazon_pvc_enrollments_for_audiences`
- `amazon_pvc_streaming_events_feed`
- `amazon_pvc_streaming_events_feed_for_audiences`

#### Retail Purchases (2 sources)
- `amazon_retail_purchases`
- `amazon_retail_purchases_for_audiences`

#### Sponsored Ads (2 sources)
- `sponsored_ads_traffic`
- `sponsored_ads_traffic_for_audiences`

#### Vehicle Data (3 sources)
- `your_garage`
- `your_garage_for_audiences`
- `experian_vehicle_purchases`

#### Offline Sales (1 source)
- `ncs_cpg_insights_stream`

## Verification Results

### Database Integrity
✅ All 44 official data sources present  
✅ No duplicate schema IDs  
✅ Consistent naming convention (underscore-separated)  
✅ Proper categorization  
✅ Field metadata populated

### API Functionality
✅ Backend service running on port 8001  
✅ Frontend service running on port 5173  
✅ API documentation accessible at `/docs`  
✅ Data source endpoints functional with authentication

### Application Status
✅ Services start successfully  
✅ No database errors  
✅ Schema relationships preserved  
✅ Query builder integration intact

## Scripts Created

1. **`cleanup_duplicate_data_sources.py`**
   - Removes duplicate/legacy data sources
   - Handles cascading deletes for related tables
   - Includes dry-run mode for safety

2. **`populate_all_data_sources.py`**
   - Runs all update scripts in sequence
   - Provides progress tracking
   - Reports any failures

## Recommendations

1. **Regular Validation**: Run the cleanup script periodically to ensure alignment
2. **Update Scripts**: Keep update scripts synchronized with AMC API changes
3. **Documentation**: Update CLAUDE.md with new data source information
4. **Testing**: Add automated tests to verify data source integrity

## Files Modified

- `/root/amazon-helper/scripts/update_dsp_impressions_sources.py` - Fixed table references
- `/root/amazon-helper/scripts/cleanup_duplicate_data_sources.py` - Created for cleanup
- `/root/amazon-helper/scripts/populate_all_data_sources.py` - Created for batch updates

## Conclusion

The AMC data sources in the RecomAMP application are now fully aligned with Amazon's official AMC documentation. The cleanup removed all duplicate and legacy entries while preserving the correct official sources with complete field metadata. The application is ready for production use with accurate schema information for query building and execution.

### Key Achievements
- ✅ Reduced data sources from 82 to 44 (official count)
- ✅ Eliminated all duplicate entries
- ✅ Populated field metadata for all sources
- ✅ Fixed script bugs for future maintenance
- ✅ Verified application functionality

The alignment ensures users have access to the correct, official AMC data sources without confusion from duplicates or outdated entries.