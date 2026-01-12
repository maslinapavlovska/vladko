import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, MessageSquare, Bot } from 'lucide-react';
import { Message } from './Message';
import { StreamingStatus, StreamingMessage } from './StreamingStatus';
import type { Message as MessageType, StreamStatus, Citation, OptionValidation } from '../types';

interface ChatAreaProps {
  messages: MessageType[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  hasDocuments: boolean;
  // Streaming props
  isStreaming?: boolean;
  streamStatus?: StreamStatus | null;
  partialAnswer?: string;
  streamCitations?: Citation[] | null;
  optionsValidation?: OptionValidation[] | null;
}

export function ChatArea({
  messages,
  isLoading,
  onSendMessage,
  hasDocuments,
  isStreaming = false,
  streamStatus = null,
  partialAnswer = '',
  streamCitations = null,
  optionsValidation = null,
}: ChatAreaProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, partialAnswer]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading && !isStreaming) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const isBusy = isLoading || isStreaming;

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 && !isStreaming ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400">
            <MessageSquare className="w-16 h-16 mb-4" />
            <p className="text-lg font-medium">No messages yet</p>
            <p className="text-sm mt-1">
              {hasDocuments
                ? 'Ask a question about your documents'
                : 'Upload a PDF to get started'}
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((message) => (
              <Message key={message.id} message={message} />
            ))}

            {/* Streaming status (before answer starts) */}
            {isStreaming && streamStatus && streamStatus.stage !== 'generating' && !partialAnswer && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <StreamingStatus status={streamStatus} optionsValidation={optionsValidation} />
                </div>
              </div>
            )}

            {/* Streaming response */}
            {isStreaming && partialAnswer && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1 bg-gray-50 rounded-lg p-4">
                  {streamStatus && streamStatus.stage === 'generating' && (
                    <div className="mb-2 text-xs text-green-600 flex items-center gap-1">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Generating answer...
                    </div>
                  )}
                  <StreamingMessage content={partialAnswer} isStreaming={isStreaming} />
                  {streamCitations && streamCitations.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs text-gray-500 mb-1">Sources:</p>
                      <div className="flex flex-wrap gap-1">
                        {streamCitations.slice(0, 3).map((c, i) => (
                          <span key={i} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                            {c.filename} p.{c.page}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Legacy loading indicator (non-streaming) */}
            {isLoading && !isStreaming && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                  <Loader2 className="w-5 h-5 text-gray-600 animate-spin" />
                </div>
                <div className="bg-gray-100 rounded-lg p-3">
                  <p className="text-gray-600">Thinking...</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              hasDocuments
                ? 'Ask a question about your documents...'
                : 'Upload a document first to ask questions'
            }
            disabled={isBusy || !hasDocuments}
            rows={1}
            className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
          />
          <button
            type="submit"
            disabled={isBusy || !input.trim() || !hasDocuments}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isBusy ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
