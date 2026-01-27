# -*- coding: utf-8 -*-
"""
Sistema de logs para comentários do YouTube
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class CommentsLogsManager:
    def __init__(self, logs_dir: str = "logs/comments"):
        """
        Inicializa o gerenciador de logs de comentários

        Args:
            logs_dir: Diretório onde os logs serão salvos
        """
        self.logs_dir = logs_dir
        os.makedirs(self.logs_dir, exist_ok=True)

    def log_collection(self, canal_id: int, video_id: str, comments_count: int,
                      new_comments: int, status: str, error: Optional[str] = None):
        """
        Registra uma coleta de comentários

        Args:
            canal_id: ID do canal
            video_id: ID do vídeo
            comments_count: Total de comentários coletados
            new_comments: Número de comentários novos
            status: Status da coleta (success, error, partial)
            error: Mensagem de erro se houver
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "canal_id": canal_id,
            "video_id": video_id,
            "comments_count": comments_count,
            "new_comments": new_comments,
            "status": status,
            "error": error
        }

        log_file = os.path.join(self.logs_dir, f"collection_{datetime.utcnow().strftime('%Y%m%d')}.json")

        try:
            # Lê logs existentes
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Adiciona novo log
            logs.append(log_entry)

            # Salva logs atualizados
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Erro ao salvar log de coleta: {e}")

    def log_translation(self, comment_id: str, source_lang: str,
                       target_lang: str, status: str, error: Optional[str] = None):
        """
        Registra uma tradução de comentário

        Args:
            comment_id: ID do comentário
            source_lang: Idioma de origem
            target_lang: Idioma de destino
            status: Status da tradução (success, error, skipped)
            error: Mensagem de erro se houver
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "comment_id": comment_id,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "status": status,
            "error": error
        }

        log_file = os.path.join(self.logs_dir, f"translation_{datetime.utcnow().strftime('%Y%m%d')}.json")

        try:
            # Lê logs existentes
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Adiciona novo log
            logs.append(log_entry)

            # Salva logs atualizados
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Erro ao salvar log de tradução: {e}")

    def log_gpt_analysis(self, comment_id: str, analysis_type: str,
                        status: str, tokens_used: int = 0, error: Optional[str] = None):
        """
        Registra uma análise GPT de comentário

        Args:
            comment_id: ID do comentário
            analysis_type: Tipo de análise (sentiment, suggestion)
            status: Status da análise (success, error, skipped)
            tokens_used: Tokens utilizados
            error: Mensagem de erro se houver
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "comment_id": comment_id,
            "analysis_type": analysis_type,
            "status": status,
            "tokens_used": tokens_used,
            "error": error
        }

        log_file = os.path.join(self.logs_dir, f"gpt_analysis_{datetime.utcnow().strftime('%Y%m%d')}.json")

        try:
            # Lê logs existentes
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Adiciona novo log
            logs.append(log_entry)

            # Salva logs atualizados
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Erro ao salvar log de análise GPT: {e}")

    def get_daily_stats(self, date: str) -> Dict[str, Any]:
        """
        Retorna estatísticas diárias

        Args:
            date: Data no formato YYYYMMDD

        Returns:
            Dicionário com estatísticas do dia
        """
        stats = {
            "collections": {"total": 0, "success": 0, "errors": 0},
            "translations": {"total": 0, "success": 0, "errors": 0},
            "gpt_analyses": {"total": 0, "success": 0, "errors": 0, "tokens": 0}
        }

        # Coletas
        collection_file = os.path.join(self.logs_dir, f"collection_{date}.json")
        if os.path.exists(collection_file):
            try:
                with open(collection_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    stats["collections"]["total"] = len(logs)
                    stats["collections"]["success"] = sum(1 for log in logs if log.get("status") == "success")
                    stats["collections"]["errors"] = sum(1 for log in logs if log.get("status") == "error")
            except:
                pass

        # Traduções
        translation_file = os.path.join(self.logs_dir, f"translation_{date}.json")
        if os.path.exists(translation_file):
            try:
                with open(translation_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    stats["translations"]["total"] = len(logs)
                    stats["translations"]["success"] = sum(1 for log in logs if log.get("status") == "success")
                    stats["translations"]["errors"] = sum(1 for log in logs if log.get("status") == "error")
            except:
                pass

        # Análises GPT
        gpt_file = os.path.join(self.logs_dir, f"gpt_analysis_{date}.json")
        if os.path.exists(gpt_file):
            try:
                with open(gpt_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    stats["gpt_analyses"]["total"] = len(logs)
                    stats["gpt_analyses"]["success"] = sum(1 for log in logs if log.get("status") == "success")
                    stats["gpt_analyses"]["errors"] = sum(1 for log in logs if log.get("status") == "error")
                    stats["gpt_analyses"]["tokens"] = sum(log.get("tokens_used", 0) for log in logs)
            except:
                pass

        return stats