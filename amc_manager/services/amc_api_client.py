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
        access_token: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        sql_query: Optional[str] = None,
        workflow_id: Optional[str] = None,
        parameter_values: Optional[Dict[str, Any]] = None,
        output_format: str = "CSV"
    ) -> Dict[str, Any]:
        """
        Create a new AMC workflow execution
        
        Args:
            instance_id: AMC instance ID
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            sql_query: SQL query for ad-hoc execution (mutually exclusive with workflow_id)
            workflow_id: Workflow ID for saved workflow execution (mutually exclusive with sql_query)
            parameter_values: Parameter values for saved workflow execution
            output_format: Output format (CSV, JSON, PARQUET)
            
        Returns:
            Execution details including execution ID
        """
        
        # Validate that either sql_query or workflow_id is provided, but not both
        if not sql_query and not workflow_id:
            raise ValueError("Either sql_query or workflow_id must be provided")
        if sql_query and workflow_id:
            raise ValueError("Cannot provide both sql_query and workflow_id")
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
        
        # Build payload based on execution mode
        if workflow_id:
            # Saved workflow execution
            payload = {
                "workflowId": workflow_id,
                "timeWindowType": "EXPLICIT",  # Use explicit time window
                "timeWindowStart": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:%S'),
                "timeWindowEnd": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
                "timeWindowTimeZone": "America/New_York",
                "outputFormat": output_format
            }
            # Add parameter values if provided
            if parameter_values:
                payload["parameterValues"] = parameter_values
        else:
            # Ad-hoc execution with SQL query
            payload = {
                "workflow": {
                    "query": {
                        "operations": [
                            {
                                "sql": sql_query
                            }
                        ]
                    }
                },
                "timeWindowType": "EXPLICIT",  # Use explicit time window
                "timeWindowStart": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:%S'),
                "timeWindowEnd": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
                "timeWindowTimeZone": "America/New_York",
                "outputFormat": output_format
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
            
            # Check if execution ID is in Location header (common for async APIs)
            location_exec_id = None
            location_header = response.headers.get('Location', '')
            if location_header:
                logger.info(f"Location header found: {location_header}")
                # Extract execution ID from location header (e.g., /amc/reporting/{instanceId}/workflowExecutions/{executionId})
                import re
                match = re.search(r'/workflowExecutions/([^/]+)', location_header)
                if match:
                    location_exec_id = match.group(1)
                    logger.info(f"Extracted execution ID from Location header: {location_exec_id}")
            
            response_data = response.json() if response.text else {}
            logger.info(f"API Response Body: {json.dumps(response_data, indent=2)}")
            
            # Check for different possible field names in the response, prioritize Location header
            execution_id = location_exec_id or response_data.get('workflowExecutionId') or response_data.get('executionId') or response_data.get('id')
            
            # Accept both 200 and 202 status codes for async operations
            if response.status_code in [200, 202]:
                if execution_id:
                    logger.info(f"Created execution: {execution_id}")
                    return {
                        "success": True,
                        "executionId": execution_id,
                        "status": response_data.get('status', 'PENDING'),
                        "outputLocation": output_location
                    }
                else:
                    # Log all fields in response to debug
                    logger.warning(f"No execution ID found in response. Available fields: {list(response_data.keys())}")
                    logger.warning(f"Full response: {json.dumps(response_data, indent=2)}")
                    
                    # Try to use any ID-like field
                    for key in ['workflowExecutionId', 'executionId', 'id', 'execution_id', 'workflowId']:
                        if key in response_data:
                            logger.info(f"Using {key} as execution ID: {response_data[key]}")
                            return {
                                "success": True,
                                "executionId": response_data[key],
                                "status": response_data.get('status', 'PENDING'),
                                "outputLocation": output_location
                            }
                    
                    return {
                        "success": False,
                        "error": "No execution ID found in API response"
                    }
            else:
                error_msg = response_data.get('message') or response_data.get('details') or f'API Error: {response.status_code}'
                logger.error(f"Failed to create execution: Status {response.status_code}, Response: {response_data}")
                logger.error(f"Response text: {response.text}")
                
                # Check if this is a "workflow not found" error - check both error_msg and full response
                error_str = str(response_data).lower()
                if (response.status_code == 404 or 
                    "does not exist" in str(error_msg).lower() or 
                    "not found" in str(error_msg).lower() or
                    "does not exist" in error_str or
                    "not found" in error_str):
                    # Raise an exception for workflow not found so it can be caught and handled
                    logger.info(f"Detected workflow not found error, raising ValueError for upstream handling")
                    raise ValueError(f"Workflow not found: {error_msg}")
                
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except ValueError as e:
            # Re-raise ValueError (workflow not found) so it can be caught upstream
            raise
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
    
    def download_and_parse_csv(self, csv_url: str) -> Dict[str, Any]:
        """
        Download and parse a CSV file from a URL
        
        Args:
            csv_url: URL to download the CSV from
            
        Returns:
            Dict with parsed CSV data
        """
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
            
            # Convert rows to list of objects with column names as keys
            data_objects = []
            for row in rows:
                row_object = {}
                for i, header in enumerate(headers):
                    row_object[header] = row[i] if i < len(row) else None
                data_objects.append(row_object)
            
            # Convert to our format with column metadata
            columns = [{"name": header, "type": "string"} for header in headers]
            
            return {
                "success": True,
                "columns": columns,
                "rows": rows,  # Keep raw rows for backwards compatibility
                "rowCount": len(rows),
                "columnCount": len(columns),
                "data": data_objects,  # Use objects with column names as keys
                "metadata": {
                    "rowCount": len(rows),
                    "columnCount": len(columns),
                    "dataSizeBytes": len(csv_content.encode('utf-8'))
                }
            }
            
        except Exception as e:
            logger.error(f"Error downloading and parsing CSV: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_executions(
        self,
        instance_id: str,
        access_token: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        limit: int = 50,
        next_token: Optional[str] = None,
        workflow_id: Optional[str] = None,
        min_creation_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List workflow executions for an AMC instance
        
        Args:
            instance_id: AMC instance ID
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            limit: Maximum number of executions to return
            next_token: Token for pagination
            workflow_id: Optional workflow ID to filter executions
            min_creation_time: Optional minimum creation time (ISO 8601)
            
        Returns:
            List of executions
        """
        # Use /workflowExecutions endpoint for listing execution history
        url = f"{self.base_url}/amc/reporting/{instance_id}/workflowExecutions"
        
        headers = {
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-MarketplaceId': marketplace_id,
            'Amazon-Advertising-API-AdvertiserId': entity_id
        }
        
        # Set up query parameters
        params = {
            'limit': limit
        }
        
        # Add optional parameters if provided
        if next_token:
            params['nextToken'] = next_token
        
        # Amazon requires either workflowId or minCreationTime
        if workflow_id:
            params['workflowId'] = workflow_id
        elif min_creation_time:
            params['minCreationTime'] = min_creation_time
        else:
            # Default to last 7 days if neither provided
            from datetime import datetime, timedelta
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            # Format as required by AMC API: yyyy-MM-dd'T'HH:mm:ss (no 'Z')
            params['minCreationTime'] = seven_days_ago.strftime('%Y-%m-%dT%H:%M:%S')
        
        logger.info(f"Listing executions for instance {instance_id}")
        logger.info(f"Request URL: {url}")
        logger.info(f"Query params: {params}")
        logger.info(f"Entity ID being used: {entity_id}")
        logger.info(f"Marketplace ID being used: {marketplace_id}")
        logger.info(f"Token preview: {access_token[:30]}..." if len(access_token) > 30 else f"Token: {access_token}")
        
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )
            
            response_data = response.json() if response.text else {}
            logger.info(f"List executions response: Status {response.status_code}")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "executions": response_data.get('executions', []),
                    "nextToken": response_data.get('nextToken')
                }
            else:
                logger.error(f"Failed to list executions: Status {response.status_code}, Response: {response_data}")
                error_message = response_data.get('message') or response_data.get('details') or f'API Error: {response.status_code}'
                
                # Include status code in error for better handling
                if response.status_code == 403:
                    error_message = f"Status 403, Response: {response_data}"
                
                return {
                    "success": False,
                    "error": error_message,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error listing executions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_workflows(
        self,
        instance_id: str,
        access_token: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        limit: int = 50,
        next_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List workflow definitions for an AMC instance
        
        Args:
            instance_id: AMC instance ID
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            limit: Maximum number of workflows to return
            next_token: Token for pagination
            
        Returns:
            List of workflow definitions
        """
        url = f"{self.base_url}/amc/reporting/{instance_id}/workflows"
        
        headers = {
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-MarketplaceId': marketplace_id,
            'Amazon-Advertising-API-AdvertiserId': entity_id
        }
        
        params = {
            'limit': limit
        }
        
        if next_token:
            params['nextToken'] = next_token
        
        logger.info(f"Listing workflows for instance {instance_id}")
        
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )
            
            response_data = response.json() if response.text else {}
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "workflows": response_data.get('workflows', []),
                    "nextToken": response_data.get('nextToken')
                }
            else:
                logger.error(f"Failed to list workflows: Status {response.status_code}, Response: {response_data}")
                return {
                    "success": False,
                    "error": response_data.get('message', f'API Error: {response.status_code}')
                }
                
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_workflow(
        self,
        instance_id: str,
        workflow_id: str,
        sql_query: str,
        access_token: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        distinct_user_count_column: Optional[str] = None,
        filtered_metrics_discriminator_column: Optional[str] = None,
        filtered_reason_column: Optional[str] = None,
        input_parameters: Optional[List[Dict[str, Any]]] = None,
        output_format: str = "CSV"
    ) -> Dict[str, Any]:
        """
        Create a workflow definition in AMC
        
        Args:
            instance_id: AMC instance ID
            workflow_id: Unique workflow identifier (alphanumeric + .-_)
            sql_query: SQL query for the workflow
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            distinct_user_count_column: Column name for distinct user counts
            filtered_metrics_discriminator_column: Column name for filtered metrics
            filtered_reason_column: Column name for filter reasons
            input_parameters: List of parameter definitions
            
        Returns:
            Success status and response data
        """
        url = f"{self.base_url}/amc/reporting/{instance_id}/workflows"
        
        headers = {
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-MarketplaceId': marketplace_id,
            'Amazon-Advertising-API-AdvertiserId': entity_id,
            'Content-Type': 'application/json'
        }
        
        # Build request body
        body = {
            'workflowId': workflow_id,
            'sqlQuery': sql_query,
            'outputFormat': output_format
        }
        
        # Add optional aggregation threshold columns
        if distinct_user_count_column:
            body['distinctUserCountColumn'] = distinct_user_count_column
        if filtered_metrics_discriminator_column:
            body['filteredMetricsDiscriminatorColumn'] = filtered_metrics_discriminator_column
        if filtered_reason_column:
            body['filteredReasonColumn'] = filtered_reason_column
        if input_parameters:
            body['inputParameters'] = input_parameters
        
        logger.info(f"Creating workflow {workflow_id} in instance {instance_id}")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=body,
                timeout=30
            )
            
            response_data = response.json() if response.text else {}
            
            if response.status_code == 200:
                logger.info(f"Successfully created workflow {workflow_id}")
                return {
                    "success": True,
                    "workflowId": workflow_id,
                    "data": response_data
                }
            else:
                logger.error(f"Failed to create workflow: Status {response.status_code}, Response: {response_data}")
                return {
                    "success": False,
                    "error": response_data.get('message', f'API Error: {response.status_code}')
                }
                
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_workflow(
        self,
        instance_id: str,
        workflow_id: str,
        sql_query: str,
        access_token: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        distinct_user_count_column: Optional[str] = None,
        filtered_metrics_discriminator_column: Optional[str] = None,
        filtered_reason_column: Optional[str] = None,
        input_parameters: Optional[List[Dict[str, Any]]] = None,
        output_format: str = "CSV"
    ) -> Dict[str, Any]:
        """
        Update an existing workflow definition in AMC
        
        Args:
            instance_id: AMC instance ID
            workflow_id: Workflow identifier to update
            sql_query: Updated SQL query
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            distinct_user_count_column: Column name for distinct user counts
            filtered_metrics_discriminator_column: Column name for filtered metrics
            filtered_reason_column: Column name for filter reasons
            input_parameters: List of parameter definitions
            
        Returns:
            Success status and response data
        """
        url = f"{self.base_url}/amc/reporting/{instance_id}/workflows/{workflow_id}"
        
        headers = {
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-MarketplaceId': marketplace_id,
            'Amazon-Advertising-API-AdvertiserId': entity_id,
            'Content-Type': 'application/json'
        }
        
        # Build request body (workflowId is required for PUT)
        body = {
            'workflowId': workflow_id,
            'sqlQuery': sql_query,
            'outputFormat': output_format
        }
        
        # Add optional aggregation threshold columns
        if distinct_user_count_column:
            body['distinctUserCountColumn'] = distinct_user_count_column
        if filtered_metrics_discriminator_column:
            body['filteredMetricsDiscriminatorColumn'] = filtered_metrics_discriminator_column
        if filtered_reason_column:
            body['filteredReasonColumn'] = filtered_reason_column
        if input_parameters:
            body['inputParameters'] = input_parameters
        
        logger.info(f"Updating workflow {workflow_id} in instance {instance_id}")
        
        try:
            response = requests.put(
                url,
                headers=headers,
                json=body,
                timeout=30
            )
            
            response_data = response.json() if response.text else {}
            
            if response.status_code == 200:
                logger.info(f"Successfully updated workflow {workflow_id}")
                return {
                    "success": True,
                    "workflowId": workflow_id,
                    "data": response_data
                }
            else:
                logger.error(f"Failed to update workflow: Status {response.status_code}, Response: {response_data}")
                return {
                    "success": False,
                    "error": response_data.get('message', f'API Error: {response.status_code}')
                }
                
        except Exception as e:
            logger.error(f"Error updating workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_workflow(
        self,
        instance_id: str,
        workflow_id: str,
        access_token: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER"
    ) -> Dict[str, Any]:
        """
        Delete a workflow definition from AMC
        
        Args:
            instance_id: AMC instance ID
            workflow_id: Workflow identifier to delete
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            
        Returns:
            Success status
        """
        url = f"{self.base_url}/amc/reporting/{instance_id}/workflows/{workflow_id}"
        
        headers = {
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-MarketplaceId': marketplace_id,
            'Amazon-Advertising-API-AdvertiserId': entity_id
        }
        
        logger.info(f"Deleting workflow {workflow_id} from instance {instance_id}")
        
        try:
            response = requests.delete(
                url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200 or response.status_code == 204:
                logger.info(f"Successfully deleted workflow {workflow_id}")
                return {
                    "success": True,
                    "workflowId": workflow_id
                }
            else:
                response_data = response.json() if response.text else {}
                logger.error(f"Failed to delete workflow: Status {response.status_code}, Response: {response_data}")
                return {
                    "success": False,
                    "error": response_data.get('message', f'API Error: {response.status_code}')
                }
                
        except Exception as e:
            logger.error(f"Error deleting workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_workflow(
        self,
        instance_id: str,
        workflow_id: str,
        access_token: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER"
    ) -> Dict[str, Any]:
        """
        Get details of a specific workflow definition
        
        Args:
            instance_id: AMC instance ID
            workflow_id: Workflow identifier
            access_token: Amazon OAuth access token
            entity_id: Advertiser entity ID
            marketplace_id: Amazon marketplace ID
            
        Returns:
            Workflow details
        """
        url = f"{self.base_url}/amc/reporting/{instance_id}/workflows/{workflow_id}"
        
        headers = {
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-MarketplaceId': marketplace_id,
            'Amazon-Advertising-API-AdvertiserId': entity_id
        }
        
        logger.info(f"Getting workflow {workflow_id} from instance {instance_id}")
        
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )
            
            response_data = response.json() if response.text else {}
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "workflow": response_data
                }
            else:
                logger.error(f"Failed to get workflow: Status {response.status_code}, Response: {response_data}")
                return {
                    "success": False,
                    "error": response_data.get('message', f'API Error: {response.status_code}')
                }
                
        except Exception as e:
            logger.error(f"Error getting workflow: {e}")
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