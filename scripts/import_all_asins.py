#!/usr/bin/env python
"""
Import all ASINs from CSV file with optimized batch processing
"""
import os
import sys
import csv
from pathlib import Path
from datetime import datetime
from decimal import Decimal
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

def import_all_asins():
    """Import all ASINs from CSV file"""
    client = get_supabase_client()
    csv_path = Path("ASIN Recom.txt")
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: ASIN Recom.txt")
        return False
    
    print(f"📂 Starting full ASIN import from: ASIN Recom.txt")
    print(f"   File has ~116,000 records")
    
    # Check current count
    try:
        count_result = client.table('product_asins').select('id', count='exact').limit(1).execute()
        existing_count = count_result.count if hasattr(count_result, 'count') else 0
        print(f"   Currently in database: {existing_count:,} records")
    except:
        existing_count = 0
    
    # Create import log
    import_log = client.table('asin_import_logs').insert({
        'file_name': 'ASIN Recom.txt - Full Import',
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
    total_processed = 0
    errors = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as file:
            # Use tab delimiter
            reader = csv.DictReader(file, delimiter='\t')
            
            batch = []
            batch_size = 500  # Larger batch for efficiency
            
            for i, row in enumerate(reader):
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
                total_processed += 1
                
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
                        
                        if total_processed % 5000 == 0:
                            print(f"✓ Processed {total_processed:,} records... ({successful:,} imported)")
                            
                    except Exception as e:
                        failed += len(batch)
                        if len(errors) < 10:
                            errors.append(f"Batch error at row {i}: {str(e)[:100]}")
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
            'total_rows': total_processed,
            'successful_imports': successful,
            'failed_imports': failed,
            'duplicate_skipped': total_processed - successful - failed,
            'error_details': {'errors': errors} if errors else None,
            'completed_at': datetime.now().isoformat()
        }).eq('id', import_id).execute()
        
        # Get final count
        final_count_result = client.table('product_asins').select('id', count='exact').limit(1).execute()
        final_count = final_count_result.count if hasattr(final_count_result, 'count') else 0
        
        print(f"\n✅ Import completed!")
        print(f"   Total processed: {total_processed:,}")
        print(f"   Successfully imported/updated: {successful:,}")
        print(f"   Failed: {failed:,}")
        print(f"   Database now contains: {final_count:,} ASINs")
        print(f"   Net increase: {final_count - existing_count:,} records")
        
        if errors:
            print(f"\n⚠ Sample errors:")
            for error in errors[:3]:
                print(f"   - {error}")
        
        # Show some statistics
        print("\n📊 Quick Statistics:")
        
        # Get brand count
        brands_result = client.table('product_asins')\
            .select('brand')\
            .neq('brand', '')\
            .limit(1000)\
            .execute()
        
        unique_brands = set(row['brand'] for row in brands_result.data if row.get('brand'))
        print(f"   Sample unique brands: {len(unique_brands)}")
        
        # Get sample ASINs
        sample_result = client.table('product_asins')\
            .select('asin, title, brand, last_known_price')\
            .limit(3)\
            .execute()
        
        if sample_result.data:
            print(f"\n📝 Sample ASINs:")
            for item in sample_result.data:
                price = f"${item['last_known_price']:.2f}" if item.get('last_known_price') else 'N/A'
                title = (item.get('title', 'No title')[:40] + '...') if item.get('title') and len(item.get('title')) > 40 else item.get('title', 'No title')
                print(f"   - {item['asin']}: {title} ({item.get('brand', 'No brand')}) - {price}")
        
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

if __name__ == "__main__":
    print("🚀 Starting full ASIN import...")
    print("⏱ This may take a few minutes for 116,000 records...")
    
    success = import_all_asins()
    
    if success:
        print("\n✅ Full import completed successfully!")
    else:
        print("\n❌ Import failed. Please check the errors above.")
        sys.exit(1)