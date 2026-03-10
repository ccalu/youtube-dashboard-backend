import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiService, Channel } from '@/services/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface AddEditCanalModalProps {
  isOpen: boolean;
  onClose: () => void;
  canal?: Channel | null;
  tipo: 'minerado' | 'nosso';
  onSuccess: () => void;
}

export const AddEditCanalModal = ({
  isOpen,
  onClose,
  canal,
  tipo,
  onSuccess,
}: AddEditCanalModalProps) => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    nome_canal: '',
    url_canal: '',
    subnicho: '',
    lingua: '',
  });
  const [newSubnicho, setNewSubnicho] = useState('');
  const [newLingua, setNewLingua] = useState('');
  const [showNewSubnicho, setShowNewSubnicho] = useState(false);
  const [showNewLingua, setShowNewLingua] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { data: filterOptions } = useQuery({
    queryKey: ['filter-options'],
    queryFn: apiService.getFilterOptions,
  });

  useEffect(() => {
    if (canal) {
      setFormData({
        nome_canal: canal.nome_canal,
        url_canal: canal.url_canal,
        subnicho: canal.subnicho || '',
        lingua: canal.lingua,
      });
    } else {
      setFormData({
        nome_canal: '',
        url_canal: '',
        subnicho: '',
        lingua: '',
      });
    }
    setNewSubnicho('');
    setNewLingua('');
    setShowNewSubnicho(false);
    setShowNewLingua(false);
    setErrors({});
  }, [canal, isOpen]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.nome_canal || formData.nome_canal.length < 3) {
      newErrors.nome_canal = 'Nome do canal deve ter no mínimo 3 caracteres';
    }

    if (!formData.url_canal) {
      newErrors.url_canal = 'URL do canal é obrigatória';
    } else if (
      !formData.url_canal.includes('youtube.com') &&
      !formData.url_canal.includes('youtu.be')
    ) {
      newErrors.url_canal = 'URL deve ser um link válido do YouTube';
    }

    const linguaValue = showNewLingua ? newLingua : formData.lingua;
    if (!linguaValue) {
      newErrors.lingua = 'Língua é obrigatória';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const submitData = {
        nome_canal: formData.nome_canal,
        url_canal: formData.url_canal,
        nicho: '', // Campo removido do formulário
        subnicho: showNewSubnicho ? newSubnicho : formData.subnicho,
        lingua: showNewLingua ? newLingua : formData.lingua,
        tipo,
        status: 'ativo',
      };

      if (canal) {
        await apiService.updateCanal(canal.id, submitData);
      } else {
        await apiService.addCanal(submitData);
      }

      // Invalidar TODOS os caches relacionados (incluindo Kanban e Comentários)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['filter-options'] }),
        queryClient.invalidateQueries({ queryKey: ['channels'] }),
        queryClient.invalidateQueries({ queryKey: ['our-channels'] }),
        queryClient.invalidateQueries({ queryKey: ['favoritos-canais'] }),
        queryClient.invalidateQueries({ queryKey: ['favoritos-videos'] }),
        queryClient.invalidateQueries({ queryKey: ['kanban-structure'] }),
        queryClient.invalidateQueries({ queryKey: ['comments-summary'] }),
        queryClient.invalidateQueries({ queryKey: ['monetized-channels-comments'] }),
      ]);

      toast({
        title: canal ? 'Canal atualizado' : 'Canal adicionado',
        description: canal
          ? 'Canal atualizado com sucesso!'
          : 'Canal adicionado com sucesso!',
      });

      onSuccess();
      onClose();
    } catch (error) {
      toast({
        title: 'Erro',
        description: 'Erro ao salvar canal. Tente novamente.',
        variant: 'destructive',
      });
      setErrors({ submit: 'Erro ao salvar canal. Tente novamente.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[525px] bg-dashboard-card border-dashboard-border">
        <DialogHeader>
          <DialogTitle className="text-foreground">
            {canal ? 'Editar Canal' : 'Adicionar Canal'}
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Preencha os dados do canal abaixo. Campos marcados com * são obrigatórios.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="nome_canal" className="text-foreground">
              Nome do Canal *
            </Label>
            <Input
              id="nome_canal"
              value={formData.nome_canal}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, nome_canal: e.target.value }))
              }
              placeholder="Ex: Meu Canal"
              className="bg-dashboard-card border-dashboard-border"
            />
            {errors.nome_canal && (
              <p className="text-sm text-destructive">{errors.nome_canal}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="url_canal" className="text-foreground">
              URL do Canal *
            </Label>
            <Input
              id="url_canal"
              value={formData.url_canal}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, url_canal: e.target.value }))
              }
              placeholder="https://youtube.com/@meucanal"
              className="bg-dashboard-card border-dashboard-border"
            />
            {errors.url_canal && (
              <p className="text-sm text-destructive">{errors.url_canal}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="subnicho" className="text-foreground">
              Subnicho *
            </Label>
            <Select
              value={showNewSubnicho ? 'new' : formData.subnicho}
              onValueChange={(value) => {
                if (value === 'new') {
                  setShowNewSubnicho(true);
                } else {
                  setShowNewSubnicho(false);
                  setFormData((prev) => ({ ...prev, subnicho: value }));
                }
              }}
            >
              <SelectTrigger className="bg-dashboard-card border-dashboard-border">
                <SelectValue placeholder="Selecione o subnicho (opcional)" />
              </SelectTrigger>
              <SelectContent className="bg-dashboard-card border-dashboard-border">
                {filterOptions?.subnichos?.map((subnicho) => (
                  <SelectItem key={subnicho} value={subnicho}>
                    {subnicho}
                  </SelectItem>
                ))}
                <SelectItem value="new">➕ Adicionar novo...</SelectItem>
              </SelectContent>
            </Select>
            {showNewSubnicho && (
              <Input
                value={newSubnicho}
                onChange={(e) => setNewSubnicho(e.target.value)}
                placeholder="Digite o novo subnicho"
                className="bg-dashboard-card border-dashboard-border mt-2"
              />
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="lingua" className="text-foreground">
              Língua *
            </Label>
            <Select
              value={showNewLingua ? 'new' : formData.lingua}
              onValueChange={(value) => {
                if (value === 'new') {
                  setShowNewLingua(true);
                } else {
                  setShowNewLingua(false);
                  setFormData((prev) => ({ ...prev, lingua: value }));
                }
              }}
            >
              <SelectTrigger className="bg-dashboard-card border-dashboard-border">
                <SelectValue placeholder="Selecione a língua" />
              </SelectTrigger>
              <SelectContent className="bg-dashboard-card border-dashboard-border">
                {filterOptions?.linguas?.map((lingua) => (
                  <SelectItem key={lingua} value={lingua}>
                    {lingua}
                  </SelectItem>
                ))}
                <SelectItem value="new">➕ Adicionar novo...</SelectItem>
              </SelectContent>
            </Select>
            {showNewLingua && (
              <Input
                value={newLingua}
                onChange={(e) => setNewLingua(e.target.value)}
                placeholder="Digite a nova língua"
                className="bg-dashboard-card border-dashboard-border mt-2"
              />
            )}
            {errors.lingua && <p className="text-sm text-destructive">{errors.lingua}</p>}
          </div>

          {errors.submit && <p className="text-sm text-destructive">{errors.submit}</p>}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isSubmitting}
              className="border-dashboard-border"
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Salvando...
                </>
              ) : (
                <>{canal ? 'Salvar Alterações' : 'Adicionar Canal'}</>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};