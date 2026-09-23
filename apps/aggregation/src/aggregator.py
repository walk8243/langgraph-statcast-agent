"""打者基本指標の集計および計算モジュール"""

from __future__ import annotations

from pydantic import BaseModel, Field


class BatterRawCounts(BaseModel):
    """ClickHouse から抽出された打者のカウント指標"""

    player_id: int
    year: int
    games: int = 0
    plate_appearances: int = 0
    at_bats: int = 0
    hits: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    total_bases: int = 0
    strikeouts: int = 0
    walks: int = 0
    hit_by_pitch: int = 0
    sac_bunts: int = 0
    sac_flies: int = 0
    grounded_into_double_play: int = 0


class BatterSeasonStats(BatterRawCounts):
    """率系指標を含めた打者シーズン基本指標"""

    batting_average: float = Field(default=0.0, description="打率 (AVG)")
    on_base_percentage: float = Field(default=0.0, description="出塁率 (OBP)")
    slugging_percentage: float = Field(default=0.0, description="長打率 (SLG)")
    ops: float = Field(default=0.0, description="OPS (OBP + SLG)")


def calculate_batter_stats(raw: BatterRawCounts) -> BatterSeasonStats:
    """カウント指標から各種率系指標を算出し、BatterSeasonStats を生成する"""
    # 打率 (AVG) = H / AB
    ba = round(raw.hits / raw.at_bats, 3) if raw.at_bats > 0 else 0.0

    # 出塁率 (OBP) = (H + BB + HBP) / (AB + BB + HBP + SF)
    obp_denom = raw.at_bats + raw.walks + raw.hit_by_pitch + raw.sac_flies
    obp = round((raw.hits + raw.walks + raw.hit_by_pitch) / obp_denom, 3) if obp_denom > 0 else 0.0

    # 長打率 (SLG) = TB / AB
    slg = round(raw.total_bases / raw.at_bats, 3) if raw.at_bats > 0 else 0.0

    # OPS = OBP + SLG
    ops = round(obp + slg, 3)

    data = raw.model_dump()
    data.update(
        {
            "batting_average": ba,
            "on_base_percentage": obp,
            "slugging_percentage": slg,
            "ops": ops,
        }
    )
    return BatterSeasonStats(**data)


class BatterStatcastRawCounts(BaseModel):
    """ClickHouse から抽出された打者の Statcast 生カウント・集計値"""

    player_id: int
    year: int
    pitches_seen: int = 0
    batted_balls: int = 0
    barrels: int = 0
    hard_hit_count: int = 0
    sum_exit_velocity: float = 0.0
    max_exit_velocity: float = 0.0
    sum_launch_angle: float = 0.0
    sweet_spot_count: int = 0


class BatterStatcastStats(BaseModel):
    """打者の Statcast 詳細指標"""

    player_id: int
    year: int
    pitches_seen: int = 0
    batted_balls: int = 0
    barrels: int = 0
    barrel_pct: float = Field(default=0.0, description="Barrel% (barrels / batted_balls * 100)")
    hard_hit_count: int = 0
    hard_hit_pct: float = Field(default=0.0, description="HardHit% (hard_hit_count / batted_balls * 100)")
    avg_exit_velocity: float = Field(default=0.0, description="平均打球速度 (mph)")
    max_exit_velocity: float = Field(default=0.0, description="最高打球速度 (mph)")
    avg_launch_angle: float = Field(default=0.0, description="平均打球角度 (度)")
    sweet_spot_pct: float = Field(default=0.0, description="SweetSpot% (8-32度 / batted_balls * 100)")


def calculate_batter_statcast_stats(raw: BatterStatcastRawCounts) -> BatterStatcastStats:
    """打者の Statcast 生カウントから率指標を計算する"""
    bb = raw.batted_balls
    barrel_pct = round((raw.barrels / bb) * 100, 2) if bb > 0 else 0.0
    hard_hit_pct = round((raw.hard_hit_count / bb) * 100, 2) if bb > 0 else 0.0
    avg_ev = round(raw.sum_exit_velocity / bb, 2) if bb > 0 else 0.0
    max_ev = round(raw.max_exit_velocity, 2)
    avg_la = round(raw.sum_launch_angle / bb, 2) if bb > 0 else 0.0
    sweet_spot_pct = round((raw.sweet_spot_count / bb) * 100, 2) if bb > 0 else 0.0

    return BatterStatcastStats(
        player_id=raw.player_id,
        year=raw.year,
        pitches_seen=raw.pitches_seen,
        batted_balls=bb,
        barrels=raw.barrels,
        barrel_pct=barrel_pct,
        hard_hit_count=raw.hard_hit_count,
        hard_hit_pct=hard_hit_pct,
        avg_exit_velocity=avg_ev,
        max_exit_velocity=max_ev,
        avg_launch_angle=avg_la,
        sweet_spot_pct=sweet_spot_pct,
    )


class PitcherStatcastRawCounts(BaseModel):
    """ClickHouse から抽出された投手の Statcast 総合生カウント・集計値"""

    player_id: int
    year: int
    total_pitches: int = 0
    batted_balls: int = 0
    barrels_allowed: int = 0
    hard_hit_count: int = 0
    sum_exit_velocity: float = 0.0
    swings: int = 0
    whiffs: int = 0
    called_strikes: int = 0


class PitcherStatcastStats(BaseModel):
    """投手の Statcast 総合詳細指標"""

    player_id: int
    year: int
    total_pitches: int = 0
    batted_balls: int = 0
    barrels_allowed: int = 0
    barrel_pct: float = Field(default=0.0, description="被Barrel% (barrels_allowed / batted_balls * 100)")
    hard_hit_count: int = 0
    hard_hit_pct: float = Field(default=0.0, description="被HardHit% (hard_hit_count / batted_balls * 100)")
    avg_exit_velocity: float = Field(default=0.0, description="平均被打球速度 (mph)")
    swings: int = 0
    whiffs: int = 0
    whiff_pct: float = Field(default=0.0, description="Whiff% (whiffs / swings * 100)")
    called_strikes: int = 0
    csw_pct: float = Field(default=0.0, description="CSW% ((called_strikes + whiffs) / total_pitches * 100)")


def calculate_pitcher_statcast_stats(raw: PitcherStatcastRawCounts) -> PitcherStatcastStats:
    """投手の Statcast 生カウントから率指標を計算する"""
    bb = raw.batted_balls
    barrel_pct = round((raw.barrels_allowed / bb) * 100, 2) if bb > 0 else 0.0
    hard_hit_pct = round((raw.hard_hit_count / bb) * 100, 2) if bb > 0 else 0.0
    avg_ev = round(raw.sum_exit_velocity / bb, 2) if bb > 0 else 0.0

    swings = raw.swings
    whiff_pct = round((raw.whiffs / swings) * 100, 2) if swings > 0 else 0.0

    total_p = raw.total_pitches
    csw_pct = (
        round(((raw.called_strikes + raw.whiffs) / total_p) * 100, 2)
        if total_p > 0
        else 0.0
    )

    return PitcherStatcastStats(
        player_id=raw.player_id,
        year=raw.year,
        total_pitches=total_p,
        batted_balls=bb,
        barrels_allowed=raw.barrels_allowed,
        barrel_pct=barrel_pct,
        hard_hit_count=raw.hard_hit_count,
        hard_hit_pct=hard_hit_pct,
        avg_exit_velocity=avg_ev,
        swings=swings,
        whiffs=raw.whiffs,
        whiff_pct=whiff_pct,
        called_strikes=raw.called_strikes,
        csw_pct=csw_pct,
    )


class PitcherPitchTypeRawCounts(BaseModel):
    """ClickHouse から抽出された球種別生カウント・集計値"""

    player_id: int
    year: int
    pitch_type: str
    pitch_name: str = ""
    pitches: int = 0
    total_pitches: int = 0
    sum_speed: float = 0.0
    speed_count: int = 0
    sum_spin_rate: float = 0.0
    spin_count: int = 0
    sum_pfx_x: float = 0.0
    sum_pfx_z: float = 0.0
    movement_count: int = 0
    swings: int = 0
    whiffs: int = 0


class PitcherPitchTypeStats(BaseModel):
    """投手の球種別 Statcast 指標"""

    player_id: int
    year: int
    pitch_type: str
    pitch_name: str = ""
    pitches: int = 0
    usage_pct: float = Field(default=0.0, description="球種投球割合 (%)")
    avg_speed: float = Field(default=0.0, description="平均球速 (mph)")
    avg_spin_rate: float = Field(default=0.0, description="平均回転数 (rpm)")
    avg_pfx_x: float = Field(default=0.0, description="平均水平変化量 (inches)")
    avg_pfx_z: float = Field(default=0.0, description="平均垂直変化量 (inches)")
    swings: int = 0
    whiffs: int = 0
    whiff_pct: float = Field(default=0.0, description="Whiff% (whiffs / swings * 100)")


def calculate_pitcher_pitch_type_stats(raw: PitcherPitchTypeRawCounts) -> PitcherPitchTypeStats:
    """球種別の生カウントから率指標・平均値を計算する"""
    usage_pct = (
        round((raw.pitches / raw.total_pitches) * 100, 2)
        if raw.total_pitches > 0
        else 0.0
    )
    avg_speed = (
        round(raw.sum_speed / raw.speed_count, 2) if raw.speed_count > 0 else 0.0
    )
    avg_spin = (
        round(raw.sum_spin_rate / raw.spin_count, 1) if raw.spin_count > 0 else 0.0
    )
    # pfx_x and pfx_z are in feet in Statcast, convert to inches (* 12)
    avg_pfx_x = (
        round((raw.sum_pfx_x / raw.movement_count) * 12, 2)
        if raw.movement_count > 0
        else 0.0
    )
    avg_pfx_z = (
        round((raw.sum_pfx_z / raw.movement_count) * 12, 2)
        if raw.movement_count > 0
        else 0.0
    )
    whiff_pct = (
        round((raw.whiffs / raw.swings) * 100, 2) if raw.swings > 0 else 0.0
    )

    return PitcherPitchTypeStats(
        player_id=raw.player_id,
        year=raw.year,
        pitch_type=raw.pitch_type,
        pitch_name=raw.pitch_name,
        pitches=raw.pitches,
        usage_pct=usage_pct,
        avg_speed=avg_speed,
        avg_spin_rate=avg_spin,
        avg_pfx_x=avg_pfx_x,
        avg_pfx_z=avg_pfx_z,
        swings=raw.swings,
        whiffs=raw.whiffs,
        whiff_pct=whiff_pct,
    )

