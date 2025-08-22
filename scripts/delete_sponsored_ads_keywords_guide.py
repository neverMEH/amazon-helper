#!/usr/bin/env python3
"""
Delete script for "Audience based on sponsored ads keywords" build guide
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def delete_guide():
    """Delete the sponsored ads keywords build guide"""
    guide_id_to_delete = "guide_audience_sponsored_ads_keywords"
    
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Find the guide
        guide_response = client.table('build_guides').select('id, name').eq('guide_id', guide_id_to_delete).execute()
        
        if not guide_response.data:
            print(f"Guide with ID '{guide_id_to_delete}' not found.")
            return False
        
        guide = guide_response.data[0]
        guide_uuid = guide['id']
        guide_name = guide['name']
        
        print(f"Found guide: {guide_name}")
        print(f"Internal ID: {guide_uuid}")
        
        # Confirm deletion
        confirm = input(f"Are you sure you want to delete the guide '{guide_name}'? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Deletion cancelled.")
            return False
        
        # Delete the guide (cascades to related tables due to foreign keys)
        delete_response = client.table('build_guides').delete().eq('id', guide_uuid).execute()
        
        if delete_response.data:
            print(f"✅ Successfully deleted guide: {guide_name}")
            return True
        else:
            print(f"❌ Failed to delete guide")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting guide: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    success = delete_guide()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()