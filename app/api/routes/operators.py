from fastapi import APIRouter
from app.core.operators import get_cached_operators, get_params
from app.models.schemas import AllOperatorsResponse, OperatorsStatusResponse

router = APIRouter(prefix="/operators", tags=["operators"])

@router.get("/all", response_model=AllOperatorsResponse)
def get_all_operators():
    """Get all available Airflow operators"""
    operators, errors = get_cached_operators()
    return {"operators": operators, "errors": errors}

@router.get("/status", response_model=OperatorsStatusResponse)
def get_operators_status():
    """Get operator availability status"""
    operators, errors = get_cached_operators()
    
    unavailable = {e["module"]: e["error"] for e in errors}
    
    return {
        "available": operators,
        "unavailable": unavailable,
        "summary": {
            "total_available_modules": len(operators),
            "total_unavailable_modules": len(unavailable),
            "total_operators": sum(len(ops) for ops in operators.values())
        }
    }

@router.get("/params/{module_name}/{operator_name}", response_model=dict)
def get_operator_params(module_name: str, operator_name: str):
    """Get operator arguments"""

    params = get_params(module_name, operator_name)
    
    # operator = operators.get(module_name, {}).get(operator_name)
    if not params:
        return {"error": "Operator not found"}

    return params
