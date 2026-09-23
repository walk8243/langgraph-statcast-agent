"""Statcast 指標計算ロジックの単体テスト"""

import pytest
from src.aggregator import (
    BatterStatcastRawCounts,
    PitcherPitchTypeRawCounts,
    PitcherStatcastRawCounts,
    calculate_batter_statcast_stats,
    calculate_pitcher_pitch_type_stats,
    calculate_pitcher_statcast_stats,
)


def test_calculate_batter_statcast_stats_standard():
    """打者 Statcast 指標の計算が正しく行われるかをテスト"""
    raw = BatterStatcastRawCounts(
        player_id=660271,
        year=2024,
        pitches_seen=500,
        batted_balls=100,
        barrels=15,
        hard_hit_count=50,
        sum_exit_velocity=9230.0,
        max_exit_velocity=117.8,
        sum_launch_angle=1250.0,
        sweet_spot_count=35,
    )

    stats = calculate_batter_statcast_stats(raw)

    assert stats.player_id == 660271
    assert stats.year == 2024
    assert stats.pitches_seen == 500
    assert stats.batted_balls == 100
    assert stats.barrels == 15
    # barrel_pct: 15 / 100 * 100 = 15.0%
    assert stats.barrel_pct == 15.0
    assert stats.hard_hit_count == 50
    # hard_hit_pct: 50 / 100 * 100 = 50.0%
    assert stats.hard_hit_pct == 50.0
    # avg_exit_velocity: 9230.0 / 100 = 92.3 mph
    assert stats.avg_exit_velocity == 92.3
    assert stats.max_exit_velocity == 117.8
    # avg_launch_angle: 1250.0 / 100 = 12.5 deg
    assert stats.avg_launch_angle == 12.5
    # sweet_spot_pct: 35 / 100 * 100 = 35.0%
    assert stats.sweet_spot_pct == 35.0


def test_calculate_batter_statcast_stats_zero_division():
    """打球数が0の場合でもゼロ除算エラーにならず 0.0 が返ることをテスト"""
    raw = BatterStatcastRawCounts(
        player_id=808963,
        year=2024,
        pitches_seen=10,
        batted_balls=0,
        barrels=0,
        hard_hit_count=0,
        sum_exit_velocity=0.0,
        max_exit_velocity=0.0,
        sum_launch_angle=0.0,
        sweet_spot_count=0,
    )

    stats = calculate_batter_statcast_stats(raw)

    assert stats.barrel_pct == 0.0
    assert stats.hard_hit_pct == 0.0
    assert stats.avg_exit_velocity == 0.0
    assert stats.max_exit_velocity == 0.0
    assert stats.avg_launch_angle == 0.0
    assert stats.sweet_spot_pct == 0.0


def test_calculate_pitcher_statcast_stats_standard():
    """投手 Statcast 総合指標の計算が正しく行われるかをテスト"""
    raw = PitcherStatcastRawCounts(
        player_id=808967,
        year=2024,
        total_pitches=1000,
        batted_balls=200,
        barrels_allowed=12,
        hard_hit_count=60,
        sum_exit_velocity=17600.0,
        swings=450,
        whiffs=135,
        called_strikes=165,
    )

    stats = calculate_pitcher_statcast_stats(raw)

    assert stats.player_id == 808967
    assert stats.year == 2024
    assert stats.total_pitches == 1000
    assert stats.batted_balls == 200
    assert stats.barrels_allowed == 12
    # barrel_pct: 12 / 200 * 100 = 6.0%
    assert stats.barrel_pct == 6.0
    assert stats.hard_hit_count == 60
    # hard_hit_pct: 60 / 200 * 100 = 30.0%
    assert stats.hard_hit_pct == 30.0
    # avg_exit_velocity: 17600.0 / 200 = 88.0 mph
    assert stats.avg_exit_velocity == 88.0
    assert stats.swings == 450
    assert stats.whiffs == 135
    # whiff_pct: 135 / 450 * 100 = 30.0%
    assert stats.whiff_pct == 30.0
    assert stats.called_strikes == 165
    # csw_pct: (165 + 135) / 1000 * 100 = 300 / 1000 * 100 = 30.0%
    assert stats.csw_pct == 30.0


def test_calculate_pitcher_statcast_stats_zero_division():
    """投球数やスイング数が0の場合でもゼロ除算エラーにならず 0.0 が返ることをテスト"""
    raw = PitcherStatcastRawCounts(
        player_id=999999,
        year=2024,
        total_pitches=0,
        batted_balls=0,
        barrels_allowed=0,
        hard_hit_count=0,
        sum_exit_velocity=0.0,
        swings=0,
        whiffs=0,
        called_strikes=0,
    )

    stats = calculate_pitcher_statcast_stats(raw)

    assert stats.barrel_pct == 0.0
    assert stats.hard_hit_pct == 0.0
    assert stats.avg_exit_velocity == 0.0
    assert stats.whiff_pct == 0.0
    assert stats.csw_pct == 0.0


def test_calculate_pitcher_pitch_type_stats_standard():
    """投手の球種別 Statcast 指標の計算が正しく行われるかをテスト"""
    raw = PitcherPitchTypeRawCounts(
        player_id=808967,
        year=2024,
        pitch_type="FS",
        pitch_name="Split-Finger",
        pitches=250,
        total_pitches=1000,
        sum_speed=22750.0,  # 250球平均 91.0 mph
        speed_count=250,
        sum_spin_rate=350000.0,  # 250球平均 1400.0 rpm
        spin_count=250,
        sum_pfx_x=-250.0,  # -1.0 ft -> -12.0 in
        sum_pfx_z=50.0,  # 0.2 ft -> 2.4 in
        movement_count=250,
        swings=120,
        whiffs=48,
    )

    stats = calculate_pitcher_pitch_type_stats(raw)

    assert stats.pitch_type == "FS"
    assert stats.pitch_name == "Split-Finger"
    assert stats.pitches == 250
    # usage_pct: 250 / 1000 * 100 = 25.0%
    assert stats.usage_pct == 25.0
    # avg_speed: 22750 / 250 = 91.0
    assert stats.avg_speed == 91.0
    # avg_spin_rate: 350000 / 250 = 1400.0
    assert stats.avg_spin_rate == 1400.0
    # avg_pfx_x: (-250 / 250) * 12 = -12.0 inches
    assert stats.avg_pfx_x == -12.0
    # avg_pfx_z: (50 / 250) * 12 = 2.4 inches
    assert stats.avg_pfx_z == 2.4
    assert stats.swings == 120
    assert stats.whiffs == 48
    # whiff_pct: 48 / 120 * 100 = 40.0%
    assert stats.whiff_pct == 40.0


def test_calculate_pitcher_pitch_type_stats_zero_division():
    """球種別集計で各カウントが0の場合でも安全に計算されることをテスト"""
    raw = PitcherPitchTypeRawCounts(
        player_id=808967,
        year=2024,
        pitch_type="KN",
        pitch_name="Knuckleball",
        pitches=0,
        total_pitches=0,
        sum_speed=0.0,
        speed_count=0,
        sum_spin_rate=0.0,
        spin_count=0,
        sum_pfx_x=0.0,
        sum_pfx_z=0.0,
        movement_count=0,
        swings=0,
        whiffs=0,
    )

    stats = calculate_pitcher_pitch_type_stats(raw)

    assert stats.usage_pct == 0.0
    assert stats.avg_speed == 0.0
    assert stats.avg_spin_rate == 0.0
    assert stats.avg_pfx_x == 0.0
    assert stats.avg_pfx_z == 0.0
    assert stats.whiff_pct == 0.0
