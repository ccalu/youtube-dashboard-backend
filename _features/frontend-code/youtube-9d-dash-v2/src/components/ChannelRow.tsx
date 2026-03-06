import React from 'react';
import { Channel } from '@/services/api';
import { TableRow, TableCell } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ColoredBadge } from '@/components/ui/colored-badge';
import { Star, ExternalLink, Edit, Trash2, BarChart3 } from 'lucide-react';
import { formatNumber } from '@/utils/formatters';
import { obterCorSubnicho, obterGradienteTranslucido } from '@/utils/subnichoColors';

interface ChannelRowProps {
  channel: Channel;
  isFavorited: boolean;
  isAnimating: boolean;
  onToggleFavorite: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onAnalytics: () => void;
  isUpdating: boolean;
}

export const ChannelRow = React.memo(({ 
  channel, 
  isFavorited, 
  isAnimating,
  onToggleFavorite, 
  onEdit, 
  onDelete,
  onAnalytics,
  isUpdating 
}: ChannelRowProps) => {
  const cores = obterCorSubnicho(channel.subnicho);
  const gradiente = obterGradienteTranslucido(channel.subnicho);
  
  return (
    <TableRow 
      className="border-table-border hover:bg-table-hover transition-colors"
      style={{ 
        background: gradiente,
        borderLeft: `4px solid ${cores.borda}`
      }}
    >
      <TableCell>
        <Button
          variant="ghost"
          size="sm"
          className="p-1 h-auto"
          onClick={onToggleFavorite}
          disabled={isUpdating}
        >
          <Star 
            className={`h-3.5 w-3.5 ${isAnimating ? 'animate-favorite' : ''} ${
              isFavorited 
                ? 'fill-yellow-500 text-yellow-500' 
                : 'text-yellow-500'
            }`} 
          />
        </Button>
      </TableCell>
      <TableCell className="font-medium text-foreground">{channel.nome_canal}</TableCell>
      <TableCell>
        <ColoredBadge text={channel.subnicho} type="subnicho" />
      </TableCell>
      <TableCell>
        <ColoredBadge text={channel.lingua} type="language" />
      </TableCell>
      <TableCell className="text-right text-foreground">{formatNumber(channel.inscritos)}</TableCell>
      <TableCell className="text-right text-foreground">{formatNumber(channel.views_7d)}</TableCell>
      <TableCell className="text-right text-foreground">{formatNumber(channel.views_30d)}</TableCell>
      <TableCell className="text-center">
        <div className="flex items-center justify-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="p-1 h-auto"
            onClick={onAnalytics}
            disabled={isUpdating}
            title="Analisar canal"
          >
            <BarChart3 className="h-4 w-4 text-blue-500" />
          </Button>
          {channel.url_canal && (
            <Button
              asChild
              variant="ghost"
              size="sm"
              className="p-1 h-auto"
            >
              <a
                href={channel.url_canal}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`Abrir canal no YouTube: ${channel.nome_canal}`}
              >
                <ExternalLink className="h-4 w-4 text-primary" />
              </a>
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="p-1 h-auto"
            onClick={onEdit}
            disabled={isUpdating}
          >
            <Edit className="h-4 w-4 text-primary" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="p-1 h-auto"
            onClick={onDelete}
            disabled={isUpdating}
          >
            <Trash2 className="h-4 w-4 text-red-500" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  );
});

ChannelRow.displayName = 'ChannelRow';
