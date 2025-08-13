#!/usr/bin/env python3
"""
Setup AMC Data Sources
Applies migration and imports all schema documentation
"""

import os
import sys
import logging
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.import_amc_schemas import AMCSchemaImporter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def apply_migration():
    """Apply the AMC data sources migration"""
    logger.info("Applying AMC data sources migration...")
    
    try:
        # Read migration file
        migration_path = Path(__file__).parent.parent / "database/supabase/migrations/12_amc_data_sources.sql"
        
        if not migration_path.exists():
            logger.error(f"Migration file not found: {migration_path}")
            return False
        
        with open(migration_path, 'r') as f:
            sql = f.read()
        
        # Connect to Supabase
        client: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        
        # Execute migration
        # Note: Supabase Python client doesn't have direct SQL execution
        # You may need to run this via Supabase dashboard or psql
        logger.warning("Note: Please run the migration SQL directly in Supabase dashboard:")
        logger.warning(f"  SQL -> New Query -> Copy contents of {migration_path}")
        logger.warning("  Then run this script again with --skip-migration flag")
        
        return True
        
    except Exception as e:
        logger.error(f"Error applying migration: {str(e)}")
        return False


def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup AMC Data Sources')
    parser.add_argument('--skip-migration', action='store_true', 
                       help='Skip migration (if already applied)')
    parser.add_argument('--reimport', action='store_true',
                       help='Force reimport of all schemas')
    args = parser.parse_args()
    
    # Step 1: Apply migration (unless skipped)
    if not args.skip_migration:
        if not apply_migration():
            logger.error("Migration failed. Please apply manually and run with --skip-migration")
            return 1
    else:
        logger.info("Skipping migration (assumed already applied)")
    
    # Step 2: Import schemas
    logger.info("Starting schema import...")
    importer = AMCSchemaImporter()
    
    try:
        # Check if schemas already exist
        client: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        
        result = client.table('amc_data_sources').select('count', count='exact').execute()
        existing_count = result.count if hasattr(result, 'count') else 0
        
        if existing_count > 0 and not args.reimport:
            logger.info(f"Found {existing_count} existing schemas. Use --reimport to force reimport.")
            return 0
        
        # Run the import
        importer.run()
        
        logger.info("✅ AMC Data Sources setup complete!")
        logger.info("\nNext steps:")
        logger.info("1. Start the backend: python main_supabase.py")
        logger.info("2. Start the frontend: cd frontend && npm run dev")
        logger.info("3. Navigate to http://localhost:5173/data-sources")
        
        return 0
        
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())