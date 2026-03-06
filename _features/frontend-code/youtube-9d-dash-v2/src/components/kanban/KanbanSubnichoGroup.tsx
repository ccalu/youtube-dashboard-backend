/**
 * Expandable subniche group within Monetizados/Não Monetizados sections
 */

import { useState } from 'react';
import { ChevronRight, ChevronDown } from 'lucide-react';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { getSubnichoEmoji } from '@/utils/subnichoEmojis';
import { KanbanChannelCard } from './KanbanChannelCard';
import type { KanbanSubnicho, KanbanChannel } from '@/types/kanban';

interface KanbanSubnichoGroupProps {
  subnicho: string;
  data: KanbanSubnicho;
  onChannelClick: (canal: KanbanChannel) => void;
  defaultExpanded?: boolean;
  isMonetized?: boolean;
}

export const KanbanSubnichoGroup = ({
  subnicho,
  data,
  onChannelClick,
  defaultExpanded = false,
  isMonetized,
}: KanbanSubnichoGroupProps) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const cores = obterCorSubnicho(subnicho);
  const emoji = getSubnichoEmoji(subnicho);

  return (
    <div className="space-y-2">
      {/* Subniche Header */}
      <div
        className="p-3 rounded-lg cursor-pointer transition-all duration-200 hover:scale-[1.01]"
        style={{
          backgroundColor: cores.fundo + '40',
          borderLeft: `3px solid ${cores.borda}`,
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-white/70" />
            ) : (
              <ChevronRight className="h-4 w-4 text-white/70" />
            )}
            <span className="text-lg">{emoji}</span>
            <span className="font-medium text-white">{subnicho}</span>
            <span className="text-sm text-white/60">({data.total} canais)</span>
          </div>
        </div>
      </div>

      {/* Channels List */}
      {isExpanded && data.canais && data.canais.length > 0 && (
        <div className="ml-4 space-y-2 animate-fade-in">
          {data.canais.map((canal) => (
            <KanbanChannelCard
              key={canal.id}
              canal={canal}
              isMonetized={isMonetized}
              onClick={() => onChannelClick(canal)}
            />
          ))}
        </div>
      )}
    </div>
  );
};
