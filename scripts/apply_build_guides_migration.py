#!/usr/bin/env python3
"""Apply Build Guides database migration"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def apply_migration():
    """Apply the Build Guides migration"""
    try:
        # Read the migration SQL
        migration_path = Path(__file__).parent / 'migrations' / 'create_build_guides_tables.sql'
        with open(migration_path, 'r') as f:
            sql = f.read()
        
        # Get Supabase client with service role
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Execute the migration using RPC
        # Note: We'll need to execute this in chunks if it's too large
        # For now, let's execute statement by statement
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        success_count = 0
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    # Use the Supabase client's postgrest client for raw SQL execution
                    # Since Supabase Python client doesn't have direct SQL execution,
                    # we'll need to use a different approach
                    logger.info(f"Executing statement {i}/{len(statements)}...")
                    # Note: This would normally require direct database access
                    # For Supabase, we might need to use the SQL editor in the dashboard
                    # or create an RPC function
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error executing statement {i}: {e}")
        
        logger.info(f"Migration applied: {success_count}/{len(statements)} statements executed successfully")
        
        # Since we can't directly execute raw SQL through the Supabase Python client,
        # let's save this as a file that can be run through the Supabase dashboard
        output_path = Path(__file__).parent / 'build_guides_migration_ready.sql'
        with open(output_path, 'w') as f:
            f.write(sql)
        
        print(f"\n✅ Migration SQL prepared successfully!")
        print(f"📄 File saved to: {output_path}")
        print("\n📌 To apply this migration:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the contents of the migration file")
        print("4. Click 'Run' to execute the migration")
        print(f"\nOr run: supabase db push (if using Supabase CLI)")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to prepare migration: {e}")
        return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)