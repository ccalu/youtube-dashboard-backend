import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ComparacaoMensal } from '@/services/financeiroApi';
import { BarChart3 } from 'lucide-react';

interface FinanceiroComparacaoCardProps {
  data: ComparacaoMensal | null;
  isLoading: boolean;
}

const formatCurrency = (value: number) => {
  if (value >= 1000) {
    return `R$ ${(value / 1000).toFixed(1)}k`;
  }
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
  }).format(value);
};

export function FinanceiroComparacaoCard({ data, isLoading }: FinanceiroComparacaoCardProps) {
  if (isLoading) {
    return (
      <Card className="bg-card border-border/50 h-full">
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Filtrar meses a partir de Outubro 2024 e mostrar apenas últimos 6 meses
  const mesesFiltrados = (() => {
    const mesesValidos = data?.meses?.filter(m => {
      const [ano, mes] = m.mes.split('-').map(Number);
      return (ano === 2024 && mes >= 10) || ano > 2024;
    }) || [];
    
    // Mostrar apenas os últimos 6 meses (mais recentes)
    return mesesValidos.slice(-6);
  })();

  if (!data || mesesFiltrados.length === 0) {
    return (
      <Card className="bg-card border-border/50 h-full">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart3 className="h-4 w-4 text-blue-500" />
            Comparação Mês a Mês
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-muted-foreground text-sm">
            Carregando comparação...
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border/50 h-full">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <BarChart3 className="h-4 w-4 text-blue-500" />
          Comparação Mês a Mês
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b-2 border-border">
                <th className="text-left py-2 px-2 text-muted-foreground font-medium bg-muted/20">Mês</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium bg-muted/20">Receita</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium bg-muted/20">Despesas</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium bg-muted/20">Lucro</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium bg-muted/20">Var.</th>
              </tr>
            </thead>
            <tbody>
              {mesesFiltrados.map((m, idx) => (
                <tr 
                  key={idx} 
                  className="border-b border-border/50 hover:bg-muted/20 transition-colors"
                >
                  <td className="py-2.5 px-2 text-white font-medium border-r border-border/30">{m.mes_nome}</td>
                  <td className="text-right py-2.5 px-2 text-green-400 border-r border-border/30">
                    {formatCurrency(m.receita)}
                  </td>
                  <td className="text-right py-2.5 px-2 text-red-400 border-r border-border/30">
                    {formatCurrency(m.despesas)}
                  </td>
                  <td className="text-right py-2.5 px-2 text-blue-400 font-medium border-r border-border/30">
                    {formatCurrency(m.lucro)}
                  </td>
                  <td className="text-right py-2.5 px-2">
                    {m.variacao !== null ? (
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        m.variacao >= 0 
                          ? 'bg-green-500/20 text-green-400' 
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {m.variacao >= 0 ? '+' : ''}{m.variacao.toFixed(0)}%
                      </span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
