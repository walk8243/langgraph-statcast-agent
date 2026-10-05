import { getArticles } from "@/lib/articles";
import { ArticlesClient } from "./articles-client";
import { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "MLB データ分析・解説レポート一覧 | Statcast Agent",
  description:
    "Statcast 投球・打球データから Text-to-SQL と Gemini LLM により自動生成された MLB 解説レポート一覧",
};

export default async function ArticlesPage() {
  const articles = await getArticles();
  return <ArticlesClient articles={articles} />;
}
