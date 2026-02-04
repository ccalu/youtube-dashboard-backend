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
            "translations": {"total": 0, "success": 0, "errors": 0}
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

        return stats

    def save_collection_log(self, log_data: Dict[str, Any]) -> bool:
        """
        Salva log completo de uma coleta de comentários

        Args:
            log_data: Dicionário com dados da coleta

        Returns:
            bool: True se salvou com sucesso
        """
        try:
            collection_id = log_data.get('collection_id', datetime.utcnow().strftime('%Y%m%d_%H%M%S'))
            log_file = os.path.join(self.logs_dir, f"full_collection_{collection_id}.json")

            # Converter datetime para string se necessário
            if 'timestamp' in log_data and hasattr(log_data['timestamp'], 'isoformat'):
                log_data['timestamp'] = log_data['timestamp'].isoformat()

            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2, default=str)

            return True

        except Exception as e:
            print(f"Erro ao salvar log de coleta: {e}")
            return False

    def get_latest_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna os logs mais recentes

        Args:
            limit: Número máximo de logs a retornar

        Returns:
            Lista de logs ordenados por data (mais recente primeiro)
        """
        logs = []
        try:
            # Listar arquivos de log
            if not os.path.exists(self.logs_dir):
                return []

            log_files = [f for f in os.listdir(self.logs_dir) if f.startswith('full_collection_')]
            log_files.sort(reverse=True)  # Mais recente primeiro

            for log_file in log_files[:limit]:
                file_path = os.path.join(self.logs_dir, log_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                        logs.append(log_data)
                except:
                    pass

        except Exception as e:
            print(f"Erro ao buscar logs: {e}")

        return logs

    def get_logs_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Retorna resumo dos logs dos últimos dias

        Args:
            days: Número de dias para incluir

        Returns:
            Dicionário com resumo
        """
        summary = {
            "total_collections": 0,
            "total_comments": 0,
            "total_errors": 0,
            "canais_processados": set()
        }

        try:
            logs = self.get_latest_logs(limit=days * 10)  # Buscar logs suficientes

            for log in logs:
                summary["total_collections"] += 1
                summary["total_comments"] += log.get("total_comentarios", 0)
                summary["total_errors"] += len(log.get("detalhes_erros", []))

                for detalhe in log.get("detalhes_sucesso", []):
                    if "canal_id" in detalhe:
                        summary["canais_processados"].add(detalhe["canal_id"])

            summary["canais_processados"] = len(summary["canais_processados"])

        except Exception as e:
            print(f"Erro ao gerar resumo: {e}")

        return summary

    def get_log_by_id(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca um log específico pelo ID

        Args:
            collection_id: ID da coleta

        Returns:
            Dados do log ou None se não encontrado
        """
        try:
            log_file = os.path.join(self.logs_dir, f"full_collection_{collection_id}.json")

            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

            # Tentar buscar por prefixo
            if os.path.exists(self.logs_dir):
                for f in os.listdir(self.logs_dir):
                    if collection_id in f:
                        file_path = os.path.join(self.logs_dir, f)
                        with open(file_path, 'r', encoding='utf-8') as file:
                            return json.load(file)

        except Exception as e:
            print(f"Erro ao buscar log: {e}")

        return None