import { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LastUpdateIndicatorProps {
  lastUpdate?: Date | null;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  className?: string;
}

export function LastUpdateIndicator({
  lastUpdate,
  onRefresh,
  isRefreshing = false,
  className,
}: LastUpdateIndicatorProps) {
  const [timeAgo, setTimeAgo] = useState('');

  useEffect(() => {
    const updateTimeAgo = () => {
      if (!lastUpdate) {
        setTimeAgo('');
        return;
      }

      const now = new Date();
      const diff = Math.floor((now.getTime() - lastUpdate.getTime()) / 1000);

      if (diff < 60) {
        setTimeAgo('agora');
      } else if (diff < 3600) {
        const minutes = Math.floor(diff / 60);
        setTimeAgo(`há ${minutes}min`);
      } else if (diff < 86400) {
        const hours = Math.floor(diff / 3600);
        setTimeAgo(`há ${hours}h`);
      } else {
        const days = Math.floor(diff / 86400);
        setTimeAgo(`há ${days}d`);
      }
    };

    updateTimeAgo();
    const interval = setInterval(updateTimeAgo, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [lastUpdate]);

  if (!lastUpdate && !onRefresh) return null;

  return (
    <div
      className={cn(
        "flex items-center gap-1.5 text-xs text-muted-foreground",
        onRefresh && "cursor-pointer hover:text-foreground transition-colors",
        className
      )}
      onClick={onRefresh}
      title={onRefresh ? "Clique para atualizar" : undefined}
    >
      <RefreshCw 
        className={cn(
          "h-3 w-3",
          isRefreshing && "animate-spin"
        )} 
      />
      {timeAgo && (
        <span className="hidden sm:inline">Atualizado {timeAgo}</span>
      )}
      {isRefreshing && (
        <span className="text-primary">Atualizando...</span>
      )}
    </div>
  );
}
