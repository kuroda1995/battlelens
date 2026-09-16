from fastapi import APIRouter, HTTPException

from app.calculations.stats import ValidationError, calculate_stats
from app.models import StatCalcRequest

router = APIRouter(prefix="/calc", tags=["calculations"])


@router.post("/stats")
def calc_stats(payload: StatCalcRequest) -> dict[str, int]:
    try:
        return calculate_stats(
            base_stats=payload.base_stats,
            ivs=payload.ivs.model_dump(),
            evs=payload.evs.model_dump(),
            nature=payload.nature,
            level=payload.level,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
