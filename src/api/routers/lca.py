from fastapi import APIRouter
from pydantic import BaseModel
from ltt_core.lca_runner import run_lca, run_monte_carlo_lca

router = APIRouter()

class LcaRequest(BaseModel):
    functional_unit: dict
    method: list

@router.post("/lca")
def lca_endpoint(request: LcaRequest):
    result = run_lca(request.functional_unit, tuple(request.method))
    return result

@router.post("/lca/montecarlo")
def montecarlo_endpoint(request: LcaRequest, iterations: int = 1000):
    # Placeholder for async job
    result = run_monte_carlo_lca(request.functional_unit, tuple(request.method), iterations)
    return {"job_id": "dummy", "result": result}