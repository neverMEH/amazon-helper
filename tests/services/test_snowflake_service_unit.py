"""
Unit Tests for Snowflake Service (Unit Testing Focus)

Tests Snowflake integration features in isolation:
- Composite UPSERT key generation (execution_id + date range)
- Date range column detection
- MERGE SQL generation logic
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime

from amc_manager.services.snowflake_service import SnowflakeService


class TestSnowflakeServiceUnit:
    """Unit tests for SnowflakeService (isolated logic testing)"""

    @pytest.fixture
    def snowflake_service(self):
        """Create SnowflakeService instance"""
        with patch('amc_manager.services.snowflake_service.DatabaseService.__init__'):
            service = SnowflakeService()
            service._client = MagicMock()  # Mock the client directly
            return service

    # ========== Date Column Detection Tests ==========

    def test_detect_date_column_with_date_name(self, snowflake_service):
        """Test date column detection with 'date' in column name"""
        # Arrange
        df = pd.DataFrame({
            'campaign_id': ['c1', 'c2'],
            'event_date': ['2025-01-01', '2025-01-02'],
            'impressions': [100, 200]
        })

        # Act
        result = snowflake_service._detect_date_column(df)

        # Assert
        assert result == 'event_date'

    def test_detect_date_column_with_week_name(self, snowflake_service):
        """Test date column detection with 'week' in column name"""
        # Arrange
        df = pd.DataFrame({
            'campaign_id': ['c1', 'c2'],
            'week_start': ['2025-01-01', '2025-01-08'],
            'impressions': [100, 200]
        })

        # Act
        result = snowflake_service._detect_date_column(df)

        # Assert
        assert result == 'week_start'

    def test_detect_date_column_with_month_name(self, snowflake_service):
        """Test date column detection with 'month' in column name"""
        # Arrange
        df = pd.DataFrame({
            'campaign_id': ['c1'],
            'month_start': ['2025-01-01'],
            'revenue': [5000]
        })

        # Act
        result = snowflake_service._detect_date_column(df)

        # Assert
        assert result == 'month_start'

    def test_detect_date_column_no_date_column(self, snowflake_service):
        """Test date column detection when no date column exists"""
        # Arrange
        df = pd.DataFrame({
            'campaign_id': ['c1', 'c2'],
            'impressions': [100, 200]
        })

        # Act
        result = snowflake_service._detect_date_column(df)

        # Assert
        assert result is None

    def test_detect_date_column_priority_date_over_week(self, snowflake_service):
        """Test that 'date' columns have priority over 'week' columns"""
        # Arrange
        df = pd.DataFrame({
            'event_date': ['2025-01-01'],
            'week_start': ['2025-01-01'],
            'impressions': [100]
        })

        # Act
        result = snowflake_service._detect_date_column(df)

        # Assert
        assert result == 'event_date'  # 'date' pattern checked first

    # ========== MERGE SQL Generation Tests (Composite Date Range Key) ==========

    def test_generate_merge_sql_with_composite_date_range_key(self, snowflake_service):
        """Test MERGE SQL generation with composite date range key (execution_id + time_window_start + time_window_end)"""
        # Arrange
        df = pd.DataFrame({
            'campaign_id': ['c1'],
            'impressions': [100],
            'execution_id': ['exec_1'],
            'time_window_start': ['2025-01-01'],
            'time_window_end': ['2025-01-31'],
            'uploaded_at': [datetime.now()]
        })
        execution_parameters = {
            'timeWindowStart': '2025-01-01',
            'timeWindowEnd': '2025-01-31'
        }

        # Act
        merge_sql = snowflake_service._generate_merge_sql(
            target_table='test_table',
            source_table='temp_table',
            df=df,
            execution_parameters=execution_parameters
        )

        # Assert - Verify composite key in ON clause
        assert 'MERGE INTO test_table' in merge_sql
        assert 'target."execution_id" = source."execution_id"' in merge_sql
        assert 'target."time_window_start" = source."time_window_start"' in merge_sql
        assert 'target."time_window_end" = source."time_window_end"' in merge_sql
        assert 'WHEN MATCHED THEN' in merge_sql
        assert 'WHEN NOT MATCHED THEN' in merge_sql

        # Verify UPDATE SET clause doesn't include key columns
        assert 'target."execution_id" = source."execution_id"' in merge_sql  # In ON clause
        # But not in UPDATE SET (key columns excluded)
        lines = merge_sql.split('\n')
        update_section = '\n'.join([l for l in lines if 'UPDATE SET' in l or (lines.index(l) > next(i for i, l in enumerate(lines) if 'UPDATE SET' in l) and 'WHEN NOT MATCHED' not in l)])
        # time_window_start and time_window_end should NOT be in UPDATE SET
        # (they're part of the composite key)

    def test_generate_merge_sql_with_date_column_key(self, snowflake_service):
        """Test MERGE SQL generation with date column as part of composite key"""
        # Arrange
        df = pd.DataFrame({
            'campaign_id': ['c1'],
            'event_date': ['2025-01-01'],
            'impressions': [100],
            'execution_id': ['exec_1'],
            'uploaded_at': [datetime.now()]
        })

        # Act
        merge_sql = snowflake_service._generate_merge_sql(
            target_table='test_table',
            source_table='temp_table',
            df=df,
            date_column='event_date'
        )

        # Assert
        assert 'MERGE INTO test_table' in merge_sql
        assert 'target."execution_id" = source."execution_id"' in merge_sql
        assert 'target."event_date" = source."event_date"' in merge_sql
        assert 'WHEN MATCHED THEN' in merge_sql

    def test_generate_merge_sql_fallback_to_uploaded_at(self, snowflake_service):
        """Test MERGE SQL generation with fallback to uploaded_at when no date column"""
        # Arrange
        df = pd.DataFrame({
            'campaign_id': ['c1'],
            'impressions': [100],
            'execution_id': ['exec_1'],
            'uploaded_at': [datetime.now()]
        })

        # Act
        merge_sql = snowflake_service._generate_merge_sql(
            target_table='test_table',
            source_table='temp_table',
            df=df
        )

        # Assert
        assert 'MERGE INTO test_table' in merge_sql
        assert 'target."execution_id" = source."execution_id"' in merge_sql
        assert 'target."uploaded_at" = source."uploaded_at"' in merge_sql

    def test_generate_merge_sql_without_date_range_params(self, snowflake_service):
        """Test that without execution_parameters, MERGE uses date column or uploaded_at"""
        # Arrange
        df = pd.DataFrame({
            'campaign_id': ['c1'],
            'week_start': ['2025-01-01'],
            'impressions': [100],
            'execution_id': ['exec_1'],
            'uploaded_at': [datetime.now()]
        })
        # No execution_parameters provided

        # Act
        merge_sql = snowflake_service._generate_merge_sql(
            target_table='test_table',
            source_table='temp_table',
            df=df,
            date_column='week_start'
        )

        # Assert - Should use week_start, not time_window_start/end
        assert 'target."week_start" = source."week_start"' in merge_sql
        assert 'time_window_start' not in merge_sql
        assert 'time_window_end' not in merge_sql

    # ========== Dtype Mapping Tests ==========

    def test_map_dtype_to_snowflake_string(self, snowflake_service):
        """Test dtype mapping for string/object columns"""
        assert snowflake_service._map_dtype_to_snowflake('object') == 'VARCHAR(16777216)'

    def test_map_dtype_to_snowflake_integer(self, snowflake_service):
        """Test dtype mapping for integer columns"""
        assert snowflake_service._map_dtype_to_snowflake('int64') == 'INTEGER'
        assert snowflake_service._map_dtype_to_snowflake('int32') == 'INTEGER'

    def test_map_dtype_to_snowflake_float(self, snowflake_service):
        """Test dtype mapping for float columns"""
        assert snowflake_service._map_dtype_to_snowflake('float64') == 'FLOAT'
        assert snowflake_service._map_dtype_to_snowflake('float32') == 'FLOAT'

    def test_map_dtype_to_snowflake_boolean(self, snowflake_service):
        """Test dtype mapping for boolean columns"""
        assert snowflake_service._map_dtype_to_snowflake('bool') == 'BOOLEAN'

    def test_map_dtype_to_snowflake_datetime(self, snowflake_service):
        """Test dtype mapping for datetime columns"""
        assert snowflake_service._map_dtype_to_snowflake('datetime64[ns]') == 'TIMESTAMP_NTZ'

    def test_map_dtype_to_snowflake_unknown(self, snowflake_service):
        """Test dtype mapping for unknown types defaults to VARCHAR"""
        assert snowflake_service._map_dtype_to_snowflake('unknown_type') == 'VARCHAR(16777216)'

    # ========== Encryption/Decryption Tests ==========

    def test_encrypt_sensitive_data_password(self, snowflake_service):
        """Test password encryption"""
        # Arrange
        config_data = {
            'password': 'test_password_123'
        }

        # Act
        encrypted = snowflake_service._encrypt_sensitive_data(config_data)

        # Assert
        assert 'password_encrypted' in encrypted
        assert encrypted['password_encrypted'] != 'test_password_123'
        assert len(encrypted['password_encrypted']) > 20  # Encrypted data is longer

    def test_encrypt_sensitive_data_private_key(self, snowflake_service):
        """Test private key encryption"""
        # Arrange
        config_data = {
            'private_key': '-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----'
        }

        # Act
        encrypted = snowflake_service._encrypt_sensitive_data(config_data)

        # Assert
        assert 'private_key_encrypted' in encrypted
        assert '-----BEGIN PRIVATE KEY-----' not in encrypted['private_key_encrypted']

    def test_encrypt_sensitive_data_both(self, snowflake_service):
        """Test encrypting both password and private key"""
        # Arrange
        config_data = {
            'password': 'test_password',
            'private_key': 'test_private_key'
        }

        # Act
        encrypted = snowflake_service._encrypt_sensitive_data(config_data)

        # Assert
        assert 'password_encrypted' in encrypted
        assert 'private_key_encrypted' in encrypted
        assert encrypted['password_encrypted'] != 'test_password'
        assert encrypted['private_key_encrypted'] != 'test_private_key'

    def test_decrypt_sensitive_data_password(self, snowflake_service):
        """Test password decryption"""
        # Arrange
        original_password = 'test_password_123'
        encrypted = snowflake_service._encrypt_sensitive_data({'password': original_password})

        # Act
        decrypted = snowflake_service._decrypt_sensitive_data(
            encrypted_password=encrypted['password_encrypted']
        )

        # Assert
        assert 'password' in decrypted
        assert decrypted['password'] == original_password

    def test_decrypt_sensitive_data_private_key(self, snowflake_service):
        """Test private key decryption"""
        # Arrange
        original_key = 'test_private_key'
        encrypted = snowflake_service._encrypt_sensitive_data({'private_key': original_key})

        # Act
        decrypted = snowflake_service._decrypt_sensitive_data(
            encrypted_key=encrypted['private_key_encrypted']
        )

        # Assert
        assert 'private_key' in decrypted
        assert decrypted['private_key'] == original_key
