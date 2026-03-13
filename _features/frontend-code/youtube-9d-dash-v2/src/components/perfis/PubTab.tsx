import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Users,
  TrendingUp,
  AlertTriangle,
  Clock,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { obterCorSubnicho } from '@/utils/subnichoColors';

// ── Types ──────────────────────────────────────────────────────────────

interface PubSummary {
  total_channels: number;
  active_channels: number;
  monetized: number;
  desmonetized: number;
  total_pub: number;
  total_done: number;
  scripts_low_count: number;
  zero_programar_count: number;
}

interface PubAlert {
  channel: string;
  subnicho: string;
  type: string;
  severity: 'red' | 'yellow';
  message: string;
  monetized: string;
}

interface HealthFactors {
  overall: string;
  scripts: string;
  programar: string;
  pub_status: string;
}

interface PubChannel {
  name: string;
  subnicho: string;
  last_pub: string;
  pub_count: number;
  done: number;
  programar: number;
  thumbs: number;
  started: string;
  days_active: number;
  frequency: number;
  prod: string;
  config: string;
  monetized: string;
  scripts_done: number;
  scripts_total: number;
  scripts_remaining: number;
  priority: string;
  url: string;
  health: string;
  health_factors: HealthFactors;
  inactive: boolean;
}

interface PubData {
  summary: PubSummary;
  alerts: PubAlert[];
  channels: PubChannel[];
  cached_at: string;
}

// ── Helpers ────────────────────────────────────────────────────────────

const API_BASE = window.location.origin;

const HEALTH_ORDER: Record<string, number> = {
  red: 0,
  yellow: 1,
  green: 2,
  gray: 3,
};

const healthDotColor = (health: string) => {
  switch (health) {
    case 'red': return 'bg-red-500';
    case 'yellow': return 'bg-yellow-500';
    case 'green': return 'bg-green-500';
    default: return 'bg-gray-500';
  }
};

const scriptsColor = (remaining: number) => {
  if (remaining < 3) return 'text-red-400';
  if (remaining < 5) return 'text-yellow-400';
  return 'text-green-400';
};

const yesNoBadge = (value: string) => {
  const isYes = value === 'SIM';
  return (
    <span
      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
        isYes
          ? 'bg-green-500/20 text-green-400'
          : 'bg-white/[0.06] text-white/40'
      }`}
    >
      {value}
    </span>
  );
};

// ── Fetch ──────────────────────────────────────────────────────────────

const fetchPubData = async (): Promise<PubData> => {
  const res = await fetch(`${API_BASE}/api/perfis/pub`);
  if (!res.ok) throw new Error(`Erro ${res.status}: ${res.statusText}`);
  return res.json();
};

// ── PubCards (inline) ──────────────────────────────────────────────────

function PubCards({ summary }: { summary: PubSummary }) {
  const cards = [
    {
      label: 'Canais Ativos',
      value: summary.active_channels,
      sub: `de ${summary.total_channels}`,
      icon: <Users className="w-5 h-5" />,
      color: 'text-teal-400',
      iconBg: 'bg-teal-500/20',
    },
    {
      label: 'Total Publicacoes',
      value: summary.total_pub.toLocaleString('pt-BR'),
      sub: null,
      icon: <TrendingUp className="w-5 h-5" />,
      color: 'text-blue-400',
      iconBg: 'bg-blue-500/20',
    },
    {
      label: 'Scripts Baixos',
      value: summary.scripts_low_count,
      sub: 'canais',
      icon: <AlertTriangle className="w-5 h-5" />,
      color: summary.scripts_low_count > 0 ? 'text-amber-400' : 'text-green-400',
      iconBg: summary.scripts_low_count > 0 ? 'bg-amber-500/20' : 'bg-green-500/20',
    },
    {
      label: 'Sem Programar',
      value: summary.zero_programar_count,
      sub: 'canais',
      icon: <Clock className="w-5 h-5" />,
      color: summary.zero_programar_count > 0 ? 'text-red-400' : 'text-green-400',
      iconBg: summary.zero_programar_count > 0 ? 'bg-red-500/20' : 'bg-green-500/20',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {cards.map((c) => (
        <Card
          key={c.label}
          className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-white/60">{c.label}</p>
              <p className={`text-2xl font-bold mt-1 ${c.color}`}>{c.value}</p>
              {c.sub && (
                <p className="text-xs text-white/40 mt-0.5">{c.sub}</p>
              )}
            </div>
            <div className={`p-2 rounded-xl ${c.iconBg}`}>
              <span className={c.color}>{c.icon}</span>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

// ── Subnicho Badge with color ─────────────────────────────────────────

function SubnichoBadge({ name }: { name: string }) {
  const cores = obterCorSubnicho(name);
  return (
    <span
      className="px-2 py-0.5 rounded-full text-xs font-medium text-white/90 whitespace-nowrap"
      style={{ backgroundColor: cores.fundo + '40', borderColor: cores.borda, border: `1px solid ${cores.borda}60` }}
    >
      {name}
    </span>
  );
}

// ── PubAlerts (inline) ─────────────────────────────────────────────────

function PubAlerts({ alerts }: { alerts: PubAlert[] }) {
  const redAlerts = alerts.filter((a) => a.severity === 'red');
  const yellowAlerts = alerts.filter((a) => a.severity === 'yellow');

  if (redAlerts.length === 0 && yellowAlerts.length === 0) return null;

  // Group alerts by type
  const groupByType = (items: PubAlert[]) => {
    const groups: Record<string, PubAlert[]> = {};
    for (const a of items) {
      const key = a.type;
      if (!groups[key]) groups[key] = [];
      groups[key].push(a);
    }
    return groups;
  };

  const ALERT_TYPE_LABELS: Record<string, string> = {
    sem_programar: 'Sem Programar',
    nunca_publicou: 'Nunca Publicou',
    scripts_critico: 'Scripts Críticos',
    scripts_baixo: 'Scripts Acabando',
    programar_amanha: 'Último Programado',
  };

  const renderAlertTable = (items: PubAlert[], type: string) => {
    if (items.length === 0) return null;
    return (
      <div key={type} className="mb-4 last:mb-0">
        <h4 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">
          {ALERT_TYPE_LABELS[type] || type} ({items.length})
        </h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/[0.06]">
              <th className="text-left py-1.5 px-2 text-xs text-white/40 font-medium w-[130px]">Subnicho</th>
              <th className="text-left py-1.5 px-2 text-xs text-white/40 font-medium">Canal</th>
              <th className="text-right py-1.5 px-2 text-xs text-white/40 font-medium">Info</th>
            </tr>
          </thead>
          <tbody>
            {items.map((a, i) => (
              <tr
                key={`${a.channel}-${i}`}
                className="border-b border-white/[0.02] hover:bg-white/[0.03] transition-colors"
              >
                <td className="py-1.5 px-2"><SubnichoBadge name={a.subnicho} /></td>
                <td className="py-1.5 px-2 text-white/80 font-medium whitespace-nowrap">{a.channel}</td>
                <td className="py-1.5 px-2 text-xs text-white/50 text-right whitespace-nowrap">{a.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderSection = (
    items: PubAlert[],
    emoji: string,
    label: string,
    borderClass: string,
    bgClass: string,
  ) => {
    if (items.length === 0) return null;
    const groups = groupByType(items);

    return (
      <Card className={`p-4 rounded-xl ${bgClass} border ${borderClass}`}>
        <h3 className="text-sm font-semibold text-white/90 mb-4 flex items-center gap-2">
          <span>{emoji}</span>
          <span>{label}</span>
          <span className="text-xs text-white/40 font-normal">({items.length})</span>
        </h3>
        {Object.entries(groups).map(([type, groupItems]) =>
          renderAlertTable(groupItems, type)
        )}
      </Card>
    );
  };

  const hasRed = redAlerts.length > 0;
  const hasYellow = yellowAlerts.length > 0;
  const hasBoth = hasRed && hasYellow;

  return (
    <div className={hasBoth ? 'grid grid-cols-1 lg:grid-cols-2 gap-3' : 'space-y-3'}>
      {renderSection(
        redAlerts,
        '🚨',
        'URGENTE',
        'border-red-500/20',
        'bg-red-500/[0.03]',
      )}
      {renderSection(
        yellowAlerts,
        '⚠️',
        'ATENÇÃO',
        'border-yellow-500/20',
        'bg-yellow-500/[0.03]',
      )}
    </div>
  );
}

// ── PubChannelsList (grouped by subnicho, collapsible, paginated) ─────

// Fixed subnicho order (same as Tabela tab)
const SUBNICHO_ORDER = [
  'reis perversos',
  'historias sombrias',
  'culturas macabras',
  'relatos de guerra',
  'frentes de batalha',
  'guerras e civilizacoes',
  'terror',
  'biografias',
  'misterios',
  'conspiracao',
  'licoes de vida',
  'registros malditos',
];

const normalizeStr = (s: string) =>
  s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

function PubChannelsList({ channels }: { channels: PubChannel[] }) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  const toggleGroup = (key: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // Separate active/inactive, group active by subnicho
  const { groups, inactive } = useMemo(() => {
    const act: PubChannel[] = [];
    const inact: PubChannel[] = [];
    for (const ch of channels) {
      if (ch.inactive) inact.push(ch);
      else act.push(ch);
    }

    // Sort: priority first, then by health
    act.sort((a, b) => {
      const aPrio = a.priority === 'SIM' ? 0 : 1;
      const bPrio = b.priority === 'SIM' ? 0 : 1;
      if (aPrio !== bPrio) return aPrio - bPrio;
      return (HEALTH_ORDER[a.health] ?? 3) - (HEALTH_ORDER[b.health] ?? 3);
    });

    // Group by subnicho
    const grpMap: Record<string, PubChannel[]> = {};
    for (const ch of act) {
      const key = ch.subnicho || '(Indefinido)';
      if (!grpMap[key]) grpMap[key] = [];
      grpMap[key].push(ch);
    }

    // Sort groups by fixed order, indefinido near-last, unknown at end
    const grps = Object.entries(grpMap)
      .map(([name, chs]) => ({ key: name, name, channels: chs }))
      .sort((a, b) => {
        const aN = normalizeStr(a.name);
        const bN = normalizeStr(b.name);
        const aIsIndef = aN.includes('indefinido');
        const bIsIndef = bN.includes('indefinido');
        if (aIsIndef && !bIsIndef) return 1;
        if (!aIsIndef && bIsIndef) return -1;
        const aIdx = SUBNICHO_ORDER.findIndex((s) => aN.includes(s));
        const bIdx = SUBNICHO_ORDER.findIndex((s) => bN.includes(s));
        const aOrder = aIdx >= 0 ? aIdx : SUBNICHO_ORDER.length;
        const bOrder = bIdx >= 0 ? bIdx : SUBNICHO_ORDER.length;
        return aOrder - bOrder;
      });

    inact.sort((a, b) => a.name.localeCompare(b.name));
    return { groups: grps, inactive: inact };
  }, [channels]);

  const renderRow = (ch: PubChannel) => (
    <tr
      key={ch.name}
      className="border-t border-white/[0.03] hover:bg-white/[0.02] transition-colors"
    >
      <td className="py-2 px-3">
        <span className={`w-2.5 h-2.5 rounded-full inline-block ${healthDotColor(ch.health)}`} />
      </td>
      <td className="py-2 px-3">
        <div className="flex items-center gap-2">
          <span className="text-sm text-white/90 font-medium">{ch.name}</span>
          {ch.url && (
            <a href={ch.url} target="_blank" rel="noopener noreferrer" className="text-white/30 hover:text-white/60 transition-colors">
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </td>
      <td className="py-2 px-3 text-sm text-white/70 whitespace-nowrap">{ch.last_pub}</td>
      <td className="py-2 px-3 text-sm">
        <span className={ch.programar === 0 ? 'text-red-400 font-semibold' : ch.programar <= 2 ? 'text-yellow-400' : 'text-white/70'}>
          {ch.programar}
        </span>
      </td>
      <td className="py-2 px-3 text-sm">
        <span className={scriptsColor(ch.scripts_remaining)}>{ch.scripts_done}/{ch.scripts_total}</span>
      </td>
      <td className="py-2 px-3">{yesNoBadge(ch.priority)}</td>
      <td className="py-2 px-3">{yesNoBadge(ch.monetized)}</td>
      <td className="py-2 px-3">{yesNoBadge(ch.prod)}</td>
    </tr>
  );

  return (
    <div className="space-y-2">
      {/* Header */}
      <h3 className="text-sm font-semibold text-white/70">
        Todos os Canais ({channels.filter((c) => !c.inactive).length})
      </h3>

      {/* Grouped cards */}
      {groups.map((group) => {
        const cores = obterCorSubnicho(group.name);
        const isExpanded = expandedGroups.has(group.key);
        const prioCount = group.channels.filter((c) => c.priority === 'SIM').length;

        return (
          <Card
            key={group.key}
            className="rounded-xl border overflow-hidden"
            style={{
              backgroundColor: cores.fundo + '18',
              borderColor: cores.borda + '50',
            }}
          >
            <button
              onClick={() => toggleGroup(group.key)}
              className="w-full flex items-center gap-3 px-4 py-3 transition-colors hover:bg-white/[0.02]"
            >
              {isExpanded
                ? <ChevronDown className="w-4 h-4 text-white/40" />
                : <ChevronRight className="w-4 h-4 text-white/40" />
              }
              <span
                className="px-2.5 py-0.5 rounded-full text-xs font-bold text-white/90"
                style={{ backgroundColor: cores.fundo + '40', border: `1px solid ${cores.borda}60` }}
              >
                {group.name}
              </span>
              <span className="text-xs text-white/40">
                {group.channels.length} {group.channels.length !== 1 ? 'canais' : 'canal'}
              </span>
              {prioCount > 0 && (
                <span className="text-xs px-1.5 py-0.5 rounded bg-teal-500/20 text-teal-400 border border-teal-500/30">
                  {prioCount} prioridade
                </span>
              )}
            </button>

            {isExpanded && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-t border-white/[0.06]">
                      {['', 'Canal', 'Ult Pub', 'Prog', 'Scripts', 'Prior', 'Monet', 'Prod'].map((h) => (
                        <th key={h} className="py-2 px-3 text-xs text-white/40 font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>{group.channels.map(renderRow)}</tbody>
                </table>
              </div>
            )}
          </Card>
        );
      })}

      {/* Inactive channels */}
      {inactive.length > 0 && (
        <Card className="rounded-xl bg-white/[0.02] border border-white/[0.04] overflow-hidden">
          <button
            onClick={() => toggleGroup('__inactive__')}
            className="w-full flex items-center gap-3 px-4 py-3 text-xs text-white/40 hover:text-white/60 transition-colors"
          >
            {expandedGroups.has('__inactive__')
              ? <ChevronDown className="w-3.5 h-3.5" />
              : <ChevronRight className="w-3.5 h-3.5" />
            }
            Inativos ({inactive.length})
          </button>
          {expandedGroups.has('__inactive__') && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <tbody>
                  {inactive.map((ch) => (
                    <tr key={ch.name} className="border-t border-white/[0.03] opacity-50">
                      <td className="py-2 px-3"><span className="w-2.5 h-2.5 rounded-full inline-block bg-gray-500" /></td>
                      <td className="py-2 px-3"><span className="text-white/60">{ch.name}</span></td>
                      <td className="py-2 px-3 text-white/40">{ch.last_pub}</td>
                      <td className="py-2 px-3 text-white/40">{ch.programar}</td>
                      <td className="py-2 px-3 text-white/40">{ch.scripts_done}/{ch.scripts_total}</td>
                      <td className="py-2 px-3">{yesNoBadge(ch.priority)}</td>
                      <td className="py-2 px-3">{yesNoBadge(ch.monetized)}</td>
                      <td className="py-2 px-3">{yesNoBadge(ch.prod)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

// ── Loading Skeleton ───────────────────────────────────────────────────

function PubSkeleton() {
  return (
    <div className="space-y-6">
      {/* Cards skeleton */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <Card
            key={i}
            className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]"
          >
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-7 w-14" />
                <Skeleton className="h-3 w-12" />
              </div>
              <Skeleton className="h-9 w-9 rounded-xl" />
            </div>
          </Card>
        ))}
      </div>
      {/* Alerts skeleton */}
      <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
        <Skeleton className="h-4 w-24 mb-3" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-2 mb-2">
            <Skeleton className="h-2.5 w-2.5 rounded-full" />
            <Skeleton className="h-3 w-28" />
            <Skeleton className="h-4 w-20 rounded-full" />
            <Skeleton className="h-3 w-40" />
          </div>
        ))}
      </Card>
      {/* Table skeleton */}
      <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="flex items-center gap-4 mb-3">
            <Skeleton className="h-2.5 w-2.5 rounded-full" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-8" />
            <Skeleton className="h-3 w-12" />
            <Skeleton className="h-4 w-12 rounded-full" />
            <Skeleton className="h-4 w-12 rounded-full" />
            <Skeleton className="h-4 w-12 rounded-full" />
          </div>
        ))}
      </Card>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────

export default function PubTab() {
  const { data, isLoading, isError, error, refetch } = useQuery<PubData>({
    queryKey: ['perfis-pub'],
    queryFn: fetchPubData,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  if (isLoading) return <PubSkeleton />;

  if (isError) {
    return (
      <Card className="p-8 rounded-xl bg-white/[0.03] border border-red-500/20 text-center">
        <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-3" />
        <p className="text-white/80 font-medium mb-1">Erro ao carregar dados</p>
        <p className="text-sm text-white/50 mb-4">
          {error instanceof Error ? error.message : 'Erro desconhecido'}
        </p>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-white/70 text-sm transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Tentar novamente
        </button>
      </Card>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <PubCards summary={data.summary} />
      <PubAlerts alerts={data.alerts} />
      <PubChannelsList channels={data.channels} />

      {data.cached_at && (
        <p className="text-xs text-white/30 text-right">
          Cache: {new Date(data.cached_at).toLocaleString('pt-BR')}
        </p>
      )}
    </div>
  );
}
