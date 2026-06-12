from fastapi.testclient import TestClient

from app.main import app


def test_ready_and_metrics_endpoints_exist() -> None:
    client = TestClient(app)

    ready = client.get("/ready")
    metrics = client.get("/metrics")

    assert ready.status_code == 200
    assert ready.json() == {"status": "pending", "checks": {"database": "pending"}}

    assert metrics.status_code == 200
    assert "uptime_seconds" in metrics.json()


def test_sla_preview_route_is_registered() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/sla/preview", json={})

    assert response.status_code == 422


def test_zabbix_sla_preview_route_is_registered() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/sla/preview/zabbix", json={})

    assert response.status_code == 422


def test_maintenance_window_route_is_registered() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/maintenance-windows", json={})

    assert response.status_code == 422


def test_sla_exclusion_route_is_registered() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/sla-exclusions", json={})

    assert response.status_code == 422


def test_sla_result_route_is_registered() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/sla-results", json={})

    assert response.status_code == 422


def test_sla_result_history_route_is_registered() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/sla-results/history")

    assert response.status_code == 422


def test_sla_result_executive_xlsx_route_is_registered() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/sla-results/executive.xlsx")

    assert response.status_code == 422


def test_sla_result_executive_pdf_route_is_registered() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/sla-results/executive.pdf")

    assert response.status_code == 422


def test_report_schedule_routes_are_registered() -> None:
    client = TestClient(app)

    create_response = client.post("/api/v1/report-schedules", json={})
    run_response = client.post("/api/v1/report-schedules/run-due", json={})

    assert create_response.status_code == 422
    assert run_response.status_code == 422
