"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Title1,
  Body1,
  Caption1,
  Button,
  Badge,
  makeStyles,
  shorthands,
  tokens,
  Text,
  Textarea,
  Spinner,
} from "@fluentui/react-components";
import {
  ArrowLeft16Regular,
  Bot24Regular,
  Person24Regular,
  Send20Regular,
  Sparkle24Regular,
  DocumentBulletList24Regular,
  Rocket24Regular,
  CheckmarkCircle24Regular,
  DismissCircle24Regular,
} from "@fluentui/react-icons";
import {
  ChatMessage,
  DeskChatRequest,
  DeskChatResponse,
  DeskGenerateResponse,
  DeskProposal,
} from "@/types/desk";

const useStyles = makeStyles({
  container: {
    maxWidth: "1000px",
    marginLeft: "auto",
    marginRight: "auto",
    ...shorthands.padding("32px", "24px"),
    display: "flex",
    flexDirection: "column",
    rowGap: "24px",
    minHeight: "100vh",
  },
  headerNav: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    ...shorthands.borderBottom("1px", "solid", tokens.colorNeutralStroke2),
    ...shorthands.padding("0", "0", "16px", "0"),
  },
  heroBanner: {
    ...shorthands.padding("28px", "32px"),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow4,
    display: "flex",
    flexDirection: "column",
    rowGap: "8px",
    background: "linear-gradient(135deg, #eef4fc 0%, #e2ecf9 100%)",
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke1),
  },
  chatArea: {
    display: "flex",
    flexDirection: "column",
    rowGap: "20px",
    flexGrow: 1,
    marginBottom: "16px",
  },
  messageRow: {
    display: "flex",
    columnGap: "14px",
    alignItems: "flex-start",
  },
  userMessageRow: {
    flexDirection: "row-reverse",
  },
  avatar: {
    width: "40px",
    height: "40px",
    ...shorthands.borderRadius("50%"),
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1,
  },
  userAvatar: {
    backgroundColor: tokens.colorNeutralBackground4,
    color: tokens.colorNeutralForeground1,
  },
  messageBubble: {
    maxWidth: "80%",
    ...shorthands.padding("14px", "18px"),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow2,
    lineHeight: "1.6",
    fontSize: "14px",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
  assistantBubble: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    color: tokens.colorNeutralForeground1,
  },
  userBubble: {
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
  },
  proposalCard: {
    marginTop: "14px",
    ...shorthands.padding("20px"),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.border("1px", "solid", tokens.colorBrandStroke2),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    display: "flex",
    flexDirection: "column",
    rowGap: "14px",
  },
  sectionItem: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.padding("10px", "14px"),
    ...shorthands.borderRadius(tokens.borderRadiusSmall),
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    fontSize: "13px",
  },
  requirementTag: {
    display: "inline-block",
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1,
    ...shorthands.padding("4px", "8px"),
    ...shorthands.borderRadius(tokens.borderRadiusSmall),
    fontSize: "12px",
    fontWeight: "600",
    marginRight: "6px",
  },
  inputCard: {
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.padding("16px", "20px"),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    boxShadow: tokens.shadow4,
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    display: "flex",
    flexDirection: "column",
    rowGap: "12px",
  },
  quickChipsRow: {
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
    alignItems: "center",
  },
  generatingBox: {
    ...shorthands.padding("24px"),
    backgroundColor: tokens.colorBrandBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.border("1px", "solid", tokens.colorBrandStroke1),
    textAlign: "center",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    rowGap: "12px",
  },
  successBox: {
    ...shorthands.padding("20px"),
    backgroundColor: "#f0fdf4",
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.border("1px", "solid", "#86efac"),
    display: "flex",
    flexDirection: "column",
    rowGap: "10px",
  },
  errorBox: {
    backgroundColor: "#fef2f2",
    ...shorthands.border("1px", "solid", "#f87171"),
    ...shorthands.padding("12px", "16px"),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    color: "#991b1b",
    display: "flex",
    alignItems: "center",
    columnGap: "8px",
  },
  footer: {
    ...shorthands.padding("24px", "0"),
    ...shorthands.borderTop("1px", "solid", tokens.colorNeutralStroke2),
    textAlign: "center",
    color: tokens.colorNeutralForeground3,
  },
});

const QUICK_PROMPTS = [
  "2026年 鈴木誠也・村上宗隆・岡本和真の打撃徹底比較",
  "大谷翔平の打球初速とバレル率の進化分析",
  "今季MLB投手の剛速球（フォーシーム95mph以上）に対する日本人打者の適応度",
];

export function DeskChatClient() {
  const styles = useStyles();
  const chatEndRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "initial",
      role: "assistant",
      content:
        "こんにちは！MLB Statcast 編集デスクAIです。\n書きたい記事のアイデアや気になる選手、比較したいテーマを教えてください。\nStatcastのデータ分析ならではの切り口や章立て・取材項目を一緒に組み立てましょう！",
      timestamp: "initial",
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingArticleTitle, setGeneratingArticleTitle] = useState("");
  const [latestProposal, setLatestProposal] = useState<DeskProposal | null>(null);
  const [generatedArticleId, setGeneratedArticleId] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isGenerating, latestProposal]);

  const handleSendMessage = useCallback(async (textToSend?: string) => {
    const text = (textToSend || inputText).trim();
    if (!text || isLoading || isGenerating) return;

    setErrorMsg(null);
    setInputText("");

    const currentLen = messages.length;
    const userMsg: ChatMessage = {
      id: `user-${currentLen + 1}`,
      role: "user",
      content: text,
      timestamp: `msg-${currentLen + 1}`,
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const historyPayload = newMessages
        .filter((m) => m.id !== "initial")
        .map((m) => ({ role: m.role, content: m.content }));

      const res = await fetch("/api/articles/desk/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: historyPayload } as DeskChatRequest),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Request failed with status ${res.status}`);
      }

      const data = (await res.json()) as DeskChatResponse;

      const aiMsg: ChatMessage = {
        id: `assistant-${currentLen + 2}`,
        role: "assistant",
        content: data.reply,
        timestamp: `msg-${currentLen + 2}`,
        proposal: data.proposal,
        is_finalized: data.is_finalized,
      };

      setMessages((prev) => [...prev, aiMsg]);
      if (data.proposal) {
        setLatestProposal(data.proposal);
      }
    } catch (err) {
      console.error("Chat error:", err);
      setErrorMsg(err instanceof Error ? err.message : "チャット送信に失敗しました");
    } finally {
      setIsLoading(false);
    }
  }, [inputText, isLoading, isGenerating, messages]);

  const handleGenerateArticle = async (proposalToGenerate: DeskProposal) => {
    if (isGenerating || isLoading) return;

    setIsGenerating(true);
    setGeneratingArticleTitle(proposalToGenerate.title);
    setErrorMsg(null);

    try {
      const res = await fetch("/api/articles/desk/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ proposal: proposalToGenerate }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || "記事生成パイプラインの実行に失敗しました");
      }

      const data = (await res.json()) as DeskGenerateResponse;
      if (data.success && data.article_id) {
        setGeneratedArticleId(data.article_id);
      } else {
        throw new Error(data.error || "記事IDの取得に失敗しました");
      }
    } catch (err) {
      console.error("Generate error:", err);
      setErrorMsg(err instanceof Error ? err.message : "記事生成に失敗しました");
    } finally {
      setIsGenerating(false);
    }
  };

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
          AI Editorial Desk
        </Badge>
      </nav>

      {/* Hero Banner */}
      <section className={styles.heroBanner}>
        <Title1>AI 編集デスクと企画する</Title1>
        <Body1 style={{ color: tokens.colorNeutralForeground2, lineHeight: "1.5" }}>
          テーマや着目したい選手を伝えるだけで、編集長AIがStatcastデータに基づく切り口を壁打ち提案。
          章立てと取材データリストを固めて、ワンクリックで本格的な総合解説記事を執筆できます。
        </Body1>
      </section>

      {/* Error Banner */}
      {errorMsg && (
        <div className={styles.errorBox}>
          <DismissCircle24Regular />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Chat Messages Area */}
      <section className={styles.chatArea}>
        {messages.map((m) => {
          const isUser = m.role === "user";
          return (
            <div
              key={m.id}
              className={`${styles.messageRow} ${isUser ? styles.userMessageRow : ""}`}
            >
              <div className={`${styles.avatar} ${isUser ? styles.userAvatar : ""}`}>
                {isUser ? <Person24Regular /> : <Bot24Regular />}
              </div>
              <div
                className={`${styles.messageBubble} ${
                  isUser ? styles.userBubble : styles.assistantBubble
                }`}
              >
                <div>{m.content}</div>

                {/* Proposal Draft Card */}
                {m.proposal && (
                  <div className={styles.proposalCard}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <DocumentBulletList24Regular style={{ color: tokens.colorBrandForeground1 }} />
                      <Text weight="semibold" size={400}>
                        【企画案ドラフト】: {m.proposal.title}
                      </Text>
                    </div>

                    <Caption1 style={{ color: tokens.colorNeutralForeground2 }}>
                      <strong>主旨:</strong> {m.proposal.theme}
                    </Caption1>

                    <div style={{ display: "flex", flexDirection: "column", rowGap: "8px" }}>
                      <Text weight="semibold" size={200}>想定アウトライン（章構成）:</Text>
                      {m.proposal.sections.map((sec, idx) => (
                        <div key={idx} className={styles.sectionItem}>
                          <Text weight="semibold">{idx + 1}. {sec.title}</Text>
                          {sec.material_label && (
                            <Badge appearance="outline" color="brand" style={{ marginLeft: "8px" }}>
                              {sec.material_label}
                            </Badge>
                          )}
                          <div style={{ color: tokens.colorNeutralForeground2, marginTop: "2px" }}>
                            {sec.description}
                          </div>
                        </div>
                      ))}
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", rowGap: "6px" }}>
                      <Text weight="semibold" size={200}>取材データ要求リスト (Text-to-SQL):</Text>
                      {m.proposal.requirements.map((req, idx) => (
                        <div key={idx} style={{ fontSize: "12px", color: tokens.colorNeutralForeground2 }}>
                          <span className={styles.requirementTag}>{req.label}</span>
                          <code>{req.prompt}</code>
                        </div>
                      ))}
                    </div>

                    <Button
                      appearance="primary"
                      icon={<Rocket24Regular />}
                      size="large"
                      disabled={isLoading || isGenerating}
                      onClick={() => m.proposal && handleGenerateArticle(m.proposal)}
                      style={{ marginTop: "8px" }}
                    >
                      この企画で総合解説記事を執筆する
                    </Button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Spinner for Chat */}
        {isLoading && (
          <div className={styles.messageRow}>
            <div className={styles.avatar}>
              <Bot24Regular />
            </div>
            <div className={`${styles.messageBubble} ${styles.assistantBubble}`}>
              <Spinner size="tiny" label="編集デスクが思考・企画案を策定中..." />
            </div>
          </div>
        )}

        {/* Multi-material Generation Progress Box */}
        {isGenerating && (
          <div className={styles.generatingBox}>
            <Spinner size="medium" label="多段オーケストレーション記事を執筆中..." />
            <Text weight="semibold" size={400}>
              『{generatingArticleTitle}』
            </Text>
            <Caption1 style={{ color: tokens.colorNeutralForeground2 }}>
              1. Text-to-SQL で複数の ClickHouse データ素材を並列集計中...<br />
              2. 収集したファクトテーブルを章立てに埋め込み、Gemini で総合分析記事を合成中...
            </Caption1>
          </div>
        )}

        {/* Generated Success Card */}
        {generatedArticleId && (
          <div className={styles.successBox}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <CheckmarkCircle24Regular style={{ color: "#16a34a" }} />
              <Text weight="bold" size={400} style={{ color: "#15803d" }}>
                総合解説記事の生成・保存が完了しました！ (記事 #{generatedArticleId})
              </Text>
            </div>
            <Body1 style={{ color: "#166534" }}>
              複数のデータ素材表が埋め込まれたリッチな解説レポートが完成しました。
            </Body1>
            <div>
              <Link href={`/articles/${generatedArticleId}`} style={{ textDecoration: "none" }}>
                <Button appearance="primary" size="large">
                  完成した記事を読む →
                </Button>
              </Link>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </section>

      {/* Input Card */}
      <section className={styles.inputCard}>
        {/* Quick prompt chips */}
        <div className={styles.quickChipsRow}>
          <Caption1 style={{ color: tokens.colorNeutralForeground3 }}>ヒント:</Caption1>
          {QUICK_PROMPTS.map((qp, idx) => (
            <Button
              key={idx}
              appearance="subtle"
              size="small"
              disabled={isLoading || isGenerating}
              onClick={() => handleSendMessage(qp)}
            >
              💡 {qp}
            </Button>
          ))}
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "flex-end" }}>
          <Textarea
            value={inputText}
            onChange={(e, data) => setInputText(data.value)}
            placeholder="記事のテーマや選手名、比較したいポイントを入力してください... (例: 鈴木誠也と村上宗隆のメジャー適応度の違いを比較したい)"
            resize="vertical"
            rows={2}
            disabled={isLoading || isGenerating}
            style={{ flexGrow: 1 }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
          />
          <Button
            appearance="primary"
            icon={<Send20Regular />}
            size="large"
            disabled={!inputText.trim() || isLoading || isGenerating}
            onClick={() => handleSendMessage()}
          >
            送信
          </Button>
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
