from pydantic import BaseModel
from typing import Dict, List, Any

class OperatorError(BaseModel):
    module: str
    error: str

class AllOperatorsResponse(BaseModel):
    operators: Dict[str, List[str]]
    errors: List[OperatorError]

class OperatorsStatusResponse(BaseModel):
    available: Dict[str, List[str]]
    unavailable: Dict[str, str]
    summary: Dict[str, int]