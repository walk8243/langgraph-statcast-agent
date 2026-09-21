-- 選手マスタテーブル定義
CREATE TABLE IF NOT EXISTS players (
    player_id BIGINT PRIMARY KEY,
    name_en VARCHAR(255) NOT NULL,
    name_ja VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 打者シーズン基本指標テーブル定義
CREATE TABLE IF NOT EXISTS batter_season_stats (
    player_id BIGINT NOT NULL,
    year INT NOT NULL,
    games INT NOT NULL DEFAULT 0,
    plate_appearances INT NOT NULL DEFAULT 0,
    at_bats INT NOT NULL DEFAULT 0,
    hits INT NOT NULL DEFAULT 0,
    doubles INT NOT NULL DEFAULT 0,
    triples INT NOT NULL DEFAULT 0,
    home_runs INT NOT NULL DEFAULT 0,
    total_bases INT NOT NULL DEFAULT 0,
    strikeouts INT NOT NULL DEFAULT 0,
    walks INT NOT NULL DEFAULT 0,
    hit_by_pitch INT NOT NULL DEFAULT 0,
    sac_bunts INT NOT NULL DEFAULT 0,
    sac_flies INT NOT NULL DEFAULT 0,
    grounded_into_double_play INT NOT NULL DEFAULT 0,
    batting_average NUMERIC(5, 3) NOT NULL DEFAULT 0.000,
    on_base_percentage NUMERIC(5, 3) NOT NULL DEFAULT 0.000,
    slugging_percentage NUMERIC(5, 3) NOT NULL DEFAULT 0.000,
    ops NUMERIC(5, 3) NOT NULL DEFAULT 0.000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, year)
);

CREATE INDEX IF NOT EXISTS idx_batter_season_stats_year ON batter_season_stats (year);

