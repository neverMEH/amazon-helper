"""Integration test for Report Dashboard API endpoints"""

import requests
import json
from datetime import date


def test_api_routes_registered():
    """Test that all report dashboard routes are registered"""
    response = requests.get("http://localhost:8001/api/debug/routes")
    assert response.status_code == 200
    
    routes = response.json()["routes"]
    route_paths = [r["path"] for r in routes]
    
    # Check that our new endpoints are registered
    expected_routes = [
        "/api/collections/{collection_id}/report-dashboard",
        "/api/collections/{collection_id}/report-dashboard/compare",
        "/api/collections/{collection_id}/report-dashboard/chart-data",
        "/api/collections/{collection_id}/report-dashboard/export",
        "/api/collections/{collection_id}/report-configs",
        "/api/collections/{collection_id}/report-snapshots",
        "/api/report-snapshots/{snapshot_id}"
    ]
    
    for route in expected_routes:
        assert route in route_paths, f"Route {route} not found in registered routes"
    
    print("✅ All report dashboard routes are registered!")


def test_openapi_spec():
    """Test that endpoints are documented in OpenAPI spec"""
    response = requests.get("http://localhost:8001/openapi.json")
    assert response.status_code == 200
    
    spec = response.json()
    paths = spec.get("paths", {})
    
    # Check for our endpoints in the OpenAPI spec
    expected_paths = [
        "/api/collections/{collection_id}/report-dashboard",
        "/api/collections/{collection_id}/report-dashboard/compare",
        "/api/collections/{collection_id}/report-dashboard/chart-data",
    ]
    
    for path in expected_paths:
        assert path in paths, f"Path {path} not found in OpenAPI spec"
    
    # Check that the dashboard endpoint has the right methods
    dashboard_path = paths.get("/api/collections/{collection_id}/report-dashboard", {})
    assert "get" in dashboard_path, "GET method not found for dashboard endpoint"
    
    # Check that compare endpoint has POST method
    compare_path = paths.get("/api/collections/{collection_id}/report-dashboard/compare", {})
    assert "post" in compare_path, "POST method not found for compare endpoint"
    
    print("✅ All endpoints are properly documented in OpenAPI spec!")


def test_unauthorized_access():
    """Test that endpoints require authentication"""
    # Try to access dashboard endpoint without auth
    response = requests.get("http://localhost:8001/api/collections/test-id/report-dashboard")
    
    # Should return 401 Unauthorized or 403 Forbidden
    assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    print("✅ Endpoints properly require authentication!")


if __name__ == "__main__":
    try:
        test_api_routes_registered()
        test_openapi_spec()
        test_unauthorized_access()
        print("\n✅ All integration tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server. Make sure the backend is running on http://localhost:8001")
        exit(1)