-- チームマスタテーブル定義（結合キー・画面表示用）
CREATE TABLE IF NOT EXISTS teams (
    team_id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    abbreviation VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 選手マスタテーブル定義
CREATE TABLE IF NOT EXISTS players (
    player_id BIGINT PRIMARY KEY,
    name_en VARCHAR(255) NOT NULL,
    name_ja VARCHAR(255),
    team_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

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

