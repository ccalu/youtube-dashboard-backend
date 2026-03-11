-- RPC para contar comentarios por canal (evita N+1 no Mission Control)
CREATE OR REPLACE FUNCTION count_comments_by_canal()
RETURNS TABLE(canal_id INTEGER, count BIGINT) AS $$
    SELECT canal_id, COUNT(*) as count
    FROM video_comments
    GROUP BY canal_id;
$$ LANGUAGE sql STABLE;
