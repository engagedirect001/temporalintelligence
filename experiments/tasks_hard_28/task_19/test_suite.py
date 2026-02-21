import pytest
import json
from buggy_code import JsonRpcServer, JsonRpcError


@pytest.fixture
def server():
    s = JsonRpcServer()
    s.register("add", lambda a, b: a + b)
    s.register("greet", lambda name="World": f"Hello, {name}!")
    s.register("fail", lambda: (_ for _ in ()).throw(JsonRpcError(-1, "Custom error")))
    return s


def test_basic_call(server):
    req = json.dumps({"jsonrpc": "2.0", "method": "add", "params": [1, 2], "id": 1})
    resp = json.loads(server.handle_request(req))
    assert resp["result"] == 3
    assert resp["id"] == 1


def test_response_has_jsonrpc_field(server):
    """Bug 3: success response must include 'jsonrpc': '2.0'."""
    req = json.dumps({"jsonrpc": "2.0", "method": "add", "params": [1, 2], "id": 1})
    resp = json.loads(server.handle_request(req))
    assert resp.get("jsonrpc") == "2.0", \
        "Response must include 'jsonrpc': '2.0'"


def test_notification_no_response(server):
    """Notification (no 'id') should return None (no response)."""
    req = json.dumps({"jsonrpc": "2.0", "method": "add", "params": [1, 2]})
    resp = server.handle_request(req)
    assert resp is None


def test_batch_all_notifications(server):
    """Bug 2: batch of only notifications should return nothing, not empty array."""
    batch = json.dumps([
        {"jsonrpc": "2.0", "method": "add", "params": [1, 2]},
        {"jsonrpc": "2.0", "method": "add", "params": [3, 4]},
    ])
    resp = server.handle_request(batch)
    assert resp is None, f"Batch of notifications should return None, got {resp}"


def test_batch_mixed(server):
    batch = json.dumps([
        {"jsonrpc": "2.0", "method": "add", "params": [1, 2], "id": 1},
        {"jsonrpc": "2.0", "method": "add", "params": [3, 4]},  # notification
        {"jsonrpc": "2.0", "method": "add", "params": [5, 6], "id": 2},
    ])
    resp = json.loads(server.handle_request(batch))
    assert len(resp) == 2, f"Should have 2 responses (not 3), got {len(resp)}"


def test_method_not_found(server):
    req = json.dumps({"jsonrpc": "2.0", "method": "nonexistent", "id": 1})
    resp = json.loads(server.handle_request(req))
    assert "error" in resp
    assert resp["error"]["code"] == -32601


def test_parse_error(server):
    resp = json.loads(server.handle_request("not json!!!"))
    assert resp["error"]["code"] == -32700


def test_named_params(server):
    req = json.dumps({"jsonrpc": "2.0", "method": "greet", "params": {"name": "Claude"}, "id": 1})
    resp = json.loads(server.handle_request(req))
    assert resp["result"] == "Hello, Claude!"


def test_id_null(server):
    """id: null is a valid request (not a notification)."""
    req = json.dumps({"jsonrpc": "2.0", "method": "add", "params": [1, 2], "id": None})
    resp = json.loads(server.handle_request(req))
    assert resp["id"] is None
    assert resp["result"] == 3
