import { Loader2, Search, FileSearch, CheckCircle, Brain, Sparkles } from 'lucide-react';
import type { StreamStatus, OptionValidation } from '../types';

interface StreamingStatusProps {
  status: StreamStatus;
  optionsValidation?: OptionValidation[] | null;
}

const stageConfig: Record<string, { icon: React.ElementType; color: string; bgColor: string }> = {
  detecting: { icon: Brain, color: 'text-purple-600', bgColor: 'bg-purple-50' },
  analyzing: { icon: Brain, color: 'text-purple-600', bgColor: 'bg-purple-50' },
  searching: { icon: Search, color: 'text-blue-600', bgColor: 'bg-blue-50' },
  validating: { icon: FileSearch, color: 'text-amber-600', bgColor: 'bg-amber-50' },
  generating: { icon: Sparkles, color: 'text-green-600', bgColor: 'bg-green-50' },
  complete: { icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-50' },
};

export function StreamingStatus({ status, optionsValidation }: StreamingStatusProps) {
  const config = stageConfig[status.stage] || stageConfig.detecting;
  const Icon = config.icon;

  return (
    <div className={`flex flex-col gap-2 p-3 rounded-lg border border-gray-200 ${config.bgColor}`}>
      <div className="flex items-center gap-3">
        <div className={config.color}>
          {status.stage === 'complete' ? (
            <Icon className="w-5 h-5" />
          ) : (
            <Loader2 className="w-5 h-5 animate-spin" />
          )}
        </div>

        <div className="flex-1">
          <p className="text-sm font-medium text-gray-700">{status.message}</p>

          {status.details?.terms && (
            <div className="flex flex-wrap gap-1 mt-1">
              {(status.details.terms as string[]).slice(0, 5).map((term, i) => (
                <span
                  key={i}
                  className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded"
                >
                  {term}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Options validation display */}
      {optionsValidation && optionsValidation.length > 0 && status.stage === 'validating' && (
        <div className="mt-2 pt-2 border-t border-gray-200">
          <p className="text-xs font-medium text-gray-500 mb-1">Document Search Results:</p>
          <div className="grid grid-cols-2 gap-1">
            {optionsValidation.map((opt, i) => (
              <div
                key={i}
                className={`flex items-center gap-1 text-xs px-2 py-1 rounded ${
                  opt.found_in_documents
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {opt.found_in_documents ? (
                  <CheckCircle className="w-3 h-3" />
                ) : (
                  <span className="w-3 h-3 text-center">-</span>
                )}
                <span className="truncate">{opt.option}</span>
                {opt.found_in_documents && (
                  <span className="text-green-600">({opt.evidence_count})</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface StreamingMessageProps {
  content: string;
  isStreaming: boolean;
}

export function StreamingMessage({ content, isStreaming }: StreamingMessageProps) {
  return (
    <div className="prose prose-sm max-w-none">
      <p className="whitespace-pre-wrap">
        {content}
        {isStreaming && (
          <span className="inline-block w-2 h-4 ml-0.5 bg-gray-400 animate-pulse" />
        )}
      </p>
    </div>
  );
}
