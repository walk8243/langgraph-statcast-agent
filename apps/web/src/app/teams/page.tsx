import { Metadata } from "next";
import { getTeams, groupTeamsByLeagueAndDivision } from "@/lib/teams";
import { TeamsClient } from "./teams-client";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "MLB チーム一覧 | Statcast Agent Web",
  description:
    "MLB 全30球団のチーム一覧。アメリカン・リーグおよびナショナル・リーグの東・中・西地区ごとに整理され、選手一覧（ロスター）へアクセスできます。",
};

export default async function TeamsPage() {
  const teams = await getTeams();
  const leagueGroups = groupTeamsByLeagueAndDivision(teams);

  return <TeamsClient initialLeagueGroups={leagueGroups} allTeams={teams} />;
}
