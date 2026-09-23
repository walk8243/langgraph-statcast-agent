import { query } from "@/lib/db";
import { Team } from "@/types/team";
import { Player } from "@/types/player";

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
