"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.auth import router as auth_router
from .api.auth import org_router, apikey_router
from .api.middleware import RBACMiddleware
from .db import init_database

# Create FastAPI app
app = FastAPI(
    title="ArcticCodex API",
    version="1.0.0",
    description="Enterprise AI platform with trinary logic",
)

# Add CORS middleware (configure for your domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add RBAC middleware (must be before routes)
app.add_middleware(RBACMiddleware)

# Register routers
app.include_router(auth_router)
app.include_router(org_router)
app.include_router(apikey_router)

# Health check endpoint
@app.get("/health")
def health():
    """Health check for load balancers."""
    return {"status": "ok"}

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        init_database(create_tables=False)  # Use migrations in production
    except Exception as e:
        print(f"[WARN] Database initialization failed: {e}")

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for debugging."""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
