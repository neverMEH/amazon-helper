#!/usr/bin/env python3
"""
Cleanup duplicate and legacy AMC data sources
Aligns database with official AMC data sources from update scripts
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Set
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Official schema IDs from update scripts
OFFICIAL_SCHEMA_IDS = {
    'amazon_attributed_events_by_conversion_time',
    'amazon_attributed_events_by_conversion_time_for_audiences',
    'amazon_attributed_events_by_traffic_time',
    'amazon_attributed_events_by_traffic_time_for_audiences',
    'amazon_brand_store_engagement_events',
    'amazon_brand_store_engagement_events_for_audiences',
    'amazon_brand_store_engagement_events_non_endemic',
    'amazon_brand_store_engagement_events_non_endemic_for_audiences',
    'amazon_brand_store_page_views',
    'amazon_brand_store_page_views_for_audiences',
    'amazon_brand_store_page_views_non_endemic',
    'amazon_brand_store_page_views_non_endemic_for_audiences',
    'amazon_pvc_enrollments',
    'amazon_pvc_enrollments_for_audiences',
    'amazon_pvc_streaming_events_feed',
    'amazon_pvc_streaming_events_feed_for_audiences',
    'amazon_retail_purchases',
    'amazon_retail_purchases_for_audiences',
    'conversions',
    'conversions_all',
    'conversions_all_for_audiences',
    'conversions_for_audiences',
    'conversions_with_relevance',
    'conversions_with_relevance_for_audiences',
    'dsp_clicks',
    'dsp_clicks_for_audiences',
    'dsp_impressions',
    'dsp_impressions_by_matched_segments',
    'dsp_impressions_by_matched_segments_for_audiences',
    'dsp_impressions_by_user_segments',
    'dsp_impressions_by_user_segments_for_audiences',
    'dsp_impressions_for_audiences',
    'dsp_video_events_feed',
    'dsp_video_events_feed_for_audiences',
    'dsp_views',
    'dsp_views_for_audiences',
    'experian_vehicle_purchases',
    'ncs_cpg_insights_stream',
    'segment_metadata',
    'segment_metadata_for_audiences',
    'sponsored_ads_traffic',
    'sponsored_ads_traffic_for_audiences',
    'your_garage',
    'your_garage_for_audiences'
}

# Schema IDs to remove (legacy/duplicate entries)
SCHEMA_IDS_TO_REMOVE = [
    'amazon-attributed-events',
    'amazon-brand-store-insights',
    'amazon-retail-purchases',
    'amazon-your-garage',
    'audience-segments',
    'audience_segments_amer_inmarket',
    'audience_segments_amer_inmarket_for_audiences',
    'audience_segments_amer_inmarket_snapshot',
    'audience_segments_amer_inmarket_snapshot_for_audiences',
    'audience_segments_amer_lifestyle',
    'audience_segments_amer_lifestyle_for_audiences',
    'audience_segments_amer_lifestyle_snapshot',
    'audience_segments_amer_lifestyle_snapshot_for_audiences',
    'audience_segments_apac_inmarket',
    'audience_segments_apac_inmarket_for_audiences',
    'audience_segments_apac_inmarket_snapshot',
    'audience_segments_apac_inmarket_snapshot_for_audiences',
    'audience_segments_apac_lifestyle',
    'audience_segments_apac_lifestyle_for_audiences',
    'audience_segments_apac_lifestyle_snapshot',
    'audience_segments_apac_lifestyle_snapshot_for_audiences',
    'audience_segments_eu_inmarket',
    'audience_segments_eu_inmarket_for_audiences',
    'audience_segments_eu_inmarket_snapshot',
    'audience_segments_eu_inmarket_snapshot_for_audiences',
    'audience_segments_eu_lifestyle',
    'audience_segments_eu_lifestyle_for_audiences',
    'audience_segments_eu_lifestyle_snapshot',
    'audience_segments_eu_lifestyle_snapshot_for_audiences',
    'conversions-all',
    'conversions-with-relevance',
    'dsp-clicks',
    'dsp-impressions',
    'dsp-impressions-segment-tables',
    'dsp-video-events',
    'dsp-views',
    'pvc-insights',
    'sponsored-ads-traffic'
]


def get_current_data_sources():
    """Get all current data sources from database"""
    try:
        result = supabase.table('amc_data_sources').select('*').execute()
        return result.data
    except Exception as e:
        logger.error(f"Error fetching data sources: {e}")
        return []


def remove_duplicate_sources(dry_run=False):
    """Remove duplicate and legacy data sources"""
    logger.info("Starting cleanup of duplicate data sources...")
    
    removed_count = 0
    errors = []
    
    for schema_id in SCHEMA_IDS_TO_REMOVE:
        try:
            # First check if it exists
            check_result = supabase.table('amc_data_sources')\
                .select('id, name, category')\
                .eq('schema_id', schema_id)\
                .execute()
            
            if check_result.data:
                source = check_result.data[0]
                logger.info(f"Found legacy source to remove: {schema_id} ({source['name']})")
                
                if not dry_run:
                    # Get the ID for cascading deletes
                    source_id = source['id']
                    
                    # Delete related records first (due to foreign key constraints)
                    # Delete fields
                    supabase.table('amc_schema_fields')\
                        .delete()\
                        .eq('data_source_id', source_id)\
                        .execute()
                    
                    # Delete examples
                    supabase.table('amc_query_examples')\
                        .delete()\
                        .eq('data_source_id', source_id)\
                        .execute()
                    
                    # Delete sections
                    supabase.table('amc_schema_sections')\
                        .delete()\
                        .eq('data_source_id', source_id)\
                        .execute()
                    
                    # Delete relationships (both as source and target)
                    supabase.table('amc_schema_relationships')\
                        .delete()\
                        .eq('source_schema_id', source_id)\
                        .execute()
                    
                    supabase.table('amc_schema_relationships')\
                        .delete()\
                        .eq('target_schema_id', source_id)\
                        .execute()
                    
                    # Finally delete the data source
                    result = supabase.table('amc_data_sources')\
                        .delete()\
                        .eq('schema_id', schema_id)\
                        .execute()
                    
                    logger.info(f"  ✓ Removed: {schema_id}")
                    removed_count += 1
                else:
                    logger.info(f"  [DRY RUN] Would remove: {schema_id}")
                    removed_count += 1
            else:
                logger.debug(f"Schema ID not found (already removed?): {schema_id}")
                
        except Exception as e:
            error_msg = f"Error removing {schema_id}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    return removed_count, errors


def verify_remaining_sources():
    """Verify that only official sources remain"""
    sources = get_current_data_sources()
    current_ids = {s['schema_id'] for s in sources}
    
    # Check for any remaining non-official sources
    extra_ids = current_ids - OFFICIAL_SCHEMA_IDS
    
    if extra_ids:
        logger.warning(f"Found {len(extra_ids)} non-official sources still in database:")
        for sid in sorted(extra_ids):
            source = next((s for s in sources if s['schema_id'] == sid), None)
            if source:
                logger.warning(f"  - {sid}: {source['name']}")
    else:
        logger.info("✓ All remaining sources are official!")
    
    # Check if any official sources are missing
    missing_ids = OFFICIAL_SCHEMA_IDS - current_ids
    if missing_ids:
        logger.warning(f"Found {len(missing_ids)} official sources missing from database:")
        for sid in sorted(missing_ids):
            logger.warning(f"  - {sid}")
        logger.info("Run the appropriate update scripts to add these sources.")
    else:
        logger.info("✓ All official sources are present!")
    
    return len(extra_ids), len(missing_ids)


def generate_report(removed_count, errors, extra_count, missing_count):
    """Generate a summary report"""
    report = []
    report.append("\n" + "="*60)
    report.append("AMC DATA SOURCES CLEANUP REPORT")
    report.append("="*60)
    report.append(f"Timestamp: {datetime.now().isoformat()}")
    report.append("")
    
    report.append("CLEANUP RESULTS:")
    report.append(f"  • Sources removed: {removed_count}")
    report.append(f"  • Errors encountered: {len(errors)}")
    
    if errors:
        report.append("\nERRORS:")
        for error in errors:
            report.append(f"  - {error}")
    
    report.append("\nVERIFICATION:")
    report.append(f"  • Non-official sources remaining: {extra_count}")
    report.append(f"  • Official sources missing: {missing_count}")
    
    # Get final count
    sources = get_current_data_sources()
    report.append(f"\nFINAL STATE:")
    report.append(f"  • Total data sources in database: {len(sources)}")
    report.append(f"  • Expected official sources: {len(OFFICIAL_SCHEMA_IDS)}")
    
    if extra_count == 0 and missing_count == 0:
        report.append("\n✅ DATABASE IS FULLY ALIGNED WITH OFFICIAL AMC DATA SOURCES!")
    else:
        report.append("\n⚠️ Some discrepancies remain. Please review and run update scripts as needed.")
    
    report.append("="*60)
    
    report_text = "\n".join(report)
    print(report_text)
    
    # Save report to file
    report_file = Path(__file__).parent / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report_text)
    
    logger.info(f"Report saved to: {report_file}")
    
    return report_text


def main():
    """Main cleanup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cleanup duplicate AMC data sources')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview changes without making them')
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("Running in DRY RUN mode - no changes will be made")
    
    # Show initial state
    sources = get_current_data_sources()
    logger.info(f"Current data sources in database: {len(sources)}")
    
    # Perform cleanup
    removed_count, errors = remove_duplicate_sources(dry_run=args.dry_run)
    
    if not args.dry_run:
        # Verify results
        extra_count, missing_count = verify_remaining_sources()
        
        # Generate report
        generate_report(removed_count, errors, extra_count, missing_count)
    else:
        logger.info(f"\n[DRY RUN] Would remove {removed_count} sources")
        logger.info("Run without --dry-run to apply changes")
    
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())