export interface HealthStatus {
  api: 'ok' | 'error' | 'checking';
  ollama: 'ok' | 'unreachable' | 'checking';
}

export interface Scores {
  combined?: number;
  keyword?: number;
  semantic?: number;
  grep_match?: number;
  verified_match?: number;
}

export interface Citation {
  filename: string;
  page: number;
  excerpt: string;
  match_type: 'keyword' | 'semantic' | 'both' | 'grep' | 'verified';
  keyword_matches: string[];
  scores: Scores;
}

export interface RetrievalSummary {
  source: string;
  match_type: 'keyword' | 'semantic' | 'both';
  keywords_found: string[];
  scores: Scores;
}

// Two-stage MCQ types
export interface Stage1Analysis {
  search_terms: string[];
  reasoning: string;
  raw_response?: string;
}

export interface GrepResult {
  term: string;
  filename: string;
  page: number;
  match_line: string;
  context_before: string[];
  context_after: string[];
  full_excerpt: string;
}

// NEW: Option validation - shows which options were found
export interface OptionValidation {
  option: string;
  found_in_documents: boolean;
  evidence_count: number;
  sources: string[];
}

// NEW: Structured justification for answers
export interface AnswerJustification {
  answer: string | null;
  confidence: 'HIGH' | 'LOW' | 'NONE' | 'UNKNOWN';
  evidence_quote: string | null;
  source: string | null;
  explanation: string;
  validated: boolean;
  validation_note: string;
}

export interface Reasoning {
  // Original fields (for non-MCQ)
  keywords_extracted?: string[];
  chunks_retrieved?: number;
  retrieval_summary?: RetrievalSummary[];
  prompt_sent: string;
  is_mcq?: boolean;
  mcq_options?: string[];
  // Two-stage MCQ fields
  stage1_analysis?: Stage1Analysis;
  stage2_grep_results?: GrepResult[];
  // NEW: Validation and justification
  options_validation?: OptionValidation[];
  justification?: AnswerJustification;
  used_web_search?: boolean;
  web_search_query?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'error';
  content: string;
  citations?: Citation[];
  reasoning?: Reasoning;
}

export interface QueryRequest {
  question: string;
  top_k?: number;
  enable_web_fallback?: boolean;
  chat_id?: string;
  project_id?: string;
  include_history?: boolean;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  reasoning: Reasoning;
  chat_id?: string;
  message_id?: string;
}

// Project types
export interface Project {
  id: string;
  name: string;
  description?: string;
  color: string;
  created_at: string;
  updated_at: string;
  document_count?: number;
  chat_count?: number;
}

export interface ProjectDetail extends Project {
  recent_documents?: Document[];
  recent_chats?: Chat[];
}

// Document types
export interface Document {
  id: string;
  project_id: string;
  filename: string;
  filepath: string;
  file_size?: number;
  page_count?: number;
  chunk_count?: number;
  uploaded_at: string;
}

// Chat types (replaces Conversation)
export interface Chat {
  id: string;
  project_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  preview?: string;
}

export interface ChatDetail extends Chat {
  messages: Message[];
}

export interface ChatList {
  chats: Chat[];
  total: number;
  page: number;
  per_page: number;
}

// Search result type - includes matched_content from backend
export interface ChatSearchResult extends Chat {
  matched_content?: string;
}

// Legacy aliases for backwards compatibility during migration
export type Conversation = Chat;
export type ConversationDetail = ChatDetail;
export type ConversationList = ChatList;
export type ConversationSearchResult = ChatSearchResult;

export interface UploadResponse {
  id: string;
  filename: string;
  project_id: string;
  pages: number;
  chunks: number;
  file_size?: number;
}

// Streaming types
export type PipelineStage =
  | 'detecting'
  | 'analyzing'
  | 'searching'
  | 'validating'
  | 'generating'
  | 'complete';

export interface StreamStatus {
  stage: PipelineStage;
  message: string;
  details?: Record<string, unknown>;
}

export interface StreamState {
  status: StreamStatus | null;
  partialAnswer: string;
  citations: Citation[] | null;
  reasoning: Reasoning | null;
  optionsValidation: OptionValidation[] | null;
  isStreaming: boolean;
  error: string | null;
}
