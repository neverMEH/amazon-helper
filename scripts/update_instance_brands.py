"""Script to update instance brands from provided data"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

# Brand data from the user
brand_data = [
    {"brand_name": "Issey Miyake", "instance_id": "amcfgermlrz"},
    {"brand_name": "Babyzen", "instance_id": "amccwscrrq8"},
    {"brand_name": "Petag", "instance_id": "amcgmtbxikm"},
    {"brand_name": "Beast Sports Nutrition", "instance_id": "amcuwvavi2c"},
    {"brand_name": "Beauty For Real", "instance_id": "amc1ryu6cfx"},
    {"brand_name": "Beekman 1802", "instance_id": "amcbh7iaiyo"},
    {"brand_name": "Bioelements", "instance_id": "amcyrodlazj"},
    {"brand_name": "Biosil", "instance_id": "amc32d6ndaq"},
    {"brand_name": "Brainmd", "instance_id": "amcevssuawv"},
    {"brand_name": "Brunt Workwear", "instance_id": "amcz3ds4z3p"},
    {"brand_name": "Brunt Workwear", "instance_id": "amcpty36ykq"},  # duplicate
    {"brand_name": "Cellfood", "instance_id": "amcejx15rxg"},
    {"brand_name": "Dphue", "instance_id": "amc4tzbsn6p"},
    {"brand_name": "Dr Brandt", "instance_id": "amc2msuriyj"},
    {"brand_name": "Earthly Body", "instance_id": "amczihg5eeg"},
    {"brand_name": "Fekkai", "instance_id": "amccfnbscqp"},
    {"brand_name": "Finaflex", "instance_id": "amcoofgv1te"},
    {"brand_name": "Juice Beauty", "instance_id": "amctftix0zs"},
    {"brand_name": "Kneipp", "instance_id": "amcq0fosngn"},
    {"brand_name": "Kusmi Tea", "instance_id": "amcvqirv65e"},
    {"brand_name": "Lafco", "instance_id": "amcn3n0vw3a"},
    {"brand_name": "Masimo Stork", "instance_id": "amckqfu9xyc"},
    {"brand_name": "Master Supplements", "instance_id": "amc3xan0joi"},
    {"brand_name": "Messermeister", "instance_id": "amcsuca4g2i"},
    {"brand_name": "Miko", "instance_id": "amcv3yfzczt"},
    {"brand_name": "Nahs", "instance_id": "amcu8iexypz"},
    {"brand_name": "Natures Plus", "instance_id": "amc6cibyqdk"},
    {"brand_name": "Natures Plus", "instance_id": "amcrmzp8ksg"},  # duplicate
    {"brand_name": "Nest New York", "instance_id": "amcuvz39w6v"},
    {"brand_name": "Oofos", "instance_id": "amcrmxo9w4w"},
    {"brand_name": "Sandbox", "instance_id": "amchnfozgta"},
    {"brand_name": "Shiseido", "instance_id": "amc6ikpceyf"},
    {"brand_name": "Sisu Mouth Guards", "instance_id": "amc3urviq5f"},
    {"brand_name": "Skinfix", "instance_id": "amcaihrnqbt"},
    {"brand_name": "Solgar", "instance_id": "amczj5bslba"},
    {"brand_name": "Sova Night Guards", "instance_id": "amcbidnursc"},
    {"brand_name": "Stevita", "instance_id": "amc2i81srqu"},
    {"brand_name": "Stokke", "instance_id": "amce4iszklc"},
    {"brand_name": "Strider", "instance_id": "amchhzyxqqv"},
    {"brand_name": "Supergoop", "instance_id": "amcibersblt"},
    {"brand_name": "Tenpoint", "instance_id": "amczyucihqb"},
    {"brand_name": "Terry Naturally", "instance_id": "amckqdowe3r"},
    {"brand_name": "Triangle", "instance_id": "amcbsmnktjt"},
    {"brand_name": "True Grace", "instance_id": "amcmjuveoi2"},
    {"brand_name": "Wolf 1834", "instance_id": "amccsrdncjy"},
    {"brand_name": "Zak", "instance_id": "amcc3z1jwgk"},
    {"brand_name": "Drunken Elephant", "instance_id": "amcgjj6iu5v"},
    {"brand_name": "Nelson (Bach, Spatone, Rescue)", "instance_id": "amcukusaamj"},
]

def update_instance_brands():
    """Update brands for instances"""
    client = SupabaseManager.get_client(use_service_role=True)
    
    # Get a default user ID (we'll use the first user)
    user_response = client.table('users').select('id').limit(1).execute()
    if not user_response.data:
        logger.error("No users found in database")
        return
    
    default_user_id = user_response.data[0]['id']
    logger.info(f"Using user ID: {default_user_id}")
    
    # Process each brand-instance association
    success_count = 0
    error_count = 0
    
    for item in brand_data:
        brand_name = item['brand_name']
        instance_id = item['instance_id']
        
        try:
            # Get internal instance ID
            instance_response = client.table('amc_instances')\
                .select('id, instance_name')\
                .eq('instance_id', instance_id)\
                .execute()
            
            if not instance_response.data:
                logger.warning(f"Instance {instance_id} not found for brand {brand_name}")
                error_count += 1
                continue
            
            internal_id = instance_response.data[0]['id']
            instance_name = instance_response.data[0]['instance_name']
            
            # Check if brand already exists for this instance
            existing_response = client.table('instance_brands')\
                .select('*')\
                .eq('instance_id', internal_id)\
                .eq('brand_tag', brand_name)\
                .execute()
            
            if existing_response.data:
                logger.info(f"Brand '{brand_name}' already exists for instance {instance_id} ({instance_name})")
                success_count += 1
                continue
            
            # Insert new brand association
            insert_data = {
                'instance_id': internal_id,
                'brand_tag': brand_name,
                'user_id': default_user_id
            }
            
            insert_response = client.table('instance_brands')\
                .insert(insert_data)\
                .execute()
            
            if insert_response.data:
                logger.info(f"✓ Added brand '{brand_name}' to instance {instance_id} ({instance_name})")
                success_count += 1
            else:
                logger.error(f"Failed to add brand '{brand_name}' to instance {instance_id}")
                error_count += 1
                
        except Exception as e:
            logger.error(f"Error processing brand '{brand_name}' for instance {instance_id}: {e}")
            error_count += 1
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"Update complete!")
    logger.info(f"Success: {success_count}")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Total processed: {len(brand_data)}")
    
    # Show current brand associations
    logger.info(f"\n{'='*50}")
    logger.info("Current brand associations:")
    
    try:
        # Get all instances with their brands
        instances_response = client.table('amc_instances')\
            .select('instance_id, instance_name, instance_brands(brand_tag)')\
            .order('instance_name')\
            .execute()
        
        for instance in instances_response.data:
            brands = [b['brand_tag'] for b in instance.get('instance_brands', [])]
            if brands:
                logger.info(f"\n{instance['instance_name']} ({instance['instance_id']}):")
                for brand in sorted(brands):
                    logger.info(f"  - {brand}")
    except Exception as e:
        logger.error(f"Error fetching current associations: {e}")


if __name__ == "__main__":
    update_instance_brands()