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
        
        # Extract date parameters from parameter_values
        # Check for various date parameter formats
        time_window_start = None
        time_window_end = None
        
        if parameter_values:
            # Look for date parameters in various formats
            for start_key in ['startDate', 'start_date', 'timeWindowStart', 'beginDate']:
                if start_key in parameter_values:
                    time_window_start = parameter_values[start_key]
                    logger.info(f"Found start date parameter '{start_key}': {time_window_start}")
                    break
            
            for end_key in ['endDate', 'end_date', 'timeWindowEnd', 'finishDate']:
                if end_key in parameter_values:
                    time_window_end = parameter_values[end_key]
                    logger.info(f"Found end date parameter '{end_key}': {time_window_end}")
                    break
        
        # Parse and format dates for AMC API
        if time_window_start:
            try:
                # Parse the date string (handle various formats)
                if 'T' in str(time_window_start):
                    # Already in ISO format, just ensure no timezone
                    time_window_start = str(time_window_start).replace('Z', '').split('+')[0].split('.')[0]
                else:
                    # Date only format (YYYY-MM-DD), add time component
                    time_window_start = f"{time_window_start}T00:00:00"
                logger.info(f"Formatted start date for AMC: {time_window_start}")
            except Exception as e:
                logger.warning(f"Error parsing start date: {e}, using default")
                time_window_start = None
        
        if time_window_end:
            try:
                # Parse the date string (handle various formats)
                if 'T' in str(time_window_end):
                    # Already in ISO format, just ensure no timezone
                    time_window_end = str(time_window_end).replace('Z', '').split('+')[0].split('.')[0]
                else:
                    # Date only format (YYYY-MM-DD), add time component (end of day)
                    time_window_end = f"{time_window_end}T23:59:59"
                logger.info(f"Formatted end date for AMC: {time_window_end}")
            except Exception as e:
                logger.warning(f"Error parsing end date: {e}, using default")
                time_window_end = None
        
        # Use default dates if not provided (14-21 days ago to account for AMC data lag)
        if not time_window_start or not time_window_end:
            logger.warning("Date parameters not found or invalid, using default date range (14-21 days ago for AMC data lag)")
            from datetime import timedelta
            # AMC has a 14-day data lag, so we need to query older data
            end_date = datetime.utcnow() - timedelta(days=14)  # 14 days ago
            start_date = end_date - timedelta(days=7)  # 21 days ago
            time_window_start = start_date.replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:%S')
            time_window_end = end_date.replace(hour=23, minute=59, second=59, microsecond=0).strftime('%Y-%m-%dT%H:%M:%S')
            logger.info(f"Using default date range (accounting for AMC data lag): {time_window_start} to {time_window_end}")
        
        # Build payload based on execution mode
        if workflow_id:
            # Saved workflow execution
            payload = {
                "workflowId": workflow_id,
                "timeWindowType": "EXPLICIT",  # Use explicit time window
                "timeWindowStart": time_window_start,
                "timeWindowEnd": time_window_end,
                "timeWindowTimeZone": "America/New_York",
                "outputFormat": output_format
            }
            # Add parameter values if provided (for workflow parameters, not time window)
            if parameter_values:
                # Create a copy without date parameters (they're handled by timeWindow fields)
                workflow_params = {k: v for k, v in parameter_values.items() 
                                 if k not in ['startDate', 'start_date', 'endDate', 'end_date', 
                                            'timeWindowStart', 'timeWindowEnd', 'date_range_preset']}
                if workflow_params:
                    payload["parameterValues"] = workflow_params
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
                "timeWindowStart": time_window_start,
                "timeWindowEnd": time_window_end,
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
                
                # Extract detailed error information for SQL compilation errors
                error_details = None
                if response.status_code == 400 and 'details' in response_data:
                    details_str = str(response_data.get('details', ''))
                    
                    # Check if this is a SQL compilation error
                    if 'unable to compile' in details_str.lower() or 'sql query was invalid' in details_str.lower():
                        # Parse the error message for specific SQL issues
                        error_details = {
                            'failureReason': 'SQL Query Compilation Failed',
                            'errorCode': response_data.get('code', 'AMC-SQL-COMPILE'),
                            'errorMessage': details_str,
                            'validationErrors': [],
                            'queryValidation': details_str
                        }
                        
                        # Extract specific error location if present (e.g., "From line 38, column 10...")
                        import re
                        line_match = re.search(r'From line (\d+), column (\d+) to line (\d+), column (\d+):', details_str)
                        if line_match:
                            error_details['validationErrors'].append(
                                f"Error at line {line_match.group(1)}, column {line_match.group(2)}: Check SQL syntax"
                            )
                        
                        # Extract object not found errors
                        object_match = re.search(r"Object '([^']+)' not found", details_str)
                        if object_match:
                            error_details['validationErrors'].append(
                                f"Table or column '{object_match.group(1)}' does not exist in AMC schema"
                            )
                
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
                    "error": error_msg,
                    "errorDetails": error_details
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
            
            # Extract detailed error information
            failure_reason = response_data.get('failureReason')
            validation_errors = response_data.get('validationErrors', [])
            error_details = None
            
            if failure_reason or validation_errors:
                error_details = {
                    "failureReason": failure_reason,
                    "validationErrors": validation_errors,
                    "errorCode": response_data.get('errorCode'),
                    "errorMessage": response_data.get('errorMessage'),
                    "errorDetails": response_data.get('errorDetails'),
                    "queryValidation": response_data.get('queryValidation')
                }
                
                # Log detailed error for debugging
                logger.error(f"Execution {execution_id} failed with details: {json.dumps(error_details, indent=2)}")
            
            return {
                "success": True,
                "executionId": execution_id,
                "status": status_map.get(amc_status, 'running'),
                "amcStatus": amc_status,
                "progress": self._calculate_progress(amc_status),
                "startTime": response_data.get('startTime'),
                "endTime": response_data.get('endTime'),
                "outputLocation": response_data.get('outputLocation'),
                "error": failure_reason,
                "errorDetails": error_details
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
        logger.info(f"Downloading CSV from S3 for execution {execution_id}")
        
        try:
            # Download the CSV file
            csv_response = requests.get(csv_url, timeout=60)
            if csv_response.status_code != 200:
                logger.error(f"Failed to download CSV: Status {csv_response.status_code}")
                return {
                    "success": False,
                    "error": f"Failed to download CSV: Status {csv_response.status_code}"
                }
            
            logger.info(f"Successfully downloaded CSV, size: {len(csv_response.text)} bytes")
            
            # Parse CSV content
            csv_content = csv_response.text
            
            # Log first few lines for debugging (without sensitive data)
            if len(csv_content) > 0:
                preview_lines = csv_content.split('\n')[:5]
                logger.info(f"CSV preview (first 5 lines): {preview_lines}")
            
            csv_reader = csv.reader(io.StringIO(csv_content))
            
            # Get headers (first row)
            headers = next(csv_reader, [])
            
            # Get all rows
            rows = list(csv_reader)
            
            logger.info(f"Parsed CSV: {len(headers)} columns, {len(rows)} rows")
            
            # Check for empty results
            if len(rows) == 0:
                logger.warning("CSV file contains headers but no data rows - query returned empty results")
                logger.info(f"Headers found: {headers}")
                logger.info("Possible causes: 1) Date range has no data, 2) Query filters too restrictive, 3) AMC data lag")
            
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
            logger.info(f"Starting CSV download from: {csv_url[:100]}...")  # Log first 100 chars of URL
            
            # Download the CSV file
            csv_response = requests.get(csv_url, timeout=60)
            if csv_response.status_code != 200:
                logger.error(f"Failed to download CSV: Status {csv_response.status_code}")
                return {
                    "success": False,
                    "error": f"Failed to download CSV: Status {csv_response.status_code}"
                }
            
            # Parse CSV content
            csv_content = csv_response.text
            content_length = len(csv_content)
            logger.info(f"Downloaded CSV content: {content_length} bytes")
            
            # Log first few lines for debugging (without sensitive data)
            if content_length > 0:
                preview_lines = csv_content.split('\n')[:3]
                logger.info(f"CSV preview (first 3 lines): {preview_lines}")
            
            csv_reader = csv.reader(io.StringIO(csv_content))
            
            # Get headers (first row)
            headers = next(csv_reader, [])
            
            # Get all rows
            rows = list(csv_reader)
            
            # Log parsing results
            logger.info(f"Parsed CSV: {len(headers)} columns, {len(rows)} data rows")
            if len(headers) > 0:
                logger.info(f"Column headers: {headers}")
            
            # Check for empty results
            if len(rows) == 0:
                logger.warning("CSV file contains headers but no data rows - query returned empty results")
                logger.info("Common causes of empty AMC results:")
                logger.info("1. Date range mismatch - check that timeWindowStart/End match your data availability")
                logger.info("2. Query filters too restrictive - verify WHERE clauses")
                logger.info("3. AMC data lag - recent data may not be available yet (24-48 hour lag)")
                logger.info("4. Timezone issues - AMC uses America/New_York by default")
                logger.info("5. Parameter substitution issues - check that parameters are correctly replaced in SQL")
            
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
                    "dataSizeBytes": len(csv_content.encode('utf-8')),
                    "isEmpty": len(rows) == 0
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
        
        logger.info(f"Getting download URLs for execution {execution_id} on instance {instance_id}")
        
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
            download_urls = response_data.get('downloadUrls', [])
            logger.info(f"Got {len(download_urls)} download URLs for execution {execution_id}")
            return {
                "success": True,
                "executionId": execution_id,
                "downloadUrls": download_urls,
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