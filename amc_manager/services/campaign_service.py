"""Campaign import and management service"""

import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.logger_simple import get_logger
from ..config import settings
from .db_service import db_service
from .token_service import token_service

logger = get_logger(__name__)


class CampaignService:
    """Service for importing and managing campaigns from Amazon API"""
    
    def __init__(self):
        self.base_url = "https://advertising-api.amazon.com"
        self.dsp_campaigns_endpoint = f"{self.base_url}/dsp/campaigns"
        self.sp_campaigns_endpoint = f"{self.base_url}/sp/campaigns"
        self.sd_campaigns_endpoint = f"{self.base_url}/sd/campaigns"
        self.sb_campaigns_endpoint = f"{self.base_url}/sb/campaigns"
    
    async def import_campaigns_for_user(self, user_id: str, profile_id: str) -> Dict[str, int]:
        """
        Import campaigns for a specific profile
        
        Args:
            user_id: User ID in database
            profile_id: Amazon Advertising profile ID
            
        Returns:
            Dictionary with counts of imported campaigns by type
        """
        counts = {
            'dsp': 0,
            'sponsored_products': 0,
            'sponsored_display': 0,
            'sponsored_brands': 0,
            'total': 0
        }
        
        # Get valid token
        access_token = await token_service.get_valid_token(user_id)
        if not access_token:
            logger.error("No valid token available")
            return counts
        
        # Import each campaign type
        logger.info(f"Importing campaigns for profile {profile_id}")
        
        # DSP Campaigns
        dsp_campaigns = await self._fetch_dsp_campaigns(access_token, profile_id)
        if dsp_campaigns:
            for campaign in dsp_campaigns:
                await self._store_campaign(user_id, campaign, 'DSP', profile_id)
                counts['dsp'] += 1
        
        # Sponsored Products
        sp_campaigns = await self._fetch_sponsored_campaigns(
            access_token, profile_id, self.sp_campaigns_endpoint, 'SP'
        )
        if sp_campaigns:
            for campaign in sp_campaigns:
                await self._store_campaign(user_id, campaign, 'SP', profile_id)
                counts['sponsored_products'] += 1
        
        # Sponsored Display
        sd_campaigns = await self._fetch_sponsored_campaigns(
            access_token, profile_id, self.sd_campaigns_endpoint, 'SD'
        )
        if sd_campaigns:
            for campaign in sd_campaigns:
                await self._store_campaign(user_id, campaign, 'SD', profile_id)
                counts['sponsored_display'] += 1
        
        # Sponsored Brands
        sb_campaigns = await self._fetch_sponsored_campaigns(
            access_token, profile_id, self.sb_campaigns_endpoint, 'SB'
        )
        if sb_campaigns:
            for campaign in sb_campaigns:
                await self._store_campaign(user_id, campaign, 'SB', profile_id)
                counts['sponsored_brands'] += 1
        
        counts['total'] = sum([counts['dsp'], counts['sponsored_products'], 
                              counts['sponsored_display'], counts['sponsored_brands']])
        
        logger.info(f"Imported {counts['total']} campaigns for profile {profile_id}")
        return counts
    
    async def _fetch_dsp_campaigns(self, access_token: str, profile_id: str) -> Optional[List[Dict]]:
        """Fetch DSP campaigns"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Amazon-Advertising-API-Scope': profile_id,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(self.dsp_campaigns_endpoint, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"DSP campaigns fetch failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching DSP campaigns: {e}")
            return None
    
    async def _fetch_sponsored_campaigns(self, access_token: str, profile_id: str, 
                                       endpoint: str, campaign_type: str) -> Optional[List[Dict]]:
        """Fetch sponsored campaigns (SP/SD/SB)"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Amazon-Advertising-API-Scope': profile_id,
            'Content-Type': 'application/json'
        }
        
        try:
            # For sponsored campaigns, we need to use the extended endpoint
            url = f"{endpoint}/extended"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"{campaign_type} campaigns fetch failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching {campaign_type} campaigns: {e}")
            return None
    
    async def _store_campaign(self, user_id: str, campaign_data: Dict, 
                            campaign_type: str, profile_id: str) -> bool:
        """Store campaign in database"""
        try:
            # Extract campaign info based on type
            if campaign_type == 'DSP':
                campaign_id = campaign_data.get('campaignId', campaign_data.get('id'))
                campaign_name = campaign_data.get('name', 'Unknown')
                marketplace_id = campaign_data.get('marketplaceId', 'ATVPDKIKX0DER')
            else:
                campaign_id = campaign_data.get('campaignId')
                campaign_name = campaign_data.get('name', 'Unknown')
                marketplace_id = campaign_data.get('marketplaceId', 'ATVPDKIKX0DER')
            
            if not campaign_id:
                return False
            
            # Prepare campaign mapping data
            mapping_data = {
                'campaign_id': str(campaign_id),
                'campaign_name': campaign_name,
                'original_name': campaign_name,
                'campaign_type': campaign_type,
                'marketplace_id': marketplace_id,
                'profile_id': str(profile_id),
                'user_id': user_id,
                'first_seen_at': datetime.utcnow().isoformat(),
                'last_seen_at': datetime.utcnow().isoformat(),
                'brand_tag': await self._auto_tag_brand(campaign_name),
                'asins': [],  # Will be populated later
                'tags': [campaign_type],
                'brand_metadata': campaign_data
            }
            
            # Store in database
            result = await db_service.create_campaign_mapping(mapping_data)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error storing campaign: {e}")
            return False
    
    async def _auto_tag_brand(self, campaign_name: str) -> Optional[str]:
        """Auto-tag campaign with brand based on name patterns"""
        # Simple brand detection based on common patterns
        campaign_lower = campaign_name.lower()
        
        # Define brand patterns (extend this based on your brands)
        brand_patterns = {
            'dirty labs': ['dirty labs', 'dirtylabs'],
            'planetary design': ['planetary', 'planetary design'],
            'defender': ['defender', 'defender operations'],
            'wise essentials': ['wise essentials', 'wise'],
            'supergoop': ['supergoop'],
            'terry naturally': ['terry naturally', 'terry'],
            'juicebeauty': ['juice beauty', 'juicebeauty'],
            'beekman': ['beekman', 'beekman1802'],
            'messermeister': ['messermeister'],
            'stokke': ['stokke'],
            'oofos': ['oofos'],
            'triangle': ['triangle'],
            'wolf1834': ['wolf', 'wolf1834'],
            'fekkia': ['fekkia'],
            'true grace': ['true grace', 'truegrace'],
            'natures plus': ['natures plus', 'naturesplus'],
            'brain md': ['brain md', 'brainmd'],
            'dphu': ['dphu'],
            'beauty for real': ['beauty for real', 'beautyforrreal'],
            'kneipp': ['kneipp'],
            'nest new york': ['nest new york', 'nest'],
            'dr brandt': ['dr brandt', 'drbrandt'],
            'skinfix': ['skinfix'],
            'issey miyake': ['issey miyake', 'isseymiyake'],
            'drunk elephant': ['drunk elephant', 'drunkelephant']
        }
        
        # Check each brand pattern
        for brand_tag, patterns in brand_patterns.items():
            for pattern in patterns:
                if pattern in campaign_lower:
                    return brand_tag
        
        # Check for marketplace indicators
        if any(market in campaign_lower for market in ['_us', '_ca', '_mx']):
            # Extract brand from format like "brand_us_campaign"
            parts = campaign_name.split('_')
            if parts:
                return parts[0].lower()
        
        return None
    
    async def update_campaign_asins(self, campaign_id: str, marketplace_id: str, 
                                  asins: List[str]) -> bool:
        """Update ASINs for a campaign"""
        try:
            # Get existing campaign
            campaigns = await db_service.get_user_campaigns(None)  # Need to fix this
            campaign = next((c for c in campaigns 
                           if c['campaign_id'] == campaign_id 
                           and c['marketplace_id'] == marketplace_id), None)
            
            if not campaign:
                logger.error(f"Campaign not found: {campaign_id}")
                return False
            
            # Update ASINs
            result = await db_service.create_campaign_mapping({
                'id': campaign['id'],
                'campaign_id': campaign_id,
                'marketplace_id': marketplace_id,
                'asins': asins,
                'last_seen_at': datetime.utcnow().isoformat()
            })
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating campaign ASINs: {e}")
            return False

# Global instance
campaign_service = CampaignService()