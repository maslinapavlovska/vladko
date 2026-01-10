import { useState } from 'react';
import { ChevronDown, ChevronRight, FileText } from 'lucide-react';
import type { Citation as CitationType } from '../types';

interface CitationProps {
  citations: CitationType[];
}

export function Citation({ citations }: CitationProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (citations.length === 0) {
    return null;
  }

  const getMatchTypeBadgeClass = (matchType: string) => {
    switch (matchType) {
      case 'both':
        return 'bg-green-100 text-green-700';
      case 'keyword':
        return 'bg-yellow-100 text-yellow-700';
      case 'grep':
        return 'bg-emerald-100 text-emerald-700';
      default:
        return 'bg-blue-100 text-blue-700';
    }
  };

  return (
    <div className="mt-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
        <span>{citations.length} source{citations.length !== 1 ? 's' : ''}</span>
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2">
          {citations.map((citation, index) => (
            <div
              key={index}
              className="p-3 bg-gray-50 rounded-lg border border-gray-200"
            >
              {/* Header row */}
              <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1">
                <FileText className="w-4 h-4" />
                <span>{citation.filename}</span>
                <span className="text-gray-400">•</span>
                <span className="text-blue-600">Page {citation.page}</span>

                {/* Match type badge */}
                {citation.match_type && (
                  <span
                    className={`ml-auto px-1.5 py-0.5 rounded text-xs ${getMatchTypeBadgeClass(
                      citation.match_type
                    )}`}
                  >
                    {citation.match_type}
                  </span>
                )}
              </div>

              {/* Keywords found */}
              {citation.keyword_matches?.length > 0 && (
                <div className="text-xs text-gray-500 mb-1">
                  Keywords found: {citation.keyword_matches.join(', ')}
                </div>
              )}

              {/* Excerpt */}
              <p className="text-sm text-gray-600 bg-white p-2 rounded border text-xs leading-relaxed">
                {citation.excerpt}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
