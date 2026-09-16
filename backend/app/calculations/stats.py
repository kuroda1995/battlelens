"""実数値(最終ステータス)の計算ロジック。

「ポケモンチャンピオンズ」の努力値仕様(0〜32段階での割り振り)に基づく。
式自体はルール・数式であり著作物の複製ではないため、独自実装として扱う。

努力値は段階(0〜32)で管理する。実機での実測値をもとに検証した結果、
性格による影響は以下のように非対称な仕組みになっている。
  - 補正なし: 1段階につき内部加算値が+2、最終値への乗算補正なし
  - 上がりやすい方: 段階の増え方は補正なしと同じ(+2ずつ)だが、
    最終値に従来シリーズと同じ×1.1の補正がかかる
  - 上がりにくい方: 最終値への乗算補正(×0.9等)はかからない代わりに、
    10・20・30段階目だけ増加が止まる(+0)という形でトータルの伸びが抑えられる
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

MAX_EV_PER_STAT = 32  # 努力値は0〜32段階で割り振る
MAX_EV_TOTAL = 66  # 6ステータス合計の上限(段階の合計値)
MAX_IV = 31
DEFAULT_LEVEL = 50

# 上がりにくいステータスがこれらの段階に到達すると、増加量が+0になる(据え置き)
HINDER_FLAT_STAGES = frozenset({10, 20, 30})

BOOST_MULTIPLIER_NUM = 11  # ×1.1 を整数演算で行うための分子
BOOST_MULTIPLIER_DEN = 10  # 浮動小数点誤差(例: 140*1.1=153.999...)を避けるため


class ValidationError(ValueError):
    pass


def validate_evs(evs: dict[str, int]) -> None:
    for key in STAT_KEYS:
        value = evs.get(key, 0)
        if value < 0 or value > MAX_EV_PER_STAT:
            raise ValidationError(f"努力値 '{key}' は0〜{MAX_EV_PER_STAT}段階の範囲で指定してください")
    total = sum(evs.get(key, 0) for key in STAT_KEYS)
    if total > MAX_EV_TOTAL:
        raise ValidationError(f"努力値の合計は{MAX_EV_TOTAL}段階以下にしてください(現在: {total})")


def validate_ivs(ivs: dict[str, int]) -> None:
    for key in STAT_KEYS:
        value = ivs.get(key, MAX_IV)
        if value < 0 or value > MAX_IV:
            raise ValidationError(f"個体値 '{key}' は0〜{MAX_IV}の範囲で指定してください")


def nature_role(nature: str, stat_key: str) -> str:
    """"boost" / "hinder" / "neutral" のいずれかを返す。HPは常に neutral。"""
    if stat_key == "hp":
        return "neutral"
    nature = nature.lower()
    if nature not in NATURES:
        raise ValidationError(f"不明な性格です: {nature}")
    boosted, lowered = NATURES[nature]
    if stat_key == boosted:
        return "boost"
    if stat_key == lowered:
        return "hinder"
    return "neutral"


def ev_stage_contribution(stage: int, role: str) -> int:
    """努力段階(0〜32)を、実数値計算に使う内部の加算値に変換する。

    従来シリーズの `floor(努力値/4)` に相当する項をこの戻り値に置き換える。
    上がりやすい/補正なしは1段階につき+2。上がりにくい方だけ、
    10・20・30段階目で増加が止まる(+0)。
    """
    contribution = stage * 2
    if role == "hinder":
        contribution -= 2 * sum(1 for s in HINDER_FLAT_STAGES if s <= stage)
    return contribution


def calculate_stat(
    base: int,
    iv: int,
    ev: int,
    level: int,
    stat_key: str,
    nature: str = "hardy",
) -> int:
    role = nature_role(nature, stat_key)
    contribution = ev_stage_contribution(ev, role)
    inner = ((2 * base + iv + contribution) * level) // 100
    if stat_key == "hp":
        if base == 1:  # 一部の種族(例: タマゴのみ)を考慮した特例。基本未使用。
            return 1
        return inner + level + 10

    raw = inner + 5
    if role == "boost":
        # 浮動小数点の誤差(140*1.1=153.999...等)を避けるため整数演算で×1.1する
        return (raw * BOOST_MULTIPLIER_NUM) // BOOST_MULTIPLIER_DEN
    return raw


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
