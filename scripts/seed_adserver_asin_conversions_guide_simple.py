#!/usr/bin/env python
"""
Simplified seed script for Amazon Ad Server - Daily Performance with ASIN Conversions build guide
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

def main():
    """Main execution function"""
    print("Starting Amazon Ad Server - Daily ASIN Conversions guide creation...")
    
    try:
        # Create the guide
        guide_data = {
            "guide_id": "guide_adserver_daily_asin_conversions",
            "name": "Amazon Ad Server - Daily Performance with ASIN Conversions",
            "short_description": "Track the impact of Amazon Ad Server advertising on Amazon conversions and Ad Server Tag Manager conversions with custom attribution",
            "category": "Amazon Ad Server",
            "difficulty_level": "advanced",
            "estimated_time_minutes": 45,
            "prerequisites": [
                "AMC Instance with Ad Server data",
                "Understanding of attribution models",
                "Knowledge of ASIN tracking"
            ],
            "tags": ["ad-server", "conversions", "attribution", "asin-tracking", "cross-channel"],
            "is_published": True,
            "display_order": 10,
            "icon": "📊"
        }
        
        # Check if guide exists
        existing = supabase.table("build_guides").select("*").eq("guide_id", guide_data["guide_id"]).execute()
        
        if existing.data:
            print(f"Guide {guide_data['guide_id']} already exists, updating...")
            result = supabase.table("build_guides").update(guide_data).eq("guide_id", guide_data["guide_id"]).execute()
        else:
            print(f"Creating new guide {guide_data['guide_id']}...")
            result = supabase.table("build_guides").insert(guide_data).execute()
        
        guide = result.data[0]
        guide_uuid = guide["id"]
        guide_id = guide["guide_id"]
        
        print(f"Successfully created/updated guide: {guide_id}")
        print(f"Category: {guide['category']}")
        print(f"Difficulty: {guide['difficulty_level']}")
        
        # Note: Sections, queries, examples, and metrics would be added here
        # This simplified version just creates the main guide
        
        print("\n✅ Guide successfully created!")
        print("Note: Run the full script to add sections, queries, examples, and metrics")
        
    except Exception as e:
        print(f"\n❌ Error creating guide: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()