#!/usr/bin/env python3
"""Apply batch execution migration to Supabase database."""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def apply_batch_migration():
    """Apply the batch execution migration."""
    try:
        # Get Supabase client with service role
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Check if batch_executions table already exists
        check_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'batch_executions'
        );
        """
        
        result = client.rpc('execute_sql', {'query': check_query}).execute()
        
        if result.data and result.data[0]['exists']:
            logger.info("batch_executions table already exists, skipping migration")
            return True
        
        logger.info("Applying batch execution migration...")
        
        # Read migration file
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'database/supabase/migrations/11_batch_executions.sql'
        )
        
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        # Note: We'll need to execute this through Supabase dashboard or CLI
        # as the Python client doesn't support direct SQL execution
        
        print("Migration SQL loaded. Please execute the following migration through Supabase dashboard:")
        print("=" * 80)
        print(migration_sql[:500] + "...")
        print("=" * 80)
        print("\nFull migration saved to: /tmp/batch_migration.sql")
        
        with open('/tmp/batch_migration.sql', 'w') as f:
            f.write(migration_sql)
        
        return True
        
    except Exception as e:
        logger.error(f"Error applying migration: {e}")
        return False

if __name__ == "__main__":
    success = apply_batch_migration()
    sys.exit(0 if success else 1)