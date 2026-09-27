-- チームマスタテーブル定義（結合キー・画面表示用）
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


-- 選手マスタテーブル定義
CREATE TABLE IF NOT EXISTS players (
    player_id BIGINT PRIMARY KEY,
    name_en VARCHAR(255) NOT NULL,
    name_ja VARCHAR(255),
    team_id BIGINT,
    primary_number VARCHAR(10),
    primary_position_code VARCHAR(10),
    primary_position_name VARCHAR(50),
    primary_position_type VARCHAR(50),
    primary_position_abbreviation VARCHAR(10),
    bat_side VARCHAR(10),
    pitch_hand VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE players ADD COLUMN IF NOT EXISTS primary_number VARCHAR(10);
ALTER TABLE players ADD COLUMN IF NOT EXISTS primary_position_code VARCHAR(10);
ALTER TABLE players ADD COLUMN IF NOT EXISTS primary_position_name VARCHAR(50);
ALTER TABLE players ADD COLUMN IF NOT EXISTS primary_position_type VARCHAR(50);
ALTER TABLE players ADD COLUMN IF NOT EXISTS primary_position_abbreviation VARCHAR(10);
ALTER TABLE players ADD COLUMN IF NOT EXISTS bat_side VARCHAR(10);
ALTER TABLE players ADD COLUMN IF NOT EXISTS pitch_hand VARCHAR(10);

CREATE INDEX IF NOT EXISTS idx_players_team_id ON players (team_id);

-- 試合テーブル定義（試合メタデータ、対戦カード、スコア、チーム結合用）
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

-- 打者シーズン基本指標テーブル定義
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

-- 投手シーズン基本指標テーブル定義
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

-- 選手解説レポートテーブル定義（LangGraph エージェント生成結果の保存）
CREATE TABLE IF NOT EXISTS player_reports (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT NOT NULL,
    year INT NOT NULL,
    report_text TEXT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (player_id, year)
);

CREATE INDEX IF NOT EXISTS idx_player_reports_player_year ON player_reports (player_id, year);

-- 打者 Statcast 詳細指標テーブル定義
CREATE TABLE IF NOT EXISTS batter_statcast_stats (
    player_id BIGINT NOT NULL,
    year INT NOT NULL,
    pitches_seen INT NOT NULL DEFAULT 0,
    batted_balls INT NOT NULL DEFAULT 0,
    barrels INT NOT NULL DEFAULT 0,
    barrel_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    hard_hit_count INT NOT NULL DEFAULT 0,
    hard_hit_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    avg_exit_velocity NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    max_exit_velocity NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    avg_launch_angle NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    sweet_spot_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, year)
);

CREATE INDEX IF NOT EXISTS idx_batter_statcast_stats_year ON batter_statcast_stats (year);

-- 投手 Statcast 総合詳細指標テーブル定義
CREATE TABLE IF NOT EXISTS pitcher_statcast_stats (
    player_id BIGINT NOT NULL,
    year INT NOT NULL,
    total_pitches INT NOT NULL DEFAULT 0,
    batted_balls INT NOT NULL DEFAULT 0,
    barrels_allowed INT NOT NULL DEFAULT 0,
    barrel_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    hard_hit_count INT NOT NULL DEFAULT 0,
    hard_hit_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    avg_exit_velocity NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    swings INT NOT NULL DEFAULT 0,
    whiffs INT NOT NULL DEFAULT 0,
    whiff_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    called_strikes INT NOT NULL DEFAULT 0,
    csw_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, year)
);

CREATE INDEX IF NOT EXISTS idx_pitcher_statcast_stats_year ON pitcher_statcast_stats (year);

-- 投手球種別 Statcast 指標テーブル定義
CREATE TABLE IF NOT EXISTS pitcher_pitch_type_stats (
    player_id BIGINT NOT NULL,
    year INT NOT NULL,
    pitch_type VARCHAR(10) NOT NULL,
    pitch_name VARCHAR(50) NOT NULL DEFAULT '',
    pitches INT NOT NULL DEFAULT 0,
    usage_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    avg_speed NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    avg_spin_rate NUMERIC(6, 1) NOT NULL DEFAULT 0.0,
    avg_pfx_x NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    avg_pfx_z NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    swings INT NOT NULL DEFAULT 0,
    whiffs INT NOT NULL DEFAULT 0,
    whiff_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, year, pitch_type)
);

CREATE INDEX IF NOT EXISTS idx_pitcher_pitch_type_stats_player_year ON pitcher_pitch_type_stats (player_id, year);

-- ========================================================
-- 試合速報用テーブル群 (Real-time Live Game Data)
-- ========================================================

-- 試合進行・スコアボード状況テーブル
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
    current_batter_id BIGINT REFERENCES players(player_id) ON DELETE SET NULL,
    current_pitcher_id BIGINT REFERENCES players(player_id) ON DELETE SET NULL,
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

-- 打席ごとの結果情報テーブル
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

-- 1球ごとの投球・Statcast情報テーブル
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
