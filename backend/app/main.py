from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import connect_to_mongo, close_mongo_connection, setup_indexes
from app.routers import auth, projects, executions, websocket, policies, logs, risk, analytics, workspaces, api_keys, sdk
from app.routers.executions import sdk_router as executions_sdk_router
from app.config import settings
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    connect_to_mongo()
    await setup_indexes()
    yield
    # Shutdown: Close database client
    close_mongo_connection()

app = FastAPI(
    title="Aegis Cloud",
    description="FastAPI + MongoDB enterprise control plane for Aegis SDK.",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware
app.add_middleware(RequestIDMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(projects.router)
app.include_router(api_keys.router)
app.include_router(sdk.router)
app.include_router(executions_sdk_router)
app.include_router(executions.router)
app.include_router(policies.router)
app.include_router(risk.router)
app.include_router(analytics.router)
app.include_router(websocket.router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Aegis Cloud API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

