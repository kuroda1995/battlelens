import asyncio

import httpx
from fastapi import APIRouter, HTTPException

from app.calculations.damage import calculate_damage
from app.calculations.stats import ValidationError, calculate_stats
from app.config import get_settings
from app.models import DamageCalcRequest, StatCalcRequest

router = APIRouter(prefix="/calc", tags=["calculations"])

_type_chart_cache: dict[str, dict[str, list[str]]] | None = None
_type_chart_lock = asyncio.Lock()


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


async def _get_type_chart(client: httpx.AsyncClient) -> dict[str, dict[str, list[str]]]:
    """タイプ相性表(全18タイプ)を取得してキャッシュする。

    18種類のみの固定データなので、初回アクセス時に一度だけ全件取得すれば
    以降は再取得不要。
    """
    global _type_chart_cache
    async with _type_chart_lock:
        if _type_chart_cache is not None:
            return _type_chart_cache

        base_url = get_settings().pokeapi_base_url
        list_resp = await client.get(f"{base_url}/type", params={"limit": 30})
        list_resp.raise_for_status()
        entries = [e for e in list_resp.json()["results"] if e["name"] not in ("unknown", "shadow")]

        async def fetch_one(entry: dict) -> tuple[str, dict[str, list[str]]]:
            resp = await client.get(entry["url"])
            resp.raise_for_status()
            relations = resp.json()["damage_relations"]
            return entry["name"], {
                "double_damage_to": [t["name"] for t in relations["double_damage_to"]],
                "half_damage_to": [t["name"] for t in relations["half_damage_to"]],
                "no_damage_to": [t["name"] for t in relations["no_damage_to"]],
            }

        results = await asyncio.gather(*(fetch_one(e) for e in entries))
        _type_chart_cache = dict(results)
        return _type_chart_cache


def _type_multiplier(
    move_type: str, defender_types: list[str], chart: dict[str, dict[str, list[str]]]
) -> float:
    relations = chart.get(move_type, {})
    multiplier = 1.0
    for defender_type in defender_types:
        if defender_type in relations.get("no_damage_to", []):
            multiplier *= 0.0
        elif defender_type in relations.get("double_damage_to", []):
            multiplier *= 2.0
        elif defender_type in relations.get("half_damage_to", []):
            multiplier *= 0.5
    return multiplier


@router.post("/damage")
async def calc_damage(payload: DamageCalcRequest) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        chart = await _get_type_chart(client)

    type_multiplier = _type_multiplier(payload.move_type, payload.defender.types, chart)

    return calculate_damage(
        attacker_base_stats=payload.attacker.base_stats,
        attacker_ivs=payload.attacker.ivs.model_dump(),
        attacker_evs=payload.attacker.evs.model_dump(),
        attacker_nature=payload.attacker.nature,
        attacker_level=payload.attacker.level,
        attacker_types=payload.attacker.types,
        attacker_item=payload.attacker.item,
        defender_base_stats=payload.defender.base_stats,
        defender_ivs=payload.defender.ivs.model_dump(),
        defender_evs=payload.defender.evs.model_dump(),
        defender_nature=payload.defender.nature,
        defender_level=payload.defender.level,
        defender_types=payload.defender.types,
        defender_item=payload.defender.item,
        move_power=payload.move_power,
        move_type=payload.move_type,
        move_damage_class=payload.move_damage_class,
        type_multiplier=type_multiplier,
        weather=payload.weather,
        trick_room=payload.trick_room,
        critical=payload.critical,
    )
