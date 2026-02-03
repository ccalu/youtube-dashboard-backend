// ==================== CONFIGURAÇÃO ====================
// ⚠️ IMPORTANTE: Substituir pela URL real do seu projeto Railway
const RAILWAY_WEBHOOK_URL = 'https://SEU-PROJETO.railway.app/api/yt-upload/webhook';

// ==================== FUNÇÃO PRINCIPAL ====================
/**
 * Função disparada automaticamente quando a planilha é editada.
 * Monitora aba "Videos" e envia webhook quando vídeo está pronto para upload.
 */
function onEdit(e) {
  const sheet = e.source.getActiveSheet();

  // Só monitora aba "Videos"
  if (sheet.getName() !== 'Videos') {
    Logger.log('⏭️ Ignorando edição (não é aba Videos)');
    return;
  }

  const row = e.range.getRow();

  // Ignora header
  if (row === 1) {
    Logger.log('⏭️ Ignorando header');
    return;
  }

  // ==================== BUSCA CONFIGURAÇÃO ====================
  // Lê aba "Config" com dados do canal
  const configSheet = e.source.getSheetByName('Config');
  if (!configSheet) {
    Logger.log('❌ ERRO: Aba Config não encontrada!');
    Logger.log('💡 Crie uma aba chamada "Config" com:');
    Logger.log('   A1: CHANNEL_ID    | B1: UCxxxxxxxxxxxxxxxxx');
    Logger.log('   A2: SUBNICHO      | B2: dark_history');
    Logger.log('   A3: LINGUA        | B3: pt');
    Logger.log('   A4: NOME_CANAL    | B4: Dark History PT');
    return;
  }

  const channel_id = configSheet.getRange('B1').getValue();
  const subnicho = configSheet.getRange('B2').getValue();
  const lingua = configSheet.getRange('B3').getValue();
  const nome_canal = configSheet.getRange('B4').getValue();

  // Valida config
  if (!channel_id || !subnicho || !lingua) {
    Logger.log('❌ ERRO: Config incompleta!');
    Logger.log('   Channel ID: ' + (channel_id || '(vazio)'));
    Logger.log('   Subnicho: ' + (subnicho || '(vazio)'));
    Logger.log('   Língua: ' + (lingua || '(vazio)'));
    return;
  }

  Logger.log('✅ Config carregada: ' + nome_canal + ' (' + lingua + ')');

  // ==================== BUSCA DADOS DA LINHA ====================
  // Pega dados da linha editada (até coluna O = 15)
  const values = sheet.getRange(row, 1, 1, 15).getValues()[0];

  const titulo = values[0];        // A - Name
  const descricao = values[1];     // B - Description
  const status = values[9];        // J - Status
  const post = values[10];         // K - Post
  const video_url = values[12];    // M - youtube url (Drive link)
  const upload = values[14];       // O - Upload

  // ==================== VALIDAÇÕES ====================
  // ✅ Regra: J="done" AND K=vazio AND O=vazio

  if (status !== 'done') {
    Logger.log('⏭️ Status não é "done" (atual: "' + status + '")');
    return;
  }

  if (post && post !== '') {
    Logger.log('⏭️ Vídeo já publicado (K preenchido: "' + post + '")');
    return;
  }

  if (upload && upload !== '') {
    Logger.log('⏭️ Upload já realizado (O preenchido: "' + upload + '")');
    return;
  }

  // Verifica dados mínimos
  if (!titulo || !video_url) {
    Logger.log('⚠️ Título ou Drive URL vazios, ignorando');
    Logger.log('   Título: ' + (titulo || '(vazio)'));
    Logger.log('   Drive URL: ' + (video_url || '(vazio)'));
    return;
  }

  // ==================== PREPARA PAYLOAD ====================
  const payload = {
    video_url: video_url,
    titulo: titulo,
    descricao: descricao || '',  // COM hashtags
    channel_id: channel_id,
    subnicho: subnicho,
    lingua: lingua,
    nome_canal: nome_canal,
    sheets_row: row,
    spreadsheet_id: SpreadsheetApp.getActiveSpreadsheet().getId()
  };

  Logger.log('📤 Enviando webhook...');
  Logger.log('   Título: ' + titulo.substring(0, 50) + '...');
  Logger.log('   Canal: ' + nome_canal);
  Logger.log('   Row: ' + row);

  // ==================== ENVIA WEBHOOK ====================
  try {
    const response = UrlFetchApp.fetch(RAILWAY_WEBHOOK_URL, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });

    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();

    if (responseCode === 200) {
      Logger.log('✅ Webhook enviado com sucesso!');
      Logger.log('📥 Resposta: ' + responseText);
    } else {
      Logger.log('❌ Erro no webhook!');
      Logger.log('   Status: ' + responseCode);
      Logger.log('   Resposta: ' + responseText);

      // Marca erro na coluna O
      sheet.getRange(row, 15).setValue('❌ Erro ' + responseCode);
    }

  } catch (error) {
    Logger.log('❌ Exceção ao enviar webhook!');
    Logger.log('   Erro: ' + error.message);

    // Marca erro na coluna O
    sheet.getRange(row, 15).setValue('❌ ' + error.message.substring(0, 20));
  }
}

// ==================== FUNÇÃO DE TESTE ====================
/**
 * Função para testar o webhook manualmente.
 * Execute: Run → testWebhook
 */
function testWebhook() {
  Logger.log('🧪 Iniciando teste de webhook...');

  const configSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Config');

  if (!configSheet) {
    Logger.log('❌ Aba Config não encontrada!');
    return;
  }

  const payload = {
    video_url: 'https://drive.google.com/uc?id=TEST123',
    titulo: 'TESTE - Upload Automatizado',
    descricao: 'Teste do sistema de upload automatizado #teste #automacao',
    channel_id: configSheet.getRange('B1').getValue(),
    subnicho: configSheet.getRange('B2').getValue(),
    lingua: configSheet.getRange('B3').getValue(),
    nome_canal: configSheet.getRange('B4').getValue(),
    sheets_row: 999,
    spreadsheet_id: SpreadsheetApp.getActiveSpreadsheet().getId()
  };

  Logger.log('📤 Payload:');
  Logger.log(JSON.stringify(payload, null, 2));

  try {
    const response = UrlFetchApp.fetch(RAILWAY_WEBHOOK_URL, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });

    Logger.log('📥 Response Code: ' + response.getResponseCode());
    Logger.log('📥 Response: ' + response.getContentText());

  } catch (error) {
    Logger.log('❌ Erro: ' + error.message);
  }
}

// ==================== INSTRUÇÕES DE INSTALAÇÃO ====================
/*

📋 COMO INSTALAR ESTE SCRIPT:

1. Abra sua planilha Google Sheets
2. Extensions → Apps Script
3. Apague todo o código padrão
4. Cole este código completo
5. IMPORTANTE: Substitua RAILWAY_WEBHOOK_URL (linha 3) pela URL real do seu projeto
6. File → Save
7. Run → testWebhook (autorizar na primeira vez)
8. Configurar trigger:
   - Triggers (ícone relógio) → Add Trigger
   - Function: onEdit
   - Event source: From spreadsheet
   - Event type: On edit
   - Save

📊 ESTRUTURA DA PLANILHA:

Aba "Config":
| A              | B                        |
|----------------|--------------------------|
| CHANNEL_ID     | UCxxxxxxxxxxxxxxxxx      |
| SUBNICHO       | dark_history             |
| LINGUA         | pt                       |
| NOME_CANAL     | Dark History PT          |

Aba "Videos":
| A (Name) | B (Description) | J (Status) | K (Post) | M (Drive)        | O (Upload) |
|----------|-----------------|------------|----------|------------------|------------|
| Título 1 | Descrição #tags | done       | (vazio)  | drive.google.com | (vazio)    |

✅ TRIGGER DISPARA QUANDO:
- J (Status) = "done"
- K (Post) = vazio
- O (Upload) = vazio

✅ APÓS UPLOAD:
- Coluna O será marcada como "done" automaticamente (pelo backend)

*/
