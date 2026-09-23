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

export interface PositionGroup {
  group_key: string;
  group_name_ja: string;
  group_name_en: string;
  order: number;
  players: Player[];
}
