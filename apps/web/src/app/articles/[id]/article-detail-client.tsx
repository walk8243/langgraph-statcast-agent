"use client";

import React, { useState } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Title1,
  Title2,
  Title3,
  Subtitle1,
  Body1,
  Caption1,
  Button,
  Card,
  Badge,
  makeStyles,
  shorthands,
  tokens,
  Text,
  Accordion,
  AccordionItem,
  AccordionHeader,
  AccordionPanel,
} from "@fluentui/react-components";
import {
  ArrowLeft16Regular,
  Bot24Regular,
  Calendar20Regular,
  Comment20Regular,
  Database24Regular,
  Code20Regular,
  Sparkle24Regular,
  Info20Regular,
} from "@fluentui/react-icons";
import { ArticleDetail } from "@/types/article";

const useStyles = makeStyles({
  container: {
    maxWidth: "1000px",
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
    rowGap: "16px",
    background: "linear-gradient(135deg, #f7f9fc 0%, #eef2f7 100%)",
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
  },
  titleArea: {
    display: "flex",
    flexDirection: "column",
    rowGap: "8px",
  },
  metaTagsRow: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    flexWrap: "wrap",
  },
  promptContainer: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.padding("14px", "16px"),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.borderLeft("4px", "solid", tokens.colorBrandStroke1),
    boxShadow: tokens.shadow2,
    display: "flex",
    flexDirection: "column",
    rowGap: "4px",
  },
  promptHeader: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    fontWeight: "600",
    color: tokens.colorNeutralForeground2,
    fontSize: "13px",
  },
  promptBody: {
    fontSize: "14px",
    fontStyle: "italic",
    color: tokens.colorNeutralForeground1,
  },
  metadataCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.padding("16px"),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow2,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
  },
  sqlCodeBlock: {
    backgroundColor: "#1e1e1e",
    color: "#d4d4d4",
    ...shorthands.padding("16px"),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    fontFamily: "Consolas, Monaco, 'Courier New', monospace",
    fontSize: "13px",
    lineHeight: "1.5",
    overflowX: "auto",
    marginTop: "8px",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
  },
  summaryText: {
    fontSize: "13px",
    color: tokens.colorNeutralForeground2,
    marginTop: "4px",
  },
  articleContentCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.padding("40px"),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow4,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
  },
  markdownContainer: {
    color: tokens.colorNeutralForeground1,
    lineHeight: "1.8",
    fontSize: "15px",
    "& h1": {
      fontSize: "26px",
      fontWeight: "700",
      marginTop: "32px",
      marginBottom: "16px",
      paddingBottom: "8px",
      borderBottom: `2px solid ${tokens.colorBrandStroke1}`,
      color: tokens.colorNeutralForeground1,
    },
    "& h2": {
      fontSize: "22px",
      fontWeight: "700",
      marginTop: "28px",
      marginBottom: "14px",
      paddingBottom: "6px",
      borderBottom: `1px solid ${tokens.colorNeutralStroke3}`,
      color: tokens.colorNeutralForeground1,
    },
    "& h3": {
      fontSize: "18px",
      fontWeight: "600",
      marginTop: "20px",
      marginBottom: "10px",
      color: tokens.colorNeutralForeground1,
    },
    "& p": {
      marginTop: "12px",
      marginBottom: "12px",
      fontSize: "15px",
    },
    "& ul, & ol": {
      marginTop: "8px",
      marginBottom: "16px",
      paddingLeft: "24px",
    },
    "& li": {
      marginTop: "4px",
      marginBottom: "4px",
      fontSize: "15px",
    },
    "& hr": {
      ...shorthands.border("none"),
      borderTop: `1px solid ${tokens.colorNeutralStroke3}`,
      margin: "32px 0",
    },
    "& blockquote": {
      ...shorthands.borderLeft("4px", "solid", tokens.colorBrandStroke1),
      margin: "16px 0",
      ...shorthands.padding("12px", "20px"),
      backgroundColor: tokens.colorNeutralBackground2,
      color: tokens.colorNeutralForeground2,
      ...shorthands.borderRadius("0", tokens.borderRadiusMedium, tokens.borderRadiusMedium, "0"),
    },
    "& strong": {
      fontWeight: "700",
      color: tokens.colorBrandForeground1,
    },
    "& table": {
      width: "100%",
      borderCollapse: "collapse",
      marginTop: "20px",
      marginBottom: "20px",
      display: "block",
      overflowX: "auto",
      boxShadow: tokens.shadow2,
      ...shorthands.borderRadius(tokens.borderRadiusMedium),
    },
    "& th, & td": {
      ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
      ...shorthands.padding("10px", "14px"),
      textAlign: "left",
      fontSize: "14px",
    },
    "& th": {
      backgroundColor: tokens.colorNeutralBackground3,
      fontWeight: "700",
      color: tokens.colorNeutralForeground1,
      whiteSpace: "nowrap",
    },
    "& tr:nth-child(even)": {
      backgroundColor: tokens.colorNeutralBackground2,
    },
    "& code": {
      backgroundColor: tokens.colorNeutralBackground3,
      ...shorthands.padding("2px", "6px"),
      ...shorthands.borderRadius(tokens.borderRadiusSmall),
      fontFamily: "monospace",
      fontSize: "13px",
    },
    "& pre": {
      backgroundColor: "#1e1e1e",
      color: "#d4d4d4",
      ...shorthands.padding("16px"),
      ...shorthands.borderRadius(tokens.borderRadiusMedium),
      overflowX: "auto",
      marginTop: "12px",
      marginBottom: "16px",
    },
  },
  footer: {
    ...shorthands.padding("24px", "0"),
    ...shorthands.borderTop("1px", "solid", tokens.colorNeutralStroke2),
    textAlign: "center",
    color: tokens.colorNeutralForeground3,
  },
});

interface ArticleDetailClientProps {
  article: ArticleDetail;
}

export function ArticleDetailClient({ article }: ArticleDetailClientProps) {
  const styles = useStyles();

  return (
    <main className={styles.container}>
      {/* Header Nav */}
      <nav className={styles.headerNav}>
        <Link href="/articles" style={{ textDecoration: "none" }}>
          <Button appearance="subtle" icon={<ArrowLeft16Regular />}>
            記事一覧へ戻る
          </Button>
        </Link>
        <Badge appearance="filled" color="brand" icon={<Sparkle24Regular />}>
          AI Report Detail
        </Badge>
      </nav>

      {/* Hero Banner */}
      <section className={styles.heroBanner}>
        <div className={styles.titleArea}>
          <div className={styles.metaTagsRow}>
            <Badge appearance="filled" color="brand">
              レポート # {article.id}
            </Badge>
            <Badge appearance="tint" color="informative" icon={<Bot24Regular />}>
              Model: {article.model_name}
            </Badge>
            <Caption1 style={{ color: tokens.colorNeutralForeground3, display: "flex", alignItems: "center", gap: "4px" }}>
              <Calendar20Regular style={{ fontSize: "14px" }} />
              作成日時: {new Date(article.created_at).toLocaleString("ja-JP", {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </Caption1>
          </div>
          <Title1 style={{ marginTop: "8px", lineHeight: "1.3" }}>{article.title}</Title1>
        </div>

        {/* Prompt section */}
        <div className={styles.promptContainer}>
          <div className={styles.promptHeader}>
            <Comment20Regular />
            <span>分析指示 (Prompt)</span>
          </div>
          <div className={styles.promptBody}>&ldquo;{article.prompt}&rdquo;</div>
        </div>
      </section>

      {/* Query & Execution Metadata Accordion */}
      {(article.generated_sql || article.execution_summary) && (
        <section className={styles.metadataCard}>
          <Accordion collapsible defaultOpenItems={[]}>
            <AccordionItem value="metadata">
              <AccordionHeader icon={<Code20Regular />}>
                <Text weight="semibold">データ集計メタデータ（Text-to-SQL &amp; ClickHouse）</Text>
              </AccordionHeader>
              <AccordionPanel>
                {article.execution_summary && (
                  <div style={{ marginBottom: "12px" }}>
                    <Caption1 className={styles.summaryText}>
                      <strong>集計実行サマリー:</strong> {article.execution_summary}
                    </Caption1>
                  </div>
                )}
                {article.generated_sql && (
                  <div>
                    <Caption1 style={{ color: tokens.colorNeutralForeground2, display: "flex", alignItems: "center", gap: "6px" }}>
                      <Database24Regular style={{ fontSize: "16px", color: tokens.colorBrandForeground1 }} />
                      自動生成された ClickHouse SQL クエリ:
                    </Caption1>
                    <pre className={styles.sqlCodeBlock}>
                      <code>{article.generated_sql}</code>
                    </pre>
                  </div>
                )}
              </AccordionPanel>
            </AccordionItem>
          </Accordion>
        </section>
      )}

      {/* Main Article Content */}
      <article className={styles.articleContentCard}>
        <div className={styles.markdownContainer}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {article.content_markdown}
          </ReactMarkdown>
        </div>
      </article>

      {/* Bottom Navigation */}
      <div style={{ display: "flex", justifyContent: "center", marginTop: "16px" }}>
        <Link href="/articles" style={{ textDecoration: "none" }}>
          <Button appearance="secondary" icon={<ArrowLeft16Regular />} size="large">
            記事一覧へ戻る
          </Button>
        </Link>
      </div>

      {/* Footer */}
      <footer className={styles.footer}>
        <Caption1>
          langgraph-statcast-agent &bull; Next.js 16 + React 19 + Fluent UI v9
        </Caption1>
      </footer>
    </main>
  );
}
