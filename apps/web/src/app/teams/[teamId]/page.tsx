import { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  getTeamById,
  getPlayersByTeamId,
  groupPlayersByPosition,
} from "@/lib/players";
import { TeamRosterClient } from "./team-roster-client";

export const dynamic = "force-dynamic";

interface TeamDetailPageProps {
  params: Promise<{
    teamId: string;
  }>;
}

export async function generateMetadata({
  params,
}: TeamDetailPageProps): Promise<Metadata> {
  const { teamId } = await params;
  const teamIdNum = Number.parseInt(teamId, 10);

  if (Number.isNaN(teamIdNum)) {
    return {
      title: "チームが見つかりません | Statcast Agent Web",
    };
  }

  const team = await getTeamById(teamIdNum);
  if (!team) {
    return {
      title: "チームが見つかりません | Statcast Agent Web",
    };
  }

  return {
    title: `${team.name} 選手一覧（ロスター） | Statcast Agent Web`,
    description: `${team.name}（${team.abbreviation}）の所属選手一覧。ポジション別のロスター情報、背番号、投打、選手詳細・AI解説レポートを閲覧できます。`,
  };
}

export default async function TeamDetailPage({ params }: TeamDetailPageProps) {
  const { teamId } = await params;
  const teamIdNum = Number.parseInt(teamId, 10);

  if (Number.isNaN(teamIdNum)) {
    notFound();
  }

  const team = await getTeamById(teamIdNum);
  if (!team) {
    notFound();
  }

  const players = await getPlayersByTeamId(teamIdNum);
  const positionGroups = groupPlayersByPosition(players);

  return (
    <TeamRosterClient
      team={team}
      players={players}
      positionGroups={positionGroups}
    />
  );
}
