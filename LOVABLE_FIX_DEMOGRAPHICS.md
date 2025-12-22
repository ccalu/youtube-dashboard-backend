# CORREÇÃO URGENTE - DEMOGRAPHICS E DADOS INDIVIDUAIS

## PROBLEMA IDENTIFICADO
O backend está retornando TODOS os dados corretamente, mas o frontend NÃO está exibindo:
1. **Demographics** (idade + gênero) - NÃO APARECE
2. **Dados individuais completos** dos canais - SÓ MOSTRA revenue/views/RPM

## ENDPOINT FUNCIONANDO
```
GET https://seu-backend.railway.app/api/monetization/analytics-advanced?period=7d
GET https://seu-backend.railway.app/api/monetization/analytics-advanced?period=7d&channel_id=UCxxxxxx
```

## O QUE PRECISA SER CORRIGIDO

### 1. NA TAB "ANALYTICS AVANÇADO" DO MODAL DE MONETIZAÇÃO

#### PROBLEMA 1: Demographics não aparecem
**ONDE:** No modal de monetização, quando mostra dados agregados por subnicho
**CORREÇÃO:** Adicionar seção de Demographics com gráficos

```tsx
// ADICIONAR APÓS A SEÇÃO DE TRAFFIC SOURCES
<div className="mt-6">
  <h4 className="text-sm font-medium text-gray-700 mb-3">Demographics</h4>
  <div className="grid grid-cols-2 gap-4">
    {/* Gráfico de Idade */}
    <div className="bg-gray-50 rounded-lg p-4">
      <h5 className="text-xs font-medium text-gray-600 mb-2">Faixa Etária</h5>
      {Object.entries(subnicho.demographics || {})
        .filter(([key]) => key.includes('age'))
        .map(([key, value]) => {
          const [age, gender] = key.split('_');
          const ageLabel = age.replace('age', '').replace('-', '+ ');
          return (
            <div key={key} className="flex justify-between items-center mb-2">
              <span className="text-xs text-gray-600">{ageLabel}</span>
              <div className="flex items-center gap-2">
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${gender === 'male' ? 'bg-blue-500' : 'bg-pink-500'}`}
                    style={{ width: `${value}%` }}
                  />
                </div>
                <span className="text-xs text-gray-700 font-medium w-12 text-right">
                  {value.toFixed(1)}%
                </span>
              </div>
            </div>
          );
        })}
    </div>

    {/* Gráfico de Gênero */}
    <div className="bg-gray-50 rounded-lg p-4">
      <h5 className="text-xs font-medium text-gray-600 mb-2">Gênero</h5>
      {(() => {
        const maleTotal = Object.entries(subnicho.demographics || {})
          .filter(([key]) => key.includes('male'))
          .reduce((sum, [, value]) => sum + value, 0);
        const femaleTotal = Object.entries(subnicho.demographics || {})
          .filter(([key]) => key.includes('female'))
          .reduce((sum, [, value]) => sum + value, 0);

        return (
          <>
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs text-gray-600">Masculino</span>
              <div className="flex items-center gap-2">
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-blue-500"
                    style={{ width: `${maleTotal}%` }}
                  />
                </div>
                <span className="text-xs text-gray-700 font-medium w-12 text-right">
                  {maleTotal.toFixed(1)}%
                </span>
              </div>
            </div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs text-gray-600">Feminino</span>
              <div className="flex items-center gap-2">
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-pink-500"
                    style={{ width: `${femaleTotal}%` }}
                  />
                </div>
                <span className="text-xs text-gray-700 font-medium w-12 text-right">
                  {femaleTotal.toFixed(1)}%
                </span>
              </div>
            </div>
          </>
        );
      })()}
    </div>
  </div>
</div>
```

### 2. QUANDO CLICAR EM UM CANAL INDIVIDUAL

#### PROBLEMA 2: Só mostra revenue/views/RPM
**ONDE:** Ao clicar em um canal específico no modal
**CORREÇÃO:** Fazer chamada ao endpoint COM channel_id e mostrar TODOS os dados

```tsx
// Quando o usuário clicar em um canal
const handleChannelClick = async (channelId: string) => {
  try {
    // IMPORTANTE: Adicionar channel_id na URL
    const response = await fetch(
      `${API_URL}/api/monetization/analytics-advanced?period=${period}&channel_id=${channelId}`
    );
    const data = await response.json();

    // data agora contém todos os dados do canal:
    // - traffic_sources
    // - search_terms
    // - suggested_videos
    // - demographics
    // - devices

    setSelectedChannelData(data);
    setShowChannelDetails(true);
  } catch (error) {
    console.error('Erro ao buscar dados do canal:', error);
  }
};

// Modal de detalhes do canal
const ChannelDetailsModal = ({ channelData, onClose }) => {
  if (!channelData) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">
            {channelData.channel_name} - Analytics Detalhado
          </h3>

          {/* Revenue/Views/RPM - JÁ EXISTE */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            {/* ... código existente ... */}
          </div>

          {/* ADICIONAR: Traffic Sources */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Fontes de Tráfego</h4>
            <div className="space-y-2">
              {channelData.traffic_sources?.map((source) => (
                <div key={source.source} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{source.source}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-green-500"
                        style={{ width: `${source.percentage}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-700 font-medium">
                      {source.percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ADICIONAR: Demographics */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Demografia</h4>
            <div className="grid grid-cols-2 gap-4">
              {channelData.demographics?.map((demo) => (
                <div key={`${demo.age_group}_${demo.gender}`} className="flex justify-between items-center">
                  <span className="text-xs text-gray-600">
                    {demo.age_group.replace('age', '')} {demo.gender === 'male' ? '♂' : '♀'}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${demo.gender === 'male' ? 'bg-blue-500' : 'bg-pink-500'}`}
                        style={{ width: `${demo.percentage}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-700 font-medium">
                      {demo.percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ADICIONAR: Top Search Terms */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Top 10 Termos de Busca</h4>
            <div className="space-y-1">
              {channelData.search_terms?.slice(0, 10).map((term, index) => (
                <div key={term.term} className="flex justify-between items-center">
                  <span className="text-xs text-gray-600">
                    {index + 1}. {term.term}
                  </span>
                  <span className="text-xs text-gray-700 font-medium">
                    {term.views} views
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* ADICIONAR: Suggested Videos */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Top 10 Vídeos que Recomendam</h4>
            <div className="space-y-2">
              {channelData.suggested_videos?.slice(0, 10).map((video, index) => (
                <div key={video.source_video_id} className="border-b pb-2">
                  <div className="text-xs text-gray-700 font-medium">
                    {index + 1}. {video.source_video_title}
                  </div>
                  <div className="text-xs text-gray-500">
                    Canal: {video.source_channel_name} | Views: {video.views_generated}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ADICIONAR: Devices */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Dispositivos</h4>
            <div className="space-y-2">
              {channelData.devices?.map((device) => (
                <div key={device.device} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{device.device}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-purple-500"
                        style={{ width: `${device.percentage}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-700 font-medium">
                      {device.percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={onClose}
            className="mt-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};
```

## RESUMO DAS CORREÇÕES

1. **Demographics agregados por subnicho**: Adicionar gráficos de idade e gênero
2. **Dados individuais dos canais**:
   - Fazer chamada COM `channel_id` no parâmetro
   - Exibir TODOS os dados retornados (não só revenue/views/RPM)
   - Incluir: Traffic Sources, Demographics, Search Terms, Suggested Videos, Devices

## TESTE RÁPIDO
Para verificar se está funcionando, abra o console do navegador e execute:
```javascript
fetch('https://seu-backend.railway.app/api/monetization/analytics-advanced?period=7d&channel_id=UCuPMXZ05uQnIuj5bhAk_BPQ')
  .then(r => r.json())
  .then(console.log)
```

Você deve ver demographics, traffic_sources, search_terms, etc. no response.