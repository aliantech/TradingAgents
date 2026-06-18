from datetime import UTC, datetime
from hashlib import sha256
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AgentTokenModel
from app.db.session import get_db_session

TOKEN_PREFIX = "aql_agent_"


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
    authorization: Annotated[str | None, Header()] = None,
    session: Session = Depends(get_db_session),
) -> AgentTokenModel:
    raw_token = extract_bearer(authorization)
    token_hash = hash_token(raw_token)
    token = session.scalar(select(AgentTokenModel).where(AgentTokenModel.token_hash == token_hash))
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unknown agent token")
    if token.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"agent token is {token.status}")
    if token.expires_at is not None and token.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="agent token expired")
    token.last_used_at = datetime.now(UTC)
    session.commit()
    return token


def require_scope(scope: str):
    def dependency(token: AgentTokenModel = Depends(get_current_agent_token)) -> AgentTokenModel:
        if scope not in set(parse_csv(token.scopes)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"agent token lacks required scope: {scope}")
        return token

    return dependency
