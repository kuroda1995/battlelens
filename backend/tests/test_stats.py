import pytest

from app.calculations.stats import (
    STAT_KEYS,
    ValidationError,
    calculate_stat,
    calculate_stats,
    validate_evs,
    validate_ivs,
)


def test_hp_calculation():
    # inner = ((2*100 + 31 + 252//4) * 50) // 100 = 147, HP = 147 + 50 + 10
    assert calculate_stat(base=100, iv=31, ev=252, level=50, stat_key="hp") == 207


def test_neutral_nature_has_no_modifier():
    assert (
        calculate_stat(base=100, iv=31, ev=252, level=50, stat_key="defense", nature="hardy")
        == 152
    )


def test_boosted_nature_applies_1_1_multiplier():
    assert (
        calculate_stat(base=100, iv=31, ev=252, level=50, stat_key="attack", nature="adamant")
        == 167
    )


def test_lowered_nature_applies_0_9_multiplier():
    assert (
        calculate_stat(
            base=100, iv=31, ev=252, level=50, stat_key="special_attack", nature="adamant"
        )
        == 136
    )


def test_unknown_nature_raises():
    with pytest.raises(ValidationError):
        calculate_stat(base=100, iv=31, ev=0, level=50, stat_key="attack", nature="not-a-nature")


def test_validate_evs_rejects_total_over_510():
    evs = {key: 0 for key in STAT_KEYS}
    evs["attack"] = 252
    evs["defense"] = 252
    evs["speed"] = 252  # total 756 > 510
    with pytest.raises(ValidationError):
        validate_evs(evs)


def test_validate_evs_rejects_over_252_per_stat():
    evs = {key: 0 for key in STAT_KEYS}
    evs["attack"] = 253
    with pytest.raises(ValidationError):
        validate_evs(evs)


def test_validate_ivs_rejects_out_of_range():
    ivs = {key: 31 for key in STAT_KEYS}
    ivs["speed"] = 32
    with pytest.raises(ValidationError):
        validate_ivs(ivs)


def test_calculate_stats_returns_all_keys():
    base_stats = {key: 100 for key in STAT_KEYS}
    ivs = {key: 31 for key in STAT_KEYS}
    evs = {key: 0 for key in STAT_KEYS}
    evs["speed"] = 252
    result = calculate_stats(base_stats, ivs, evs, nature="jolly", level=50)
    assert set(result.keys()) == set(STAT_KEYS)
    assert result["speed"] == 167  # jolly boosts speed, ev=252
    assert result["special_attack"] == 108  # jolly lowers special_attack, ev=0
    assert result["attack"] == 120  # neutral for this nature, ev=0
