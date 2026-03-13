import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Monitor, Power, PowerOff, ExternalLink, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ProxyChannel {
  conta: string;
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

export function ProxysTab() {
  const { data, isLoading, isError, error, refetch } = useQuery<ProxysData>({
    queryKey: ['perfis-proxys'],
    queryFn: fetchProxys,
  });

  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('Todos');
  const [monetizationFilter, setMonetizationFilter] = useState<string>('Todos');

  const handleCopy = (text: string, fieldId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldId);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const filteredChannels = useMemo(() => {
    if (!data?.channels) return [];
    return data.channels
      .filter((ch) => {
        if (statusFilter !== 'Todos' && ch.status !== statusFilter) return false;
        if (monetizationFilter !== 'Todos' && ch.monetization !== monetizationFilter) return false;
        return true;
      })
      .sort((a, b) => a.conta.localeCompare(b.conta));
  }, [data?.channels, statusFilter, monetizationFilter]);

  const statusBadge = (status: string) => {
    if (status === 'ATIVO') {
      return (
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
          ATIVO
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-white/[0.06] text-white/40 border border-white/[0.08]">
        OFF
      </span>
    );
  };

  const monetizationBadge = (mon: string) => {
    switch (mon) {
      case 'ATIVA':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
            ATIVA
          </span>
        );
      case 'DESMONETIZADA':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30">
            DESMONETIZADA
          </span>
        );
      case 'OFF':
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-white/[0.06] text-white/40 border border-white/[0.08]">
            OFF
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-white/[0.06] text-white/50 border border-white/[0.08]">
            {mon}
          </span>
        );
    }
  };

  // Loading skeleton
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
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-10 bg-white/[0.04] rounded animate-pulse" />
            ))}
          </div>
        </Card>
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <Card className="p-6 rounded-xl bg-white/[0.03] border border-red-500/20">
        <div className="text-center space-y-3">
          <p className="text-red-400 text-sm">
            Erro ao carregar dados: {error instanceof Error ? error.message : 'Erro desconhecido'}
          </p>
          <Button
            onClick={() => refetch()}
            variant="outline"
            size="sm"
            className="border-white/[0.1] text-white/60 hover:text-white"
          >
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
            <Monitor className="w-4 h-4 text-white/40" />
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
            <PowerOff className="w-4 h-4 text-white/40" />
            <span className="text-2xl font-bold text-white/40">{stats?.off ?? 0}</span>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2">
          <span className="text-xs text-white/50">Status:</span>
          {['Todos', 'ATIVO', 'OFF'].map((opt) => (
            <button
              key={opt}
              onClick={() => setStatusFilter(opt)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                statusFilter === opt
                  ? 'bg-white/[0.12] text-white'
                  : 'bg-white/[0.04] text-white/50 hover:bg-white/[0.08] hover:text-white/70'
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-white/50">Monetizacao:</span>
          {['Todos', 'ATIVA', 'OFF', 'DESMONETIZADA'].map((opt) => (
            <button
              key={opt}
              onClick={() => setMonetizationFilter(opt)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                monetizationFilter === opt
                  ? 'bg-white/[0.12] text-white'
                  : 'bg-white/[0.04] text-white/50 hover:bg-white/[0.08] hover:text-white/70'
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
        <span className="text-xs text-white/30 ml-auto">
          {filteredChannels.length} resultado{filteredChannels.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Table */}
      <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/[0.06]">
              <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Conta</th>
              <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">@Usuario</th>
              <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Email</th>
              <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Senha</th>
              <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Local Proxy</th>
              <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Status</th>
              <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Monetizacao</th>
              <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Criacao</th>
              <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Link</th>
            </tr>
          </thead>
          <tbody>
            {filteredChannels.map((ch, i) => (
              <tr
                key={`${ch.conta}-${i}`}
                className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
              >
                <td className="py-2 px-3 text-white/90 font-medium whitespace-nowrap">{ch.conta}</td>
                <td className="py-2 px-3 text-white/70 whitespace-nowrap">{ch.username}</td>
                <td className="py-2 px-3 whitespace-nowrap">
                  <span
                    onClick={() => handleCopy(ch.email, `email-${i}`)}
                    className="cursor-pointer hover:text-cyan-400 transition-colors relative text-white/70"
                  >
                    {ch.email}
                    {copiedField === `email-${i}` && (
                      <span className="absolute -top-6 left-0 text-xs text-green-400 bg-black/80 px-2 py-1 rounded whitespace-nowrap z-10">
                        Copiado!
                      </span>
                    )}
                  </span>
                </td>
                <td className="py-2 px-3 whitespace-nowrap">
                  <span
                    onClick={() => handleCopy(ch.password, `pass-${i}`)}
                    className="cursor-pointer hover:text-cyan-400 transition-colors relative text-white/70"
                  >
                    {ch.password}
                    {copiedField === `pass-${i}` && (
                      <span className="absolute -top-6 left-0 text-xs text-green-400 bg-black/80 px-2 py-1 rounded whitespace-nowrap z-10">
                        Copiado!
                      </span>
                    )}
                  </span>
                </td>
                <td className="py-2 px-3 text-white/60 whitespace-nowrap">{ch.location}</td>
                <td className="py-2 px-3 whitespace-nowrap">{statusBadge(ch.status)}</td>
                <td className="py-2 px-3 whitespace-nowrap">{monetizationBadge(ch.monetization)}</td>
                <td className="py-2 px-3 text-white/50 whitespace-nowrap">{ch.created}</td>
                <td className="py-2 px-3 whitespace-nowrap">
                  {ch.link ? (
                    <a
                      href={ch.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400/70 hover:text-cyan-400 transition-colors"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  ) : (
                    <span className="text-white/20">-</span>
                  )}
                </td>
              </tr>
            ))}
            {filteredChannels.length === 0 && (
              <tr>
                <td colSpan={9} className="py-8 text-center text-white/40 text-sm">
                  Nenhuma conta encontrada com os filtros selecionados
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
