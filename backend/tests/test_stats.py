import pytest

from app.calculations.stats import (
    STAT_KEYS,
    ValidationError,
    calculate_stat,
    calculate_stats,
    ev_stage_contribution,
    nature_role,
    validate_evs,
    validate_ivs,
)

# 実機での実測値(マスカーニャ、いじっぱり、Lv.50、個体値31)をもとに検証。
# こうげき(種族値110・上がりやすい): 0→143, 10→154, 20→165, 30→176, 32→178
# とくこう(種族値70・上がりにくい): 0→90, 10→99, 20→108, 30→117, 32→119
# ぼうぎょ(種族値70・無補正): 0→90, 32→122


# --- 努力段階(0〜32)→内部加算値の変換ロジック ---------------------------


def test_neutral_and_boost_contribution_is_double_the_stage():
    for stage, expected in [(0, 0), (10, 20), (20, 40), (30, 60), (32, 64)]:
        assert ev_stage_contribution(stage, "neutral") == expected
        assert ev_stage_contribution(stage, "boost") == expected


def test_hinder_contribution_plateaus_at_milestone_stages():
    for stage, expected in [(0, 0), (9, 18), (10, 18), (19, 36), (20, 36), (29, 54), (30, 54), (32, 58)]:
        assert ev_stage_contribution(stage, "hinder") == expected


def test_nature_role_hp_is_always_neutral():
    assert nature_role("adamant", "hp") == "neutral"


def test_nature_role_boost_and_hinder():
    assert nature_role("adamant", "attack") == "boost"
    assert nature_role("adamant", "special_attack") == "hinder"
    assert nature_role("adamant", "defense") == "neutral"


def test_nature_role_unknown_nature_raises():
    with pytest.raises(ValidationError):
        nature_role("not-a-nature", "attack")


# --- 実数値計算(実機の実測値と突き合わせ) -------------------------------


@pytest.mark.parametrize(
    "stage, expected",
    [(0, 143), (10, 154), (20, 165), (30, 176), (32, 178)],
)
def test_boosted_stat_matches_real_measurements(stage, expected):
    # マスカーニャ・こうげき種族値110・いじっぱり(上がりやすい)
    assert (
        calculate_stat(base=110, iv=31, ev=stage, level=50, stat_key="attack", nature="adamant")
        == expected
    )


@pytest.mark.parametrize(
    "stage, expected",
    [(0, 90), (10, 99), (20, 108), (30, 117), (32, 119)],
)
def test_hindered_stat_matches_real_measurements(stage, expected):
    # マスカーニャ・とくこう種族値70・いじっぱり(上がりにくい)
    assert (
        calculate_stat(
            base=70, iv=31, ev=stage, level=50, stat_key="special_attack", nature="adamant"
        )
        == expected
    )


@pytest.mark.parametrize("stage, expected", [(0, 90), (32, 122)])
def test_neutral_stat_matches_real_measurements(stage, expected):
    # マスカーニャ・ぼうぎょ種族値70・無補正
    assert (
        calculate_stat(base=70, iv=31, ev=stage, level=50, stat_key="defense", nature="adamant")
        == expected
    )


def test_hp_ignores_nature():
    # HPは常にneutral扱い(性格の影響を受けない)。contribution=32*2=64
    assert calculate_stat(base=100, iv=31, ev=32, level=50, stat_key="hp") == 207


def test_unknown_nature_raises():
    with pytest.raises(ValidationError):
        calculate_stat(base=100, iv=31, ev=0, level=50, stat_key="attack", nature="not-a-nature")


def test_validate_evs_rejects_total_over_66():
    evs = {key: 0 for key in STAT_KEYS}
    evs["attack"] = 32
    evs["defense"] = 32
    evs["speed"] = 32  # 合計96 > 66
    with pytest.raises(ValidationError):
        validate_evs(evs)


def test_validate_evs_rejects_over_32_per_stat():
    evs = {key: 0 for key in STAT_KEYS}
    evs["attack"] = 33
    with pytest.raises(ValidationError):
        validate_evs(evs)


def test_validate_ivs_rejects_out_of_range():
    ivs = {key: 31 for key in STAT_KEYS}
    ivs["speed"] = 32
    with pytest.raises(ValidationError):
        validate_ivs(ivs)


def test_calculate_stats_returns_all_keys():
    base_stats = {"hp": 100, "attack": 110, "defense": 70, "special_attack": 70, "special_defense": 70, "speed": 100}
    ivs = {key: 31 for key in STAT_KEYS}
    evs = {key: 0 for key in STAT_KEYS}
    evs["attack"] = 32
    result = calculate_stats(base_stats, ivs, evs, nature="adamant", level=50)
    assert set(result.keys()) == set(STAT_KEYS)
    assert result["attack"] == 178
    assert result["special_attack"] == 90  # ev0なので変化なし
    assert result["defense"] == 90  # 無補正・ev0


def test_calculate_stats_rejects_total_over_66():
    base_stats = {key: 100 for key in STAT_KEYS}
    ivs = {key: 31 for key in STAT_KEYS}
    evs = {key: 32 for key in STAT_KEYS}  # 合計192 > 66
    with pytest.raises(ValidationError):
        calculate_stats(base_stats, ivs, evs, nature="hardy", level=50)
