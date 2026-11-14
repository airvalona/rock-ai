import pytest
from fastapi.testclient import TestClient
from rock.core.gateway import app, GatewayService

def test_gateway_ui_and_agent_endpoints():
    client = TestClient(app)

    # Test dashboard HTML serving
    response = client.get("/")
    assert response.status_code == 200
    assert "rock.ai" in response.text
    assert "Fleet Active 24/7" in response.text

    # Test health check
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "ok"
