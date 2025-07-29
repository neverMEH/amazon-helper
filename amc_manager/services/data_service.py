"""Data retrieval service for campaigns, ASINs, and results"""

import boto3
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO

from ..core import AMCAPIClient, AMCAPIEndpoints, get_logger
from ..core.exceptions import APIError, ValidationError
from ..config import settings


logger = get_logger(__name__)


class DataRetrievalService:
    """Service for retrieving campaign data, ASINs, and execution results"""
    
    def __init__(self, api_client: AMCAPIClient):
        """
        Initialize data retrieval service
        
        Args:
            api_client: Configured AMC API client
        """
        self.api_client = api_client
        self.s3_client = self._init_s3_client()
        
    def _init_s3_client(self):
        """Initialize S3 client for result retrieval"""
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            return boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
        return None
        
    async def get_dsp_campaigns(
        self,
        user_id: str,
        user_token: Dict[str, Any],
        profile_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve DSP campaign data
        
        Args:
            user_id: User identifier
            user_token: User's auth token
            profile_id: Advertising profile ID
            filters: Optional filters (status, date range, etc.)
            
        Returns:
            List of DSP campaigns with enriched data
        """
        try:
            params = {
                'profileId': profile_id,
                'campaignType': 'sponsoredDisplay',
                **(filters or {})
            }
            
            response = self.api_client.get(
                AMCAPIEndpoints.CAMPAIGNS,
                user_id,
                user_token,
                params=params
            )
            
            campaigns = response.get('campaigns', [])
            
            # Enrich campaign data
            for campaign in campaigns:
                campaign['campaignType'] = 'DSP'
                campaign['amcCampaignName'] = campaign.get('name', '')
                campaign['originalName'] = campaign.get('name', '')  # Store original name
                
            logger.info(f"Retrieved {len(campaigns)} DSP campaigns")
            return campaigns
            
        except APIError as e:
            logger.error(f"Failed to retrieve DSP campaigns: {e}")
            raise
            
    async def get_sponsored_ads_campaigns(
        self,
        user_id: str,
        user_token: Dict[str, Any],
        profile_id: str,
        ad_type: str = 'all',
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve Sponsored Ads campaigns (Products, Brands, Display)
        
        Args:
            user_id: User identifier
            user_token: User's auth token
            profile_id: Advertising profile ID
            ad_type: Type of sponsored ads ('products', 'brands', 'display', 'all')
            filters: Optional filters
            
        Returns:
            List of sponsored ads campaigns
        """
        campaign_types = {
            'products': 'sponsoredProducts',
            'brands': 'sponsoredBrands',
            'display': 'sponsoredDisplay',
            'all': None
        }
        
        try:
            all_campaigns = []
            
            if ad_type == 'all':
                # Retrieve all types
                for type_key, type_value in campaign_types.items():
                    if type_key != 'all':
                        params = {
                            'profileId': profile_id,
                            'campaignType': type_value,
                            **(filters or {})
                        }
                        
                        response = self.api_client.get(
                            AMCAPIEndpoints.CAMPAIGNS,
                            user_id,
                            user_token,
                            params=params
                        )
                        
                        campaigns = response.get('campaigns', [])
                        for campaign in campaigns:
                            campaign['campaignType'] = type_key.title()
                            campaign['amcCampaignName'] = campaign.get('name', '')
                            campaign['originalName'] = campaign.get('name', '')
                            
                        all_campaigns.extend(campaigns)
            else:
                # Retrieve specific type
                campaign_type = campaign_types.get(ad_type)
                if not campaign_type:
                    raise ValidationError(f"Invalid ad type: {ad_type}")
                    
                params = {
                    'profileId': profile_id,
                    'campaignType': campaign_type,
                    **(filters or {})
                }
                
                response = self.api_client.get(
                    AMCAPIEndpoints.CAMPAIGNS,
                    user_id,
                    user_token,
                    params=params
                )
                
                campaigns = response.get('campaigns', [])
                for campaign in campaigns:
                    campaign['campaignType'] = ad_type.title()
                    campaign['amcCampaignName'] = campaign.get('name', '')
                    campaign['originalName'] = campaign.get('name', '')
                    
                all_campaigns = campaigns
                
            logger.info(f"Retrieved {len(all_campaigns)} sponsored ads campaigns")
            return all_campaigns
            
        except APIError as e:
            logger.error(f"Failed to retrieve sponsored ads campaigns: {e}")
            raise
            
    async def get_active_asins(
        self,
        instance_id: str,
        user_id: str,
        user_token: Dict[str, Any],
        time_range_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Retrieve active ASINs from AMC instance
        
        Args:
            instance_id: AMC instance ID
            user_id: User identifier
            user_token: User's auth token
            time_range_days: Number of days to look back for active ASINs
            
        Returns:
            List of active ASINs with metrics
        """
        # This would typically run a query to get active ASINs
        # For now, we'll create a placeholder implementation
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_range_days)
        
        # SQL query to get active ASINs
        sql_query = f"""
        SELECT 
            asin,
            COUNT(DISTINCT user_id) as unique_users,
            SUM(impressions) as total_impressions,
            SUM(clicks) as total_clicks,
            SUM(conversions) as total_conversions
        FROM amazon_attributed_events_by_conversion_time
        WHERE 
            conversion_event_dt >= '{start_date.strftime('%Y-%m-%d')}'
            AND conversion_event_dt <= '{end_date.strftime('%Y-%m-%d')}'
            AND asin IS NOT NULL
        GROUP BY asin
        ORDER BY total_conversions DESC
        """
        
        # In a real implementation, this would execute the query via workflow
        # For now, return sample data structure
        logger.info(f"Retrieving active ASINs for last {time_range_days} days")
        
        return [
            {
                'asin': 'SAMPLE_ASIN',
                'uniqueUsers': 0,
                'impressions': 0,
                'clicks': 0,
                'conversions': 0,
                'lastSeen': end_date.isoformat()
            }
        ]
        
    async def get_execution_results(
        self,
        instance_id: str,
        execution_id: str,
        user_id: str,
        user_token: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Retrieve execution results from S3
        
        Args:
            instance_id: AMC instance ID
            execution_id: Execution ID
            user_id: User identifier
            user_token: User's auth token
            
        Returns:
            Execution results including S3 location and data preview
        """
        try:
            # Get execution details
            endpoint = AMCAPIEndpoints.EXECUTION_DETAIL.format(
                instance_id=instance_id,
                execution_id=execution_id
            )
            
            response = self.api_client.get(
                endpoint,
                user_id,
                user_token
            )
            
            result = {
                'executionId': execution_id,
                'status': response.get('status'),
                'completedAt': response.get('completedAt'),
                's3Location': response.get('outputLocation'),
                'rowCount': response.get('rowCount', 0),
                'sizeBytes': response.get('sizeBytes', 0)
            }
            
            # If execution is complete and S3 location exists, get preview
            if result['status'] == 'completed' and result['s3Location']:
                result['dataPreview'] = await self._get_s3_data_preview(
                    result['s3Location']
                )
                
            logger.info(f"Retrieved results for execution {execution_id}")
            return result
            
        except APIError as e:
            logger.error(f"Failed to retrieve execution results: {e}")
            raise
            
    async def _get_s3_data_preview(
        self,
        s3_location: str,
        preview_rows: int = 100
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get preview of data from S3
        
        Args:
            s3_location: S3 path (s3://bucket/key)
            preview_rows: Number of rows to preview
            
        Returns:
            List of preview rows or None if unavailable
        """
        if not self.s3_client:
            logger.warning("S3 client not configured, cannot retrieve preview")
            return None
            
        try:
            # Parse S3 location
            parts = s3_location.replace('s3://', '').split('/', 1)
            if len(parts) != 2:
                logger.error(f"Invalid S3 location: {s3_location}")
                return None
                
            bucket, key = parts
            
            # Get object from S3
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            
            # Read CSV data
            csv_content = response['Body'].read().decode('utf-8')
            df = pd.read_csv(StringIO(csv_content), nrows=preview_rows)
            
            # Convert to list of dicts
            preview_data = df.to_dict('records')
            
            logger.info(f"Retrieved {len(preview_data)} preview rows from S3")
            return preview_data
            
        except Exception as e:
            logger.error(f"Failed to get S3 preview: {e}")
            return None
            
    async def get_campaign_mapping(
        self,
        campaigns: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create mapping of campaign names to IDs and metadata
        
        Args:
            campaigns: List of campaign data
            
        Returns:
            Dictionary mapping campaign names to campaign info
        """
        mapping = {}
        
        for campaign in campaigns:
            # Use both current name and original name for mapping
            current_name = campaign.get('name', '')
            original_name = campaign.get('originalName', current_name)
            
            campaign_info = {
                'campaignId': campaign.get('campaignId'),
                'campaignType': campaign.get('campaignType'),
                'status': campaign.get('status'),
                'createdDate': campaign.get('createdDate'),
                'currentName': current_name,
                'originalName': original_name
            }
            
            # Map both names to the same campaign info
            if current_name:
                mapping[current_name] = campaign_info
            if original_name and original_name != current_name:
                mapping[original_name] = campaign_info
                
        logger.info(f"Created mapping for {len(mapping)} campaign names")
        return mapping