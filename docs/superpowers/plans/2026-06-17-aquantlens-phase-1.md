# AQuantLens US Options Branch Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the AQuantLens U.S/options Phase 1 AI research workbench foundation on top of TradingAgents.

**Architecture:** Keep TradingAgents as the analysis engine and add clean product boundaries around it: FastAPI backend, React/Vite frontend, TimescaleDB persistence, Redis realtime state, and provider-based market data ingestion. This is a separate U.S/options branch rather than a direct modification of the existing AQuantLens mainline. Phase 1 is research-only and must not include live order execution.

**Tech Stack:** Python, FastAPI, TradingAgents/LangGraph, PostgreSQL, TimescaleDB, Redis, React, Vite, TypeScript, shadcn/ui, Tailwind CSS, i18next, TanStack Table, lightweight-charts.

---

## Branch Boundary

- Active branch: `aquanlens-us`.
- Product role: AQuantLens U.S/options sibling branch.
- Market focus: U.S. equities, ETFs, SPX/SPY/QQQ, VIX, and selected U.S. options.
- Do not import A-share assumptions, China-market provider assumptions, or legacy AQuantLens runtime constraints unless they are explicitly useful.

## File Structure

Planned top-level structure:

```text
backend/
  app/
    api/
    core/
    db/
    market_data/
    options/
    reports/
    tradingagents_adapter/
    realtime/
  tests/
frontend/
  src/
    app/
    components/
    features/
      analysis/
      dashboard/
      market-data/
      options/
      reports/
      settings/
    i18n/
    lib/
    routes/
docs/
  architecture/
  roadmap/
  superpowers/
```

Use this plan as the implementation sequence. Each task should end in a small commit.

### Task 1: Create Backend Skeleton

**Files:**

- Create: `backend/pyproject.toml`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/api/health.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Add failing health test**

Create `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_service_identity():
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "AQuantLens API",
        "status": "ok",
    }
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd backend
pytest tests/test_health.py -q
```

Expected: failure because backend package does not exist yet.

- [ ] **Step 3: Implement FastAPI skeleton**

Create `backend/pyproject.toml`:

```toml
[project]
name = "aquantlens-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi",
  "uvicorn[standard]",
  "pydantic-settings",
]

[project.optional-dependencies]
test = [
  "pytest",
  "httpx",
]

[tool.pytest.ini_options]
pythonpath = ["."]
```

Create `backend/app/core/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "AQuantLens API"

    model_config = SettingsConfigDict(env_prefix="AQUANTLENS_")


settings = Settings()
```

Create `backend/app/api/health.py`:

```python
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"service": settings.service_name, "status": "ok"}
```

Create `backend/app/main.py`:

```python
from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(title="AQuantLens API")
app.include_router(health_router)
```

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
cd backend
pytest tests/test_health.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/app backend/tests/test_health.py
git commit -m "feat: add aquantlens backend skeleton"
```

### Task 2: Define Analysis API Contract

**Files:**

- Create: `backend/app/analysis/schemas.py`
- Create: `backend/app/api/analysis.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_analysis_api.py`

- [ ] **Step 1: Add failing API contract test**

Create `backend/tests/test_analysis_api.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_start_analysis_accepts_phase_one_payload():
    client = TestClient(app)
    response = client.post(
        "/api/analysis",
        json={
            "symbol": "SPY",
            "asset_type": "etf",
            "analysis_date": "2026-06-17",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "standard",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["symbol"] == "SPY"
    assert payload["status"] == "queued"
    assert payload["language"] == "zh"
    assert isinstance(payload["analysis_id"], str)
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd backend
pytest tests/test_analysis_api.py -q
```

Expected: `404 Not Found`.

- [ ] **Step 3: Implement contract-only endpoint**

Create `backend/app/analysis/schemas.py`:

```python
from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class AssetType(StrEnum):
    equity = "equity"
    etf = "etf"
    index = "index"
    option = "option"


class ReportLanguage(StrEnum):
    zh = "zh"
    en = "en"


class AnalysisDepth(StrEnum):
    quick = "quick"
    standard = "standard"
    deep = "deep"


class AnalysisRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    asset_type: AssetType
    analysis_date: date
    language: ReportLanguage = ReportLanguage.zh
    llm_provider: str = Field(min_length=1, max_length=64)
    model: str = Field(min_length=1, max_length=128)
    depth: AnalysisDepth = AnalysisDepth.standard


class AnalysisQueuedResponse(BaseModel):
    analysis_id: UUID
    symbol: str
    status: str
    language: ReportLanguage
```

Create `backend/app/api/analysis.py`:

```python
from uuid import uuid4

from fastapi import APIRouter, status

from app.analysis.schemas import AnalysisQueuedResponse, AnalysisRequest

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("", response_model=AnalysisQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def start_analysis(request: AnalysisRequest) -> AnalysisQueuedResponse:
    return AnalysisQueuedResponse(
        analysis_id=uuid4(),
        symbol=request.symbol.upper(),
        status="queued",
        language=request.language,
    )
```

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI

from app.api.analysis import router as analysis_router
from app.api.health import router as health_router

app = FastAPI(title="AQuantLens API")
app.include_router(health_router)
app.include_router(analysis_router)
```

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
cd backend
pytest tests/test_analysis_api.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/app backend/tests/test_analysis_api.py
git commit -m "feat: define analysis api contract"
```

### Task 3: Add Structured Chinese Report Schema

**Files:**

- Create: `backend/app/reports/schemas.py`
- Create: `backend/tests/test_report_schema.py`

- [ ] **Step 1: Add report schema test**

Create `backend/tests/test_report_schema.py`:

```python
from app.reports.schemas import ResearchReport


def test_research_report_requires_chinese_sections():
    report = ResearchReport(
        analysis_id="00000000-0000-0000-0000-000000000001",
        symbol="SPY",
        language="zh",
        summary="SPY 当前趋势偏强，但需要关注波动率和宏观风险。",
        market_background="美股处于风险偏好修复阶段。",
        fundamental_analysis="ETF 本身不做公司基本面分析，重点观察成分股与估值。",
        technical_analysis="价格位于主要均线上方，MACD 维持正区间。",
        sentiment_analysis="新闻和市场情绪整体中性偏多。",
        options_observation="SPX/SPY 期权 IV 回落，0DTE 成交活跃。",
        bull_case="趋势延续和流动性改善支持上行。",
        bear_case="估值和事件风险可能触发回撤。",
        risk_factors=["FOMC", "VIX spike"],
        trade_plan="等待回踩关键均线后分批观察。",
        position_sizing="研究阶段不生成实盘仓位。",
        take_profit_stop_loss="以关键支撑和波动率变化作为风控参考。",
        confidence=0.62,
    )

    assert report.language == "zh"
    assert report.confidence == 0.62
    assert "SPX/SPY" in report.options_observation
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd backend
pytest tests/test_report_schema.py -q
```

Expected: import failure because schema does not exist.

- [ ] **Step 3: Implement report schema**

Create `backend/app/reports/schemas.py`:

```python
from uuid import UUID

from pydantic import BaseModel, Field


class ResearchReport(BaseModel):
    analysis_id: UUID
    symbol: str
    language: str = "zh"
    summary: str
    market_background: str
    fundamental_analysis: str
    technical_analysis: str
    sentiment_analysis: str
    options_observation: str
    bull_case: str
    bear_case: str
    risk_factors: list[str]
    trade_plan: str
    position_sizing: str
    take_profit_stop_loss: str
    confidence: float = Field(ge=0.0, le=1.0)
```

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
cd backend
pytest tests/test_report_schema.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/reports backend/tests/test_report_schema.py
git commit -m "feat: add structured research report schema"
```

### Task 4: Add Data Model Contracts

**Files:**

- Create: `backend/app/market_data/schemas.py`
- Create: `backend/app/options/schemas.py`
- Create: `backend/tests/test_market_data_schemas.py`

- [ ] **Step 1: Add schema tests**

Create `backend/tests/test_market_data_schemas.py`:

```python
from datetime import datetime, timezone

from app.market_data.schemas import MarketBar
from app.options.schemas import OptionSnapshot


def test_market_bar_contract():
    bar = MarketBar(
        symbol="SPY",
        timeframe="1m",
        timestamp=datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc),
        open=550.0,
        high=551.0,
        low=549.5,
        close=550.5,
        volume=1000000,
        source="provider",
    )

    assert bar.symbol == "SPY"
    assert bar.timeframe == "1m"


def test_option_snapshot_contract():
    snapshot = OptionSnapshot(
        option_symbol="SPXW260617C06000000",
        underlying_symbol="SPX",
        timestamp=datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc),
        bid=10.1,
        ask=10.4,
        last=10.2,
        volume=1200,
        open_interest=8000,
        implied_volatility=0.18,
        delta=0.48,
        gamma=0.02,
        theta=-0.15,
        vega=0.34,
        source="provider",
    )

    assert snapshot.underlying_symbol == "SPX"
    assert snapshot.delta == 0.48
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd backend
pytest tests/test_market_data_schemas.py -q
```

Expected: import failure.

- [ ] **Step 3: Implement schemas**

Create `backend/app/market_data/schemas.py`:

```python
from datetime import datetime

from pydantic import BaseModel, Field


class MarketBar(BaseModel):
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int = Field(ge=0)
    source: str
```

Create `backend/app/options/schemas.py`:

```python
from datetime import datetime

from pydantic import BaseModel, Field


class OptionSnapshot(BaseModel):
    option_symbol: str
    underlying_symbol: str
    timestamp: datetime
    bid: float | None = None
    ask: float | None = None
    last: float | None = None
    volume: int = Field(default=0, ge=0)
    open_interest: int | None = None
    implied_volatility: float | None = None
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None
    source: str
```

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
cd backend
pytest tests/test_market_data_schemas.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/market_data backend/app/options backend/tests/test_market_data_schemas.py
git commit -m "feat: add market data schema contracts"
```

### Task 5: Create Frontend Skeleton

**Files:**

- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/app/App.tsx`
- Create: `frontend/src/i18n/index.ts`

- [ ] **Step 1: Create React/Vite project files**

Create `frontend/package.json`:

```json
{
  "name": "aquantlens-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@vitejs/plugin-react": "latest",
    "vite": "latest",
    "typescript": "latest",
    "react": "latest",
    "react-dom": "latest",
    "i18next": "latest",
    "react-i18next": "latest"
  },
  "devDependencies": {}
}
```

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AQuantLens</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `frontend/src/i18n/index.ts`:

```typescript
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

i18n.use(initReactI18next).init({
  lng: "zh",
  fallbackLng: "zh",
  resources: {
    zh: {
      translation: {
        title: "AQuantLens",
        subtitle: "AI 投研工作台",
      },
    },
    en: {
      translation: {
        title: "AQuantLens",
        subtitle: "AI Trading Research Workbench",
      },
    },
  },
});

export default i18n;
```

Create `frontend/src/app/App.tsx`:

```tsx
import { useTranslation } from "react-i18next";

export function App() {
  const { t, i18n } = useTranslation();

  return (
    <main>
      <h1>{t("title")}</h1>
      <p>{t("subtitle")}</p>
      <button type="button" onClick={() => i18n.changeLanguage(i18n.language === "zh" ? "en" : "zh")}>
        {i18n.language === "zh" ? "English" : "中文"}
      </button>
    </main>
  );
}
```

Create `frontend/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "./app/App";
import "./i18n";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 2: Install dependencies and build**

Run on Ubuntu project environment unless the user explicitly approves Mac-local dependency installation:

```bash
cd frontend
npm install
npm run build
```

Expected: build succeeds and emits a Vite production bundle.

- [ ] **Step 3: Commit**

```bash
git add frontend
git commit -m "feat: add aquantlens frontend skeleton"
```

### Task 6: Add Market Data Provider Interface

**Files:**

- Create: `backend/app/market_data/provider.py`
- Create: `backend/tests/test_market_data_provider.py`

- [ ] **Step 1: Add provider interface test**

Create `backend/tests/test_market_data_provider.py`:

```python
from datetime import date

from app.market_data.provider import MarketDataProvider


class FakeProvider(MarketDataProvider):
    def fetch_daily_bars(self, symbol: str, start: date, end: date):
        return []


def test_provider_interface_supports_daily_bars():
    provider = FakeProvider()
    bars = provider.fetch_daily_bars("SPY", date(2026, 6, 1), date(2026, 6, 17))

    assert bars == []
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd backend
pytest tests/test_market_data_provider.py -q
```

Expected: import failure.

- [ ] **Step 3: Implement provider protocol**

Create `backend/app/market_data/provider.py`:

```python
from abc import ABC, abstractmethod
from datetime import date

from app.market_data.schemas import MarketBar


class MarketDataProvider(ABC):
    @abstractmethod
    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> list[MarketBar]:
        raise NotImplementedError
```

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
cd backend
pytest tests/test_market_data_provider.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/market_data/provider.py backend/tests/test_market_data_provider.py
git commit -m "feat: define market data provider interface"
```

### Task 7: Add Phase 1 Verification Flow

**Files:**

- Create: `docs/roadmap/phase-1-verification.md`

- [ ] **Step 1: Create verification checklist**

Create `docs/roadmap/phase-1-verification.md`:

```markdown
# Phase 1 Verification

## Required End-to-End Flow

- Start backend API.
- Start frontend UI.
- Open AQuantLens workbench.
- Select Chinese UI.
- Start SPY analysis.
- Confirm analysis job enters queued/running status.
- Confirm progress updates render in UI.
- Confirm Chinese report is generated.
- Confirm report is saved.
- Confirm report appears in history.
- Confirm SPY K-line chart renders.
- Confirm selected SPY or SPX option-chain snapshot renders.

## Safety Checks

- No live order placement exists.
- No broker credentials are required for Phase 1.
- No `.env` values are printed in logs.
- AI output is labelled as research, not investment advice.
```

- [ ] **Step 2: Commit**

```bash
git add docs/roadmap/phase-1-verification.md
git commit -m "docs: add phase one verification checklist"
```

## Self-Review

Spec coverage:

- Bilingual frontend: covered in Task 5.
- FastAPI backend boundary: covered in Tasks 1 and 2.
- Chinese structured reports: covered in Task 3.
- Market data and options schema: covered in Task 4.
- Provider abstraction: covered in Task 6.
- Verification: covered in Task 7.
- Live trading exclusion: covered in design docs and verification safety checks.

No placeholders remain in this plan. Any later implementation should split larger production work into follow-up plans after these foundations are committed and verified.
