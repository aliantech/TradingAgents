from datetime import UTC, datetime
from hashlib import sha256
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AgentAuditModel, AgentTokenModel
from app.db.session import get_db_session

TOKEN_PREFIX = "aql_agent_"
RATE_LIMIT_BUCKETS: dict[str, tuple[int, int]] = {}


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def hash_token(raw_token: str) -> str:
    return sha256(raw_token.encode("utf-8")).hexdigest()


def extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing or malformed agent token")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].startswith(TOKEN_PREFIX):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing or malformed agent token")
    return parts[1]


def get_current_agent_token(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    session: Session = Depends(get_db_session),
) -> AgentTokenModel:
    try:
        raw_token = extract_bearer(authorization)
    except HTTPException as exc:
        record_agent_audit(session, request=request, token=None, scope_class="auth", status_code=exc.status_code, detail=str(exc.detail))
        raise
    token_hash = hash_token(raw_token)
    token = session.scalar(select(AgentTokenModel).where(AgentTokenModel.token_hash == token_hash))
    if token is None:
        record_agent_audit(session, request=request, token=None, scope_class="auth", status_code=401, detail="unknown agent token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unknown agent token")
    if token.status != "active":
        record_agent_audit(session, request=request, token=token, scope_class="auth", status_code=401, detail=f"agent token is {token.status}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"agent token is {token.status}")
    expires_at = as_utc(token.expires_at)
    if expires_at is not None and expires_at < datetime.now(UTC):
        record_agent_audit(session, request=request, token=token, scope_class="auth", status_code=401, detail="agent token expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="agent token expired")
    enforce_rate_limit(session, request=request, token=token)
    token.last_used_at = datetime.now(UTC)
    session.commit()
    return token


def require_scope(scope: str):
    def dependency(
        request: Request,
        token: AgentTokenModel = Depends(get_current_agent_token),
        session: Session = Depends(get_db_session),
    ) -> AgentTokenModel:
        if scope not in set(parse_csv(token.scopes)):
            detail = f"agent token lacks required scope: {scope}"
            record_agent_audit(session, request=request, token=token, scope_class=scope, status_code=403, detail=detail)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"agent token lacks required scope: {scope}")
        return token

    return dependency


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def enforce_rate_limit(session: Session, *, request: Request, token: AgentTokenModel) -> None:
    limit = max(token.rate_limit_per_min, 0)
    if limit == 0:
        record_agent_audit(session, request=request, token=token, scope_class="auth", status_code=429, detail="agent token rate limit exceeded")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="agent token rate limit exceeded")

    now = datetime.now(UTC)
    bucket = int(now.timestamp() // 60)
    key = str(token.id)
    current_bucket, count = RATE_LIMIT_BUCKETS.get(key, (bucket, 0))
    if current_bucket != bucket:
        current_bucket, count = bucket, 0
    if count >= limit:
        record_agent_audit(session, request=request, token=token, scope_class="auth", status_code=429, detail="agent token rate limit exceeded")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="agent token rate limit exceeded")
    RATE_LIMIT_BUCKETS[key] = (current_bucket, count + 1)


def list_matches(item: str, allowlist: list[str]) -> bool:
    if not allowlist or "*" in allowlist:
        return True
    normalized = item.strip().upper()
    return any(normalized == allowed.strip().upper() for allowed in allowlist)


def ensure_instrument_allowed(token: AgentTokenModel, symbol: str) -> None:
    if not list_matches(symbol, parse_csv(token.instruments)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"instrument not allowed: {symbol}")


def record_agent_audit(
    session: Session,
    *,
    request: Request,
    token: AgentTokenModel | None,
    scope_class: str,
    status_code: int,
    detail: str | None = None,
) -> None:
    session.add(
        AgentAuditModel(
            agent_token_id=token.id if token else None,
            agent_name=token.name if token else None,
            route=request.url.path,
            method=request.method,
            scope_class=scope_class,
            status_code=status_code,
            detail=detail,
        )
    )
    session.commit()
