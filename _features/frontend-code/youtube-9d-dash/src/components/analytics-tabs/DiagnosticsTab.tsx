import React from 'react';
import { Channel } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  AlertTriangle, 
  CheckCircle, 
  TrendingDown, 
  TrendingUp, 
  Lightbulb,
  Activity
} from 'lucide-react';

interface DiagnosticsTabProps {
  canal: Channel;
}

interface Diagnostic {
  type: 'success' | 'warning' | 'danger';
  title: string;
  description: string;
  icon: React.ReactNode;
}

export const DiagnosticsTab: React.FC<DiagnosticsTabProps> = ({ canal }) => {
  const generateDiagnostics = (): Diagnostic[] => {
    const diagnostics: Diagnostic[] = [];

    // Growth Analysis
    const growth7d = canal.growth_7d ?? 0;
    const growth30d = canal.growth_30d ?? 0;

    if (growth7d < -10) {
      diagnostics.push({
        type: 'danger',
        title: 'Queda Acentuada de Views (7d)',
        description: `O canal teve uma queda de ${Math.abs(growth7d).toFixed(1)}% nos últimos 7 dias. Verifique se há problemas com conteúdo recente.`,
        icon: <TrendingDown className="h-5 w-5" />,
      });
    } else if (growth7d < 0) {
      diagnostics.push({
        type: 'warning',
        title: 'Leve Queda de Views (7d)',
        description: `O canal teve uma queda de ${Math.abs(growth7d).toFixed(1)}% nos últimos 7 dias. Considere analisar os últimos vídeos.`,
        icon: <TrendingDown className="h-5 w-5" />,
      });
    } else if (growth7d > 20) {
      diagnostics.push({
        type: 'success',
        title: 'Crescimento Excepcional (7d)',
        description: `O canal cresceu ${growth7d.toFixed(1)}% nos últimos 7 dias! Identifique o que está funcionando.`,
        icon: <TrendingUp className="h-5 w-5" />,
      });
    }

    // 30d Growth
    if (growth30d < -20) {
      diagnostics.push({
        type: 'danger',
        title: 'Tendência Negativa (30d)',
        description: `Queda de ${Math.abs(growth30d).toFixed(1)}% no mês. Pode ser necessário revisar a estratégia de conteúdo.`,
        icon: <TrendingDown className="h-5 w-5" />,
      });
    } else if (growth30d > 30) {
      diagnostics.push({
        type: 'success',
        title: 'Crescimento Consistente (30d)',
        description: `Crescimento de ${growth30d.toFixed(1)}% no mês. O canal está em ótima trajetória!`,
        icon: <TrendingUp className="h-5 w-5" />,
      });
    }

    // Engagement Analysis
    const engagement = canal.engagement_rate ?? 0;
    if (engagement < 1) {
      diagnostics.push({
        type: 'warning',
        title: 'Engajamento Baixo',
        description: 'Taxa de engajamento abaixo de 1%. Considere melhorar CTAs e interação com audiência.',
        icon: <Activity className="h-5 w-5" />,
      });
    } else if (engagement > 5) {
      diagnostics.push({
        type: 'success',
        title: 'Excelente Engajamento',
        description: `Taxa de engajamento de ${engagement.toFixed(2)}%! A audiência está altamente envolvida.`,
        icon: <Activity className="h-5 w-5" />,
      });
    }

    // Video frequency
    const videosWeek = canal.videos_publicados_7d ?? 0;
    if (videosWeek === 0) {
      diagnostics.push({
        type: 'warning',
        title: 'Sem Uploads Recentes',
        description: 'Nenhum vídeo publicado nos últimos 7 dias. Consistência é importante para o algoritmo.',
        icon: <AlertTriangle className="h-5 w-5" />,
      });
    } else if (videosWeek >= 7) {
      diagnostics.push({
        type: 'success',
        title: 'Alta Frequência de Upload',
        description: `${videosWeek} vídeos nos últimos 7 dias. Excelente consistência!`,
        icon: <CheckCircle className="h-5 w-5" />,
      });
    }

    // Score Analysis
    const score = canal.score_calculado ?? 0;
    if (score < 40) {
      diagnostics.push({
        type: 'danger',
        title: 'Score Baixo',
        description: 'O score geral do canal está baixo. Foque em melhorar métricas principais.',
        icon: <AlertTriangle className="h-5 w-5" />,
      });
    } else if (score >= 80) {
      diagnostics.push({
        type: 'success',
        title: 'Score Excelente',
        description: 'O canal está performando muito bem em todas as métricas!',
        icon: <CheckCircle className="h-5 w-5" />,
      });
    }

    // If no issues found
    if (diagnostics.length === 0) {
      diagnostics.push({
        type: 'success',
        title: 'Canal Saudável',
        description: 'Não foram identificados problemas significativos. Continue monitorando as métricas.',
        icon: <CheckCircle className="h-5 w-5" />,
      });
    }

    return diagnostics;
  };

  const diagnostics = generateDiagnostics();

  const getTypeStyles = (type: Diagnostic['type']) => {
    switch (type) {
      case 'success':
        return {
          border: 'border-green-500',
          bg: 'bg-green-500/10',
          text: 'text-green-500',
        };
      case 'warning':
        return {
          border: 'border-yellow-500',
          bg: 'bg-yellow-500/10',
          text: 'text-yellow-500',
        };
      case 'danger':
        return {
          border: 'border-red-500',
          bg: 'bg-red-500/10',
          text: 'text-red-500',
        };
    }
  };

  return (
    <div className="space-y-4 fade-in">
      {/* Header */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Lightbulb className="h-4 w-4" />
            Diagnóstico do Canal
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Análise automática baseada nas métricas do canal. 
            Identificamos pontos de atenção e oportunidades de melhoria.
          </p>
        </CardContent>
      </Card>

      {/* Diagnostics List */}
      <div className="space-y-3">
        {diagnostics.map((diagnostic, index) => {
          const styles = getTypeStyles(diagnostic.type);
          return (
            <Card key={index} className={`border-l-4 ${styles.border}`}>
              <CardContent className="pt-4">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-full ${styles.bg}`}>
                    <div className={styles.text}>{diagnostic.icon}</div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-foreground">{diagnostic.title}</h4>
                      <Badge 
                        variant={diagnostic.type === 'success' ? 'default' : 'secondary'}
                        className={`text-xs ${
                          diagnostic.type === 'danger' ? 'bg-red-500' :
                          diagnostic.type === 'warning' ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`}
                      >
                        {diagnostic.type === 'success' ? 'OK' : 
                         diagnostic.type === 'warning' ? 'Atenção' : 'Crítico'}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {diagnostic.description}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
