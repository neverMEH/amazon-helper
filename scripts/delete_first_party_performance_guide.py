#!/usr/bin/env python
"""
Delete script for First-Party vs Unknown Customer Performance Analysis Build Guide
Removes the guide and all related data
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

def delete_first_party_performance_guide():
    """Delete the First-Party vs Unknown Customer Performance Analysis guide"""
    
    guide_id = "guide_first_party_performance"
    
    try:
        # Delete the guide (cascade will handle related tables)
        result = supabase.table("build_guides").delete().eq("guide_id", guide_id).execute()
        
        if result.data:
            print(f"✅ Successfully deleted guide: {guide_id}")
            print("   All related sections, queries, examples, and metrics were also removed.")
        else:
            print(f"⚠️  Guide not found: {guide_id}")
            
    except Exception as e:
        print(f"❌ Error deleting guide: {e}")
        raise

if __name__ == "__main__":
    delete_first_party_performance_guide()