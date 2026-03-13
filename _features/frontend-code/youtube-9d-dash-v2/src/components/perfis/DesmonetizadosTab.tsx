import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, ArrowRightLeft, RefreshCw, ShieldX } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Demonetization {
  conta: string;
  channel_name: string;
  date_demonetized: string;
  date_reapply: string;
  reason: string;
  status: string;
}

interface Transfer {
  conta: string;
  channel_name: string;
  new_email: string;
  new_password: string;
  date_new_owner: string;
  date_transfer: string;
  status: string;
  became: string;
}

interface DesmonetizadosData {
  demonetizations: Demonetization[];
  transfers: Transfer[];
  stats: {
    total_demonetized: number;
    reasons: Record<string, number>;
    transfers_done: number;
    transfers_waiting: number;
    transfers_todo: number;
  };
  cached_at: string;
}

const fetchDesmonetizados = async (): Promise<DesmonetizadosData> => {
  const res = await fetch('/api/perfis/desmonetizados');
  if (!res.ok) throw new Error('Erro ao carregar dados de desmonetizados');
  return res.json();
};

const reasonBadge = (reason: string) => {
  switch (reason) {
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
    default:
      return (
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-white/[0.06] text-white/50 border border-white/[0.08]">
          {reason}
        </span>
      );
  }
};

const transferStatusBadge = (status: string) => {
  switch (status) {
    case 'done':
      return (
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
          done
        </span>
      );
    case 'waiting':
      return (
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
          waiting
        </span>
      );
    case 'to do':
      return (
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30">
          to do
        </span>
      );
    default:
      return (
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-white/[0.06] text-white/50 border border-white/[0.08]">
          {status}
        </span>
      );
  }
};

export function DesmonetizadosTab() {
  const { data, isLoading, isError, error, refetch } = useQuery<DesmonetizadosData>({
    queryKey: ['perfis-desmonetizados'],
    queryFn: fetchDesmonetizados,
  });

  const [copiedField, setCopiedField] = useState<string | null>(null);

  const handleCopy = (text: string, fieldId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldId);
    setTimeout(() => setCopiedField(null), 2000);
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
            {[1, 2, 3, 4].map((i) => (
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
  const transfersPending = (stats?.transfers_waiting ?? 0) + (stats?.transfers_todo ?? 0);

  return (
    <div className="space-y-4">
      {/* Stat Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-xs text-white/60 mb-1">Total Desmonetizados</p>
          <div className="flex items-center gap-2">
            <ShieldX className="w-4 h-4 text-red-400" />
            <span className="text-2xl font-bold text-white/90">{stats?.total_demonetized ?? 0}</span>
          </div>
        </Card>
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-xs text-white/60 mb-2">Por Motivo</p>
          <div className="flex flex-wrap gap-1.5">
            {stats?.reasons &&
              Object.entries(stats.reasons).map(([reason, count]) => (
                <span key={reason} className="text-xs">
                  {reasonBadge(reason)}{' '}
                  <span className="text-white/50 ml-0.5">{count}</span>
                </span>
              ))}
          </div>
        </Card>
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-xs text-white/60 mb-1">Transfers Pendentes</p>
          <div className="flex items-center gap-2">
            <ArrowRightLeft className="w-4 h-4 text-yellow-400" />
            <span className="text-2xl font-bold text-yellow-400">{transfersPending}</span>
          </div>
        </Card>
      </div>

      {/* Demonetization History Table */}
      <div>
        <h3 className="text-sm font-medium text-white/90 mb-3 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          Historico de Desmonetizacoes
        </h3>
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Conta</th>
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Nome Canal</th>
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Data Desmonetizacao</th>
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Data Pedir Revisao</th>
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Motivo</th>
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {data?.demonetizations.map((d, i) => (
                <tr
                  key={`demo-${i}`}
                  className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                >
                  <td className="py-2 px-3 text-white/90 font-medium whitespace-nowrap">{d.conta}</td>
                  <td className="py-2 px-3 text-white/70 whitespace-nowrap">{d.channel_name}</td>
                  <td className="py-2 px-3 text-white/60 whitespace-nowrap">{d.date_demonetized}</td>
                  <td className="py-2 px-3 text-white/60 whitespace-nowrap">{d.date_reapply}</td>
                  <td className="py-2 px-3 whitespace-nowrap">{reasonBadge(d.reason)}</td>
                  <td className="py-2 px-3 text-white/60 whitespace-nowrap">{d.status}</td>
                </tr>
              ))}
              {(!data?.demonetizations || data.demonetizations.length === 0) && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-white/40 text-sm">
                    Nenhum registro de desmonetizacao
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      </div>

      {/* Owner Transfer Table */}
      <div>
        <h3 className="text-sm font-medium text-white/90 mb-3 flex items-center gap-2">
          <ArrowRightLeft className="w-4 h-4 text-cyan-400" />
          Troca de Owner
        </h3>
        <Card className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Conta</th>
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Nome Canal</th>
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Gmail Novo</th>
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Data Owner Novo</th>
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Data Troca</th>
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Status</th>
                <th className="text-left py-2 px-3 text-xs text-white/50 font-medium">Virou</th>
              </tr>
            </thead>
            <tbody>
              {data?.transfers.map((t, i) => (
                <tr
                  key={`transfer-${i}`}
                  className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                >
                  <td className="py-2 px-3 text-white/90 font-medium whitespace-nowrap">{t.conta}</td>
                  <td className="py-2 px-3 text-white/70 whitespace-nowrap">{t.channel_name}</td>
                  <td className="py-2 px-3 whitespace-nowrap">
                    <span
                      onClick={() => handleCopy(t.new_email, `transfer-email-${i}`)}
                      className="cursor-pointer hover:text-cyan-400 transition-colors relative text-white/70"
                    >
                      {t.new_email}
                      {copiedField === `transfer-email-${i}` && (
                        <span className="absolute -top-6 left-0 text-xs text-green-400 bg-black/80 px-2 py-1 rounded whitespace-nowrap z-10">
                          Copiado!
                        </span>
                      )}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-white/60 whitespace-nowrap">{t.date_new_owner}</td>
                  <td className="py-2 px-3 text-white/60 whitespace-nowrap">{t.date_transfer}</td>
                  <td className="py-2 px-3 whitespace-nowrap">{transferStatusBadge(t.status)}</td>
                  <td className="py-2 px-3 text-white/60 whitespace-nowrap">{t.became || '-'}</td>
                </tr>
              ))}
              {(!data?.transfers || data.transfers.length === 0) && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-white/40 text-sm">
                    Nenhuma troca de owner registrada
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  );
}
