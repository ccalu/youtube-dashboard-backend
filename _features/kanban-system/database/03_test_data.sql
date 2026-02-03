-- Script 03: Dados de teste para o sistema Kanban
-- Data: 28/01/2025
-- Objetivo: Inserir dados de exemplo para testar o sistema

-- =====================================================
-- IMPORTANTE: Só execute se quiser dados de teste!
-- =====================================================

-- Buscar alguns canais nossos para teste
DO $$
DECLARE
    v_canal_id INTEGER;
    v_canal_nome TEXT;
BEGIN
    -- Pegar o primeiro canal não monetizado
    SELECT id, nome INTO v_canal_id, v_canal_nome
    FROM canais_monitorados
    WHERE tipo = 'nosso' AND (monetizado = false OR monetizado IS NULL)
    LIMIT 1;

    IF v_canal_id IS NOT NULL THEN
        -- Adicionar algumas notas de exemplo
        INSERT INTO kanban_notes (canal_id, note_text, note_color, position) VALUES
        (v_canal_id, 'Testando micro-nicho de Império Bizantino. Foco em batalhas épicas e queda de Constantinopla.', 'yellow', 1),
        (v_canal_id, '30 vídeos agendados para próximo mês. 1 por dia, horário fixo 18h.', 'green', 2),
        (v_canal_id, 'CTR melhorando com novos thumbnails. Manter estratégia de cores vibrantes.', 'blue', 3);

        -- Adicionar histórico de exemplo
        PERFORM log_kanban_action(
            v_canal_id,
            'note_added',
            'Nota amarela adicionada sobre teste de micro-nicho',
            jsonb_build_object('note_color', 'yellow')
        );

        PERFORM log_kanban_action(
            v_canal_id,
            'status_change',
            'Status inicial definido como Em Teste Inicial',
            jsonb_build_object('to_status', 'em_teste_inicial')
        );

        RAISE NOTICE 'Dados de teste adicionados para canal: %', v_canal_nome;
    END IF;

    -- Pegar um canal monetizado
    SELECT id, nome INTO v_canal_id, v_canal_nome
    FROM canais_monitorados
    WHERE tipo = 'nosso' AND monetizado = true
    LIMIT 1;

    IF v_canal_id IS NOT NULL THEN
        -- Definir status e adicionar notas
        UPDATE canais_monitorados
        SET
            kanban_status = 'em_crescimento',
            kanban_status_since = CURRENT_TIMESTAMP - INTERVAL '15 days'
        WHERE id = v_canal_id;

        INSERT INTO kanban_notes (canal_id, note_text, note_color, position) VALUES
        (v_canal_id, 'Canal crescendo bem! CPM alto, manter frequência de postagem.', 'green', 1),
        (v_canal_id, 'Testar live streaming semana que vem. Preparar conteúdo especial.', 'purple', 2);

        RAISE NOTICE 'Dados de teste adicionados para canal monetizado: %', v_canal_nome;
    END IF;
END $$;

-- =====================================================
-- QUERIES DE VERIFICAÇÃO
-- =====================================================

-- Ver distribuição de status
SELECT
    CASE
        WHEN monetizado THEN 'Monetizados'
        ELSE 'Não Monetizados'
    END as categoria,
    kanban_status,
    COUNT(*) as total
FROM canais_monitorados
WHERE tipo = 'nosso'
GROUP BY monetizado, kanban_status
ORDER BY monetizado DESC, kanban_status;

-- Ver canais com notas
SELECT
    c.nome,
    c.kanban_status,
    COUNT(n.id) as total_notas
FROM canais_monitorados c
LEFT JOIN kanban_notes n ON n.canal_id = c.id
WHERE c.tipo = 'nosso'
GROUP BY c.id, c.nome, c.kanban_status
HAVING COUNT(n.id) > 0;

-- Ver histórico recente
SELECT
    c.nome as canal,
    h.action_type,
    h.description,
    h.performed_at
FROM kanban_history h
JOIN canais_monitorados c ON c.id = h.canal_id
WHERE h.is_deleted = FALSE
ORDER BY h.performed_at DESC
LIMIT 10;