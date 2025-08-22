#!/usr/bin/env python3
"""
Verification script for Extended Customer Value build guide
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    print("Error: Missing Supabase credentials")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

def verify_guide():
    """Verify the Extended Customer Value guide was created successfully"""
    
    print("Verifying Extended Customer Value build guide...\n")
    
    # 1. Check main guide
    guide_result = supabase.table("build_guides").select("*").eq("guide_id", "guide_extended_customer_value").execute()
    if not guide_result.data:
        print("❌ Guide not found")
        return False
    
    guide = guide_result.data[0]
    guide_uuid = guide['id']
    print(f"✓ Guide found: {guide['name']}")
    print(f"  - Category: {guide['category']}")
    print(f"  - Difficulty: {guide['difficulty_level']}")
    print(f"  - Time: {guide['estimated_time_minutes']} minutes")
    print(f"  - Status: {'Published' if guide['is_published'] else 'Draft'}")
    
    # 2. Check sections
    sections_result = supabase.table("build_guide_sections").select("*").eq("guide_id", guide_uuid).order("display_order").execute()
    print(f"\n✓ Sections: {len(sections_result.data)}")
    for section in sections_result.data:
        print(f"  {section['display_order']}. {section['title']}")
    
    # 3. Check queries
    queries_result = supabase.table("build_guide_queries").select("*").eq("guide_id", guide_uuid).order("display_order").execute()
    print(f"\n✓ Queries: {len(queries_result.data)}")
    for query in queries_result.data:
        print(f"  {query['display_order']}. {query['title']} ({query['query_type']})")
        
    # 4. Check examples
    if queries_result.data:
        examples_count = 0
        for query in queries_result.data:
            examples_result = supabase.table("build_guide_examples").select("*").eq("guide_query_id", query['id']).execute()
            examples_count += len(examples_result.data)
            for example in examples_result.data:
                print(f"    - Example: {example['example_name']}")
        print(f"  Total examples: {examples_count}")
    
    # 5. Check metrics
    metrics_result = supabase.table("build_guide_metrics").select("*").eq("guide_id", guide_uuid).order("display_order").execute()
    print(f"\n✓ Metrics: {len(metrics_result.data)}")
    for metric in metrics_result.data:
        print(f"  - {metric['metric_name']} ({metric['metric_type']}): {metric['display_name']}")
    
    print("\n✅ Verification complete! Guide is ready to use.")
    return True

if __name__ == "__main__":
    try:
        verify_guide()
    except Exception as e:
        print(f"❌ Error verifying guide: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)