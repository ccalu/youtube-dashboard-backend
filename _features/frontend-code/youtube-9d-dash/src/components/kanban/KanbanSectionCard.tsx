/**
 * Main section card (Monetizados / Não Monetizados)
 */

import { useState } from 'react';
import { ChevronRight, ChevronDown } from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { KanbanSubnichoGroup } from './KanbanSubnichoGroup';
import type { KanbanSection, KanbanChannel } from '@/types/kanban';

const normalizeString = (str: string) =>
  str
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

// Mantém a ordem coerente com a aba Tabela
const SUBNICHE_ORDER = [
  'monetizados',
  'reis perversos',
  'historias sombrias',
  'culturas macabras',
  'relatos de guerra',
  'frentes de guerra',
  'guerras e civilizacoes',
  'licoes de vida',
  'registros malditos',
];

const LAST_SUBNICHE = ['desmonetizado', 'desmonetizados'];
const EXCLUDED_SUBNICHES = ['historias aleatorias', 'contos familiares'];

interface KanbanSectionCardProps {
  title: string;
  emoji: string;
  section: KanbanSection;
  onChannelClick: (canal: KanbanChannel) => void;
  accentColor: string;
  defaultExpanded?: boolean;
  isMonetized?: boolean;
  gradientFrom?: string;
  gradientTo?: string;
}

export const KanbanSectionCard = ({
  title,
  emoji,
  section,
  onChannelClick,
  accentColor,
  defaultExpanded = false,
  isMonetized,
  gradientFrom,
  gradientTo,
}: KanbanSectionCardProps) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const sortedSubnichos = Object.entries(section.subnichos ?? {})
    .filter(([subnicho]) => !EXCLUDED_SUBNICHES.includes(normalizeString(subnicho)))
    // Não Monetizados: excluir subnicho "Monetizados"
    .filter(([subnicho]) => !(isMonetized === false && normalizeString(subnicho) === 'monetizados'))
    // Monetizados: excluir subnicho "Desmonetizados"
    .filter(([subnicho]) => {
      const normalized = normalizeString(subnicho);
      return !(isMonetized === true && (normalized === 'desmonetizado' || normalized === 'desmonetizados'));
    })
    .sort(([a], [b]) => {
      const na = normalizeString(a);
      const nb = normalizeString(b);

      const aIsLast = LAST_SUBNICHE.includes(na);
      const bIsLast = LAST_SUBNICHE.includes(nb);
      if (aIsLast && !bIsLast) return 1;
      if (!aIsLast && bIsLast) return -1;
      if (aIsLast && bIsLast) return 0;

      const ia = SUBNICHE_ORDER.findIndex((s) => normalizeString(s) === na);
      const ib = SUBNICHE_ORDER.findIndex((s) => normalizeString(s) === nb);

      if (ia === -1 && ib === -1) return 0;
      if (ia === -1) return 1;
      if (ib === -1) return -1;
      return ia - ib;
    });

  // Build gradient or fallback style
  const headerStyle = gradientFrom && gradientTo
    ? {
        background: `linear-gradient(135deg, ${gradientFrom}30 0%, ${gradientTo}40 100%)`,
        borderLeft: `4px solid ${accentColor}`,
      }
    : { backgroundColor: accentColor + '25' };

  return (
    <Card className="border-0 shadow-lg overflow-hidden">
      {/* Header with gradient */}
      <CardHeader
        className="p-4 cursor-pointer transition-all duration-200 hover:brightness-110"
        style={headerStyle}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{emoji}</span>
            <div>
              <h3 className="font-bold text-lg text-foreground">{title}</h3>
              <p className="text-sm text-muted-foreground">
                {section.total} canais
              </p>
            </div>
          </div>
          {isExpanded ? (
            <ChevronDown className="h-5 w-5 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-5 w-5 text-muted-foreground" />
          )}
        </div>
      </CardHeader>

      {/* Content - Subnichos */}
      {isExpanded && section.subnichos && (
        <CardContent className="p-4 space-y-3 animate-fade-in">
          {sortedSubnichos.map(([subnicho, data]) => (
            <KanbanSubnichoGroup
              key={subnicho}
              subnicho={subnicho}
              data={data}
              onChannelClick={onChannelClick}
              isMonetized={isMonetized}
            />
          ))}
        </CardContent>
      )}
    </Card>
  );
};
