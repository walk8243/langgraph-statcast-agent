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
    risp_plate_appearances: int = 0
    risp_at_bats: int = 0
    risp_hits: int = 0


class BatterSeasonStats(BatterRawCounts):
    """率系指標を含めた打者シーズン基本指標"""

    batting_average: float = Field(default=0.0, description="打率 (AVG)")
    on_base_percentage: float = Field(default=0.0, description="出塁率 (OBP)")
    slugging_percentage: float = Field(default=0.0, description="長打率 (SLG)")
    ops: float = Field(default=0.0, description="OPS (OBP + SLG)")
    risp_batting_average: float = Field(default=0.0, description="得点圏打率 (RISP AVG)")


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

    # 得点圏打率 (RISP AVG) = RISP_H / RISP_AB
    risp_ba = (
        round(raw.risp_hits / raw.risp_at_bats, 3)
        if raw.risp_at_bats > 0
        else 0.0
    )

    data = raw.model_dump()
    data.update(
        {
            "batting_average": ba,
            "on_base_percentage": obp,
            "slugging_percentage": slg,
            "ops": ops,
            "risp_batting_average": risp_ba,
        }
    )
    return BatterSeasonStats(**data)
