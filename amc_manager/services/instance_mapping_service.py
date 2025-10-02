"""Instance parameter mapping service for managing brand, ASIN, and campaign associations"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

from ..core.logger_simple import get_logger
from .db_service import db_service

logger = get_logger(__name__)


class InstanceMappingService:
    """Service for managing instance-level parameter mappings (brands, ASINs, campaigns)"""

    def __init__(self):
        self.db = db_service

    def get_available_brands(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all brands available to the user from campaigns and product_asins tables.

        Args:
            user_id: The user ID

        Returns:
            List of brand dictionaries with brand_tag, brand_name, asin_count, campaign_count
        """
        try:
            brands_dict = {}

            # Get ALL campaigns with pagination to avoid hitting the 1000 row limit
            offset = 0
            batch_size = 1000
            while True:
                campaigns_result = self.db.client.table('campaigns')\
                    .select('brand, campaign_id')\
                    .not_.is_('brand', 'null')\
                    .range(offset, offset + batch_size - 1)\
                    .execute()

                if not campaigns_result.data:
                    break

                for row in campaigns_result.data:
                    brand = row.get('brand')
                    campaign_id = row.get('campaign_id')

                    # Skip promotion IDs (won't work in AMC queries)
                    if isinstance(campaign_id, str) and campaign_id.startswith(('coupon-', 'promo-', 'percentageoff-', 'amountoff-', 'buyxgety-')):
                        continue

                    if brand and brand.strip():
                        if brand not in brands_dict:
                            brands_dict[brand] = {
                                'brand_tag': brand,
                                'brand_name': brand,
                                'source': 'campaign',
                                'asin_count': 0,
                                'campaign_count': 0
                            }
                        brands_dict[brand]['campaign_count'] = brands_dict[brand].get('campaign_count', 0) + 1

                if len(campaigns_result.data) < batch_size:
                    break
                offset += batch_size

            # Get ALL ASINs with pagination
            offset = 0
            while True:
                asins_result = self.db.client.table('product_asins')\
                    .select('brand')\
                    .eq('active', True)\
                    .not_.is_('brand', 'null')\
                    .range(offset, offset + batch_size - 1)\
                    .execute()

                if not asins_result.data:
                    break

                for row in asins_result.data:
                    brand = row.get('brand')
                    if brand and brand.strip():
                        if brand not in brands_dict:
                            brands_dict[brand] = {
                                'brand_tag': brand,
                                'brand_name': brand,
                                'source': 'product',
                                'asin_count': 0,
                                'campaign_count': 0
                            }
                        else:
                            # If brand already exists from campaigns, update source to indicate both
                            if brands_dict[brand]['source'] == 'campaign':
                                brands_dict[brand]['source'] = 'both'

                        brands_dict[brand]['asin_count'] = brands_dict[brand].get('asin_count', 0) + 1

                if len(asins_result.data) < batch_size:
                    break
                offset += batch_size

            # Convert to list and sort by brand name
            brands_list = sorted(brands_dict.values(), key=lambda x: x['brand_tag'])

            return brands_list

        except Exception as e:
            logger.error(f"Error fetching available brands: {e}")
            return []

    def get_brand_asins(self, brand_tag: str, user_id: str, search: Optional[str] = None,
                       limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Get all ASINs associated with a specific brand from product_asins table.

        Args:
            brand_tag: The brand identifier
            user_id: The user ID
            search: Optional search term for filtering
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            Dict with brand_tag, asins list, total count, limit, offset
        """
        try:
            # Query product_asins table for this brand
            query = self.db.client.table('product_asins')\
                .select('asin, title, brand, last_known_price, active', count='exact')\
                .eq('brand', brand_tag)\
                .eq('active', True)

            # Apply search filter if provided
            if search:
                query = query.or_(f'asin.ilike.%{search}%,title.ilike.%{search}%')

            # Apply pagination
            query = query.range(offset, offset + limit - 1)

            result = query.execute()

            return {
                'brand_tag': brand_tag,
                'asins': result.data,
                'total': result.count or 0,
                'limit': limit,
                'offset': offset
            }
        except Exception as e:
            logger.error(f"Error fetching brand ASINs for {brand_tag}: {e}")
            return {
                'brand_tag': brand_tag,
                'asins': [],
                'total': 0,
                'limit': limit,
                'offset': offset
            }

    def get_brand_campaigns(self, brand_tag: str, user_id: str, search: Optional[str] = None,
                           campaign_type: Optional[str] = None, limit: int = 100,
                           offset: int = 0) -> Dict[str, Any]:
        """
        Get all campaigns associated with a specific brand.

        Args:
            brand_tag: The brand identifier
            user_id: The user ID
            search: Optional search term
            campaign_type: Optional campaign type filter (SP, SB, SD, DSP)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            Dict with brand_tag, campaigns list, total count
        """
        try:
            # Query campaigns table for this brand
            query = self.db.client.table('campaigns')\
                .select('campaign_id, name, type, state, brand', count='exact')\
                .eq('brand', brand_tag)

            # Apply optional filters
            if search:
                query = query.ilike('name', f'%{search}%')

            if campaign_type:
                query = query.eq('type', campaign_type)

            # Apply pagination
            query = query.range(offset, offset + limit - 1)

            result = query.execute()

            # Filter out promotion IDs (won't work in AMC queries)
            campaigns = [{
                'campaign_id': row['campaign_id'],
                'campaign_name': row['name'],
                'campaign_type': row.get('type'),
                'state': row.get('state'),
                'brand': row['brand']
            } for row in result.data
            if not (isinstance(row['campaign_id'], str) and
                   row['campaign_id'].startswith(('coupon-', 'promo-', 'percentageoff-', 'amountoff-', 'buyxgety-')))]

            return {
                'brand_tag': brand_tag,
                'campaigns': campaigns,
                'total': result.count or 0,
                'limit': limit,
                'offset': offset
            }
        except Exception as e:
            logger.error(f"Error fetching brand campaigns for {brand_tag}: {e}")
            return {
                'brand_tag': brand_tag,
                'campaigns': [],
                'total': 0,
                'limit': limit,
                'offset': offset
            }

    def get_instance_mappings(self, instance_id: str, user_id: str) -> Dict[str, Any]:
        """
        Retrieve all parameter mappings for an instance.

        Args:
            instance_id: The instance UUID
            user_id: The user ID (for permission check)

        Returns:
            Dict with brands, asins_by_brand, campaigns_by_brand, updated_at
        """
        try:
            # Verify user has access to this instance
            instance = self.db.client.table('amc_instances')\
                .select('*, amc_accounts!inner(user_id)')\
                .eq('id', instance_id)\
                .execute()

            if not instance.data or instance.data[0]['amc_accounts']['user_id'] != user_id:
                logger.warning(f"User {user_id} doesn't have access to instance {instance_id}")
                return {
                    'instance_id': instance_id,
                    'brands': [],
                    'asins_by_brand': {},
                    'campaigns_by_brand': {},
                    'updated_at': None
                }

            # Get brands
            brands_result = self.db.client.table('instance_brands')\
                .select('brand_tag')\
                .eq('instance_id', instance_id)\
                .execute()

            brands = [b['brand_tag'] for b in brands_result.data]

            # Get ASINs grouped by brand
            asins_result = self.db.client.table('instance_brand_asins')\
                .select('brand_tag, asin')\
                .eq('instance_id', instance_id)\
                .execute()

            asins_by_brand = {}
            for row in asins_result.data:
                brand = row['brand_tag']
                if brand not in asins_by_brand:
                    asins_by_brand[brand] = []
                asins_by_brand[brand].append(row['asin'])

            # Get campaigns grouped by brand
            campaigns_result = self.db.client.table('instance_brand_campaigns')\
                .select('brand_tag, campaign_id')\
                .eq('instance_id', instance_id)\
                .execute()

            campaigns_by_brand = {}
            for row in campaigns_result.data:
                brand = row['brand_tag']
                if brand not in campaigns_by_brand:
                    campaigns_by_brand[brand] = []
                campaigns_by_brand[brand].append(row['campaign_id'])

            # Get most recent update timestamp
            latest_asin = self.db.client.table('instance_brand_asins')\
                .select('updated_at')\
                .eq('instance_id', instance_id)\
                .order('updated_at', desc=True)\
                .limit(1)\
                .execute()

            latest_campaign = self.db.client.table('instance_brand_campaigns')\
                .select('updated_at')\
                .eq('instance_id', instance_id)\
                .order('updated_at', desc=True)\
                .limit(1)\
                .execute()

            updated_at = None
            if latest_asin.data:
                updated_at = latest_asin.data[0]['updated_at']
            if latest_campaign.data:
                campaign_time = latest_campaign.data[0]['updated_at']
                if not updated_at or campaign_time > updated_at:
                    updated_at = campaign_time

            return {
                'instance_id': instance_id,
                'brands': brands,
                'asins_by_brand': asins_by_brand,
                'campaigns_by_brand': campaigns_by_brand,
                'updated_at': updated_at
            }

        except Exception as e:
            logger.error(f"Error fetching instance mappings for {instance_id}: {e}")
            return {
                'instance_id': instance_id,
                'brands': [],
                'asins_by_brand': {},
                'campaigns_by_brand': {},
                'updated_at': None
            }

    def save_instance_mappings(self, instance_id: str, user_id: str,
                              mappings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save instance mappings (transactional: delete existing + insert new).

        Args:
            instance_id: The instance UUID
            user_id: The user ID
            mappings: Dict with brands, asins_by_brand, campaigns_by_brand

        Returns:
            Dict with success status, message, and stats
        """
        try:
            # Verify user has access
            instance = self.db.client.table('amc_instances')\
                .select('*, amc_accounts!inner(user_id)')\
                .eq('id', instance_id)\
                .execute()

            if not instance.data or instance.data[0]['amc_accounts']['user_id'] != user_id:
                return {
                    'success': False,
                    'message': 'Access denied: User does not have permission to modify this instance'
                }

            brands = mappings.get('brands', [])
            asins_by_brand = mappings.get('asins_by_brand', {})
            campaigns_by_brand = mappings.get('campaigns_by_brand', {})

            # Validate at least one brand
            if not brands:
                return {
                    'success': False,
                    'message': 'At least one brand must be provided'
                }

            # Delete existing mappings
            self.db.client.table('instance_brands')\
                .delete().eq('instance_id', instance_id).execute()
            self.db.client.table('instance_brand_asins')\
                .delete().eq('instance_id', instance_id).execute()
            self.db.client.table('instance_brand_campaigns')\
                .delete().eq('instance_id', instance_id).execute()

            # Insert brand associations
            brand_records = []
            for brand_tag in brands:
                brand_records.append({
                    'id': str(uuid4()),
                    'instance_id': instance_id,
                    'brand_tag': brand_tag,
                    'user_id': user_id,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                })

            if brand_records:
                self.db.client.table('instance_brands').insert(brand_records).execute()

            # Insert ASIN mappings
            asin_records = []
            for brand_tag, asins in asins_by_brand.items():
                if brand_tag not in brands:
                    continue  # Skip ASINs for brands not in the list
                for asin in asins:
                    asin_records.append({
                        'id': str(uuid4()),
                        'instance_id': instance_id,
                        'brand_tag': brand_tag,
                        'asin': asin,
                        'user_id': user_id,
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    })

            if asin_records:
                self.db.client.table('instance_brand_asins').insert(asin_records).execute()

            # Insert campaign mappings
            campaign_records = []
            for brand_tag, campaigns in campaigns_by_brand.items():
                if brand_tag not in brands:
                    continue  # Skip campaigns for brands not in the list
                for campaign_id in campaigns:
                    campaign_records.append({
                        'id': str(uuid4()),
                        'instance_id': instance_id,
                        'brand_tag': brand_tag,
                        'campaign_id': campaign_id,
                        'user_id': user_id,
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    })

            if campaign_records:
                self.db.client.table('instance_brand_campaigns').insert(campaign_records).execute()

            return {
                'success': True,
                'message': 'Instance mappings saved successfully',
                'instance_id': instance_id,
                'stats': {
                    'brands_saved': len(brand_records),
                    'asins_saved': len(asin_records),
                    'campaigns_saved': len(campaign_records)
                },
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error saving instance mappings for {instance_id}: {e}")
            return {
                'success': False,
                'message': f'Failed to save mappings: {str(e)}'
            }

    def get_parameter_values(self, instance_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get formatted parameter values for auto-population in query execution.

        Args:
            instance_id: The instance UUID
            user_id: The user ID

        Returns:
            Dict with parameters (brand_list, asin_list, campaign_ids, campaign_names) and has_mappings flag
        """
        try:
            mappings = self.get_instance_mappings(instance_id, user_id)

            if not mappings['brands']:
                return {
                    'instance_id': instance_id,
                    'parameters': {
                        'brand_list': '',
                        'asin_list': '',
                        'campaign_ids': '',
                        'campaign_names': ''
                    },
                    'has_mappings': False
                }

            # Format brands as comma-separated list
            brand_list = ','.join(mappings['brands'])

            # Collect all ASINs across brands
            all_asins = []
            for brand_asins in mappings['asins_by_brand'].values():
                all_asins.extend(brand_asins)
            asin_list = ','.join(all_asins)

            # Collect all campaign IDs across brands
            all_campaign_ids = []
            for brand_campaigns in mappings['campaigns_by_brand'].values():
                all_campaign_ids.extend(brand_campaigns)
            campaign_ids = ','.join(str(cid) for cid in all_campaign_ids)

            # TODO: Fetch campaign names when campaign_mappings table exists
            campaign_names = ''

            return {
                'instance_id': instance_id,
                'parameters': {
                    'brand_list': brand_list,
                    'asin_list': asin_list,
                    'campaign_ids': campaign_ids,
                    'campaign_names': campaign_names
                },
                'has_mappings': True
            }

        except Exception as e:
            logger.error(f"Error getting parameter values for {instance_id}: {e}")
            return {
                'instance_id': instance_id,
                'parameters': {
                    'brand_list': '',
                    'asin_list': '',
                    'campaign_ids': '',
                    'campaign_names': ''
                },
                'has_mappings': False
            }


# Singleton instance
instance_mapping_service = InstanceMappingService()
