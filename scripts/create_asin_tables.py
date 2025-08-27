#!/usr/bin/env python
"""
Migration script to create ASIN management tables
"""
import os
import sys
from pathlib import Path

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

def create_asin_tables():
    """Create product_asins and asin_import_logs tables"""
    
    client = get_supabase_client()
    
    # SQL migration script
    migration_sql = """
    -- Create product_asins table
    CREATE TABLE IF NOT EXISTS product_asins (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        asin VARCHAR(20) NOT NULL,
        title TEXT,
        brand VARCHAR(255),
        marketplace VARCHAR(20) DEFAULT 'ATVPDKIKX0DER',
        active BOOLEAN DEFAULT true,
        description TEXT,
        department VARCHAR(255),
        manufacturer VARCHAR(255),
        product_group VARCHAR(255),
        product_type VARCHAR(255),
        color VARCHAR(100),
        size VARCHAR(100),
        model VARCHAR(255),
        item_length DECIMAL(10,2),
        item_height DECIMAL(10,2),
        item_width DECIMAL(10,2),
        item_weight DECIMAL(10,2),
        item_unit_dimension VARCHAR(20),
        item_unit_weight VARCHAR(20),
        parent_asin VARCHAR(20),
        variant_type VARCHAR(100),
        last_known_price DECIMAL(10,2),
        monthly_estimated_sales DECIMAL(12,2),
        monthly_estimated_units INTEGER,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        last_imported_at TIMESTAMPTZ,
        CONSTRAINT unique_asin_marketplace UNIQUE(asin, marketplace)
    );

    -- Create asin_import_logs table
    CREATE TABLE IF NOT EXISTS asin_import_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id),
        file_name VARCHAR(255),
        total_rows INTEGER,
        successful_imports INTEGER,
        failed_imports INTEGER,
        duplicate_skipped INTEGER,
        import_status VARCHAR(50),
        error_details JSONB,
        started_at TIMESTAMPTZ DEFAULT NOW(),
        completed_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Add performance indexes
    CREATE INDEX IF NOT EXISTS idx_asins_brand ON product_asins(brand) WHERE active = true;
    CREATE INDEX IF NOT EXISTS idx_asins_marketplace ON product_asins(marketplace) WHERE active = true;
    CREATE INDEX IF NOT EXISTS idx_asins_asin ON product_asins(asin);
    CREATE INDEX IF NOT EXISTS idx_asins_parent ON product_asins(parent_asin) WHERE parent_asin IS NOT NULL;
    CREATE INDEX IF NOT EXISTS idx_asins_search ON product_asins USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(asin, '')));
    CREATE INDEX IF NOT EXISTS idx_asins_brand_marketplace ON product_asins(brand, marketplace) WHERE active = true;
    CREATE INDEX IF NOT EXISTS idx_import_logs_user ON asin_import_logs(user_id);
    CREATE INDEX IF NOT EXISTS idx_import_logs_status ON asin_import_logs(import_status);

    -- Create update trigger function
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    -- Add trigger to product_asins table
    DROP TRIGGER IF EXISTS update_product_asins_updated_at ON product_asins;
    CREATE TRIGGER update_product_asins_updated_at 
        BEFORE UPDATE ON product_asins 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    """
    
    print("Creating ASIN management tables...")
    
    # Execute migration using Supabase's SQL execution
    try:
        # We need to use the Supabase Management API or direct database connection
        # Since we're using Supabase client, we'll create a migration record
        
        # First, let's check if tables already exist
        try:
            existing_check = client.table('product_asins').select('id').limit(1).execute()
            print("✓ product_asins table already exists")
            return True
        except:
            pass
        
        # If we get here, table doesn't exist - we need to apply migration
        # Save migration SQL to file for manual execution
        migration_file = Path(__file__).parent / "migrations" / "001_create_asin_tables.sql"
        migration_file.parent.mkdir(exist_ok=True)
        
        with open(migration_file, 'w') as f:
            f.write(migration_sql)
        
        print(f"Migration SQL saved to: {migration_file}")
        print("\nTo apply this migration, you have two options:")
        print("1. Run it directly in Supabase SQL Editor (Dashboard > SQL Editor)")
        print("2. Use Supabase CLI: supabase db push")
        print("\nOr we can apply it using the Supabase Management API...")
        
        # Try using Supabase Management API
        from scripts.apply_migration_via_supabase import apply_migration
        result = apply_migration(migration_sql, "001_create_asin_tables")
        
        if result:
            print("✓ Migration applied successfully!")
            return True
        else:
            print("⚠ Please apply the migration manually using the SQL above")
            return False
            
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        print("\nPlease apply the migration manually in Supabase Dashboard")
        return False

if __name__ == "__main__":
    success = create_asin_tables()
    sys.exit(0 if success else 1)