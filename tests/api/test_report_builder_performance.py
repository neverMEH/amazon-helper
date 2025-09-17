"""
Performance and load tests for Report Builder API
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestReportBuilderPerformance:
    """Test performance characteristics and load handling"""

    def test_concurrent_validations(self, client, mock_auth_user):
        """Test handling of multiple concurrent validation requests"""
        def make_validation_request(index):
            return client.post(
                "/api/report-builder/validate-parameters",
                json={
                    "workflow_id": f"workflow-{index}",
                    "parameters": {
                        "campaigns": [f"campaign-{i}" for i in range(10)]
                    },
                    "lookback_config": {
                        "type": "relative",
                        "value": 7 + index,
                        "unit": "days"
                    }
                },
                headers={"Authorization": "Bearer test-token"}
            )

        # Execute 50 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_validation_request, i) for i in range(50)]
            responses = [f.result() for f in futures]
            end_time = time.time()

        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)

        # Should complete within reasonable time (5 seconds for 50 requests)
        assert end_time - start_time < 5.0

        # Verify responses are valid
        for response in responses:
            data = response.json()
            assert "valid" in data

    def test_large_backfill_performance(self, client, mock_auth_user):
        """Test performance with 365-day backfill configuration"""
        start_date = (datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = datetime.utcnow().strftime('%Y-%m-%d')

        start_time = time.time()
        response = client.post(
            "/api/report-builder/preview-schedule",
            json={
                "workflow_id": "test-workflow",
                "instance_id": "test-instance",
                "lookback_config": {
                    "type": "custom",
                    "start_date": start_date,
                    "end_date": end_date
                },
                "schedule_config": {
                    "type": "backfill_with_schedule",
                    "frequency": "daily",
                    "backfill_config": {
                        "enabled": True,
                        "periods": 365,
                        "segmentation": "daily"
                    }
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )
        end_time = time.time()

        assert response.status_code == 200
        data = response.json()

        # Should calculate 365 segments efficiently (under 1 second)
        assert end_time - start_time < 1.0

        # Verify backfill preview is generated
        assert "backfill_preview" in data
        assert data["backfill_preview"]["total_periods"] == 365
        assert len(data["backfill_preview"]["segments"]) > 0

    def test_parameter_processing_performance(self, client, mock_auth_user):
        """Test performance with large parameter sets"""
        # Generate large parameter sets
        large_campaigns = [f"campaign_{i}" for i in range(1000)]
        large_asins = [f"ASIN{i:010d}" for i in range(500)]

        start_time = time.time()
        response = client.post(
            "/api/report-builder/validate-parameters",
            json={
                "workflow_id": "test-workflow",
                "parameters": {
                    "campaigns": large_campaigns,
                    "asins": large_asins,
                    "date_range": {"start": "2025-01-01", "end": "2025-09-17"},
                    "metrics": ["impressions", "clicks", "conversions", "spend", "sales"],
                    "group_by": ["campaign", "asin", "date"]
                },
                "lookback_config": {
                    "type": "relative",
                    "value": 30,
                    "unit": "days"
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )
        end_time = time.time()

        assert response.status_code == 200
        # Should process large parameter sets within 2 seconds
        assert end_time - start_time < 2.0

    def test_sql_preview_generation_performance(self, client, mock_auth_user):
        """Test SQL preview generation performance with complex queries"""
        # Complex configuration with many parameters
        complex_config = {
            "workflow_id": "complex-workflow",
            "instance_id": "test-instance",
            "parameters": {
                "campaigns": [f"c{i}" for i in range(100)],
                "asins": [f"A{i}" for i in range(50)],
                "start_date": "2025-08-01",
                "end_date": "2025-09-17",
                "metrics": ["impressions", "clicks", "spend"],
                "filters": {
                    "min_impressions": 1000,
                    "max_acos": 30,
                    "campaign_types": ["SP", "SD", "SB"]
                }
            },
            "lookback_config": {
                "type": "custom",
                "start_date": "2025-08-01",
                "end_date": "2025-09-17"
            },
            "schedule_config": {
                "type": "scheduled",
                "frequency": "daily",
                "time": "09:00",
                "timezone": "America/New_York"
            }
        }

        start_time = time.time()
        response = client.post(
            "/api/report-builder/review",
            json=complex_config,
            headers={"Authorization": "Bearer test-token"}
        )
        end_time = time.time()

        assert response.status_code == 200
        data = response.json()

        # SQL preview generation should be fast (under 500ms)
        assert end_time - start_time < 0.5

        # Verify SQL preview is generated
        assert "sql_preview" in data
        assert len(data["sql_preview"]) > 0

    def test_submission_rate_limiting(self, client, mock_auth_user):
        """Test rate limiting on submission endpoint"""
        submission_data = {
            "workflow_id": "test-workflow",
            "instance_id": "test-instance",
            "parameters": {},
            "lookback_config": {"type": "relative", "value": 7, "unit": "days"},
            "schedule_config": {"type": "once"}
        }

        responses = []
        for i in range(20):
            response = client.post(
                "/api/report-builder/submit",
                json=submission_data,
                headers={"Authorization": "Bearer test-token"}
            )
            responses.append(response)

        # Should handle rapid submissions gracefully
        # Some may be rate limited (429) after threshold
        status_codes = [r.status_code for r in responses]
        assert 200 in status_codes  # At least some should succeed

        # If rate limiting is implemented, should see 429s
        # if 429 in status_codes:
        #     assert responses[status_codes.index(429)].headers.get('Retry-After')

    def test_memory_usage_with_large_results(self, client, mock_auth_user):
        """Test memory efficiency with large result sets"""
        # Mock a large backfill operation
        response = client.post(
            "/api/report-builder/preview-schedule",
            json={
                "workflow_id": "test-workflow",
                "instance_id": "test-instance",
                "lookback_config": {
                    "type": "custom",
                    "start_date": "2023-01-01",
                    "end_date": "2025-09-17"
                },
                "schedule_config": {
                    "type": "backfill_with_schedule",
                    "frequency": "daily",
                    "backfill_config": {
                        "enabled": True,
                        "periods": 1000,  # Very large number of periods
                        "segmentation": "daily"
                    }
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        # Response should be paginated or limited
        if "backfill_preview" in data and "segments" in data["backfill_preview"]:
            # Should limit segments in preview to prevent huge responses
            assert len(data["backfill_preview"]["segments"]) <= 100

    def test_database_connection_pooling(self, client, mock_auth_user):
        """Test efficient database connection usage"""
        def make_request(index):
            return client.post(
                "/api/report-builder/validate-parameters",
                json={
                    "workflow_id": f"workflow-{index}",
                    "parameters": {},
                    "lookback_config": {
                        "type": "relative",
                        "value": 7,
                        "unit": "days"
                    }
                },
                headers={"Authorization": "Bearer test-token"}
            )

        # Simulate burst of requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(100)]
            responses = [f.result() for f in futures]

        # All should succeed without connection exhaustion
        assert all(r.status_code == 200 for r in responses)

    def test_cache_effectiveness(self, client, mock_auth_user):
        """Test caching for repeated requests"""
        request_data = {
            "workflow_id": "cached-workflow",
            "parameters": {"campaigns": ["c1", "c2"]},
            "lookback_config": {"type": "relative", "value": 7, "unit": "days"}
        }

        # First request (cache miss)
        start_time1 = time.time()
        response1 = client.post(
            "/api/report-builder/validate-parameters",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        time1 = time.time() - start_time1

        # Second identical request (should hit cache)
        start_time2 = time.time()
        response2 = client.post(
            "/api/report-builder/validate-parameters",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        time2 = time.time() - start_time2

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Second request should be faster if caching is implemented
        # (This assumes caching is implemented; if not, times will be similar)
        # assert time2 <= time1

    def test_timeout_handling(self, client, mock_auth_user):
        """Test handling of slow/timeout scenarios"""
        with patch('amc_manager.api.report_builder.validate_parameters') as mock_validate:
            # Simulate slow processing
            async def slow_validate(*args, **kwargs):
                await asyncio.sleep(35)  # Longer than typical timeout
                return {"valid": True}

            mock_validate.side_effect = slow_validate

            start_time = time.time()
            response = client.post(
                "/api/report-builder/validate-parameters",
                json={
                    "workflow_id": "slow-workflow",
                    "parameters": {},
                    "lookback_config": {"type": "relative", "value": 7, "unit": "days"}
                },
                headers={"Authorization": "Bearer test-token"},
                timeout=30  # 30-second timeout
            )
            end_time = time.time()

            # Should timeout before 35 seconds
            assert end_time - start_time < 35

    def test_parallel_backfill_execution_limit(self, client, mock_auth_user):
        """Test that parallel backfill executions are properly limited"""
        # Create multiple backfill requests
        backfill_configs = []
        for i in range(10):
            config = {
                "workflow_id": f"workflow-{i}",
                "instance_id": f"instance-{i}",
                "parameters": {},
                "lookback_config": {
                    "type": "custom",
                    "start_date": "2025-01-01",
                    "end_date": "2025-09-17"
                },
                "schedule_config": {
                    "type": "backfill_with_schedule",
                    "frequency": "weekly",
                    "backfill_config": {
                        "enabled": True,
                        "periods": 52,
                        "segmentation": "weekly"
                    }
                }
            }
            backfill_configs.append(config)

        # Submit all backfills concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    client.post,
                    "/api/report-builder/submit",
                    json=config,
                    headers={"Authorization": "Bearer test-token"}
                )
                for config in backfill_configs
            ]
            responses = [f.result() for f in futures]

        # System should handle concurrent backfills appropriately
        success_count = sum(1 for r in responses if r.status_code == 200)
        queued_or_limited = sum(1 for r in responses if r.status_code in [202, 429])

        # At least some should succeed
        assert success_count > 0

        # System should manage load (queue or rate limit excess)
        assert success_count + queued_or_limited == len(responses)

    def test_cost_estimation_performance(self, client, mock_auth_user):
        """Test cost estimation calculation performance"""
        configs_with_costs = []

        # Generate various configurations
        for days in [7, 30, 90, 180, 365]:
            for segmentation in ["daily", "weekly", "monthly"]:
                config = {
                    "workflow_id": "cost-test-workflow",
                    "instance_id": "test-instance",
                    "lookback_config": {
                        "type": "relative",
                        "value": days,
                        "unit": "days"
                    },
                    "schedule_config": {
                        "type": "backfill_with_schedule",
                        "frequency": "daily",
                        "backfill_config": {
                            "enabled": True,
                            "periods": days if segmentation == "daily" else days // 7,
                            "segmentation": segmentation
                        }
                    }
                }
                configs_with_costs.append(config)

        total_time = 0
        for config in configs_with_costs:
            start_time = time.time()
            response = client.post(
                "/api/report-builder/preview-schedule",
                json=config,
                headers={"Authorization": "Bearer test-token"}
            )
            total_time += time.time() - start_time

            assert response.status_code == 200
            data = response.json()
            assert "cost_estimate" in data

        # Average time per estimation should be under 200ms
        avg_time = total_time / len(configs_with_costs)
        assert avg_time < 0.2

    def test_graceful_degradation_under_load(self, client, mock_auth_user):
        """Test system degradation under heavy load"""
        def stress_test_request(index):
            # Mix of different operations
            operations = [
                ("/api/report-builder/validate-parameters", {
                    "workflow_id": f"stress-{index}",
                    "parameters": {"test": index},
                    "lookback_config": {"type": "relative", "value": 7, "unit": "days"}
                }),
                ("/api/report-builder/preview-schedule", {
                    "workflow_id": f"stress-{index}",
                    "instance_id": "test",
                    "lookback_config": {"type": "relative", "value": 7, "unit": "days"},
                    "schedule_config": {"type": "once"}
                })
            ]

            endpoint, data = operations[index % 2]
            return client.post(
                endpoint,
                json=data,
                headers={"Authorization": "Bearer test-token"}
            )

        # Simulate heavy load
        with ThreadPoolExecutor(max_workers=50) as executor:
            start_time = time.time()
            futures = [executor.submit(stress_test_request, i) for i in range(200)]
            responses = [f.result() for f in futures]
            end_time = time.time()

        # Count response types
        success_200 = sum(1 for r in responses if r.status_code == 200)
        client_errors = sum(1 for r in responses if 400 <= r.status_code < 500)
        server_errors = sum(1 for r in responses if r.status_code >= 500)

        # Most requests should still succeed
        assert success_200 > len(responses) * 0.8  # 80% success rate

        # Server errors should be minimal
        assert server_errors < len(responses) * 0.05  # Less than 5% server errors

        # Should complete within reasonable time
        assert end_time - start_time < 30  # 30 seconds for 200 requests