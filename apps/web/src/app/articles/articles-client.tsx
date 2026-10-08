"use client";

import React from "react";
import Link from "next/link";
import {
  Title1,
  Title2,
  Title3,
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
  Sparkle24Regular,
  ArrowLeft16Regular,
  ArrowRight16Regular,
  Bot24Regular,
  Calendar20Regular,
  DocumentText24Regular,
  Comment20Regular,
  Rocket24Regular,
} from "@fluentui/react-icons";
import { ArticleListItem } from "@/types/article";

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
  headerNav: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    ...shorthands.borderBottom("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.padding("0", "0", "16px", "0"),
  },
  heroBanner: {
    ...shorthands.padding("36px", "32px"),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow4,
    display: "flex",
    flexDirection: "column",
    rowGap: "12px",
    background: "linear-gradient(135deg, #f0f4f9 0%, #e6effa 100%)",
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke1),
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))",
    gap: "24px",
  },
  card: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    boxShadow: tokens.shadow2,
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    transitionProperty: "all",
    transitionDuration: "200ms",
    ":hover": {
      boxShadow: tokens.shadow8,
      transform: "translateY(-2px)",
    },
  },
  cardContent: {
    ...shorthands.padding("12px", "16px"),
    display: "flex",
    flexDirection: "column",
    rowGap: "12px",
    flexGrow: 1,
  },
  metaRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    flexWrap: "wrap",
  },
  promptBox: {
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.padding("10px", "12px"),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.borderLeft("3px", "solid", tokens.colorBrandStroke1),
    display: "flex",
    alignItems: "flex-start",
    gap: "8px",
  },
  promptText: {
    fontSize: "13px",
    color: tokens.colorNeutralForeground2,
    fontStyle: "italic",
    lineHeight: "1.4",
  },
  summaryText: {
    color: tokens.colorNeutralForeground2,
    fontSize: "14px",
    lineHeight: "1.6",
  },
  emptyCard: {
    ...shorthands.padding("48px", "24px"),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.border("1px", "dashed", tokens.colorNeutralStroke1),
    textAlign: "center",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    rowGap: "16px",
  },
  footer: {
    ...shorthands.padding("24px", "0"),
    ...shorthands.borderTop("1px", "solid", tokens.colorNeutralStroke2),
    textAlign: "center",
    color: tokens.colorNeutralForeground3,
  },
});

interface ArticlesClientProps {
  articles: ArticleListItem[];
}

export function ArticlesClient({ articles }: ArticlesClientProps) {
  const styles = useStyles();

  return (
    <main className={styles.container}>
      {/* Header Nav */}
      <nav className={styles.headerNav}>
        <Link href="/" style={{ textDecoration: "none" }}>
          <Button appearance="subtle" icon={<ArrowLeft16Regular />}>
            ダッシュボードへ戻る
          </Button>
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Link href="/articles/desk" style={{ textDecoration: "none" }}>
            <Button appearance="primary" icon={<Rocket24Regular />}>
              AI 編集デスクと企画する
            </Button>
          </Link>
          <Badge appearance="filled" color="brand" icon={<Sparkle24Regular />}>
            AI Generated Reports
          </Badge>
        </div>
      </nav>

      {/* Hero Banner */}
      <section className={styles.heroBanner}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
          <div style={{ display: "flex", flexDirection: "column", rowGap: "8px" }}>
            <Badge appearance="outline" color="brand" style={{ alignSelf: "flex-start" }}>
              Text-to-SQL &amp; LLM 記事生成
            </Badge>
            <Title1>MLB データ分析・解説レポート一覧</Title1>
            <Subtitle1 style={{ color: tokens.colorNeutralForeground2 }}>
              自然言語の指示から ClickHouse の Statcast データを動的集計し、Google Gemini が自動執筆した解説記事です。
            </Subtitle1>
            <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>
              登録記事数: {articles.length} 件
            </Caption1>
          </div>
          <Link href="/articles/desk" style={{ textDecoration: "none", alignSelf: "center" }}>
            <Button appearance="primary" size="large" icon={<Sparkle24Regular />}>
              新機能: AI 編集デスクと対話企画
            </Button>
          </Link>
        </div>
      </section>

      {/* Articles Grid or Empty State */}
      {articles.length === 0 ? (
        <div className={styles.emptyCard}>
          <DocumentText24Regular style={{ fontSize: "48px", color: tokens.colorNeutralForeground3 }} />
          <Title3>生成された記事がまだありません</Title3>
          <Body1 style={{ color: tokens.colorNeutralForeground2 }}>
            CLI ツール（<code>article-generator --generate-article &quot;お題&quot;</code>）を実行すると、ここに記事が追加されます。
          </Body1>
        </div>
      ) : (
        <section className={styles.grid}>
          {articles.map((article) => (
            <Card key={article.id} className={styles.card}>
              <CardHeader
                image={<DocumentText24Regular style={{ color: tokens.colorBrandForeground1 }} />}
                header={
                  <Text weight="semibold" size={400} style={{ lineHeight: "1.4" }}>
                    {article.title}
                  </Text>
                }
              />

              <div className={styles.cardContent}>
                <div className={styles.metaRow}>
                  <Badge appearance="tint" color="informative" icon={<Bot24Regular />}>
                    {article.model_name}
                  </Badge>
                  <Caption1 style={{ color: tokens.colorNeutralForeground3, display: "flex", alignItems: "center", gap: "4px" }}>
                    <Calendar20Regular style={{ fontSize: "14px" }} />
                    {new Date(article.created_at).toLocaleString("ja-JP", {
                      year: "numeric",
                      month: "2-digit",
                      day: "2-digit",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </Caption1>
                </div>

                <div className={styles.promptBox}>
                  <Comment20Regular style={{ color: tokens.colorBrandForeground1, flexShrink: 0, marginTop: "2px" }} />
                  <span className={styles.promptText}>&ldquo;{article.prompt}&rdquo;</span>
                </div>

                <Body1 className={styles.summaryText}>{article.summary}</Body1>
              </div>

              <CardFooter>
                <Link href={`/articles/${article.id}`} style={{ textDecoration: "none", width: "100%" }}>
                  <Button
                    appearance="primary"
                    icon={<ArrowRight16Regular />}
                    iconPosition="after"
                    style={{ width: "100%" }}
                  >
                    記事を読む
                  </Button>
                </Link>
              </CardFooter>
            </Card>
          ))}
        </section>
      )}

      {/* Footer */}
      <footer className={styles.footer}>
        <Caption1>
          langgraph-statcast-agent &bull; Next.js 16 + React 19 + Fluent UI v9
        </Caption1>
      </footer>
    </main>
  );
}
