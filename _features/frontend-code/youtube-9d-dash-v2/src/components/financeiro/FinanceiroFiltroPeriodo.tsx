import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Calendar, Scale, FolderOpen, Check } from 'lucide-react';
import { PeriodoFinanceiro, financeiroApi, Taxa } from '@/services/financeiroApi';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';

interface FinanceiroFiltroPeriodoProps {
  periodo: PeriodoFinanceiro;
  onPeriodoChange: (periodo: PeriodoFinanceiro) => void;
}

const periodos: { value: PeriodoFinanceiro; label: string }[] = [
  { value: '7d', label: 'Últimos 7 dias' },
  { value: '15d', label: 'Últimos 15 dias' },
  { value: '30d', label: 'Últimos 30 dias' },
  { value: 'all', label: 'Todo Período' },
];

const getPeriodoLabel = (periodo: PeriodoFinanceiro) => {
  const found = periodos.find(p => p.value === periodo);
  if (found) return found.label;
  // Custom period
  if (periodo.includes(',')) {
    const [start, end] = periodo.split(',');
    return `${formatDateDisplay(start)} - ${formatDateDisplay(end)}`;
  }
  return periodo;
};

const formatDateDisplay = (dateStr: string) => {
  const date = new Date(dateStr + 'T12:00:00');
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
};

export function FinanceiroFiltroPeriodo({ periodo, onPeriodoChange }: FinanceiroFiltroPeriodoProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const [modalPeriodoOpen, setModalPeriodoOpen] = useState(false);
  const [modalTaxasOpen, setModalTaxasOpen] = useState(false);
  const [modalCustomOpen, setModalCustomOpen] = useState(false);
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [novaTaxa, setNovaTaxa] = useState({ nome: '', percentual: 3, aplica_sobre: 'receita' });

  // Taxas query
  const { data: taxasData } = useQuery({
    queryKey: ['financeiro-taxas'],
    queryFn: () => financeiroApi.getTaxas(),
  });

  const createTaxaMutation = useMutation({
    mutationFn: financeiroApi.createTaxa,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financeiro-taxas'] });
      toast({ title: 'Taxa criada com sucesso!' });
      setNovaTaxa({ nome: '', percentual: 3, aplica_sobre: 'receita' });
    },
    onError: () => {
      toast({ title: 'Erro ao criar taxa', variant: 'destructive' });
    },
  });

  const deleteTaxaMutation = useMutation({
    mutationFn: financeiroApi.deleteTaxa,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financeiro-taxas'] });
      toast({ title: 'Taxa excluída!' });
    },
  });

  const handleSelectPeriodo = (value: PeriodoFinanceiro) => {
    onPeriodoChange(value);
    setModalPeriodoOpen(false);
  };

  const handleCustomPeriodo = () => {
    if (customStart && customEnd) {
      onPeriodoChange(`${customStart},${customEnd}`);
      setModalCustomOpen(false);
      setModalPeriodoOpen(false);
    }
  };

  const handleExportCSV = () => {
    financeiroApi.exportCSV(periodo);
  };

  return (
    <>
      {/* Header: 💲 Financeiro + icons with colors */}
      <div className="flex items-center justify-between w-full mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-2">
            <span className="text-4xl">💲</span>
            <span>Financeiro</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1">{getPeriodoLabel(periodo)}</p>
        </div>
        
        {/* Icons: Calendar (blue), Scale (orange), FolderOpen (green) */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setModalPeriodoOpen(true)}
            title="Período"
            className="h-10 w-10 bg-blue-500/15 border-blue-500/30 hover:bg-blue-500/25 hover:border-blue-500/50"
          >
            <Calendar className="h-5 w-5 text-blue-400" />
          </Button>
          
          <Button
            variant="outline"
            size="icon"
            onClick={() => setModalTaxasOpen(true)}
            title="Gerenciar Taxas"
            className="h-10 w-10 bg-orange-500/15 border-orange-500/30 hover:bg-orange-500/25 hover:border-orange-500/50"
          >
            <Scale className="h-5 w-5 text-orange-400" />
          </Button>
          
          <Button
            variant="outline"
            size="icon"
            onClick={handleExportCSV}
            title="Exportar CSV"
            className="h-10 w-10 bg-green-500/15 border-green-500/30 hover:bg-green-500/25 hover:border-green-500/50"
          >
            <FolderOpen className="h-5 w-5 text-green-400" />
          </Button>
        </div>
      </div>

      {/* Modal Período */}
      <Dialog open={modalPeriodoOpen} onOpenChange={setModalPeriodoOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Selecionar Período</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-2 py-4">
            {periodos.map((p) => (
              <Button
                key={p.value}
                variant={periodo === p.value ? 'default' : 'outline'}
                className={`w-full justify-between ${
                  periodo === p.value 
                    ? 'bg-emerald-600 hover:bg-emerald-700 text-white' 
                    : ''
                }`}
                onClick={() => handleSelectPeriodo(p.value)}
              >
                <span>{p.label}</span>
                {periodo === p.value && <Check className="h-4 w-4" />}
              </Button>
            ))}
            
            <Button
              variant="outline"
              className="w-full"
              onClick={() => {
                setModalCustomOpen(true);
                setModalPeriodoOpen(false);
              }}
            >
              Período Customizado
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal Custom Period */}
      <Dialog open={modalCustomOpen} onOpenChange={setModalCustomOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Período Customizado</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label>Data Início</Label>
              <Input
                type="date"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
              />
            </div>
            <div>
              <Label>Data Fim</Label>
              <Input
                type="date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
              />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setModalCustomOpen(false)}>
                Cancelar
              </Button>
              <Button onClick={handleCustomPeriodo}>
                Aplicar
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal Taxas */}
      <Dialog open={modalTaxasOpen} onOpenChange={setModalTaxasOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Gerenciar Taxas</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Lista de taxas existentes */}
            <div className="space-y-2 max-h-[200px] overflow-y-auto">
              {taxasData?.taxas?.map((taxa) => (
                <div key={taxa.id} className="flex items-center justify-between p-2 rounded bg-muted/30">
                  <div>
                    <span className="text-sm font-medium">{taxa.nome}</span>
                    <span className="text-xs text-muted-foreground ml-2">
                      {taxa.percentual}% sobre {taxa.aplica_sobre}
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-500 hover:text-red-600"
                    onClick={() => deleteTaxaMutation.mutate(taxa.id)}
                  >
                    Excluir
                  </Button>
                </div>
              ))}
              {(!taxasData?.taxas || taxasData.taxas.length === 0) && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Nenhuma taxa cadastrada
                </p>
              )}
            </div>
            
            {/* Adicionar nova taxa */}
            <div className="border-t pt-4 space-y-3">
              <h4 className="text-sm font-semibold">Adicionar Nova Taxa</h4>
              <div>
                <Label>Nome</Label>
                <Input
                  value={novaTaxa.nome}
                  onChange={(e) => setNovaTaxa({ ...novaTaxa, nome: e.target.value })}
                  placeholder="Ex: Taxa YouTube"
                />
              </div>
              <div>
                <Label>Percentual (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={novaTaxa.percentual}
                  onChange={(e) => setNovaTaxa({ ...novaTaxa, percentual: parseFloat(e.target.value) })}
                />
              </div>
              <Button 
                className="w-full"
                onClick={() => createTaxaMutation.mutate({
                  ...novaTaxa,
                  ativo: true,
                })}
                disabled={!novaTaxa.nome}
              >
                Adicionar Taxa
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
