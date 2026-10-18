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
   - players テーブルと結合する場合、型を揃えるために `toUInt64()` でキャストし、ReplacingMergeTree の重複排除のため必ず `FINAL` を付与: `JOIN statcast.players p FINAL ON toUInt64(s.batter) = p.player_id`
   - games テーブルと結合する場合も型をキャストして `FINAL` を付与: `JOIN statcast.games g FINAL ON toUInt64(s.game_pk) = g.game_pk`
   - teams テーブルと結合可能: `JOIN statcast.teams t ON s.home_team = t.abbreviation`
2. statcast.players:
   - 選手マスタ情報 (player_id: UInt64, full_name, primary_position_name, bat_side, pitch_hand)。ReplacingMergeTree エンジンのため JOIN 時に `FINAL` が必須。
   - 大谷翔平は full_name = 'Shohei Ohtani'、鈴木誠也は full_name = 'Seiya Suzuki'。
3. statcast.teams:
   - チームマスタ情報 (team_id: UInt32, name, abbreviation, league_name, division_name)。
   - ロサンゼルス・ドジャースは abbreviation = 'LAD'、ニューヨーク・ヤンキースは abbreviation = 'NYY'、シカゴ・カブスは abbreviation = 'CHC'。
4. statcast.games:
   - 試合結果 (game_pk: UInt64, game_date, season: UInt16, game_type, home_team_name, away_team_name, home_score, away_score)。ReplacingMergeTree エンジンのため JOIN 時に `FINAL` が必須。
5. statcast.boxscore_batting (個人打撃ボックススコア):
   - 選手個人の試合別集計成績 (game_pk: UInt64, team_id: UInt32, player_id: UInt64, plate_appearances, at_bats, hits, doubles, triples, home_runs, rbi, runs, base_on_balls, strike_outs, hit_by_pitch, sac_flies, sac_bunts, stolen_bases, total_bases 等)。
   - 選手個人のシーズン基礎指標（打席数 PA, 打数 AB, 安打 H, 本塁打 HR, 打点 RBI, 得点 R, 打率 AVG, 出塁率 OBP, 長打率 SLG, OPS等）を集計する際は【必ず本テーブル】を使用する。ReplacingMergeTree のため `JOIN statcast.players p FINAL ON bb.player_id = p.player_id` のように結合する。
6. statcast.boxscore_teams (チームボックススコア):
   - チーム全体の試合別集計成績 (game_pk: UInt64, team_id: UInt32, team_name, plate_appearances, runs, hits, home_runs 等)。
   - チーム全体のスコア・打撃指標を集計する場合にのみ使用する。選手の個人成績集計に本テーブルを使用してはならない。
7. statcast.boxscore_positions (守備位置詳細):
   - 選手の試合別守備位置履歴 (game_pk, team_id, player_id, position_code, position_name 等)。守備位置変遷の分析にのみ使用し、打撃スタッツの集計には使用しない。
        """.strip(),
    ),
    (
        "ClickHouse SQL 集計のベストプラクティス",
        """
ClickHouse クエリ作成の重要ルール:
1. ReplacingMergeTree の重複排除 (FINAL 必須 - CRITICAL):
   - `statcast.players`、`statcast.games`、`statcast.boxscore_*` テーブルは `ReplacingMergeTree` を採用しており、非同期マージ完了前は同一IDで更新前後の複数行が存在します。
   - そのため、これらのテーブルを JOIN する際は【必ずテーブルエイリアスの直前に `FINAL` 修飾子】を付与してください:
     `JOIN statcast.players p FINAL ON toUInt64(s.batter) = p.player_id`
     `JOIN statcast.games g FINAL ON toUInt64(s.game_pk) = g.game_pk`
     `FROM statcast.boxscore_batting bb FINAL`
     `FINAL` を怠ると、同一選手・試合が複数行マッチして打席数や本塁打数が2倍以上に増殖（ファンアウト）する重大な集計バグとなります。
2. 型の厳格性 (Type Strictness):
   - JOIN ON 条件のキー型は符号を含めて一致している必要があります。`statcast_raw` (Int64) と `games`/`players` (UInt64) を JOIN する際は、必ず `toUInt64(s.game_pk) = g.game_pk` や `toUInt64(s.batter) = p.player_id` と明示的にキャストしてください。
3. Statcast 打球品質指標の集計母数 (BBE - CRITICAL):
   - 平均打球初速（Avg EV / `avg(s.launch_speed)`）、最高打球初速（Max EV / `max(s.launch_speed)`）、HardHit%（初速95mph以上）、Barrel%（バレル率）、SweetSpot%（打球角度8〜32度）の公式母数は、ファウルを含まない【インプレー打球 (Batted Ball Events: `s.type = 'X' AND s.launch_speed IS NOT NULL`)】です。
   - `s.type = 'X'` の絞り込みを省略して `WHERE s.launch_speed IS NOT NULL` だけで集計するとファウル球（`type = 'S'` や `type = 'B'` のファウル）まで母数に含まれ、初速やハードヒット率が大幅に過小評価されてしまいます。必ず `s.type = 'X' AND s.launch_speed IS NOT NULL` で絞り込んでください。
4. Barrel%（バレル率）の正確な判定:
   - `statcast.statcast_raw` の `launch_speed_angle` カラムにおいて、値 `6` が「Barrel（バレル）」を表します。
   - Barrel% の計算式: `round(countIf(s.launch_speed_angle = 6) * 100.0 / count(), 2) AS barrel_pct`（母数は `s.type = 'X' AND s.launch_speed IS NOT NULL`）。
5. 選手個人スタッツ vs チームスタッツの使い分け:
   - 選手の打撃成績（PA, AB, H, HR, RBI, R, BB%, K%, AVG, OBP, SLG, OPS等）は、必ず `statcast.boxscore_batting` テーブルを集計してください。チーム成績テーブル `statcast.boxscore_teams` を選手成績集計に使用することは厳禁です。
6. シーズン集計と試合区分:
   - シーズン（年度）集計時は必ず `statcast.games` テーブルを結合し、`WHERE g.season = YYYY AND g.game_type = 'R'`（レギュラーシーズン）で絞り込んでください。
        """.strip(),
    ),
    (
        "シーズン集計と試合区分（game_type）のルール",
        """
シーズン成績・年度スタッツの集計ルール:
- シーズン（年度）の成績を求める際は、必ず statcast.games テーブルを結合する:
  `JOIN statcast.games g FINAL ON toUInt64(s.game_pk) = g.game_pk`
- ユーザーから特定の指定がない限り、「〇〇年の成績」「〇〇年打撃スタッツ」はレギュラーシーズンのみを対象とするため、必ず `g.season = YYYY` かつ `g.game_type = 'R'` で絞り込む（オープン戦 'S' やポストシーズンを除外するため）。
        """.strip(),
    ),
]

# Sample Question and SQL queries
SQL_EXAMPLES: List[Tuple[str, str]] = [
    (
        "2024年のチーム別本塁打数ランキング",
        """
SELECT
    s.home_team AS team,
    count() AS total_home_runs
FROM statcast.statcast_raw AS s
JOIN statcast.games g FINAL ON toUInt64(s.game_pk) = g.game_pk
WHERE g.season = 2024 AND g.game_type = 'R' AND s.events = 'home_run'
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
JOIN statcast.games g FINAL ON toUInt64(s.game_pk) = g.game_pk
LEFT JOIN statcast.players p FINAL ON toUInt64(s.batter) = p.player_id
WHERE g.season = 2024 AND g.game_type = 'R' AND s.type = 'X' AND s.launch_speed IS NOT NULL
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
JOIN statcast.players p FINAL ON toUInt64(s.batter) = p.player_id
JOIN statcast.games g FINAL ON toUInt64(s.game_pk) = g.game_pk
WHERE p.full_name LIKE '%Ohtani%' AND g.season = 2024 AND g.game_type = 'R' AND s.type = 'X' AND s.launch_speed IS NOT NULL
GROUP BY player_name
        """.strip(),
    ),
    (
        "村上宗隆選手の2026年打撃スタッツ（本塁打・打球初速・飛距離・投球数）",
        """
SELECT
    p.full_name AS player_name,
    countIf(s.events = 'home_run') AS home_runs,
    countIf(s.launch_speed >= 95.0) AS hard_hit_count,
    round(avg(s.launch_speed), 2) AS avg_launch_speed_mph,
    round(max(s.launch_speed), 2) AS max_launch_speed_mph,
    round(avg(s.launch_angle), 2) AS avg_launch_angle_deg,
    round(avg(s.hit_distance_sc), 2) AS avg_distance_ft,
    round(max(s.hit_distance_sc), 2) AS max_distance_ft,
    count() AS total_pitches_seen
FROM statcast.statcast_raw AS s
JOIN statcast.players p FINAL ON toUInt64(s.batter) = p.player_id
JOIN statcast.games g FINAL ON toUInt64(s.game_pk) = g.game_pk
WHERE p.full_name LIKE '%Munetaka Murakami%' AND g.season = 2026 AND g.game_type = 'R'
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
JOIN statcast.players p FINAL ON toUInt64(s.pitcher) = p.player_id
JOIN statcast.games g FINAL ON toUInt64(s.game_pk) = g.game_pk
WHERE g.season = 2024 AND g.game_type = 'R'
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
WHERE launch_angle IS NOT NULL AND launch_speed IS NOT NULL AND type = 'X'
GROUP BY angle_category
ORDER BY hits DESC
        """.strip(),
    ),
    (
        "2026年の鈴木誠也選手の打撃成績（打席数、打数、安打、本塁打、打点、打率、出塁率、長打率、OPS）",
        """
SELECT
    p.full_name AS player_name,
    sum(bb.plate_appearances) AS pa,
    sum(bb.at_bats) AS ab,
    sum(bb.hits) AS h,
    sum(bb.home_runs) AS hr,
    sum(bb.rbi) AS rbi,
    sum(bb.runs) AS r,
    round(sum(bb.base_on_balls) / nullIf(sum(bb.plate_appearances), 0), 3) AS bb_pct,
    round(sum(bb.strike_outs) / nullIf(sum(bb.plate_appearances), 0), 3) AS k_pct,
    round(sum(bb.hits) / nullIf(sum(bb.at_bats), 0), 3) AS avg,
    round((sum(bb.hits) + sum(bb.base_on_balls) + sum(bb.hit_by_pitch)) / nullIf(sum(bb.at_bats) + sum(bb.base_on_balls) + sum(bb.hit_by_pitch) + sum(bb.sac_flies), 0), 3) AS obp,
    round(sum(bb.total_bases) / nullIf(sum(bb.at_bats), 0), 3) AS slg,
    round(obp + slg, 3) AS ops
FROM statcast.boxscore_batting AS bb
JOIN statcast.players p FINAL ON bb.player_id = p.player_id
JOIN statcast.games g FINAL ON toUInt64(bb.game_pk) = g.game_pk
WHERE g.season = 2026 AND g.game_type = 'R' AND p.full_name LIKE '%Seiya Suzuki%'
GROUP BY p.player_id, p.full_name
        """.strip(),
    ),
    (
        "2026年の鈴木誠也・村上宗隆・岡本和真の打球品質指標（打球数、平均初速、最高初速、HardHit%、Barrel%、SweetSpot%）",
        """
SELECT
    p.full_name AS player_name,
    count() AS total_batted_balls,
    round(avg(s.launch_speed), 1) AS avg_launch_speed_mph,
    round(max(s.launch_speed), 1) AS max_launch_speed_mph,
    round(countIf(s.launch_speed >= 95.0) * 100.0 / count(), 1) AS hard_hit_pct,
    round(countIf(s.launch_speed_angle = 6) * 100.0 / count(), 1) AS barrel_pct,
    round(countIf(s.launch_angle BETWEEN 8 AND 32) * 100.0 / count(), 1) AS sweet_spot_pct
FROM statcast.statcast_raw AS s
JOIN statcast.players p FINAL ON toUInt64(s.batter) = p.player_id
JOIN statcast.games g FINAL ON toUInt64(s.game_pk) = g.game_pk
WHERE g.season = 2026
  AND g.game_type = 'R'
  AND s.type = 'X'
  AND s.launch_speed IS NOT NULL
  AND (p.full_name LIKE '%Seiya Suzuki%' OR p.full_name LIKE '%Munetaka Murakami%' OR p.full_name LIKE '%Kazuma Okamoto%')
GROUP BY p.full_name
ORDER BY avg_launch_speed_mph DESC
        """.strip(),
    ),
    (
        "2026年の鈴木誠也・村上宗隆・岡本和真の期待指標（打席数、期待打率xBA、期待wOBA xwOBA）",
        """
SELECT
    p.full_name AS player_name,
    countIf(s.events != '' AND s.events NOT IN ('sac_bunt', 'sac_fly', 'catcher_interf')) AS pa,
    round(avg(s.estimated_ba_using_speedangle), 3) AS xba,
    round(avg(s.estimated_woba_using_speedangle), 3) AS xwoba
FROM statcast.statcast_raw AS s
JOIN statcast.players p FINAL ON toUInt64(s.batter) = p.player_id
JOIN statcast.games g FINAL ON toUInt64(s.game_pk) = g.game_pk
WHERE g.season = 2026
  AND g.game_type = 'R'
  AND (p.full_name LIKE '%Seiya Suzuki%' OR p.full_name LIKE '%Munetaka Murakami%' OR p.full_name LIKE '%Kazuma Okamoto%')
GROUP BY p.full_name
ORDER BY xwoba DESC
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
