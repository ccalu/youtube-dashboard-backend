import { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { useQueryClient } from '@tanstack/react-query';

interface DataRefreshButtonProps {
  className?: string;
}

export const DataRefreshButton = ({ className }: DataRefreshButtonProps) => {
  const [isCollecting, setIsCollecting] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const handleCollectData = async () => {
    setIsCollecting(true);
    try {
      toast({
        title: "Iniciando coleta de dados",
        description: "Aguarde enquanto coletamos os dados mais recentes..."
      });

      const response = await fetch('https://youtube-dashboard-backend-production.up.railway.app/api/collect-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Erro na requisição');
      }

      // Invalidar e recarregar os dados
      await queryClient.invalidateQueries({ queryKey: ['channels'] });
      await queryClient.invalidateQueries({ queryKey: ['videos'] });
      await queryClient.invalidateQueries({ queryKey: ['filter-options'] });

      toast({
        title: "Dados atualizados com sucesso!",
        description: "As informações mais recentes foram carregadas."
      });
    } catch (error) {
      toast({
        title: "Erro ao atualizar dados",
        description: "Não foi possível coletar os dados. Tente novamente mais tarde.",
        variant: "destructive"
      });
    } finally {
      setIsCollecting(false);
    }
  };

  return (
    <Button
      onClick={handleCollectData}
      disabled={isCollecting}
      variant="outline"
      className={className}
      size="default"
    >
      <RefreshCw className={`h-4 w-4 ${isCollecting ? 'animate-spin' : ''} sm:mr-2`} />
      <span className="hidden sm:inline">{isCollecting ? 'Coletando...' : 'Atualizar Dados'}</span>
    </Button>
  );
};