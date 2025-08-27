# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-27-asin-management-page/spec.md

## Schema Design

### Primary Table: product_asins

```sql
CREATE TABLE product_asins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asin VARCHAR(20) NOT NULL,
    title TEXT,
    brand VARCHAR(255),
    marketplace VARCHAR(20) DEFAULT 'ATVPDKIKX0DER',
    
    -- Core metadata fields from ASIN Recom.txt
    active BOOLEAN DEFAULT true,
    description TEXT,
    department VARCHAR(255),
    manufacturer VARCHAR(255),
    product_group VARCHAR(255),
    product_type VARCHAR(255),
    color VARCHAR(100),
    size VARCHAR(100),
    model VARCHAR(255),
    
    -- Dimensional data
    item_length DECIMAL(10,2),
    item_height DECIMAL(10,2),
    item_width DECIMAL(10,2),
    item_weight DECIMAL(10,2),
    item_unit_dimension VARCHAR(20),
    item_unit_weight VARCHAR(20),
    
    -- Parent/variant relationships
    parent_asin VARCHAR(20),
    variant_type VARCHAR(100),
    
    -- Sales and pricing data
    last_known_price DECIMAL(10,2),
    monthly_estimated_sales DECIMAL(12,2),
    monthly_estimated_units INTEGER,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_imported_at TIMESTAMPTZ,
    
    -- Unique constraint on ASIN + marketplace combination
    CONSTRAINT unique_asin_marketplace UNIQUE(asin, marketplace)
);

-- Performance indexes
CREATE INDEX idx_asins_brand ON product_asins(brand) WHERE active = true;
CREATE INDEX idx_asins_marketplace ON product_asins(marketplace) WHERE active = true;
CREATE INDEX idx_asins_asin ON product_asins(asin);
CREATE INDEX idx_asins_parent ON product_asins(parent_asin) WHERE parent_asin IS NOT NULL;
CREATE INDEX idx_asins_search ON product_asins USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(asin, '')));
CREATE INDEX idx_asins_brand_marketplace ON product_asins(brand, marketplace) WHERE active = true;
```

### Import History Table: asin_import_logs

```sql
CREATE TABLE asin_import_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    file_name VARCHAR(255),
    total_rows INTEGER,
    successful_imports INTEGER,
    failed_imports INTEGER,
    duplicate_skipped INTEGER,
    import_status VARCHAR(50), -- 'processing', 'completed', 'failed'
    error_details JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Audit trail
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_import_logs_user ON asin_import_logs(user_id);
CREATE INDEX idx_import_logs_status ON asin_import_logs(import_status);
```

## Migration Implementation

```sql
-- Migration: Add product_asins table
BEGIN;

-- Create main ASIN table
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

-- Create import logs table
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

-- Add all indexes
CREATE INDEX IF NOT EXISTS idx_asins_brand ON product_asins(brand) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_asins_marketplace ON product_asins(marketplace) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_asins_asin ON product_asins(asin);
CREATE INDEX IF NOT EXISTS idx_asins_parent ON product_asins(parent_asin) WHERE parent_asin IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_asins_search ON product_asins USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(asin, '')));
CREATE INDEX IF NOT EXISTS idx_asins_brand_marketplace ON product_asins(brand, marketplace) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_import_logs_user ON asin_import_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_import_logs_status ON asin_import_logs(import_status);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_product_asins_updated_at 
    BEFORE UPDATE ON product_asins 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
```

## Data Import Strategy

### Bulk Insert with Conflict Resolution

```sql
-- Example bulk upsert for CSV import
INSERT INTO product_asins (
    asin, title, brand, marketplace, active, 
    description, manufacturer, product_group,
    item_length, item_height, item_width, item_weight,
    last_known_price, monthly_estimated_units,
    last_imported_at
) VALUES 
    ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW())
ON CONFLICT (asin, marketplace) 
DO UPDATE SET
    title = EXCLUDED.title,
    brand = EXCLUDED.brand,
    active = EXCLUDED.active,
    description = EXCLUDED.description,
    manufacturer = EXCLUDED.manufacturer,
    product_group = EXCLUDED.product_group,
    item_length = EXCLUDED.item_length,
    item_height = EXCLUDED.item_height,
    item_width = EXCLUDED.item_width,
    item_weight = EXCLUDED.item_weight,
    last_known_price = EXCLUDED.last_known_price,
    monthly_estimated_units = EXCLUDED.monthly_estimated_units,
    updated_at = NOW(),
    last_imported_at = NOW();
```

## Query Patterns

### Get ASINs with Filtering

```sql
-- Paginated query with filters
SELECT id, asin, title, brand, marketplace, 
       last_known_price, monthly_estimated_units,
       updated_at
FROM product_asins
WHERE active = true
  AND ($1::text IS NULL OR brand = $1)
  AND ($2::text IS NULL OR marketplace = $2)
  AND ($3::text IS NULL OR 
       asin ILIKE '%' || $3 || '%' OR 
       title ILIKE '%' || $3 || '%')
ORDER BY brand, asin
LIMIT $4 OFFSET $5;
```

### Get Unique Brands

```sql
-- For brand dropdown
SELECT DISTINCT brand 
FROM product_asins 
WHERE active = true 
  AND brand IS NOT NULL
ORDER BY brand;
```

## Rationale

1. **Unique Constraint**: ASIN + marketplace combination ensures no duplicates while allowing same ASIN across different marketplaces
2. **Partial Indexes**: WHERE clauses on indexes optimize for active records, reducing index size
3. **GIN Index**: Full-text search on title and ASIN for fast text searching
4. **JSONB for Errors**: Flexible error storage in import logs for varying error structures
5. **Separate Import Logs**: Track import history without cluttering main table
6. **Updated Trigger**: Automatic timestamp updates maintain data freshness tracking