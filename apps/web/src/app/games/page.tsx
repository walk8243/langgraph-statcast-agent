import { Metadata } from "next";
import { getGamesByDate, getLatestGameDate } from "@/lib/games";
import GamesClient from "./games-client";

export const dynamic = "force-dynamic";

interface GamesPageProps {
  searchParams: Promise<{
    date?: string;
  }>;
}

export async function generateMetadata({ searchParams }: GamesPageProps): Promise<Metadata> {
  const resolvedParams = await searchParams;
  const targetDate = resolvedParams?.date;
  const dateLabel = targetDate ? ` (${targetDate})` : "";
  return {
    title: `MLB 試合一覧・速報${dateLabel} | Statcast Agent Web`,
    description: "進行中および特定日の MLB 試合一覧とリアルタイム一球速報画面へのアクセスを提供します。",
  };
}

function getTodayJst(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tokyo" }).format(new Date());
}

export default async function GamesPage({ searchParams }: GamesPageProps) {
  const resolvedParams = await searchParams;
  const requestedDate = resolvedParams?.date;

  const today = getTodayJst();
  const latestDate = await getLatestGameDate();

  let targetDate = requestedDate;
  if (!targetDate || !/^\d{4}-\d{2}-\d{2}$/.test(targetDate) || isNaN(Date.parse(targetDate))) {
    targetDate = today;
  }

  const games = await getGamesByDate(targetDate);

  return (
    <GamesClient
      games={games}
      currentDate={targetDate}
      latestDate={latestDate || today}
      today={today}
    />
  );
}

