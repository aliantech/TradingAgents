from pathlib import Path

from app.agent_mcp.server import McpJsonRpcServer
from app.agent_mcp.wrapper import AgentGatewayMcpClient, AgentGatewayRequest, AgentMcpToolbox


def test_mcp_toolbox_exposes_only_research_gateway_tools():
    toolbox = AgentMcpToolbox(client=AgentGatewayMcpClient("http://gateway.local", "aql_agent_test"))

    tool_names = {tool["name"] for tool in toolbox.list_tools()}

    assert tool_names == {
        "whoami",
        "check_health",
        "list_reports",
        "get_report",
        "submit_analysis",
        "get_job",
        "get_job_result",
    }
    assert not any("order" in name or "trade" in name or "broker" in name for name in tool_names)


def test_mcp_toolbox_forwards_read_tools_to_agent_gateway_only():
    transport = RecordingTransport(
        {
            ("GET", "http://gateway.local/api/agent/v1/reports"): [{"symbol": "SPY"}],
            ("GET", "http://gateway.local/api/agent/v1/reports/report-1"): {"symbol": "SPY"},
        }
    )
    toolbox = AgentMcpToolbox(
        client=AgentGatewayMcpClient(
            "http://gateway.local/",
            "aql_agent_test_token",
            transport=transport,
        )
    )

    list_result = toolbox.call_tool("list_reports", {})
    report_result = toolbox.call_tool("get_report", {"report_id": "report-1"})

    assert list_result == [{"symbol": "SPY"}]
    assert report_result == {"symbol": "SPY"}
    assert transport.requests == [
        AgentGatewayRequest(
            method="GET",
            url="http://gateway.local/api/agent/v1/reports",
            headers={"Authorization": "Bearer aql_agent_test_token"},
            json_body=None,
        ),
        AgentGatewayRequest(
            method="GET",
            url="http://gateway.local/api/agent/v1/reports/report-1",
            headers={"Authorization": "Bearer aql_agent_test_token"},
            json_body=None,
        ),
    ]
    assert all("/api/agent/v1" in request.url for request in transport.requests)


def test_mcp_toolbox_submits_analysis_job_with_idempotency_key():
    transport = RecordingTransport(
        {
            ("POST", "http://gateway.local/api/agent/v1/jobs/research-analysis"): {
                "job_id": "job-1",
                "status": "completed",
            }
        }
    )
    toolbox = AgentMcpToolbox(
        client=AgentGatewayMcpClient(
            "http://gateway.local",
            "aql_agent_test_token",
            transport=transport,
        )
    )
    payload = {
        "symbol": "SPY",
        "asset_type": "etf",
        "analysis_date": "2026-06-19",
        "language": "zh",
        "llm_provider": "openai",
        "model": "gpt-5.5",
        "depth": "standard",
        "analyst_set": "macro-options",
        "research_template": "general",
        "idempotency_key": "analysis-spy-2026-06-19",
    }

    result = toolbox.call_tool("submit_analysis", payload)

    assert result == {"job_id": "job-1", "status": "completed"}
    assert transport.requests == [
        AgentGatewayRequest(
            method="POST",
            url="http://gateway.local/api/agent/v1/jobs/research-analysis",
            headers={
                "Authorization": "Bearer aql_agent_test_token",
                "Idempotency-Key": "analysis-spy-2026-06-19",
            },
            json_body={
                "symbol": "SPY",
                "asset_type": "etf",
                "analysis_date": "2026-06-19",
                "language": "zh",
                "llm_provider": "openai",
                "model": "gpt-5.5",
                "depth": "standard",
                "analyst_set": "macro-options",
                "research_template": "general",
            },
        )
    ]


def test_mcp_wrapper_source_does_not_bypass_gateway_or_read_secrets():
    source = "\n".join(path.read_text() for path in Path("app/agent_mcp").glob("*.py"))

    forbidden_fragments = [
        "app.db",
        "SessionLocal",
        "get_db_session",
        "dotenv",
        "os.environ",
        ".env",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_mcp_json_rpc_server_lists_and_calls_tools():
    transport = RecordingTransport(
        {
            ("GET", "http://gateway.local/api/agent/v1/health"): {
                "service": "AQuantLens Agent Gateway",
                "status": "ok",
            }
        }
    )
    server = McpJsonRpcServer(
        toolbox=AgentMcpToolbox(
            client=AgentGatewayMcpClient(
                "http://gateway.local",
                "aql_agent_test_token",
                transport=transport,
            )
        )
    )

    initialize_response = server.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    list_response = server.handle(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    )
    call_response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "check_health", "arguments": {}},
        }
    )

    assert initialize_response["result"]["serverInfo"]["name"] == "aquantlens-agent-gateway"
    assert {tool["name"] for tool in list_response["result"]["tools"]} >= {"check_health"}
    assert call_response == {
        "jsonrpc": "2.0",
        "id": 3,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": '{"service": "AQuantLens Agent Gateway", "status": "ok"}',
                }
            ],
            "isError": False,
        },
    }


class RecordingTransport:
    def __init__(self, responses):
        self.responses = responses
        self.requests: list[AgentGatewayRequest] = []

    def __call__(self, request: AgentGatewayRequest):
        self.requests.append(request)
        return self.responses[(request.method, request.url)]
