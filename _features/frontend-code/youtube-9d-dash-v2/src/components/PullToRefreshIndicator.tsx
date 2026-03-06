import { RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PullToRefreshIndicatorProps {
  pullDistance: number;
  isRefreshing: boolean;
  shouldTrigger: boolean;
  threshold?: number;
}

export function PullToRefreshIndicator({
  pullDistance,
  isRefreshing,
  shouldTrigger,
  threshold = 80,
}: PullToRefreshIndicatorProps) {
  if (pullDistance === 0 && !isRefreshing) return null;

  const progress = Math.min(pullDistance / threshold, 1);
  const rotation = progress * 180;

  return (
    <div
      className="fixed top-0 left-0 right-0 flex justify-center pointer-events-none z-50"
      style={{
        transform: `translateY(${Math.min(pullDistance, threshold * 1.2)}px)`,
        opacity: Math.min(progress * 2, 1),
      }}
    >
      <div
        className={cn(
          "flex items-center justify-center w-10 h-10 rounded-full bg-card border border-border shadow-lg transition-colors",
          shouldTrigger && "bg-primary border-primary"
        )}
      >
        <RefreshCw
          className={cn(
            "h-5 w-5 transition-colors",
            shouldTrigger ? "text-primary-foreground" : "text-muted-foreground",
            isRefreshing && "animate-spin"
          )}
          style={{
            transform: isRefreshing ? undefined : `rotate(${rotation}deg)`,
          }}
        />
      </div>
    </div>
  );
}
