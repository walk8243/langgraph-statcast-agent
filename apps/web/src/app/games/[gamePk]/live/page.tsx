import { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  getGameDetail,
  getLiveLinescore,
  getLivePlaysWithPitches,
} from "@/lib/games";
import LiveGameClient from "./live-game-client";

export const dynamic = "force-dynamic";

interface LiveGamePageProps {
  params: Promise<{
    gamePk: string;
  }>;
}

export async function generateMetadata({
  params,
}: LiveGamePageProps): Promise<Metadata> {
  const { gamePk } = await params;
  const gamePkNum = Number.parseInt(gamePk, 10);

  if (Number.isNaN(gamePkNum)) {
    return {
      title: "試合が見つかりません | Statcast Agent Web",
    };
  }

  const game = await getGameDetail(gamePkNum);
  if (!game) {
    return {
      title: "試合が見つかりません | Statcast Agent Web",
    };
  }

  const title = `【試合速報】${game.away_team_abbr} vs ${game.home_team_abbr} (${game.status}) | Statcast Agent Web`;
  const description = `${game.away_team_name} vs ${game.home_team_name} のリアルタイム試合速報・スコアボード・一球速報・Statcast指標を配信しています。`;

  return {
    title,
    description,
  };
}

export default async function LiveGamePage({ params }: LiveGamePageProps) {
  const { gamePk } = await params;
  const gamePkNum = Number.parseInt(gamePk, 10);

  if (Number.isNaN(gamePkNum)) {
    notFound();
  }

  const [game, linescore, plays] = await Promise.all([
    getGameDetail(gamePkNum),
    getLiveLinescore(gamePkNum),
    getLivePlaysWithPitches(gamePkNum),
  ]);

  if (!game) {
    notFound();
  }

  return (
    <LiveGameClient
      initialData={{
        game,
        linescore,
        plays,
      }}
    />
  );
}
