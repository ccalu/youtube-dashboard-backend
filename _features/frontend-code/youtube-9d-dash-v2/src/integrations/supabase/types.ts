export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "12.2.3 (519615d)"
  }
  public: {
    Tables: {
      authenticity_analysis_runs: {
        Row: {
          alert_count: number | null
          authenticity_level: string | null
          authenticity_score: number | null
          channel_id: string
          channel_name: string | null
          created_at: string | null
          has_alerts: boolean | null
          id: number
          report_text: string | null
          results_json: Json | null
          run_date: string | null
          structure_score: number | null
          title_score: number | null
          total_videos_analyzed: number | null
        }
        Insert: {
          alert_count?: number | null
          authenticity_level?: string | null
          authenticity_score?: number | null
          channel_id: string
          channel_name?: string | null
          created_at?: string | null
          has_alerts?: boolean | null
          id?: number
          report_text?: string | null
          results_json?: Json | null
          run_date?: string | null
          structure_score?: number | null
          title_score?: number | null
          total_videos_analyzed?: number | null
        }
        Update: {
          alert_count?: number | null
          authenticity_level?: string | null
          authenticity_score?: number | null
          channel_id?: string
          channel_name?: string | null
          created_at?: string | null
          has_alerts?: boolean | null
          id?: number
          report_text?: string | null
          results_json?: Json | null
          run_date?: string | null
          structure_score?: number | null
          title_score?: number | null
          total_videos_analyzed?: number | null
        }
        Relationships: []
      }
      calendar_config: {
        Row: {
          created_at: string | null
          id: number
          socio_emoji: string
          socio_key: string
          socio_name: string
        }
        Insert: {
          created_at?: string | null
          id?: number
          socio_emoji: string
          socio_key: string
          socio_name: string
        }
        Update: {
          created_at?: string | null
          id?: number
          socio_emoji?: string
          socio_key?: string
          socio_name?: string
        }
        Relationships: []
      }
      calendar_events: {
        Row: {
          category: string | null
          created_at: string | null
          created_by: string
          deleted_at: string | null
          description: string | null
          event_date: string
          event_type: string | null
          id: number
          is_deleted: boolean | null
          title: string
          updated_at: string | null
        }
        Insert: {
          category?: string | null
          created_at?: string | null
          created_by: string
          deleted_at?: string | null
          description?: string | null
          event_date: string
          event_type?: string | null
          id?: number
          is_deleted?: boolean | null
          title: string
          updated_at?: string | null
        }
        Update: {
          category?: string | null
          created_at?: string | null
          created_by?: string
          deleted_at?: string | null
          description?: string | null
          event_date?: string
          event_type?: string | null
          id?: number
          is_deleted?: boolean | null
          title?: string
          updated_at?: string | null
        }
        Relationships: []
      }
      canais_monitorados: {
        Row: {
          coleta_falhas_consecutivas: number | null
          coleta_ultimo_erro: string | null
          coleta_ultimo_sucesso: string | null
          custom_url: string | null
          data_adicionado: string | null
          frequencia_semanal: number | null
          id: number
          is_monetized: boolean | null
          kanban_status: string | null
          kanban_status_since: string | null
          lingua: string | null
          melhor_dia_semana: number | null
          melhor_hora: number | null
          monetizado: boolean | null
          nicho: string | null
          nome_canal: string
          published_at: string | null
          status: string | null
          subnicho: string | null
          tipo: string
          total_comentarios_coletados: number | null
          ultima_coleta: string | null
          ultimo_comentario_coletado: string | null
          url_canal: string
          video_count: number | null
        }
        Insert: {
          coleta_falhas_consecutivas?: number | null
          coleta_ultimo_erro?: string | null
          coleta_ultimo_sucesso?: string | null
          custom_url?: string | null
          data_adicionado?: string | null
          frequencia_semanal?: number | null
          id?: number
          is_monetized?: boolean | null
          kanban_status?: string | null
          kanban_status_since?: string | null
          lingua?: string | null
          melhor_dia_semana?: number | null
          melhor_hora?: number | null
          monetizado?: boolean | null
          nicho?: string | null
          nome_canal: string
          published_at?: string | null
          status?: string | null
          subnicho?: string | null
          tipo?: string
          total_comentarios_coletados?: number | null
          ultima_coleta?: string | null
          ultimo_comentario_coletado?: string | null
          url_canal: string
          video_count?: number | null
        }
        Update: {
          coleta_falhas_consecutivas?: number | null
          coleta_ultimo_erro?: string | null
          coleta_ultimo_sucesso?: string | null
          custom_url?: string | null
          data_adicionado?: string | null
          frequencia_semanal?: number | null
          id?: number
          is_monetized?: boolean | null
          kanban_status?: string | null
          kanban_status_since?: string | null
          lingua?: string | null
          melhor_dia_semana?: number | null
          melhor_hora?: number | null
          monetizado?: boolean | null
          nicho?: string | null
          nome_canal?: string
          published_at?: string | null
          status?: string | null
          subnicho?: string | null
          tipo?: string
          total_comentarios_coletados?: number | null
          ultima_coleta?: string | null
          ultimo_comentario_coletado?: string | null
          url_canal?: string
          video_count?: number | null
        }
        Relationships: []
      }
      canal_analytics_cache: {
        Row: {
          anomalias_detectadas: Json | null
          canal_id: number
          clusters_conteudo: Json | null
          created_at: string | null
          id: number
          melhor_posting_time: Json | null
          padroes_identificados: Json | null
          top_videos_cache: Json | null
          updated_at: string | null
        }
        Insert: {
          anomalias_detectadas?: Json | null
          canal_id: number
          clusters_conteudo?: Json | null
          created_at?: string | null
          id?: number
          melhor_posting_time?: Json | null
          padroes_identificados?: Json | null
          top_videos_cache?: Json | null
          updated_at?: string | null
        }
        Update: {
          anomalias_detectadas?: Json | null
          canal_id?: number
          clusters_conteudo?: Json | null
          created_at?: string | null
          id?: number
          melhor_posting_time?: Json | null
          padroes_identificados?: Json | null
          top_videos_cache?: Json | null
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "canal_analytics_cache_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: true
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "canal_analytics_cache_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: true
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "canal_analytics_cache_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: true
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "canal_analytics_cache_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: true
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "canal_analytics_cache_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: true
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      coletas_historico: {
        Row: {
          canais_erro: number | null
          canais_sucesso: number | null
          canais_total: number | null
          created_at: string | null
          data_fim: string | null
          data_inicio: string
          duracao_segundos: number | null
          id: number
          mensagem_erro: string | null
          requisicoes_usadas: number | null
          status: string
          videos_coletados: number | null
        }
        Insert: {
          canais_erro?: number | null
          canais_sucesso?: number | null
          canais_total?: number | null
          created_at?: string | null
          data_fim?: string | null
          data_inicio: string
          duracao_segundos?: number | null
          id?: number
          mensagem_erro?: string | null
          requisicoes_usadas?: number | null
          status: string
          videos_coletados?: number | null
        }
        Update: {
          canais_erro?: number | null
          canais_sucesso?: number | null
          canais_total?: number | null
          created_at?: string | null
          data_fim?: string | null
          data_inicio?: string
          duracao_segundos?: number | null
          id?: number
          mensagem_erro?: string | null
          requisicoes_usadas?: number | null
          status?: string
          videos_coletados?: number | null
        }
        Relationships: []
      }
      comments_collection_logs: {
        Row: {
          canais_com_erro: number | null
          canais_com_sucesso: number | null
          canais_processados: number | null
          comentarios_analisados: number | null
          comentarios_nao_analisados: number | null
          created_at: string | null
          detalhes_erros: Json | null
          detalhes_sucesso: Json | null
          id: string
          percentual_limite_diario: number | null
          tempo_execucao: number | null
          timestamp: string
          tipo: string
          tokens_usados: number | null
          total_comentarios: number | null
        }
        Insert: {
          canais_com_erro?: number | null
          canais_com_sucesso?: number | null
          canais_processados?: number | null
          comentarios_analisados?: number | null
          comentarios_nao_analisados?: number | null
          created_at?: string | null
          detalhes_erros?: Json | null
          detalhes_sucesso?: Json | null
          id: string
          percentual_limite_diario?: number | null
          tempo_execucao?: number | null
          timestamp: string
          tipo: string
          tokens_usados?: number | null
          total_comentarios?: number | null
        }
        Update: {
          canais_com_erro?: number | null
          canais_com_sucesso?: number | null
          canais_processados?: number | null
          comentarios_analisados?: number | null
          comentarios_nao_analisados?: number | null
          created_at?: string | null
          detalhes_erros?: Json | null
          detalhes_sucesso?: Json | null
          id?: string
          percentual_limite_diario?: number | null
          tempo_execucao?: number | null
          timestamp?: string
          tipo?: string
          tokens_usados?: number | null
          total_comentarios?: number | null
        }
        Relationships: []
      }
      copy_analysis_runs: {
        Row: {
          channel_avg_retention: number | null
          channel_avg_views: number | null
          channel_avg_watch_time: number | null
          channel_id: string
          channel_name: string | null
          created_at: string | null
          id: number
          report_text: string | null
          results_json: Json | null
          run_date: string | null
          total_videos_analyzed: number | null
          total_videos_excluded: number | null
          total_videos_no_match: number | null
        }
        Insert: {
          channel_avg_retention?: number | null
          channel_avg_views?: number | null
          channel_avg_watch_time?: number | null
          channel_id: string
          channel_name?: string | null
          created_at?: string | null
          id?: number
          report_text?: string | null
          results_json?: Json | null
          run_date?: string | null
          total_videos_analyzed?: number | null
          total_videos_excluded?: number | null
          total_videos_no_match?: number | null
        }
        Update: {
          channel_avg_retention?: number | null
          channel_avg_views?: number | null
          channel_avg_watch_time?: number | null
          channel_id?: string
          channel_name?: string | null
          created_at?: string | null
          id?: number
          report_text?: string | null
          results_json?: Json | null
          run_date?: string | null
          total_videos_analyzed?: number | null
          total_videos_excluded?: number | null
          total_videos_no_match?: number | null
        }
        Relationships: []
      }
      dados_canais_historico: {
        Row: {
          canal_id: number | null
          data_coleta: string
          engagement_rate: number | null
          id: number
          inscritos: number | null
          inscritos_diff: number | null
          total_views: number | null
          videos_publicados_7d: number | null
          views_15d: number | null
          views_30d: number | null
          views_60d: number | null
          views_7d: number | null
        }
        Insert: {
          canal_id?: number | null
          data_coleta: string
          engagement_rate?: number | null
          id?: number
          inscritos?: number | null
          inscritos_diff?: number | null
          total_views?: number | null
          videos_publicados_7d?: number | null
          views_15d?: number | null
          views_30d?: number | null
          views_60d?: number | null
          views_7d?: number | null
        }
        Update: {
          canal_id?: number | null
          data_coleta?: string
          engagement_rate?: number | null
          id?: number
          inscritos?: number | null
          inscritos_diff?: number | null
          total_views?: number | null
          videos_publicados_7d?: number | null
          views_15d?: number | null
          views_30d?: number | null
          views_60d?: number | null
          views_7d?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "dados_canais_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "dados_canais_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "dados_canais_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "dados_canais_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "dados_canais_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      engagement_cache: {
        Row: {
          canal_id: number
          created_at: string | null
          data: Json
          expires_at: string
          id: number
          processed_at: string
          processing_time_ms: number | null
          total_comments: number | null
          total_videos: number | null
          updated_at: string | null
        }
        Insert: {
          canal_id: number
          created_at?: string | null
          data: Json
          expires_at: string
          id?: number
          processed_at?: string
          processing_time_ms?: number | null
          total_comments?: number | null
          total_videos?: number | null
          updated_at?: string | null
        }
        Update: {
          canal_id?: number
          created_at?: string | null
          data?: Json
          expires_at?: string
          id?: number
          processed_at?: string
          processing_time_ms?: number | null
          total_comments?: number | null
          total_videos?: number | null
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "engagement_cache_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: true
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "engagement_cache_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: true
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "engagement_cache_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: true
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "engagement_cache_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: true
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "engagement_cache_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: true
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      favoritos: {
        Row: {
          data_favoritado: string | null
          id: number
          item_id: number
          tipo: string
        }
        Insert: {
          data_favoritado?: string | null
          id?: number
          item_id: number
          tipo: string
        }
        Update: {
          data_favoritado?: string | null
          id?: number
          item_id?: number
          tipo?: string
        }
        Relationships: []
      }
      financeiro_categorias: {
        Row: {
          ativo: boolean | null
          cor: string | null
          created_at: string | null
          icon: string | null
          id: number
          nome: string
          tipo: string
          updated_at: string | null
        }
        Insert: {
          ativo?: boolean | null
          cor?: string | null
          created_at?: string | null
          icon?: string | null
          id?: number
          nome: string
          tipo: string
          updated_at?: string | null
        }
        Update: {
          ativo?: boolean | null
          cor?: string | null
          created_at?: string | null
          icon?: string | null
          id?: number
          nome?: string
          tipo?: string
          updated_at?: string | null
        }
        Relationships: []
      }
      financeiro_lancamentos: {
        Row: {
          categoria_id: number | null
          created_at: string | null
          data: string
          descricao: string | null
          id: number
          recorrencia: string | null
          tipo: string
          updated_at: string | null
          usuario: string | null
          valor: number
        }
        Insert: {
          categoria_id?: number | null
          created_at?: string | null
          data: string
          descricao?: string | null
          id?: number
          recorrencia?: string | null
          tipo: string
          updated_at?: string | null
          usuario?: string | null
          valor: number
        }
        Update: {
          categoria_id?: number | null
          created_at?: string | null
          data?: string
          descricao?: string | null
          id?: number
          recorrencia?: string | null
          tipo?: string
          updated_at?: string | null
          usuario?: string | null
          valor?: number
        }
        Relationships: [
          {
            foreignKeyName: "financeiro_lancamentos_categoria_id_fkey"
            columns: ["categoria_id"]
            isOneToOne: false
            referencedRelation: "financeiro_categorias"
            referencedColumns: ["id"]
          },
        ]
      }
      financeiro_metas: {
        Row: {
          ativo: boolean | null
          created_at: string | null
          id: number
          nome: string
          periodo_fim: string
          periodo_inicio: string
          tipo: string
          updated_at: string | null
          valor_objetivo: number
        }
        Insert: {
          ativo?: boolean | null
          created_at?: string | null
          id?: number
          nome: string
          periodo_fim: string
          periodo_inicio: string
          tipo: string
          updated_at?: string | null
          valor_objetivo: number
        }
        Update: {
          ativo?: boolean | null
          created_at?: string | null
          id?: number
          nome?: string
          periodo_fim?: string
          periodo_inicio?: string
          tipo?: string
          updated_at?: string | null
          valor_objetivo?: number
        }
        Relationships: []
      }
      financeiro_taxas: {
        Row: {
          aplica_sobre: string
          ativo: boolean | null
          created_at: string | null
          id: number
          nome: string
          percentual: number
          updated_at: string | null
        }
        Insert: {
          aplica_sobre?: string
          ativo?: boolean | null
          created_at?: string | null
          id?: number
          nome: string
          percentual: number
          updated_at?: string | null
        }
        Update: {
          aplica_sobre?: string
          ativo?: boolean | null
          created_at?: string | null
          id?: number
          nome?: string
          percentual?: number
          updated_at?: string | null
        }
        Relationships: []
      }
      gap_analysis: {
        Row: {
          analyzed_week_end: string
          analyzed_week_start: string
          avg_views: number
          competitor_count: number
          created_at: string | null
          example_videos: Json | null
          gap_description: string | null
          gap_title: string
          id: number
          recommendation: string | null
          subniche: string
        }
        Insert: {
          analyzed_week_end: string
          analyzed_week_start: string
          avg_views: number
          competitor_count: number
          created_at?: string | null
          example_videos?: Json | null
          gap_description?: string | null
          gap_title: string
          id?: number
          recommendation?: string | null
          subniche: string
        }
        Update: {
          analyzed_week_end?: string
          analyzed_week_start?: string
          avg_views?: number
          competitor_count?: number
          created_at?: string | null
          example_videos?: Json | null
          gap_description?: string | null
          gap_title?: string
          id?: number
          recommendation?: string | null
          subniche?: string
        }
        Relationships: []
      }
      gpt_analysis_metrics: {
        Row: {
          avg_response_time_ms: number | null
          created_at: string | null
          date: string | null
          errors_count: number | null
          estimated_cost_usd: number | null
          high_confidence_count: number | null
          id: number
          low_confidence_count: number | null
          medium_confidence_count: number | null
          success_rate: number | null
          total_analyzed: number | null
          total_tokens_input: number | null
          total_tokens_output: number | null
        }
        Insert: {
          avg_response_time_ms?: number | null
          created_at?: string | null
          date?: string | null
          errors_count?: number | null
          estimated_cost_usd?: number | null
          high_confidence_count?: number | null
          id?: number
          low_confidence_count?: number | null
          medium_confidence_count?: number | null
          success_rate?: number | null
          total_analyzed?: number | null
          total_tokens_input?: number | null
          total_tokens_output?: number | null
        }
        Update: {
          avg_response_time_ms?: number | null
          created_at?: string | null
          date?: string | null
          errors_count?: number | null
          estimated_cost_usd?: number | null
          high_confidence_count?: number | null
          id?: number
          low_confidence_count?: number | null
          medium_confidence_count?: number | null
          success_rate?: number | null
          total_analyzed?: number | null
          total_tokens_input?: number | null
          total_tokens_output?: number | null
        }
        Relationships: []
      }
      kanban_history: {
        Row: {
          action_type: string
          canal_id: number
          description: string
          details: Json | null
          id: number
          is_deleted: boolean | null
          performed_at: string | null
        }
        Insert: {
          action_type: string
          canal_id: number
          description: string
          details?: Json | null
          id?: number
          is_deleted?: boolean | null
          performed_at?: string | null
        }
        Update: {
          action_type?: string
          canal_id?: number
          description?: string
          details?: Json | null
          id?: number
          is_deleted?: boolean | null
          performed_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "kanban_history_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kanban_history_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kanban_history_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kanban_history_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "kanban_history_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      kanban_notes: {
        Row: {
          canal_id: number
          coluna_id: string | null
          created_at: string | null
          id: number
          note_color: string | null
          note_text: string
          position: number | null
          stage_id: string | null
          updated_at: string | null
        }
        Insert: {
          canal_id: number
          coluna_id?: string | null
          created_at?: string | null
          id?: number
          note_color?: string | null
          note_text: string
          position?: number | null
          stage_id?: string | null
          updated_at?: string | null
        }
        Update: {
          canal_id?: number
          coluna_id?: string | null
          created_at?: string | null
          id?: number
          note_color?: string | null
          note_text?: string
          position?: number | null
          stage_id?: string | null
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "kanban_notes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kanban_notes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kanban_notes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kanban_notes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "kanban_notes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      keyword_analysis: {
        Row: {
          analyzed_date: string
          avg_views: number
          created_at: string | null
          frequency: number
          id: number
          keyword: string
          period_days: number
          video_count: number
        }
        Insert: {
          analyzed_date?: string
          avg_views: number
          created_at?: string | null
          frequency: number
          id?: number
          keyword: string
          period_days: number
          video_count: number
        }
        Update: {
          analyzed_date?: string
          avg_views?: number
          created_at?: string | null
          frequency?: number
          id?: number
          keyword?: string
          period_days?: number
          video_count?: number
        }
        Relationships: []
      }
      micronicho_analysis_runs: {
        Row: {
          channel_id: string
          channel_name: string | null
          concentration_pct: number | null
          created_at: string | null
          id: number
          micronicho_count: number | null
          micronichos_list: Json | null
          patterns_json: Json | null
          ranking_json: Json | null
          report_text: string | null
          run_date: string | null
          total_videos_analyzed: number | null
        }
        Insert: {
          channel_id: string
          channel_name?: string | null
          concentration_pct?: number | null
          created_at?: string | null
          id?: number
          micronicho_count?: number | null
          micronichos_list?: Json | null
          patterns_json?: Json | null
          ranking_json?: Json | null
          report_text?: string | null
          run_date?: string | null
          total_videos_analyzed?: number | null
        }
        Update: {
          channel_id?: string
          channel_name?: string | null
          concentration_pct?: number | null
          created_at?: string | null
          id?: number
          micronicho_count?: number | null
          micronichos_list?: Json | null
          patterns_json?: Json | null
          ranking_json?: Json | null
          report_text?: string | null
          run_date?: string | null
          total_videos_analyzed?: number | null
        }
        Relationships: []
      }
      notificacoes: {
        Row: {
          canal_id: number | null
          created_at: string | null
          data_disparo: string | null
          data_vista: string | null
          id: number
          mensagem: string
          nome_canal: string
          nome_video: string
          periodo_dias: number
          tipo_alerta: string
          tipo_canal: string | null
          video_id: string
          views_atingidas: number
          vista: boolean | null
        }
        Insert: {
          canal_id?: number | null
          created_at?: string | null
          data_disparo?: string | null
          data_vista?: string | null
          id?: number
          mensagem: string
          nome_canal: string
          nome_video: string
          periodo_dias: number
          tipo_alerta: string
          tipo_canal?: string | null
          video_id: string
          views_atingidas: number
          vista?: boolean | null
        }
        Update: {
          canal_id?: number | null
          created_at?: string | null
          data_disparo?: string | null
          data_vista?: string | null
          id?: number
          mensagem?: string
          nome_canal?: string
          nome_video?: string
          periodo_dias?: number
          tipo_alerta?: string
          tipo_canal?: string | null
          video_id?: string
          views_atingidas?: number
          vista?: boolean | null
        }
        Relationships: [
          {
            foreignKeyName: "notificacoes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "notificacoes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "notificacoes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "notificacoes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "notificacoes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      regras_notificacoes: {
        Row: {
          ativa: boolean | null
          created_at: string | null
          id: number
          nome_regra: string
          periodo_dias: number
          subnichos: string[] | null
          tipo_canal: string | null
          views_minimas: number
        }
        Insert: {
          ativa?: boolean | null
          created_at?: string | null
          id?: number
          nome_regra: string
          periodo_dias: number
          subnichos?: string[] | null
          tipo_canal?: string | null
          views_minimas: number
        }
        Update: {
          ativa?: boolean | null
          created_at?: string | null
          id?: number
          nome_regra?: string
          periodo_dias?: number
          subnichos?: string[] | null
          tipo_canal?: string | null
          views_minimas?: number
        }
        Relationships: []
      }
      satisfaction_analysis_runs: {
        Row: {
          channel_avg_approval: number | null
          channel_avg_comment_ratio: number | null
          channel_avg_sub_ratio: number | null
          channel_id: string
          channel_name: string | null
          created_at: string | null
          id: number
          report_text: string | null
          results_json: Json | null
          run_date: string | null
          total_videos_analyzed: number | null
          total_videos_excluded: number | null
        }
        Insert: {
          channel_avg_approval?: number | null
          channel_avg_comment_ratio?: number | null
          channel_avg_sub_ratio?: number | null
          channel_id: string
          channel_name?: string | null
          created_at?: string | null
          id?: number
          report_text?: string | null
          results_json?: Json | null
          run_date?: string | null
          total_videos_analyzed?: number | null
          total_videos_excluded?: number | null
        }
        Update: {
          channel_avg_approval?: number | null
          channel_avg_comment_ratio?: number | null
          channel_avg_sub_ratio?: number | null
          channel_id?: string
          channel_name?: string | null
          created_at?: string | null
          id?: number
          report_text?: string | null
          results_json?: Json | null
          run_date?: string | null
          total_videos_analyzed?: number | null
          total_videos_excluded?: number | null
        }
        Relationships: []
      }
      subniche_trends_snapshot: {
        Row: {
          analyzed_date: string | null
          avg_views: number | null
          created_at: string | null
          engagement_rate: number | null
          id: number
          period_days: number
          snapshot_date: string | null
          subnicho: string
          total_videos: number | null
          trend_percent: number | null
        }
        Insert: {
          analyzed_date?: string | null
          avg_views?: number | null
          created_at?: string | null
          engagement_rate?: number | null
          id?: number
          period_days: number
          snapshot_date?: string | null
          subnicho: string
          total_videos?: number | null
          trend_percent?: number | null
        }
        Update: {
          analyzed_date?: string | null
          avg_views?: number | null
          created_at?: string | null
          engagement_rate?: number | null
          id?: number
          period_days?: number
          snapshot_date?: string | null
          subnicho?: string
          total_videos?: number | null
          trend_percent?: number | null
        }
        Relationships: []
      }
      theme_analysis_runs: {
        Row: {
          analyzed_video_data: Json | null
          channel_id: string
          channel_name: string | null
          concentration_pct: number | null
          created_at: string | null
          id: number
          patterns_json: Json | null
          ranking_json: Json | null
          report_text: string | null
          run_date: string | null
          run_number: number | null
          theme_count: number | null
          themes_json: Json | null
          themes_list: Json | null
          total_videos_analyzed: number | null
        }
        Insert: {
          analyzed_video_data?: Json | null
          channel_id: string
          channel_name?: string | null
          concentration_pct?: number | null
          created_at?: string | null
          id?: number
          patterns_json?: Json | null
          ranking_json?: Json | null
          report_text?: string | null
          run_date?: string | null
          run_number?: number | null
          theme_count?: number | null
          themes_json?: Json | null
          themes_list?: Json | null
          total_videos_analyzed?: number | null
        }
        Update: {
          analyzed_video_data?: Json | null
          channel_id?: string
          channel_name?: string | null
          concentration_pct?: number | null
          created_at?: string | null
          id?: number
          patterns_json?: Json | null
          ranking_json?: Json | null
          report_text?: string | null
          run_date?: string | null
          run_number?: number | null
          theme_count?: number | null
          themes_json?: Json | null
          themes_list?: Json | null
          total_videos_analyzed?: number | null
        }
        Relationships: []
      }
      title_patterns: {
        Row: {
          analyzed_date: string
          avg_views: number
          created_at: string | null
          example_title: string
          id: number
          pattern_description: string | null
          pattern_structure: string
          period_days: number
          subniche: string
          video_count: number
        }
        Insert: {
          analyzed_date?: string
          avg_views: number
          created_at?: string | null
          example_title: string
          id?: number
          pattern_description?: string | null
          pattern_structure: string
          period_days: number
          subniche: string
          video_count: number
        }
        Update: {
          analyzed_date?: string
          avg_views?: number
          created_at?: string | null
          example_title?: string
          id?: number
          pattern_description?: string | null
          pattern_structure?: string
          period_days?: number
          subniche?: string
          video_count?: number
        }
        Relationships: []
      }
      title_structure_analysis_runs: {
        Row: {
          channel_id: string
          channel_name: string | null
          created_at: string | null
          has_ctr_data: boolean | null
          id: number
          patterns_json: Json | null
          ranking_json: Json | null
          report_text: string | null
          run_date: string | null
          structure_count: number | null
          structures_list: Json | null
          total_videos_analyzed: number | null
        }
        Insert: {
          channel_id: string
          channel_name?: string | null
          created_at?: string | null
          has_ctr_data?: boolean | null
          id?: number
          patterns_json?: Json | null
          ranking_json?: Json | null
          report_text?: string | null
          run_date?: string | null
          structure_count?: number | null
          structures_list?: Json | null
          total_videos_analyzed?: number | null
        }
        Update: {
          channel_id?: string
          channel_name?: string | null
          created_at?: string | null
          has_ctr_data?: boolean | null
          id?: number
          patterns_json?: Json | null
          ranking_json?: Json | null
          report_text?: string | null
          run_date?: string | null
          structure_count?: number | null
          structures_list?: Json | null
          total_videos_analyzed?: number | null
        }
        Relationships: []
      }
      tm_collections: {
        Row: {
          avg_quality_score: number | null
          collected_at: string
          collected_date: string
          countries_collected: Json | null
          error_message: string | null
          id: number
          sources_used: Json | null
          status: string | null
          total_google: number | null
          total_hackernews: number | null
          total_trends: number | null
          total_youtube: number | null
          trends_above_50: number | null
          trends_above_70: number | null
          youtube_discovery: number | null
          youtube_subnicho: number | null
          youtube_trending: number | null
          youtube_units_used: number | null
        }
        Insert: {
          avg_quality_score?: number | null
          collected_at?: string
          collected_date: string
          countries_collected?: Json | null
          error_message?: string | null
          id?: number
          sources_used?: Json | null
          status?: string | null
          total_google?: number | null
          total_hackernews?: number | null
          total_trends?: number | null
          total_youtube?: number | null
          trends_above_50?: number | null
          trends_above_70?: number | null
          youtube_discovery?: number | null
          youtube_subnicho?: number | null
          youtube_trending?: number | null
          youtube_units_used?: number | null
        }
        Update: {
          avg_quality_score?: number | null
          collected_at?: string
          collected_date?: string
          countries_collected?: Json | null
          error_message?: string | null
          id?: number
          sources_used?: Json | null
          status?: string | null
          total_google?: number | null
          total_hackernews?: number | null
          total_trends?: number | null
          total_youtube?: number | null
          trends_above_50?: number | null
          trends_above_70?: number | null
          youtube_discovery?: number | null
          youtube_subnicho?: number | null
          youtube_trending?: number | null
          youtube_units_used?: number | null
        }
        Relationships: []
      }
      tm_patterns: {
        Row: {
          avg_quality_score: number | null
          avg_volume: number | null
          best_subnicho: string | null
          countries_found: string[] | null
          created_at: string | null
          days_active: number | null
          first_seen: string
          id: number
          is_evergreen: boolean | null
          is_growing: boolean | null
          last_seen: string
          max_volume: number | null
          sources_found: string[] | null
          title_normalized: string
          total_volume: number | null
          updated_at: string | null
          video_id: string | null
        }
        Insert: {
          avg_quality_score?: number | null
          avg_volume?: number | null
          best_subnicho?: string | null
          countries_found?: string[] | null
          created_at?: string | null
          days_active?: number | null
          first_seen: string
          id?: number
          is_evergreen?: boolean | null
          is_growing?: boolean | null
          last_seen: string
          max_volume?: number | null
          sources_found?: string[] | null
          title_normalized: string
          total_volume?: number | null
          updated_at?: string | null
          video_id?: string | null
        }
        Update: {
          avg_quality_score?: number | null
          avg_volume?: number | null
          best_subnicho?: string | null
          countries_found?: string[] | null
          created_at?: string | null
          days_active?: number | null
          first_seen?: string
          id?: number
          is_evergreen?: boolean | null
          is_growing?: boolean | null
          last_seen?: string
          max_volume?: number | null
          sources_found?: string[] | null
          title_normalized?: string
          total_volume?: number | null
          updated_at?: string | null
          video_id?: string | null
        }
        Relationships: []
      }
      tm_subnicho_matches: {
        Row: {
          collected_date: string
          created_at: string | null
          id: number
          match_score: number | null
          matched_keywords: string[] | null
          subnicho: string
          trend_id: number | null
        }
        Insert: {
          collected_date?: string
          created_at?: string | null
          id?: number
          match_score?: number | null
          matched_keywords?: string[] | null
          subnicho: string
          trend_id?: number | null
        }
        Update: {
          collected_date?: string
          created_at?: string | null
          id?: number
          match_score?: number | null
          matched_keywords?: string[] | null
          subnicho?: string
          trend_id?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "tm_subnicho_matches_trend_id_fkey"
            columns: ["trend_id"]
            isOneToOne: false
            referencedRelation: "tm_trends"
            referencedColumns: ["id"]
          },
        ]
      }
      tm_trends: {
        Row: {
          author: string | null
          category_id: string | null
          channel_id: string | null
          channel_title: string | null
          collected_at: string
          collected_date: string
          collection_type: string | null
          comment_count: number | null
          country: string | null
          duration_seconds: number | null
          engagement_ratio: number | null
          id: number
          language: string | null
          like_count: number | null
          matched_subnicho: string | null
          published_at: string | null
          quality_score: number | null
          raw_data: Json | null
          source: string
          thumbnail: string | null
          title: string
          url: string | null
          video_id: string | null
          volume: number | null
        }
        Insert: {
          author?: string | null
          category_id?: string | null
          channel_id?: string | null
          channel_title?: string | null
          collected_at?: string
          collected_date?: string
          collection_type?: string | null
          comment_count?: number | null
          country?: string | null
          duration_seconds?: number | null
          engagement_ratio?: number | null
          id?: number
          language?: string | null
          like_count?: number | null
          matched_subnicho?: string | null
          published_at?: string | null
          quality_score?: number | null
          raw_data?: Json | null
          source: string
          thumbnail?: string | null
          title: string
          url?: string | null
          video_id?: string | null
          volume?: number | null
        }
        Update: {
          author?: string | null
          category_id?: string | null
          channel_id?: string | null
          channel_title?: string | null
          collected_at?: string
          collected_date?: string
          collection_type?: string | null
          comment_count?: number | null
          country?: string | null
          duration_seconds?: number | null
          engagement_ratio?: number | null
          id?: number
          language?: string | null
          like_count?: number | null
          matched_subnicho?: string | null
          published_at?: string | null
          quality_score?: number | null
          raw_data?: Json | null
          source?: string
          thumbnail?: string | null
          title?: string
          url?: string | null
          video_id?: string | null
          volume?: number | null
        }
        Relationships: []
      }
      top_channels_snapshot: {
        Row: {
          canal_id: number
          created_at: string | null
          id: number
          rank_position: number
          snapshot_date: string
          subniche: string
          subscribers_gained_30d: number
          views_30d: number
        }
        Insert: {
          canal_id: number
          created_at?: string | null
          id?: number
          rank_position: number
          snapshot_date?: string
          subniche: string
          subscribers_gained_30d: number
          views_30d: number
        }
        Update: {
          canal_id?: number
          created_at?: string | null
          id?: number
          rank_position?: number
          snapshot_date?: string
          subniche?: string
          subscribers_gained_30d?: number
          views_30d?: number
        }
        Relationships: [
          {
            foreignKeyName: "top_channels_snapshot_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "top_channels_snapshot_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "top_channels_snapshot_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "top_channels_snapshot_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "top_channels_snapshot_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      transcriptions: {
        Row: {
          created_at: string | null
          id: string
          transcription: string
          updated_at: string | null
          video_id: string
        }
        Insert: {
          created_at?: string | null
          id?: string
          transcription: string
          updated_at?: string | null
          video_id: string
        }
        Update: {
          created_at?: string | null
          id?: string
          transcription?: string
          updated_at?: string | null
          video_id?: string
        }
        Relationships: []
      }
      video_comments: {
        Row: {
          actionable_items: Json | null
          analyzed_at: string | null
          author_channel_id: string | null
          author_name: string | null
          canal_id: number | null
          categories: string[] | null
          collected_at: string | null
          comment_id: string
          comment_text_original: string
          comment_text_pt: string | null
          created_at: string | null
          emotional_tone: string | null
          gpt_analysis: Json | null
          id: number
          insight_summary: string | null
          is_reply: boolean | null
          is_resolved: boolean | null
          is_responded: boolean | null
          is_reviewed: boolean | null
          is_translated: boolean | null
          like_count: number | null
          parent_comment_id: string | null
          primary_category: string | null
          priority_score: number | null
          published_at: string
          reply_count: number | null
          requires_response: boolean | null
          resolved_at: string | null
          responded_at: string | null
          response_generated_at: string | null
          response_tone: string | null
          reviewed_at: string | null
          sentiment_category: string | null
          sentiment_confidence: number | null
          sentiment_score: number | null
          suggested_response: string | null
          translation_updated_at: string | null
          updated_at: string | null
          urgency_level: string | null
          video_id: string
          video_title: string | null
        }
        Insert: {
          actionable_items?: Json | null
          analyzed_at?: string | null
          author_channel_id?: string | null
          author_name?: string | null
          canal_id?: number | null
          categories?: string[] | null
          collected_at?: string | null
          comment_id: string
          comment_text_original: string
          comment_text_pt?: string | null
          created_at?: string | null
          emotional_tone?: string | null
          gpt_analysis?: Json | null
          id?: number
          insight_summary?: string | null
          is_reply?: boolean | null
          is_resolved?: boolean | null
          is_responded?: boolean | null
          is_reviewed?: boolean | null
          is_translated?: boolean | null
          like_count?: number | null
          parent_comment_id?: string | null
          primary_category?: string | null
          priority_score?: number | null
          published_at: string
          reply_count?: number | null
          requires_response?: boolean | null
          resolved_at?: string | null
          responded_at?: string | null
          response_generated_at?: string | null
          response_tone?: string | null
          reviewed_at?: string | null
          sentiment_category?: string | null
          sentiment_confidence?: number | null
          sentiment_score?: number | null
          suggested_response?: string | null
          translation_updated_at?: string | null
          updated_at?: string | null
          urgency_level?: string | null
          video_id: string
          video_title?: string | null
        }
        Update: {
          actionable_items?: Json | null
          analyzed_at?: string | null
          author_channel_id?: string | null
          author_name?: string | null
          canal_id?: number | null
          categories?: string[] | null
          collected_at?: string | null
          comment_id?: string
          comment_text_original?: string
          comment_text_pt?: string | null
          created_at?: string | null
          emotional_tone?: string | null
          gpt_analysis?: Json | null
          id?: number
          insight_summary?: string | null
          is_reply?: boolean | null
          is_resolved?: boolean | null
          is_responded?: boolean | null
          is_reviewed?: boolean | null
          is_translated?: boolean | null
          like_count?: number | null
          parent_comment_id?: string | null
          primary_category?: string | null
          priority_score?: number | null
          published_at?: string
          reply_count?: number | null
          requires_response?: boolean | null
          resolved_at?: string | null
          responded_at?: string | null
          response_generated_at?: string | null
          response_tone?: string | null
          reviewed_at?: string | null
          sentiment_category?: string | null
          sentiment_confidence?: number | null
          sentiment_score?: number | null
          suggested_response?: string | null
          translation_updated_at?: string | null
          updated_at?: string | null
          urgency_level?: string | null
          video_id?: string
          video_title?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      video_comments_summary: {
        Row: {
          actionable_summary: Json | null
          analyzed_comments: number | null
          avg_confidence: number | null
          avg_sentiment_score: number | null
          canal_id: number | null
          created_at: string | null
          first_comment_at: string | null
          high_priority_count: number | null
          id: number
          last_analyzed_at: string | null
          last_comment_at: string | null
          low_priority_count: number | null
          medium_priority_count: number | null
          mixed_count: number | null
          negative_count: number | null
          negative_percentage: number | null
          neutral_count: number | null
          positive_count: number | null
          positive_percentage: number | null
          praise_count: number | null
          problems_count: number | null
          questions_count: number | null
          requires_response_count: number | null
          resolved_count: number | null
          responded_count: number | null
          reviewed_count: number | null
          suggestions_count: number | null
          top_negative_insights: Json | null
          top_positive_insights: Json | null
          top_questions: Json | null
          top_topics: string[] | null
          total_comments: number | null
          updated_at: string | null
          video_id: string
          video_title: string | null
        }
        Insert: {
          actionable_summary?: Json | null
          analyzed_comments?: number | null
          avg_confidence?: number | null
          avg_sentiment_score?: number | null
          canal_id?: number | null
          created_at?: string | null
          first_comment_at?: string | null
          high_priority_count?: number | null
          id?: number
          last_analyzed_at?: string | null
          last_comment_at?: string | null
          low_priority_count?: number | null
          medium_priority_count?: number | null
          mixed_count?: number | null
          negative_count?: number | null
          negative_percentage?: number | null
          neutral_count?: number | null
          positive_count?: number | null
          positive_percentage?: number | null
          praise_count?: number | null
          problems_count?: number | null
          questions_count?: number | null
          requires_response_count?: number | null
          resolved_count?: number | null
          responded_count?: number | null
          reviewed_count?: number | null
          suggestions_count?: number | null
          top_negative_insights?: Json | null
          top_positive_insights?: Json | null
          top_questions?: Json | null
          top_topics?: string[] | null
          total_comments?: number | null
          updated_at?: string | null
          video_id: string
          video_title?: string | null
        }
        Update: {
          actionable_summary?: Json | null
          analyzed_comments?: number | null
          avg_confidence?: number | null
          avg_sentiment_score?: number | null
          canal_id?: number | null
          created_at?: string | null
          first_comment_at?: string | null
          high_priority_count?: number | null
          id?: number
          last_analyzed_at?: string | null
          last_comment_at?: string | null
          low_priority_count?: number | null
          medium_priority_count?: number | null
          mixed_count?: number | null
          negative_count?: number | null
          negative_percentage?: number | null
          neutral_count?: number | null
          positive_count?: number | null
          positive_percentage?: number | null
          praise_count?: number | null
          problems_count?: number | null
          questions_count?: number | null
          requires_response_count?: number | null
          resolved_count?: number | null
          responded_count?: number | null
          reviewed_count?: number | null
          suggestions_count?: number | null
          top_negative_insights?: Json | null
          top_positive_insights?: Json | null
          top_questions?: Json | null
          top_topics?: string[] | null
          total_comments?: number | null
          updated_at?: string | null
          video_id?: string
          video_title?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "video_comments_summary_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "video_comments_summary_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "video_comments_summary_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "video_comments_summary_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "video_comments_summary_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      videos_historico: {
        Row: {
          canal_id: number | null
          comentarios: number | null
          data_coleta: string
          data_publicacao: string | null
          duracao: number | null
          id: number
          likes: number | null
          titulo: string
          url_video: string
          video_id: string
          views_atuais: number | null
        }
        Insert: {
          canal_id?: number | null
          comentarios?: number | null
          data_coleta: string
          data_publicacao?: string | null
          duracao?: number | null
          id?: number
          likes?: number | null
          titulo: string
          url_video: string
          video_id: string
          views_atuais?: number | null
        }
        Update: {
          canal_id?: number | null
          comentarios?: number | null
          data_coleta?: string
          data_publicacao?: string | null
          duracao?: number | null
          id?: number
          likes?: number | null
          titulo?: string
          url_video?: string
          video_id?: string
          views_atuais?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "videos_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "videos_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "videos_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "videos_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "videos_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      weekly_reports: {
        Row: {
          created_at: string | null
          id: number
          report_data: Json
          week_end: string
          week_start: string
        }
        Insert: {
          created_at?: string | null
          id?: number
          report_data: Json
          week_end: string
          week_start: string
        }
        Update: {
          created_at?: string | null
          id?: number
          report_data?: Json
          week_end?: string
          week_start?: string
        }
        Relationships: []
      }
      yt_canal_upload_diario: {
        Row: {
          channel_id: string
          channel_name: string | null
          created_at: string | null
          data: string
          erro_mensagem: string | null
          hora_processamento: string | null
          id: number
          sheets_row_number: number | null
          status: string
          tentativa_numero: number | null
          updated_at: string | null
          upload_id: number | null
          upload_realizado: boolean | null
          video_titulo: string | null
          video_url: string | null
          youtube_video_id: string | null
        }
        Insert: {
          channel_id: string
          channel_name?: string | null
          created_at?: string | null
          data: string
          erro_mensagem?: string | null
          hora_processamento?: string | null
          id?: number
          sheets_row_number?: number | null
          status?: string
          tentativa_numero?: number | null
          updated_at?: string | null
          upload_id?: number | null
          upload_realizado?: boolean | null
          video_titulo?: string | null
          video_url?: string | null
          youtube_video_id?: string | null
        }
        Update: {
          channel_id?: string
          channel_name?: string | null
          created_at?: string | null
          data?: string
          erro_mensagem?: string | null
          hora_processamento?: string | null
          id?: number
          sheets_row_number?: number | null
          status?: string
          tentativa_numero?: number | null
          updated_at?: string | null
          upload_id?: number | null
          upload_realizado?: boolean | null
          video_titulo?: string | null
          video_url?: string | null
          youtube_video_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "yt_canal_upload_diario_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: false
            referencedRelation: "yt_channel_summary"
            referencedColumns: ["channel_id"]
          },
          {
            foreignKeyName: "yt_canal_upload_diario_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: false
            referencedRelation: "yt_channels"
            referencedColumns: ["channel_id"]
          },
          {
            foreignKeyName: "yt_canal_upload_diario_upload_id_fkey"
            columns: ["upload_id"]
            isOneToOne: false
            referencedRelation: "yt_upload_queue"
            referencedColumns: ["id"]
          },
        ]
      }
      yt_canal_upload_historico: {
        Row: {
          channel_id: string
          channel_name: string
          created_at: string | null
          data: string
          erro_mensagem: string | null
          hora_processamento: string
          id: number
          sheets_row_number: number | null
          status: string
          tentativa_numero: number | null
          upload_id: number | null
          video_titulo: string | null
          video_url: string | null
          youtube_video_id: string | null
        }
        Insert: {
          channel_id: string
          channel_name: string
          created_at?: string | null
          data: string
          erro_mensagem?: string | null
          hora_processamento: string
          id?: number
          sheets_row_number?: number | null
          status: string
          tentativa_numero?: number | null
          upload_id?: number | null
          video_titulo?: string | null
          video_url?: string | null
          youtube_video_id?: string | null
        }
        Update: {
          channel_id?: string
          channel_name?: string
          created_at?: string | null
          data?: string
          erro_mensagem?: string | null
          hora_processamento?: string
          id?: number
          sheets_row_number?: number | null
          status?: string
          tentativa_numero?: number | null
          upload_id?: number | null
          video_titulo?: string | null
          video_url?: string | null
          youtube_video_id?: string | null
        }
        Relationships: []
      }
      yt_channel_credentials: {
        Row: {
          channel_id: string
          client_id: string
          client_secret: string
          created_at: string | null
          id: number
          updated_at: string | null
        }
        Insert: {
          channel_id: string
          client_id: string
          client_secret: string
          created_at?: string | null
          id?: number
          updated_at?: string | null
        }
        Update: {
          channel_id?: string
          client_id?: string
          client_secret?: string
          created_at?: string | null
          id?: number
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "fk_channel"
            columns: ["channel_id"]
            isOneToOne: true
            referencedRelation: "yt_channel_summary"
            referencedColumns: ["channel_id"]
          },
          {
            foreignKeyName: "fk_channel"
            columns: ["channel_id"]
            isOneToOne: true
            referencedRelation: "yt_channels"
            referencedColumns: ["channel_id"]
          },
        ]
      }
      yt_channel_credentials_backup: {
        Row: {
          channel_id: string | null
          client_id: string | null
          client_secret: string | null
          created_at: string | null
          id: number | null
          updated_at: string | null
        }
        Insert: {
          channel_id?: string | null
          client_id?: string | null
          client_secret?: string | null
          created_at?: string | null
          id?: number | null
          updated_at?: string | null
        }
        Update: {
          channel_id?: string | null
          client_id?: string | null
          client_secret?: string | null
          created_at?: string | null
          id?: number | null
          updated_at?: string | null
        }
        Relationships: []
      }
      yt_channels: {
        Row: {
          avg_ctr: number | null
          channel_id: string
          channel_name: string
          copy_spreadsheet_id: string | null
          created_at: string | null
          default_playlist_id: string | null
          id: number
          is_active: boolean | null
          is_monetized: boolean | null
          last_analytics_update: string | null
          last_scan_at: string | null
          last_scan_status: string | null
          lingua: string | null
          monetization_start_date: string | null
          performance_score: number | null
          projeto_api: string | null
          proxy_id: string | null
          proxy_name: string | null
          proxy_url: string | null
          show_monetization_history: boolean | null
          spreadsheet_id: string | null
          subnicho: string | null
          total_impressions: number | null
          total_subscribers: number | null
          total_videos: number | null
          updated_at: string | null
          upload_automatico: boolean | null
        }
        Insert: {
          avg_ctr?: number | null
          channel_id: string
          channel_name: string
          copy_spreadsheet_id?: string | null
          created_at?: string | null
          default_playlist_id?: string | null
          id?: number
          is_active?: boolean | null
          is_monetized?: boolean | null
          last_analytics_update?: string | null
          last_scan_at?: string | null
          last_scan_status?: string | null
          lingua?: string | null
          monetization_start_date?: string | null
          performance_score?: number | null
          projeto_api?: string | null
          proxy_id?: string | null
          proxy_name?: string | null
          proxy_url?: string | null
          show_monetization_history?: boolean | null
          spreadsheet_id?: string | null
          subnicho?: string | null
          total_impressions?: number | null
          total_subscribers?: number | null
          total_videos?: number | null
          updated_at?: string | null
          upload_automatico?: boolean | null
        }
        Update: {
          avg_ctr?: number | null
          channel_id?: string
          channel_name?: string
          copy_spreadsheet_id?: string | null
          created_at?: string | null
          default_playlist_id?: string | null
          id?: number
          is_active?: boolean | null
          is_monetized?: boolean | null
          last_analytics_update?: string | null
          last_scan_at?: string | null
          last_scan_status?: string | null
          lingua?: string | null
          monetization_start_date?: string | null
          performance_score?: number | null
          projeto_api?: string | null
          proxy_id?: string | null
          proxy_name?: string | null
          proxy_url?: string | null
          show_monetization_history?: boolean | null
          spreadsheet_id?: string | null
          subnicho?: string | null
          total_impressions?: number | null
          total_subscribers?: number | null
          total_videos?: number | null
          updated_at?: string | null
          upload_automatico?: boolean | null
        }
        Relationships: []
      }
      yt_collection_logs: {
        Row: {
          channel_id: string | null
          collected_at: string | null
          id: number
          message: string | null
          status: string
        }
        Insert: {
          channel_id?: string | null
          collected_at?: string | null
          id?: number
          message?: string | null
          status: string
        }
        Update: {
          channel_id?: string | null
          collected_at?: string | null
          id?: number
          message?: string | null
          status?: string
        }
        Relationships: [
          {
            foreignKeyName: "yt_collection_logs_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: false
            referencedRelation: "yt_channel_summary"
            referencedColumns: ["channel_id"]
          },
          {
            foreignKeyName: "yt_collection_logs_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: false
            referencedRelation: "yt_channels"
            referencedColumns: ["channel_id"]
          },
        ]
      }
      yt_country_metrics: {
        Row: {
          channel_id: string
          country_code: string
          created_at: string | null
          date: string
          id: number
          revenue: number | null
          views: number | null
          watch_time_minutes: number | null
        }
        Insert: {
          channel_id: string
          country_code: string
          created_at?: string | null
          date: string
          id?: number
          revenue?: number | null
          views?: number | null
          watch_time_minutes?: number | null
        }
        Update: {
          channel_id?: string
          country_code?: string
          created_at?: string | null
          date?: string
          id?: number
          revenue?: number | null
          views?: number | null
          watch_time_minutes?: number | null
        }
        Relationships: []
      }
      yt_daily_metrics: {
        Row: {
          avg_retention_pct: number | null
          avg_view_duration_sec: number | null
          channel_id: string
          comments: number | null
          cpm: number | null
          created_at: string | null
          ctr_approx: number | null
          date: string
          id: number
          is_estimate: boolean | null
          likes: number | null
          revenue: number | null
          rpm: number | null
          shares: number | null
          subscribers_gained: number | null
          subscribers_lost: number | null
          views: number | null
          watch_hours: number | null
          watch_time_minutes: number | null
        }
        Insert: {
          avg_retention_pct?: number | null
          avg_view_duration_sec?: number | null
          channel_id: string
          comments?: number | null
          cpm?: number | null
          created_at?: string | null
          ctr_approx?: number | null
          date: string
          id?: number
          is_estimate?: boolean | null
          likes?: number | null
          revenue?: number | null
          rpm?: number | null
          shares?: number | null
          subscribers_gained?: number | null
          subscribers_lost?: number | null
          views?: number | null
          watch_hours?: number | null
          watch_time_minutes?: number | null
        }
        Update: {
          avg_retention_pct?: number | null
          avg_view_duration_sec?: number | null
          channel_id?: string
          comments?: number | null
          cpm?: number | null
          created_at?: string | null
          ctr_approx?: number | null
          date?: string
          id?: number
          is_estimate?: boolean | null
          likes?: number | null
          revenue?: number | null
          rpm?: number | null
          shares?: number | null
          subscribers_gained?: number | null
          subscribers_lost?: number | null
          views?: number | null
          watch_hours?: number | null
          watch_time_minutes?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "yt_daily_metrics_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: false
            referencedRelation: "yt_channel_summary"
            referencedColumns: ["channel_id"]
          },
          {
            foreignKeyName: "yt_daily_metrics_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: false
            referencedRelation: "yt_channels"
            referencedColumns: ["channel_id"]
          },
        ]
      }
      yt_demographics: {
        Row: {
          age_group: string | null
          channel_id: string
          created_at: string | null
          date: string
          gender: string | null
          id: number
          percentage: number | null
          updated_at: string | null
          views: number | null
          watch_time_minutes: number | null
        }
        Insert: {
          age_group?: string | null
          channel_id: string
          created_at?: string | null
          date: string
          gender?: string | null
          id?: number
          percentage?: number | null
          updated_at?: string | null
          views?: number | null
          watch_time_minutes?: number | null
        }
        Update: {
          age_group?: string | null
          channel_id?: string
          created_at?: string | null
          date?: string
          gender?: string | null
          id?: number
          percentage?: number | null
          updated_at?: string | null
          views?: number | null
          watch_time_minutes?: number | null
        }
        Relationships: []
      }
      yt_device_metrics: {
        Row: {
          channel_id: string
          created_at: string | null
          date: string
          device_type: string
          id: number
          percentage: number | null
          updated_at: string | null
          views: number | null
          watch_time_minutes: number | null
        }
        Insert: {
          channel_id: string
          created_at?: string | null
          date: string
          device_type: string
          id?: number
          percentage?: number | null
          updated_at?: string | null
          views?: number | null
          watch_time_minutes?: number | null
        }
        Update: {
          channel_id?: string
          created_at?: string | null
          date?: string
          device_type?: string
          id?: number
          percentage?: number | null
          updated_at?: string | null
          views?: number | null
          watch_time_minutes?: number | null
        }
        Relationships: []
      }
      yt_oauth_tokens: {
        Row: {
          access_token: string | null
          channel_id: string
          created_at: string | null
          id: number
          refresh_token: string
          token_expiry: string | null
          updated_at: string | null
        }
        Insert: {
          access_token?: string | null
          channel_id: string
          created_at?: string | null
          id?: number
          refresh_token: string
          token_expiry?: string | null
          updated_at?: string | null
        }
        Update: {
          access_token?: string | null
          channel_id?: string
          created_at?: string | null
          id?: number
          refresh_token?: string
          token_expiry?: string | null
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "yt_oauth_tokens_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: true
            referencedRelation: "yt_channel_summary"
            referencedColumns: ["channel_id"]
          },
          {
            foreignKeyName: "yt_oauth_tokens_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: true
            referencedRelation: "yt_channels"
            referencedColumns: ["channel_id"]
          },
        ]
      }
      yt_oauth_tokens_backup: {
        Row: {
          access_token: string | null
          channel_id: string | null
          created_at: string | null
          id: number | null
          refresh_token: string | null
          token_expiry: string | null
          updated_at: string | null
        }
        Insert: {
          access_token?: string | null
          channel_id?: string | null
          created_at?: string | null
          id?: number | null
          refresh_token?: string | null
          token_expiry?: string | null
          updated_at?: string | null
        }
        Update: {
          access_token?: string | null
          channel_id?: string | null
          created_at?: string | null
          id?: number | null
          refresh_token?: string | null
          token_expiry?: string | null
          updated_at?: string | null
        }
        Relationships: []
      }
      yt_proxy_credentials: {
        Row: {
          client_id: string
          client_secret: string
          created_at: string | null
          id: number
          proxy_name: string
          updated_at: string | null
        }
        Insert: {
          client_id: string
          client_secret: string
          created_at?: string | null
          id?: number
          proxy_name: string
          updated_at?: string | null
        }
        Update: {
          client_id?: string
          client_secret?: string
          created_at?: string | null
          id?: number
          proxy_name?: string
          updated_at?: string | null
        }
        Relationships: []
      }
      yt_proxy_credentials_backup: {
        Row: {
          client_id: string | null
          client_secret: string | null
          created_at: string | null
          id: number | null
          proxy_name: string | null
          updated_at: string | null
        }
        Insert: {
          client_id?: string | null
          client_secret?: string | null
          created_at?: string | null
          id?: number | null
          proxy_name?: string | null
          updated_at?: string | null
        }
        Update: {
          client_id?: string | null
          client_secret?: string | null
          created_at?: string | null
          id?: number | null
          proxy_name?: string | null
          updated_at?: string | null
        }
        Relationships: []
      }
      yt_reporting_jobs: {
        Row: {
          channel_id: string
          created_at: string | null
          error_message: string | null
          id: number
          job_id: string | null
          last_report_date: string | null
          last_report_id: string | null
          report_type: string
          status: string
          updated_at: string | null
        }
        Insert: {
          channel_id: string
          created_at?: string | null
          error_message?: string | null
          id?: number
          job_id?: string | null
          last_report_date?: string | null
          last_report_id?: string | null
          report_type?: string
          status?: string
          updated_at?: string | null
        }
        Update: {
          channel_id?: string
          created_at?: string | null
          error_message?: string | null
          id?: number
          job_id?: string | null
          last_report_date?: string | null
          last_report_id?: string | null
          report_type?: string
          status?: string
          updated_at?: string | null
        }
        Relationships: []
      }
      yt_search_analytics: {
        Row: {
          channel_id: string
          created_at: string | null
          date: string
          id: number
          percentage_of_search: number | null
          search_term: string
          updated_at: string | null
          views: number | null
        }
        Insert: {
          channel_id: string
          created_at?: string | null
          date: string
          id?: number
          percentage_of_search?: number | null
          search_term: string
          updated_at?: string | null
          views?: number | null
        }
        Update: {
          channel_id?: string
          created_at?: string | null
          date?: string
          id?: number
          percentage_of_search?: number | null
          search_term?: string
          updated_at?: string | null
          views?: number | null
        }
        Relationships: []
      }
      yt_suggested_sources: {
        Row: {
          channel_id: string
          created_at: string | null
          date: string
          id: number
          source_channel_name: string | null
          source_video_id: string | null
          source_video_title: string | null
          updated_at: string | null
          views_generated: number | null
        }
        Insert: {
          channel_id: string
          created_at?: string | null
          date: string
          id?: number
          source_channel_name?: string | null
          source_video_id?: string | null
          source_video_title?: string | null
          updated_at?: string | null
          views_generated?: number | null
        }
        Update: {
          channel_id?: string
          created_at?: string | null
          date?: string
          id?: number
          source_channel_name?: string | null
          source_video_id?: string | null
          source_video_title?: string | null
          updated_at?: string | null
          views_generated?: number | null
        }
        Relationships: []
      }
      yt_traffic_summary: {
        Row: {
          channel_id: string
          created_at: string | null
          date: string
          id: number
          percentage: number | null
          source_type: string
          updated_at: string | null
          views: number | null
          watch_time_minutes: number | null
        }
        Insert: {
          channel_id: string
          created_at?: string | null
          date: string
          id?: number
          percentage?: number | null
          source_type: string
          updated_at?: string | null
          views?: number | null
          watch_time_minutes?: number | null
        }
        Update: {
          channel_id?: string
          created_at?: string | null
          date?: string
          id?: number
          percentage?: number | null
          source_type?: string
          updated_at?: string | null
          views?: number | null
          watch_time_minutes?: number | null
        }
        Relationships: []
      }
      yt_upload_daily_logs: {
        Row: {
          canais_com_erro: string[] | null
          canais_sem_video: string[] | null
          created_at: string | null
          data: string
          hora_fim: string | null
          hora_inicio: string
          id: number
          observacoes: string | null
          tentativa_numero: number | null
          total_canais: number
          total_elegiveis: number
          total_erro: number
          total_pulado: number
          total_sem_video: number
          total_sucesso: number
        }
        Insert: {
          canais_com_erro?: string[] | null
          canais_sem_video?: string[] | null
          created_at?: string | null
          data: string
          hora_fim?: string | null
          hora_inicio: string
          id?: number
          observacoes?: string | null
          tentativa_numero?: number | null
          total_canais?: number
          total_elegiveis?: number
          total_erro?: number
          total_pulado?: number
          total_sem_video?: number
          total_sucesso?: number
        }
        Update: {
          canais_com_erro?: string[] | null
          canais_sem_video?: string[] | null
          created_at?: string | null
          data?: string
          hora_fim?: string | null
          hora_inicio?: string
          id?: number
          observacoes?: string | null
          tentativa_numero?: number | null
          total_canais?: number
          total_elegiveis?: number
          total_erro?: number
          total_pulado?: number
          total_sem_video?: number
          total_sucesso?: number
        }
        Relationships: []
      }
      yt_upload_queue: {
        Row: {
          channel_id: string
          completed_at: string | null
          created_at: string | null
          descricao: string | null
          error_details: Json | null
          error_message: string | null
          error_type: string | null
          id: number
          last_retry_at: string | null
          lingua: string | null
          progress: number | null
          queue_position: number | null
          retry_count: number | null
          scheduled_at: string | null
          sheets_row_number: number | null
          spreadsheet_id: string | null
          started_at: string | null
          status: string | null
          subnicho: string | null
          tags: string[] | null
          titulo: string
          updated_at: string | null
          video_url: string
          youtube_studio_url: string | null
          youtube_video_id: string | null
        }
        Insert: {
          channel_id: string
          completed_at?: string | null
          created_at?: string | null
          descricao?: string | null
          error_details?: Json | null
          error_message?: string | null
          error_type?: string | null
          id?: number
          last_retry_at?: string | null
          lingua?: string | null
          progress?: number | null
          queue_position?: number | null
          retry_count?: number | null
          scheduled_at?: string | null
          sheets_row_number?: number | null
          spreadsheet_id?: string | null
          started_at?: string | null
          status?: string | null
          subnicho?: string | null
          tags?: string[] | null
          titulo: string
          updated_at?: string | null
          video_url: string
          youtube_studio_url?: string | null
          youtube_video_id?: string | null
        }
        Update: {
          channel_id?: string
          completed_at?: string | null
          created_at?: string | null
          descricao?: string | null
          error_details?: Json | null
          error_message?: string | null
          error_type?: string | null
          id?: number
          last_retry_at?: string | null
          lingua?: string | null
          progress?: number | null
          queue_position?: number | null
          retry_count?: number | null
          scheduled_at?: string | null
          sheets_row_number?: number | null
          spreadsheet_id?: string | null
          started_at?: string | null
          status?: string | null
          subnicho?: string | null
          tags?: string[] | null
          titulo?: string
          updated_at?: string | null
          video_url?: string
          youtube_studio_url?: string | null
          youtube_video_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "yt_upload_queue_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: false
            referencedRelation: "yt_channel_summary"
            referencedColumns: ["channel_id"]
          },
          {
            foreignKeyName: "yt_upload_queue_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: false
            referencedRelation: "yt_channels"
            referencedColumns: ["channel_id"]
          },
        ]
      }
      yt_video_daily: {
        Row: {
          avg_retention_pct: number | null
          avg_view_duration: number | null
          card_click_rate: number | null
          channel_id: string
          comments: number | null
          created_at: string | null
          ctr: number | null
          date: string
          id: number
          impressions: number | null
          likes: number | null
          revenue: number | null
          subscribers_gained: number | null
          title: string | null
          video_id: string
          views: number | null
        }
        Insert: {
          avg_retention_pct?: number | null
          avg_view_duration?: number | null
          card_click_rate?: number | null
          channel_id: string
          comments?: number | null
          created_at?: string | null
          ctr?: number | null
          date: string
          id?: number
          impressions?: number | null
          likes?: number | null
          revenue?: number | null
          subscribers_gained?: number | null
          title?: string | null
          video_id: string
          views?: number | null
        }
        Update: {
          avg_retention_pct?: number | null
          avg_view_duration?: number | null
          card_click_rate?: number | null
          channel_id?: string
          comments?: number | null
          created_at?: string | null
          ctr?: number | null
          date?: string
          id?: number
          impressions?: number | null
          likes?: number | null
          revenue?: number | null
          subscribers_gained?: number | null
          title?: string | null
          video_id?: string
          views?: number | null
        }
        Relationships: []
      }
      yt_video_metrics: {
        Row: {
          avg_retention_pct: number | null
          avg_view_duration: number | null
          card_click_rate: number | null
          channel_id: string
          comments: number | null
          created_at: string | null
          ctr: number | null
          dislikes: number | null
          id: number
          impressions: number | null
          likes: number | null
          revenue: number | null
          subscribers_gained: number | null
          title: string | null
          updated_at: string | null
          video_id: string
          views: number | null
        }
        Insert: {
          avg_retention_pct?: number | null
          avg_view_duration?: number | null
          card_click_rate?: number | null
          channel_id: string
          comments?: number | null
          created_at?: string | null
          ctr?: number | null
          dislikes?: number | null
          id?: number
          impressions?: number | null
          likes?: number | null
          revenue?: number | null
          subscribers_gained?: number | null
          title?: string | null
          updated_at?: string | null
          video_id: string
          views?: number | null
        }
        Update: {
          avg_retention_pct?: number | null
          avg_view_duration?: number | null
          card_click_rate?: number | null
          channel_id?: string
          comments?: number | null
          created_at?: string | null
          ctr?: number | null
          dislikes?: number | null
          id?: number
          impressions?: number | null
          likes?: number | null
          revenue?: number | null
          subscribers_gained?: number | null
          title?: string | null
          updated_at?: string | null
          video_id?: string
          views?: number | null
        }
        Relationships: []
      }
    }
    Views: {
      canais_com_metricas: {
        Row: {
          engagement_rate: number | null
          growth_30d: number | null
          growth_7d: number | null
          id: number | null
          inscritos: number | null
          lingua: string | null
          nicho: string | null
          nome_canal: string | null
          score_calculado: number | null
          status: string | null
          subnicho: string | null
          tipo: string | null
          ultima_coleta: string | null
          url_canal: string | null
          videos_publicados_7d: number | null
          views_15d: number | null
          views_30d: number | null
          views_60d: number | null
          views_7d: number | null
        }
        Relationships: []
      }
      canais_com_metricas_cache: {
        Row: {
          data_adicionado: string | null
          data_coleta: string | null
          engagement_rate: number | null
          id: number | null
          inscritos: number | null
          lingua: string | null
          nicho: string | null
          nome_canal: string | null
          status: string | null
          subnicho: string | null
          tipo: string | null
          ultima_coleta: string | null
          url_canal: string | null
          videos_publicados_7d: number | null
          views_15d: number | null
          views_30d: number | null
          views_60d: number | null
          views_7d: number | null
        }
        Relationships: []
      }
      mv_canal_video_stats: {
        Row: {
          canal_id: number | null
          total_videos: number | null
          total_views: number | null
        }
        Relationships: [
          {
            foreignKeyName: "videos_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "videos_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "videos_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "videos_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "videos_historico_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      mv_dashboard_completo: {
        Row: {
          canal_id: number | null
          coleta_falhas_consecutivas: number | null
          coleta_ultimo_erro: string | null
          coleta_ultimo_sucesso: string | null
          created_at: string | null
          custom_url: string | null
          data_adicionado: string | null
          data_ultimo_historico: string | null
          engagement_rate: number | null
          frequencia_semanal: number | null
          id: number | null
          inscritos: number | null
          inscritos_diff: number | null
          lingua: string | null
          melhor_dia_semana: number | null
          melhor_hora: number | null
          nicho: string | null
          nome: string | null
          nome_canal: string | null
          published_at: string | null
          status: string | null
          subnicho: string | null
          tipo: string | null
          total_comentarios_coletados: number | null
          total_video_views: number | null
          total_views: number | null
          ultima_coleta: string | null
          ultimo_comentario_coletado: string | null
          url_canal: string | null
          videos_30d: number | null
          videos_publicados_7d: number | null
          views_15d: number | null
          views_30d: number | null
          views_60d: number | null
          views_7d: number | null
        }
        Relationships: []
      }
      notificacoes_completas: {
        Row: {
          canal_id: number | null
          created_at: string | null
          data_disparo: string | null
          data_vista: string | null
          id: number | null
          lingua: string | null
          mensagem: string | null
          nome_canal: string | null
          nome_video: string | null
          periodo_dias: number | null
          subnicho: string | null
          tipo_alerta: string | null
          tipo_canal: string | null
          url_canal: string | null
          video_id: string | null
          views_atingidas: number | null
          vista: boolean | null
        }
        Relationships: [
          {
            foreignKeyName: "notificacoes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "notificacoes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "notificacoes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "notificacoes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "notificacoes_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      pending_response_view: {
        Row: {
          author_name: string | null
          canal_id: number | null
          comment_id: string | null
          comment_text_original: string | null
          id: number | null
          like_count: number | null
          nome_canal: string | null
          primary_category: string | null
          priority_score: number | null
          published_at: string | null
          response_tone: string | null
          sentiment_category: string | null
          subnicho: string | null
          suggested_response: string | null
          urgency_level: string | null
          video_id: string | null
          video_title: string | null
        }
        Relationships: [
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      priority_comments_view: {
        Row: {
          author_name: string | null
          canal_id: number | null
          comment_id: string | null
          comment_text_original: string | null
          id: number | null
          is_resolved: boolean | null
          is_responded: boolean | null
          is_reviewed: boolean | null
          like_count: number | null
          nome_canal: string | null
          primary_category: string | null
          priority_level: string | null
          priority_score: number | null
          published_at: string | null
          requires_response: boolean | null
          sentiment_category: string | null
          subnicho: string | null
          suggested_response: string | null
          urgency_level: string | null
          video_id: string | null
          video_title: string | null
        }
        Relationships: [
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_com_metricas_cache"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "canais_monitorados"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["canal_id"]
          },
          {
            foreignKeyName: "video_comments_canal_id_fkey"
            columns: ["canal_id"]
            isOneToOne: false
            referencedRelation: "mv_dashboard_completo"
            referencedColumns: ["id"]
          },
        ]
      }
      tm_evergreen: {
        Row: {
          avg_quality_score: number | null
          avg_volume: number | null
          best_subnicho: string | null
          countries_found: string[] | null
          days_active: number | null
          first_seen: string | null
          last_seen: string | null
          sources_found: string[] | null
          title: string | null
          video_id: string | null
        }
        Insert: {
          avg_quality_score?: number | null
          avg_volume?: number | null
          best_subnicho?: string | null
          countries_found?: string[] | null
          days_active?: number | null
          first_seen?: string | null
          last_seen?: string | null
          sources_found?: string[] | null
          title?: string | null
          video_id?: string | null
        }
        Update: {
          avg_quality_score?: number | null
          avg_volume?: number | null
          best_subnicho?: string | null
          countries_found?: string[] | null
          days_active?: number | null
          first_seen?: string | null
          last_seen?: string | null
          sources_found?: string[] | null
          title?: string | null
          video_id?: string | null
        }
        Relationships: []
      }
      tm_top_by_subnicho: {
        Row: {
          channel_title: string | null
          country: string | null
          language: string | null
          match_score: number | null
          quality_score: number | null
          source: string | null
          subnicho: string | null
          thumbnail: string | null
          title: string | null
          url: string | null
          video_id: string | null
          volume: number | null
        }
        Relationships: []
      }
      yt_channel_summary: {
        Row: {
          avg_daily_revenue: number | null
          avg_rpm: number | null
          channel_id: string | null
          channel_name: string | null
          days_monetized: number | null
          monetization_start_date: string | null
          total_revenue: number | null
          total_subscribers: number | null
          total_views: number | null
        }
        Relationships: []
      }
      yt_company_daily: {
        Row: {
          avg_rpm: number | null
          channels_active: number | null
          date: string | null
          net_subscribers: number | null
          total_revenue: number | null
          total_views: number | null
        }
        Relationships: []
      }
      yt_last_7_days: {
        Row: {
          avg_daily_revenue: number | null
          channel_id: string | null
          net_subs_7d: number | null
          revenue_7d: number | null
          rpm_7d: number | null
          views_7d: number | null
        }
        Relationships: [
          {
            foreignKeyName: "yt_daily_metrics_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: false
            referencedRelation: "yt_channel_summary"
            referencedColumns: ["channel_id"]
          },
          {
            foreignKeyName: "yt_daily_metrics_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: false
            referencedRelation: "yt_channels"
            referencedColumns: ["channel_id"]
          },
        ]
      }
      yt_monthly_projection: {
        Row: {
          channel_id: string | null
          projected_monthly_revenue: number | null
          projected_monthly_views: number | null
        }
        Relationships: [
          {
            foreignKeyName: "yt_daily_metrics_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: false
            referencedRelation: "yt_channel_summary"
            referencedColumns: ["channel_id"]
          },
          {
            foreignKeyName: "yt_daily_metrics_channel_id_fkey"
            columns: ["channel_id"]
            isOneToOne: false
            referencedRelation: "yt_channels"
            referencedColumns: ["channel_id"]
          },
        ]
      }
      yt_monthly_summary: {
        Row: {
          avg_rpm: number | null
          channel_name: string | null
          month: string | null
          net_subscribers: number | null
          proxy_name: string | null
          total_revenue: number | null
          total_views: number | null
          total_watch_hours: number | null
        }
        Relationships: []
      }
      yt_video_growth: {
        Row: {
          channel_id: string | null
          days_tracked: number | null
          first_date: string | null
          last_date: string | null
          revenue_growth: number | null
          title: string | null
          video_id: string | null
          views_growth: number | null
        }
        Relationships: []
      }
    }
    Functions: {
      calculate_performance_optimized: {
        Args: { cutoff_date: string }
        Returns: {
          avg_upload_time: number
          success_rate: number
          uploads_per_hour: number
        }[]
      }
      clean_old_deleted_events: { Args: never; Returns: undefined }
      delete_expired_engagement_cache: { Args: never; Returns: number }
      get_queue_stats_optimized: {
        Args: { cutoff_date: string }
        Returns: {
          completed: number
          failed: number
          pending: number
          processing: number
        }[]
      }
      refresh_all_dashboard_mvs: {
        Args: never
        Returns: {
          execution_time: string
          mv_name: string
          rows_affected: number
          status: string
        }[]
      }
      refresh_mv_canal_video_stats: { Args: never; Returns: undefined }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
