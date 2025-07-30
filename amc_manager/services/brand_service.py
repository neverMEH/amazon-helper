"""Brand management service"""

from typing import Dict, Any, List, Optional
from ..core.logger_simple import get_logger
from .db_service import db_service

logger = get_logger(__name__)


class BrandService:
    """Service for managing brands across instances and campaigns"""
    
    def __init__(self):
        self.db = db_service
    
    def get_all_brands_sync(self, user_id: str) -> List[Dict[str, str]]:
        """
        Get all available brands for a user from both configurations and campaigns
        
        Returns:
            List of dicts with brand_tag, brand_name, and source
        """
        try:
            return self.db.get_available_brands_sync(user_id)
        except Exception as e:
            logger.error(f"Error fetching brands: {e}")
            return []
    
    def get_instance_brands_sync(self, instance_id: str) -> List[str]:
        """
        Get brands directly associated with an instance
        
        Args:
            instance_id: The AMC instance ID
            
        Returns:
            List of brand tags
        """
        try:
            return self.db.get_instance_brands_direct_sync(instance_id)
        except Exception as e:
            logger.error(f"Error fetching instance brands: {e}")
            return []
    
    def update_instance_brands_sync(self, instance_id: str, brand_tags: List[str], user_id: str) -> bool:
        """
        Update brands associated with an instance
        
        Args:
            instance_id: The AMC instance ID
            brand_tags: List of brand tags to associate
            user_id: The user making the update
            
        Returns:
            True if successful
        """
        try:
            # Validate brand tags
            brand_tags = [tag.strip() for tag in brand_tags if tag and tag.strip()]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_tags = []
            for tag in brand_tags:
                if tag not in seen:
                    seen.add(tag)
                    unique_tags.append(tag)
            
            return self.db.update_instance_brands_sync(instance_id, unique_tags, user_id)
        except Exception as e:
            logger.error(f"Error updating instance brands: {e}")
            return False
    
    def get_brand_stats_sync(self, user_id: str) -> Dict[str, Dict[str, int]]:
        """
        Get statistics for all brands
        
        Returns:
            Dict mapping brand_tag to stats (campaign_count, instance_count, etc.)
        """
        try:
            stats = {}
            
            # Get all campaigns to count by brand
            campaigns = self.db.get_user_campaigns_sync(user_id)
            for campaign in campaigns:
                brand = campaign.get('brand_tag')
                if brand:
                    if brand not in stats:
                        stats[brand] = {
                            'campaign_count': 0,
                            'instance_count': 0,
                            'asin_count': 0
                        }
                    stats[brand]['campaign_count'] += 1
                    
                    # Count unique ASINs
                    asins = campaign.get('asins', [])
                    if asins:
                        stats[brand]['asin_count'] = len(set(asins))
            
            # Get instance counts
            instances = self.db.get_user_instances_sync(user_id)
            for instance in instances:
                instance_brands = self.get_instance_brands_sync(instance['instance_id'])
                for brand in instance_brands:
                    if brand in stats:
                        stats[brand]['instance_count'] += 1
            
            return stats
        except Exception as e:
            logger.error(f"Error calculating brand stats: {e}")
            return {}
    
    def validate_brand_tag(self, brand_tag: str) -> tuple[bool, Optional[str]]:
        """
        Validate a brand tag
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not brand_tag or not brand_tag.strip():
            return False, "Brand tag cannot be empty"
        
        brand_tag = brand_tag.strip()
        
        # Check length
        if len(brand_tag) > 100:
            return False, "Brand tag must be 100 characters or less"
        
        # Check for invalid characters (optional, depending on requirements)
        # For now, we'll allow most characters
        
        return True, None
    
    def normalize_brand_tag(self, brand_tag: str) -> str:
        """
        Normalize a brand tag for consistency
        
        Args:
            brand_tag: The brand tag to normalize
            
        Returns:
            Normalized brand tag
        """
        # Basic normalization: trim and lowercase
        return brand_tag.strip().lower()
    
    def merge_brands_sync(self, user_id: str, source_brand: str, target_brand: str) -> bool:
        """
        Merge one brand into another (updates all campaigns and instance associations)
        
        Args:
            user_id: The user performing the merge
            source_brand: Brand to merge from (will be removed)
            target_brand: Brand to merge into
            
        Returns:
            True if successful
        """
        try:
            # This would require additional database methods to:
            # 1. Update all campaigns with source_brand to use target_brand
            # 2. Update all instance_brands with source_brand to use target_brand
            # 3. Handle any brand_configurations
            
            # For now, return False as not implemented
            logger.warning("Brand merge not yet implemented")
            return False
        except Exception as e:
            logger.error(f"Error merging brands: {e}")
            return False


# Global instance
brand_service = BrandService()