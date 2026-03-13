import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CreditCard, ChevronDown, ChevronRight, Users, Zap, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface LinkedChannel {
  conta: string;
  name: string;
  date_linked: string;
  monetization: string;
}

interface AdsenseAccount {
  name: string;
  email: string;
  cnpj: string;
  channels: LinkedChannel[];
}

interface AdsenseData {
  accounts: AdsenseAccount[];
  stats: {
    total_accounts: number;
    total_channels_linked: number;
    active_monetized: number;
  };
  cached_at: string;
}

const fetchAdsense = async (): Promise<AdsenseData> => {
  const res = await fetch('/api/perfis/adsense');
  if (!res.ok) throw new Error('Erro ao carregar dados de Adsense');
  return res.json();
};

const monetizationBadge = (mon: string) => {
  const normalized = mon?.trim();
  switch (normalized) {
    case 'ATIVO':
    case 'ATIVA':
      return (
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
          {normalized}
        </span>
      );
    case 'Inauthentic content':
      return (
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30">
          Inauthentic content
        </span>
      );
    case 'Related Channel':
      return (
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-orange-500/20 text-orange-400 border border-orange-500/30">
          Related Channel
        </span>
      );
    case 'Sexually gratifying content':
      return (
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400 border border-purple-500/30">
          Sexually gratifying content
        </span>
      );
    case 'SOLICITADO':
      return (
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400 border border-blue-500/30">
          SOLICITADO
        </span>
      );
    default:
      return (
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-white/[0.06] text-white/50 border border-white/[0.08]">
          {normalized || '-'}
        </span>
      );
  }
};

export function AdsenseTab() {
  const { data, isLoading, isError, error, refetch } = useQuery<AdsenseData>({
    queryKey: ['perfis-adsense'],
    queryFn: fetchAdsense,
  });

  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [expandedAccounts, setExpandedAccounts] = useState<Set<number>>(new Set());

  const handleCopy = (text: string, fieldId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldId);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const toggleAccount = (index: number) => {
    setExpandedAccounts((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
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
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <div className="h-6 w-48 bg-white/[0.06] rounded animate-pulse mb-2" />
            <div className="h-4 w-32 bg-white/[0.04] rounded animate-pulse" />
          </Card>
        ))}
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
      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-xs text-white/60 mb-1">Total Contas Adsense</p>
          <div className="flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-white/40" />
            <span className="text-2xl font-bold text-white/90">{stats?.total_accounts ?? 0}</span>
          </div>
        </Card>
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-xs text-white/60 mb-1">Canais Vinculados</p>
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-cyan-400" />
            <span className="text-2xl font-bold text-white/90">{stats?.total_channels_linked ?? 0}</span>
          </div>
        </Card>
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-xs text-white/60 mb-1">Monetizados Ativos</p>
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-green-400" />
            <span className="text-2xl font-bold text-green-400">{stats?.active_monetized ?? 0}</span>
          </div>
        </Card>
      </div>

      {/* Adsense Account Cards */}
      <div className="space-y-3">
        {data?.accounts.map((account, idx) => {
          const isExpanded = expandedAccounts.has(idx);
          return (
            <Card
              key={`adsense-${idx}`}
              className="rounded-xl bg-white/[0.03] border border-white/[0.06] overflow-hidden"
            >
              {/* Account Header */}
              <button
                onClick={() => toggleAccount(idx)}
                className="w-full flex items-center justify-between p-4 hover:bg-white/[0.02] transition-colors text-left"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <CreditCard className="w-4 h-4 text-white/40 flex-shrink-0" />
                    <span className="text-sm font-medium text-white/90 truncate">{account.name}</span>
                    <span className="text-xs text-white/40">
                      {account.channels.length} canal{account.channels.length !== 1 ? 'is' : ''}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 mt-1 ml-7">
                    <span
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopy(account.email, `adsense-email-${idx}`);
                      }}
                      className="cursor-pointer hover:text-cyan-400 transition-colors relative text-xs text-white/60"
                    >
                      {account.email}
                      {copiedField === `adsense-email-${idx}` && (
                        <span className="absolute -top-6 left-0 text-xs text-green-400 bg-black/80 px-2 py-1 rounded whitespace-nowrap z-10">
                          Copiado!
                        </span>
                      )}
                    </span>
                    {account.cnpj && (
                      <span className="text-xs text-white/40">CNPJ: {account.cnpj}</span>
                    )}
                  </div>
                </div>
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-white/40 flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-white/40 flex-shrink-0" />
                )}
              </button>

              {/* Expanded Channels List */}
              {isExpanded && (
                <div className="border-t border-white/[0.06] px-4 py-3 space-y-2">
                  {account.channels.length === 0 ? (
                    <p className="text-xs text-white/40 text-center py-2">Nenhum canal vinculado</p>
                  ) : (
                    account.channels.map((ch, ci) => (
                      <div
                        key={`ch-${idx}-${ci}`}
                        className="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-white/[0.02] transition-colors"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <span className="text-xs text-white/50 font-mono flex-shrink-0">{ch.conta}</span>
                          <span className="text-sm text-white/80 truncate">{ch.name}</span>
                        </div>
                        <div className="flex-shrink-0 ml-3">
                          {monetizationBadge(ch.monetization)}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </Card>
          );
        })}

        {(!data?.accounts || data.accounts.length === 0) && (
          <Card className="p-8 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <p className="text-center text-white/40 text-sm">Nenhuma conta Adsense encontrada</p>
          </Card>
        )}
      </div>
    </div>
  );
}
