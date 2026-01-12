import { useState } from 'react';
import {
  MessageSquare,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import type { Conversation, ConversationDetail } from '../types';

interface ConversationListProps {
  conversations: Conversation[];
  activeConversation: ConversationDetail | null;
  isLoading: boolean;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onNewChat: () => void;
}

export function ConversationList({
  conversations,
  activeConversation,
  isLoading,
  onSelect,
  onCreate,
  onDelete,
  onRename,
  onNewChat,
}: ConversationListProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const startEditing = (conv: Conversation) => {
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const saveEdit = () => {
    if (editingId && editTitle.trim()) {
      onRename(editingId, editTitle.trim());
    }
    setEditingId(null);
    setEditTitle('');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditTitle('');
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  // Group conversations by date
  const groupedConversations = conversations.reduce((groups, conv) => {
    const dateLabel = formatDate(conv.updated_at);
    if (!groups[dateLabel]) {
      groups[dateLabel] = [];
    }
    groups[dateLabel].push(conv);
    return groups;
  }, {} as Record<string, Conversation[]>);

  if (isCollapsed) {
    return (
      <div className="w-10 bg-gray-50 border-r border-gray-200 flex flex-col items-center py-2">
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded"
          title="Expand conversations"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
        <button
          onClick={onNewChat}
          className="mt-2 p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded"
          title="New chat"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-gray-200 flex items-center justify-between">
        <h2 className="font-semibold text-gray-800 text-sm">Conversations</h2>
        <button
          onClick={() => setIsCollapsed(true)}
          className="p-1 text-gray-400 hover:text-gray-600 rounded"
          title="Collapse"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-2">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && conversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            Loading...
          </div>
        ) : conversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            No conversations yet.
            <br />
            Start a new chat!
          </div>
        ) : (
          Object.entries(groupedConversations).map(([dateLabel, convs]) => (
            <div key={dateLabel}>
              <div className="px-3 py-1 text-xs font-medium text-gray-500 uppercase">
                {dateLabel}
              </div>
              {convs.map(conv => (
                <div
                  key={conv.id}
                  className={`group mx-2 mb-1 rounded-lg transition-colors ${
                    activeConversation?.id === conv.id
                      ? 'bg-blue-100 border border-blue-200'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  {editingId === conv.id ? (
                    <div className="flex items-center gap-1 p-2">
                      <input
                        type="text"
                        value={editTitle}
                        onChange={e => setEditTitle(e.target.value)}
                        onKeyDown={e => {
                          if (e.key === 'Enter') saveEdit();
                          if (e.key === 'Escape') cancelEdit();
                        }}
                        className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        autoFocus
                      />
                      <button
                        onClick={saveEdit}
                        className="p-1 text-green-600 hover:bg-green-50 rounded"
                      >
                        <Check className="w-3 h-3" />
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="p-1 text-red-600 hover:bg-red-50 rounded"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ) : (
                    <div
                      className="flex items-center gap-2 p-2 cursor-pointer"
                      onClick={() => onSelect(conv.id)}
                    >
                      <MessageSquare className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-800 truncate">
                          {conv.title}
                        </div>
                        {conv.preview && (
                          <div className="text-xs text-gray-500 truncate">
                            {conv.preview}
                          </div>
                        )}
                      </div>
                      <div className="hidden group-hover:flex items-center gap-1">
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            startEditing(conv);
                          }}
                          className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded"
                          title="Rename"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            if (confirm('Delete this conversation?')) {
                              onDelete(conv.id);
                            }
                          }}
                          className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                          title="Delete"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
