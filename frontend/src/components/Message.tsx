import { User, Bot, AlertCircle } from 'lucide-react';
import { Citation } from './Citation';
import { ThoughtProcess } from './ThoughtProcess';
import type { Message as MessageType } from '../types';

interface MessageProps {
  message: MessageType;
}

export function Message({ message }: MessageProps) {
  const isUser = message.role === 'user';
  const isError = message.role === 'error';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
          ${isUser ? 'bg-blue-100' : isError ? 'bg-red-100' : 'bg-gray-100'}`}
      >
        {isUser ? (
          <User className="w-5 h-5 text-blue-600" />
        ) : isError ? (
          <AlertCircle className="w-5 h-5 text-red-600" />
        ) : (
          <Bot className="w-5 h-5 text-gray-600" />
        )}
      </div>

      <div className={`flex-1 max-w-[80%] ${isUser ? 'text-right' : ''}`}>
        <div
          className={`inline-block p-3 rounded-lg ${
            isUser
              ? 'bg-blue-600 text-white'
              : isError
              ? 'bg-red-50 text-red-800 border border-red-200'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Thought Process (before citations) */}
        {message.reasoning && <ThoughtProcess reasoning={message.reasoning} />}

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <Citation citations={message.citations} />
        )}
      </div>
    </div>
  );
}
