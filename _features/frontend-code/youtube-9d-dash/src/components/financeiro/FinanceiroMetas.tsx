import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Meta } from '@/services/financeiroApi';
import { Skeleton } from '@/components/ui/skeleton';
import { Target, Plus, Pencil, Trash2, Loader2, GripVertical } from 'lucide-react';

interface FinanceiroMetasProps {
  metas: Meta[];
  isLoading: boolean;
  onSave: (data: Omit<Meta, 'id' | 'created_at' | 'updated_at' | 'valor_atual' | 'percentual_progresso'>) => Promise<void>;
  onUpdate: (id: number, data: Partial<Meta>) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
  }).format(value);
};

export function FinanceiroMetas({ metas, isLoading, onSave, onUpdate, onDelete }: FinanceiroMetasProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingMeta, setEditingMeta] = useState<Meta | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [orderedMetas, setOrderedMetas] = useState<Meta[]>([]);
  const [draggedId, setDraggedId] = useState<number | null>(null);
  const [dragOverId, setDragOverId] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    tipo: 'receita' as 'receita' | 'despesa' | 'lucro',
    valor_objetivo: '',
    periodo_inicio: '',
    periodo_fim: '',
    ativo: true,
  });

  // Sincroniza orderedMetas com metas quando metas muda
  useEffect(() => {
    setOrderedMetas(metas);
  }, [metas]);

  const handleDragStart = (e: React.DragEvent, id: number) => {
    setDraggedId(id);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, targetId: number) => {
    e.preventDefault();
    if (draggedId === null || draggedId === targetId) return;

    const draggedIndex = orderedMetas.findIndex(m => m.id === draggedId);
    const targetIndex = orderedMetas.findIndex(m => m.id === targetId);

    if (draggedIndex === -1 || targetIndex === -1) return;

    const newOrder = [...orderedMetas];
    const [removed] = newOrder.splice(draggedIndex, 1);
    newOrder.splice(targetIndex, 0, removed);
    
    setOrderedMetas(newOrder);
    setDraggedId(null);
  };

  const handleDragEnd = () => {
    setDraggedId(null);
  };

  const handleEdit = (meta: Meta) => {
    setEditingMeta(meta);
    setFormData({
      nome: meta.nome,
      tipo: meta.tipo,
      valor_objetivo: meta.valor_objetivo.toString(),
      periodo_inicio: meta.periodo_inicio,
      periodo_fim: meta.periodo_fim,
      ativo: meta.ativo,
    });
    setModalOpen(true);
  };

  const handleAdd = () => {
    setEditingMeta(null);
    setFormData({
      nome: '',
      tipo: 'receita',
      valor_objetivo: '',
      periodo_inicio: new Date().toISOString().split('T')[0],
      periodo_fim: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      ativo: true,
    });
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!formData.nome || !formData.valor_objetivo) return;
    
    setIsSaving(true);
    try {
      const data = {
        nome: formData.nome,
        tipo: formData.tipo,
        valor_objetivo: parseFloat(formData.valor_objetivo),
        periodo_inicio: formData.periodo_inicio,
        periodo_fim: formData.periodo_fim,
        ativo: formData.ativo,
      };
      
      if (editingMeta) {
        await onUpdate(editingMeta.id, data);
      } else {
        await onSave(data);
      }
      setModalOpen(false);
    } finally {
      setIsSaving(false);
    }
  };

  // Calcula o percentual real baseado em valor_atual / valor_objetivo
  const calcularPercentual = (meta: Meta) => {
    const atual = meta.valor_atual || 0;
    const objetivo = meta.valor_objetivo || 1;
    return (atual / objetivo) * 100;
  };

  // Retorna as cores do card baseado no percentual
  const getCardColors = (percentual: number) => {
    if (percentual >= 60) {
      return {
        bg: 'bg-gradient-to-r from-emerald-500/20 to-green-600/20',
        border: 'border-emerald-500/40',
        progressBg: 'bg-emerald-500',
        textColor: 'text-emerald-400',
      };
    }
    if (percentual >= 30) {
      return {
        bg: 'bg-gradient-to-r from-amber-500/20 to-orange-600/20',
        border: 'border-amber-500/40',
        progressBg: 'bg-amber-500',
        textColor: 'text-amber-400',
      };
    }
    return {
      bg: 'bg-gradient-to-r from-red-500/20 to-rose-600/20',
      border: 'border-red-500/40',
      progressBg: 'bg-red-500',
      textColor: 'text-red-400',
    };
  };

  const getTipoLabel = (tipo: string) => {
    switch (tipo) {
      case 'receita': return 'Receita';
      case 'despesa': return 'Despesa';
      case 'lucro': return 'Lucro';
      default: return tipo;
    }
  };

  if (isLoading) {
    return (
      <Card className="bg-card border-border/50">
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className="bg-card border-border/50 h-full">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Target className="h-4 w-4 text-emerald-500" />
              Metas
            </CardTitle>
            <Button
              size="sm"
              onClick={handleAdd}
              className="h-7 text-xs bg-emerald-600 hover:bg-emerald-700"
            >
              <Plus className="h-3 w-3 mr-1" />
              Nova
            </Button>
          </div>
        </CardHeader>
        
        <CardContent>
          {orderedMetas.length === 0 ? (
            <div className="flex flex-col items-center justify-center text-muted-foreground py-8">
              <Target className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-sm">Nenhuma meta definida</p>
            </div>
          ) : (
            <div className="space-y-3">
              {orderedMetas.map((meta) => {
                const percentual = calcularPercentual(meta);
                const colors = getCardColors(percentual);
                const isDragging = draggedId === meta.id;
                
                return (
                  <div
                    key={meta.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, meta.id)}
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(e, meta.id)}
                    onDragEnd={handleDragEnd}
                    className={`p-3 rounded-lg border ${colors.bg} ${colors.border} transition-all cursor-grab active:cursor-grabbing ${isDragging ? 'opacity-50 scale-95' : ''}`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <GripVertical className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-sm text-white truncate">{meta.nome}</span>
                            <Badge variant="outline" className="text-[10px] flex-shrink-0">
                              {getTipoLabel(meta.tipo)}
                            </Badge>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {formatCurrency(meta.valor_atual || 0)} de {formatCurrency(meta.valor_objetivo)}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-0.5 flex-shrink-0">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => handleEdit(meta)}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-muted-foreground hover:text-red-500"
                          onClick={() => onDelete(meta.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Progress 
                        value={Math.min(percentual, 100)} 
                        className="flex-1 h-2"
                        indicatorClassName={colors.progressBg}
                      />
                      <span className={`text-sm font-bold min-w-[45px] text-right ${colors.textColor}`}>
                        {percentual.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingMeta ? 'Editar Meta' : 'Nova Meta'}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Nome</Label>
              <Input
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                placeholder="Ex: Meta de Receita Mensal"
              />
            </div>

            <div className="space-y-2">
              <Label>Tipo</Label>
              <Select
                value={formData.tipo}
                onValueChange={(value: 'receita' | 'despesa' | 'lucro') => setFormData({ ...formData, tipo: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="receita">Receita</SelectItem>
                  <SelectItem value="despesa">Despesa</SelectItem>
                  <SelectItem value="lucro">Lucro</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Valor Objetivo (R$)</Label>
              <Input
                type="number"
                min="0"
                step="0.01"
                value={formData.valor_objetivo}
                onChange={(e) => setFormData({ ...formData, valor_objetivo: e.target.value })}
                placeholder="0,00"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Início</Label>
                <Input
                  type="date"
                  value={formData.periodo_inicio}
                  onChange={(e) => setFormData({ ...formData, periodo_inicio: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Fim</Label>
                <Input
                  type="date"
                  value={formData.periodo_fim}
                  onChange={(e) => setFormData({ ...formData, periodo_fim: e.target.value })}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setModalOpen(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleSave} 
              disabled={isSaving}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {editingMeta ? 'Salvar' : 'Criar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
