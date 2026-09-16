"""実数値(最終ステータス)の計算ロジック。

対戦シリーズで公開されている計算式(Bulbapedia等で広く解説されている
ゲームメカニクスの数式)に基づく。式自体はルール・数式であり著作物の
複製ではないため、独自実装として扱う。
"""

from __future__ import annotations

STAT_KEYS = ("hp", "attack", "defense", "special_attack", "special_defense", "speed")

# nature -> (boosted_stat, lowered_stat)。無補正の性格は (None, None)。
NATURES: dict[str, tuple[str | None, str | None]] = {
    "hardy": (None, None),
    "docile": (None, None),
    "serious": (None, None),
    "bashful": (None, None),
    "quirky": (None, None),
    "lonely": ("attack", "defense"),
    "brave": ("attack", "speed"),
    "adamant": ("attack", "special_attack"),
    "naughty": ("attack", "special_defense"),
    "bold": ("defense", "attack"),
    "relaxed": ("defense", "speed"),
    "impish": ("defense", "special_attack"),
    "lax": ("defense", "special_defense"),
    "timid": ("speed", "attack"),
    "hasty": ("speed", "defense"),
    "jolly": ("speed", "special_attack"),
    "naive": ("speed", "special_defense"),
    "modest": ("special_attack", "attack"),
    "mild": ("special_attack", "defense"),
    "quiet": ("special_attack", "speed"),
    "rash": ("special_attack", "special_defense"),
    "calm": ("special_defense", "attack"),
    "gentle": ("special_defense", "defense"),
    "sassy": ("special_defense", "speed"),
    "careful": ("special_defense", "special_attack"),
}

MAX_EV_PER_STAT = 252
MAX_EV_TOTAL = 510
MAX_IV = 31
DEFAULT_LEVEL = 50


class ValidationError(ValueError):
    pass


def validate_evs(evs: dict[str, int]) -> None:
    for key in STAT_KEYS:
        value = evs.get(key, 0)
        if value < 0 or value > MAX_EV_PER_STAT:
            raise ValidationError(f"努力値 '{key}' は0〜{MAX_EV_PER_STAT}の範囲で指定してください")
    total = sum(evs.get(key, 0) for key in STAT_KEYS)
    if total > MAX_EV_TOTAL:
        raise ValidationError(f"努力値の合計は{MAX_EV_TOTAL}以下にしてください(現在: {total})")


def validate_ivs(ivs: dict[str, int]) -> None:
    for key in STAT_KEYS:
        value = ivs.get(key, MAX_IV)
        if value < 0 or value > MAX_IV:
            raise ValidationError(f"個体値 '{key}' は0〜{MAX_IV}の範囲で指定してください")


def nature_modifier(nature: str, stat_key: str) -> float:
    if stat_key == "hp":
        return 1.0
    nature = nature.lower()
    if nature not in NATURES:
        raise ValidationError(f"不明な性格です: {nature}")
    boosted, lowered = NATURES[nature]
    if stat_key == boosted:
        return 1.1
    if stat_key == lowered:
        return 0.9
    return 1.0


def calculate_stat(
    base: int,
    iv: int,
    ev: int,
    level: int,
    stat_key: str,
    nature: str = "hardy",
) -> int:
    inner = ((2 * base + iv + ev // 4) * level) // 100
    if stat_key == "hp":
        if base == 1:  # 一部の種族(例: タマゴのみ)を考慮した特例。基本未使用。
            return 1
        return inner + level + 10
    value = inner + 5
    modifier = nature_modifier(nature, stat_key)
    return int(value * modifier)


def calculate_stats(
    base_stats: dict[str, int],
    ivs: dict[str, int],
    evs: dict[str, int],
    nature: str,
    level: int = DEFAULT_LEVEL,
) -> dict[str, int]:
    validate_evs(evs)
    validate_ivs(ivs)
    return {
        key: calculate_stat(
            base=base_stats[key],
            iv=ivs.get(key, MAX_IV),
            ev=evs.get(key, 0),
            level=level,
            stat_key=key,
            nature=nature,
        )
        for key in STAT_KEYS
    }
