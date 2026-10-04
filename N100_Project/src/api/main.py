"""
Main FastAPI Application for N100 Financial Intelligence Platform.
Exposes 16 REST endpoints under /api/v1 prefix with CORS, request logging, and OpenAPI documentation.
"""

import json
import logging
from pathlib import Path
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from src.api.routers import (
    companies,
    documents,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("n100_api")

app = FastAPI(
    title="N100 Financial Intelligence API",
    description="Institutional-grade REST API service for fundamental analysis, multi-metric screening, peer benchmarking, and regulatory filings.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
)

# 1. CORS Middleware (allow all origins for internal analytics)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 2. Request Logging Middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({process_time_ms}ms)")
    response.headers["X-Process-Time-Ms"] = str(process_time_ms)
    return response


# 3. Mount all 8 Routers under /api/v1
api_v1_prefix = "/api/v1"

app.include_router(health.router, prefix=api_v1_prefix)
app.include_router(companies.router, prefix=api_v1_prefix)
app.include_router(screener.router, prefix=api_v1_prefix)
app.include_router(sectors.router, prefix=api_v1_prefix)
app.include_router(peers.router, prefix=api_v1_prefix)
app.include_router(valuation.router, prefix=api_v1_prefix)
app.include_router(portfolio.router, prefix=api_v1_prefix)
app.include_router(documents.router, prefix=api_v1_prefix)


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root to OpenAPI docs."""
    return RedirectResponse(url="/docs")


def export_openapi_spec(output_path: Path) -> None:
    """Exports the OpenAPI JSON schema to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)


if __name__ == "__main__":
    import uvicorn
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    docs_dir = PROJECT_ROOT / "docs"
    export_openapi_spec(docs_dir / "openapi.json")
    print("Exported OpenAPI spec to docs/openapi.json")
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
