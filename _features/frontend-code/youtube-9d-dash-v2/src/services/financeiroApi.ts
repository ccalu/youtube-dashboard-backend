import { API_BASE_URL } from './api';

// Types
export interface FinanceiroOverview {
  periodo: string;
  receita_bruta: number;
  despesas_totais: number;
  despesas_fixas: number;
  despesas_unicas: number;
  taxas_totais: number;
  lucro_liquido: number;
  receita_variacao: number;
  despesas_variacao: number;
  lucro_variacao: number;
}

export interface TaxaCambio {
  taxa: number;
  atualizado_em: string;
}

export interface GraficoReceitaDespesas {
  data: string;
  receita: number;
  despesas: number;
  taxas: number;
  lucro: number;
}

export interface BreakdownCategoria {
  categoria: string;
  valor: number;
  percentual: number;
  cor: string;
}

export interface BreakdownRecorrencia {
  tipo: string;
  valor: number;
  percentual: number;
  cor?: string;
}

export interface Lancamento {
  id: number;
  categoria_id: number;
  categoria_nome?: string;
  categoria_cor?: string;
  categoria_icon?: string;
  valor: number;
  data: string;
  descricao: string;
  tipo: 'receita' | 'despesa';
  recorrencia: 'fixa' | 'unica' | null;
  usuario?: string;
  created_at?: string;
  updated_at?: string;
  financeiro_categorias?: {
    cor: string;
    nome: string;
  };
}

export interface Categoria {
  id: number;
  nome: string;
  tipo: 'receita' | 'despesa';
  cor: string;
  icon?: string;
  ativo: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Taxa {
  id: number;
  nome: string;
  percentual: number;
  aplica_sobre: string;
  ativo: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Meta {
  id: number;
  nome: string;
  tipo: 'receita' | 'despesa' | 'lucro';
  valor_objetivo: number;
  valor_atual?: number;
  percentual_progresso?: number;
  periodo_inicio: string;
  periodo_fim: string;
  ativo: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ProjecaoMes {
  mes: string;
  mes_nome: string;
  total_ate_hoje: number;
  projecao_mes: number;
  media_diaria: number;
  dias_decorridos: number;
  dias_restantes: number;
  dias_total: number;
  taxa_cambio?: number;
}

export interface ComparacaoMensal {
  meses: {
    mes: string;
    mes_nome: string;
    receita: number;
    despesas: number;
    taxas: number;
    lucro: number;
    variacao: number | null;
  }[];
}

// Period can be preset or custom date range (YYYY-MM-DD,YYYY-MM-DD)
export type PeriodoFinanceiro = '7d' | '15d' | '30d' | 'all' | string;

class FinanceiroApiService {
  private fetchApi = async <T>(endpoint: string, options?: RequestInit): Promise<T> => {
    try {
      const { getAuthHeaders, handle401 } = await import('@/lib/authFetch');
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          ...getAuthHeaders(),
          ...(options?.headers as Record<string, string>),
        },
      });

      if (response.status === 401) { handle401(response); throw new Error('Session expired'); }
      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      throw error;
    }
  };

  // Helper to get period param
  private getPeriodoParam = (periodo: PeriodoFinanceiro): string => {
    if (periodo === 'all') {
      return '2024-10-26,' + new Date().toISOString().split('T')[0];
    }
    return periodo;
  };

  // Overview
  getOverview = async (periodo: PeriodoFinanceiro = '30d'): Promise<FinanceiroOverview> => {
    return this.fetchApi(`/api/financeiro/overview?periodo=${this.getPeriodoParam(periodo)}`);
  };

  // Taxa de Câmbio
  getTaxaCambio = async (): Promise<TaxaCambio> => {
    return this.fetchApi('/api/financeiro/taxa-cambio');
  };

  // Projeção do Mês (NEW)
  getProjecaoMes = async (): Promise<ProjecaoMes> => {
    return this.fetchApi('/api/financeiro/projecao-mes');
  };

  // Comparação Mensal (NEW)
  getComparacaoMensal = async (meses: number = 6): Promise<ComparacaoMensal> => {
    return this.fetchApi(`/api/financeiro/comparacao-mensal?meses=${meses}`);
  };

  // Gráfico Receita vs Despesas
  getGraficoReceitaDespesas = async (periodo: PeriodoFinanceiro = '30d'): Promise<GraficoReceitaDespesas[]> => {
    const response = await this.fetchApi<{ dados: GraficoReceitaDespesas[] }>(`/api/financeiro/graficos/receita-despesas?periodo=${this.getPeriodoParam(periodo)}`);
    return response.dados || [];
  };

  // Breakdown Despesas
  getBreakdownDespesas = async (periodo: PeriodoFinanceiro = '30d'): Promise<{
    por_categoria: BreakdownCategoria[];
    por_recorrencia: BreakdownRecorrencia[];
    total: number;
  }> => {
    return this.fetchApi(`/api/financeiro/graficos/despesas-breakdown?periodo=${this.getPeriodoParam(periodo)}`);
  };

  // Lançamentos
  getLancamentos = async (params?: {
    periodo?: PeriodoFinanceiro;
    tipo?: 'receita' | 'despesa';
    recorrencia?: 'fixa' | 'unica';
  }): Promise<{ lancamentos: Lancamento[]; total: number }> => {
    const queryParams = new URLSearchParams();
    if (params?.periodo) queryParams.append('periodo', this.getPeriodoParam(params.periodo));
    if (params?.tipo) queryParams.append('tipo', params.tipo);
    if (params?.recorrencia) queryParams.append('recorrencia', params.recorrencia);
    
    return this.fetchApi(`/api/financeiro/lancamentos?${queryParams.toString()}`);
  };

  createLancamento = async (data: {
    categoria_id: number;
    valor: number;
    data: string;
    descricao: string;
    tipo: 'receita' | 'despesa';
    recorrencia?: 'fixa' | 'unica' | null;
    usuario?: string;
  }): Promise<Lancamento> => {
    // Send as JSON body per V3 spec
    return this.fetchApi('/api/financeiro/lancamentos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  };

  updateLancamento = async (id: number, data: Partial<Lancamento>): Promise<Lancamento> => {
    return this.fetchApi(`/api/financeiro/lancamentos/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  };

  deleteLancamento = async (id: number): Promise<void> => {
    await this.fetchApi(`/api/financeiro/lancamentos/${id}`, {
      method: 'DELETE',
    });
  };

  // Categorias
  getCategorias = async (): Promise<{ categorias: Categoria[]; total: number }> => {
    return this.fetchApi('/api/financeiro/categorias');
  };

  createCategoria = async (data: Omit<Categoria, 'id' | 'created_at' | 'updated_at'>): Promise<Categoria> => {
    return this.fetchApi('/api/financeiro/categorias', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  };

  updateCategoria = async (id: number, data: Partial<Categoria>): Promise<Categoria> => {
    return this.fetchApi(`/api/financeiro/categorias/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  };

  deleteCategoria = async (id: number): Promise<void> => {
    await this.fetchApi(`/api/financeiro/categorias/${id}`, {
      method: 'DELETE',
    });
  };

  // Taxas
  getTaxas = async (): Promise<{ taxas: Taxa[]; total: number }> => {
    return this.fetchApi('/api/financeiro/taxas');
  };

  createTaxa = async (data: Omit<Taxa, 'id' | 'created_at' | 'updated_at'>): Promise<Taxa> => {
    return this.fetchApi('/api/financeiro/taxas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  };

  updateTaxa = async (id: number, data: Partial<Taxa>): Promise<Taxa> => {
    return this.fetchApi(`/api/financeiro/taxas/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  };

  deleteTaxa = async (id: number): Promise<void> => {
    await this.fetchApi(`/api/financeiro/taxas/${id}`, {
      method: 'DELETE',
    });
  };

  // Metas
  getMetas = async (periodo?: PeriodoFinanceiro): Promise<{ metas: Meta[]; total: number }> => {
    const url = periodo 
      ? `/api/financeiro/metas/progresso?periodo=${this.getPeriodoParam(periodo)}`
      : '/api/financeiro/metas/progresso';
    return this.fetchApi(url);
  };

  createMeta = async (data: Omit<Meta, 'id' | 'created_at' | 'updated_at' | 'valor_atual' | 'percentual_progresso'>): Promise<Meta> => {
    return this.fetchApi('/api/financeiro/metas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  };

  updateMeta = async (id: number, data: Partial<Meta>): Promise<Meta> => {
    return this.fetchApi(`/api/financeiro/metas/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  };

  deleteMeta = async (id: number): Promise<void> => {
    await this.fetchApi(`/api/financeiro/metas/${id}`, {
      method: 'DELETE',
    });
  };

  // Export CSV
  exportCSV = (periodo: PeriodoFinanceiro = '30d'): void => {
    window.open(`${API_BASE_URL}/api/financeiro/lancamentos/export-csv?periodo=${this.getPeriodoParam(periodo)}`, '_blank');
  };
}

export const financeiroApi = new FinanceiroApiService();