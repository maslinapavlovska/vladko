import { useState, useEffect } from 'react';
import type { HealthStatus } from '../types';
import { checkHealth } from '../services/api';

export function useHealth() {
  const [health, setHealth] = useState<HealthStatus>({
    api: 'checking',
    ollama: 'checking',
  });

  useEffect(() => {
    const check = async () => {
      const status = await checkHealth();
      setHealth(status);
    };

    check();
    const interval = setInterval(check, 30000); // Poll every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return health;
}
