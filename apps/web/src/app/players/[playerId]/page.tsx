import { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  getPlayerDetailById,
  getBatterSeasonStatsByPlayerId,
  getPitcherSeasonStatsByPlayerId,
  getPlayerReportsByPlayerId,
} from "@/lib/players";
import PlayerDetailClient from "./player-detail-client";

export const dynamic = "force-dynamic";

interface PlayerDetailPageProps {
  params: Promise<{
    playerId: string;
  }>;
}

export async function generateMetadata({
  params,
}: PlayerDetailPageProps): Promise<Metadata> {
  const { playerId } = await params;
  const playerIdNum = Number.parseInt(playerId, 10);

  if (Number.isNaN(playerIdNum)) {
    return {
      title: "選手が見つかりません | Statcast Agent Web",
    };
  }

  const player = await getPlayerDetailById(playerIdNum);
  if (!player) {
    return {
      title: "選手が見つかりません | Statcast Agent Web",
    };
  }

  const mainName = player.name_ja || player.name_en;
  return {
    title: `${mainName} 選手詳細・AI解説レポート | Statcast Agent Web`,
    description: `${mainName}（${player.name_en}）の選手プロフィール、年度別打撃・投球成績、LangGraph AI Agent による解説分析レポートを掲載しています。`,
  };
}

export default async function PlayerDetailPage({
  params,
}: PlayerDetailPageProps) {
  const { playerId } = await params;
  const playerIdNum = Number.parseInt(playerId, 10);

  if (Number.isNaN(playerIdNum)) {
    notFound();
  }

  const player = await getPlayerDetailById(playerIdNum);
  if (!player) {
    notFound();
  }

  const [batterStats, pitcherStats, reports] = await Promise.all([
    getBatterSeasonStatsByPlayerId(playerIdNum),
    getPitcherSeasonStatsByPlayerId(playerIdNum),
    getPlayerReportsByPlayerId(playerIdNum),
  ]);

  return (
    <PlayerDetailClient
      player={player}
      batterStats={batterStats}
      pitcherStats={pitcherStats}
      reports={reports}
    />
  );
}
