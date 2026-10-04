"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Title1,
  Subtitle1,
  Body1,
  Caption1,
  Button,
  Card,
  CardHeader,
  CardFooter,
  Badge,
  Text,
  Input,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import {
  Sport24Regular,
  ArrowRight16Regular,
  ArrowLeft16Regular,
  CheckmarkCircle20Filled,
} from "@fluentui/react-icons";
import { GameHeaderInfo } from "@/types/game";

const useStyles = makeStyles({
  container: {
    maxWidth: "1200px",
    marginLeft: "auto",
    marginRight: "auto",
    ...shorthands.padding("32px", "24px"),
    display: "flex",
    flexDirection: "column",
    rowGap: "28px",
  },
  topNav: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  header: {
    display: "flex",
    flexDirection: "column",
    rowGap: "8px",
  },
  dateNavCard: {
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "16px",
    ...shorthands.padding("14px", "20px"),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    boxShadow: tokens.shadow2,
  },
  dateNavCenter: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    flexWrap: "wrap",
  },
  dateInput: {
    minWidth: "150px",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
    gap: "20px",
  },
  card: {
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    ...shorthands.padding("16px"),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    backgroundColor: tokens.colorNeutralBackground1,
    boxShadow: tokens.shadow2,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
  },
  liveCard: {
    ...shorthands.border("2px", "solid", tokens.colorBrandStroke1),
  },
  scoreOverview: {
    display: "flex",
    justifyContent: "space-around",
    alignItems: "center",
    ...shorthands.padding("16px", "8px"),
    ...shorthands.margin("12px", "0"),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusSmall),
  },
  statusBadge: {
    whiteSpace: "nowrap",
    flexShrink: 0,
  },
});

function getAdjacentDate(dateStr: string, offsetDays: number): string {
  const [year, month, day] = dateStr.split("-").map(Number);
  const d = new Date(Date.UTC(year, month - 1, day + offsetDays));
  return d.toISOString().slice(0, 10);
}

function formatDateJa(dateStr: string): string {
  const [year, month, day] = dateStr.split("-").map(Number);
  const d = new Date(Date.UTC(year, month - 1, day));
  const weekdays = ["日", "月", "火", "水", "木", "金", "土"];
  const weekday = weekdays[d.getUTCDay()];
  return `${year}年${month}月${day}日 (${weekday})`;
}

interface GamesClientProps {
  games: GameHeaderInfo[];
  currentDate: string;
  latestDate: string;
}

export default function GamesClient({ games, currentDate, latestDate }: GamesClientProps) {
  const styles = useStyles();
  const router = useRouter();

  const prevDate = getAdjacentDate(currentDate, -1);
  const nextDate = getAdjacentDate(currentDate, 1);

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    if (val && /^\d{4}-\d{2}-\d{2}$/.test(val)) {
      router.push(`/games?date=${val}`);
    }
  };

  return (
    <main className={styles.container}>
      {/* Top Nav */}
      <nav className={styles.topNav}>
        <Link href="/" style={{ textDecoration: "none" }}>
          <Button appearance="subtle" icon={<ArrowLeft16Regular />}>
            トップページへ戻る
          </Button>
        </Link>
      </nav>

      {/* Header */}
      <header className={styles.header}>
        <Title1>MLB 試合一覧 &amp; リアルタイム速報</Title1>
        <Subtitle1 style={{ color: tokens.colorNeutralForeground2 }}>
          進行中（Live）および日本時間（JST）の日付ごとに試合を選択して、一球速報・スコアボード・Statcast指標をリアルタイムに閲覧できます。
        </Subtitle1>
      </header>

      {/* Date Navigation Bar */}
      <section className={styles.dateNavCard} aria-label="日付ナビゲーション">
        <Link href={`/games?date=${prevDate}`} style={{ textDecoration: "none" }}>
          <Button appearance="outline" icon={<ArrowLeft16Regular />}>
            前日 ({prevDate})
          </Button>
        </Link>

        <div className={styles.dateNavCenter}>
          <Input
            type="date"
            value={currentDate}
            onChange={handleDateChange}
            className={styles.dateInput}
            aria-label="試合日付の選択 (日本時間)"
          />

          {latestDate && latestDate !== currentDate && (
            <Link href={`/games?date=${latestDate}`} style={{ textDecoration: "none" }}>
              <Button appearance="subtle" size="small">
                最新試合日 ({latestDate}) へ
              </Button>
            </Link>
          )}
        </div>

        <Link href={`/games?date=${nextDate}`} style={{ textDecoration: "none" }}>
          <Button appearance="outline" icon={<ArrowRight16Regular />} iconPosition="after">
            翌日 ({nextDate})
          </Button>
        </Link>
      </section>

      {/* Games List Grid */}
      <section className={styles.grid}>
        {games.length === 0 ? (
          <Card style={{ padding: "48px 24px", textAlign: "center", gridColumn: "1 / -1" }}>
            <Body1 style={{ color: tokens.colorNeutralForeground2, display: "block", marginBottom: "16px" }}>
              {formatDateJa(currentDate)} (日本時間) に行われた試合データはありません。
            </Body1>
            {latestDate && latestDate !== currentDate && (
              <div>
                <Link href={`/games?date=${latestDate}`} style={{ textDecoration: "none" }}>
                  <Button appearance="primary" icon={<ArrowRight16Regular />} iconPosition="after">
                    最新の試合日 ({latestDate}) を表示する
                  </Button>
                </Link>
              </div>
            )}
          </Card>

        ) : (
          games.map((g) => {
            const isLive =
              g.status.toLowerCase().includes("progress") ||
              g.status.toLowerCase().includes("live");
            const isFinal = g.status.toLowerCase().includes("final");

            return (
              <Card
                key={`game-${g.game_pk}`}
                className={`${styles.card} ${isLive ? styles.liveCard : ""}`}
              >
                <div>
                  <CardHeader
                    image={<Sport24Regular style={{ color: isLive ? tokens.colorBrandForeground1 : tokens.colorNeutralForeground2 }} />}
                    header={
                      <Text weight="semibold" size={400}>
                        {g.away_team_abbr} vs {g.home_team_abbr}
                      </Text>
                    }
                    description={
                      <Caption1 style={{ color: tokens.colorNeutralForeground2 }}>
                        {g.game_date_time ? new Date(g.game_date_time).toLocaleString("ja-JP") : "日時未定"}
                      </Caption1>
                    }
                    action={
                      isLive ? (
                        <Badge appearance="filled" color="danger" className={styles.statusBadge}>
                          LIVE 進行中
                        </Badge>
                      ) : isFinal ? (
                        <Badge appearance="tint" color="success" icon={<CheckmarkCircle20Filled />} className={styles.statusBadge}>
                          試合終了
                        </Badge>
                      ) : (
                        <Badge appearance="outline" color="informative" className={styles.statusBadge}>
                          {g.status}
                        </Badge>
                      )
                    }
                  />

                  {/* Score Overview */}
                  <div className={styles.scoreOverview}>
                    <div style={{ textAlign: "center" }}>
                      <Text size={500} weight="bold">
                        {g.away_score !== null ? g.away_score : "-"}
                      </Text>
                      <br />
                      <Caption1>{g.away_team_name}</Caption1>
                    </div>
                    <Text size={400} weight="bold" style={{ color: tokens.colorNeutralForeground3 }}>
                      -
                    </Text>
                    <div style={{ textAlign: "center" }}>
                      <Text size={500} weight="bold">
                        {g.home_score !== null ? g.home_score : "-"}
                      </Text>
                      <br />
                      <Caption1>{g.home_team_name}</Caption1>
                    </div>
                  </div>
                </div>

                <CardFooter style={{ justifyContent: "flex-end" }}>
                  <Link href={`/games/${g.game_pk}/live`} style={{ textDecoration: "none" }}>
                    <Button
                      appearance={isLive ? "primary" : "secondary"}
                      icon={<ArrowRight16Regular />}
                      iconPosition="after"
                    >
                      {isLive ? "一球速報を見る (Live)" : "試合結果・詳細を見る"}
                    </Button>
                  </Link>
                </CardFooter>
              </Card>
            );
          })
        )}
      </section>
    </main>
  );
}
