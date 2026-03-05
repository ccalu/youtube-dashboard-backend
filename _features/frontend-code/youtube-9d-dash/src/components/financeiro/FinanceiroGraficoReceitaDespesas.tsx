import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { GraficoReceitaDespesas } from '@/services/financeiroApi';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp } from 'lucide-react';

interface FinanceiroGraficoReceitaDespesasProps {
  data: GraficoReceitaDespesas[];
  isLoading: boolean;
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
  }).format(value);
};

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr + 'T12:00:00');
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl">
        <p className="text-white font-medium mb-2">{formatDate(label)}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-slate-300">{entry.name}:</span>
            <span className="text-white font-medium">{formatCurrency(entry.value)}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function FinanceiroGraficoReceitaDespesas({ data, isLoading }: FinanceiroGraficoReceitaDespesasProps) {
  // Transformar dados em acumulado para evitar picos de despesas isoladas
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    // Ordenar por data
    const sorted = [...data].sort((a, b) => a.data.localeCompare(b.data));
    
    // Calcular valores acumulados
    let receitaAcumulada = 0;
    let despesasAcumuladas = 0;
    
    return sorted.map(item => {
      receitaAcumulada += item.receita || 0;
      despesasAcumuladas += item.despesas || 0;
      
      return {
        data: item.data,
        receita: receitaAcumulada,
        despesas: despesasAcumuladas,
      };
    });
  }, [data]);

  if (isLoading) {
    return (
      <Card className="bg-card border-border/50 h-full">
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[280px] w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border/50 h-full">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <TrendingUp className="h-4 w-4 text-emerald-500" />
          Receita vs Despesas (Acumulado)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis 
                dataKey="data" 
                tickFormatter={formatDate}
                stroke="#64748b"
                fontSize={11}
                tick={{ fill: '#94a3b8' }}
              />
              <YAxis 
                tickFormatter={(value) => `R$${(value / 1000).toFixed(0)}k`}
                stroke="#64748b"
                fontSize={11}
                tick={{ fill: '#94a3b8' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend 
                wrapperStyle={{ paddingTop: '10px' }}
                formatter={(value) => <span className="text-slate-300 text-xs">{value}</span>}
              />
              <Line 
                type="monotone" 
                dataKey="receita" 
                name="Receita"
                stroke="#10B981" 
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5, fill: '#10B981' }}
              />
              <Line 
                type="monotone" 
                dataKey="despesas" 
                name="Despesas"
                stroke="#EF4444" 
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5, fill: '#EF4444' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
