import { query } from "@/lib/db";
import { Team, LeagueGroup, DivisionGroup } from "@/types/team";

const LEAGUE_LABELS: Record<string, string> = {
  "American League": "アメリカン・リーグ (AL)",
  "National League": "ナショナル・リーグ (NL)",
};

const DIVISION_LABELS: Record<string, string> = {
  "American League East": "ア・リーグ 東地区 (East)",
  "American League Central": "ア・リーグ 中地区 (Central)",
  "American League West": "ア・リーグ 西地区 (West)",
  "National League East": "ナ・リーグ 東地区 (East)",
  "National League Central": "ナ・リーグ 中地区 (Central)",
  "National League West": "ナ・リーグ 西地区 (West)",
};

/**
 * PostgreSQL の teams テーブルからチーム一覧を取得する
 */
export async function getTeams(): Promise<Team[]> {
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
     ORDER BY league_name ASC, division_name ASC, name ASC`
  );
  return result.rows;
}

/**
 * チーム一覧をリーグおよび地区ごとにグルーピングする
 */
export function groupTeamsByLeagueAndDivision(teams: Team[]): LeagueGroup[] {
  const leaguesOrder = ["American League", "National League"];
  const divisionSuffixes = ["East", "Central", "West"];

  const grouped: Record<string, Record<string, Team[]>> = {
    "American League": {
      "American League East": [],
      "American League Central": [],
      "American League West": [],
    },
    "National League": {
      "National League East": [],
      "National League Central": [],
      "National League West": [],
    },
  };

  for (const team of teams) {
    const league = team.league_name || "Other";
    const division = team.division_name || "Other";

    if (!grouped[league]) {
      grouped[league] = {};
    }
    if (!grouped[league][division]) {
      grouped[league][division] = [];
    }
    grouped[league][division].push(team);
  }

  const result: LeagueGroup[] = [];

  for (const leagueName of leaguesOrder) {
    if (!grouped[leagueName]) continue;
    const divisions: DivisionGroup[] = [];

    for (const suffix of divisionSuffixes) {
      const fullDivisionName = `${leagueName} ${suffix}`;
      const divTeams = grouped[leagueName][fullDivisionName] || [];
      if (divTeams.length > 0) {
        divisions.push({
          division_name: fullDivisionName,
          division_label_ja: DIVISION_LABELS[fullDivisionName] || fullDivisionName,
          teams: divTeams,
        });
      }
    }

    result.push({
      league_name: leagueName,
      league_label_ja: LEAGUE_LABELS[leagueName] || leagueName,
      divisions,
    });
  }

  return result;
}
