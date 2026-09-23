"use client";

import React, { useState } from "react";
import {
  Title1,
  Title2,
  Subtitle1,
  Body1,
  Caption1,
  Button,
  Card,
  CardHeader,
  CardFooter,
  Badge,
  makeStyles,
  shorthands,
  tokens,
  Text,
} from "@fluentui/react-components";
import {
  Database24Regular,
  PeopleTeam24Regular,
  Sparkle24Regular,
  ArrowRight16Regular,
  CheckmarkCircle20Filled,
  ArrowSync24Regular,
} from "@fluentui/react-icons";

const useStyles = makeStyles({
  container: {
    maxWidth: "1200px",
    marginLeft: "auto",
    marginRight: "auto",
    ...shorthands.padding("32px", "24px"),
    display: "flex",
    flexDirection: "column",
    rowGap: "32px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    ...shorthands.borderBottom("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.padding("0", "0", "16px", "0"),
  },
  logoGroup: {
    display: "flex",
    alignItems: "center",
    columnGap: "12px",
  },
  badgeGroup: {
    display: "flex",
    alignItems: "center",
    columnGap: "8px",
  },
  hero: {
    ...shorthands.padding("48px", "32px"),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow4,
    display: "flex",
    flexDirection: "column",
    rowGap: "16px",
    background: "linear-gradient(135deg, #ffffff 0%, #f0f4f9 100%)",
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke1),
  },
  heroButtons: {
    display: "flex",
    columnGap: "12px",
    marginTop: "8px",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
    gap: "24px",
  },
  card: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    boxShadow: tokens.shadow2,
    transitionProperty: "all",
    transitionDuration: "200ms",
    ":hover": {
      boxShadow: tokens.shadow8,
      transform: "translateY(-2px)",
    },
  },
  cardHeaderIcon: {
    color: tokens.colorBrandForeground1,
  },
  cardContent: {
    ...shorthands.padding("12px", "16px"),
    display: "flex",
    flexDirection: "column",
    rowGap: "8px",
  },
  verificationBox: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.padding("24px"),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    display: "flex",
    flexDirection: "column",
    rowGap: "16px",
  },
  counterRow: {
    display: "flex",
    alignItems: "center",
    columnGap: "16px",
  },
  footer: {
    ...shorthands.padding("24px", "0"),
    ...shorthands.borderTop("1px", "solid", tokens.colorNeutralStroke2),
    textAlign: "center",
    color: tokens.colorNeutralForeground3,
  },
});

export default function HomePage() {
  const styles = useStyles();
  const [clickCount, setClickCount] = useState(0);

  return (
    <main className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.logoGroup}>
          <Sparkle24Regular className={styles.cardHeaderIcon} />
          <Title2>Statcast Agent Web</Title2>
        </div>
        <div className={styles.badgeGroup}>
          <Badge appearance="filled" color="brand">
            Next.js App Router
          </Badge>
          <Badge appearance="tint" color="success" icon={<CheckmarkCircle20Filled />}>
            Fluent UI v9
          </Badge>
        </div>
      </header>

      {/* Hero Section */}
      <section className={styles.hero}>
        <Badge appearance="outline" color="brand" style={{ alignSelf: "flex-start" }}>
          フロントエンド表示基盤
        </Badge>
        <Title1>MLB Statcast Agent Dashboard</Title1>
        <Subtitle1 style={{ color: tokens.colorNeutralForeground2 }}>
          LangGraph と Google Gemini を活用した MLB 選手分析・レポート生成基盤の Web ダッシュボード
        </Subtitle1>
        <Body1 style={{ maxWidth: "720px", color: tokens.colorNeutralForeground3 }}>
          PostgreSQL のチーム・選手データおよび ClickHouse の Statcast 投球集計データを活用し、
          直感的な UI でデータの閲覧と AI エージェントによる分析レポートを提供します。
        </Body1>

        <div className={styles.heroButtons}>
          <Button
            appearance="primary"
            icon={<ArrowRight16Regular />}
            iconPosition="after"
            size="large"
          >
            チーム一覧画面へ
          </Button>
          <Button appearance="secondary" size="large">
            システム概要
          </Button>
        </div>
      </section>

      {/* Feature Cards Grid */}
      <section className={styles.grid}>
        <Card className={styles.card}>
          <CardHeader
            image={<PeopleTeam24Regular className={styles.cardHeaderIcon} />}
            header={<Text weight="semibold">MLB チーム・選手一覧</Text>}
            description={<Caption1>マスターデータ閲覧</Caption1>}
            action={<Badge color="informative">Upcoming</Badge>}
          />
          <div className={styles.cardContent}>
            <Body1>
              全30球団をア・リーグ / ナ・リーグや地区別に一覧表示し、各球団のロスターおよび選手詳細ページへとナビゲートします。
            </Body1>
          </div>
          <CardFooter>
            <Button appearance="subtle" icon={<ArrowRight16Regular />} iconPosition="after">
              詳細を確認
            </Button>
          </CardFooter>
        </Card>

        <Card className={styles.card}>
          <CardHeader
            image={<Database24Regular className={styles.cardHeaderIcon} />}
            header={<Text weight="semibold">RDB / PostgreSQL 連携</Text>}
            description={<Caption1>Next.js Server Components</Caption1>}
            action={<Badge color="success">Connected</Badge>}
          />
          <div className={styles.cardContent}>
            <Body1>
              Next.js サーバー側から直接 PostgreSQL（teams, players, player_reports テーブル）へ高速アクセス。別途バックエンドAPIサーバーなしでシームレスに連携。
            </Body1>
          </div>
          <CardFooter>
            <Button appearance="subtle" icon={<ArrowRight16Regular />} iconPosition="after">
              DB接続仕様
            </Button>
          </CardFooter>
        </Card>

        <Card className={styles.card}>
          <CardHeader
            image={<Sparkle24Regular className={styles.cardHeaderIcon} />}
            header={<Text weight="semibold">LangGraph AI エージェント</Text>}
            description={<Caption1>選手解説レポート自動生成</Caption1>}
            action={<Badge color="brand">Gemini 3.8 Flash</Badge>}
          />
          <div className={styles.cardContent}>
            <Body1>
              球種別被打率や球速・変化量などの Statcast 指標を基に、Google Gemini が自然な解説レポートを自動生成・蓄積します。
            </Body1>
          </div>
          <CardFooter>
            <Button appearance="subtle" icon={<ArrowRight16Regular />} iconPosition="after">
              エージェント実行
            </Button>
          </CardFooter>
        </Card>
      </section>

      {/* Interactive Verification Section */}
      <section className={styles.verificationBox}>
        <Text weight="semibold" size={400}>
          Fluent UI インタラクション検証
        </Text>
        <Body1>
          Fluent UI のボタンスタイルや状態管理（React Hooks）がクライアントサイドで正常に機能しているかをテストできます。
        </Body1>
        <div className={styles.counterRow}>
          <Button
            appearance="primary"
            icon={<ArrowSync24Regular />}
            onClick={() => setClickCount((prev) => prev + 1)}
          >
            カウンターを増やす
          </Button>
          <Badge size="large" appearance="filled" color="brand">
            クリック回数: {clickCount}
          </Badge>
          {clickCount > 0 && (
            <Button appearance="outline" onClick={() => setClickCount(0)}>
              リセット
            </Button>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <Caption1>
          langgraph-statcast-agent &bull; Next.js 16 + React 19 + Fluent UI v9
        </Caption1>
      </footer>
    </main>
  );
}
