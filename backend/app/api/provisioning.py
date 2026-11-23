from fastapi import APIRouter, HTTPException, status
from app.schemas.provisioning import (
    ProvisioningDraft,
    PlanResponse,
    ApplyRequest,
    ApplyResponse,
    DestroyRequest,
    OperationRecord
)
from app.services.terraform_service import (
    generate_plan,
    run_apply,
    run_destroy,
    get_operation_status,
    list_recent_operations
)

router = APIRouter(prefix="/provisioning", tags=["Provisioning"])

@router.post("/plan", response_model=PlanResponse)
def create_plan(config: ProvisioningDraft):
    try:
        return generate_plan(config)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan generation failed: {str(e)}"
        )

@router.post("/apply", response_model=ApplyResponse)
def execute_apply(req: ApplyRequest):
    try:
        return run_apply(req.plan_id, req.confirmation_phrase)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate apply operation: {str(e)}"
        )

@router.post("/destroy", response_model=ApplyResponse)
def execute_destroy(req: DestroyRequest):
    try:
        return run_destroy(req.plan_id, req.confirmation_phrase)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate destroy operation: {str(e)}"
        )

@router.get("/operations/{operation_id}", response_model=OperationRecord)
def check_operation(operation_id: str):
    try:
        return get_operation_status(operation_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

@router.get("/operations", response_model=list[OperationRecord])
def get_operations():
    return list_recent_operations()
