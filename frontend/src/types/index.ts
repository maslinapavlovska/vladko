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
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  reasoning: Reasoning;
}

export interface UploadResponse {
  filename: string;
  pages: number;
  chunks: number;
}
