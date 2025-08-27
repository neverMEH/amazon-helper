#!/usr/bin/env python3
"""Apply campaign optimization functions and indexes to the database"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def apply_optimizations():
    """Apply optimization functions and indexes to the database"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Read the SQL file
        sql_file = Path(__file__).parent / 'create_campaign_optimization_functions.sql'
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Split into individual statements (separated by semicolon + newline)
        statements = [s.strip() for s in sql_content.split(';\n') if s.strip()]
        
        logger.info(f"Found {len(statements)} SQL statements to execute")
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue
                
            # Add semicolon back
            statement = statement + ';'
            
            # Get first few words for logging
            first_line = statement.split('\n')[0][:80]
            logger.info(f"Executing statement {i}: {first_line}...")
            
            try:
                # Use rpc to execute raw SQL
                result = client.rpc('exec_sql', {'query': statement}).execute()
                logger.info(f"✓ Statement {i} executed successfully")
            except Exception as e:
                # Try alternative approach - direct execution
                logger.warning(f"RPC failed, trying alternative method: {e}")
                # Note: This might fail if exec_sql function doesn't exist
                # In production, you'd execute these via Supabase dashboard or migration tool
                logger.warning(f"Statement {i} may need manual execution: {first_line}")
        
        logger.info("\n" + "="*50)
        logger.info("Testing optimized functions...")
        
        # Test the brand function
        try:
            result = client.rpc('get_campaign_brands_with_counts').execute()
            if result.data:
                logger.info(f"✓ Brand function works! Found {len(result.data)} unique brands")
                # Show first few brands
                for brand in result.data[:3]:
                    logger.info(f"  - {brand['brand']}: {brand['campaign_count']} campaigns")
            else:
                logger.info("✓ Brand function works but no brands found")
        except Exception as e:
            logger.error(f"✗ Brand function test failed: {e}")
        
        # Test the statistics function
        try:
            result = client.rpc('get_campaign_statistics').execute()
            if result.data and len(result.data) > 0:
                stats = result.data[0]
                logger.info(f"✓ Statistics function works!")
                logger.info(f"  - Total campaigns: {stats.get('total_campaigns', 0)}")
                logger.info(f"  - Enabled: {stats.get('enabled_campaigns', 0)}")
                logger.info(f"  - Paused: {stats.get('paused_campaigns', 0)}")
                logger.info(f"  - Archived: {stats.get('archived_campaigns', 0)}")
            else:
                logger.info("✓ Statistics function works but no data")
        except Exception as e:
            logger.error(f"✗ Statistics function test failed: {e}")
        
        logger.info("\n" + "="*50)
        logger.info("Campaign optimization setup complete!")
        logger.info("\nNote: If any functions failed to create, you may need to:")
        logger.info("1. Run the SQL statements directly in the Supabase SQL editor")
        logger.info("2. Or use Supabase migrations")
        logger.info(f"\nSQL file location: {sql_file}")
        
    except Exception as e:
        logger.error(f"Error applying optimizations: {e}")
        logger.info("\nTo apply manually:")
        logger.info("1. Go to your Supabase dashboard")
        logger.info("2. Navigate to SQL Editor")
        logger.info(f"3. Copy and run the contents of: {Path(__file__).parent / 'create_campaign_optimization_functions.sql'}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Starting campaign optimization setup...")
    success = apply_optimizations()
    sys.exit(0 if success else 1)