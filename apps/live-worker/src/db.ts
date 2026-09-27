/**
 * PostgreSQL 永続化モジュール (live_linescores, live_plays, live_pitches)
 */

import pg, { Pool, PoolClient } from "pg";
import {
  DiffResult,
  GameInfo,
  LiveLinescoreRecord,
  LivePitchRecord,
  LivePlayRecord,
  PlayerRecord,
} from "./types.js";

export const DEFAULT_LIVE_DDL = `
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

CREATE TABLE IF NOT EXISTS players (
    player_id BIGINT PRIMARY KEY,
    name_en VARCHAR(255) NOT NULL,
    name_ja VARCHAR(255),
    team_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS live_linescores (
    game_pk BIGINT PRIMARY KEY REFERENCES games(game_pk) ON DELETE CASCADE,
    current_inning INT NOT NULL DEFAULT 1,
    is_top_inning BOOLEAN NOT NULL DEFAULT TRUE,
    scheduled_innings INT DEFAULT 9,
    balls INT NOT NULL DEFAULT 0,
    strikes INT NOT NULL DEFAULT 0,
    outs INT NOT NULL DEFAULT 0,
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
    first_base_runner_id BIGINT REFERENCES players(player_id) ON DELETE SET NULL,
    second_base_runner_id BIGINT REFERENCES players(player_id) ON DELETE SET NULL,
    third_base_runner_id BIGINT REFERENCES players(player_id) ON DELETE SET NULL,
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
`;

export function createDbPool(config?: pg.PoolConfig): Pool {
  return new pg.Pool({
    host: config?.host || process.env.POSTGRES_HOST || "localhost",
    port: config?.port || parseInt(process.env.POSTGRES_PORT || "5432", 10),
    database: config?.database || process.env.POSTGRES_DB || "statcast",
    user: config?.user || process.env.POSTGRES_USER || "statcast",
    password: config?.password || process.env.POSTGRES_PASSWORD || "statcast_pass",
    max: config?.max || 10,
    idleTimeoutMillis: config?.idleTimeoutMillis || 30000,
  });
}

export async function initializeTables(poolOrClient: Pool | PoolClient): Promise<void> {
  await poolOrClient.query(DEFAULT_LIVE_DDL);
}

export async function findInProgressGames(poolOrClient: Pool | PoolClient): Promise<number[]> {
  const sql = `
    SELECT game_pk
    FROM games
    WHERE status ILIKE '%Progress%' OR status = 'Live'
    ORDER BY game_date_time ASC;
  `;
  const res = await poolOrClient.query(sql);
  return res.rows.map((r: any) => parseInt(r.game_pk, 10));
}

export async function upsertGameRecord(client: PoolClient, game: GameInfo): Promise<void> {
  if (!game.game_pk) return;
  const sql = `
    INSERT INTO games (
        game_pk, game_date_time, season, game_type, status,
        home_team_id, away_team_id, home_score, away_score,
        updated_at
    ) VALUES (
        $1, $2, $3, $4, $5,
        $6, $7, $8, $9,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (game_pk) DO UPDATE SET
        status = EXCLUDED.status,
        home_score = COALESCE(EXCLUDED.home_score, games.home_score),
        away_score = COALESCE(EXCLUDED.away_score, games.away_score),
        updated_at = CURRENT_TIMESTAMP;
  `;
  await client.query(sql, [
    game.game_pk,
    game.game_date_time,
    game.season,
    game.game_type,
    game.status,
    game.home_team_id,
    game.away_team_id,
    game.home_score,
    game.away_score,
  ]);
}

export async function upsertPlayers(client: PoolClient, players: PlayerRecord[]): Promise<void> {
  if (!players.length) return;
  const sql = `
    INSERT INTO players (player_id, name_en, team_id, updated_at)
    VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
    ON CONFLICT (player_id) DO UPDATE SET
        name_en = EXCLUDED.name_en,
        team_id = COALESCE(EXCLUDED.team_id, players.team_id),
        updated_at = CURRENT_TIMESTAMP;
  `;
  for (const p of players) {
    await client.query(sql, [p.player_id, p.name_en, p.team_id]);
  }
}

export async function upsertLinescore(
  client: PoolClient,
  ls: LiveLinescoreRecord
): Promise<void> {
  const sql = `
    INSERT INTO live_linescores (
        game_pk, current_inning, is_top_inning, scheduled_innings,
        balls, strikes, outs, home_score, away_score,
        home_hits, away_hits, home_errors, away_errors,
        innings_json, updated_at
    ) VALUES (
        $1, $2, $3, $4,
        $5, $6, $7, $8, $9,
        $10, $11, $12, $13,
        $14::jsonb, CURRENT_TIMESTAMP
    )
    ON CONFLICT (game_pk) DO UPDATE SET
        current_inning = EXCLUDED.current_inning,
        is_top_inning = EXCLUDED.is_top_inning,
        scheduled_innings = EXCLUDED.scheduled_innings,
        balls = EXCLUDED.balls,
        strikes = EXCLUDED.strikes,
        outs = EXCLUDED.outs,
        home_score = EXCLUDED.home_score,
        away_score = EXCLUDED.away_score,
        home_hits = EXCLUDED.home_hits,
        away_hits = EXCLUDED.away_hits,
        home_errors = EXCLUDED.home_errors,
        away_errors = EXCLUDED.away_errors,
        innings_json = EXCLUDED.innings_json,
        updated_at = CURRENT_TIMESTAMP;
  `;
  await client.query(sql, [
    ls.game_pk,
    ls.current_inning,
    ls.is_top_inning,
    ls.scheduled_innings,
    ls.balls,
    ls.strikes,
    ls.outs,
    ls.home_score,
    ls.away_score,
    ls.home_hits,
    ls.away_hits,
    ls.home_errors,
    ls.away_errors,
    ls.innings_json,
  ]);
}

export async function upsertPlays(client: PoolClient, plays: LivePlayRecord[]): Promise<void> {
  if (!plays.length) return;
  const sql = `
    INSERT INTO live_plays (
        game_pk, at_bat_index, inning, half_inning, is_top_inning,
        batter_id, pitcher_id, first_base_runner_id, second_base_runner_id, third_base_runner_id,
        event, event_type, description, rbi, away_score, home_score,
        is_scoring_play, is_out, is_complete, start_time, end_time, updated_at
    ) VALUES (
        $1, $2, $3, $4, $5,
        $6, $7, $8, $9, $10,
        $11, $12, $13, $14, $15, $16,
        $17, $18, $19, $20, $21, CURRENT_TIMESTAMP
    )
    ON CONFLICT (game_pk, at_bat_index) DO UPDATE SET
        inning = EXCLUDED.inning,
        half_inning = EXCLUDED.half_inning,
        is_top_inning = EXCLUDED.is_top_inning,
        batter_id = EXCLUDED.batter_id,
        pitcher_id = EXCLUDED.pitcher_id,
        first_base_runner_id = EXCLUDED.first_base_runner_id,
        second_base_runner_id = EXCLUDED.second_base_runner_id,
        third_base_runner_id = EXCLUDED.third_base_runner_id,
        event = EXCLUDED.event,
        event_type = EXCLUDED.event_type,
        description = EXCLUDED.description,
        rbi = EXCLUDED.rbi,
        away_score = EXCLUDED.away_score,
        home_score = EXCLUDED.home_score,
        is_scoring_play = EXCLUDED.is_scoring_play,
        is_out = EXCLUDED.is_out,
        is_complete = EXCLUDED.is_complete,
        start_time = EXCLUDED.start_time,
        end_time = EXCLUDED.end_time,
        updated_at = CURRENT_TIMESTAMP;
  `;
  for (const p of plays) {
    await client.query(sql, [
      p.game_pk,
      p.at_bat_index,
      p.inning,
      p.half_inning,
      p.is_top_inning,
      p.batter_id,
      p.pitcher_id,
      p.first_base_runner_id,
      p.second_base_runner_id,
      p.third_base_runner_id,
      p.event,
      p.event_type,
      p.description,
      p.rbi,
      p.away_score,
      p.home_score,
      p.is_scoring_play,
      p.is_out,
      p.is_complete,
      p.start_time,
      p.end_time,
    ]);
  }
}

export async function upsertPitches(
  client: PoolClient,
  pitches: LivePitchRecord[]
): Promise<void> {
  if (!pitches.length) return;
  const sql = `
    INSERT INTO live_pitches (
        game_pk, at_bat_index, pitch_number, play_id, pitch_type, pitch_name,
        start_speed, end_speed, zone, p_x, p_z, spin_rate, spin_direction,
        break_angle, break_vertical, break_vertical_induced, break_horizontal,
        call_code, call_description, description,
        balls, strikes, outs, is_strike, is_ball, is_in_play, is_pitch,
        launch_speed, launch_angle, total_distance, trajectory, hardness, hit_location,
        coord_x, coord_y, start_time, end_time
    ) VALUES (
        $1, $2, $3, $4, $5, $6,
        $7, $8, $9, $10, $11, $12, $13,
        $14, $15, $16, $17,
        $18, $19, $20,
        $21, $22, $23, $24, $25, $26, $27,
        $28, $29, $30, $31, $32, $33,
        $34, $35, $36, $37
    )
    ON CONFLICT (game_pk, at_bat_index, pitch_number) DO UPDATE SET
        play_id = EXCLUDED.play_id,
        pitch_type = EXCLUDED.pitch_type,
        pitch_name = EXCLUDED.pitch_name,
        start_speed = EXCLUDED.start_speed,
        end_speed = EXCLUDED.end_speed,
        zone = EXCLUDED.zone,
        p_x = EXCLUDED.p_x,
        p_z = EXCLUDED.p_z,
        spin_rate = EXCLUDED.spin_rate,
        spin_direction = EXCLUDED.spin_direction,
        break_angle = EXCLUDED.break_angle,
        break_vertical = EXCLUDED.break_vertical,
        break_vertical_induced = EXCLUDED.break_vertical_induced,
        break_horizontal = EXCLUDED.break_horizontal,
        call_code = EXCLUDED.call_code,
        call_description = EXCLUDED.call_description,
        description = EXCLUDED.description,
        balls = EXCLUDED.balls,
        strikes = EXCLUDED.strikes,
        outs = EXCLUDED.outs,
        is_strike = EXCLUDED.is_strike,
        is_ball = EXCLUDED.is_ball,
        is_in_play = EXCLUDED.is_in_play,
        is_pitch = EXCLUDED.is_pitch,
        launch_speed = EXCLUDED.launch_speed,
        launch_angle = EXCLUDED.launch_angle,
        total_distance = EXCLUDED.total_distance,
        trajectory = EXCLUDED.trajectory,
        hardness = EXCLUDED.hardness,
        hit_location = EXCLUDED.hit_location,
        coord_x = EXCLUDED.coord_x,
        coord_y = EXCLUDED.coord_y,
        start_time = EXCLUDED.start_time,
        end_time = EXCLUDED.end_time;
  `;
  for (const p of pitches) {
    await client.query(sql, [
      p.game_pk,
      p.at_bat_index,
      p.pitch_number,
      p.play_id,
      p.pitch_type,
      p.pitch_name,
      p.start_speed,
      p.end_speed,
      p.zone,
      p.p_x,
      p.p_z,
      p.spin_rate,
      p.spin_direction,
      p.break_angle,
      p.break_vertical,
      p.break_vertical_induced,
      p.break_horizontal,
      p.call_code,
      p.call_description,
      p.description,
      p.balls,
      p.strikes,
      p.outs,
      p.is_strike,
      p.is_ball,
      p.is_in_play,
      p.is_pitch,
      p.launch_speed,
      p.launch_angle,
      p.total_distance,
      p.trajectory,
      p.hardness,
      p.hit_location,
      p.coord_x,
      p.coord_y,
      p.start_time,
      p.end_time,
    ]);
  }
}

export async function saveDiffResult(pool: Pool, diff: DiffResult): Promise<void> {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");

    // 1. 外部キー制約のための games / players の事前登録
    await upsertGameRecord(client, diff.game_info);
    await upsertPlayers(client, diff.players);

    // 2. 各テーブルへの UPSERT
    if (diff.linescore) {
      await upsertLinescore(client, diff.linescore);
    }
    if (diff.plays.length) {
      await upsertPlays(client, diff.plays);
    }
    if (diff.pitches.length) {
      await upsertPitches(client, diff.pitches);
    }

    await client.query("COMMIT");
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
}
