#!/usr/bin/env python3
"""Rollback instance templates migration from Supabase"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


def rollback_migration():
    """Rollback the instance templates migration"""
    print("\nRollback Instance Templates Migration")
    print("=" * 60)
    print("⚠️  WARNING: This will DELETE the instance_templates table and all data!")
    print("=" * 60)

    # Rollback SQL
    rollback_sql = """
BEGIN;

-- Drop instance_templates table (CASCADE will remove dependent objects)
DROP TABLE IF EXISTS instance_templates CASCADE;

COMMIT;
"""

    # Get Supabase client with service role
    print("\nConnecting to Supabase...")
    client = SupabaseManager.get_client(use_service_role=True)

    # Display rollback information
    print("\nRollback Summary:")
    print("-" * 60)
    print("Will remove:")
    print("  • instance_templates table")
    print("  • All RLS policies on instance_templates")
    print("  • All indexes on instance_templates")
    print("  • All triggers on instance_templates")
    print("  • ALL DATA in instance_templates (irreversible!)")
    print("-" * 60)

    # Display rollback SQL
    print("\n⚠️  IMPORTANT: Run this SQL in the Supabase SQL Editor")
    print("URL: https://supabase.com/dashboard/project/loqaorroihxfkjvcrkdv/sql/new")
    print("\n" + "="*60)
    print("ROLLBACK SQL:")
    print("="*60)
    print(rollback_sql)
    print("="*60)

    print("\n📋 Copy the SQL above and run it in Supabase SQL Editor")
    print("⚠️  WARNING: This action is IRREVERSIBLE!")
    print("All instance template data will be permanently deleted.")

    # Save to temporary file for easy copying
    temp_file = Path(__file__).parent / "temp_rollback_05.sql"
    with open(temp_file, 'w') as f:
        f.write(rollback_sql)
    print(f"\n💾 SQL also saved to: {temp_file}")

    return True


if __name__ == "__main__":
    print("\n" + "!"*60)
    print("!  WARNING: THIS WILL DELETE THE INSTANCE_TEMPLATES TABLE  !")
    print("!"*60)

    response = input("\nAre you sure you want to proceed with rollback? (yes/no): ")

    if response.lower() == 'yes':
        success = rollback_migration()
        if success:
            print("\n✅ Rollback SQL ready to apply in Supabase SQL Editor")
            print("\nNext Steps:")
            print("1. Open Supabase SQL Editor")
            print("2. Copy/paste the rollback SQL")
            print("3. Run the query")
            print("4. Verify table is removed successfully")
        else:
            print("\n✗ Rollback preparation failed")
    else:
        print("\n✗ Rollback cancelled by user")
