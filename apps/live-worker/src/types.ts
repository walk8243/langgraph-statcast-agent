/**
 * 型定義モジュール
 */

export interface GameInfo {
  game_pk: number;
  game_date_time: Date;
  season: number;
  game_type: string;
  status: string;
  status_code: string | null;
  abstract_state: string;
  home_team_id: number | null;
  away_team_id: number | null;
  home_score: number | null;
  away_score: number | null;
}

export interface PlayerRecord {
  player_id: number;
  name_en: string;
  team_id: number | null;
}

export interface LiveLinescoreRecord {
  game_pk: number;
  current_inning: number;
  is_top_inning: boolean;
  scheduled_innings: number;
  balls: number;
  strikes: number;
  outs: number;
  home_score: number;
  away_score: number;
  home_hits: number;
  away_hits: number;
  home_errors: number;
  away_errors: number;
  innings_json: string;
}

export interface LivePlayRecord {
  game_pk: number;
  at_bat_index: number;
  inning: number;
  half_inning: string;
  is_top_inning: boolean;
  batter_id: number;
  pitcher_id: number;
  first_base_runner_id: number | null;
  second_base_runner_id: number | null;
  third_base_runner_id: number | null;
  event: string | null;
  event_type: string | null;
  description: string | null;
  rbi: number;
  away_score: number;
  home_score: number;
  is_scoring_play: boolean;
  is_out: boolean;
  is_complete: boolean;
  start_time: Date | null;
  end_time: Date | null;
}

export interface LivePitchRecord {
  game_pk: number;
  at_bat_index: number;
  pitch_number: number;
  play_id: string | null;
  pitch_type: string | null;
  pitch_name: string | null;
  start_speed: number | null;
  end_speed: number | null;
  zone: number | null;
  p_x: number | null;
  p_z: number | null;
  spin_rate: number | null;
  spin_direction: number | null;
  break_angle: number | null;
  break_vertical: number | null;
  break_vertical_induced: number | null;
  break_horizontal: number | null;
  call_code: string | null;
  call_description: string | null;
  description: string | null;
  balls: number;
  strikes: number;
  outs: number;
  is_strike: boolean;
  is_ball: boolean;
  is_in_play: boolean;
  is_pitch: boolean;
  launch_speed: number | null;
  launch_angle: number | null;
  total_distance: number | null;
  trajectory: string | null;
  hardness: string | null;
  hit_location: string | null;
  coord_x: number | null;
  coord_y: number | null;
  start_time: Date | null;
  end_time: Date | null;
}

export type LiveEventType = "linescore" | "play" | "pitch" | "game_status";

export interface LiveEvent {
  game_pk: number;
  event_type: LiveEventType;
  timestamp: string;
  data: Record<string, any>;
}

export interface DiffResult {
  game_pk: number;
  game_info: GameInfo;
  players: PlayerRecord[];
  linescore: LiveLinescoreRecord | null;
  plays: LivePlayRecord[];
  pitches: LivePitchRecord[];
  events: LiveEvent[];
}
