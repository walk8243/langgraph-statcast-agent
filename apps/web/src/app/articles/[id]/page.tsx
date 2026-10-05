import { Metadata } from "next";
import { notFound } from "next/navigation";
import { getArticleById } from "@/lib/articles";
import { ArticleDetailClient } from "./article-detail-client";

export const dynamic = "force-dynamic";

interface ArticleDetailPageProps {
  params: Promise<{
    id: string;
  }>;
}

export async function generateMetadata({
  params,
}: ArticleDetailPageProps): Promise<Metadata> {
  const { id } = await params;
  const idNum = Number.parseInt(id, 10);

  if (Number.isNaN(idNum)) {
    return {
      title: "記事が見つかりません | Statcast Agent Web",
    };
  }

  const article = await getArticleById(idNum);
  if (!article) {
    return {
      title: "記事が見つかりません | Statcast Agent Web",
    };
  }

  return {
    title: `${article.title} | Statcast Agent Web`,
    description: `${article.prompt} に対する Statcast データ分析および Google Gemini による自動生成解説記事です。`,
  };
}

export default async function ArticleDetailPage({
  params,
}: ArticleDetailPageProps) {
  const { id } = await params;
  const idNum = Number.parseInt(id, 10);

  if (Number.isNaN(idNum)) {
    notFound();
  }

  const article = await getArticleById(idNum);
  if (!article) {
    notFound();
  }

  return <ArticleDetailClient article={article} />;
}
