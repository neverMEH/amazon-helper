#!/usr/bin/env python3
"""Apply instance parameter mapping migration to Supabase"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


def apply_migration():
    """Apply the instance parameter mapping migration"""
    print("\nApplying Instance Parameter Mapping Migration")
    print("=" * 60)

    # Read migration file
    migration_path = Path(__file__).parent.parent / "database" / "supabase" / "migrations" / "04_instance_parameter_mapping.sql"

    if not migration_path.exists():
        print(f"✗ Migration file not found: {migration_path}")
        return False

    print(f"✓ Found migration file: {migration_path}")

    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    # Get Supabase client with service role
    print("\nConnecting to Supabase...")
    client = SupabaseManager.get_client(use_service_role=True)

    # Display migration information
    print("\nMigration Summary:")
    print("-" * 60)
    print("Creates:")
    print("  • instance_brand_asins table (junction for instance-brand-ASIN)")
    print("  • instance_brand_campaigns table (junction for instance-brand-campaign)")
    print("  • Index on campaign_mappings.brand_tag for performance")
    print("\nIncludes:")
    print("  • Foreign key constraints")
    print("  • Performance indexes")
    print("  • Row Level Security (RLS) policies")
    print("  • Auto-update triggers for updated_at")
    print("-" * 60)

    # Apply migration
    print("\n⚠️  IMPORTANT: Run this SQL in the Supabase SQL Editor")
    print("URL: https://supabase.com/dashboard/project/loqaorroihxfkjvcrkdv/sql/new")
    print("\n" + "="*60)
    print("MIGRATION SQL:")
    print("="*60)
    print(migration_sql)
    print("="*60)

    print("\n📋 Copy the SQL above and run it in Supabase SQL Editor")
    print("This ensures proper permissions and transaction handling")

    # Save to temporary file for easy copying
    temp_file = Path(__file__).parent / "temp_migration_04.sql"
    with open(temp_file, 'w') as f:
        f.write(migration_sql)
    print(f"\n💾 SQL also saved to: {temp_file}")

    return True


if __name__ == "__main__":
    success = apply_migration()
    if success:
        print("\n✅ Migration ready to apply in Supabase SQL Editor")
        print("\nNext Steps:")
        print("1. Open Supabase SQL Editor")
        print("2. Copy/paste the migration SQL")
        print("3. Run the query")
        print("4. Verify tables are created successfully")
    else:
        print("\n✗ Migration preparation failed")
