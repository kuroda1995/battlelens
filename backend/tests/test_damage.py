from app.calculations.damage import calculate_damage, determine_turn_order
from app.calculations.stats import STAT_KEYS

BASE_STATS = {key: 100 for key in STAT_KEYS}
IVS = {key: 31 for key in STAT_KEYS}


def _attacker_evs():
    evs = {key: 0 for key in STAT_KEYS}
    evs["attack"] = 32  # 最大段階
    return evs


def _defender_evs():
    return {key: 0 for key in STAT_KEYS}


def _base_kwargs(**overrides):
    kwargs = dict(
        attacker_base_stats=BASE_STATS,
        attacker_ivs=IVS,
        attacker_evs=_attacker_evs(),
        attacker_nature="adamant",  # attackを上げやすい(boost) -> ×1.1込みで実数値167
        attacker_level=50,
        attacker_types=["dragon"],
        attacker_item="none",
        defender_base_stats=BASE_STATS,
        defender_ivs=IVS,
        defender_evs=_defender_evs(),
        defender_nature="hardy",
        defender_level=50,
        defender_types=["normal"],
        defender_item="none",
        move_power=100,
        move_type="normal",
        move_damage_class="physical",
        type_multiplier=1.0,
        weather="none",
        trick_room=False,
        critical=False,
    )
    kwargs.update(overrides)
    return kwargs


def test_baseline_damage_range():
    # attacker attack=167(stats.pyのテストで検証済み), defender defense=120, HP=175
    result = calculate_damage(**_base_kwargs())
    assert result["attacker_stat"] == 167
    assert result["defender_stat"] == 120
    assert result["defender_hp"] == 175
    assert result["min_damage"] == 53
    assert result["max_damage"] == 63
    assert result["min_percent"] == 30.3
    assert result["max_percent"] == 36.0
    assert result["hits_to_ko_best"] == 3
    assert result["hits_to_ko_worst"] == 4


def test_stab_multiplies_damage_by_1_5():
    result = calculate_damage(**_base_kwargs(attacker_types=["normal"]))
    assert result["min_damage"] == 80
    assert result["max_damage"] == 94


def test_critical_hit_multiplies_damage_by_1_5():
    result = calculate_damage(**_base_kwargs(critical=True))
    assert result["min_damage"] == 80
    assert result["max_damage"] == 94


def test_super_effective_type_multiplier():
    result = calculate_damage(**_base_kwargs(type_multiplier=2.0))
    assert result["min_damage"] == 107
    assert result["max_damage"] == 126


def test_type_immunity_results_in_zero_damage():
    result = calculate_damage(**_base_kwargs(type_multiplier=0.0))
    assert result["min_damage"] == 0
    assert result["max_damage"] == 0
    assert result["hits_to_ko_best"] is None
    assert result["hits_to_ko_worst"] is None


def test_weather_boosts_matching_move_type():
    result = calculate_damage(**_base_kwargs(move_type="fire", weather="sun"))
    assert result["min_damage"] == 80
    assert result["max_damage"] == 94


def test_defender_eviolite_boosts_defense():
    result = calculate_damage(**_base_kwargs(defender_item="eviolite"))
    assert result["min_damage"] == 36
    assert result["max_damage"] == 42


def test_attacker_choice_band_boosts_attack():
    result = calculate_damage(**_base_kwargs(attacker_item="choice-band"))
    assert result["min_damage"] == 79
    assert result["max_damage"] == 93


def test_life_orb_boosts_damage():
    result = calculate_damage(**_base_kwargs(attacker_item="life-orb"))
    assert result["min_damage"] == 69
    assert result["max_damage"] == 82


def test_expert_belt_only_applies_when_super_effective():
    not_effective = calculate_damage(**_base_kwargs(attacker_item="expert-belt"))
    assert not_effective["min_damage"] == 53
    assert not_effective["max_damage"] == 63

    effective = calculate_damage(**_base_kwargs(attacker_item="expert-belt", type_multiplier=2.0))
    assert effective["min_damage"] == 128
    assert effective["max_damage"] == 151


def test_turn_order_faster_attacker_moves_first():
    assert determine_turn_order(150, 100, trick_room=False) == "attacker"


def test_turn_order_trick_room_reverses_order():
    assert determine_turn_order(150, 100, trick_room=True) == "defender"


def test_turn_order_tie():
    assert determine_turn_order(100, 100, trick_room=False) == "tie"
