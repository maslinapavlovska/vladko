export interface HealthStatus {
  api: 'ok' | 'error' | 'checking';
  ollama: 'ok' | 'unreachable' | 'checking';
}

export interface Scores {
  combined?: number;
  keyword?: number;
  semantic?: number;
  grep_match?: number;
}

export interface Citation {
  filename: string;
  page: number;
  excerpt: string;
  match_type: 'keyword' | 'semantic' | 'both' | 'grep';
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
