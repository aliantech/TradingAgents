from collections.abc import Callable
from dataclasses import dataclass
import json
from typing import Any
from urllib import error, request


JsonObject = dict[str, Any]
Transport = Callable[["AgentGatewayRequest"], Any]


@dataclass(frozen=True)
class AgentGatewayRequest:
    method: str
    url: str
    headers: dict[str, str]
    json_body: JsonObject | None = None


class AgentGatewayMcpClient:
    def __init__(
        self,
        gateway_base_url: str,
        agent_token: str,
        transport: Transport | None = None,
    ) -> None:
        self.gateway_base_url = gateway_base_url.rstrip("/")
        self.agent_token = agent_token
        self.transport = transport or urllib_transport

    def get(self, path: str) -> Any:
        return self._send("GET", path)

    def post(
        self,
        path: str,
        json_body: JsonObject,
        *,
        idempotency_key: str | None = None,
    ) -> Any:
        headers = {}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return self._send("POST", path, json_body=json_body, extra_headers=headers)

    def _send(
        self,
        method: str,
        path: str,
        *,
        json_body: JsonObject | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        normalized_path = path if path.startswith("/") else f"/{path}"
        headers = {"Authorization": f"Bearer {self.agent_token}"}
        headers.update(extra_headers or {})
        return self.transport(
            AgentGatewayRequest(
                method=method,
                url=f"{self.gateway_base_url}/api/agent/v1{normalized_path}",
                headers=headers,
                json_body=json_body,
            )
        )


class AgentMcpToolbox:
    def __init__(self, client: AgentGatewayMcpClient) -> None:
        self.client = client

    def list_tools(self) -> list[JsonObject]:
        return [
            {"name": "whoami", "description": "Return the current agent token identity."},
            {"name": "check_health", "description": "Check Agent Gateway health."},
            {"name": "list_reports", "description": "List scoped research reports."},
            {"name": "get_report", "description": "Read one scoped research report."},
            {"name": "submit_analysis", "description": "Submit a research analysis job."},
            {"name": "get_job", "description": "Poll a research job."},
            {"name": "get_job_result", "description": "Read a completed research job result."},
        ]

    def call_tool(self, name: str, arguments: JsonObject) -> Any:
        if name == "whoami":
            return self.client.get("/whoami")
        if name == "check_health":
            return self.client.get("/health")
        if name == "list_reports":
            return self.client.get("/reports")
        if name == "get_report":
            return self.client.get(f"/reports/{required_argument(arguments, 'report_id')}")
        if name == "submit_analysis":
            return self.submit_analysis(arguments)
        if name == "get_job":
            return self.client.get(f"/jobs/{required_argument(arguments, 'job_id')}")
        if name == "get_job_result":
            return self.client.get(f"/jobs/{required_argument(arguments, 'job_id')}/result")
        raise ValueError(f"unknown MCP tool: {name}")

    def submit_analysis(self, arguments: JsonObject) -> Any:
        payload = {
            key: value
            for key, value in arguments.items()
            if key != "idempotency_key"
        }
        return self.client.post(
            "/jobs/research-analysis",
            payload,
            idempotency_key=arguments.get("idempotency_key"),
        )


def required_argument(arguments: JsonObject, name: str) -> str:
    value = arguments.get(name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing required MCP tool argument: {name}")
    return value


def urllib_transport(agent_request: AgentGatewayRequest) -> Any:
    body = None
    headers = dict(agent_request.headers)
    if agent_request.json_body is not None:
        body = json.dumps(agent_request.json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    http_request = request.Request(
        agent_request.url,
        data=body,
        headers=headers,
        method=agent_request.method,
    )
    try:
        with request.urlopen(http_request, timeout=30) as response:
            return decode_response(response.read())
    except error.HTTPError as exc:
        raise RuntimeError(decode_response(exc.read())) from exc


def decode_response(body: bytes) -> Any:
    if not body:
        return None
    return json.loads(body.decode("utf-8"))
