import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { TrendingUp, TrendingDown, DollarSign, Receipt, Calculator, Wallet } from 'lucide-react';
import { FinanceiroOverview, TaxaCambio, financeiroApi } from '@/services/financeiroApi';
import { Skeleton } from '@/components/ui/skeleton';

interface FinanceiroOverviewCardsProps {
  data: FinanceiroOverview | null;
  isLoading: boolean;
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
  }).format(value);
};

const formatPercent = (value: number) => {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
};

export function FinanceiroOverviewCards({ data, isLoading }: FinanceiroOverviewCardsProps) {
  const [taxaCambio, setTaxaCambio] = useState<TaxaCambio | null>(null);

  const loadTaxaCambio = useCallback(async () => {
    try {
      const taxaData = await financeiroApi.getTaxaCambio();
      setTaxaCambio(taxaData);
    } catch (error) {
    }
  }, []);

  useEffect(() => {
    loadTaxaCambio();
    // Auto-refresh every 5 minutes
    const interval = setInterval(loadTaxaCambio, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadTaxaCambio]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="bg-card border-0">
            <CardContent className="p-4">
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-8 w-32 mb-2" />
              <Skeleton className="h-4 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: 'Receita Bruta',
      value: data?.receita_bruta || 0,
      variation: data?.receita_variacao || 0,
      icon: DollarSign,
      gradient: 'from-green-500 to-emerald-600',
      bgGlow: 'shadow-green-500/20',
    },
    {
      title: 'Despesas Totais',
      value: data?.despesas_totais || 0,
      variation: data?.despesas_variacao || 0,
      icon: Receipt,
      gradient: 'from-red-500 to-rose-600',
      bgGlow: 'shadow-red-500/20',
      invertVariation: true,
    },
    {
      title: 'Taxas (3%)',
      value: data?.taxas_totais || 0,
      variation: data?.receita_variacao || 0, // Taxas follow receita
      icon: Calculator,
      // V3: ORANGE gradient for Taxas
      gradient: 'from-orange-500 to-orange-600',
      bgGlow: 'shadow-orange-500/20',
    },
    {
      title: 'Lucro Líquido',
      value: data?.lucro_liquido || 0,
      variation: data?.lucro_variacao || 0,
      icon: Wallet,
      gradient: 'from-blue-500 to-blue-600',
      bgGlow: 'shadow-blue-500/20',
      showExchangeRate: true,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => {
        const Icon = card.icon;
        const isPositive = card.invertVariation 
          ? card.variation <= 0 
          : card.variation >= 0;
        
        return (
          <Card 
            key={index} 
            className={`relative overflow-hidden border-0 bg-gradient-to-br ${card.gradient} shadow-lg ${card.bgGlow}`}
          >
            <CardContent className="p-4 sm:p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white/80">{card.title}</span>
                <div className="h-8 w-8 rounded-full bg-white/20 flex items-center justify-center">
                  <Icon className="h-4 w-4 text-white" />
                </div>
              </div>
              
              <div className="text-2xl sm:text-3xl font-bold text-white mb-1">
                {formatCurrency(card.value)}
              </div>
              
              {/* V3: Variation + Exchange Rate INLINE for Lucro Líquido */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1">
                  {isPositive ? (
                    <TrendingUp className="h-4 w-4 text-emerald-200" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-200" />
                  )}
                  <span className={`text-sm font-medium ${isPositive ? 'text-emerald-200' : 'text-red-200'}`}>
                    {formatPercent(card.variation)}
                  </span>
                </div>
                
                {/* V3: USD/BRL inline on Lucro card */}
                {card.showExchangeRate && taxaCambio?.taxa && (
                  <div className="text-xs text-white/70">
                    USD/BRL R$ {taxaCambio.taxa.toFixed(2)}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}