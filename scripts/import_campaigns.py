#!/usr/bin/env python3
"""Import campaigns from Amazon API into Supabase"""

import os
import sys
import asyncio
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.services.campaign_service import campaign_service
from amc_manager.services.db_service import db_service
from amc_manager.services.token_service import token_service
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


async def import_campaigns_for_email(email: str, profile_ids: list = None):
    """Import campaigns for a user by email"""
    print(f"\nImporting campaigns for user: {email}")
    print("=" * 50)
    
    # Get user
    user = await db_service.get_user_by_email(email)
    if not user:
        print(f"✗ User not found: {email}")
        return
    
    print(f"✓ Found user: {user['name']} (ID: {user['id']})")
    
    # Validate token
    access_token = await token_service.get_valid_token(user['id'])
    if not access_token:
        print("✗ No valid token available for user")
        print("\nPlease run token validation first:")
        print("  python scripts/validate_tokens.py --store")
        return
    
    print("✓ Valid access token found")
    
    # Get user profiles
    profiles = await token_service.get_user_profiles(access_token)
    if not profiles:
        print("✗ No advertising profiles found")
        return
    
    print(f"\n✓ Found {len(profiles)} advertising profiles:")
    
    # Filter profiles if specific ones requested
    if profile_ids:
        profiles = [p for p in profiles if str(p['profileId']) in profile_ids]
        print(f"  Filtered to {len(profiles)} profiles")
    
    # Import campaigns for each profile
    total_counts = {
        'dsp': 0,
        'sponsored_products': 0,
        'sponsored_display': 0,
        'sponsored_brands': 0,
        'total': 0
    }
    
    for i, profile in enumerate(profiles, 1):
        profile_id = profile['profileId']
        profile_name = profile.get('accountInfo', {}).get('name', 'Unknown')
        country = profile.get('countryCode', 'US')
        
        print(f"\n[{i}/{len(profiles)}] Profile: {profile_id} - {profile_name} ({country})")
        
        # Skip if not US marketplace (for now)
        if country != 'US':
            print("  ⚠️  Skipping non-US marketplace")
            continue
        
        # Import campaigns
        print("  Importing campaigns...")
        counts = await campaign_service.import_campaigns_for_user(
            user['id'], 
            str(profile_id)
        )
        
        # Update totals
        for key, value in counts.items():
            total_counts[key] += value
        
        print(f"  ✓ Imported: DSP={counts['dsp']}, SP={counts['sponsored_products']}, "
              f"SD={counts['sponsored_display']}, SB={counts['sponsored_brands']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("Import Summary:")
    print(f"  DSP Campaigns: {total_counts['dsp']}")
    print(f"  Sponsored Products: {total_counts['sponsored_products']}")
    print(f"  Sponsored Display: {total_counts['sponsored_display']}")
    print(f"  Sponsored Brands: {total_counts['sponsored_brands']}")
    print(f"  Total Campaigns: {total_counts['total']}")
    print("=" * 50)
    
    return total_counts


async def list_campaigns(email: str):
    """List all campaigns for a user"""
    print(f"\nListing campaigns for user: {email}")
    print("=" * 50)
    
    # Get user
    user = await db_service.get_user_by_email(email)
    if not user:
        print(f"✗ User not found: {email}")
        return
    
    # Get campaigns
    campaigns = await db_service.get_user_campaigns(user['id'])
    if not campaigns:
        print("No campaigns found")
        return
    
    print(f"\nFound {len(campaigns)} campaigns:")
    
    # Group by type
    by_type = {}
    for campaign in campaigns:
        campaign_type = campaign['campaign_type']
        if campaign_type not in by_type:
            by_type[campaign_type] = []
        by_type[campaign_type].append(campaign)
    
    # Display by type
    for campaign_type, type_campaigns in sorted(by_type.items()):
        print(f"\n{campaign_type} Campaigns ({len(type_campaigns)}):")
        for campaign in type_campaigns[:5]:  # Show first 5 of each type
            brand_tag = campaign.get('brand_tag', '')
            brand_str = f" [{brand_tag}]" if brand_tag else ""
            print(f"  - {campaign['campaign_id']}: {campaign['campaign_name']}{brand_str}")
        
        if len(type_campaigns) > 5:
            print(f"  ... and {len(type_campaigns) - 5} more")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Import campaigns from Amazon API")
    parser.add_argument('--email', default='nick@nevermeh.com', help='User email')
    parser.add_argument('--profiles', nargs='+', help='Specific profile IDs to import')
    parser.add_argument('--list', action='store_true', help='List existing campaigns')
    
    args = parser.parse_args()
    
    print("Amazon Campaign Importer")
    print("=" * 50)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.list:
        # List existing campaigns
        await list_campaigns(args.email)
    else:
        # Import campaigns
        await import_campaigns_for_email(args.email, args.profiles)
    
    print(f"\n✅ Campaign import completed!")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())