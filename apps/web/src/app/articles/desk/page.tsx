import { Metadata } from "next";
import { DeskChatClient } from "./desk-chat-client";

export const metadata: Metadata = {
  title: "AI 編集デスク | MLB Statcast 分析レポート企画",
  description: "MLB Statcast データ分析の専門AI編集デスクと対話し、立体的な取材・章立て企画から総合解説記事を生成します。",
};

export default function DeskPage() {
  return <DeskChatClient />;
}
