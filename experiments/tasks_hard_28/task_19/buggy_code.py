"""
Task 19: JSON-RPC 2.0 Protocol Implementation
Category: Combined — API/protocol + serialization bugs
"""
import json
from typing import Any, Dict, Optional, Callable


class JsonRpcError(Exception):
    def __init__(self, code, message, data=None):
        self.code = code
        self.message = message
        self.data = data


class JsonRpcServer:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    def __init__(self):
        self.methods = {}
    
    def register(self, name, func):
        self.methods[name] = func
    
    def handle_request(self, raw_json: str) -> Optional[str]:
        """Process a JSON-RPC request and return response JSON."""
        try:
            request = json.loads(raw_json)
        except json.JSONDecodeError:
            return json.dumps(self._error_response(None, self.PARSE_ERROR, "Parse error"))
        
        # Handle batch requests
        if isinstance(request, list):
            if not request:
                return json.dumps(self._error_response(None, self.INVALID_REQUEST, "Empty batch"))
            
            responses = []
            for req in request:
                resp = self._process_single(req)
                # Bug 1: notifications (no "id") should NOT produce a response
                # but we add all responses including None
                if resp is not None:
                    responses.append(resp)
            
            # Bug 2: if all batch items are notifications, should return nothing (not empty array)
            return json.dumps(responses) if responses else json.dumps([])
        
        result = self._process_single(request)
        if result is None:
            return None  # notification
        return json.dumps(result)
    
    def _process_single(self, request: dict) -> Optional[dict]:
        if not isinstance(request, dict):
            return self._error_response(None, self.INVALID_REQUEST, "Request must be object")
        
        # Validate JSON-RPC version
        if request.get("jsonrpc") != "2.0":
            return self._error_response(
                request.get("id"), self.INVALID_REQUEST, "Invalid JSON-RPC version"
            )
        
        method = request.get("method")
        if not isinstance(method, str):
            return self._error_response(
                request.get("id"), self.INVALID_REQUEST, "Method must be string"
            )
        
        params = request.get("params", [])
        request_id = request.get("id")
        is_notification = "id" not in request
        
        if method not in self.methods:
            if is_notification:
                return None
            return self._error_response(request_id, self.METHOD_NOT_FOUND, "Method not found")
        
        try:
            if isinstance(params, list):
                result = self.methods[method](*params)
            elif isinstance(params, dict):
                result = self.methods[method](**params)
            else:
                return self._error_response(request_id, self.INVALID_PARAMS, "Invalid params")
        except TypeError as e:
            return self._error_response(request_id, self.INVALID_PARAMS, str(e))
        except JsonRpcError as e:
            return self._error_response(request_id, e.code, e.message, e.data)
        except Exception as e:
            return self._error_response(request_id, self.INTERNAL_ERROR, str(e))
        
        if is_notification:
            return None
        
        # Bug 3: response doesn't include "jsonrpc": "2.0" field
        return {
            "result": result,
            "id": request_id
        }
    
    def _error_response(self, request_id, code, message, data=None):
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {
            "jsonrpc": "2.0",
            "error": error,
            "id": request_id
        }
