from fastapi import APIRouter
from app.core.dags import store_dag
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dags", tags=["dags"])

@router.post("/save")
def save_dag(dag_data: dict):
    """Endpoint to save a DAG"""
    logger.info("DAG save endpoint called gaaa")
    response, errors = store_dag(dag_data)
    return {"message": "DAG saved successfully gaaa"}