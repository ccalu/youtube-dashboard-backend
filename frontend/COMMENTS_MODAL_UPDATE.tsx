/**
 * ATUALIZAÇÃO DO MODAL DE COMENTÁRIOS - 03/02/2026
 *
 * Este arquivo contém as modificações necessárias para adicionar
 * o botão "Gerar Resposta" no modal de comentários do dashboard.
 *
 * INSTRUÇÕES:
 * 1. Localize o componente CommentsModal no Lovable
 * 2. Adicione o botão e função abaixo na área de ações de cada comentário
 * 3. O botão deve aparecer ao lado do botão "Marcar como Respondido"
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Loader2, Sparkles, CheckCircle } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

// ========== ADICIONAR ESTA FUNÇÃO NO COMPONENTE ==========

const handleGenerateResponse = async (commentId: string, index: number) => {
  setGeneratingResponse({ [index]: true });

  try {
    const response = await fetch(
      `${import.meta.env.VITE_API_URL}/api/comentarios/${commentId}/gerar-resposta`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error('Erro ao gerar resposta');
    }

    const data = await response.json();

    // Atualizar o comentário local com a resposta gerada
    setComments(prevComments =>
      prevComments.map((comment, i) =>
        i === index
          ? { ...comment, suggested_response: data.suggested_response }
          : comment
      )
    );

    toast({
      title: 'Resposta Gerada!',
      description: 'Uma resposta personalizada foi criada para este comentário.',
      variant: 'success',
    });

  } catch (error) {
    console.error('Erro ao gerar resposta:', error);
    toast({
      title: 'Erro ao gerar resposta',
      description: 'Não foi possível gerar uma resposta. Tente novamente.',
      variant: 'destructive',
    });
  } finally {
    setGeneratingResponse({ [index]: false });
  }
};

// ========== ADICIONAR ESTE ESTADO NO INÍCIO DO COMPONENTE ==========

const [generatingResponse, setGeneratingResponse] = useState<Record<number, boolean>>({});

// ========== ADICIONAR ESTE BOTÃO NA ÁREA DE AÇÕES DE CADA COMENTÁRIO ==========

{/* Botão Gerar Resposta - Adicionar antes ou depois do botão "Marcar como Respondido" */}
<Button
  variant="outline"
  size="sm"
  onClick={() => handleGenerateResponse(comment.comment_id, index)}
  disabled={generatingResponse[index] || comment.is_responded}
  className="flex items-center gap-2"
>
  {generatingResponse[index] ? (
    <>
      <Loader2 className="h-4 w-4 animate-spin" />
      Gerando...
    </>
  ) : comment.suggested_response ? (
    <>
      <Sparkles className="h-4 w-4 text-amber-500" />
      Regenerar Resposta
    </>
  ) : (
    <>
      <Sparkles className="h-4 w-4" />
      Gerar Resposta
    </>
  )}
</Button>

// ========== MODIFICAR A EXIBIÇÃO DA RESPOSTA SUGERIDA ==========

{comment.suggested_response && (
  <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
    <div className="flex items-start gap-2">
      <Sparkles className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
          Resposta Sugerida:
        </p>
        <p className="text-sm text-blue-800 dark:text-blue-200 whitespace-pre-wrap">
          {comment.suggested_response}
        </p>
        {comment.response_generated_at && (
          <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
            Gerada em: {new Date(comment.response_generated_at).toLocaleString('pt-BR')}
          </p>
        )}
      </div>
    </div>
  </div>
)}

// ========== EXEMPLO DE INTEGRAÇÃO COMPLETA ==========

{/* Este é um exemplo de como deve ficar a área de cada comentário */}
<div className="comment-item">
  {/* Informações do comentário */}
  <div className="comment-header">
    <strong>{comment.author_name}</strong>
    <span className="text-muted">{comment.like_count} likes</span>
  </div>

  <div className="comment-text">
    {comment.comment_text_pt || comment.comment_text_original}
  </div>

  {/* Resposta Sugerida (se existir) */}
  {comment.suggested_response && (
    <div className="suggested-response">
      {/* Código da resposta sugerida acima */}
    </div>
  )}

  {/* Área de Ações */}
  <div className="comment-actions flex gap-2 mt-3">
    {/* Botão Gerar Resposta */}
    <Button
      variant="outline"
      size="sm"
      onClick={() => handleGenerateResponse(comment.comment_id, index)}
      disabled={generatingResponse[index] || comment.is_responded}
    >
      {generatingResponse[index] ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin mr-2" />
          Gerando...
        </>
      ) : comment.suggested_response ? (
        <>
          <Sparkles className="h-4 w-4 mr-2 text-amber-500" />
          Regenerar
        </>
      ) : (
        <>
          <Sparkles className="h-4 w-4 mr-2" />
          Gerar Resposta
        </>
      )}
    </Button>

    {/* Botão Marcar como Respondido */}
    <Button
      variant={comment.is_responded ? "default" : "outline"}
      size="sm"
      onClick={() => handleMarkAsResponded(comment.comment_id, index)}
      disabled={!comment.suggested_response}
    >
      {comment.is_responded ? (
        <>
          <CheckCircle className="h-4 w-4 mr-2" />
          Respondido
        </>
      ) : (
        'Marcar como Respondido'
      )}
    </Button>
  </div>
</div>

// ========== NOTAS IMPORTANTES ==========

/**
 * 1. O botão "Gerar Resposta" deve estar SEMPRE visível
 * 2. Se já existe uma resposta, o botão muda para "Regenerar"
 * 3. O botão fica desabilitado enquanto gera a resposta
 * 4. A resposta gerada aparece imediatamente abaixo do comentário
 * 5. Só permite marcar como respondido se tiver uma resposta sugerida
 * 6. O endpoint retorna a resposta em português brasileiro natural
 * 7. A resposta é contextualizada com informações do canal e vídeo
 */