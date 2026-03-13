import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
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
  owner: string;
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

// Owner color palette — distinct colors per sócio
const OWNER_COLORS: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  LUCCA: {
    bg: 'rgba(59, 130, 246, 0.06)',
    border: 'rgba(59, 130, 246, 0.20)',
    text: 'text-blue-400',
    badge: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  },
  CELLIBS: {
    bg: 'rgba(34, 197, 94, 0.06)',
    border: 'rgba(34, 197, 94, 0.20)',
    text: 'text-green-400',
    badge: 'bg-green-500/20 text-green-400 border-green-500/30',
  },
  MARCELO: {
    bg: 'rgba(34, 197, 94, 0.06)',
    border: 'rgba(34, 197, 94, 0.20)',
    text: 'text-green-400',
    badge: 'bg-green-500/20 text-green-400 border-green-500/30',
  },
  MICHA: {
    bg: 'rgba(34, 197, 94, 0.06)',
    border: 'rgba(34, 197, 94, 0.20)',
    text: 'text-green-400',
    badge: 'bg-green-500/20 text-green-400 border-green-500/30',
  },
  ARTHUR: {
    bg: 'rgba(239, 68, 68, 0.06)',
    border: 'rgba(239, 68, 68, 0.20)',
    text: 'text-red-400',
    badge: 'bg-red-500/20 text-red-400 border-red-500/30',
  },
  JOAO: {
    bg: 'rgba(249, 115, 22, 0.06)',
    border: 'rgba(249, 115, 22, 0.20)',
    text: 'text-orange-400',
    badge: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  },
};

const DEFAULT_OWNER_COLOR = {
  bg: 'rgba(255, 255, 255, 0.03)',
  border: 'rgba(255, 255, 255, 0.06)',
  text: 'text-white/60',
  badge: 'bg-white/[0.08] text-white/60 border-white/[0.12]',
};

function getOwnerColor(owner: string) {
  // Normalize: remove accents + uppercase
  const normalized = owner.toUpperCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  return OWNER_COLORS[normalized] || DEFAULT_OWNER_COLOR;
}

const monetizationBadge = (mon: string) => {
  const normalized = mon?.trim();
  switch (normalized) {
    case 'ATIVO':
    case 'ATIVA':
      return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">{normalized}</span>;
    case 'Inauthentic content':
      return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30">Inauthentic</span>;
    case 'Related Channel':
      return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-orange-500/20 text-orange-400 border border-orange-500/30">Related</span>;
    case 'Sexually gratifying content':
      return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400 border border-purple-500/30">Sexual</span>;
    case 'SOLICITADO':
      return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400 border border-blue-500/30">SOLICITADO</span>;
    default:
      return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-white/[0.06] text-white/50 border border-white/[0.08]">{normalized || '-'}</span>;
  }
};

export function AdsenseTab() {
  const { data, isLoading, isError, error, refetch } = useQuery<AdsenseData>({
    queryKey: ['perfis-adsense'],
    queryFn: fetchAdsense,
  });

  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [expandedAccounts, setExpandedAccounts] = useState<Set<string>>(new Set());

  const handleCopy = (text: string, fieldId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldId);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const toggleAccount = (key: string) => {
    setExpandedAccounts((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // Group accounts by owner
  const ownerGroups = useMemo(() => {
    if (!data?.accounts) return [];
    const groups: Record<string, AdsenseAccount[]> = {};
    for (const acc of data.accounts) {
      const owner = acc.owner || 'Outros';
      if (!groups[owner]) groups[owner] = [];
      groups[owner].push(acc);
    }
    return Object.entries(groups);
  }, [data?.accounts]);

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
      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-xs text-white/60 mb-1">Total Contas Adsense</p>
          <div className="flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-amber-400" />
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

      {/* Grouped by Owner */}
      <div className="space-y-6">
        {ownerGroups.map(([owner, accounts]) => {
          const colors = getOwnerColor(owner);
          const totalChannels = accounts.reduce((s, a) => s + a.channels.length, 0);

          return (
            <div key={owner} className="space-y-2">
              {/* Owner header */}
              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${colors.badge}`}>
                  {owner}
                </span>
                <span className="text-xs text-white/40">
                  {accounts.length} conta{accounts.length !== 1 ? 's' : ''} — {totalChannels} canal{totalChannels !== 1 ? 'is' : ''}
                </span>
              </div>

              {/* Account cards */}
              <div className="space-y-2">
                {accounts.map((account, idx) => {
                  const key = `${owner}-${idx}`;
                  const isExpanded = expandedAccounts.has(key);

                  return (
                    <Card
                      key={key}
                      className="rounded-xl overflow-hidden"
                      style={{
                        backgroundColor: colors.bg,
                        borderColor: colors.border,
                        border: `1px solid ${colors.border}`,
                      }}
                    >
                      {/* Account Header */}
                      <button
                        onClick={() => toggleAccount(key)}
                        className="w-full flex items-center justify-between p-4 hover:bg-white/[0.02] transition-colors text-left"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3">
                            <CreditCard className={`w-4 h-4 flex-shrink-0 ${colors.text}`} />
                            <span className="text-sm font-medium text-white/90 truncate">{account.name}</span>
                            <span className="text-xs text-white/40">
                              {account.channels.length} canal{account.channels.length !== 1 ? 'is' : ''}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 mt-1 ml-7">
                            <span
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCopy(account.email, `adsense-email-${key}`);
                              }}
                              className="cursor-pointer hover:text-cyan-400 transition-colors relative text-xs text-white/60"
                            >
                              {account.email}
                              {copiedField === `adsense-email-${key}` && (
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
                        {isExpanded
                          ? <ChevronDown className="w-4 h-4 text-white/40 flex-shrink-0" />
                          : <ChevronRight className="w-4 h-4 text-white/40 flex-shrink-0" />
                        }
                      </button>

                      {/* Expanded Channels List */}
                      {isExpanded && (
                        <div className="border-t border-white/[0.06] px-4 py-3 space-y-2">
                          {account.channels.map((ch, ci) => (
                            <div
                              key={`ch-${key}-${ci}`}
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
                          ))}
                        </div>
                      )}
                    </Card>
                  );
                })}
              </div>
            </div>
          );
        })}

        {(!data?.accounts || data.accounts.length === 0) && (
          <Card className="p-8 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <p className="text-center text-white/40 text-sm">Nenhuma conta Adsense encontrada</p>
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
