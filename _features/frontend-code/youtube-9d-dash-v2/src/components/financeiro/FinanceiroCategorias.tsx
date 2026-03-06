import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Categoria } from '@/services/financeiroApi';
import { Plus, Pencil, Trash2, Loader2, Tags } from 'lucide-react';

interface FinanceiroCategoriasProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  categorias: Categoria[];
  onSave: (data: Omit<Categoria, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  onUpdate: (id: number, data: Partial<Categoria>) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}

const CORES_PREDEFINIDAS = [
  '#10B981', '#EF4444', '#3B82F6', '#8B5CF6', '#F59E0B',
  '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1',
];

export function FinanceiroCategorias({
  open,
  onOpenChange,
  categorias,
  onSave,
  onUpdate,
  onDelete,
}: FinanceiroCategoriasProps) {
  const [editingCategoria, setEditingCategoria] = useState<Categoria | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState({
    nome: '',
    tipo: 'despesa' as 'receita' | 'despesa',
    cor: CORES_PREDEFINIDAS[0],
    icon: '',
    ativo: true,
  });

  const resetForm = () => {
    setEditingCategoria(null);
    setFormData({
      nome: '',
      tipo: 'despesa',
      cor: CORES_PREDEFINIDAS[0],
      icon: '',
      ativo: true,
    });
  };

  const handleEdit = (categoria: Categoria) => {
    setEditingCategoria(categoria);
    setFormData({
      nome: categoria.nome,
      tipo: categoria.tipo,
      cor: categoria.cor,
      icon: categoria.icon || '',
      ativo: categoria.ativo,
    });
  };

  const handleSave = async () => {
    if (!formData.nome) return;
    
    setIsSaving(true);
    try {
      if (editingCategoria) {
        await onUpdate(editingCategoria.id, formData);
      } else {
        await onSave(formData);
      }
      resetForm();
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    await onDelete(id);
  };

  const receitaCategorias = categorias.filter(c => c.tipo === 'receita');
  const despesaCategorias = categorias.filter(c => c.tipo === 'despesa');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Tags className="h-5 w-5 text-emerald-500" />
            Gerenciar Categorias
          </DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Form */}
          <div className="space-y-4 p-4 bg-muted/30 rounded-lg">
            <h3 className="font-medium text-sm">
              {editingCategoria ? 'Editar Categoria' : 'Nova Categoria'}
            </h3>
            
            <div className="space-y-3">
              <div className="space-y-1">
                <Label className="text-xs">Nome</Label>
                <Input
                  value={formData.nome}
                  onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                  placeholder="Nome da categoria"
                  className="h-9"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Tipo</Label>
                <Select
                  value={formData.tipo}
                  onValueChange={(value: 'receita' | 'despesa') => setFormData({ ...formData, tipo: value })}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="receita">Receita</SelectItem>
                    <SelectItem value="despesa">Despesa</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Cor</Label>
                <div className="flex flex-wrap gap-2">
                  {CORES_PREDEFINIDAS.map((cor) => (
                    <button
                      key={cor}
                      type="button"
                      className={`w-7 h-7 rounded-full transition-all ${
                        formData.cor === cor ? 'ring-2 ring-white ring-offset-2 ring-offset-background scale-110' : ''
                      }`}
                      style={{ backgroundColor: cor }}
                      onClick={() => setFormData({ ...formData, cor })}
                    />
                  ))}
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                {editingCategoria && (
                  <Button variant="outline" size="sm" onClick={resetForm} className="flex-1">
                    Cancelar
                  </Button>
                )}
                <Button
                  size="sm"
                  onClick={handleSave}
                  disabled={isSaving || !formData.nome}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                >
                  {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {editingCategoria ? 'Salvar' : 'Criar'}
                </Button>
              </div>
            </div>
          </div>

          {/* List */}
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-4">
              {/* Receitas */}
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider">
                  Receitas ({receitaCategorias.length})
                </h4>
                <div className="space-y-1">
                  {receitaCategorias.map((cat) => (
                    <div
                      key={cat.id}
                      className="flex items-center justify-between p-2 rounded-md hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: cat.cor }}
                        />
                        <span className="text-sm">{cat.nome}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => handleEdit(cat)}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 hover:text-red-500"
                          onClick={() => handleDelete(cat.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  {receitaCategorias.length === 0 && (
                    <p className="text-xs text-muted-foreground text-center py-2">
                      Nenhuma categoria de receita
                    </p>
                  )}
                </div>
              </div>

              {/* Despesas */}
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider">
                  Despesas ({despesaCategorias.length})
                </h4>
                <div className="space-y-1">
                  {despesaCategorias.map((cat) => (
                    <div
                      key={cat.id}
                      className="flex items-center justify-between p-2 rounded-md hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: cat.cor }}
                        />
                        <span className="text-sm">{cat.nome}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => handleEdit(cat)}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 hover:text-red-500"
                          onClick={() => handleDelete(cat.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  {despesaCategorias.length === 0 && (
                    <p className="text-xs text-muted-foreground text-center py-2">
                      Nenhuma categoria de despesa
                    </p>
                  )}
                </div>
              </div>
            </div>
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
}
