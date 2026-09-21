import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.scheduler.manager import scheduler_manager
from app.scheduler.orchestrator import scheduler_orchestrator
from app.websocket.manager import ws_connection_manager

setup_logging()
logger = logging.getLogger("app.main")

async def run_orchestrator_loops():
    """Polled task that syncs DB triggers and sweeps crashed workers."""
    while True:
        try:
            await asyncio.sleep(10)
            await scheduler_orchestrator.sync_database_triggers()
            await scheduler_orchestrator.recover_crashed_workers()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Orchestrator sync loop error: {str(e)}")

async def broadcast_metrics_loop():
    """Polled task that gathers cluster throughput and broadcasts to WebSocket clients."""
    from app.services.metrics_service import MetricsService
    while True:
        try:
            await asyncio.sleep(2.0)
            # Only perform database queries if there are active connections
            if ws_connection_manager.active_connections:
                from app.db.database import AsyncSessionFactory
                async with AsyncSessionFactory() as session:
                    metrics_service = MetricsService(session)
                    stats = await metrics_service.get_dashboard_metrics()
                    await ws_connection_manager.broadcast_to_topic("metrics", stats)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"WebSocket metrics broadcast loop error: {str(e)}")

async def broadcast_observability_loop():
    """Polled task that gathers observability metrics for subscribed orgs and broadcasts to WebSocket clients."""
    while True:
        try:
            await asyncio.sleep(2.0)
            if ws_connection_manager.active_connections:
                # Find all unique org IDs subscribed
                org_ids = set()
                for connection, topics in list(ws_connection_manager.active_connections.items()):
                    for topic in topics:
                        if topic.startswith("observability:"):
                            org_ids.add(topic.split(":")[1])
                
                if org_ids:
                    from app.db.database import AsyncSessionFactory
                    from app.services.metrics_service import MetricsService
                    import uuid
                    async with AsyncSessionFactory() as session:
                        metrics_service = MetricsService(session)
                        for org_id_str in org_ids:
                            try:
                                org_id = uuid.UUID(org_id_str)
                                stats = await metrics_service.get_observability_metrics(org_id)
                                await ws_connection_manager.broadcast_to_topic(f"observability:{org_id_str}", stats)
                            except Exception as ex:
                                logger.error(f"Error broadcasting to org {org_id_str}: {str(ex)}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"WebSocket observability broadcast loop error: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle hooks
    logger.info("Initializing application startup sequence...")
    await scheduler_manager.start()
    
    # Sync initial schedules from DB on startup
    await scheduler_orchestrator.sync_database_triggers()
    
    # Start background daemon tasks
    app.state.orchestrator_task = asyncio.create_task(run_orchestrator_loops())
    app.state.metrics_broadcast_task = asyncio.create_task(broadcast_metrics_loop())
    app.state.observability_broadcast_task = asyncio.create_task(broadcast_observability_loop())
    
    yield
    
    # Shutdown lifecycle hooks
    logger.info("Initializing application shutdown sequence...")
    
    # Cancel tasks
    app.state.orchestrator_task.cancel()
    app.state.metrics_broadcast_task.cancel()
    app.state.observability_broadcast_task.cancel()
    await asyncio.gather(
        app.state.orchestrator_task,
        app.state.metrics_broadcast_task,
        app.state.observability_broadcast_task,
        return_exceptions=True
    )
    
    await scheduler_manager.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
    description="Distributed Job Scheduler Platform API backend"
)

# 1. Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Setup Security Headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# 3. Setup sliding window Rate Limiter
app.add_middleware(RateLimitMiddleware, limit=120, window_seconds=60)

# 4. Response Compression (Gzip)
app.add_middleware(GZipMiddleware, minimum_size=500)

# 5. Setup Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# 3. Register global exception handlers
register_exception_handlers(app)

# 3a. Override FastAPI's default 422 handler to return consistent error format
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    # Build a human-readable message from the first validation error
    first = errors[0] if errors else {}
    field_path = " → ".join(str(p) for p in first.get("loc", []) if p != "body")
    raw_msg = first.get("msg", "Validation error")
    message = f"{field_path}: {raw_msg}" if field_path else raw_msg
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "details": {"errors": errors}
            }
        }
    )

# 4. Include API routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} Platform API",
        "documentation": "/docs",
        "status": "online"
    }

# 5. Setup WebSocket connection endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_connection_manager.connect(websocket)
    try:
        while True:
            # Main socket loop: listen for user events/subscriptions
            data = await websocket.receive_json()
            action = data.get("action")
            topic = data.get("topic")
            
            if action == "subscribe" and topic:
                await ws_connection_manager.subscribe(websocket, topic)
                await websocket.send_json({"event": "subscribed", "topic": topic})
            elif action == "unsubscribe" and topic:
                await ws_connection_manager.unsubscribe(websocket, topic)
                await websocket.send_json({"event": "unsubscribed", "topic": topic})
            else:
                await websocket.send_json({"event": "error", "message": "Unknown action or missing topic"})
                
    except WebSocketDisconnect:
        ws_connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket execution error: {str(e)}")
        ws_connection_manager.disconnect(websocket)
