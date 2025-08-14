#!/usr/bin/env python3
"""
Populate all AMC data sources with fields and metadata
Runs all update scripts to ensure complete data
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# List of update scripts to run in order
UPDATE_SCRIPTS = [
    'update_conversions_sources.py',
    'update_conversions_all_sources.py',
    'update_conversions_relevance_sources.py',
    'update_attributed_events_sources.py',
    'update_brand_store_sources.py',
    'update_dsp_clicks_sources.py',
    'update_dsp_impressions_sources.py',
    'update_dsp_segments_sources.py',
    'update_dsp_video_sources.py',
    'update_dsp_views_sources.py',
    'update_sponsored_ads_traffic_sources.py',
    'update_pvc_insights_sources.py',
    'update_retail_purchases_sources.py',
    'update_your_garage_sources.py',
    'update_experian_vehicle_sources.py',
    'update_ncs_cpg_insights_sources.py',
    'update_audience_segments_sources.py'
]


def run_update_script(script_name: str) -> Tuple[bool, str]:
    """
    Run a single update script
    
    Args:
        script_name: Name of the script to run
        
    Returns:
        Tuple of (success, output/error message)
    """
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        return False, f"Script not found: {script_path}"
    
    try:
        logger.info(f"Running {script_name}...")
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout per script
        )
        
        if result.returncode == 0:
            logger.info(f"  ✓ {script_name} completed successfully")
            return True, result.stdout
        else:
            logger.error(f"  ✗ {script_name} failed with return code {result.returncode}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        logger.error(f"  ✗ {script_name} timed out")
        return False, "Script execution timed out"
    except Exception as e:
        logger.error(f"  ✗ Error running {script_name}: {e}")
        return False, str(e)


def main():
    """Main function to run all update scripts"""
    logger.info("="*60)
    logger.info("AMC DATA SOURCES POPULATION")
    logger.info("="*60)
    logger.info(f"Will run {len(UPDATE_SCRIPTS)} update scripts")
    logger.info("")
    
    success_count = 0
    failed_scripts = []
    
    for script_name in UPDATE_SCRIPTS:
        success, message = run_update_script(script_name)
        
        if success:
            success_count += 1
        else:
            failed_scripts.append((script_name, message))
    
    # Summary
    logger.info("")
    logger.info("="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Scripts run: {len(UPDATE_SCRIPTS)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {len(failed_scripts)}")
    
    if failed_scripts:
        logger.info("")
        logger.info("Failed scripts:")
        for script, error in failed_scripts:
            logger.info(f"  - {script}")
            if error and len(error) < 200:
                logger.info(f"    Error: {error[:200]}")
    
    if success_count == len(UPDATE_SCRIPTS):
        logger.info("")
        logger.info("✅ All data sources populated successfully!")
        return 0
    else:
        logger.warning("")
        logger.warning(f"⚠️ {len(failed_scripts)} scripts failed. Please review and run them manually.")
        return 1


if __name__ == "__main__":
    sys.exit(main())