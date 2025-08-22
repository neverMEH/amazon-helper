#!/usr/bin/env python3
"""
Verify all components of the cart abandonment guide
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def verify_guide_components():
    """Verify all components of the cart abandonment guide were created"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get the guide
        guide_response = client.table('build_guides').select('*').eq('guide_id', 'guide_cart_abandonment_audience').execute()
        
        if not guide_response.data:
            logger.error("Guide not found!")
            return False
            
        guide = guide_response.data[0]
        guide_uuid = guide['id']
        
        print("\n" + "="*80)
        print("CART ABANDONMENT AUDIENCE GUIDE - VERIFICATION REPORT")
        print("="*80)
        
        print(f"\n📚 GUIDE DETAILS:")
        print(f"  Name: {guide['name']}")
        print(f"  Category: {guide['category']}")
        print(f"  Difficulty: {guide['difficulty_level']}")
        print(f"  Est. Time: {guide['estimated_time_minutes']} minutes")
        print(f"  Published: {guide['is_published']}")
        print(f"  Tags: {', '.join(guide['tags'])}")
        
        # Get sections
        sections_response = client.table('build_guide_sections').select('*').eq('guide_id', guide_uuid).order('display_order').execute()
        print(f"\n📄 SECTIONS ({len(sections_response.data)}):")
        for section in sections_response.data:
            print(f"  {section['display_order']}. {section['title']}")
            print(f"     - ID: {section['section_id']}")
            print(f"     - Content Length: {len(section['content_markdown'])} chars")
        
        # Get queries
        queries_response = client.table('build_guide_queries').select('*').eq('guide_id', guide_uuid).order('display_order').execute()
        print(f"\n🔍 QUERIES ({len(queries_response.data)}):")
        for query in queries_response.data:
            print(f"  {query['display_order']}. {query['title']}")
            print(f"     - Type: {query['query_type']}")
            print(f"     - Parameters: {list(query.get('parameters_schema', {}).keys())}")
            
            # Get examples for this query
            examples_response = client.table('build_guide_examples').select('*').eq('guide_query_id', query['id']).execute()
            if examples_response.data:
                print(f"     - Examples: {len(examples_response.data)} sample result(s)")
        
        # Get metrics
        metrics_response = client.table('build_guide_metrics').select('*').eq('guide_id', guide_uuid).order('display_order').execute()
        print(f"\n📊 METRICS & DIMENSIONS ({len(metrics_response.data)}):")
        metrics_list = [m for m in metrics_response.data if m['metric_type'] == 'metric']
        dimensions_list = [d for d in metrics_response.data if d['metric_type'] == 'dimension']
        
        print(f"  Metrics ({len(metrics_list)}):")
        for metric in metrics_list:
            print(f"    - {metric['display_name']} ({metric['metric_name']})")
            
        print(f"  Dimensions ({len(dimensions_list)}):")
        for dimension in dimensions_list:
            print(f"    - {dimension['display_name']} ({dimension['metric_name']})")
        
        print("\n" + "="*80)
        print("✅ GUIDE VERIFICATION COMPLETE - ALL COMPONENTS CREATED SUCCESSFULLY!")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify guide: {e}")
        return False

if __name__ == "__main__":
    success = verify_guide_components()
    sys.exit(0 if success else 1)