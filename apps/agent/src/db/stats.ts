import { pool } from "./client.js";

export interface PlayerInfo {
  playerId: number;
  nameEn: string;
  nameJa: string | null;
  teamId: number | null;
  teamName: string | null;
}

export interface BatterSeasonStats {
  year: number;
  games: number;
  plateAppearances: number;
  atBats: number;
  runs: number;
  hits: number;
  doubles: number;
  triples: number;
  homeRuns: number;
  rbi: number;
  totalBases: number;
  strikeouts: number;
  walks: number;
  intentionalWalks: number;
  hitByPitch: number;
  stolenBases: number;
  caughtStealing: number;
  battingAverage: number;
  onBasePercentage: number;
  sluggingPercentage: number;
  ops: number;
}

export interface PitcherSeasonStats {
  year: number;
  wins: number;
  losses: number;
  era: number;
  gamesPitched: number;
  gamesStarted: number;
  completeGames: number;
  shutouts: number;
  saves: number;
  saveOpportunities: number;
  holds: number;
  blownSaves: number;
  inningsPitched: string;
  outs: number;
  hits: number;
  runs: number;
  earnedRuns: number;
  homeRuns: number;
  walks: number;
  strikeouts: number;
  whip: number;
  battingAverageAgainst: number;
  battersFaced: number;
  numberOfPitches: number;
}

export interface PlayerFullStats {
  player: PlayerInfo;
  year: number;
  batterStats: BatterSeasonStats | null;
  pitcherStats: PitcherSeasonStats | null;
}

export async function fetchPlayerFullStats(
  playerId: number,
  year: number
): Promise<PlayerFullStats | null> {
  // 1. 選手マスタ情報取得
  const playerRes = await pool.query(
    `
    SELECT 
      p.player_id, 
      p.name_en, 
      p.name_ja, 
      p.team_id,
      t.name AS team_name
    FROM players p
    LEFT JOIN teams t ON p.team_id = t.team_id
    WHERE p.player_id = $1
    `,
    [playerId]
  );

  if (playerRes.rows.length === 0) {
    return null;
  }

  const pRow = playerRes.rows[0];
  const player: PlayerInfo = {
    playerId: Number(pRow.player_id),
    nameEn: pRow.name_en,
    nameJa: pRow.name_ja,
    teamId: pRow.team_id ? Number(pRow.team_id) : null,
    teamName: pRow.team_name,
  };

  // 2. 打者成績取得
  const batterRes = await pool.query(
    `
    SELECT *
    FROM batter_season_stats
    WHERE player_id = $1 AND year = $2
    `,
    [playerId, year]
  );

  let batterStats: BatterSeasonStats | null = null;
  if (batterRes.rows.length > 0) {
    const b = batterRes.rows[0];
    batterStats = {
      year: b.year,
      games: b.games,
      plateAppearances: b.plate_appearances,
      atBats: b.at_bats,
      runs: b.runs,
      hits: b.hits,
      doubles: b.doubles,
      triples: b.triples,
      homeRuns: b.home_runs,
      rbi: b.rbi,
      totalBases: b.total_bases,
      strikeouts: b.strikeouts,
      walks: b.walks,
      intentionalWalks: b.intentional_walks,
      hitByPitch: b.hit_by_pitch,
      stolenBases: b.stolen_bases,
      caughtStealing: b.caught_stealing,
      battingAverage: Number(b.batting_average),
      onBasePercentage: Number(b.on_base_percentage),
      sluggingPercentage: Number(b.slugging_percentage),
      ops: Number(b.ops),
    };
  }

  // 3. 投手成績取得
  const pitcherRes = await pool.query(
    `
    SELECT *
    FROM pitcher_season_stats
    WHERE player_id = $1 AND year = $2
    `,
    [playerId, year]
  );

  let pitcherStats: PitcherSeasonStats | null = null;
  if (pitcherRes.rows.length > 0) {
    const pt = pitcherRes.rows[0];
    pitcherStats = {
      year: pt.year,
      wins: pt.wins,
      losses: pt.losses,
      era: Number(pt.era),
      gamesPitched: pt.games_pitched,
      gamesStarted: pt.games_started,
      completeGames: pt.complete_games,
      shutouts: pt.shutouts,
      saves: pt.saves,
      saveOpportunities: pt.save_opportunities,
      holds: pt.holds,
      blownSaves: pt.blown_saves,
      inningsPitched: pt.innings_pitched,
      outs: pt.outs,
      hits: pt.hits,
      runs: pt.runs,
      earnedRuns: pt.earned_runs,
      homeRuns: pt.home_runs,
      walks: pt.walks,
      strikeouts: pt.strikeouts,
      whip: Number(pt.whip),
      battingAverageAgainst: Number(pt.batting_average_against),
      battersFaced: pt.batters_faced,
      numberOfPitches: pt.number_of_pitches,
    };
  }

  return {
    player,
    year,
    batterStats,
    pitcherStats,
  };
}

export async function savePlayerReport(
  playerId: number,
  year: number,
  reportText: string,
  modelName: string
): Promise<void> {
  await pool.query(
    `
    INSERT INTO player_reports (player_id, year, report_text, model_name, updated_at)
    VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
    ON CONFLICT (player_id, year)
    DO UPDATE SET
      report_text = EXCLUDED.report_text,
      model_name = EXCLUDED.model_name,
      updated_at = CURRENT_TIMESTAMP
    `,
    [playerId, year, reportText, modelName]
  );
}

export async function fetchPlayerReport(
  playerId: number,
  year: number
): Promise<string | null> {
  const res = await pool.query(
    `
    SELECT report_text
    FROM player_reports
    WHERE player_id = $1 AND year = $2
    `,
    [playerId, year]
  );

  if (res.rows.length === 0) {
    return null;
  }
  return res.rows[0].report_text;
}
