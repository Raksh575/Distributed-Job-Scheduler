import uuid
from typing import List

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import get_current_user, RequirePermission
from app.models.core import User
from app.schemas.dto import WorkflowCreate, WorkflowResponse
from app.services.workflow_service import WorkflowService

router = APIRouter(tags=["Workflows"])

@router.get("/{org_id}/projects/{project_id}/workflows", response_model=List[WorkflowResponse], dependencies=[Depends(RequirePermission("job_management"))])
async def list_workflows(
    org_id: uuid.UUID = Path(...),
    project_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """List workflows for a project."""
    svc = WorkflowService(db)
    return await svc.list_workflows(project_id)


@router.post("/{org_id}/projects/{project_id}/workflows", response_model=WorkflowResponse, dependencies=[Depends(RequirePermission("job_management"))])
async def create_workflow(
    payload: WorkflowCreate,
    org_id: uuid.UUID = Path(...),
    project_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Submit a new workflow (DAG) consisting of multiple jobs."""
    svc = WorkflowService(db)
    # nodes is a list of WorkflowNodeCreate objects; we need dicts for service
    nodes = [n.model_dump() for n in payload.nodes]
    return await svc.submit_workflow(project_id, payload.name, nodes, current_user.id)


@router.get("/{org_id}/workflows/{workflow_id}", response_model=WorkflowResponse, dependencies=[Depends(RequirePermission("job_management"))])
async def get_workflow(
    org_id: uuid.UUID = Path(...),
    workflow_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get workflow details and its nested jobs."""
    svc = WorkflowService(db)
    workflow = await svc.get_workflow(workflow_id)
    return workflow


@router.post("/{org_id}/workflows/{workflow_id}/cancel", response_model=WorkflowResponse, dependencies=[Depends(RequirePermission("job_management"))])
async def cancel_workflow(
    org_id: uuid.UUID = Path(...),
    workflow_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Cancel a running workflow and all pending/running child jobs."""
    svc = WorkflowService(db)
    return await svc.cancel_workflow(workflow_id, current_user.id)


@router.post("/{org_id}/workflows/{workflow_id}/retry", response_model=WorkflowResponse, dependencies=[Depends(RequirePermission("job_management"))])
async def retry_workflow(
    org_id: uuid.UUID = Path(...),
    workflow_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Retry failed jobs within a workflow."""
    svc = WorkflowService(db)
    return await svc.retry_workflow(workflow_id, current_user.id)
