"""打者指標計算ロジックの単体テスト"""

import pytest
from src.aggregator import BatterRawCounts, calculate_batter_stats


def test_calculate_batter_stats_standard():
    """標準的な打者指標の計算が正しく行われるかをテスト"""
    raw = BatterRawCounts(
        player_id=673548,
        year=2024,
        games=10,
        plate_appearances=40,
        at_bats=35,
        hits=10,
        doubles=2,
        triples=1,
        home_runs=2,
        total_bases=20,  # 5*1 + 2*2 + 1*3 + 2*4 = 5 + 4 + 3 + 8 = 20
        strikeouts=8,
        walks=4,
        hit_by_pitch=1,
        sac_bunts=0,
        sac_flies=0,
        grounded_into_double_play=1,
        risp_plate_appearances=12,
        risp_at_bats=10,
        risp_hits=3,
    )

    stats = calculate_batter_stats(raw)

    # 打率: 10 / 35 = 0.2857... -> 0.286
    assert stats.batting_average == 0.286

    # 出塁率: (10 + 4 + 1) / (35 + 4 + 1 + 0) = 15 / 40 = 0.375
    assert stats.on_base_percentage == 0.375

    # 長打率: 20 / 35 = 0.5714... -> 0.571
    assert stats.slugging_percentage == 0.571

    # OPS: 0.375 + 0.571 = 0.946
    assert stats.ops == 0.946

    # カウント指標が保持されていること
    assert stats.games == 10
    assert stats.plate_appearances == 40
    assert stats.at_bats == 35
    assert stats.hits == 10
    assert stats.doubles == 2
    assert stats.triples == 1
    assert stats.home_runs == 2
    assert stats.total_bases == 20
    assert stats.strikeouts == 8
    assert stats.walks == 4
    assert stats.hit_by_pitch == 1
    assert stats.sac_bunts == 0
    assert stats.sac_flies == 0
    assert stats.grounded_into_double_play == 1


def test_calculate_batter_stats_zero_division():
    """打数や打席が0の場合でもゼロ除算エラーにならず 0.0 が返ることをテスト"""
    raw = BatterRawCounts(
        player_id=808963,
        year=2024,
        games=1,
        plate_appearances=0,
        at_bats=0,
        hits=0,
        doubles=0,
        triples=0,
        home_runs=0,
        total_bases=0,
        strikeouts=0,
        walks=0,
        hit_by_pitch=0,
        sac_bunts=0,
        sac_flies=0,
        grounded_into_double_play=0,
    )

    stats = calculate_batter_stats(raw)

    assert stats.batting_average == 0.0
    assert stats.on_base_percentage == 0.0
    assert stats.slugging_percentage == 0.0
    assert stats.ops == 0.0


def test_calculate_batter_stats_only_walks():
    """打数0で四球のみの場合の出塁率計算をテスト"""
    raw = BatterRawCounts(
        player_id=123456,
        year=2024,
        games=1,
        plate_appearances=2,
        at_bats=0,
        hits=0,
        doubles=0,
        triples=0,
        home_runs=0,
        total_bases=0,
        strikeouts=0,
        walks=2,
        hit_by_pitch=0,
        sac_bunts=0,
        sac_flies=0,
        grounded_into_double_play=0,
    )

    stats = calculate_batter_stats(raw)

    assert stats.batting_average == 0.0
    # 出塁率: (0 + 2 + 0) / (0 + 2 + 0 + 0) = 1.0
    assert stats.on_base_percentage == 1.0
    assert stats.slugging_percentage == 0.0
    assert stats.ops == 1.0
