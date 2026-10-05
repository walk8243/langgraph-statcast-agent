export interface ArticleListItem {
  id: number;
  title: string;
  prompt: string;
  model_name: string;
  created_at: string;
  summary: string;
}

export interface ArticleDetail {
  id: number;
  title: string;
  prompt: string;
  generated_sql: string | null;
  execution_summary: string | null;
  content_markdown: string;
  model_name: string;
  created_at: string;
  updated_at: string;
}
