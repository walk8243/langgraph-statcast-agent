import { query } from "./db";
import { ArticleListItem, ArticleDetail } from "@/types/article";

interface ArticleRow {
  id: number | string;
  title: string;
  prompt: string;
  generated_sql?: string | null;
  execution_summary?: string | null;
  content_markdown?: string;
  summary_snippet?: string;
  model_name: string;
  created_at: Date | string;
  updated_at?: Date | string;
}

function cleanMarkdownSnippet(text: string): string {
  return text
    .replace(/^#+\s+/gm, "") // remove headers
    .replace(/[*_~`]/g, "") // remove formatting characters
    .replace(/\[(.*?)\]\(.*?\)/g, "$1") // link markdown
    .replace(/\|/g, " ") // table borders
    .replace(/\s+/g, " ") // collapse whitespaces
    .trim();
}

export async function getArticles(limit = 50): Promise<ArticleListItem[]> {
  try {
    const res = await query<ArticleRow>(
      `SELECT
        id,
        title,
        prompt,
        model_name,
        created_at,
        SUBSTRING(content_markdown FROM 1 FOR 400) AS summary_snippet
      FROM articles
      ORDER BY created_at DESC
      LIMIT $1`,
      [limit]
    );

    return res.rows.map((row) => ({
      id: Number(row.id),
      title: row.title,
      prompt: row.prompt,
      model_name: row.model_name,
      created_at:
        row.created_at instanceof Date
          ? row.created_at.toISOString()
          : String(row.created_at),
      summary: cleanMarkdownSnippet(row.summary_snippet || "").slice(0, 160) + "...",
    }));
  } catch (error) {
    console.error("Failed to fetch articles:", error);
    return [];
  }
}

export async function getArticleById(id: number): Promise<ArticleDetail | null> {
  try {
    const res = await query<ArticleRow>(
      `SELECT
        id,
        title,
        prompt,
        generated_sql,
        execution_summary,
        content_markdown,
        model_name,
        created_at,
        updated_at
      FROM articles
      WHERE id = $1`,
      [id]
    );

    if (res.rows.length === 0) {
      return null;
    }

    const row = res.rows[0];
    return {
      id: Number(row.id),
      title: row.title,
      prompt: row.prompt,
      generated_sql: row.generated_sql || null,
      execution_summary: row.execution_summary || null,
      content_markdown: row.content_markdown || "",
      model_name: row.model_name,
      created_at:
        row.created_at instanceof Date
          ? row.created_at.toISOString()
          : String(row.created_at),
      updated_at:
        row.updated_at instanceof Date
          ? row.updated_at.toISOString()
          : String(row.updated_at),
    };
  } catch (error) {
    console.error(`Failed to fetch article with id ${id}:`, error);
    return null;
  }
}
