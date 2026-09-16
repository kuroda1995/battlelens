"""「ポケモンチャンピオンズ」独自データの補正テーブル。

本アプリは種族名・タイプ・技等の基礎データをPokéAPI(本編ゲームのデータ)
から取得しているが、チャンピオンズは本編と種族値がリバランスされている
場合があることが実機での検証で判明した(例: マスカーニャのとくこう)。

未確認の種族・ステータスは本編(PokeAPI)の値をそのまま使う。実機で確認が
取れた差分だけを、ここに追記していく運用とする。
"""

# PokéAPIの種族ID(pokemon.id) -> 上書きするステータスのみを指定する辞書
BASE_STAT_OVERRIDES: dict[int, dict[str, int]] = {
    908: {"special_attack": 70},  # マスカーニャ: 本編は81だが実機確認で70
}


def apply_base_stat_overrides(species_id: int, base_stats: dict[str, int]) -> dict[str, int]:
    override = BASE_STAT_OVERRIDES.get(species_id)
    if not override:
        return base_stats
    return {**base_stats, **override}
