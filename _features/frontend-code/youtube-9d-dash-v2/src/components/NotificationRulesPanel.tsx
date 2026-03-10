import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MultiSelect, MultiSelectChips } from "@/components/ui/multi-select";
import { useToast } from "@/hooks/use-toast";
import { Plus, Edit, Trash2, TrendingUp, CheckCircle2, XCircle } from "lucide-react";

const API_URL = "https://youtube-dashboard-backend-production.up.railway.app";

interface Regra {
  id: number;
  nome_regra: string;
  views_minimas: number;
  periodo_dias: number;
  tipo_canal: string;
  subnichos?: string[] | null;
  ativa: boolean;
  created_at: string;
}

interface FormData {
  nome_regra: string;
  views_minimas: string;
  periodo_dias: string;
  tipo_canal: string;
  subnichos: string[];
  ativa: boolean;
}

export default function NotificationRulesPanel() {
  const { toast } = useToast();
  const [regras, setRegras] = useState<Regra[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [regraToDelete, setRegraToDelete] = useState<number | null>(null);
  const [regraToEdit, setRegraToEdit] = useState<Regra | null>(null);
  const [subnichos, setSubnichos] = useState<string[]>([]);
  
  const [formData, setFormData] = useState<FormData>({
    nome_regra: "",
    views_minimas: "",
    periodo_dias: "",
    tipo_canal: "ambos",
    subnichos: [],
    ativa: true,
  });

  // Buscar regras e subnichos ao carregar
  useEffect(() => {
    fetchRegras();
    fetchSubnichos();
  }, []);

  const fetchSubnichos = async () => {
    try {
      const response = await fetch(`${API_URL}/api/filtros`);
      const data = await response.json();
      setSubnichos(data.subnichos || []);
    } catch {
    }
  };

  const fetchRegras = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/regras-notificacoes`);
      const data = await response.json();
      setRegras(data.regras || []);
    } catch (error) {
      toast({
        title: "Erro",
        description: "Não foi possível carregar as regras",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      nome_regra: "",
      views_minimas: "",
      periodo_dias: "",
      tipo_canal: "ambos",
      subnichos: [],
      ativa: true,
    });
  };

  const handleCreateRegra = async () => {
    try {
      const payload = {
        nome_regra: String(formData.nome_regra),
        views_minimas: parseInt(formData.views_minimas),
        periodo_dias: parseInt(formData.periodo_dias),
        tipo_canal: String(formData.tipo_canal),
        subnichos: formData.subnichos && formData.subnichos.length > 0 ? formData.subnichos : null,
        ativa: true
      };

      const response = await fetch(`${API_URL}/api/regras-notificacoes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Erro ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      toast({ title: "Sucesso", description: "Regra criada", duration: 4000 });
      fetchRegras();
      setIsCreateDialogOpen(false);
      resetForm();
      
    } catch (error) {
      toast({ 
        title: "Erro", 
        description: error instanceof Error ? error.message : "Erro ao criar regra",
        variant: "destructive" 
      });
    }
  };

  const handleEditRegra = async () => {
    if (!regraToEdit) return;

    try {
      const payload = {
        nome_regra: String(formData.nome_regra),
        views_minimas: parseInt(formData.views_minimas),
        periodo_dias: parseInt(formData.periodo_dias),
        tipo_canal: String(formData.tipo_canal),
        subnichos: formData.subnichos && formData.subnichos.length > 0 ? formData.subnichos : null,
        ativa: Boolean(formData.ativa)
      };

      const response = await fetch(`${API_URL}/api/regras-notificacoes/${regraToEdit.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Erro ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      toast({ title: "Sucesso", description: "Regra atualizada", duration: 4000 });
      fetchRegras();
      setIsEditDialogOpen(false);
      setRegraToEdit(null);
      resetForm();
      
    } catch (error) {
      toast({ 
        title: "Erro", 
        description: error instanceof Error ? error.message : "Erro ao atualizar regra",
        variant: "destructive" 
      });
    }
  };

  const handleDeleteRegra = async () => {
    if (!regraToDelete) return;

    try {
      const response = await fetch(
        `${API_URL}/api/regras-notificacoes/${regraToDelete}`,
        {
          method: "DELETE",
        }
      );

      if (response.ok) {
        toast({
          title: "Sucesso! 🗑️",
          description: "Regra deletada com sucesso",
        });
        setDeleteDialogOpen(false);
        setRegraToDelete(null);
        fetchRegras();
      } else {
        throw new Error("Erro ao deletar regra");
      }
    } catch (error) {
      toast({
        title: "Erro",
        description: "Não foi possível deletar a regra",
        variant: "destructive",
      });
    }
  };

  const handleToggleRegra = async (regra: Regra) => {
    try {
      const response = await fetch(
        `${API_URL}/api/regras-notificacoes/${regra.id}/toggle`,
        {
          method: "PUT",
        }
      );

      if (response.ok) {
        const status = regra.ativa ? "desativada" : "ativada";
        toast({
          title: `Regra ${status}! 🔄`,
          description: `A regra "${regra.nome_regra}" foi ${status} com sucesso`,
        });
        fetchRegras();
      } else {
        throw new Error("Erro ao alterar status da regra");
      }
    } catch (error) {
      toast({
        title: "Erro",
        description: "Não foi possível alterar o status da regra",
        variant: "destructive",
      });
    }
  };

  const openEditDialog = (regra: Regra) => {
    setRegraToEdit(regra);
    setFormData({
      nome_regra: regra.nome_regra,
      views_minimas: regra.views_minimas.toString(),
      periodo_dias: regra.periodo_dias.toString(),
      tipo_canal: regra.tipo_canal,
      subnichos: regra.subnichos || [],
      ativa: regra.ativa,
    });
    setIsEditDialogOpen(true);
  };

  const openDeleteDialog = (regraId: number) => {
    setRegraToDelete(regraId);
    setDeleteDialogOpen(true);
  };

  const formatViews = (views: number) => {
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`;
    if (views >= 1000) return `${(views / 1000).toFixed(0)}k`;
    return views.toString();
  };

  const formatTipoCanal = (tipo: string) => {
    const tipos: Record<string, string> = {
      ambos: "Todos os canais",
      nosso: "Nossos canais",
      minerado: "Canais minerados",
    };
    return tipos[tipo] || tipo;
  };

  // Estatísticas
  const stats = {
    total: regras.length,
    ativas: regras.filter((r) => r.ativa).length,
    inativas: regras.filter((r) => !r.ativa).length,
  };

  return (
    <div className="space-y-6">
      {/* Header com Stats - EXATO DA IMAGEM */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1 - Total de Regras (Azul) */}
        <Card className="border-2 shadow-md hover:shadow-lg transition-shadow" 
              style={{ 
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderColor: 'rgba(59, 130, 246, 0.3)'
              }}>
          <CardContent className="pt-3 pb-3 md:pt-6 md:pb-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-muted-foreground font-medium mb-1 md:mb-2">Total de Regras</p>
                <p className="text-2xl md:text-4xl font-bold text-white">{stats.total}</p>
              </div>
              <TrendingUp className="h-6 w-6 md:h-8 md:w-8" style={{ color: '#3b82f6' }} />
            </div>
          </CardContent>
        </Card>

        {/* Card 2 - Regras Ativas (Verde) */}
        <Card className="border-2 shadow-md hover:shadow-lg transition-shadow"
              style={{ 
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                borderColor: 'rgba(34, 197, 94, 0.3)'
              }}>
          <CardContent className="pt-3 pb-3 md:pt-6 md:pb-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-muted-foreground font-medium mb-1 md:mb-2">Regras Ativas</p>
                <p className="text-2xl md:text-4xl font-bold" style={{ color: '#22c55e' }}>{stats.ativas}</p>
              </div>
              <CheckCircle2 className="h-6 w-6 md:h-8 md:w-8" style={{ color: '#22c55e' }} />
            </div>
          </CardContent>
        </Card>

        {/* Card 3 - Regras Inativas (Vermelho) */}
        <Card className="border-2 shadow-md hover:shadow-lg transition-shadow"
              style={{ 
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderColor: 'rgba(239, 68, 68, 0.3)'
              }}>
          <CardContent className="pt-3 pb-3 md:pt-6 md:pb-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-muted-foreground font-medium mb-1 md:mb-2">Regras Inativas</p>
                <p className="text-2xl md:text-4xl font-bold" style={{ color: '#ef4444' }}>{stats.inativas}</p>
              </div>
              <XCircle className="h-6 w-6 md:h-8 md:w-8" style={{ color: '#ef4444' }} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Título e Botão Nova Regra */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl md:text-3xl font-bold text-white">Regras de Notificações</h2>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button 
              onClick={resetForm}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Plus className="h-4 w-4 md:mr-2" />
              <span className="hidden md:inline">Nova Regra</span>
            </Button>
          </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Criar Nova Regra</DialogTitle>
                <DialogDescription>
                  Defina as condições para criar notificações automáticas
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="nome">Nome da Regra</Label>
                  <Input
                    id="nome"
                    placeholder="Ex: 20K em 48h"
                    value={formData.nome_regra}
                    onChange={(e) =>
                      setFormData({ ...formData, nome_regra: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="views">Views Mínimas</Label>
                  <Input
                    id="views"
                    type="number"
                    placeholder="Ex: 20000"
                    value={formData.views_minimas}
                    onChange={(e) =>
                      setFormData({ ...formData, views_minimas: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="periodo">Período (dias)</Label>
                  <Input
                    id="periodo"
                    type="number"
                    placeholder="Ex: 2"
                    value={formData.periodo_dias}
                    onChange={(e) =>
                      setFormData({ ...formData, periodo_dias: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tipo">Tipo de Canal</Label>
                  <Select
                    value={formData.tipo_canal}
                    onValueChange={(value) =>
                      setFormData({ ...formData, tipo_canal: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ambos">Todos os canais</SelectItem>
                      <SelectItem value="nosso">Nossos canais</SelectItem>
                      <SelectItem value="minerado">Canais minerados</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="subnichos">Subnichos (opcional)</Label>
                  <MultiSelect
                    options={subnichos.map(s => ({ label: s, value: s }))}
                    selected={formData.subnichos}
                    onChange={(selected) => setFormData({ ...formData, subnichos: selected })}
                    placeholder="Selecione subnichos"
                  />
                  {formData.subnichos.length > 0 && (
                    <MultiSelectChips
                      options={subnichos.map(s => ({ label: s, value: s }))}
                      selected={formData.subnichos}
                      onRemove={(value) => 
                        setFormData({ 
                          ...formData, 
                          subnichos: formData.subnichos.filter(s => s !== value) 
                        })
                      }
                    />
                  )}
                  <p className="text-xs text-muted-foreground">
                    Deixe vazio para receber notificações de todos os subnichos
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="ativa"
                    checked={formData.ativa}
                    onCheckedChange={(checked) =>
                      setFormData({ ...formData, ativa: checked })
                    }
                  />
                  <Label htmlFor="ativa">Regra ativa</Label>
                </div>
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => {
                    setIsCreateDialogOpen(false);
                    resetForm();
                  }}
                >
                  Cancelar
                </Button>
                <Button onClick={handleCreateRegra}>Criar Regra</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

      {/* Lista de Regras - EXATO DA IMAGEM */}
      <div className="space-y-4">
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">
              Carregando regras...
            </div>
          ) : regras.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              Nenhuma regra cadastrada. Crie sua primeira regra!
            </div>
          ) : (
            regras.map((regra) => (
              <div
                key={regra.id}
                className="rounded-xl p-5 border-2 transition-all hover:shadow-lg"
                style={{
                  backgroundColor: regra.ativa ? 'rgba(22, 163, 74, 0.08)' : 'rgba(71, 85, 105, 0.2)',
                  borderColor: regra.ativa ? 'rgba(34, 197, 94, 0.3)' : 'rgba(100, 116, 139, 0.3)'
                }}
              >
                {/* Linha 1: Nome + Badge + Toggle */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <h3 className="text-sm md:text-lg font-bold text-white">
                      {regra.nome_regra}
                    </h3>
                    <Badge 
                      className="hidden md:inline-flex text-xs font-semibold px-2 py-0.5"
                      style={{
                        backgroundColor: 'rgba(34, 197, 94, 0.2)',
                        color: '#22c55e',
                        border: 'none'
                      }}
                    >
                      ✓ Ativa
                    </Badge>
                  </div>
                  
                  <div className="hidden md:flex items-center gap-2">
                    <span className="text-sm text-gray-300">Ativa</span>
                    <Switch
                      checked={regra.ativa}
                      onCheckedChange={() => handleToggleRegra(regra)}
                    />
                  </div>
                </div>

                {/* Linha 2: Views */}
                <div className="flex items-center gap-2 mb-2">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
                    <line x1="12" y1="20" x2="12" y2="10"></line>
                    <line x1="18" y1="20" x2="18" y2="4"></line>
                    <line x1="6" y1="20" x2="6" y2="16"></line>
                  </svg>
                  <span className="text-white text-xs md:text-[15px]">
                    <strong style={{ color: '#3b82f6' }}>{formatViews(regra.views_minimas)}</strong> views em{" "}
                    <strong style={{ color: '#3b82f6' }}>{regra.periodo_dias}</strong>{" "}
                    {regra.periodo_dias === 1 ? "dia" : "dias"}
                  </span>
                </div>

                {/* Linha 3: Tipo de Canal */}
                <div className="flex items-center gap-2 mb-2">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <circle cx="12" cy="12" r="6"></circle>
                    <circle cx="12" cy="12" r="2"></circle>
                  </svg>
                  <span className="text-white text-xs md:text-[15px]">
                    {formatTipoCanal(regra.tipo_canal)}
                  </span>
                </div>

                {/* Linha 4: Subnichos */}
                <div className="flex items-center gap-2 mb-2">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#eab308" strokeWidth="2">
                    <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>
                    <line x1="7" y1="7" x2="7.01" y2="7"></line>
                  </svg>
                  <div className="flex flex-wrap gap-1.5">
                    {!regra.subnichos || regra.subnichos.length === 0 ? (
                      <Badge 
                        className="text-xs px-2 py-0.5 bg-slate-700 text-white border-0"
                      >
                        Todos os subnichos
                      </Badge>
                    ) : (
                      regra.subnichos.map(s => (
                        <Badge 
                          key={s}
                          className="text-xs px-2 py-0.5 bg-slate-700 text-white border-0"
                        >
                          {s}
                        </Badge>
                      ))
                    )}
                  </div>
                </div>

                {/* Linha 5: Data de Criação */}
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-sm">📅</span>
                  <span className="text-sm text-gray-400">
                    Criada em: {new Date(regra.created_at).toLocaleDateString('pt-BR')}
                  </span>
                </div>

                {/* Footer: Botões */}
                <div className="flex justify-end gap-2 pt-3 border-t border-gray-700">
                  {/* Mobile: Toggle + Ícones */}
                  <div className="flex md:hidden items-center gap-2">
                    <Switch
                      checked={regra.ativa}
                      onCheckedChange={() => handleToggleRegra(regra)}
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openEditDialog(regra)}
                      className="border-white/50 text-white hover:bg-white/10 px-2"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openDeleteDialog(regra.id)}
                      className="border-red-400/50 text-red-400 hover:bg-red-500/10 px-2"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  {/* Desktop: Botões com texto */}
                  <div className="hidden md:flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openEditDialog(regra)}
                      className="border-white/50 text-white hover:bg-white/10"
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      Editar
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openDeleteDialog(regra.id)}
                      className="border-red-400/50 text-red-400 hover:bg-red-500/10"
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Deletar
                    </Button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

      {/* Dialog de Edição */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar Regra</DialogTitle>
            <DialogDescription>
              Atualize as condições da regra de notificação
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-nome">Nome da Regra</Label>
              <Input
                id="edit-nome"
                placeholder="Ex: 20K em 48h"
                value={formData.nome_regra}
                onChange={(e) =>
                  setFormData({ ...formData, nome_regra: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-views">Views Mínimas</Label>
              <Input
                id="edit-views"
                type="number"
                placeholder="Ex: 20000"
                value={formData.views_minimas}
                onChange={(e) =>
                  setFormData({ ...formData, views_minimas: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-periodo">Período (dias)</Label>
              <Input
                id="edit-periodo"
                type="number"
                placeholder="Ex: 2"
                value={formData.periodo_dias}
                onChange={(e) =>
                  setFormData({ ...formData, periodo_dias: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-tipo">Tipo de Canal</Label>
              <Select
                value={formData.tipo_canal}
                onValueChange={(value) =>
                  setFormData({ ...formData, tipo_canal: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ambos">Todos os canais</SelectItem>
                  <SelectItem value="nosso">Nossos canais</SelectItem>
                  <SelectItem value="minerado">Canais minerados</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-subnichos">Subnichos (opcional)</Label>
              <MultiSelect
                options={subnichos.map(s => ({ label: s, value: s }))}
                selected={formData.subnichos}
                onChange={(selected) => setFormData({ ...formData, subnichos: selected })}
                placeholder="Selecione subnichos"
              />
              {formData.subnichos.length > 0 && (
                <MultiSelectChips
                  options={subnichos.map(s => ({ label: s, value: s }))}
                  selected={formData.subnichos}
                  onRemove={(value) => 
                    setFormData({ 
                      ...formData, 
                      subnichos: formData.subnichos.filter(s => s !== value) 
                    })
                  }
                />
              )}
              <p className="text-xs text-muted-foreground">
                Deixe vazio para receber notificações de todos os subnichos
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="edit-ativa"
                checked={formData.ativa}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, ativa: checked })
                }
              />
              <Label htmlFor="edit-ativa">Regra ativa</Label>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsEditDialogOpen(false);
                setRegraToEdit(null);
                resetForm();
              }}
            >
              Cancelar
            </Button>
            <Button onClick={handleEditRegra}>Salvar Alterações</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog de Confirmação de Delete */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Tem certeza?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. A regra será deletada permanentemente.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setRegraToDelete(null)}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteRegra}
              className="bg-red-600 hover:bg-red-700"
            >
              Deletar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
