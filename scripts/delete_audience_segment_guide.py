#!/usr/bin/env python
"""
Deletion script for Audience Segment Conversions Build Guide
Removes the guide and all related data from the database
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

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    sys.exit(1)

supabase: Client = create_client(url, key)

def delete_guide():
    """Delete the Audience Segment Conversions guide and all related data"""
    try:
        # Find the guide
        result = supabase.table("build_guides").select("id, name").eq("guide_id", "guide_audience_segment_conversions").execute()
        
        if not result.data:
            print("Guide 'guide_audience_segment_conversions' not found")
            return False
            
        guide = result.data[0]
        guide_uuid = guide["id"]
        guide_name = guide["name"]
        
        print(f"Deleting guide: {guide_name}")
        
        # Delete the guide (should cascade to related tables)
        supabase.table("build_guides").delete().eq("id", guide_uuid).execute()
        
        print(f"✅ Successfully deleted guide: {guide_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting guide: {str(e)}")
        return False

def main():
    """Main execution"""
    print("Audience Segment Conversions Guide Deletion Script")
    print("=" * 50)
    
    # Confirm deletion
    confirm = input("Are you sure you want to delete the Audience Segment Conversions guide? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("Deletion cancelled")
        return
    
    if delete_guide():
        print("\nGuide has been successfully removed from the database")
    else:
        print("\nFailed to delete the guide")
        sys.exit(1)

if __name__ == "__main__":
    main()