import { FileText, Server, Cpu } from 'lucide-react';
import type { HealthStatus } from '../types';

interface HeaderProps {
  health: HealthStatus;
}

function StatusBadge({
  label,
  status,
  icon: Icon,
}: {
  label: string;
  status: 'ok' | 'error' | 'unreachable' | 'checking';
  icon: React.ElementType;
}) {
  const colors = {
    ok: 'bg-green-100 text-green-800',
    error: 'bg-red-100 text-red-800',
    unreachable: 'bg-red-100 text-red-800',
    checking: 'bg-yellow-100 text-yellow-800',
  };

  const statusText = {
    ok: 'Connected',
    error: 'Disconnected',
    unreachable: 'Unreachable',
    checking: 'Checking...',
  };

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${colors[status]}`}>
      <Icon className="w-4 h-4" />
      <span>{label}:</span>
      <span>{statusText[status]}</span>
    </div>
  );
}

export function Header({ health }: HeaderProps) {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-8 h-8 text-blue-600" />
          <h1 className="text-xl font-semibold text-gray-900">RAG Document Q&A</h1>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge label="API" status={health.api} icon={Server} />
          <StatusBadge label="Ollama" status={health.ollama} icon={Cpu} />
        </div>
      </div>
    </header>
  );
}
