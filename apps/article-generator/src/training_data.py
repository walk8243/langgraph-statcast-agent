"""Statcast and MLB domain knowledge, documentation, and training data."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from src.clickhouse_client import ClickHouseClient
from src.qdrant_memory import QdrantKnowledgeStore

logger = logging.getLogger(__name__)

# Documentation on Statcast metrics and baseball terms
STATCAST_DOCS: List[Tuple[str, str]] = [
    (
        "Statcast 打球・投球指標ガイド",
        """
Statcast 主要指標解説:
- launch_speed: 打球初速 (mph)。95 mph 以上は「Hard Hit」と定義される。打球の質を測る最も重要な指標。
- launch_angle: 打球角度 (度)。8〜32度が安打になりやすい「Sweet Spot」。25〜30度付近で十分な初速があると本塁打になりやすい（Barrel）。
- hit_distance_sc: 推定飛距離 (フィート)。1フィートは約0.3048メートル。
- release_speed: 投球の初速・球速 (mph)。
- release_spin_rate: 投球の回転数 (rpm)。高回転のフォーシームはホップ成分が増え、低回転は沈みやすい。
- effective_speed: 体感速度 (mph)。投球のエクステンション（球離れの前進度）を加味した速度。
- events: 打席完了時の結果 ('home_run', 'single', 'double', 'triple', 'strikeout', 'walk', 'hit_by_pitch', 'field_out', 'force_out', 'grounded_into_double_play')。
- description: 各投球ごとの判定 ('ball', 'called_strike', 'swinging_strike', 'foul', 'hit_into_play')。
- pitch_name / pitch_type: 球種名称 ('4-Seam Fastball', 'Slider', 'Sweeper', 'Sinker', 'Changeup', 'Curveball', 'Splitter', 'Cutter' 等)。
- zone: コース番号 (1-9 はストライクゾーン、11-14 はボールゾーンの各象限)。
- game_year: 開催年度 (2024, 2025等)。
- stand: 打者の左右 ('L', 'R')。
- p_throws: 投手の左右 ('L', 'R')。
        """.strip(),
    ),
    (
        "ClickHouse テーブル構造とリレーション",
        """
ClickHouse データベース statcast 内の主要テーブル:
1. statcast.statcast_raw:
   - 全投球・打球の生データ (pitch-by-pitch)。
   - batter カラムは打者の player_id (Int64)、pitcher カラムは投手の player_id (Int64)、game_pk も Int64。
   - players テーブルと結合する場合、型を揃えるために `toUInt64()` でキャスト: `JOIN statcast.players p ON toUInt64(s.batter) = p.player_id`
   - games テーブルと結合する場合も型をキャスト: `JOIN statcast.games g ON toUInt64(s.game_pk) = g.game_pk`
   - teams テーブルと結合可能: `JOIN statcast.teams t ON s.home_team = t.abbreviation`
2. statcast.players:
   - 選手マスタ情報 (player_id: UInt64, full_name, primary_position_name, bat_side, pitch_hand)。
   - 大谷翔平は full_name = 'Shohei Ohtani'。
3. statcast.teams:
   - チームマスタ情報 (team_id: UInt32, name, abbreviation, league_name, division_name)。
   - ロサンゼルス・ドジャースは abbreviation = 'LAD'、ニューヨーク・ヤンキースは abbreviation = 'NYY'。
   - リーグ・地区別チーム一覧の取得に直接使用可能 (`SELECT league_name, division_name, name, abbreviation FROM statcast.teams WHERE active = 1 ORDER BY league_name, division_name, name`)。
4. statcast.games:
   - 試合結果 (game_pk: UInt64, game_date, season: UInt16, home_team_name, away_team_name, home_score, away_score, is_winner_home, is_winner_away)。
5. statcast.boxscore_batting / boxscore_pitching:
   - 試合ごとの選手別集計ボックススコア (game_pk: UInt64, team_id: UInt32, player_id: UInt64)。
        """.strip(),
    ),
    (
        "ClickHouse SQL 集計のベストプラクティス",
        """
ClickHouse クエリ作成の注意点:
- 型の厳格性 (Type Strictness): JOIN ON 条件のキー型は符号を含めて一致している必要があります。statcast_raw (Int64) と games/players (UInt64) を JOIN する際は、必ず `toUInt64(s.game_pk) = g.game_pk` や `toUInt64(s.batter) = p.player_id` と明示的にキャストしてください。
- 条件付き集計には `countIf(cond)`, `avgIf(col, cond)`, `sumIf(col, cond)` 関数を活用すると高速。
- 打球初速や飛距離は NULL の投球もあるため、`WHERE launch_speed IS NOT NULL` または `avg(launch_speed)` を使用する。
- 本塁打の集計は `WHERE events = 'home_run'` または `countIf(events = 'home_run')`。
- 年度別の絞り込みは `WHERE game_year = 2024` または `WHERE toYear(game_date) = 2024`。
- 文字列の部分一致は `LIKE '%keyword%'` または `ilike` を使用。
- 順位付けには `ORDER BY ... DESC LIMIT N` を使用する。
        """.strip(),
    ),
]

# Sample Question and SQL queries
SQL_EXAMPLES: List[Tuple[str, str]] = [
    (
        "2024年のチーム別本塁打数ランキング",
        """
SELECT
    home_team AS team,
    count() AS total_home_runs
FROM statcast.statcast_raw
WHERE game_year = 2024 AND events = 'home_run'
GROUP BY team
ORDER BY total_home_runs DESC
        """.strip(),
    ),
    (
        "2024年の打球初速（launch_speed）トップ10",
        """
SELECT
    p.full_name AS batter_name,
    s.game_date,
    s.launch_speed,
    s.launch_angle,
    s.hit_distance_sc,
    s.events
FROM statcast.statcast_raw AS s
LEFT JOIN statcast.players AS p ON toUInt64(s.batter) = p.player_id
WHERE s.game_year = 2024 AND s.launch_speed IS NOT NULL
ORDER BY s.launch_speed DESC
LIMIT 10
        """.strip(),
    ),
    (
        "MLB各地区のチーム一覧と所属地区",
        """
SELECT
    league_name,
    division_name,
    name AS team_name,
    abbreviation
FROM statcast.teams
WHERE active = 1
ORDER BY league_name, division_name, team_name
        """.strip(),
    ),
    (
        "球種ごとの平均球速・回転数と投球割合",
        """
SELECT
    pitch_name,
    count() AS pitch_count,
    round(count() * 100.0 / sum(count()) OVER (), 2) AS usage_pct,
    round(avg(release_speed), 1) AS avg_speed_mph,
    round(avg(release_spin_rate), 0) AS avg_spin_rpm
FROM statcast.statcast_raw
WHERE pitch_name IS NOT NULL AND pitch_name != ''
GROUP BY pitch_name
ORDER BY pitch_count DESC
        """.strip(),
    ),
    (
        "大谷翔平選手の2024年打撃指標（本塁打数、平均打球初速、最大打球初速、平均飛距離）",
        """
SELECT
    p.full_name AS player_name,
    countIf(s.events = 'home_run') AS home_runs,
    round(avg(s.launch_speed), 1) AS avg_launch_speed_mph,
    round(max(s.launch_speed), 1) AS max_launch_speed_mph,
    round(avg(s.hit_distance_sc), 1) AS avg_distance_ft
FROM statcast.statcast_raw AS s
JOIN statcast.players AS p ON toUInt64(s.batter) = p.player_id
WHERE p.full_name LIKE '%Ohtani%' AND s.game_year = 2024
GROUP BY player_name
        """.strip(),
    ),
    (
        "2024年の奪三振数トップ10投手",
        """
SELECT
    p.full_name AS pitcher_name,
    countIf(s.events = 'strikeout') AS strikeouts,
    round(avg(s.release_speed), 1) AS avg_speed_mph
FROM statcast.statcast_raw AS s
JOIN statcast.players AS p ON toUInt64(s.pitcher) = p.player_id
WHERE s.game_year = 2024
GROUP BY pitcher_name
ORDER BY strikeouts DESC
LIMIT 10
        """.strip(),
    ),
    (
        "打球角度と打撃結果の相関（角度帯ごとの本塁打・安打・打球数集計）",
        """
SELECT
    multiIf(
        launch_angle < 10, 'Ground ball (< 10°)',
        launch_angle < 25, 'Line drive (10-25°)',
        launch_angle < 40, 'Fly ball (25-40°)',
        'Pop up (>= 40°)'
    ) AS angle_category,
    count() AS total_batted_balls,
    countIf(events = 'home_run') AS home_runs,
    countIf(events IN ('single', 'double', 'triple', 'home_run')) AS hits,
    round(avg(launch_speed), 1) AS avg_exit_velocity
FROM statcast.statcast_raw
WHERE launch_angle IS NOT NULL AND launch_speed IS NOT NULL
GROUP BY angle_category
ORDER BY hits DESC
        """.strip(),
    ),
]


def train_knowledge_base(
    store: QdrantKnowledgeStore,
    clickhouse: ClickHouseClient,
) -> Dict[str, int]:
    """Train/populate Qdrant with ClickHouse schema DDL, documentation, and SQL examples.

    Args:
        store: QdrantKnowledgeStore instance.
        clickhouse: ClickHouseClient instance.

    Returns:
        Summary counts of registered items.
    """
    store.ensure_collection()

    ddl_count = 0
    doc_count = 0
    sql_count = 0

    # 1. Register live ClickHouse DDLs
    try:
        schemas = clickhouse.get_table_schemas()
        for table_name, ddl in schemas.items():
            store.add_ddl(table_name, ddl)
            ddl_count += 1
            logger.info(f"Registered DDL for table: {table_name}")
    except Exception as e:
        logger.warning(f"Could not fetch live schemas from ClickHouse ({e}), registering static DDL")
        # Static fallback if ClickHouse is not yet populated
        store.add_ddl(
            "statcast_raw",
            "CREATE TABLE statcast.statcast_raw (game_date Date, batter Int64, pitcher Int64, events Nullable(String), launch_speed Nullable(Float64), launch_angle Nullable(Float64), hit_distance_sc Nullable(Float64), release_speed Nullable(Float64), release_spin_rate Nullable(Float64), pitch_name Nullable(String), game_year Nullable(Int64), home_team Nullable(String), away_team Nullable(String))",
        )
        ddl_count += 1

    # 2. Register Documentation
    for title, content in STATCAST_DOCS:
        store.add_documentation(title, content)
        doc_count += 1
        logger.info(f"Registered documentation: {title}")

    # 3. Register Sample SQL queries
    for question, sql in SQL_EXAMPLES:
        store.add_sql_example(question, sql)
        sql_count += 1
        logger.info(f"Registered SQL example: {question}")

    total = ddl_count + doc_count + sql_count
    logger.info(f"Training completed: {total} items registered to Qdrant.")
    return {
        "ddls": ddl_count,
        "docs": doc_count,
        "sql_examples": sql_count,
        "total": total,
    }
