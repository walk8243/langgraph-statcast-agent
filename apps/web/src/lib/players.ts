import { query } from "@/lib/db";
import { Team } from "@/types/team";
import {
  Player,
  PlayerDetail,
  BatterSeasonStat,
  PitcherSeasonStat,
  PlayerReport,
  BatterStatcastStat,
  PitcherStatcastStat,
  PitcherPitchTypeStat,
} from "@/types/player";

export { groupPlayersByPosition, formatBatsThrows } from "./player-utils";

/**
 * チームIDからチーム基本情報を取得する
 */
export async function getTeamById(teamId: number): Promise<Team | null> {
  const result = await query<Team>(
    `SELECT
       team_id,
       name,
       abbreviation,
       league_id,
       league_name,
       division_id,
       division_name
     FROM teams
     WHERE team_id = $1`,
    [teamId]
  );

  return result.rows[0] ?? null;
}

/**
 * 指定したチームIDに所属する選手一覧を取得する
 */
export async function getPlayersByTeamId(teamId: number): Promise<Player[]> {
  const result = await query<Player>(
    `SELECT
       player_id,
       name_en,
       name_ja,
       team_id,
       primary_number,
       primary_position_code,
       primary_position_name,
       primary_position_type,
       primary_position_abbreviation,
       bat_side,
       pitch_hand
     FROM players
     WHERE team_id = $1
     ORDER BY
       CASE
         WHEN primary_number IS NULL OR primary_number = '' THEN 9999
         ELSE CAST(primary_number AS INTEGER)
       END ASC,
       name_en ASC`,
    [teamId]
  );

  return result.rows;
}

/**
 * 選手IDから選手詳細情報（所属チーム情報含む）を取得する
 */
export async function getPlayerDetailById(playerId: number): Promise<PlayerDetail | null> {
  const result = await query<PlayerDetail>(
    `SELECT
       p.player_id,
       p.name_en,
       p.name_ja,
       p.team_id,
       p.primary_number,
       p.primary_position_code,
       p.primary_position_name,
       p.primary_position_type,
       p.primary_position_abbreviation,
       p.bat_side,
       p.pitch_hand,
       t.name AS team_name,
       t.abbreviation AS team_abbreviation,
       t.league_name,
       t.division_name
     FROM players p
     LEFT JOIN teams t ON p.team_id = t.team_id
     WHERE p.player_id = $1`,
    [playerId]
  );

  return result.rows[0] ?? null;
}

/**
 * 選手IDから打者シーズン成績一覧（年度降順）を取得する
 */
export async function getBatterSeasonStatsByPlayerId(
  playerId: number
): Promise<BatterSeasonStat[]> {
  const result = await query<BatterSeasonStat>(
    `SELECT
       player_id,
       year,
       games,
       plate_appearances,
       at_bats,
       runs,
       hits,
       doubles,
       triples,
       home_runs,
       rbi,
       total_bases,
       strikeouts,
       walks,
       intentional_walks,
       hit_by_pitch,
       sac_bunts,
       sac_flies,
       grounded_into_double_play,
       stolen_bases,
       caught_stealing,
       batting_average,
       on_base_percentage,
       slugging_percentage,
       ops
     FROM batter_season_stats
     WHERE player_id = $1
     ORDER BY year DESC`,
    [playerId]
  );

  return result.rows;
}

/**
 * 選手IDから投手シーズン成績一覧（年度降順）を取得する
 */
export async function getPitcherSeasonStatsByPlayerId(
  playerId: number
): Promise<PitcherSeasonStat[]> {
  const result = await query<PitcherSeasonStat>(
    `SELECT
       player_id,
       year,
       wins,
       losses,
       era,
       games_pitched,
       games_started,
       complete_games,
       shutouts,
       saves,
       save_opportunities,
       holds,
       blown_saves,
       innings_pitched,
       outs,
       hits,
       runs,
       earned_runs,
       home_runs,
       walks,
       intentional_walks,
       strikeouts,
       hit_by_pitch,
       whip,
       batting_average_against,
       batters_faced,
       number_of_pitches
     FROM pitcher_season_stats
     WHERE player_id = $1
     ORDER BY year DESC`,
    [playerId]
  );

  return result.rows;
}

/**
 * 選手IDから選手解説レポート一覧（年度降順）を取得する
 */
export async function getPlayerReportsByPlayerId(
  playerId: number
): Promise<PlayerReport[]> {
  const result = await query<PlayerReport>(
    `SELECT
       id,
       player_id,
       year,
       report_text,
       model_name,
       created_at,
       updated_at
     FROM player_reports
     WHERE player_id = $1
     ORDER BY year DESC`,
    [playerId]
  );

  return result.rows;
}

/**
 * 選手IDから最新年度の打者 Statcast 指標を取得する
 */
export async function getLatestBatterStatcastStatsByPlayerId(
  playerId: number
): Promise<BatterStatcastStat | null> {
  const result = await query<BatterStatcastStat>(
    `SELECT
       player_id,
       year,
       pitches_seen,
       batted_balls,
       barrels,
       barrel_pct,
       hard_hit_count,
       hard_hit_pct,
       avg_exit_velocity,
       max_exit_velocity,
       avg_launch_angle,
       sweet_spot_pct
     FROM batter_statcast_stats
     WHERE player_id = $1
     ORDER BY year DESC
     LIMIT 1`,
    [playerId]
  );

  return result.rows[0] ?? null;
}

/**
 * 選手IDから最新年度の投手 Statcast 総合指標を取得する
 */
export async function getLatestPitcherStatcastStatsByPlayerId(
  playerId: number
): Promise<PitcherStatcastStat | null> {
  const result = await query<PitcherStatcastStat>(
    `SELECT
       player_id,
       year,
       total_pitches,
       batted_balls,
       barrels_allowed,
       barrel_pct,
       hard_hit_count,
       hard_hit_pct,
       avg_exit_velocity,
       swings,
       whiffs,
       whiff_pct,
       called_strikes,
       csw_pct
     FROM pitcher_statcast_stats
     WHERE player_id = $1
     ORDER BY year DESC
     LIMIT 1`,
    [playerId]
  );

  return result.rows[0] ?? null;
}

/**
 * 選手IDから最新年度の投手球種別 Statcast 指標一覧（投球数降順）を取得する
 */
export async function getLatestPitcherPitchTypeStatsByPlayerId(
  playerId: number
): Promise<PitcherPitchTypeStat[]> {
  const result = await query<PitcherPitchTypeStat>(
    `SELECT
       player_id,
       year,
       pitch_type,
       pitch_name,
       pitches,
       usage_pct,
       avg_speed,
       avg_spin_rate,
       avg_pfx_x,
       avg_pfx_z,
       swings,
       whiffs,
       whiff_pct
     FROM pitcher_pitch_type_stats
     WHERE player_id = $1
       AND year = (
         SELECT year
         FROM pitcher_pitch_type_stats
         WHERE player_id = $1
         ORDER BY year DESC
         LIMIT 1
       )
     ORDER BY pitches DESC`,
    [playerId]
  );

  return result.rows;
}

