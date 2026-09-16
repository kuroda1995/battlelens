"""ダメージ計算ロジック(広く公開されているゲームメカニクスの計算式に基づく)。

このモジュールは純粋な計算のみを行い、PokéAPIへの問い合わせ(タイプ相性表・
技の威力/タイプの取得)は呼び出し側(routers/damage.py)の責務とする。
stats.py と同様、既知の入力に対する期待値をユニットテストで担保する。
"""

from __future__ import annotations

import math

from app.calculations.stats import calculate_stats

CRITICAL_MULTIPLIER = 1.5
STAB_MULTIPLIER = 1.5
MIN_DAMAGE_ROLL = 0.85
MAX_DAMAGE_ROLL = 1.00

# 天候によるダメージ倍率(技のタイプに対して)
WEATHER_DAMAGE_MULTIPLIER = {
    "sun": {"fire": 1.5, "water": 0.5},
    "rain": {"water": 1.5, "fire": 0.5},
}

# 天候による防御側の実数値補正(対応タイプを持つ場合のみ)
WEATHER_DEFENSE_BOOST = {
    "sand": {"stat": "special_defense", "type": "rock", "multiplier": 1.5},
    "snow": {"stat": "defense", "type": "ice", "multiplier": 1.5},
}

# 攻撃側の持ち物によるステータス補正
ATTACKER_ITEM_STAT_BOOST = {
    "choice-band": [{"stat": "attack", "multiplier": 1.5}],
    "choice-specs": [{"stat": "special_attack", "multiplier": 1.5}],
    "choice-scarf": [{"stat": "speed", "multiplier": 1.5}],
}
# 防御側の持ち物によるステータス補正
DEFENDER_ITEM_STAT_BOOST = {
    "choice-scarf": [{"stat": "speed", "multiplier": 1.5}],
    "assault-vest": [{"stat": "special_defense", "multiplier": 1.5}],
    "eviolite": [
        {"stat": "defense", "multiplier": 1.5},
        {"stat": "special_defense", "multiplier": 1.5},
    ],
}
# 攻撃側の持ち物による与ダメージそのものの倍率
ATTACKER_ITEM_DAMAGE_MULTIPLIER = {
    "life-orb": 1.3,
}
EXPERT_BELT_MULTIPLIER = 1.2


def apply_item_stat_boosts(stats: dict[str, int], item: str, table: dict[str, list[dict]]) -> dict[str, int]:
    result = dict(stats)
    for effect in table.get(item, []):
        result[effect["stat"]] = int(result[effect["stat"]] * effect["multiplier"])
    return result


def apply_weather_defense_boost(
    stats: dict[str, int], weather: str, defender_types: list[str]
) -> dict[str, int]:
    boost = WEATHER_DEFENSE_BOOST.get(weather)
    if boost and boost["type"] in defender_types:
        result = dict(stats)
        result[boost["stat"]] = int(result[boost["stat"]] * boost["multiplier"])
        return result
    return stats


def determine_turn_order(attacker_speed: int, defender_speed: int, trick_room: bool) -> str:
    """"attacker" / "defender" / "tie" のいずれかを返す。"""
    if attacker_speed == defender_speed:
        return "tie"
    attacker_is_faster = attacker_speed > defender_speed
    if trick_room:
        attacker_is_faster = not attacker_is_faster
    return "attacker" if attacker_is_faster else "defender"


def calculate_damage(
    *,
    attacker_base_stats: dict[str, int],
    attacker_ivs: dict[str, int],
    attacker_evs: dict[str, int],
    attacker_nature: str,
    attacker_level: int,
    attacker_types: list[str],
    attacker_item: str,
    defender_base_stats: dict[str, int],
    defender_ivs: dict[str, int],
    defender_evs: dict[str, int],
    defender_nature: str,
    defender_level: int,
    defender_types: list[str],
    defender_item: str,
    move_power: int,
    move_type: str,
    move_damage_class: str,
    type_multiplier: float,
    weather: str = "none",
    trick_room: bool = False,
    critical: bool = False,
) -> dict:
    attacker_stats = calculate_stats(
        attacker_base_stats, attacker_ivs, attacker_evs, attacker_nature, attacker_level
    )
    defender_stats = calculate_stats(
        defender_base_stats, defender_ivs, defender_evs, defender_nature, defender_level
    )

    attacker_stats = apply_item_stat_boosts(attacker_stats, attacker_item, ATTACKER_ITEM_STAT_BOOST)
    defender_stats = apply_item_stat_boosts(defender_stats, defender_item, DEFENDER_ITEM_STAT_BOOST)
    defender_stats = apply_weather_defense_boost(defender_stats, weather, defender_types)

    is_physical = move_damage_class == "physical"
    offensive_stat = attacker_stats["attack" if is_physical else "special_attack"]
    defensive_stat = max(defender_stats["defense" if is_physical else "special_defense"], 1)

    if move_power <= 0 or type_multiplier <= 0:
        base_damage = 0.0
    else:
        base_damage = (
            (2 * attacker_level / 5 + 2) * move_power * offensive_stat / defensive_stat
        ) / 50 + 2

    modifier = 1.0
    if weather in WEATHER_DAMAGE_MULTIPLIER and move_type in WEATHER_DAMAGE_MULTIPLIER[weather]:
        modifier *= WEATHER_DAMAGE_MULTIPLIER[weather][move_type]
    if critical:
        modifier *= CRITICAL_MULTIPLIER
    if move_type in attacker_types:
        modifier *= STAB_MULTIPLIER
    modifier *= type_multiplier
    if attacker_item in ATTACKER_ITEM_DAMAGE_MULTIPLIER:
        modifier *= ATTACKER_ITEM_DAMAGE_MULTIPLIER[attacker_item]
    if attacker_item == "expert-belt" and type_multiplier > 1.0:
        modifier *= EXPERT_BELT_MULTIPLIER

    if base_damage <= 0:
        min_damage = 0
        max_damage = 0
    else:
        min_damage = max(math.floor(base_damage * modifier * MIN_DAMAGE_ROLL), 1)
        max_damage = max(math.floor(base_damage * modifier * MAX_DAMAGE_ROLL), 1)

    defender_hp = defender_stats["hp"]
    min_percent = round(min_damage / defender_hp * 100, 1)
    max_percent = round(max_damage / defender_hp * 100, 1)
    hits_to_ko_best = math.ceil(defender_hp / max_damage) if max_damage > 0 else None
    hits_to_ko_worst = math.ceil(defender_hp / min_damage) if min_damage > 0 else None

    turn_order = determine_turn_order(attacker_stats["speed"], defender_stats["speed"], trick_room)

    return {
        "attacker_stat": offensive_stat,
        "defender_stat": defensive_stat,
        "defender_hp": defender_hp,
        "min_damage": min_damage,
        "max_damage": max_damage,
        "min_percent": min_percent,
        "max_percent": max_percent,
        "hits_to_ko_best": hits_to_ko_best,
        "hits_to_ko_worst": hits_to_ko_worst,
        "type_multiplier": type_multiplier,
        "attacker_speed": attacker_stats["speed"],
        "defender_speed": defender_stats["speed"],
        "turn_order": turn_order,
    }
