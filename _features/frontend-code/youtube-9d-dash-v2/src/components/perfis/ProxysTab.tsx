import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Monitor, Power, PowerOff, ExternalLink, RefreshCw, ChevronDown, ChevronRight, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { obterCorSubnicho } from '@/utils/subnichoColors';

interface ProxyChannel {
  conta: string;
  subnicho: string;
  subnicho_code: string;
  username: string;
  email: string;
  password: string;
  location: string;
  two_fa: string;
  status: string;
  monetization: string;
  created: string;
  link: string;
  adsense: string;
  recovery_email: string;
  supplier: string;
}

interface ProxysData {
  channels: ProxyChannel[];
  stats: { total: number; active: number; off: number };
  cached_at: string;
}

const fetchProxys = async (): Promise<ProxysData> => {
  const res = await fetch('/api/perfis/proxys');
  if (!res.ok) throw new Error('Erro ao carregar dados de proxys');
  return res.json();
};

function CopyableCell({ text, id, copiedField, onCopy }: {
  text: string;
  id: string;
  copiedField: string | null;
  onCopy: (text: string, id: string) => void;
}) {
  if (!text) return <span className="text-white/20">-</span>;
  return (
    <span
      onClick={() => onCopy(text, id)}
      className="cursor-pointer hover:text-cyan-400 transition-colors relative text-white/70"
    >
      {text}
      {copiedField === id && (
        <span className="absolute -top-6 left-0 text-xs text-green-400 bg-black/80 px-2 py-1 rounded whitespace-nowrap z-10">
          Copiado!
        </span>
      )}
    </span>
  );
}

export function ProxysTab() {
  const { data, isLoading, isError, error, refetch } = useQuery<ProxysData>({
    queryKey: ['perfis-proxys'],
    queryFn: fetchProxys,
  });

  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('Todos');
  const [monetizationFilter, setMonetizationFilter] = useState<string>('Todos');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  const handleCopy = (text: string, fieldId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldId);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const toggleGroup = (code: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });
  };

  // Group channels by subnicho_code, apply filters
  const groupedChannels = useMemo(() => {
    if (!data?.channels) return [];

    const filtered = data.channels.filter((ch) => {
      if (statusFilter !== 'Todos' && ch.status.toUpperCase() !== statusFilter) return false;
      if (monetizationFilter !== 'Todos' && ch.monetization.toUpperCase() !== monetizationFilter) return false;
      return true;
    });

    // Group by subnicho_code
    const groups: Record<string, { code: string; name: string; channels: ProxyChannel[] }> = {};
    for (const ch of filtered) {
      const key = ch.subnicho_code || 'OTHER';
      if (!groups[key]) {
        groups[key] = { code: key, name: ch.subnicho || ch.conta, channels: [] };
      }
      groups[key].channels.push(ch);
    }

    // Sort groups by code, and within each group: ativos first
    const sorted = Object.values(groups).sort((a, b) => a.code.localeCompare(b.code));
    for (const g of sorted) {
      g.channels.sort((a, b) => {
        // Monetizados first, then ativos, then OFF
        const monOrder = (ch: ProxyChannel) => {
          const mon = ch.monetization.toUpperCase();
          if (mon === 'ATIVA' || mon === 'ATIVO') return 0;
          const st = ch.status.toUpperCase();
          if (st === 'OFF') return 2;
          return 1;
        };
        return monOrder(a) - monOrder(b) || a.conta.localeCompare(b.conta);
      });
    }
    return sorted;
  }, [data?.channels, statusFilter, monetizationFilter]);

  const totalFiltered = useMemo(() => groupedChannels.reduce((s, g) => s + g.channels.length, 0), [groupedChannels]);

  const monetizationBadge = (mon: string) => {
    switch (mon.toUpperCase()) {
      case 'ATIVA':
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">ATIVA</span>;
      case 'DESMONETIZADA':
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30">DESMON</span>;
      case 'OFF':
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-white/[0.06] text-white/40 border border-white/[0.08]">OFF</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-white/[0.06] text-white/50 border border-white/[0.08]">{mon}</span>;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <div className="h-4 w-24 bg-white/[0.06] rounded animate-pulse mb-2" />
              <div className="h-8 w-16 bg-white/[0.06] rounded animate-pulse" />
            </Card>
          ))}
        </div>
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <div className="h-5 w-40 bg-white/[0.06] rounded animate-pulse mb-3" />
            <div className="space-y-2">
              {[1, 2].map((j) => <div key={j} className="h-10 bg-white/[0.04] rounded animate-pulse" />)}
            </div>
          </Card>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <Card className="p-6 rounded-xl bg-white/[0.03] border border-red-500/20">
        <div className="text-center space-y-3">
          <p className="text-red-400 text-sm">
            Erro ao carregar dados: {error instanceof Error ? error.message : 'Erro desconhecido'}
          </p>
          <Button onClick={() => refetch()} variant="outline" size="sm" className="border-white/[0.1] text-white/60 hover:text-white">
            <RefreshCw className="w-4 h-4 mr-2" /> Tentar novamente
          </Button>
        </div>
      </Card>
    );
  }

  const stats = data?.stats;

  return (
    <div className="space-y-4">
      {/* Stat Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-xs text-white/60 mb-1">Total Contas</p>
          <div className="flex items-center gap-2">
            <Monitor className="w-4 h-4 text-blue-400" />
            <span className="text-2xl font-bold text-white/90">{stats?.total ?? 0}</span>
          </div>
        </Card>
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-xs text-white/60 mb-1">Ativas</p>
          <div className="flex items-center gap-2">
            <Power className="w-4 h-4 text-green-400" />
            <span className="text-2xl font-bold text-green-400">{stats?.active ?? 0}</span>
          </div>
        </Card>
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-xs text-white/60 mb-1">Desligadas</p>
          <div className="flex items-center gap-2">
            <PowerOff className="w-4 h-4 text-red-400" />
            <span className="text-2xl font-bold text-red-400">{stats?.off ?? 0}</span>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <Filter className="w-3.5 h-3.5 text-white/30" />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white/[0.04] border border-white/[0.08] text-white/70 hover:bg-white/[0.08] transition-colors">
              Status: {statusFilter === 'Todos' ? 'Todos' : statusFilter === 'ATIVO' ? 'Ativo' : 'Off'}
              <ChevronDown className="w-3 h-3 text-white/40" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="min-w-[120px]">
            {[
              { value: 'Todos', label: 'Todos' },
              { value: 'ATIVO', label: 'Ativo' },
              { value: 'OFF', label: 'Off' },
            ].map((opt) => (
              <DropdownMenuItem
                key={opt.value}
                onClick={() => setStatusFilter(opt.value)}
                className={statusFilter === opt.value ? 'font-semibold' : ''}
              >
                {opt.value === 'ATIVO' && <span className="w-2 h-2 rounded-full bg-green-500 mr-2" />}
                {opt.value === 'OFF' && <span className="w-2 h-2 rounded-full bg-red-500 mr-2" />}
                {opt.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white/[0.04] border border-white/[0.08] text-white/70 hover:bg-white/[0.08] transition-colors">
              Monet: {monetizationFilter === 'Todos' ? 'Todos' : monetizationFilter === 'ATIVA' ? 'Ativa' : monetizationFilter === 'DESMONETIZADA' ? 'Desmon' : 'Off'}
              <ChevronDown className="w-3 h-3 text-white/40" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="min-w-[150px]">
            {[
              { value: 'Todos', label: 'Todos', dot: '' },
              { value: 'ATIVA', label: 'Ativa', dot: 'bg-green-500' },
              { value: 'OFF', label: 'Off', dot: 'bg-white/40' },
              { value: 'DESMONETIZADA', label: 'Desmonetizada', dot: 'bg-red-500' },
            ].map((opt) => (
              <DropdownMenuItem
                key={opt.value}
                onClick={() => setMonetizationFilter(opt.value)}
                className={monetizationFilter === opt.value ? 'font-semibold' : ''}
              >
                {opt.dot && <span className={`w-2 h-2 rounded-full ${opt.dot} mr-2`} />}
                {opt.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <span className="text-xs text-white/30 ml-auto">
          {totalFiltered} conta{totalFiltered !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Grouped Cards by Subnicho */}
      <div className="space-y-3">
        {groupedChannels.map((group) => {
          const cores = obterCorSubnicho(group.name);
          const isCollapsed = !expandedGroups.has(group.code);

          return (
            <Card
              key={group.code}
              className="rounded-xl border overflow-hidden"
              style={{
                backgroundColor: cores.fundo + '30',
                borderColor: cores.borda + '80',
              }}
            >
              {/* Group header */}
              <button
                onClick={() => toggleGroup(group.code)}
                className="w-full flex items-center gap-3 px-4 py-3 transition-colors hover:bg-white/[0.02]"
              >
                {isCollapsed
                  ? <ChevronRight className="w-4 h-4 text-white/40" />
                  : <ChevronDown className="w-4 h-4 text-white/40" />
                }
                <span
                  className="px-2.5 py-0.5 rounded-full text-xs font-bold text-white/90"
                  style={{ backgroundColor: cores.fundo + '40', border: `1px solid ${cores.borda}60` }}
                >
                  {group.code}
                </span>
                <span className="text-sm font-medium text-white/80">{group.name}</span>
                <span className="text-xs text-white/40 ml-auto">{group.channels.length} conta{group.channels.length !== 1 ? 's' : ''}</span>
              </button>

              {/* Channel rows */}
              {!isCollapsed && (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-t border-white/[0.06]">
                        <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Conta</th>
                        <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">@Usuário</th>
                        <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Email</th>
                        <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Senha</th>
                        <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Local</th>
                        <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Monet</th>
                        <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Criação</th>
                        <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Link</th>
                      </tr>
                    </thead>
                    <tbody>
                      {group.channels.map((ch, i) => {
                        const isOff = ch.status.toUpperCase() === 'OFF';
                        return (
                          <tr
                            key={`${ch.conta}-${i}`}
                            className={`border-t border-white/[0.03] hover:bg-white/[0.02] transition-colors ${isOff ? 'opacity-50' : ''}`}
                          >
                            <td className="py-2 px-3 text-white/90 font-medium whitespace-nowrap">
                              <div className="flex items-center gap-1.5">
                                <span className={`w-2 h-2 rounded-full ${isOff ? 'bg-red-500' : 'bg-green-500'}`} />
                                {ch.conta}
                              </div>
                            </td>
                            <td className="py-2 px-3 text-white/70 whitespace-nowrap">{ch.username || '-'}</td>
                            <td className="py-2 px-3 whitespace-nowrap">
                              <CopyableCell text={ch.email} id={`email-${group.code}-${i}`} copiedField={copiedField} onCopy={handleCopy} />
                            </td>
                            <td className="py-2 px-3 whitespace-nowrap">
                              <CopyableCell text={ch.password} id={`pass-${group.code}-${i}`} copiedField={copiedField} onCopy={handleCopy} />
                            </td>
                            <td className="py-2 px-3 text-white/60 whitespace-nowrap">{ch.location || '-'}</td>
                            <td className="py-2 px-3 whitespace-nowrap">{monetizationBadge(ch.monetization)}</td>
                            <td className="py-2 px-3 text-white/50 whitespace-nowrap">{ch.created || '-'}</td>
                            <td className="py-2 px-3 whitespace-nowrap">
                              {ch.link ? (
                                <a href={ch.link} target="_blank" rel="noopener noreferrer" className="text-cyan-400/70 hover:text-cyan-400 transition-colors">
                                  <ExternalLink className="w-4 h-4" />
                                </a>
                              ) : (
                                <span className="text-white/20">-</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          );
        })}

        {groupedChannels.length === 0 && (
          <Card className="p-8 rounded-xl bg-white/[0.03] border border-white/[0.06] text-center">
            <p className="text-white/40 text-sm">Nenhuma conta encontrada com os filtros selecionados</p>
          </Card>
        )}
      </div>

      {data?.cached_at && (
        <p className="text-xs text-white/30 text-right">
          Cache: {new Date(data.cached_at).toLocaleString('pt-BR')}
        </p>
      )}
    </div>
  );
}
