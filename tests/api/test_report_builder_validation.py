"""
Validation and edge case tests for Report Builder API
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestReportBuilderValidation:
    """Test validation rules and edge cases"""

    def test_amc_14_month_retention_limit(self, client, mock_auth_user):
        """Test that dates beyond 14 months are rejected"""
        # Date 15 months ago
        old_date = (datetime.utcnow() - timedelta(days=450)).strftime('%Y-%m-%d')

        response = client.post(
            "/api/report-builder/validate-parameters",
            json={
                "workflow_id": "test-workflow",
                "parameters": {},
                "lookback_config": {
                    "type": "custom",
                    "start_date": old_date,
                    "end_date": datetime.utcnow().strftime('%Y-%m-%d')
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert any("14-month" in error or "retention" in error for error in data.get("errors", []))

    def test_future_dates_validation(self, client, mock_auth_user):
        """Test that future dates are rejected"""
        future_date = (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d')

        response = client.post(
            "/api/report-builder/validate-parameters",
            json={
                "workflow_id": "test-workflow",
                "parameters": {},
                "lookback_config": {
                    "type": "custom",
                    "start_date": datetime.utcnow().strftime('%Y-%m-%d'),
                    "end_date": future_date
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert any("future" in error.lower() for error in data.get("errors", []))

    def test_invalid_date_range(self, client, mock_auth_user):
        """Test that end date before start date is rejected"""
        response = client.post(
            "/api/report-builder/validate-parameters",
            json={
                "workflow_id": "test-workflow",
                "parameters": {},
                "lookback_config": {
                    "type": "custom",
                    "start_date": "2025-08-01",
                    "end_date": "2025-07-01"  # Before start date
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert any("end date" in error.lower() or "before" in error.lower()
                  for error in data.get("errors", []))

    def test_missing_required_parameters(self, client, mock_auth_user):
        """Test validation with missing required parameters"""
        response = client.post(
            "/api/report-builder/validate-parameters",
            json={
                "workflow_id": "test-workflow",
                # Missing parameters when workflow requires them
                "parameters": {},
                "lookback_config": {
                    "type": "relative",
                    "value": 7,
                    "unit": "days"
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        # Should still pass validation at this endpoint
        # Parameter requirements are checked at submission
        assert response.status_code == 200

    def test_invalid_schedule_frequency(self, client, mock_auth_user):
        """Test invalid schedule frequency values"""
        response = client.post(
            "/api/report-builder/preview-schedule",
            json={
                "workflow_id": "test-workflow",
                "instance_id": "test-instance",
                "lookback_config": {
                    "type": "relative",
                    "value": 7,
                    "unit": "days"
                },
                "schedule_config": {
                    "type": "scheduled",
                    "frequency": "invalid_frequency",  # Should be daily/weekly/monthly
                    "time": "09:00",
                    "timezone": "UTC"
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422  # Validation error

    def test_maximum_backfill_periods(self, client, mock_auth_user):
        """Test maximum backfill period limits"""
        response = client.post(
            "/api/report-builder/preview-schedule",
            json={
                "workflow_id": "test-workflow",
                "instance_id": "test-instance",
                "lookback_config": {
                    "type": "custom",
                    "start_date": "2020-01-01",  # 5+ years of data
                    "end_date": "2025-09-17"
                },
                "schedule_config": {
                    "type": "backfill_with_schedule",
                    "frequency": "daily",
                    "backfill_config": {
                        "enabled": True,
                        "periods": 2000,  # Excessive periods
                        "segmentation": "daily"
                    }
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should include warnings about large operation
        assert "backfill_preview" in data
        if data["backfill_preview"]["total_periods"] > 365:
            # Should have warning about large backfill
            assert float(data["backfill_preview"]["estimated_duration"].split()[0]) > 10  # hours

    def test_invalid_timezone(self, client, mock_auth_user):
        """Test invalid timezone handling"""
        response = client.post(
            "/api/report-builder/preview-schedule",
            json={
                "workflow_id": "test-workflow",
                "instance_id": "test-instance",
                "lookback_config": {
                    "type": "relative",
                    "value": 7,
                    "unit": "days"
                },
                "schedule_config": {
                    "type": "scheduled",
                    "frequency": "daily",
                    "time": "09:00",
                    "timezone": "Invalid/Timezone"
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        # Should either reject or default to UTC
        assert response.status_code in [200, 422]

    def test_parameter_injection_prevention(self, client, mock_auth_user):
        """Test SQL injection prevention in parameters"""
        response = client.post(
            "/api/report-builder/validate-parameters",
            json={
                "workflow_id": "test-workflow",
                "parameters": {
                    "campaigns": ["'; DROP TABLE campaigns; --"],
                    "custom_value": "1 OR 1=1"
                },
                "lookback_config": {
                    "type": "relative",
                    "value": 7,
                    "unit": "days"
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        # Parameters should be safely handled

    def test_extremely_large_parameter_lists(self, client, mock_auth_user):
        """Test handling of very large parameter lists"""
        # Generate 10,000 campaign IDs
        large_campaign_list = [f"campaign_{i}" for i in range(10000)]

        response = client.post(
            "/api/report-builder/validate-parameters",
            json={
                "workflow_id": "test-workflow",
                "parameters": {
                    "campaigns": large_campaign_list
                },
                "lookback_config": {
                    "type": "relative",
                    "value": 7,
                    "unit": "days"
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should handle or warn about large parameter lists
        if "warnings" in data:
            assert any("large" in w.lower() or "limit" in w.lower() for w in data["warnings"])

    def test_null_and_empty_values(self, client, mock_auth_user):
        """Test handling of null and empty values"""
        test_cases = [
            # Null workflow_id
            {
                "workflow_id": None,
                "parameters": {},
                "lookback_config": {"type": "relative", "value": 7, "unit": "days"}
            },
            # Empty string workflow_id
            {
                "workflow_id": "",
                "parameters": {},
                "lookback_config": {"type": "relative", "value": 7, "unit": "days"}
            },
            # Null parameters
            {
                "workflow_id": "test",
                "parameters": None,
                "lookback_config": {"type": "relative", "value": 7, "unit": "days"}
            },
            # Missing lookback_config
            {
                "workflow_id": "test",
                "parameters": {}
            }
        ]

        for test_case in test_cases:
            response = client.post(
                "/api/report-builder/validate-parameters",
                json=test_case,
                headers={"Authorization": "Bearer test-token"}
            )
            # Should handle gracefully (400 or 422)
            assert response.status_code in [400, 422]

    def test_boundary_values(self, client, mock_auth_user):
        """Test boundary values for various fields"""
        test_cases = [
            # Zero lookback days
            {
                "lookback_config": {"type": "relative", "value": 0, "unit": "days"},
                "expected_error": True
            },
            # Negative lookback days
            {
                "lookback_config": {"type": "relative", "value": -7, "unit": "days"},
                "expected_error": True
            },
            # Maximum allowed lookback (14 months = ~420 days)
            {
                "lookback_config": {"type": "relative", "value": 420, "unit": "days"},
                "expected_error": False
            },
            # Just over maximum
            {
                "lookback_config": {"type": "relative", "value": 450, "unit": "days"},
                "expected_error": True
            }
        ]

        for test_case in test_cases:
            response = client.post(
                "/api/report-builder/validate-parameters",
                json={
                    "workflow_id": "test-workflow",
                    "parameters": {},
                    "lookback_config": test_case["lookback_config"]
                },
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            if test_case["expected_error"]:
                assert data["valid"] is False
            else:
                # Might have warnings but should be valid
                assert "errors" not in data or len(data["errors"]) == 0

    def test_concurrent_submission_prevention(self, client, mock_auth_user):
        """Test prevention of duplicate concurrent submissions"""
        submission_data = {
            "workflow_id": "test-workflow",
            "instance_id": "test-instance",
            "parameters": {},
            "lookback_config": {"type": "relative", "value": 7, "unit": "days"},
            "schedule_config": {"type": "once"}
        }

        # First submission
        response1 = client.post(
            "/api/report-builder/submit",
            json=submission_data,
            headers={"Authorization": "Bearer test-token"}
        )
        assert response1.status_code == 200

        # Immediate duplicate submission (should be rejected or queued)
        response2 = client.post(
            "/api/report-builder/submit",
            json=submission_data,
            headers={"Authorization": "Bearer test-token"}
        )

        # Should either queue or reject duplicate
        assert response2.status_code in [200, 409]  # 409 Conflict for duplicate

    def test_special_characters_in_parameters(self, client, mock_auth_user):
        """Test handling of special characters in parameters"""
        special_chars_test = {
            "workflow_id": "test-workflow",
            "parameters": {
                "name": "Test & Report <with> 'quotes' \"double\" and \\backslash",
                "description": "Line1\nLine2\rLine3\tTabbed",
                "unicode": "测试 тест ทดสอบ 🚀"
            },
            "lookback_config": {"type": "relative", "value": 7, "unit": "days"}
        }

        response = client.post(
            "/api/report-builder/validate-parameters",
            json=special_chars_test,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        # Should handle special characters properly

    def test_malformed_json_handling(self, client, mock_auth_user):
        """Test handling of malformed JSON requests"""
        # Send malformed JSON
        response = client.post(
            "/api/report-builder/validate-parameters",
            data='{"workflow_id": "test", "parameters": {invalid json}',
            headers={
                "Authorization": "Bearer test-token",
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 422  # Unprocessable entity

    def test_resource_limits(self, client, mock_auth_user):
        """Test resource limits and quotas"""
        # Test creating many schedules for same workflow
        for i in range(10):
            response = client.post(
                "/api/report-builder/submit",
                json={
                    "workflow_id": "test-workflow",
                    "instance_id": f"instance-{i}",
                    "parameters": {},
                    "lookback_config": {"type": "relative", "value": 7, "unit": "days"},
                    "schedule_config": {
                        "type": "scheduled",
                        "frequency": "daily",
                        "time": f"{i:02d}:00"
                    }
                },
                headers={"Authorization": "Bearer test-token"}
            )

            if i < 5:
                # First few should succeed
                assert response.status_code == 200
            # System may implement rate limiting or quotas

    def test_invalid_workflow_id(self, client, mock_auth_user):
        """Test handling of non-existent workflow IDs"""
        response = client.post(
            "/api/report-builder/validate-parameters",
            json={
                "workflow_id": "non-existent-workflow-12345",
                "parameters": {},
                "lookback_config": {"type": "relative", "value": 7, "unit": "days"}
            },
            headers={"Authorization": "Bearer test-token"}
        )

        # Should handle gracefully
        assert response.status_code in [200, 404]

    def test_invalid_instance_id(self, client, mock_auth_user):
        """Test handling of non-existent instance IDs"""
        response = client.post(
            "/api/report-builder/submit",
            json={
                "workflow_id": "test-workflow",
                "instance_id": "non-existent-instance-12345",
                "parameters": {},
                "lookback_config": {"type": "relative", "value": 7, "unit": "days"},
                "schedule_config": {"type": "once"}
            },
            headers={"Authorization": "Bearer test-token"}
        )

        # Should reject with appropriate error
        assert response.status_code in [400, 404]