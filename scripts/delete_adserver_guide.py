#!/usr/bin/env python
"""
Quick script to delete the Amazon Ad Server guides that were created incorrectly
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

def delete_guide():
    """Delete the incorrectly created Ad Server guides"""
    
    guide_ids_to_delete = [
        "guide_adserver_audience_segments",
        "guide_adserver_campaign_overlap",
        "guide_adserver_dco_target_signals",
        "guide_adserver_media_cost",
        "guide_adserver_display_streaming_overlap"
    ]
    
    for guide_id in guide_ids_to_delete:
        try:
            result = supabase.table("build_guides").delete().eq("guide_id", guide_id).execute()
            if result.data:
                print(f"✓ Deleted guide: {guide_id}")
            else:
                print(f"- Guide not found: {guide_id}")
        except Exception as e:
            print(f"✗ Error deleting {guide_id}: {e}")
    
    print("\n✅ Cleanup completed!")

if __name__ == "__main__":
    try:
        delete_guide()
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)