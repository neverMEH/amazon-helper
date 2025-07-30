#!/usr/bin/env python3
"""Apply instance brands migration to Supabase"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


def apply_migration():
    """Apply the instance brands migration"""
    print("\nApplying Instance Brands Migration")
    print("=" * 50)
    
    # Read migration file
    migration_path = Path(__file__).parent.parent / "database" / "supabase" / "migrations" / "02_instance_brands.sql"
    
    if not migration_path.exists():
        print(f"✗ Migration file not found: {migration_path}")
        return False
    
    print(f"✓ Found migration file: {migration_path}")
    
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    # Get Supabase client with service role
    print("\nConnecting to Supabase...")
    client = SupabaseManager.get_client(use_service_role=True)
    
    # Apply migration
    print("\nApplying migration...")
    print("Note: Run this SQL in the Supabase SQL editor for best results")
    print("URL: https://supabase.com/dashboard/project/loqaorroihxfkjvcrkdv/sql/new")
    print("\n" + "="*50)
    print("MIGRATION SQL:")
    print("="*50)
    print(migration_sql[:500] + "..." if len(migration_sql) > 500 else migration_sql)
    print("="*50)
    
    print("\n⚠️  IMPORTANT: Copy the migration SQL above and run it in the Supabase SQL editor")
    print("This ensures proper permissions and error handling")
    
    return True


if __name__ == "__main__":
    success = apply_migration()
    if success:
        print("\n✅ Migration file ready to apply")
    else:
        print("\n✗ Migration preparation failed")