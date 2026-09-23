export interface Player {
  player_id: number;
  name_en: string;
  name_ja: string | null;
  team_id: number | null;
  primary_number: string | null;
  primary_position_code: string | null;
  primary_position_name: string | null;
  primary_position_type: string | null;
  primary_position_abbreviation: string | null;
  bat_side: string | null;
  pitch_hand: string | null;
}

export interface PlayerDetail extends Player {
  team_name: string | null;
  team_abbreviation: string | null;
  league_name: string | null;
  division_name: string | null;
}

export interface PositionGroup {
  group_key: string;
  group_name_ja: string;
  group_name_en: string;
  order: number;
  players: Player[];
}

export interface BatterSeasonStat {
  player_id: number;
  year: number;
  games: number;
  plate_appearances: number;
  at_bats: number;
  runs: number;
  hits: number;
  doubles: number;
  triples: number;
  home_runs: number;
  rbi: number;
  total_bases: number;
  strikeouts: number;
  walks: number;
  intentional_walks: number;
  hit_by_pitch: number;
  sac_bunts: number;
  sac_flies: number;
  grounded_into_double_play: number;
  stolen_bases: number;
  caught_stealing: number;
  batting_average: string | number;
  on_base_percentage: string | number;
  slugging_percentage: string | number;
  ops: string | number;
}

export interface PitcherSeasonStat {
  player_id: number;
  year: number;
  wins: number;
  losses: number;
  era: string | number;
  games_pitched: number;
  games_started: number;
  complete_games: number;
  shutouts: number;
  saves: number;
  save_opportunities: number;
  holds: number;
  blown_saves: number;
  innings_pitched: string;
  outs: number;
  hits: number;
  runs: number;
  earned_runs: number;
  home_runs: number;
  walks: number;
  intentional_walks: number;
  strikeouts: number;
  hit_by_pitch: number;
  whip: string | number;
  batting_average_against: string | number;
  batters_faced: number;
  number_of_pitches: number;
}

export interface PlayerReport {
  id: number;
  player_id: number;
  year: number;
  report_text: string;
  model_name: string;
  created_at: string;
  updated_at: string;
}

