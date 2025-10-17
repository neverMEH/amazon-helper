"""
Snowflake Integration Service

Handles uploading execution results to Snowflake data warehouse.
Supports both password and key-pair authentication.
Uses UPSERT (MERGE INTO) to prevent duplicate data.
"""

import json
import pandas as pd
import snowflake.connector
from snowflake.connector import DictCursor
from snowflake.connector.pandas_tools import write_pandas
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import re
import uuid
from cryptography.hazmat.primitives import serialization
import base64

from ..services.db_service import DatabaseService, with_connection_retry
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class SnowflakeService(DatabaseService):
    """Service for managing Snowflake data warehouse integration"""

    def __init__(self):
        super().__init__()

    def _detect_date_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Detect the primary date column in DataFrame for UPSERT key

        Priority:
        1. Columns with 'date' in name (date, event_date, purchase_date)
        2. Columns with 'week' in name (week, week_start, week_ending)
        3. Columns with 'month' in name (month, month_start)
        4. Columns with 'period' or 'time' in name
        5. Any datetime64 dtype column

        Args:
            df: DataFrame to analyze

        Returns:
            Column name or None if no date column found
        """
        date_patterns = [
            r'.*date.*',
            r'.*week.*',
            r'.*month.*',
            r'.*period.*',
            r'.*day.*',
            r'.*time.*'
        ]

        # Check for pattern matches (case-insensitive)
        for pattern in date_patterns:
            for col in df.columns:
                if re.match(pattern, str(col), re.IGNORECASE):
                    logger.info(f"Detected date column by pattern '{pattern}': {col}")
                    return col

        # Check for datetime types
        for col_name, dtype in df.dtypes.items():
            if 'datetime' in str(dtype):
                logger.info(f"Detected date column by dtype: {col_name} ({dtype})")
                return col_name

        logger.warning("No date column detected in DataFrame")
        return None

    @with_connection_retry
    def get_user_snowflake_config(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get active Snowflake configuration for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Snowflake configuration or None if not found
        """
        try:
            response = self.client.table('snowflake_configurations')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .single()\
                .execute()
                
            if response.data:
                return response.data
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Snowflake config for user {user_id}: {e}")
            return None

    @with_connection_retry
    def create_snowflake_config(self, config_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Create a new Snowflake configuration
        
        Args:
            config_data: Configuration data including:
                - account_identifier: Snowflake account identifier
                - warehouse: Snowflake warehouse name
                - database: Snowflake database name
                - schema: Snowflake schema name
                - role: Snowflake role (optional)
                - username: Username for password auth
                - password: Password for password auth (will be encrypted)
                - private_key: Private key for key-pair auth (will be encrypted)
            user_id: User ID creating the configuration
            
        Returns:
            Created Snowflake configuration
        """
        try:
            # Encrypt sensitive data
            encrypted_data = self._encrypt_sensitive_data(config_data)
            
            # Prepare data for insertion
            insert_data = {
                'user_id': user_id,
                'account_identifier': config_data['account_identifier'],
                'warehouse': config_data['warehouse'],
                'database': config_data['database'],
                'schema': config_data['schema'],
                'role': config_data.get('role'),
                'username': config_data.get('username'),
                'password_encrypted': encrypted_data.get('password_encrypted'),
                'private_key_encrypted': encrypted_data.get('private_key_encrypted'),
                'is_active': True,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = self.client.table('snowflake_configurations').insert(insert_data).execute()
            
            if response.data:
                logger.info(f"Created Snowflake configuration for user {user_id}")
                return response.data[0]
            else:
                raise Exception("Failed to create Snowflake configuration")
                
        except Exception as e:
            logger.error(f"Error creating Snowflake configuration: {e}")
            raise

    def _encrypt_sensitive_data(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive data (password, private key)
        In production, use proper encryption libraries like cryptography
        """
        encrypted_data = {}
        
        if 'password' in config_data and config_data['password']:
            # Simple base64 encoding for demo - use proper encryption in production
            encrypted_data['password_encrypted'] = base64.b64encode(
                config_data['password'].encode()
            ).decode()
            
        if 'private_key' in config_data and config_data['private_key']:
            # Simple base64 encoding for demo - use proper encryption in production
            encrypted_data['private_key_encrypted'] = base64.b64encode(
                config_data['private_key'].encode()
            ).decode()
            
        return encrypted_data

    def _decrypt_sensitive_data(self, encrypted_password: str = None, encrypted_key: str = None) -> Dict[str, str]:
        """
        Decrypt sensitive data
        """
        decrypted_data = {}
        
        if encrypted_password:
            decrypted_data['password'] = base64.b64decode(encrypted_password.encode()).decode()
            
        if encrypted_key:
            decrypted_data['private_key'] = base64.b64decode(encrypted_key.encode()).decode()
            
        return decrypted_data

    def _get_snowflake_connection(self, config: Dict[str, Any]) -> snowflake.connector.SnowflakeConnection:
        """
        Create Snowflake connection using the provided configuration
        
        Args:
            config: Snowflake configuration
            
        Returns:
            Snowflake connection
        """
        try:
            # Decrypt sensitive data
            decrypted_data = self._decrypt_sensitive_data(
                config.get('password_encrypted'),
                config.get('private_key_encrypted')
            )
            
            # Build connection parameters
            conn_params = {
                'account': config['account_identifier'],
                'warehouse': config['warehouse'],
                'database': config['database'],
                'schema': config['schema'],
            }
            
            # Add role if provided
            if config.get('role'):
                conn_params['role'] = config['role']
            
            # Use key-pair authentication if private key is available
            if decrypted_data.get('private_key'):
                # Parse private key
                private_key = serialization.load_pem_private_key(
                    decrypted_data['private_key'].encode(),
                    password=None
                )
                conn_params['private_key'] = private_key
            else:
                # Use password authentication
                conn_params['user'] = config['username']
                conn_params['password'] = decrypted_data['password']
            
            # Create connection
            connection = snowflake.connector.connect(**conn_params)
            logger.info(f"Successfully connected to Snowflake account: {config['account_identifier']}")
            return connection
            
        except Exception as e:
            logger.error(f"Error connecting to Snowflake: {e}")
            raise

    def upload_execution_results(
        self,
        execution_id: str,
        results: Dict[str, Any],
        table_name: str,
        user_id: str,
        week_start: str = None
    ) -> Dict[str, Any]:
        """
        Upload execution results to Snowflake

        Args:
            execution_id: Execution ID
            results: Execution results with columns and rows
            table_name: Target table name in Snowflake
            user_id: User ID for configuration lookup
            week_start: Week start date for this execution (YYYY-MM-DD format)

        Returns:
            Upload result with status and details
        """
        try:
            # Get user's Snowflake configuration
            config = self.get_user_snowflake_config(user_id)
            if not config:
                raise Exception("No active Snowflake configuration found for user")

            # Update execution status to uploading
            self._update_execution_snowflake_status(execution_id, 'uploading')

            # Create Snowflake connection
            connection = self._get_snowflake_connection(config)

            try:
                # Prepare data for upload
                columns = results.get('columns', [])
                rows = results.get('rows', [])

                if not columns or not rows:
                    raise Exception("No data to upload")

                # Create DataFrame
                df = pd.DataFrame(rows, columns=[col['name'] for col in columns])

                # Add metadata columns
                df['execution_id'] = execution_id
                df['uploaded_at'] = datetime.utcnow()
                df['user_id'] = user_id

                # Add week_start column if provided (for template executions)
                if week_start:
                    df['week_start'] = week_start
                    logger.info(f"Adding week_start column with value: {week_start}")
                
                # Create table if it doesn't exist
                full_table_name = f"{config['database']}.{config['schema']}.{table_name}"
                self._create_table_if_not_exists(connection, full_table_name, df)
                
                # Upload data
                self._upload_dataframe_to_snowflake(connection, df, full_table_name)
                
                # Update execution status to completed
                self._update_execution_snowflake_status(
                    execution_id, 
                    'completed', 
                    row_count=len(df)
                )
                
                logger.info(f"Successfully uploaded {len(df)} rows to Snowflake table {full_table_name}")
                
                return {
                    'success': True,
                    'table_name': full_table_name,
                    'row_count': len(df),
                    'uploaded_at': datetime.utcnow().isoformat()
                }
                
            finally:
                connection.close()
                
        except Exception as e:
            logger.error(f"Error uploading results to Snowflake: {e}")
            # Update execution status to failed
            self._update_execution_snowflake_status(execution_id, 'failed', error_message=str(e))
            
            return {
                'success': False,
                'error': str(e)
            }

    def _map_dtype_to_snowflake(self, dtype) -> str:
        """Map pandas dtype to Snowflake type"""
        dtype_str = str(dtype)
        if dtype_str == 'object':
            return 'VARCHAR(16777216)'  # Max VARCHAR size
        elif 'int' in dtype_str:
            return 'INTEGER'
        elif 'float' in dtype_str:
            return 'FLOAT'
        elif dtype_str == 'bool':
            return 'BOOLEAN'
        elif 'datetime' in dtype_str:
            return 'TIMESTAMP_NTZ'
        else:
            return 'VARCHAR(16777216)'

    def _create_table_if_not_exists(
        self,
        connection: snowflake.connector.SnowflakeConnection,
        table_name: str,
        df: pd.DataFrame
    ):
        """
        Create table in Snowflake if it doesn't exist with dynamic primary key
        based on detected date column
        """
        try:
            cursor = connection.cursor()

            # Detect date column for composite primary key
            date_column = self._detect_date_column(df)

            # Generate column definitions
            columns = []
            for col_name, dtype in df.dtypes.items():
                snowflake_type = self._map_dtype_to_snowflake(dtype)
                columns.append(f'"{col_name}" {snowflake_type}')

            # Add composite primary key based on detected date column
            if date_column and date_column in df.columns:
                pk_clause = f'PRIMARY KEY ("execution_id", "{date_column}")'
                logger.info(f"Creating table with composite PK: (execution_id, {date_column})")
            else:
                pk_clause = 'PRIMARY KEY ("execution_id", "uploaded_at")'
                logger.info("Creating table with PK: (execution_id, uploaded_at)")

            columns.append(pk_clause)

            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(columns)}
            )
            """

            cursor.execute(create_sql)
            cursor.close()

            logger.info(f"Created/verified table {table_name}")

        except Exception as e:
            logger.error(f"Error creating table {table_name}: {e}")
            raise

    def _generate_merge_sql(
        self,
        target_table: str,
        source_table: str,
        df: pd.DataFrame,
        date_column: Optional[str] = None
    ) -> str:
        """
        Generate MERGE INTO SQL with dynamic join condition

        Join keys:
        - Always: execution_id
        - If date_column exists: AND date_column
        - Fallback: execution_id + uploaded_at
        """
        columns = [f'"{col}"' for col in df.columns]

        # Build ON clause (join condition)
        if date_column and date_column in df.columns:
            # Use execution_id + date_column as composite key
            on_clause = f'''
                target."execution_id" = source."execution_id"
                AND target."{date_column}" = source."{date_column}"
            '''
            logger.info(f"Using composite key for UPSERT: (execution_id, {date_column})")
        else:
            # Fallback: use execution_id + uploaded_at
            on_clause = f'''
                target."execution_id" = source."execution_id"
                AND target."uploaded_at" = source."uploaded_at"
            '''
            logger.warning("No date column found, using (execution_id, uploaded_at) as key")

        # Build UPDATE SET clause (all columns except keys)
        exclude_from_update = {'execution_id', date_column, 'uploaded_at'} if date_column else {'execution_id', 'uploaded_at'}
        update_cols = [col for col in df.columns if col not in exclude_from_update]
        update_set = ', '.join([
            f'target."{col}" = source."{col}"' for col in update_cols
        ])

        # Build INSERT clause
        insert_cols = ', '.join(columns)
        insert_vals = ', '.join([f'source."{col}"' for col in df.columns])

        merge_sql = f"""
        MERGE INTO {target_table} AS target
        USING {source_table} AS source
        ON {on_clause}
        WHEN MATCHED THEN
            UPDATE SET {update_set}
        WHEN NOT MATCHED THEN
            INSERT ({insert_cols})
            VALUES ({insert_vals})
        """

        return merge_sql

    def _upload_dataframe_to_snowflake(
        self,
        connection: snowflake.connector.SnowflakeConnection,
        df: pd.DataFrame,
        table_name: str
    ):
        """
        UPSERT DataFrame to Snowflake using MERGE INTO

        This prevents duplicate data by upserting based on execution_id + date column
        """
        try:
            cursor = connection.cursor()

            # Auto-detect date column
            date_column = self._detect_date_column(df)
            logger.info(f"Using date column for UPSERT: {date_column or 'None (fallback to uploaded_at)'}")

            # Create temp table with unique name
            temp_table = f"TEMP_{uuid.uuid4().hex[:8].upper()}"

            try:
                # Generate CREATE TEMP TABLE statement
                temp_columns = []
                for col_name, dtype in df.dtypes.items():
                    snowflake_type = self._map_dtype_to_snowflake(dtype)
                    temp_columns.append(f'"{col_name}" {snowflake_type}')

                create_temp_sql = f"""
                CREATE TEMPORARY TABLE {temp_table} (
                    {', '.join(temp_columns)}
                )
                """

                cursor.execute(create_temp_sql)
                logger.info(f"Created temporary table: {temp_table}")

                # Insert data into temp table using write_pandas
                success, nchunks, nrows, _ = write_pandas(
                    connection,
                    df,
                    temp_table,
                    auto_create_table=False,
                    quote_identifiers=True
                )

                logger.info(f"Loaded {nrows} rows into temp table {temp_table}")

                # Generate and execute MERGE statement
                merge_sql = self._generate_merge_sql(
                    target_table=table_name,
                    source_table=temp_table,
                    df=df,
                    date_column=date_column
                )

                logger.info(f"Executing UPSERT to {table_name}")
                cursor.execute(merge_sql)

                # Get merge statistics
                merge_result = cursor.fetchone()
                if merge_result:
                    logger.info(f"MERGE completed: {merge_result}")

                logger.info(f"Successfully UPSERTed {len(df)} rows to {table_name}")

            finally:
                # Clean up temporary table
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
                    logger.info(f"Dropped temporary table: {temp_table}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp table {temp_table}: {cleanup_error}")

                cursor.close()

        except Exception as e:
            logger.error(f"Error upserting DataFrame to Snowflake: {e}")
            raise

    @with_connection_retry
    def _update_execution_snowflake_status(
        self, 
        execution_id: str, 
        status: str, 
        row_count: int = None, 
        error_message: str = None
    ):
        """
        Update Snowflake status for an execution
        """
        try:
            update_data = {
                'snowflake_status': status,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if status == 'completed':
                update_data['snowflake_uploaded_at'] = datetime.utcnow().isoformat()
                if row_count:
                    update_data['snowflake_row_count'] = row_count
            elif status == 'failed':
                update_data['snowflake_error_message'] = error_message
            
            response = self.client.table('workflow_executions')\
                .update(update_data)\
                .eq('execution_id', execution_id)\
                .execute()
                
            if response.data:
                logger.info(f"Updated execution {execution_id} Snowflake status to {status}")
            else:
                logger.warning(f"No execution found with ID {execution_id}")
                
        except Exception as e:
            logger.error(f"Error updating execution Snowflake status: {e}")

    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test Snowflake connection with provided configuration
        
        Args:
            config: Snowflake configuration to test
            
        Returns:
            Test result with success status and details
        """
        try:
            connection = self._get_snowflake_connection(config)
            
            # Test query
            cursor = connection.cursor()
            cursor.execute("SELECT CURRENT_VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            connection.close()
            
            return {
                'success': True,
                'message': f'Successfully connected to Snowflake version {version}',
                'version': version
            }
            
        except Exception as e:
            logger.error(f"Snowflake connection test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @with_connection_retry
    def list_user_tables(self, user_id: str, database: str = None, schema: str = None) -> List[Dict[str, Any]]:
        """
        List tables in user's Snowflake database/schema
        
        Args:
            user_id: User ID
            database: Database name (optional, uses config default)
            schema: Schema name (optional, uses config default)
            
        Returns:
            List of tables with metadata
        """
        try:
            config = self.get_user_snowflake_config(user_id)
            if not config:
                raise Exception("No active Snowflake configuration found for user")
            
            connection = self._get_snowflake_connection(config)
            
            try:
                cursor = connection.cursor(DictCursor)
                
                # Use provided database/schema or config defaults
                target_database = database or config['database']
                target_schema = schema or config['schema']
                
                query = f"""
                SELECT 
                    TABLE_NAME,
                    TABLE_TYPE,
                    ROW_COUNT,
                    BYTES,
                    CREATED,
                    LAST_ALTERED
                FROM {target_database}.INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = '{target_schema}'
                ORDER BY TABLE_NAME
                """
                
                cursor.execute(query)
                tables = cursor.fetchall()
                cursor.close()
                
                return [
                    {
                        'name': table['TABLE_NAME'],
                        'type': table['TABLE_TYPE'],
                        'row_count': table['ROW_COUNT'],
                        'size_bytes': table['BYTES'],
                        'created': table['CREATED'],
                        'last_altered': table['LAST_ALTERED']
                    }
                    for table in tables
                ]
                
            finally:
                connection.close()
                
        except Exception as e:
            logger.error(f"Error listing Snowflake tables: {e}")
            return []

    @with_connection_retry
    def update_snowflake_config(self, config_id: str, update_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Update Snowflake configuration
        
        Args:
            config_id: Configuration ID
            update_data: Fields to update
            user_id: User ID for authorization
            
        Returns:
            Updated Snowflake configuration
        """
        try:
            # Encrypt sensitive data if provided
            if 'password' in update_data or 'private_key' in update_data:
                encrypted_data = self._encrypt_sensitive_data(update_data)
                update_data.update(encrypted_data)
                # Remove plain text sensitive data
                update_data.pop('password', None)
                update_data.pop('private_key', None)
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            response = self.client.table('snowflake_configurations')\
                .update(update_data)\
                .eq('id', config_id)\
                .eq('user_id', user_id)\
                .execute()
                
            if response.data:
                logger.info(f"Updated Snowflake configuration: {config_id}")
                return response.data[0]
            else:
                raise Exception("Configuration not found or access denied")
                
        except Exception as e:
            logger.error(f"Error updating Snowflake configuration: {e}")
            raise

    @with_connection_retry
    def delete_snowflake_config(self, config_id: str, user_id: str) -> bool:
        """
        Delete Snowflake configuration
        
        Args:
            config_id: Configuration ID
            user_id: User ID for authorization
            
        Returns:
            True if deleted successfully
        """
        try:
            response = self.client.table('snowflake_configurations')\
                .delete()\
                .eq('id', config_id)\
                .eq('user_id', user_id)\
                .execute()
                
            if response.data:
                logger.info(f"Deleted Snowflake configuration: {config_id}")
                return True
            else:
                raise Exception("Configuration not found or access denied")
                
        except Exception as e:
            logger.error(f"Error deleting Snowflake configuration: {e}")
            raise
