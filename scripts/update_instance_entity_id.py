#!/usr/bin/env python
"""Update AMC instance with entity_id"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager

def update_entity_id(instance_name: str, entity_id: str):
    """Update entity_id for an AMC instance"""
    db = SupabaseManager().get_client()
    
    # Update the instance
    result = db.table('amc_instances').update({
        'entity_id': entity_id
    }).eq('instance_name', instance_name).execute()
    
    if result.data:
        print(f"✓ Updated {instance_name} with entity_id: {entity_id}")
        return True
    else:
        print(f"✗ Failed to update {instance_name}")
        return False

if __name__ == "__main__":
    # For Supergoop, we need the actual entity_id from Amazon
    # This is typically the profile ID or advertiser ID
    # Common patterns:
    # - Profile ID: A numeric ID like "1234567890" 
    # - Entity ID format: "ENTITY_XXXXX" or just the profile ID
    
    instance_name = "recommercesupergoopus"
    
    # IMPORTANT: Replace this with the actual entity_id from Amazon
    # You can find this in:
    # 1. Amazon Advertising Console - Profile details
    # 2. AMC Console - Instance configuration
    # 3. API response when calling /v2/profiles endpoint
    
    # Using a placeholder for now - YOU MUST REPLACE THIS
    entity_id = "ENTITY_PLACEHOLDER"  # <-- REPLACE WITH ACTUAL VALUE
    
    print(f"Updating {instance_name} with entity_id: {entity_id}")
    print("⚠️  WARNING: Using placeholder entity_id - this will NOT work until you provide the real value!")
    print()
    print("To find the correct entity_id:")
    print("1. Log into Amazon Advertising Console")
    print("2. Go to your account/profile settings")
    print("3. Look for Profile ID or Advertiser ID")
    print("4. Replace ENTITY_PLACEHOLDER with that value")
    print()
    
    # Uncomment and update this line with the real entity_id:
    # entity_id = "YOUR_ACTUAL_ENTITY_ID_HERE"
    # update_entity_id(instance_name, entity_id)