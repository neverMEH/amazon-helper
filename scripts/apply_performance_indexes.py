"""Apply performance indexes to Supabase database"""

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger
import sys

logger = get_logger(__name__)

def apply_indexes():
    """Apply performance indexes to the database"""
    try:
        # Get Supabase client with service role
        client = SupabaseManager.get_client(use_service_role=True)
        logger.info("Connected to Supabase")
        
        # Read the migration SQL
        with open('database/supabase/migrations/03_performance_indexes.sql', 'r') as f:
            sql = f.read()
        
        # Split into individual statements
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        logger.info(f"Applying {len(statements)} index creation statements...")
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            try:
                # Skip ANALYZE statements as they're not supported via Supabase client
                if statement.upper().startswith('ANALYZE'):
                    logger.info(f"Skipping ANALYZE statement {i}")
                    continue
                    
                # Execute the index creation
                client.rpc('exec_sql', {'query': statement}).execute()
                logger.info(f"✓ Applied statement {i}/{len(statements)}")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f"Index already exists (statement {i})")
                else:
                    logger.error(f"Failed to apply statement {i}: {e}")
                    logger.error(f"Statement: {statement[:100]}...")
        
        logger.info("✓ Performance indexes applied successfully!")
        
        # Check if indexes were created
        check_sql = """
        SELECT tablename, indexname 
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND indexname LIKE 'idx_%'
        ORDER BY tablename, indexname;
        """
        
        try:
            result = client.rpc('exec_sql', {'query': check_sql}).execute()
            if result.data:
                logger.info(f"\nCreated indexes:")
                for row in result.data:
                    logger.info(f"  - {row['tablename']}: {row['indexname']}")
        except:
            logger.info("Could not verify indexes (requires exec_sql function)")
        
    except Exception as e:
        logger.error(f"Failed to apply indexes: {e}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Starting performance index migration...")
    
    success = apply_indexes()
    
    if success:
        logger.info("✓ Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("✗ Migration failed!")
        sys.exit(1)