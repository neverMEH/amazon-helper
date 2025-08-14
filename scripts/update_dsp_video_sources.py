#!/usr/bin/env python3
"""
Update DSP Video Events data sources in AMC
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

# Define the DSP Video Events data sources
dsp_video_sources = [
    {
        "schema_id": "dsp_video_events_feed",
        "name": "Amazon DSP Video Events Feed",
        "description": "Analytics table with the same structure as dsp_impressions but provides video metrics for each video creative event triggered by the video player and associated with the impression event. Tracks video engagement including plays, pauses, quartile completions, and user interactions. Note: Workflows using this table will time out when run over extended periods.",
        "category": "DSP",
        "table_type": "Analytics"
    },
    {
        "schema_id": "dsp_video_events_feed_for_audiences",
        "name": "Amazon DSP Video Events Feed for Audiences",
        "description": "Audience table with the same structure as dsp_impressions but provides video metrics for each video creative event triggered by the video player and associated with the impression event. Tracks video engagement including plays, pauses, quartile completions, and user interactions. Note: Workflows using this table will time out when run over extended periods.",
        "category": "DSP",
        "table_type": "Audience"
    }
]

# Define the additional fields for DSP video events tables (in addition to all dsp_impressions fields)
dsp_video_additional_fields = [
    {
        "name": "video_click",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video clicks. Possible values for this field are: '1' (if the video was viewed to completion) or '0' (if the video was not viewed to completion). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_complete",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video impressions where the video was viewed to completion (100%). Possible values for this field are: '1' (if the video was viewed to completion) or '0' (if the video was not viewed to completion). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_creative_view",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video impressions where an additional ad element, such as the video companion ad or VPAID overlay, was viewed. Possible values for this field are: '1' (if the additional ad element was viewed) or '0' (if the additional ad element was not viewed). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_first_quartile",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video impressions where the video was viewed to the first quartile (at least 25% completion). Possible values for this field are: '1' (if the video was viewed to at least 25% completion) or '0' (if the video was not viewed to 25% completion). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_impression",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video impressions where the first frame of the ad was shown. Possible values for this field are: '1' (if the first frame of the video was shown) or '0' (if the first frame of the video was not shown). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_midpoint",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video impressions where the video was viewed to the midpoint (at least 50% completion). Possible values for this field are: '1' (if the video was viewed to at least 50% completion) or '0' (if the video was not viewed to 50% completion). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_mute",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video mutes. Possible values for this field are: '1' (if the user muted the video) or '0' (if the user did not mute the video). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_pause",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video pauses. Possible values for this field are: '1' (if the user paused the video) or '0' (if the user did not pause the video). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_replay",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video impressions where the ad was replayed again after it completed. Possible values for this field are: 1 (if the user replayed the video after completion) or 0 (if the video was not replayed after completion). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_resume",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video impressions where the video was resumed after a pause. Possible values for this field are: 1 (if the video was resumed after a pause) or 0 (if the video was not resumed after a pause). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_skip_backward",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video impressions that had backward skips. Possible values for this field are: '1' (if the user skipped the video backward) or '0' (if the user did not skip the video backward). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_skip_forward",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video impressions that had forward skips. Possible values for this field are: '1' (if the user skipped the video forward) or '0' (if the user did not skip the video forward). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_start",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video impression starts. Possible values for this field are: '1' (if the user started the video) or '0' (if the user did not start the video). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_third_quartile",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video impressions where the video was viewed to the third quartile (at least 75% completion). Possible values for this field are: '1' (if the video was viewed to at least 75% completion) or '0' (if the video was not viewed to 75% completion). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "video_unmute",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The number of Amazon DSP video unmutes. Possible values for this field are: '1' (if the video was unmuted) or '0' (if the video was not unmuted). This field will always be '0' for non-video impressions.",
        "aggregation_threshold": "NONE"
    }
]

def update_dsp_video():
    """Update DSP Video Events data sources"""
    
    print("\n=== Updating DSP Video Events Data Sources ===\n")
    
    # Update/Insert data sources
    for source in dsp_video_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            if existing.data:
                # Update existing
                result = supabase.table('amc_data_sources').update({
                    'name': source['name'],
                    'description': source['description'],
                    'category': source['category'],
                    'tags': [source.get('table_type'), 'Video-Metrics', 'Performance-Warning'] if source.get('table_type') else ['Video-Metrics', 'Performance-Warning'],
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
                    'tags': [source.get('table_type'), 'Video-Metrics', 'Performance-Warning'] if source.get('table_type') else ['Video-Metrics', 'Performance-Warning'],
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).execute()
                print(f"✅ Created data source: {source['schema_id']}")
                data_source_id = result.data[0]['id']
            
            # Note: These tables have all fields from dsp_impressions PLUS the video fields
            print(f"  Inherits all fields from dsp_impressions")
            print(f"  Plus {len(dsp_video_additional_fields)} video-specific metrics")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            continue
    
    print("\n=== DSP Video Events Update Complete ===")
    
    # Verify the update
    print("\n=== Verification ===")
    for schema_id in ['dsp_video_events_feed', 'dsp_video_events_feed_for_audiences']:
        result = supabase.table('amc_data_sources').select('name, description, tags').eq('schema_id', schema_id).execute()
        if result.data:
            print(f"\n{schema_id}:")
            print(f"  Name: {result.data[0]['name']}")
            print(f"  Description: {result.data[0]['description'][:100]}...")
            print(f"  Tags: {result.data[0].get('tags', [])}")
    
    print("\n⚠️  Important Note: These tables have performance limitations and will time out when run over extended periods.")
    print("   Video events provide detailed engagement metrics for video creative campaigns.")
    
    print("\n📊 Video Metrics Available:")
    print("   - Quartile completions (25%, 50%, 75%, 100%)")
    print("   - User interactions (play, pause, mute, unmute, skip)")
    print("   - Engagement metrics (clicks, replays, creative views)")

if __name__ == "__main__":
    update_dsp_video()