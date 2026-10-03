import { query } from "@/lib/db";
import {
  GameHeaderInfo,
  InningDetail,
  LiveLinescore,
  LivePitch,
  LivePlay,
} from "@/types/game";

/**
 * 試合基本情報および対戦チーム情報を取得する
 */
export async function getGameDetail(gamePk: number): Promise<GameHeaderInfo | null> {
  const sql = `
    SELECT
      g.game_pk,
      g.game_date_time,
      g.season,
      g.game_type,
      g.status,
      g.home_team_id,
      g.away_team_id,
      COALESCE(ht.name, 'Home Team') as home_team_name,
      COALESCE(at.name, 'Away Team') as away_team_name,
      COALESCE(ht.abbreviation, 'HOME') as home_team_abbr,
      COALESCE(at.abbreviation, 'AWAY') as away_team_abbr,
      g.home_score,
      g.away_score
    FROM games g
    LEFT JOIN teams ht ON g.home_team_id = ht.team_id
    LEFT JOIN teams at ON g.away_team_id = at.team_id
    WHERE g.game_pk = $1
  `;
  const result = await query(sql, [gamePk]);
  if (result.rows.length === 0) return null;

  const row = result.rows[0];
  return {
    game_pk: Number(row.game_pk),
    game_date_time: row.game_date_time ? new Date(row.game_date_time).toISOString() : "",
    season: Number(row.season),
    game_type: row.game_type || "R",
    status: row.status || "Unknown",
    home_team_id: Number(row.home_team_id),
    away_team_id: Number(row.away_team_id),
    home_team_name: row.home_team_name,
    away_team_name: row.away_team_name,
    home_team_abbr: row.home_team_abbr,
    away_team_abbr: row.away_team_abbr,
    home_score: row.home_score !== null ? Number(row.home_score) : null,
    away_score: row.away_score !== null ? Number(row.away_score) : null,
  };
}

/**
 * 最新のラインスコアおよびイニング別得点を取得する
 */
export async function getLiveLinescore(gamePk: number): Promise<LiveLinescore | null> {
  const sql = `
    SELECT
      game_pk,
      current_inning,
      is_top_inning,
      scheduled_innings,
      balls,
      strikes,
      outs,
      home_score,
      away_score,
      home_hits,
      away_hits,
      home_errors,
      away_errors,
      innings_json
    FROM live_linescores
    WHERE game_pk = $1
  `;
  const result = await query(sql, [gamePk]);
  if (result.rows.length === 0) return null;

  const row = result.rows[0];
  let parsedInnings: InningDetail[] = [];
  try {
    if (typeof row.innings_json === "string") {
      parsedInnings = JSON.parse(row.innings_json);
    } else if (Array.isArray(row.innings_json)) {
      parsedInnings = row.innings_json;
    }
  } catch {
    parsedInnings = [];
  }

  return {
    game_pk: Number(row.game_pk),
    current_inning: Number(row.current_inning),
    is_top_inning: Boolean(row.is_top_inning),
    scheduled_innings: Number(row.scheduled_innings || 9),
    balls: Number(row.balls || 0),
    strikes: Number(row.strikes || 0),
    outs: Number(row.outs || 0),
    home_score: Number(row.home_score || 0),
    away_score: Number(row.away_score || 0),
    home_hits: Number(row.home_hits || 0),
    away_hits: Number(row.away_hits || 0),
    home_errors: Number(row.home_errors || 0),
    away_errors: Number(row.away_errors || 0),
    innings: parsedInnings,
  };
}

/**
 * 打席履歴および配球・Statcast投球指標を取得する
 */
export async function getLivePlaysWithPitches(gamePk: number): Promise<LivePlay[]> {
  const playsSql = `
    SELECT
      p.game_pk,
      p.at_bat_index,
      p.inning,
      p.half_inning,
      p.is_top_inning,
      p.batter_id,
      COALESCE(b.name_ja, b.name_en, '打者 ' || p.batter_id) as batter_name,
      p.pitcher_id,
      COALESCE(pi.name_ja, pi.name_en, '投手 ' || p.pitcher_id) as pitcher_name,
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
      p.end_time
    FROM live_plays p
    LEFT JOIN players b ON p.batter_id = b.player_id
    LEFT JOIN players pi ON p.pitcher_id = pi.player_id
    WHERE p.game_pk = $1
    ORDER BY p.at_bat_index ASC
  `;

  const pitchesSql = `
    SELECT
      game_pk,
      at_bat_index,
      pitch_number,
      play_id,
      pitch_type,
      pitch_name,
      start_speed,
      end_speed,
      zone,
      p_x,
      p_z,
      spin_rate,
      spin_direction,
      break_angle,
      break_vertical,
      break_vertical_induced,
      break_horizontal,
      call_code,
      call_description,
      description,
      balls,
      strikes,
      outs,
      is_strike,
      is_ball,
      is_in_play,
      is_pitch,
      launch_speed,
      launch_angle,
      total_distance,
      trajectory,
      hardness,
      hit_location,
      coord_x,
      coord_y,
      start_time,
      end_time
    FROM live_pitches
    WHERE game_pk = $1
    ORDER BY at_bat_index ASC, pitch_number ASC
  `;

  const [playsResult, pitchesResult] = await Promise.all([
    query(playsSql, [gamePk]),
    query(pitchesSql, [gamePk]),
  ]);

  const pitchesByAtBat = new Map<number, LivePitch[]>();
  for (const row of pitchesResult.rows) {
    const atBatIndex = Number(row.at_bat_index);
    if (!pitchesByAtBat.has(atBatIndex)) {
      pitchesByAtBat.set(atBatIndex, []);
    }
    pitchesByAtBat.get(atBatIndex)!.push({
      game_pk: Number(row.game_pk),
      at_bat_index: atBatIndex,
      pitch_number: Number(row.pitch_number),
      play_id: row.play_id,
      pitch_type: row.pitch_type,
      pitch_name: row.pitch_name,
      start_speed: row.start_speed !== null ? Number(row.start_speed) : null,
      end_speed: row.end_speed !== null ? Number(row.end_speed) : null,
      zone: row.zone !== null ? Number(row.zone) : null,
      p_x: row.p_x !== null ? Number(row.p_x) : null,
      p_z: row.p_z !== null ? Number(row.p_z) : null,
      spin_rate: row.spin_rate !== null ? Number(row.spin_rate) : null,
      spin_direction: row.spin_direction !== null ? Number(row.spin_direction) : null,
      break_angle: row.break_angle !== null ? Number(row.break_angle) : null,
      break_vertical: row.break_vertical !== null ? Number(row.break_vertical) : null,
      break_vertical_induced: row.break_vertical_induced !== null ? Number(row.break_vertical_induced) : null,
      break_horizontal: row.break_horizontal !== null ? Number(row.break_horizontal) : null,
      call_code: row.call_code,
      call_description: row.call_description,
      description: row.description,
      balls: Number(row.balls || 0),
      strikes: Number(row.strikes || 0),
      outs: Number(row.outs || 0),
      is_strike: Boolean(row.is_strike),
      is_ball: Boolean(row.is_ball),
      is_in_play: Boolean(row.is_in_play),
      is_pitch: Boolean(row.is_pitch),
      launch_speed: row.launch_speed !== null ? Number(row.launch_speed) : null,
      launch_angle: row.launch_angle !== null ? Number(row.launch_angle) : null,
      total_distance: row.total_distance !== null ? Number(row.total_distance) : null,
      trajectory: row.trajectory,
      hardness: row.hardness,
      hit_location: row.hit_location,
      coord_x: row.coord_x !== null ? Number(row.coord_x) : null,
      coord_y: row.coord_y !== null ? Number(row.coord_y) : null,
      start_time: row.start_time ? new Date(row.start_time).toISOString() : null,
      end_time: row.end_time ? new Date(row.end_time).toISOString() : null,
    });
  }

  return playsResult.rows.map((row) => {
    const atBatIndex = Number(row.at_bat_index);
    return {
      game_pk: Number(row.game_pk),
      at_bat_index: atBatIndex,
      inning: Number(row.inning),
      half_inning: row.half_inning,
      is_top_inning: Boolean(row.is_top_inning),
      batter_id: Number(row.batter_id),
      batter_name: row.batter_name,
      pitcher_id: Number(row.pitcher_id),
      pitcher_name: row.pitcher_name,
      first_base_runner_id: row.first_base_runner_id ? Number(row.first_base_runner_id) : null,
      second_base_runner_id: row.second_base_runner_id ? Number(row.second_base_runner_id) : null,
      third_base_runner_id: row.third_base_runner_id ? Number(row.third_base_runner_id) : null,
      event: row.event,
      event_type: row.event_type,
      description: row.description,
      rbi: Number(row.rbi || 0),
      away_score: Number(row.away_score || 0),
      home_score: Number(row.home_score || 0),
      is_scoring_play: Boolean(row.is_scoring_play),
      is_out: Boolean(row.is_out),
      is_complete: Boolean(row.is_complete),
      start_time: row.start_time ? new Date(row.start_time).toISOString() : null,
      end_time: row.end_time ? new Date(row.end_time).toISOString() : null,
      pitches: pitchesByAtBat.get(atBatIndex) || [],
    };
  });
}

/**
 * 直近および進行中の試合一覧を取得する
 */
export async function getRecentGames(): Promise<GameHeaderInfo[]> {
  const sql = `
    SELECT
      g.game_pk,
      g.game_date_time,
      g.season,
      g.game_type,
      g.status,
      g.home_team_id,
      g.away_team_id,
      COALESCE(ht.name, 'Home Team') as home_team_name,
      COALESCE(at.name, 'Away Team') as away_team_name,
      COALESCE(ht.abbreviation, 'HOME') as home_team_abbr,
      COALESCE(at.abbreviation, 'AWAY') as away_team_abbr,
      g.home_score,
      g.away_score
    FROM games g
    LEFT JOIN teams ht ON g.home_team_id = ht.team_id
    LEFT JOIN teams at ON g.away_team_id = at.team_id
    ORDER BY
      CASE
        WHEN g.status ILIKE '%Progress%' OR g.status = 'Live' THEN 1
        WHEN g.status ILIKE '%Final%' THEN 2
        ELSE 3
      END ASC,
      g.game_date_time DESC
    LIMIT 30
  `;
  const result = await query(sql);

  return result.rows.map((row) => ({
    game_pk: Number(row.game_pk),
    game_date_time: row.game_date_time ? new Date(row.game_date_time).toISOString() : "",
    season: Number(row.season),
    game_type: row.game_type || "R",
    status: row.status || "Unknown",
    home_team_id: Number(row.home_team_id),
    away_team_id: Number(row.away_team_id),
    home_team_name: row.home_team_name,
    away_team_name: row.away_team_name,
    home_team_abbr: row.home_team_abbr,
    away_team_abbr: row.away_team_abbr,
    home_score: row.home_score !== null ? Number(row.home_score) : null,
    away_score: row.away_score !== null ? Number(row.away_score) : null,
  }));
}
