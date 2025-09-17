"""
Comprehensive integration tests for Report Builder API endpoints.
Tests full workflow from validation through submission with various scenarios.
"""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, patch, AsyncMock
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI

from amc_manager.schemas.report_builder import (
    LookbackConfig,
    SegmentationConfig,
    BackfillConfig,
    ScheduleConfig,
    ReportBuilderValidateRequest,
    ReportBuilderPreviewRequest,
    ReportBuilderSubmitRequest,
)


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    from main_supabase import app as main_app
    return main_app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "name": "Test User"
    }


class TestReportBuilderIntegration:
    """Integration tests for complete Report Builder workflows."""

    @pytest.fixture
    def sample_workflow(self):
        """Sample workflow for testing."""
        return {
            "id": "wf-123",
            "name": "Sales Performance Report",
            "sql_query": """
                SELECT
                    campaign_id,
                    SUM(impressions) as total_impressions,
                    SUM(clicks) as total_clicks
                FROM impressions
                WHERE date >= {{start_date}}
                    AND date <= {{end_date}}
                    AND campaign_id IN ({{campaigns}})
                GROUP BY campaign_id
            """,
            "instance_id": "inst-123",
            "user_id": "user-123"
        }

    @pytest.fixture
    def sample_instance(self):
        """Sample AMC instance for testing."""
        return {
            "id": "inst-uuid",
            "instance_id": "amctest123",
            "instance_name": "Test AMC Instance",
            "account_id": "acc-123"
        }

    def test_complete_workflow_once_execution(self, client: TestClient, mock_auth_user, sample_workflow, sample_instance):
        """Test complete workflow for one-time execution."""
        # Step 1: Validate parameters
        validate_request = {
            "workflow_id": sample_workflow["id"],
            "parameters": {
                "campaigns": ["camp1", "camp2"],
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            },
            "lookback_config": {
                "type": "relative",
                "value": 30,
                "unit": "days"
            }
        }

        response = client.post("/api/report-builder/validate-parameters", json=validate_request)
        assert response.status_code == 200
        validation = response.json()
        assert validation["valid"] is True
        assert len(validation.get("warnings", [])) == 0

        # Step 2: Preview schedule
        preview_request = {
            "workflow_id": sample_workflow["id"],
            "instance_id": sample_instance["instance_id"],
            "lookback_config": validate_request["lookback_config"],
            "schedule_config": {
                "type": "once"
            }
        }

        response = client.post("/api/report-builder/preview-schedule", json=preview_request)
        assert response.status_code == 200
        preview = response.json()
        assert "schedule_preview" in preview
        assert preview["schedule_preview"]["frequency_description"] == "One-time execution"

        # Step 3: Review configuration
        review_request = {
            "workflow_id": sample_workflow["id"],
            "instance_id": sample_instance["instance_id"],
            "parameters": validate_request["parameters"],
            "lookback_config": validate_request["lookback_config"],
            "schedule_config": preview_request["schedule_config"]
        }

        response = client.post("/api/report-builder/review", json=review_request)
        assert response.status_code == 200
        review = response.json()
        assert review["validation_status"]["passed"] is True
        assert "sql_preview" in review

        # Step 4: Submit configuration
        submit_request = review_request

        with patch("amc_manager.api.report_builder.create_workflow_execution") as mock_execute:
            mock_execute.return_value = {"execution_id": "exec-123", "status": "RUNNING"}

            response = client.post("/api/report-builder/submit", json=submit_request)
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert "execution_id" in result

    def test_complete_workflow_scheduled_with_backfill(self, client: TestClient, mock_auth_user, sample_workflow):
        """Test complete workflow for scheduled execution with backfill."""
        # Prepare complex configuration
        submit_request = {
            "workflow_id": sample_workflow["id"],
            "instance_id": "amctest123",
            "parameters": {
                "campaigns": ["camp1", "camp2", "camp3"],
                "asins": ["B001", "B002", "B003", "B004", "B005"]
            },
            "lookback_config": {
                "type": "relative",
                "value": 7,
                "unit": "days"
            },
            "schedule_config": {
                "type": "backfill_with_schedule",
                "frequency": "daily",
                "time": "09:00",
                "timezone": "America/Los_Angeles",
                "backfill_config": {
                    "enabled": True,
                    "periods": 52,
                    "segmentation": "weekly"
                }
            }
        }

        # Test validation with large parameters
        validate_response = client.post(
            "/api/report-builder/validate-parameters",
            json={
                "workflow_id": submit_request["workflow_id"],
                "parameters": submit_request["parameters"],
                "lookback_config": submit_request["lookback_config"]
            }
        )
        assert validate_response.status_code == 200
        assert validate_response.json()["valid"] is True

        # Test preview with backfill
        preview_response = client.post(
            "/api/report-builder/preview-schedule",
            json={
                "workflow_id": submit_request["workflow_id"],
                "instance_id": submit_request["instance_id"],
                "lookback_config": submit_request["lookback_config"],
                "schedule_config": submit_request["schedule_config"]
            }
        )
        assert preview_response.status_code == 200
        preview = preview_response.json()
        assert "backfill_preview" in preview
        assert preview["backfill_preview"]["total_periods"] == 52
        assert len(preview["backfill_preview"]["segments"]) > 0

        # Test submission
        with patch("amc_manager.api.report_builder.create_schedule") as mock_schedule:
            with patch("amc_manager.api.report_builder.create_data_collection") as mock_collection:
                mock_schedule.return_value = {"schedule_id": "sched-123"}
                mock_collection.return_value = {"collection_id": "coll-123"}

                response = client.post("/api/report-builder/submit", json=submit_request)
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                assert "schedule_id" in result
                assert "collection_id" in result

    def test_custom_date_range_validation(self, client: TestClient, mock_auth_user):
        """Test validation with custom date ranges."""
        # Test valid custom range
        validate_request = {
            "workflow_id": "wf-123",
            "parameters": {},
            "lookback_config": {
                "type": "custom",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            }
        }

        response = client.post("/api/report-builder/validate-parameters", json=validate_request)
        assert response.status_code == 200
        assert response.json()["valid"] is True

        # Test invalid range (end before start)
        validate_request["lookback_config"]["start_date"] = "2024-01-31"
        validate_request["lookback_config"]["end_date"] = "2024-01-01"

        response = client.post("/api/report-builder/validate-parameters", json=validate_request)
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert any("end date" in err.lower() for err in result["errors"])

        # Test range exceeding AMC limit (14 months)
        validate_request["lookback_config"]["start_date"] = "2023-01-01"
        validate_request["lookback_config"]["end_date"] = "2024-06-01"

        response = client.post("/api/report-builder/validate-parameters", json=validate_request)
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert any("14" in err for err in result["errors"])

    def test_schedule_frequency_variations(self, client: TestClient, mock_auth_user):
        """Test different schedule frequency configurations."""
        base_request = {
            "workflow_id": "wf-123",
            "instance_id": "amctest123",
            "lookback_config": {
                "type": "relative",
                "value": 7,
                "unit": "days"
            }
        }

        # Test daily schedule
        daily_request = {
            **base_request,
            "schedule_config": {
                "type": "scheduled",
                "frequency": "daily",
                "time": "09:00",
                "timezone": "America/New_York"
            }
        }

        response = client.post("/api/report-builder/preview-schedule", json=daily_request)
        assert response.status_code == 200
        preview = response.json()
        assert "daily" in preview["schedule_preview"]["frequency_description"].lower()

        # Test weekly schedule
        weekly_request = {
            **base_request,
            "schedule_config": {
                "type": "scheduled",
                "frequency": "weekly",
                "time": "10:00",
                "timezone": "Europe/London",
                "day_of_week": 1  # Monday
            }
        }

        response = client.post("/api/report-builder/preview-schedule", json=weekly_request)
        assert response.status_code == 200
        preview = response.json()
        assert "weekly" in preview["schedule_preview"]["frequency_description"].lower()
        assert "monday" in preview["schedule_preview"]["frequency_description"].lower()

        # Test monthly schedule
        monthly_request = {
            **base_request,
            "schedule_config": {
                "type": "scheduled",
                "frequency": "monthly",
                "time": "00:00",
                "timezone": "Asia/Tokyo",
                "day_of_month": 15
            }
        }

        response = client.post("/api/report-builder/preview-schedule", json=monthly_request)
        assert response.status_code == 200
        preview = response.json()
        assert "monthly" in preview["schedule_preview"]["frequency_description"].lower()
        assert "15" in preview["schedule_preview"]["frequency_description"]

    def test_backfill_segmentation_options(self, client: TestClient, mock_auth_user):
        """Test different backfill segmentation configurations."""
        base_request = {
            "workflow_id": "wf-123",
            "instance_id": "amctest123",
            "lookback_config": {
                "type": "relative",
                "value": 7,
                "unit": "days"
            }
        }

        # Test daily segmentation
        daily_backfill = {
            **base_request,
            "schedule_config": {
                "type": "backfill_with_schedule",
                "frequency": "daily",
                "time": "02:00",
                "timezone": "America/Los_Angeles",
                "backfill_config": {
                    "enabled": True,
                    "periods": 30,
                    "segmentation": "daily"
                }
            }
        }

        response = client.post("/api/report-builder/preview-schedule", json=daily_backfill)
        assert response.status_code == 200
        preview = response.json()
        assert preview["backfill_preview"]["total_periods"] == 30
        assert len(preview["backfill_preview"]["segments"]) == 30

        # Test weekly segmentation
        weekly_backfill = {
            **base_request,
            "schedule_config": {
                "type": "backfill_with_schedule",
                "frequency": "weekly",
                "time": "00:00",
                "timezone": "UTC",
                "backfill_config": {
                    "enabled": True,
                    "periods": 52,
                    "segmentation": "weekly"
                }
            }
        }

        response = client.post("/api/report-builder/preview-schedule", json=weekly_backfill)
        assert response.status_code == 200
        preview = response.json()
        assert preview["backfill_preview"]["total_periods"] == 52
        assert "estimated_duration" in preview["backfill_preview"]

        # Test monthly segmentation
        monthly_backfill = {
            **base_request,
            "schedule_config": {
                "type": "backfill_with_schedule",
                "frequency": "monthly",
                "time": "23:59",
                "timezone": "Europe/Paris",
                "backfill_config": {
                    "enabled": True,
                    "periods": 12,
                    "segmentation": "monthly"
                }
            }
        }

        response = client.post("/api/report-builder/preview-schedule", json=monthly_backfill)
        assert response.status_code == 200
        preview = response.json()
        assert preview["backfill_preview"]["total_periods"] == 12
        assert preview["backfill_preview"]["parallel_executions"] <= 5

    def test_parameter_injection_and_sql_preview(self, client: TestClient, mock_auth_user):
        """Test parameter injection in SQL preview."""
        review_request = {
            "workflow_id": "wf-123",
            "instance_id": "amctest123",
            "parameters": {
                "campaigns": ["CAMP001", "CAMP002", "CAMP003"],
                "asins": ["B001TEST", "B002TEST"],
                "brand": "TestBrand"
            },
            "lookback_config": {
                "type": "custom",
                "start_date": "2024-01-15",
                "end_date": "2024-02-15"
            },
            "schedule_config": {
                "type": "once"
            }
        }

        response = client.post("/api/report-builder/review", json=review_request)
        assert response.status_code == 200
        review = response.json()

        sql_preview = review["sql_preview"]

        # Check date injection
        assert "2024-01-15" in sql_preview
        assert "2024-02-15" in sql_preview

        # Check campaign VALUES clause
        assert "VALUES" in sql_preview
        assert "CAMP001" in sql_preview
        assert "CAMP002" in sql_preview

        # Check ASIN injection
        assert "B001TEST" in sql_preview
        assert "B002TEST" in sql_preview

    def test_cost_estimation(self, client: TestClient, mock_auth_user):
        """Test cost estimation in preview."""
        preview_request = {
            "workflow_id": "wf-123",
            "instance_id": "amctest123",
            "lookback_config": {
                "type": "relative",
                "value": 365,  # Large lookback
                "unit": "days"
            },
            "schedule_config": {
                "type": "once"
            }
        }

        response = client.post("/api/report-builder/preview-schedule", json=preview_request)
        assert response.status_code == 200
        preview = response.json()

        if "cost_estimate" in preview:
            cost = preview["cost_estimate"]
            assert "data_scanned" in cost
            assert "estimated_cost" in cost
            assert "query_complexity" in cost
            assert cost["query_complexity"] in ["Low", "Medium", "High"]

    def test_audit_trail_creation(self, client: TestClient, mock_auth_user, mock_db):
        """Test that audit entries are created for each action."""
        workflow_id = "wf-123"

        # Mock database to track audit inserts
        audit_entries = []

        def mock_insert(table_name):
            class MockTable:
                def insert(self, data):
                    if table_name == "report_builder_audit":
                        audit_entries.append(data)
                    return self

                def execute(self):
                    return Mock(data=[{"id": "audit-123"}])

            return MockTable()

        mock_db.table = mock_insert

        # Perform actions that should create audit entries
        actions = [
            ("validate-parameters", {
                "workflow_id": workflow_id,
                "parameters": {"campaigns": ["c1"]},
                "lookback_config": {"type": "relative", "value": 7, "unit": "days"}
            }),
            ("preview-schedule", {
                "workflow_id": workflow_id,
                "instance_id": "inst-123",
                "lookback_config": {"type": "relative", "value": 7, "unit": "days"},
                "schedule_config": {"type": "once"}
            }),
            ("submit", {
                "workflow_id": workflow_id,
                "instance_id": "inst-123",
                "parameters": {"campaigns": ["c1"]},
                "lookback_config": {"type": "relative", "value": 7, "unit": "days"},
                "schedule_config": {"type": "once"}
            })
        ]

        for endpoint, data in actions:
            response = client.post(f"/api/report-builder/{endpoint}", json=data)
            assert response.status_code in [200, 201]

        # Verify audit entries were created
        assert len(audit_entries) >= len(actions)
        for entry in audit_entries:
            assert "user_id" in entry
            assert "action" in entry
            assert "workflow_id" in entry
            assert "configuration" in entry
            assert "timestamp" in entry


class TestReportBuilderErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_workflow_id(self, client: TestClient, mock_auth_user):
        """Test handling of invalid workflow ID."""
        response = client.post("/api/report-builder/validate-parameters", json={
            "workflow_id": "invalid-id",
            "parameters": {},
            "lookback_config": {"type": "relative", "value": 7, "unit": "days"}
        })
        assert response.status_code == 404

    def test_missing_required_fields(self, client: TestClient, mock_auth_user):
        """Test validation of required fields."""
        # Missing lookback_config
        response = client.post("/api/report-builder/validate-parameters", json={
            "workflow_id": "wf-123",
            "parameters": {}
        })
        assert response.status_code == 422

        # Missing schedule_config for preview
        response = client.post("/api/report-builder/preview-schedule", json={
            "workflow_id": "wf-123",
            "instance_id": "inst-123",
            "lookback_config": {"type": "relative", "value": 7, "unit": "days"}
        })
        assert response.status_code == 422

    def test_invalid_date_formats(self, client: TestClient, mock_auth_user):
        """Test handling of invalid date formats."""
        response = client.post("/api/report-builder/validate-parameters", json={
            "workflow_id": "wf-123",
            "parameters": {},
            "lookback_config": {
                "type": "custom",
                "start_date": "01/15/2024",  # Wrong format
                "end_date": "2024-02-15"
            }
        })
        assert response.status_code in [400, 422]

    def test_timezone_validation(self, client: TestClient, mock_auth_user):
        """Test timezone validation."""
        response = client.post("/api/report-builder/preview-schedule", json={
            "workflow_id": "wf-123",
            "instance_id": "inst-123",
            "lookback_config": {"type": "relative", "value": 7, "unit": "days"},
            "schedule_config": {
                "type": "scheduled",
                "frequency": "daily",
                "time": "25:00",  # Invalid time
                "timezone": "Invalid/Timezone"
            }
        })
        assert response.status_code in [400, 422]

    def test_parameter_limit_exceeded(self, client: TestClient, mock_auth_user):
        """Test handling of parameter limits."""
        # Create huge parameter list
        huge_campaigns = [f"CAMP{i:05d}" for i in range(10000)]

        response = client.post("/api/report-builder/validate-parameters", json={
            "workflow_id": "wf-123",
            "parameters": {"campaigns": huge_campaigns},
            "lookback_config": {"type": "relative", "value": 7, "unit": "days"}
        })

        result = response.json()
        if response.status_code == 200:
            # Should have warning about large parameter list
            assert len(result.get("warnings", [])) > 0
        else:
            # Or reject as too large
            assert response.status_code == 400

    def test_concurrent_submission_handling(self, client: TestClient, mock_auth_user):
        """Test handling of concurrent submissions."""
        import threading
        import time

        submission_results = []

        def submit_report():
            response = client.post("/api/report-builder/submit", json={
                "workflow_id": "wf-123",
                "instance_id": "inst-123",
                "parameters": {},
                "lookback_config": {"type": "relative", "value": 7, "unit": "days"},
                "schedule_config": {"type": "once"}
            })
            submission_results.append(response.status_code)

        # Launch multiple concurrent submissions
        threads = []
        for _ in range(5):
            t = threading.Thread(target=submit_report)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # At least one should succeed
        assert 200 in submission_results or 201 in submission_results

        # Others might be rate-limited or queued
        for status in submission_results:
            assert status in [200, 201, 429, 503]  # Success or rate-limited/busy


class TestReportBuilderPerformance:
    """Performance and load tests."""

    @pytest.mark.slow
    def test_large_backfill_performance(self, client: TestClient, mock_auth_user):
        """Test performance with large backfill request."""
        import time

        start_time = time.time()

        response = client.post("/api/report-builder/preview-schedule", json={
            "workflow_id": "wf-123",
            "instance_id": "inst-123",
            "lookback_config": {"type": "relative", "value": 7, "unit": "days"},
            "schedule_config": {
                "type": "backfill_with_schedule",
                "frequency": "daily",
                "time": "00:00",
                "timezone": "UTC",
                "backfill_config": {
                    "enabled": True,
                    "periods": 365,  # Full year
                    "segmentation": "daily"
                }
            }
        })

        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 5.0  # Should complete within 5 seconds

        preview = response.json()
        assert len(preview["backfill_preview"]["segments"]) == 365

    @pytest.mark.slow
    def test_complex_sql_preview_performance(self, client: TestClient, mock_auth_user):
        """Test SQL preview performance with complex queries."""
        import time

        # Complex parameters
        parameters = {
            "campaigns": [f"CAMP{i:04d}" for i in range(100)],
            "asins": [f"B{i:06d}" for i in range(50)],
            "brands": [f"Brand{i}" for i in range(20)],
            "categories": [f"Cat{i}" for i in range(30)]
        }

        start_time = time.time()

        response = client.post("/api/report-builder/review", json={
            "workflow_id": "wf-123",
            "instance_id": "inst-123",
            "parameters": parameters,
            "lookback_config": {"type": "relative", "value": 30, "unit": "days"},
            "schedule_config": {"type": "once"}
        })

        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 3.0  # Should complete within 3 seconds

        review = response.json()
        assert "sql_preview" in review
        assert len(review["sql_preview"]) > 0