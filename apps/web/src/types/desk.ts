export interface DeskSection {
  title: string;
  description: string;
  material_label?: string | null;
}

export interface DeskRequirement {
  label: string;
  prompt: string;
  section_hint?: string | null;
}

export interface DeskProposal {
  title: string;
  theme: string;
  sections: DeskSection[];
  requirements: DeskRequirement[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  proposal?: DeskProposal | null;
  is_finalized?: boolean;
}

export interface DeskChatRequest {
  messages: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
}

export interface DeskChatResponse {
  reply: string;
  is_finalized: boolean;
  proposal: DeskProposal | null;
  error?: string;
}

export interface DeskGenerateRequest {
  proposal: DeskProposal;
}

export interface DeskGenerateResponse {
  success: boolean;
  article_id?: number;
  title?: string;
  error?: string;
}
