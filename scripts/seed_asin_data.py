#!/usr/bin/env python
"""
Seed ASIN data from CSV file into the database
"""
import os
import sys
import csv
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client():
    """Create Supabase client with service role key"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        raise ValueError("Missing Supabase credentials in environment variables")
    
    return create_client(url, key)

def parse_decimal(value):
    """Parse a decimal value from CSV"""
    if not value or value.strip() == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def parse_int(value):
    """Parse an integer value from CSV"""
    if not value or value.strip() == '':
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None

def parse_bool(value):
    """Parse a boolean value from CSV"""
    if not value:
        return True
    return str(value).strip() == '1' or str(value).lower() == 'true'

def seed_asin_data(csv_file_path: str = "ASIN Recom.txt", limit: int = 100):
    """
    Seed ASIN data from CSV file
    
    Args:
        csv_file_path: Path to the CSV file
        limit: Maximum number of records to import (for testing)
    """
    client = get_supabase_client()
    
    # Check if table exists first
    try:
        test_result = client.table('product_asins').select('id').limit(1).execute()
    except Exception as e:
        if 'relation' in str(e) and 'does not exist' in str(e):
            print("❌ Error: product_asins table does not exist!")
            print("Please apply the migration first:")
            print("  1. Go to Supabase Dashboard > SQL Editor")
            print("  2. Copy contents from: scripts/migrations/001_create_asin_tables.sql")
            print("  3. Run the SQL")
            return False
    
    csv_path = Path(csv_file_path)
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_file_path}")
        return False
    
    print(f"📂 Reading ASIN data from: {csv_file_path}")
    
    # Create import log
    import_log = client.table('asin_import_logs').insert({
        'file_name': csv_file_path,
        'import_status': 'processing',
        'total_rows': 0,
        'successful_imports': 0,
        'failed_imports': 0,
        'duplicate_skipped': 0
    }).execute()
    
    if not import_log.data:
        print("❌ Failed to create import log")
        return False
        
    import_id = import_log.data[0]['id']
    
    successful = 0
    failed = 0
    duplicates = 0
    errors = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as file:
            # Use tab delimiter as the file appears to be tab-separated
            reader = csv.DictReader(file, delimiter='\t')
            
            batch = []
            batch_size = 50
            
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                
                # Map CSV columns to database fields
                asin_data = {
                    'asin': row.get('ASIN', '').strip(),
                    'title': row.get('TITLE', '').strip() or row.get('DESIRED_TITLE', '').strip(),
                    'brand': row.get('BRAND', '').strip(),
                    'active': parse_bool(row.get('ACTIVE', '1')),
                    'description': row.get('DESCRIPTION', '').strip(),
                    'department': row.get('DEPARTMENT', '').strip(),
                    'manufacturer': row.get('MANUFACTURER', '').strip(),
                    'product_group': row.get('PRODUCT_GROUP', '').strip(),
                    'product_type': row.get('PRODUCT_TYPE', '').strip(),
                    'color': row.get('COLOR', '').strip(),
                    'size': row.get('SIZE', '').strip(),
                    'model': row.get('MODEL', '').strip(),
                    'item_length': parse_decimal(row.get('ITEM_LENGTH')),
                    'item_height': parse_decimal(row.get('ITEM_HEIGHT')),
                    'item_width': parse_decimal(row.get('ITEM_WIDTH')),
                    'item_weight': parse_decimal(row.get('ITEM_WEIGHT')),
                    'item_unit_dimension': row.get('ITEM_UNIT_DIMENSION', '').strip(),
                    'item_unit_weight': row.get('ITEM_UNIT_WEIGHT', '').strip(),
                    'parent_asin': row.get('PARENT_ASIN', '').strip(),
                    'variant_type': row.get('VARIANT_TYPE', '').strip(),
                    'last_known_price': parse_decimal(row.get('LAST_KNOWN_PRICE')) or parse_decimal(row.get('MSRP')),
                    'monthly_estimated_sales': parse_decimal(row.get('MONTHLY_ESTIMATED_SALES')),
                    'monthly_estimated_units': parse_int(row.get('MONTHLY_ESTIMATED_UNITS')) or parse_int(row.get('ESTIMATED_UNITS_SOLD_LAST_MONTH')),
                    'marketplace': row.get('MARKETPLACE', 'ATVPDKIKX0DER').strip(),
                    'last_imported_at': datetime.now().isoformat()
                }
                
                # Skip if no ASIN
                if not asin_data['asin']:
                    continue
                
                # Remove None values and empty strings
                asin_data = {k: v for k, v in asin_data.items() if v not in (None, '')}
                
                batch.append(asin_data)
                
                # Insert batch when it reaches batch_size
                if len(batch) >= batch_size:
                    try:
                        result = client.table('product_asins').upsert(
                            batch,
                            on_conflict='asin,marketplace'
                        ).execute()
                        
                        if result.data:
                            successful += len(result.data)
                        
                        batch = []
                        
                        if (i + 1) % 100 == 0:
                            print(f"✓ Processed {i + 1} records...")
                            
                    except Exception as e:
                        failed += len(batch)
                        errors.append(f"Batch insert error at row {i}: {str(e)[:100]}")
                        batch = []
            
            # Insert remaining batch
            if batch:
                try:
                    result = client.table('product_asins').upsert(
                        batch,
                        on_conflict='asin,marketplace'
                    ).execute()
                    
                    if result.data:
                        successful += len(result.data)
                        
                except Exception as e:
                    failed += len(batch)
                    errors.append(f"Final batch error: {str(e)[:100]}")
        
        # Update import log
        client.table('asin_import_logs').update({
            'import_status': 'completed',
            'total_rows': successful + failed,
            'successful_imports': successful,
            'failed_imports': failed,
            'duplicate_skipped': duplicates,
            'error_details': {'errors': errors[:10]} if errors else None,
            'completed_at': datetime.now().isoformat()
        }).eq('id', import_id).execute()
        
        print(f"\n✅ Import completed!")
        print(f"   Successfully imported: {successful} ASINs")
        print(f"   Failed: {failed}")
        print(f"   Duplicates updated: {duplicates}")
        
        if errors:
            print(f"\n⚠ First few errors:")
            for error in errors[:3]:
                print(f"   - {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during import: {str(e)}")
        
        # Update import log with failure
        client.table('asin_import_logs').update({
            'import_status': 'failed',
            'error_details': {'error': str(e)},
            'completed_at': datetime.now().isoformat()
        }).eq('id', import_id).execute()
        
        return False

def verify_seeded_data():
    """Verify that data was seeded correctly"""
    client = get_supabase_client()
    
    try:
        # Count total ASINs
        count_result = client.table('product_asins').select('id', count='exact').execute()
        total_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
        
        print(f"\n📊 Database Statistics:")
        print(f"   Total ASINs: {total_count}")
        
        # Get unique brands
        brands_result = client.table('product_asins')\
            .select('brand')\
            .neq('brand', '')\
            .execute()
        
        unique_brands = set(row['brand'] for row in brands_result.data if row['brand'])
        print(f"   Unique brands: {len(unique_brands)}")
        
        # Sample some brands
        if unique_brands:
            sample_brands = list(unique_brands)[:5]
            print(f"   Sample brands: {', '.join(sample_brands)}")
        
        # Get sample ASINs
        sample_result = client.table('product_asins')\
            .select('asin, title, brand, last_known_price')\
            .limit(5)\
            .execute()
        
        if sample_result.data:
            print(f"\n📝 Sample ASINs:")
            for item in sample_result.data:
                price = f"${item['last_known_price']:.2f}" if item.get('last_known_price') else 'N/A'
                print(f"   - {item['asin']}: {item.get('title', 'No title')[:50]} ({item.get('brand', 'No brand')}) - {price}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying data: {str(e)}")
        return False

if __name__ == "__main__":
    # Check if custom limit is provided
    limit = 100
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print("Invalid limit provided, using default of 100")
    
    print(f"🚀 Starting ASIN data seed (limit: {limit} records)...")
    
    success = seed_asin_data(limit=limit)
    
    if success:
        verify_seeded_data()
        print("\n✅ Seeding completed successfully!")
    else:
        print("\n❌ Seeding failed. Please check the errors above.")
        sys.exit(1)