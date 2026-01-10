import { RotateCcw } from 'lucide-react';
import { FileUpload } from './FileUpload';
import { DocumentList } from './DocumentList';

interface SidebarProps {
  documents: string[];
  isLoading: boolean;
  onUpload: (file: File) => Promise<void>;
  onDelete: (filename: string) => Promise<void>;
  onReset: () => Promise<void>;
}

export function Sidebar({ documents, isLoading, onUpload, onDelete, onReset }: SidebarProps) {
  const handleReset = async () => {
    if (window.confirm('Are you sure you want to delete all documents? This cannot be undone.')) {
      await onReset();
    }
  };

  return (
    <aside className="w-72 bg-white border-r border-gray-200 flex flex-col">
      <FileUpload onUpload={onUpload} isLoading={isLoading} />

      <div className="flex-1 overflow-y-auto border-t border-gray-200">
        <DocumentList
          documents={documents}
          onDelete={onDelete}
          isLoading={isLoading}
        />
      </div>

      {documents.length > 0 && (
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={handleReset}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
          >
            <RotateCcw className="w-4 h-4" />
            Reset All
          </button>
        </div>
      )}
    </aside>
  );
}
