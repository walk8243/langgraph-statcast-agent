"use client";

import React from "react";
import Link from "next/link";
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
});

interface GamesClientProps {
  games: GameHeaderInfo[];
}

export default function GamesClient({ games }: GamesClientProps) {
  const styles = useStyles();

  return (
    <main className={styles.container}>
      {/* Top Nav */}
      <nav className={styles.topNav}>
        <Link href="/" style={{ textDecoration: "none" }}>
          <Button appearance="subtle" icon={<ArrowLeft16Regular />}>
            トップページへ戻る
          </Button>
        </Link>
        <Badge appearance="filled" color="brand">
          試合数: {games.length} 件
        </Badge>
      </nav>

      {/* Header */}
      <header className={styles.header}>
        <Title1>MLB 試合一覧 &amp; リアルタイム速報</Title1>
        <Subtitle1 style={{ color: tokens.colorNeutralForeground2 }}>
          進行中（Live）および直近の試合を選択して、一球速報・スコアボード・Statcast指標をリアルタイムに閲覧できます。
        </Subtitle1>
      </header>

      {/* Games List Grid */}
      <section className={styles.grid}>
        {games.length === 0 ? (
          <Card style={{ padding: "32px", textAlign: "center", gridColumn: "1 / -1" }}>
            <Body1 style={{ color: tokens.colorNeutralForeground3 }}>
              現在登録されている試合データがありません。
            </Body1>
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
                        <Badge appearance="filled" color="danger">
                          LIVE 進行中
                        </Badge>
                      ) : isFinal ? (
                        <Badge appearance="tint" color="success" icon={<CheckmarkCircle20Filled />}>
                          試合終了
                        </Badge>
                      ) : (
                        <Badge appearance="outline" color="informative">
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
