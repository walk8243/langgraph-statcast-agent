export interface Team {
  team_id: number;
  name: string;
  abbreviation: string;
  league_id: number | null;
  league_name: string | null;
  division_id: number | null;
  division_name: string | null;
}

export interface DivisionGroup {
  division_name: string;
  division_label_ja: string;
  teams: Team[];
}

export interface LeagueGroup {
  league_name: string;
  league_label_ja: string;
  divisions: DivisionGroup[];
}
