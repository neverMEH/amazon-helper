"""
AMC API Client for real query execution
"""
import logging
import time
from typing import Dict, Any, Optional
import requests
from datetime import datetime

from ..config.settings import settings

logger = logging.getLogger(__name__)


class AMCAPIClient:
    """Client for Amazon Marketing Cloud API operations"""
    
    def __init__(self):
        self.base_url = "https://advertising-api.amazon.com"
    
    def create_workflow_execution(
        self,
        instance_id: str,
        sql_query: str,
        access_token: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        output_format: str = "CSV"
    ) -> Dict[str, Any]:
        """
        Create a new AMC workflow execution
        
        Args:
            instance_id: AMC instance ID
            sql_query: SQL query to execute
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            output_format: Output format (CSV, JSON, PARQUET)
            
        Returns:
            Execution details including execution ID
        """
        url = f"{self.base_url}/amc/workflowExecutions"
        
        headers = {
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-MarketplaceId': marketplace_id,
            'Amazon-Advertising-API-AdvertiserId': entity_id,
            'Content-Type': 'application/json'
        }
        
        # Debug: Log authorization header to verify format
        logger.info(f"Authorization header: Bearer {access_token[:20]}..." if len(str(access_token)) > 20 else f"Short token: {access_token}")
        
        # Generate output location (in real implementation, this would be an S3 bucket)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_location = f"s3://amc-results/{instance_id}/{timestamp}/"
        
        payload = {
            "instanceId": instance_id,
            "sqlQuery": sql_query,
            "outputLocation": output_location,
            "dataFormat": output_format,
            "workflowName": f"query_{timestamp}"
        }
        
        logger.info(f"Creating AMC workflow execution for instance {instance_id}")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response_data = response.json() if response.text else {}
            
            if response.status_code == 200 and response_data.get('executionId'):
                logger.info(f"Created execution: {response_data['executionId']}")
                return {
                    "success": True,
                    "executionId": response_data['executionId'],
                    "status": "PENDING",
                    "outputLocation": output_location
                }
            else:
                logger.error(f"Failed to create execution: Status {response.status_code}, Response: {response_data}")
                return {
                    "success": False,
                    "error": response_data.get('message', f'API Error: {response.status_code}')
                }
                
        except Exception as e:
            logger.error(f"Error creating workflow execution: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_execution_status(
        self,
        execution_id: str,
        access_token: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER"
    ) -> Dict[str, Any]:
        """
        Get the status of an AMC workflow execution
        
        Args:
            execution_id: AMC execution ID
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            
        Returns:
            Execution status details
        """
        url = f"{self.base_url}/amc/workflowExecutions/{execution_id}"
        
        headers = {
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-MarketplaceId': marketplace_id,
            'Amazon-Advertising-API-AdvertiserId': entity_id
        }
        
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )
            
            response_data = response.json() if response.text else {}
            
            if response.status_code != 200:
                logger.error(f"Failed to get execution status: Status {response.status_code}, Response: {response_data}")
                return {
                    "success": False,
                    "error": response_data.get('message', f'API Error: {response.status_code}')
                }
            
            # Map AMC status to our status
            amc_status = response_data.get('status', 'UNKNOWN')
            status_map = {
                'PENDING': 'pending',
                'RUNNING': 'running',
                'SUCCEEDED': 'completed',
                'FAILED': 'failed',
                'CANCELLED': 'failed'
            }
            
            return {
                "success": True,
                "executionId": execution_id,
                "status": status_map.get(amc_status, 'running'),
                "amcStatus": amc_status,
                "progress": self._calculate_progress(amc_status),
                "startTime": response_data.get('startTime'),
                "endTime": response_data.get('endTime'),
                "outputLocation": response_data.get('outputLocation'),
                "error": response_data.get('failureReason')
            }
            
        except Exception as e:
            logger.error(f"Error getting execution status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_execution_results(
        self,
        execution_id: str,
        access_token: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER"
    ) -> Dict[str, Any]:
        """
        Get the results of a completed AMC workflow execution
        
        Args:
            execution_id: AMC execution ID
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            
        Returns:
            Query results
        """
        # First check if execution is complete
        status = self.get_execution_status(
            execution_id, access_token, entity_id, marketplace_id
        )
        
        if not status.get('success'):
            return status
            
        if status.get('status') != 'completed':
            return {
                "success": False,
                "error": f"Execution not complete. Status: {status.get('status')}"
            }
        
        # Get results from output location
        # In a real implementation, this would download from S3
        output_location = status.get('outputLocation')
        
        try:
            # For now, return a structure that matches what we expect
            # In production, this would parse the actual results from S3
            return {
                "success": True,
                "executionId": execution_id,
                "outputLocation": output_location,
                "resultUrl": f"{output_location}results.csv",
                "metadata": {
                    "rowCount": 0,
                    "columnCount": 0,
                    "dataSizeBytes": 0,
                    "queryRuntime": 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting execution results: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_progress(self, amc_status: str) -> int:
        """Calculate progress percentage based on AMC status"""
        progress_map = {
            'PENDING': 10,
            'RUNNING': 50,
            'SUCCEEDED': 100,
            'FAILED': 100,
            'CANCELLED': 100
        }
        return progress_map.get(amc_status, 0)


# Singleton instance
amc_api_client = AMCAPIClient()