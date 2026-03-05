import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { BreakdownCategoria, Lancamento, Categoria } from '@/services/financeiroApi';
import { Skeleton } from '@/components/ui/skeleton';
import { Receipt, Plus, Edit, Trash2 } from 'lucide-react';

interface FinanceiroDespesasCardProps {
  despesas: Lancamento[];
  breakdown: BreakdownCategoria[];
  categorias: Categoria[];
  isLoading: boolean;
  onAddDespesa: (data: {
    categoria_id: number;
    valor: number;
    data: string;
    descricao: string;
    tipo: 'despesa';
    recorrencia: 'fixa' | 'unica';
  }) => Promise<void>;
  onEditDespesa: (id: number, data: Partial<Lancamento>) => Promise<void>;
  onDeleteDespesa: (id: number) => Promise<void>;
  onCreateCategoria: (data: Omit<Categoria, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
  }).format(value);
};

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr + 'T12:00:00');
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
};

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-2 shadow-xl">
        <p className="text-white font-medium text-sm">{data.categoria || data.nome}</p>
        <p className="text-slate-300 text-xs">{formatCurrency(data.valor)}</p>
        <p className="text-slate-400 text-[10px]">{data.percentual?.toFixed(1)}%</p>
      </div>
    );
  }
  return null;
};

export function FinanceiroDespesasCard({ 
  despesas, 
  breakdown, 
  categorias,
  isLoading, 
  onAddDespesa,
  onEditDespesa,
  onDeleteDespesa,
  onCreateCategoria,
}: FinanceiroDespesasCardProps) {
  const [modalDespesaOpen, setModalDespesaOpen] = useState(false);
  const [modalCategoriaOpen, setModalCategoriaOpen] = useState(false);
  const [editingDespesa, setEditingDespesa] = useState<Lancamento | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  
  const [formData, setFormData] = useState({
    categoria_id: '',
    valor: '',
    data: new Date().toISOString().split('T')[0],
    descricao: '',
    recorrencia: 'unica' as 'fixa' | 'unica',
  });
  
  const [novaCategoria, setNovaCategoria] = useState({
    nome: '',
    cor: '#FF5733',
  });

  const despesaCategorias = categorias.filter(c => c.tipo === 'despesa' && c.ativo);

  const resetForm = () => {
    setFormData({
      categoria_id: '',
      valor: '',
      data: new Date().toISOString().split('T')[0],
      descricao: '',
      recorrencia: 'unica',
    });
    setEditingDespesa(null);
  };

  const handleOpenAdd = () => {
    resetForm();
    setModalDespesaOpen(true);
  };

  const handleOpenEdit = (desp: Lancamento) => {
    setEditingDespesa(desp);
    setFormData({
      categoria_id: desp.categoria_id.toString(),
      valor: desp.valor.toString(),
      data: desp.data,
      descricao: desp.descricao,
      recorrencia: desp.recorrencia || 'unica',
    });
    setModalDespesaOpen(true);
  };

  const handleSave = async () => {
    if (!formData.categoria_id || !formData.valor) return;
    
    setIsSaving(true);
    try {
      if (editingDespesa) {
        await onEditDespesa(editingDespesa.id, {
          categoria_id: parseInt(formData.categoria_id),
          valor: parseFloat(formData.valor),
          data: formData.data,
          descricao: formData.descricao,
          recorrencia: formData.recorrencia,
        });
      } else {
        await onAddDespesa({
          categoria_id: parseInt(formData.categoria_id),
          valor: parseFloat(formData.valor),
          data: formData.data,
          descricao: formData.descricao,
          tipo: 'despesa',
          recorrencia: formData.recorrencia,
        });
      }
      setModalDespesaOpen(false);
      resetForm();
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateCategoria = async () => {
    if (!novaCategoria.nome) return;
    
    await onCreateCategoria({
      nome: novaCategoria.nome,
      tipo: 'despesa',
      cor: novaCategoria.cor,
      ativo: true,
    });
    setModalCategoriaOpen(false);
    setNovaCategoria({ nome: '', cor: '#FF5733' });
  };

  if (isLoading) {
    return (
      <Card className="bg-card border-border/50 h-full">
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-24" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const totalDespesas = despesas.reduce((acc, d) => acc + d.valor, 0);

  return (
    <>
      <Card className="bg-card border-border/50 h-full">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Receipt className="h-4 w-4 text-red-500" />
            Despesas
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={handleOpenAdd}
            className="h-7 gap-1 text-xs"
          >
            <Plus className="h-3 w-3" />
            <span className="hidden sm:inline">Adicionar</span>
          </Button>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Layout Principal: Lista + Gráfico lado a lado */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Lista de Despesas */}
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-muted-foreground uppercase">Últimas Despesas</h4>
              <div className="space-y-1.5 max-h-[200px] overflow-y-auto pr-1">
                {despesas.length === 0 ? (
                  <div className="flex flex-col items-center justify-center text-muted-foreground py-6">
                    <Receipt className="h-8 w-8 mb-2 opacity-30" />
                    <p className="text-xs">Nenhuma despesa</p>
                  </div>
                ) : (
                  despesas.slice(0, 8).map((desp) => (
                    <div 
                      key={desp.id} 
                      className="flex items-center justify-between py-2 px-3 rounded-lg bg-muted/20 border border-border/30 hover:bg-muted/30 transition-colors"
                    >
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        {desp.financeiro_categorias?.cor && (
                          <div 
                            className="w-3 h-3 rounded-full flex-shrink-0"
                            style={{ backgroundColor: desp.financeiro_categorias.cor }}
                          />
                        )}
                        <div className="min-w-0 flex-1">
                          <p className="text-xs text-white truncate font-medium">
                            {desp.descricao || desp.financeiro_categorias?.nome || 'Sem descrição'}
                          </p>
                          <p className="text-[10px] text-muted-foreground">
                            {formatDate(desp.data)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-bold text-red-400 whitespace-nowrap">
                          {formatCurrency(desp.valor)}
                        </span>
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="h-6 w-6 opacity-50 hover:opacity-100"
                          onClick={() => handleOpenEdit(desp)}
                        >
                          <Edit className="h-3 w-3" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="h-6 w-6 text-red-500 opacity-50 hover:opacity-100"
                          onClick={() => onDeleteDespesa(desp.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Gráfico de Pizza por Categoria */}
            {breakdown.length > 0 && (
              <div className="flex flex-col">
                <h4 className="text-xs font-medium text-muted-foreground uppercase mb-2">Por Categoria</h4>
                <div className="flex-1 flex items-center">
                  <div className="h-[160px] w-[140px] flex-shrink-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={breakdown}
                          cx="50%"
                          cy="50%"
                          innerRadius={35}
                          outerRadius={60}
                          paddingAngle={2}
                          dataKey="valor"
                          nameKey="categoria"
                        >
                          {breakdown.map((entry, index) => (
                            <Cell 
                              key={`cell-${index}`} 
                              fill={entry.cor || `hsl(${index * 45}, 70%, 50%)`}
                              strokeWidth={0}
                            />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  {/* Legenda */}
                  <div className="flex-1 space-y-1.5 pl-2">
                    {breakdown.slice(0, 6).map((item, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs">
                        <div 
                          className="w-3 h-3 rounded flex-shrink-0"
                          style={{ backgroundColor: item.cor || `hsl(${idx * 45}, 70%, 50%)` }}
                        />
                        <span className="truncate text-muted-foreground flex-1">{item.categoria}</span>
                        <span className="text-white font-medium">{item.percentual?.toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Total Destacado */}
          <div className="bg-gradient-to-r from-red-500/25 to-rose-600/25 border-2 border-red-500/50 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-medium text-red-300 uppercase">Total do Período</span>
                <p className="text-[10px] text-red-400/70">{despesas.length} despesa(s)</p>
              </div>
              <span className="text-2xl font-bold text-red-400">
                {formatCurrency(totalDespesas)}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Modal Adicionar/Editar Despesa */}
      <Dialog open={modalDespesaOpen} onOpenChange={setModalDespesaOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingDespesa ? 'Editar Despesa' : 'Adicionar Despesa'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Categoria</Label>
              <div className="flex gap-2">
                <Select 
                  value={formData.categoria_id} 
                  onValueChange={(v) => setFormData({...formData, categoria_id: v})}
                >
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Selecione..." />
                  </SelectTrigger>
                  <SelectContent>
                    {despesaCategorias.map((cat) => (
                      <SelectItem key={cat.id} value={cat.id.toString()}>
                        {cat.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setModalCategoriaOpen(true)}
                  title="Nova Categoria"
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div>
              <Label>Valor (R$)</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.valor}
                onChange={(e) => setFormData({...formData, valor: e.target.value})}
                placeholder="0,00"
              />
            </div>

            <div>
              <Label>Data</Label>
              <Input
                type="date"
                value={formData.data}
                onChange={(e) => setFormData({...formData, data: e.target.value})}
              />
            </div>

            <div>
              <Label>Descrição</Label>
              <Input
                value={formData.descricao}
                onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                placeholder="Ex: Assinatura Lovable"
              />
            </div>

            <div>
              <Label>Recorrência</Label>
              <Select 
                value={formData.recorrencia} 
                onValueChange={(v: 'fixa' | 'unica') => setFormData({...formData, recorrencia: v})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unica">Única</SelectItem>
                  <SelectItem value="fixa">Fixa (mensal)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setModalDespesaOpen(false)}>
                Cancelar
              </Button>
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? 'Salvando...' : 'Salvar'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal Nova Categoria */}
      <Dialog open={modalCategoriaOpen} onOpenChange={setModalCategoriaOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Nova Categoria</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Nome</Label>
              <Input
                value={novaCategoria.nome}
                onChange={(e) => setNovaCategoria({...novaCategoria, nome: e.target.value})}
                placeholder="Ex: Marketing"
              />
            </div>
            <div>
              <Label>Cor</Label>
              <Input
                type="color"
                value={novaCategoria.cor}
                onChange={(e) => setNovaCategoria({...novaCategoria, cor: e.target.value})}
                className="h-10"
              />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setModalCategoriaOpen(false)}>
                Cancelar
              </Button>
              <Button onClick={handleCreateCategoria} disabled={!novaCategoria.nome}>
                Criar
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
