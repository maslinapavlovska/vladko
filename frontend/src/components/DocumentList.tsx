import { FileText, Trash2, Loader2 } from 'lucide-react';

interface DocumentListProps {
  documents: string[];
  onDelete: (filename: string) => Promise<void>;
  isLoading: boolean;
}

export function DocumentList({ documents, onDelete, isLoading }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 text-sm">
        No documents uploaded yet
      </div>
    );
  }

  return (
    <div className="p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Documents ({documents.length})</h3>
      <ul className="space-y-2">
        {documents.map((doc) => (
          <li
            key={doc}
            className="flex items-center justify-between p-2 bg-gray-50 rounded-lg group"
          >
            <div className="flex items-center gap-2 min-w-0">
              <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <span className="text-sm text-gray-700 truncate" title={doc}>
                {doc}
              </span>
            </div>
            <button
              onClick={() => onDelete(doc)}
              disabled={isLoading}
              className="p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-50"
              title="Delete document"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
