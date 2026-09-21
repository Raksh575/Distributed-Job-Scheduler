from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    health,
    jobs,
    users,
    orgs,
    memberships,
    queues,
    scheduler,
    dlq,
    metrics,
    audit,
    observability,
    simulator,
    exports,
    workflows
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["system"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(orgs.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(memberships.router, prefix="/organizations", tags=["memberships"])
api_router.include_router(queues.router, prefix="/organizations", tags=["queues"])
api_router.include_router(jobs.router, prefix="/organizations", tags=["jobs"])
api_router.include_router(scheduler.router, prefix="/organizations", tags=["scheduler"])
api_router.include_router(dlq.router, prefix="/organizations", tags=["dlq"])
api_router.include_router(metrics.router, prefix="/organizations", tags=["metrics"])
api_router.include_router(audit.router, prefix="/organizations", tags=["audit"])
api_router.include_router(observability.router, prefix="/organizations", tags=["observability"])
api_router.include_router(simulator.router, prefix="/organizations", tags=["simulator"])
api_router.include_router(exports.router, prefix="/organizations", tags=["exports"])
api_router.include_router(workflows.router, prefix="/organizations", tags=["workflows"])
