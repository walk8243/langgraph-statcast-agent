import { Metadata } from "next";
import { getRecentGames } from "@/lib/games";
import GamesClient from "./games-client";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "MLB 試合一覧・速報 | Statcast Agent Web",
  description: "進行中および直近の MLB 試合一覧とリアルタイム一球速報画面へのアクセスを提供します。",
};

export default async function GamesPage() {
  const games = await getRecentGames();

  return <GamesClient games={games} />;
}
