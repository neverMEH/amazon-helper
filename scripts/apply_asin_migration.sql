-- Migration: Create ASIN Management Tables
-- Date: 2025-08-27
-- Description: Creates product_asins and asin_import_logs tables with indexes and triggers

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

-- Add performance indexes for product_asins
CREATE INDEX IF NOT EXISTS idx_asins_brand ON product_asins(brand) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_asins_marketplace ON product_asins(marketplace) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_asins_asin ON product_asins(asin);
CREATE INDEX IF NOT EXISTS idx_asins_parent ON product_asins(parent_asin) WHERE parent_asin IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_asins_search ON product_asins USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(asin, '')));
CREATE INDEX IF NOT EXISTS idx_asins_brand_marketplace ON product_asins(brand, marketplace) WHERE active = true;

-- Add indexes for asin_import_logs
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

-- Grant necessary permissions
GRANT ALL ON product_asins TO authenticated;
GRANT ALL ON asin_import_logs TO authenticated;