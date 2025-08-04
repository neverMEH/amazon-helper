"""
AMC API Client for real query execution
"""
import csv
import io
import json
import logging
import time
from typing import Dict, Any, Optional, List
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
        url = f"{self.base_url}/amc/reporting/{instance_id}/workflowExecutions"
        
        headers = {
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-MarketplaceId': marketplace_id,
            'Amazon-Advertising-API-AdvertiserId': entity_id,
            'Content-Type': 'application/json'
        }
        
        # Debug: Log authorization header to verify format
        logger.info(f"Authorization header: Bearer {access_token[:20]}..." if len(str(access_token)) > 20 else f"Short token: {access_token}")
        logger.info(f"Token starts with 'Atza|': {access_token.startswith('Atza|') if access_token else 'No token'}")
        logger.info(f"Full headers being sent: {headers}")
        logger.info(f"Request URL: {url}")
        
        # Generate output location (in real implementation, this would be an S3 bucket)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_location = f"s3://amc-results/{instance_id}/{timestamp}/"
        
        # For ad hoc execution, we need to provide a workflow object with the SQL query
        # Based on AMC documentation, we can either:
        # 1. Execute a saved workflow using workflowId
        # 2. Execute an ad hoc workflow by providing the SQL in the workflow object
        payload = {
            "workflow": {
                "sqlQuery": sql_query  # SQL query for ad hoc execution
            },
            "timeWindowType": "EXPLICIT",  # Use explicit time window
            "timeWindowStart": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
            "timeWindowEnd": datetime.utcnow().isoformat(),
            "timeWindowTimeZone": "America/New_York"
        }
        
        logger.info(f"Creating AMC workflow execution for instance {instance_id}")
        logger.info(f"Request payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Log response details for debugging
            logger.info(f"API Response Status: {response.status_code}")
            logger.info(f"API Response Headers: {dict(response.headers)}")
            
            response_data = response.json() if response.text else {}
            logger.info(f"API Response Body: {json.dumps(response_data, indent=2)}")
            
            # Check for different possible field names in the response
            execution_id = response_data.get('workflowExecutionId') or response_data.get('executionId') or response_data.get('id')
            
            if response.status_code == 200 and execution_id:
                logger.info(f"Created execution: {execution_id}")
                return {
                    "success": True,
                    "executionId": execution_id,
                    "status": response_data.get('status', 'PENDING'),
                    "outputLocation": output_location
                }
            else:
                logger.error(f"Failed to create execution: Status {response.status_code}, Response: {response_data}")
                logger.error(f"Response text: {response.text}")
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
        marketplace_id: str = "ATVPDKIKX0DER",
        instance_id: str = None
    ) -> Dict[str, Any]:
        """
        Get the status of an AMC workflow execution
        
        Args:
            execution_id: AMC execution ID
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            instance_id: AMC instance ID (required)
            
        Returns:
            Execution status details
        """
        if not instance_id:
            return {"success": False, "error": "instance_id is required"}
        
        url = f"{self.base_url}/amc/reporting/{instance_id}/workflowExecutions/{execution_id}"
        
        headers = {
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-MarketplaceId': marketplace_id,
            'Amazon-Advertising-API-AdvertiserId': entity_id
        }
        
        logger.info(f"Checking execution status for {execution_id} on instance {instance_id}")
        logger.info(f"Status URL: {url}")
        
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )
            
            response_data = response.json() if response.text else {}
            logger.info(f"Status check response: Status {response.status_code}, Body: {json.dumps(response_data, indent=2)}")
            
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
        marketplace_id: str = "ATVPDKIKX0DER",
        instance_id: str = None
    ) -> Dict[str, Any]:
        """
        Get the results of a completed AMC workflow execution
        
        Args:
            execution_id: AMC execution ID
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            instance_id: AMC instance ID (required)
            
        Returns:
            Query results
        """
        if not instance_id:
            return {"success": False, "error": "instance_id is required"}
            
        # First check if execution is complete
        status = self.get_execution_status(
            execution_id, access_token, entity_id, marketplace_id, instance_id
        )
        
        if not status.get('success'):
            return status
            
        if status.get('status') != 'completed':
            return {
                "success": False,
                "error": f"Execution not complete. Status: {status.get('status')}"
            }
        
        # Get download URLs
        download_urls_response = self.get_download_urls(
            execution_id, access_token, entity_id, marketplace_id, instance_id
        )
        
        if not download_urls_response.get('success'):
            return download_urls_response
        
        download_urls = download_urls_response.get('downloadUrls', [])
        if not download_urls:
            return {
                "success": False,
                "error": "No download URLs available"
            }
        
        # Download the first URL (should be the CSV results)
        csv_url = download_urls[0] if isinstance(download_urls[0], str) else download_urls[0].get('url')
        
        try:
            # Download the CSV file
            csv_response = requests.get(csv_url, timeout=60)
            if csv_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to download CSV: Status {csv_response.status_code}"
                }
            
            # Parse CSV content
            csv_content = csv_response.text
            csv_reader = csv.reader(io.StringIO(csv_content))
            
            # Get headers (first row)
            headers = next(csv_reader, [])
            
            # Get all rows
            rows = list(csv_reader)
            
            # Convert to our format with column metadata
            columns = [{"name": header, "type": "string"} for header in headers]
            
            return {
                "success": True,
                "executionId": execution_id,
                "columns": columns,
                "rows": rows,
                "rowCount": len(rows),
                "columnCount": len(columns),
                "schema": columns,  # For backward compatibility
                "data": rows,       # For backward compatibility
                "metadata": {
                    "rowCount": len(rows),
                    "columnCount": len(columns),
                    "dataSizeBytes": len(csv_content.encode('utf-8')),
                    "queryRuntime": 0  # This would come from AMC metadata
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting execution results: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_download_urls(
        self,
        execution_id: str,
        access_token: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        instance_id: str = None
    ) -> Dict[str, Any]:
        """
        Get download URLs for workflow execution results
        
        Args:
            execution_id: AMC execution ID
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            instance_id: AMC instance ID (required)
            
        Returns:
            Download URLs for the execution results
        """
        if not instance_id:
            return {"success": False, "error": "instance_id is required"}
        
        url = f"{self.base_url}/amc/reporting/{instance_id}/workflowExecutions/{execution_id}/downloadUrls"
        
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
            
            if response.status_code == 404:
                # Execution not ready for download yet
                return {
                    "success": False,
                    "error": f"Execution with ID {execution_id} is unavailable for download.",
                    "not_ready": True
                }
            
            response_data = response.json() if response.text else {}
            
            if response.status_code != 200:
                logger.error(f"Failed to get download URLs: Status {response.status_code}, Response: {response_data}")
                return {
                    "success": False,
                    "error": response_data.get('message', f'API Error: {response.status_code}')
                }
            
            # Return the download URLs
            return {
                "success": True,
                "executionId": execution_id,
                "downloadUrls": response_data.get('downloadUrls', []),
                "expires": response_data.get('expires')
            }
            
        except Exception as e:
            logger.error(f"Error getting download URLs: {e}")
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