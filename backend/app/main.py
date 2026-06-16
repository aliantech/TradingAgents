from fastapi import FastAPI

from app.analysis.router import router as analysis_router
from app.api.health import router as health_router
from app.market_data.router import router as market_data_router
from app.options.router import router as options_router
from app.reports.router import router as reports_router

app = FastAPI(title="AQuantLens API")
app.include_router(health_router)
app.include_router(analysis_router)
app.include_router(reports_router)
app.include_router(market_data_router)
app.include_router(options_router)
