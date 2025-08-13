#!/usr/bin/env python3
"""Apply workflow versioning migration to Supabase database"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager

def apply_migration():
    """Apply the workflow versioning migration"""
    
    # Read the migration SQL
    migration_path = Path(__file__).parent.parent / 'database' / 'supabase' / 'migrations' / '10_workflow_versioning.sql'
    
    with open(migration_path, 'r') as f:
        sql = f.read()
    
    # Split into individual statements (Supabase doesn't support multiple statements in one call)
    statements = []
    current = []
    
    for line in sql.split('\n'):
        # Skip comments
        if line.strip().startswith('--'):
            continue
            
        current.append(line)
        
        # Check if this completes a statement
        if line.strip().endswith(';'):
            statement = '\n'.join(current).strip()
            if statement:
                statements.append(statement)
            current = []
    
    # Apply each statement
    client = SupabaseManager.get_client(use_service_role=True)
    
    print(f"Applying {len(statements)} migration statements...")
    
    for i, statement in enumerate(statements, 1):
        try:
            # Skip empty statements
            if not statement.strip() or statement.strip() == ';':
                continue
                
            print(f"\nStatement {i}/{len(statements)}:")
            print(f"  {statement[:100]}..." if len(statement) > 100 else f"  {statement}")
            
            # Execute the statement using RPC since direct SQL execution isn't available
            # We'll need to use the Supabase SQL editor or create tables via the API
            
            # For now, let's try using the client's raw postgrest client
            # This won't work for DDL, but let's check what we can do
            
            if statement.strip().upper().startswith('CREATE TABLE'):
                print("  ⚠️  CREATE TABLE statements need to be run via Supabase dashboard")
            elif statement.strip().upper().startswith('ALTER TABLE'):
                print("  ⚠️  ALTER TABLE statements need to be run via Supabase dashboard")
            elif statement.strip().upper().startswith('CREATE INDEX'):
                print("  ⚠️  CREATE INDEX statements need to be run via Supabase dashboard")
            elif statement.strip().upper().startswith('CREATE POLICY'):
                print("  ⚠️  CREATE POLICY statements need to be run via Supabase dashboard")
            elif statement.strip().upper().startswith('CREATE OR REPLACE'):
                print("  ⚠️  CREATE FUNCTION/VIEW statements need to be run via Supabase dashboard")
            elif statement.strip().upper().startswith('CREATE TRIGGER'):
                print("  ⚠️  CREATE TRIGGER statements need to be run via Supabase dashboard")
            elif statement.strip().upper().startswith('INSERT INTO'):
                print("  ℹ️  INSERT statements can be run after tables are created")
            else:
                print(f"  ⚠️  Unknown statement type")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("IMPORTANT: DDL statements (CREATE TABLE, ALTER TABLE, etc.) cannot be")
    print("executed via the Supabase client library. Please run the migration")
    print("directly in the Supabase SQL editor:")
    print()
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Create a new query")
    print("4. Copy the contents of database/supabase/migrations/10_workflow_versioning.sql")
    print("5. Run the query")
    print("="*60)
    
    # Output the migration for easy copying
    print("\n\nMigration SQL:")
    print("-" * 60)
    print(sql)

if __name__ == "__main__":
    apply_migration()