"""PostgreSQL 接続および初期化ユーティリティモジュール (Ingestion)"""

from __future__ import annotations

import os
from typing import Optional
import psycopg
from psycopg.rows import dict_row


def get_postgres_connection(
    host: Optional[str] = None,
    port: Optional[int] = None,
    dbname: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
) -> psycopg.Connection:
    """PostgreSQL 接続を取得する"""
    return psycopg.connect(
        host=host or os.getenv("POSTGRES_HOST", "localhost"),
        port=int(port or os.getenv("POSTGRES_PORT", 5432)),
        dbname=dbname or os.getenv("POSTGRES_DB", "statcast"),
        user=user or os.getenv("POSTGRES_USER", "statcast"),
        password=password or os.getenv("POSTGRES_PASSWORD", "statcast_pass"),
        row_factory=dict_row,
    )


DEFAULT_INIT_DDL = """
CREATE TABLE IF NOT EXISTS teams (
    team_id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    abbreviation VARCHAR(10) NOT NULL,
    league_id BIGINT,
    league_name VARCHAR(100),
    division_id BIGINT,
    division_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE teams ADD COLUMN IF NOT EXISTS league_id BIGINT;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS league_name VARCHAR(100);
ALTER TABLE teams ADD COLUMN IF NOT EXISTS division_id BIGINT;
ALTER TABLE teams ADD COLUMN IF NOT EXISTS division_name VARCHAR(100);

CREATE TABLE IF NOT EXISTS players (
    player_id BIGINT PRIMARY KEY,
    name_en VARCHAR(255) NOT NULL,
    name_ja VARCHAR(255),
    team_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE players ADD COLUMN IF NOT EXISTS team_id BIGINT;
CREATE INDEX IF NOT EXISTS idx_players_team_id ON players (team_id);

CREATE TABLE IF NOT EXISTS games (
    game_pk BIGINT PRIMARY KEY,
    game_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    season INT NOT NULL,
    game_type VARCHAR(10),
    status VARCHAR(50),
    home_team_id BIGINT,
    away_team_id BIGINT,
    home_score INT,
    away_score INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_games_game_date_time ON games (game_date_time);
CREATE INDEX IF NOT EXISTS idx_games_season ON games (season);
CREATE INDEX IF NOT EXISTS idx_games_home_team_id ON games (home_team_id);
CREATE INDEX IF NOT EXISTS idx_games_away_team_id ON games (away_team_id);

CREATE TABLE IF NOT EXISTS batter_season_stats (
    player_id BIGINT NOT NULL,
    year INT NOT NULL,
    games INT NOT NULL DEFAULT 0,
    plate_appearances INT NOT NULL DEFAULT 0,
    at_bats INT NOT NULL DEFAULT 0,
    runs INT NOT NULL DEFAULT 0,
    hits INT NOT NULL DEFAULT 0,
    doubles INT NOT NULL DEFAULT 0,
    triples INT NOT NULL DEFAULT 0,
    home_runs INT NOT NULL DEFAULT 0,
    rbi INT NOT NULL DEFAULT 0,
    total_bases INT NOT NULL DEFAULT 0,
    strikeouts INT NOT NULL DEFAULT 0,
    walks INT NOT NULL DEFAULT 0,
    intentional_walks INT NOT NULL DEFAULT 0,
    hit_by_pitch INT NOT NULL DEFAULT 0,
    sac_bunts INT NOT NULL DEFAULT 0,
    sac_flies INT NOT NULL DEFAULT 0,
    grounded_into_double_play INT NOT NULL DEFAULT 0,
    stolen_bases INT NOT NULL DEFAULT 0,
    caught_stealing INT NOT NULL DEFAULT 0,
    batting_average NUMERIC(5, 3) NOT NULL DEFAULT 0.000,
    on_base_percentage NUMERIC(5, 3) NOT NULL DEFAULT 0.000,
    slugging_percentage NUMERIC(5, 3) NOT NULL DEFAULT 0.000,
    ops NUMERIC(5, 3) NOT NULL DEFAULT 0.000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, year)
);

ALTER TABLE batter_season_stats ADD COLUMN IF NOT EXISTS runs INT NOT NULL DEFAULT 0;
ALTER TABLE batter_season_stats ADD COLUMN IF NOT EXISTS rbi INT NOT NULL DEFAULT 0;
ALTER TABLE batter_season_stats ADD COLUMN IF NOT EXISTS intentional_walks INT NOT NULL DEFAULT 0;
ALTER TABLE batter_season_stats ADD COLUMN IF NOT EXISTS stolen_bases INT NOT NULL DEFAULT 0;
ALTER TABLE batter_season_stats ADD COLUMN IF NOT EXISTS caught_stealing INT NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_batter_season_stats_year ON batter_season_stats (year);

CREATE TABLE IF NOT EXISTS pitcher_season_stats (
    player_id BIGINT NOT NULL,
    year INT NOT NULL,
    wins INT NOT NULL DEFAULT 0,
    losses INT NOT NULL DEFAULT 0,
    era NUMERIC(6, 2) NOT NULL DEFAULT 0.00,
    games_pitched INT NOT NULL DEFAULT 0,
    games_started INT NOT NULL DEFAULT 0,
    complete_games INT NOT NULL DEFAULT 0,
    shutouts INT NOT NULL DEFAULT 0,
    saves INT NOT NULL DEFAULT 0,
    save_opportunities INT NOT NULL DEFAULT 0,
    holds INT NOT NULL DEFAULT 0,
    blown_saves INT NOT NULL DEFAULT 0,
    innings_pitched VARCHAR(10) NOT NULL DEFAULT '0.0',
    outs INT NOT NULL DEFAULT 0,
    hits INT NOT NULL DEFAULT 0,
    runs INT NOT NULL DEFAULT 0,
    earned_runs INT NOT NULL DEFAULT 0,
    home_runs INT NOT NULL DEFAULT 0,
    walks INT NOT NULL DEFAULT 0,
    intentional_walks INT NOT NULL DEFAULT 0,
    strikeouts INT NOT NULL DEFAULT 0,
    hit_by_pitch INT NOT NULL DEFAULT 0,
    whip NUMERIC(6, 2) NOT NULL DEFAULT 0.00,
    batting_average_against NUMERIC(5, 3) NOT NULL DEFAULT 0.000,
    batters_faced INT NOT NULL DEFAULT 0,
    number_of_pitches INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, year)
);

CREATE INDEX IF NOT EXISTS idx_pitcher_season_stats_year ON pitcher_season_stats (year);

CREATE TABLE IF NOT EXISTS live_linescores (
    game_pk BIGINT PRIMARY KEY REFERENCES games(game_pk) ON DELETE CASCADE,
    current_inning INT NOT NULL DEFAULT 1,
    current_inning_ordinal VARCHAR(10) DEFAULT '1st',
    inning_state VARCHAR(20) DEFAULT 'Top',
    inning_half VARCHAR(10) DEFAULT 'top',
    is_top_inning BOOLEAN NOT NULL DEFAULT TRUE,
    scheduled_innings INT DEFAULT 9,
    balls INT NOT NULL DEFAULT 0,
    strikes INT NOT NULL DEFAULT 0,
    outs INT NOT NULL DEFAULT 0,
    first_base_runner_id BIGINT REFERENCES players(player_id) ON DELETE SET NULL,
    second_base_runner_id BIGINT REFERENCES players(player_id) ON DELETE SET NULL,
    third_base_runner_id BIGINT REFERENCES players(player_id) ON DELETE SET NULL,
    home_score INT NOT NULL DEFAULT 0,
    away_score INT NOT NULL DEFAULT 0,
    home_hits INT NOT NULL DEFAULT 0,
    away_hits INT NOT NULL DEFAULT 0,
    home_errors INT NOT NULL DEFAULT 0,
    away_errors INT NOT NULL DEFAULT 0,
    innings_json JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS live_plays (
    game_pk BIGINT NOT NULL REFERENCES games(game_pk) ON DELETE CASCADE,
    at_bat_index INT NOT NULL,
    inning INT NOT NULL,
    half_inning VARCHAR(10) NOT NULL,
    is_top_inning BOOLEAN NOT NULL,
    batter_id BIGINT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    pitcher_id BIGINT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    event VARCHAR(100),
    event_type VARCHAR(100),
    description TEXT,
    rbi INT NOT NULL DEFAULT 0,
    away_score INT NOT NULL DEFAULT 0,
    home_score INT NOT NULL DEFAULT 0,
    is_scoring_play BOOLEAN NOT NULL DEFAULT FALSE,
    is_out BOOLEAN NOT NULL DEFAULT FALSE,
    is_complete BOOLEAN NOT NULL DEFAULT FALSE,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_pk, at_bat_index)
);

CREATE INDEX IF NOT EXISTS idx_live_plays_game_inning ON live_plays (game_pk, inning);
CREATE INDEX IF NOT EXISTS idx_live_plays_batter ON live_plays (batter_id);
CREATE INDEX IF NOT EXISTS idx_live_plays_pitcher ON live_plays (pitcher_id);

CREATE TABLE IF NOT EXISTS live_pitches (
    game_pk BIGINT NOT NULL,
    at_bat_index INT NOT NULL,
    pitch_number INT NOT NULL,
    play_id VARCHAR(50),
    pitch_type VARCHAR(10),
    pitch_name VARCHAR(50),
    start_speed NUMERIC(5, 2),
    end_speed NUMERIC(5, 2),
    zone INT,
    p_x NUMERIC(6, 3),
    p_z NUMERIC(6, 3),
    spin_rate NUMERIC(6, 1),
    spin_direction INT,
    break_angle NUMERIC(5, 2),
    break_vertical NUMERIC(5, 2),
    break_vertical_induced NUMERIC(5, 2),
    break_horizontal NUMERIC(5, 2),
    call_code VARCHAR(10),
    call_description VARCHAR(50),
    description TEXT,
    balls INT NOT NULL DEFAULT 0,
    strikes INT NOT NULL DEFAULT 0,
    outs INT NOT NULL DEFAULT 0,
    is_strike BOOLEAN NOT NULL DEFAULT FALSE,
    is_ball BOOLEAN NOT NULL DEFAULT FALSE,
    is_in_play BOOLEAN NOT NULL DEFAULT FALSE,
    is_pitch BOOLEAN NOT NULL DEFAULT TRUE,
    launch_speed NUMERIC(5, 2),
    launch_angle NUMERIC(5, 2),
    total_distance INT,
    trajectory VARCHAR(50),
    hardness VARCHAR(20),
    hit_location VARCHAR(10),
    coord_x NUMERIC(6, 2),
    coord_y NUMERIC(6, 2),
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_pk, at_bat_index, pitch_number),
    FOREIGN KEY (game_pk, at_bat_index) REFERENCES live_plays(game_pk, at_bat_index) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_live_pitches_game_play ON live_pitches (game_pk, at_bat_index);
"""


def initialize_tables(conn: psycopg.Connection, ddl_path: Optional[str] = None) -> None:
    """初期化 DDL を実行して PostgreSQL テーブルを作成する"""
    if not ddl_path:
        ddl_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "docker", "postgres", "init.sql"
        )
        ddl_path = os.path.abspath(ddl_path)

    if os.path.exists(ddl_path):
        with open(ddl_path, encoding="utf-8") as f:
            sql = f.read()
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS team_id BIGINT;")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_players_team_id ON players (team_id);")
        conn.commit()
    else:
        # コンテナ環境などでファイルがマウントされていない場合のフォールバック
        with conn.cursor() as cur:
            cur.execute(DEFAULT_INIT_DDL)
        conn.commit()
