/**
 * Individual channel card within a subniche group
 */

import { getLanguageFlag } from '@/utils/languageFlags';
import type { KanbanChannel } from '@/types/kanban';

interface KanbanChannelCardProps {
  canal: KanbanChannel;
  isMonetized?: boolean;
  onClick: () => void;
}

const getStatusColorClasses = (color: string) => {
  const colors: Record<string, string> = {
    yellow: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    green: 'bg-green-500/20 text-green-300 border-green-500/30',
    orange: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    blue: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    gray: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
  };
  return colors[color] || colors.gray;
};

export const KanbanChannelCard = ({ canal, isMonetized, onClick }: KanbanChannelCardProps) => {
  const flag = getLanguageFlag(canal.lingua);
  const isDemonstrandoTracao = canal.status_label?.toLowerCase().includes('demonstrando');
  const effectiveStatusColor = !isMonetized && isDemonstrandoTracao ? 'green' : canal.status_color;

  return (
    <div
      className="p-3 bg-card/50 rounded-lg border border-border/50 cursor-pointer hover:bg-card/80 hover:border-border transition-all duration-200 flex items-center justify-between group"
      onClick={onClick}
    >
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-lg shrink-0">{flag}</span>
        <span className="font-medium text-sm text-foreground truncate">
          {canal.nome}
        </span>
      </div>
      <span
        className={`px-2 py-1 rounded text-[10px] font-medium border shrink-0 ml-2 ${getStatusColorClasses(
          effectiveStatusColor
        )}`}
      >
        {canal.status_emoji} {canal.status_label} há {canal.dias_no_status}d
      </span>
    </div>
  );
};
