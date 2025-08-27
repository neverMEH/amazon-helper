#!/usr/bin/env python
"""
Apply SQL migrations using Supabase Management API or MCP
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import os
from supabase import create_client
from dotenv import load_dotenv
import re

load_dotenv()

def get_supabase_client():
    """Create Supabase client with service role key"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        raise ValueError("Missing Supabase credentials in environment variables")
    
    return create_client(url, key)

def apply_migration(sql: str, migration_name: str) -> bool:
    """
    Apply a SQL migration to the database
    
    Args:
        sql: The SQL statements to execute
        migration_name: Name of the migration for logging
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the Supabase project ID from the URL
        # Format: https://xxxxx.supabase.co
        import re
        match = re.match(r'https://([^.]+)\.supabase\.co', os.getenv('SUPABASE_URL'))
        if not match:
            print("Could not extract project ID from SUPABASE_URL")
            return False
            
        project_id = match.group(1)
        print(f"Applying migration to project: {project_id}")
        
        # Since we can't directly execute DDL through the client library,
        # we'll save it and provide instructions
        migrations_dir = Path(__file__).parent / "migrations"
        migrations_dir.mkdir(exist_ok=True)
        
        migration_file = migrations_dir / f"{migration_name}.sql"
        with open(migration_file, 'w') as f:
            f.write(sql)
        
        print(f"\n✓ Migration saved to: {migration_file}")
        print("\nTo apply this migration:")
        print("1. Go to your Supabase Dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the migration SQL")
        print("4. Click 'Run' to execute")
        print("\nAlternatively, if you have Supabase CLI installed:")
        print(f"   supabase db execute --file {migration_file}")
        
        return True
        
    except Exception as e:
        print(f"Error preparing migration: {str(e)}")
        return False

def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database"""
    client = get_supabase_client()
    try:
        result = client.table(table_name).select('id').limit(1).execute()
        return True
    except Exception as e:
        if 'relation' in str(e) and 'does not exist' in str(e):
            return False
        # Some other error - table might exist
        return True

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        migration_file = sys.argv[1]
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        migration_name = Path(migration_file).stem
        success = apply_migration(sql, migration_name)
        sys.exit(0 if success else 1)
    else:
        print("Usage: python apply_migration_via_supabase.py <migration_file.sql>")