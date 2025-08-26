#!/usr/bin/env python3
"""
Update instance_brands table with comprehensive brand mappings
based on instance names and available campaigns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager
from datetime import datetime

def get_brand_suggestions(instance_name):
    """Get brand suggestions based on instance name"""
    
    # Remove common prefixes and suffixes
    cleaned = instance_name.lower()
    cleaned = cleaned.replace('recommerce', '').replace('recom', '').replace('nevermeh', '')
    cleaned = cleaned.replace('us', '').replace('ca', '').replace('eu', '').replace('sandbox', '')
    
    # Comprehensive mapping based on instance names
    mappings = {
        # Beauty & Personal Care
        'truegrace': ['True Grace', 'Terry Naturally', 'Terry Naturally Canada'],
        'terrynaturally': ['Terry Naturally', 'Terry Naturally Canada'],
        'urbandecay': ['Urban Decay'],
        'itcosmetics': ['IT Cosmetics'],
        'fekkai': ['FEKKAI', 'Fekkai'],
        'drunkelephant': ['Drunk Elephant'],
        'juicebeauty': ['Juice Beauty'],
        'supergoop': ['Supergoop!', 'Supergoop'],
        'beekman1802': ['Beekman 1802'],
        'beautyforreall': ['Beauty For Real'],
        'bioelements': ['Bioelements'],
        'cuveebeauty': ['Cuvée Beauty'],
        'earthlybody': ['Earthly Body'],
        'skinfix': ['SkinFix'],
        'drbrandt': ['Dr. Brandt'],
        
        # Health & Wellness
        'irwinnaturals': ['Irwin Naturals'],
        'probulin': ['Probulin'],
        'ridgecrestherbals': ['Ridgecrest Herbals'],
        'bioray': ['Bioray'],
        'biosil': ['BioSil'],
        'cellfood': ['Cellfood', 'Cell Food'],
        'brainmd': ['BrainMD', 'Brain MD'],
        'naturesplus': ['NaturesPlus', 'Natures Plus'],
        'solgar': ['Solgar'],
        'mastersupplements': ['Master Supplements'],
        'beastsportsnutrition': ['Beast Sports Nutrition'],
        'tevita': ['TeVita'],
        'bodyvigor': ['Body Vigor'],
        
        # Fashion & Accessories
        'isseymiyake': ['Issey Miyake'],
        'wolf1834': ['Wolf 1834'],
        'nestneyork': ['NEST New York', 'Nest New York'],
        'bruntworkwear': ['Brunt Workwear'],
        
        # Baby & Kids
        'babyzen': ['BABYZEN AS', 'BabyZen'],
        'stokke': ['Stokke'],
        'strider': ['Strider'],
        
        # Home & Kitchen
        'lafco': ['LAFCO'],
        'messermeister': ['Messermeister'],
        'kusmitea': ['Kusmi Tea'],
        'amerelle': ['AMERELLE'],
        'allamerican': ['All American 1930'],
        'arrowhomeproducts': ['Arrow Home Products'],
        'coverware': ['Coverware'],
        'ezpole': ['EZPOLE'],
        
        # Sports & Outdoors
        'oofos': ['OOFOS'],
        'sovnightguards': ['SoVa Night Guards'],
        'sisumouthguards': ['Sisu Mouthguards'],
        'triangle': ['Triangle'],
        'finaflex': ['FinaFlex'],
        'zak': ['Zak'],
        
        # Other brands
        'kneipp': ['Kneipp'],
        'shiseido': ['Shiseido'],
        'tenpoint': ['Ten Point'],
        'nah': ['NAH'],
        'dphhue': ['DPHue', 'DPH Hue'],
        'ikous': ['iKous'],
        'nelson': ['Nelson'],
        'petagus': ['Petag'],
        'bestbrands': ['Best Brands'],
        'elac': ['Elac'],
        
        # Test/Sandbox instances (no brands)
        'test': [],
        'sandbox': [],
        'defender': [],
        'desertfox': [],
        'typhoon': [],
        'dirtylabs': [],
        'emfharmony': [],
        'panera': []
    }
    
    # Find matching key in mappings
    for key, brands in mappings.items():
        if key in cleaned:
            return brands
    
    return []


def main():
    client = SupabaseManager.get_client(use_service_role=True)
    
    print("=" * 60)
    print("Instance Brand Mapping Update Script")
    print("=" * 60)
    
    # Get all instances
    instances = client.table('amc_instances').select('id, instance_name').execute()
    print(f"\n✓ Found {len(instances.data)} instances")
    
    # Get all unique brands from campaigns (handle >1000 limit)
    count_result = client.table('campaigns').select('*', count='exact').limit(1).execute()
    total_campaigns = count_result.count if hasattr(count_result, 'count') else 0
    
    available_brands = set()
    batch_size = 1000
    offset = 0
    
    while offset < total_campaigns:
        result = client.table('campaigns').select('brand').range(offset, offset + batch_size - 1).execute()
        for c in result.data:
            if c.get('brand'):
                available_brands.add(c['brand'])
        offset += batch_size
    
    print(f"✓ Found {len(available_brands)} unique brands in campaigns")
    
    # Get existing mappings
    existing = client.table('instance_brands').select('instance_id, brand_tag').execute()
    existing_mappings = {}
    for e in existing.data:
        if e['instance_id'] not in existing_mappings:
            existing_mappings[e['instance_id']] = []
        existing_mappings[e['instance_id']].append(e['brand_tag'])
    
    print(f"✓ Found {len(existing_mappings)} instances with existing brand mappings")
    
    # Process each instance
    new_mappings = []
    updated_count = 0
    
    print("\n" + "=" * 60)
    print("Processing instances...")
    print("=" * 60)
    
    for instance in instances.data:
        instance_id = instance['id']
        instance_name = instance['instance_name']
        
        # Get suggested brands
        suggested_brands = get_brand_suggestions(instance_name)
        
        # Filter to only brands that exist in campaigns
        valid_brands = []
        for brand in suggested_brands:
            # Check exact match first
            if brand in available_brands:
                valid_brands.append(brand)
            else:
                # Check case-insensitive match
                for avail_brand in available_brands:
                    if brand.lower() == avail_brand.lower():
                        valid_brands.append(avail_brand)
                        break
        
        # Remove duplicates while preserving order
        valid_brands = list(dict.fromkeys(valid_brands))
        
        # Check existing mappings
        existing_brands = existing_mappings.get(instance_id, [])
        
        print(f"\n{instance_name}:")
        print(f"  Current brands: {existing_brands if existing_brands else 'None'}")
        print(f"  Valid brands found: {valid_brands if valid_brands else 'None'}")
        
        # Add missing brands
        for brand in valid_brands:
            if brand not in existing_brands:
                # Check campaigns count
                camp_result = client.table('campaigns').select('*', count='exact').eq('brand', brand).limit(1).execute()
                count = camp_result.count if hasattr(camp_result, 'count') else 0
                
                if count > 0:
                    # Get a system user or first admin user for the mapping
                    users = client.table('users').select('id').limit(1).execute()
                    system_user_id = users.data[0]['id'] if users.data else None
                    
                    if system_user_id:
                        new_mappings.append({
                            'instance_id': instance_id,
                            'brand_tag': brand,
                            'user_id': system_user_id,  # Use first user as system user
                        })
                    print(f"    → Will add: {brand} ({count} campaigns)")
                    updated_count += 1
    
    # Insert new mappings
    if new_mappings:
        print("\n" + "=" * 60)
        print(f"Adding {len(new_mappings)} new brand mappings...")
        print("=" * 60)
        
        # Insert in batches
        batch_size = 50
        for i in range(0, len(new_mappings), batch_size):
            batch = new_mappings[i:i + batch_size]
            result = client.table('instance_brands').insert(batch).execute()
            print(f"  ✓ Inserted batch {i//batch_size + 1}")
        
        print(f"\n✓ Successfully added {len(new_mappings)} brand mappings")
    else:
        print("\n✓ All instances already have appropriate brand mappings")
    
    # Final summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    # Get updated counts
    result = client.table('instance_brands').select('instance_id', count='exact').execute()
    total_mappings = result.count if hasattr(result, 'count') else 0
    
    # Count instances with mappings
    mapped = client.table('instance_brands').select('instance_id').execute()
    unique_mapped = len(set(m['instance_id'] for m in mapped.data))
    
    print(f"Total instances: {len(instances.data)}")
    print(f"Instances with brand mappings: {unique_mapped}")
    print(f"Total brand mappings: {total_mappings}")
    print(f"New mappings added: {len(new_mappings)}")
    
    # Show instances still without mappings
    all_mapped_ids = set(m['instance_id'] for m in mapped.data)
    unmapped = [inst for inst in instances.data if inst['id'] not in all_mapped_ids]
    
    if unmapped:
        print(f"\nInstances without brand mappings ({len(unmapped)}):")
        for inst in unmapped:
            print(f"  - {inst['instance_name']} (likely test/sandbox)")


if __name__ == "__main__":
    main()