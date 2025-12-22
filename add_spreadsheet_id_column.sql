-- Adiciona coluna spreadsheet_id na tabela yt_upload_queue
ALTER TABLE yt_upload_queue 
ADD COLUMN spreadsheet_id TEXT;

COMMENT ON COLUMN yt_upload_queue.spreadsheet_id IS 'ID da planilha Google Sheets (para atualizar após upload)';
