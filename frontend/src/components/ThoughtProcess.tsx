import { useState } from 'react';
import { 
  ChevronDown, 
  ChevronRight, 
  Search, 
  Zap, 
  Brain, 
  ListChecks, 
  FileSearch, 
  MessageSquare,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Globe
} from 'lucide-react';
import type { Reasoning } from '../types';

interface ThoughtProcessProps {
  reasoning: Reasoning;
}

export function ThoughtProcess({ reasoning }: ThoughtProcessProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showPrompt, setShowPrompt] = useState(false);
  const [showGrepDetails, setShowGrepDetails] = useState(false);

  const isTwoStageMCQ = reasoning.stage1_analysis || reasoning.stage2_grep_results;
  const hasValidation = reasoning.options_validation && reasoning.options_validation.length > 0;
  const hasJustification = reasoning.justification;

  return (
    <div className="w-full mt-2">
      {/* Toggle button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700"
      >
        <Brain className="w-4 h-4" />
        <span>Thought process</span>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-2 bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm space-y-3">

          {/* MCQ Detection Banner */}
          {reasoning.is_mcq && (
            <div className="bg-amber-100 border border-amber-300 rounded p-2">
              <div className="flex items-center gap-1 font-medium text-amber-800 mb-1">
                <ListChecks className="w-4 h-4" />
                Multiple Choice Question Detected
              </div>
              <div className="text-xs text-amber-700">
                Options: {reasoning.mcq_options?.join(' | ')}
              </div>
            </div>
          )}

          {/* NEW: Options Validation Display */}
          {hasValidation && (
            <div className="bg-white border border-gray-200 rounded p-2">
              <div className="flex items-center gap-1 font-medium text-gray-800 mb-2">
                <Search className="w-4 h-4" />
                Document Search Results (Deterministic)
              </div>
              <div className="space-y-1">
                {reasoning.options_validation!.map((opt, i) => (
                  <div 
                    key={i} 
                    className={`flex items-center gap-2 p-1.5 rounded text-xs ${
                      opt.found_in_documents 
                        ? 'bg-green-50 border border-green-200' 
                        : 'bg-gray-50 border border-gray-200'
                    }`}
                  >
                    {opt.found_in_documents ? (
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    )}
                    <span className={opt.found_in_documents ? 'font-medium text-green-800' : 'text-gray-500'}>
                      {opt.option}
                    </span>
                    {opt.found_in_documents && (
                      <span className="text-green-600 ml-auto">
                        {opt.evidence_count} match{opt.evidence_count !== 1 ? 'es' : ''} 
                        {opt.sources.length > 0 && ` (${opt.sources[0]})`}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* NEW: Answer Justification Display */}
          {hasJustification && (
            <div className={`border rounded p-2 ${
              reasoning.justification!.validated 
                ? 'bg-green-50 border-green-300' 
                : 'bg-yellow-50 border-yellow-300'
            }`}>
              <div className="flex items-center gap-1 font-medium mb-2">
                {reasoning.justification!.validated ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <span className="text-green-800">Answer Verified</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-4 h-4 text-yellow-600" />
                    <span className="text-yellow-800">Validation Warning</span>
                  </>
                )}
                <span className={`ml-auto px-2 py-0.5 rounded text-xs ${
                  reasoning.justification!.confidence === 'HIGH' 
                    ? 'bg-green-200 text-green-800'
                    : reasoning.justification!.confidence === 'LOW'
                    ? 'bg-yellow-200 text-yellow-800'
                    : 'bg-gray-200 text-gray-800'
                }`}>
                  {reasoning.justification!.confidence} confidence
                </span>
              </div>
              
              {reasoning.justification!.evidence_quote && (
                <div className="text-xs mb-1">
                  <span className="font-medium">Evidence: </span>
                  <span className="italic">"{reasoning.justification!.evidence_quote}"</span>
                </div>
              )}
              
              {reasoning.justification!.source && (
                <div className="text-xs mb-1">
                  <span className="font-medium">Source: </span>
                  {reasoning.justification!.source}
                </div>
              )}
              
              {reasoning.justification!.validation_note && (
                <div className={`text-xs mt-1 p-1 rounded ${
                  reasoning.justification!.validated 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {reasoning.justification!.validation_note}
                </div>
              )}
            </div>
          )}

          {/* Web Search Indicator */}
          {reasoning.used_web_search && (
            <div className="bg-blue-50 border border-blue-200 rounded p-2">
              <div className="flex items-center gap-1 text-blue-800">
                <Globe className="w-4 h-4" />
                <span className="font-medium">Web Search Used</span>
              </div>
              <div className="text-xs text-blue-600 mt-1">
                Answer not found in documents - web search fallback activated
              </div>
            </div>
          )}

          {/* ===== TWO-STAGE MCQ DISPLAY ===== */}
          {isTwoStageMCQ && (
            <>
              {/* Stage 1: LLM Query Analysis */}
              {reasoning.stage1_analysis && (
                <div className="bg-blue-50 border border-blue-200 rounded p-2">
                  <div className="flex items-center gap-1 font-medium text-blue-800 mb-1">
                    <MessageSquare className="w-4 h-4" />
                    Stage 1: Search Terms Generated
                  </div>
                  <div className="text-xs text-blue-700 mb-2">
                    {reasoning.stage1_analysis.reasoning}
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {reasoning.stage1_analysis.search_terms.map((term, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-blue-200 text-blue-800 rounded text-xs"
                      >
                        {term}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Stage 2: Grep Results */}
              {reasoning.stage2_grep_results && reasoning.stage2_grep_results.length > 0 && (
                <div className="bg-green-50 border border-green-200 rounded p-2">
                  <div className="flex items-center gap-1 font-medium text-green-800 mb-1">
                    <FileSearch className="w-4 h-4" />
                    Stage 2: Document Matches ({reasoning.stage2_grep_results.length})
                  </div>

                  <div className="text-xs text-green-700 mb-2">
                    {Array.from(new Set(reasoning.stage2_grep_results.map(r => r.term))).map((term, i) => {
                      const count = reasoning.stage2_grep_results!.filter(r => r.term === term).length;
                      return (
                        <span key={i} className="mr-2">
                          "{term}": {count} match{count !== 1 ? 'es' : ''}
                        </span>
                      );
                    })}
                  </div>

                  <button
                    onClick={() => setShowGrepDetails(!showGrepDetails)}
                    className="text-xs text-green-600 hover:text-green-700 underline"
                  >
                    {showGrepDetails ? 'Hide' : 'Show'} grep details
                  </button>

                  {showGrepDetails && (
                    <div className="mt-2 space-y-2 max-h-64 overflow-y-auto">
                      {reasoning.stage2_grep_results.map((result, i) => (
                        <div key={i} className="p-2 bg-white rounded border text-xs">
                          <div className="font-medium text-gray-700 mb-1">
                            <span className="text-green-600">"{result.term}"</span>
                            {' → '}
                            <span>{result.filename}</span>
                            {' p.'}
                            <span className="text-blue-600">{result.page}</span>
                          </div>
                          <pre className="text-gray-600 whitespace-pre-wrap text-xs bg-gray-50 p-1 rounded">
                            {result.full_excerpt}
                          </pre>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {reasoning.stage2_grep_results && reasoning.stage2_grep_results.length === 0 && (
                <div className="bg-red-50 border border-red-200 rounded p-2">
                  <div className="text-xs text-red-700">
                    No matches found in documents for the search terms.
                  </div>
                </div>
              )}
            </>
          )}

          {/* ===== STANDARD HYBRID SEARCH DISPLAY ===== */}
          {!isTwoStageMCQ && (
            <>
              {reasoning.keywords_extracted && reasoning.keywords_extracted.length > 0 && (
                <div>
                  <div className="flex items-center gap-1 font-medium text-purple-800 mb-1">
                    <Search className="w-4 h-4" />
                    Keywords extracted
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {reasoning.keywords_extracted.map((kw, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-purple-200 text-purple-800 rounded text-xs"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {reasoning.retrieval_summary && reasoning.retrieval_summary.length > 0 && (
                <div>
                  <div className="flex items-center gap-1 font-medium text-purple-800 mb-1">
                    <Zap className="w-4 h-4" />
                    Retrieved {reasoning.chunks_retrieved || 0} chunks
                  </div>
                  <div className="space-y-1">
                    {reasoning.retrieval_summary.map((chunk, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs flex-wrap">
                        <span
                          className={`px-1.5 py-0.5 rounded ${
                            chunk.match_type === 'both'
                              ? 'bg-green-200 text-green-800'
                              : chunk.match_type === 'keyword'
                              ? 'bg-yellow-200 text-yellow-800'
                              : 'bg-blue-200 text-blue-800'
                          }`}
                        >
                          {chunk.match_type}
                        </span>
                        <span className="text-gray-700">{chunk.source}</span>
                        {chunk.keywords_found?.length > 0 && (
                          <span className="text-gray-500">
                            matched: {chunk.keywords_found.join(', ')}
                          </span>
                        )}
                        <span className="text-gray-400 ml-auto">
                          score: {chunk.scores?.combined?.toFixed(2) || 'N/A'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Full Prompt (always available) */}
          <div>
            <button
              onClick={() => setShowPrompt(!showPrompt)}
              className="text-xs text-purple-600 hover:text-purple-700 underline"
            >
              {showPrompt ? 'Hide' : 'Show'} full prompt sent to LLM
            </button>
            {showPrompt && (
              <pre className="mt-2 p-2 bg-white border rounded text-xs overflow-x-auto whitespace-pre-wrap text-gray-700 max-h-64 overflow-y-auto">
                {reasoning.prompt_sent || '(No prompt available)'}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
