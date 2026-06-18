import json
from typing import Any

from app.agent_mcp.wrapper import AgentMcpToolbox


JsonObject = dict[str, Any]


class McpJsonRpcServer:
    def __init__(self, toolbox: AgentMcpToolbox) -> None:
        self.toolbox = toolbox

    def handle(self, message: JsonObject) -> JsonObject:
        request_id = message.get("id")
        method = message.get("method")
        try:
            if method == "initialize":
                return result(request_id, initialize_result())
            if method == "tools/list":
                return result(request_id, {"tools": self.toolbox.list_tools()})
            if method == "tools/call":
                params = message.get("params") or {}
                tool_result = self.toolbox.call_tool(
                    required_string(params, "name"),
                    params.get("arguments") or {},
                )
                return result(request_id, tool_call_result(tool_result))
            return error_response(request_id, -32601, f"unknown MCP method: {method}")
        except Exception as exc:
            return error_response(request_id, -32000, str(exc))


def initialize_result() -> JsonObject:
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "aquantlens-agent-gateway",
            "version": "0.1.0",
        },
        "capabilities": {
            "tools": {
                "listChanged": False,
            }
        },
    }


def tool_call_result(payload: Any) -> JsonObject:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False),
            }
        ],
        "isError": False,
    }


def required_string(params: JsonObject, name: str) -> str:
    value = params.get(name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing required JSON-RPC param: {name}")
    return value


def result(request_id: Any, payload: JsonObject) -> JsonObject:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": payload,
    }


def error_response(request_id: Any, code: int, message: str) -> JsonObject:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }
