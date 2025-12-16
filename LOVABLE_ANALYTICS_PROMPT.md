# 🚀 PROMPT COMPLETO PARA LOVABLE - ANALYTICS AVANÇADO

## CONTEXTO
Adicione um botão "📊 Analytics Avançado" na aba de Monetização que abre um modal com analytics detalhado dos canais monetizados, incluindo origem do tráfego, termos de busca, demographics e dispositivos.

## ENDPOINT BACKEND
```
GET /api/monetization/analytics-advanced
Query params:
- period: 24h | 3d | 7d | 15d | 30d | total | monetizacao
- subnicho: string (opcional)
- channel_id: string (opcional)
- lingua: string (opcional)
```

## COMPONENTES A CRIAR

### 1. Botão na Aba Monetização
Na aba de Monetização, adicionar um botão estilizado:
```tsx
<Button
  onClick={() => setShowAnalyticsModal(true)}
  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 transition-all duration-200"
>
  <BarChart3 className="w-5 h-5" />
  📊 Analytics Avançado
</Button>
```

### 2. Modal Principal - AdvancedAnalyticsModal.tsx
```tsx
import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart3, Search, TrendingUp, Users, Smartphone, Video, ChevronRight } from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface AdvancedAnalyticsModalProps {
  open: boolean;
  onClose: () => void;
  period: string; // Sincronizado com filtro da aba
  subnicho?: string;
  lingua?: string;
}

const AdvancedAnalyticsModal: React.FC<AdvancedAnalyticsModalProps> = ({
  open,
  onClose,
  period,
  subnicho,
  lingua
}) => {
  const [activeTab, setActiveTab] = useState('subnicho');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedChannel, setSelectedChannel] = useState(null);

  useEffect(() => {
    if (open) {
      fetchAnalytics();
    }
  }, [open, period, subnicho, lingua]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        period,
        ...(subnicho && { subnicho }),
        ...(lingua && { lingua })
      });

      const response = await fetch(`/api/monetization/analytics-advanced?${params}`);
      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error('Erro ao buscar analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchChannelDetails = async (channelId: string) => {
    try {
      const params = new URLSearchParams({
        period,
        channel_id: channelId
      });

      const response = await fetch(`/api/monetization/analytics-advanced?${params}`);
      const result = await response.json();
      setSelectedChannel(result);
    } catch (error) {
      console.error('Erro ao buscar detalhes do canal:', error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-7xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-purple-600" />
            Analytics Avançado - Canais Monetizados
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="subnicho">Por Subnicho</TabsTrigger>
            <TabsTrigger value="canais">Canais Individuais</TabsTrigger>
          </TabsList>

          {/* TAB 1: Por Subnicho */}
          <TabsContent value="subnicho" className="space-y-6">
            {loading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
              </div>
            ) : (
              data?.subnichos?.map((subnicho) => (
                <SubnichoCard key={subnicho.subnicho} data={subnicho} />
              ))
            )}
          </TabsContent>

          {/* TAB 2: Canais Individuais */}
          <TabsContent value="canais" className="space-y-6">
            {selectedChannel ? (
              <ChannelDetailsView
                channel={selectedChannel}
                onBack={() => setSelectedChannel(null)}
              />
            ) : (
              <ChannelsList
                data={data}
                onSelectChannel={fetchChannelDetails}
              />
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};
```

### 3. Componente SubnichoCard
```tsx
const SubnichoCard = ({ data }) => {
  const trafficColors = {
    'YT_SEARCH': '#4285F4',
    'RELATED_VIDEO': '#EA4335',
    'BROWSE_FEATURES': '#FBBC04',
    'EXTERNAL_URL': '#34A853',
    'OTHER': '#9E9E9E'
  };

  return (
    <Card className="border-2 hover:border-purple-400 transition-colors">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="text-lg font-bold">{data.subnicho}</span>
          <span className="text-sm text-gray-500">{data.channel_count} canais</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Fontes de Tráfego */}
        <div>
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Origem do Tráfego
          </h3>
          <div className="space-y-2">
            {data.traffic_sources?.slice(0, 4).map((source) => (
              <div key={source.source} className="flex items-center justify-between">
                <span className="text-sm flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: trafficColors[source.source] || '#9E9E9E' }}
                  />
                  {formatTrafficSource(source.source)}
                </span>
                <span className="text-sm font-medium">{source.percentage}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Termos de Busca */}
        <div>
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Search className="w-4 h-4" />
            Top 5 Termos de Busca
          </h3>
          <div className="space-y-1">
            {data.top_search_terms?.map((term, idx) => (
              <div key={term.term} className="flex items-center justify-between text-sm">
                <span className="truncate">
                  <span className="text-gray-400 mr-2">{idx + 1}.</span>
                  {term.term}
                </span>
                <span className="text-xs text-gray-500">{formatNumber(term.views)} views</span>
              </div>
            ))}
          </div>
        </div>

        {/* Dispositivos */}
        <div>
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Smartphone className="w-4 h-4" />
            Dispositivos
          </h3>
          <div className="flex gap-4 flex-wrap">
            {data.devices?.map((device) => (
              <div key={device.device} className="flex flex-col items-center">
                <div className="text-2xl font-bold text-purple-600">{device.percentage}%</div>
                <div className="text-xs text-gray-500">{formatDevice(device.device)}</div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
```

### 4. Componente ChannelDetailsView
```tsx
const ChannelDetailsView = ({ channel, onBack }) => {
  const [showVideosModal, setShowVideosModal] = useState(false);

  return (
    <div className="space-y-6">
      <Button
        variant="ghost"
        onClick={onBack}
        className="mb-4"
      >
        ← Voltar para lista
      </Button>

      <Card className="border-2 border-purple-400">
        <CardHeader>
          <CardTitle className="text-xl flex items-center justify-between">
            <span>{channel.channel?.name}</span>
            <div className="flex items-center gap-2">
              <span className="text-sm bg-purple-100 text-purple-700 px-2 py-1 rounded">
                {channel.channel?.subnicho}
              </span>
              {channel.channel?.performance_score > 0.7 && (
                <span className="text-sm bg-green-100 text-green-700 px-2 py-1 rounded">
                  ⭐ Top Performer
                </span>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Gráfico de Pizza - Fontes de Tráfego */}
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-3">Origem do Tráfego</h3>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={channel.traffic_sources?.map(t => ({
                      name: formatTrafficSource(t.source_type),
                      value: t.views
                    }))}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {channel.traffic_sources?.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Lista de Termos de Busca */}
            <div>
              <h3 className="font-semibold mb-3">Termos de Busca</h3>
              <div className="space-y-2 max-h-[200px] overflow-y-auto">
                {channel.search_terms?.map((term, idx) => (
                  <div key={term.search_term} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                    <span className="text-sm">
                      <span className="text-gray-400 mr-2">{idx + 1}.</span>
                      {term.search_term}
                    </span>
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                      {formatNumber(term.views)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Vídeos que Recomendam */}
          <div>
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Video className="w-4 h-4" />
              Top 10 Vídeos que Recomendam
            </h3>
            <div className="space-y-2">
              {channel.suggested_videos?.map((video, idx) => (
                <div key={video.source_video_id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                  <span className="text-sm truncate">
                    <span className="text-gray-400 mr-2">{idx + 1}.</span>
                    <a
                      href={`https://youtube.com/watch?v=${video.source_video_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {video.source_video_id}
                    </a>
                  </span>
                  <span className="text-xs text-gray-500">
                    {formatNumber(video.views_generated)} views
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Demographics */}
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-3">Faixa Etária</h3>
              <div className="space-y-2">
                {processAgeGroups(channel.demographics).map(age => (
                  <div key={age.group} className="flex items-center justify-between">
                    <span className="text-sm">{formatAgeGroup(age.group)}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full"
                          style={{ width: `${age.percentage}%` }}
                        />
                      </div>
                      <span className="text-xs w-10 text-right">{age.percentage}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-3">Gênero</h3>
              <div className="space-y-2">
                {processGender(channel.demographics).map(g => (
                  <div key={g.gender} className="flex items-center justify-between">
                    <span className="text-sm">{formatGender(g.gender)}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            g.gender === 'MALE' ? 'bg-blue-600' : 'bg-pink-600'
                          }`}
                          style={{ width: `${g.percentage}%` }}
                        />
                      </div>
                      <span className="text-xs w-10 text-right">{g.percentage}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Dispositivos */}
          <div>
            <h3 className="font-semibold mb-3">Dispositivos</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={channel.devices?.map(d => ({
                device: formatDevice(d.device_type),
                views: d.views,
                percentage: d.percentage
              }))}>
                <XAxis dataKey="device" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="views" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Botão Ver Vídeos */}
          <Button
            onClick={() => setShowVideosModal(true)}
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
          >
            <Video className="w-4 h-4 mr-2" />
            Ver Top 20 Vídeos do Canal
          </Button>
        </CardContent>
      </Card>

      {/* Modal de Vídeos */}
      {showVideosModal && (
        <VideosModal
          channelId={channel.channel?.id}
          channelName={channel.channel?.name}
          onClose={() => setShowVideosModal(false)}
        />
      )}
    </div>
  );
};
```

### 5. Funções Auxiliares
```tsx
// Formatar origem do tráfego
const formatTrafficSource = (source: string) => {
  const labels = {
    'YT_SEARCH': 'Busca YouTube',
    'RELATED_VIDEO': 'Vídeos Sugeridos',
    'BROWSE_FEATURES': 'Homepage/Browse',
    'EXTERNAL_URL': 'Links Externos',
    'END_SCREEN': 'Telas Finais',
    'NOTIFICATION': 'Notificações',
    'PLAYLIST': 'Playlists',
    'CHANNEL': 'Página do Canal',
    'YT_OTHER_PAGE': 'Outras Páginas YT',
    'NO_LINK_EMBEDDED': 'Embeds',
    'SHORTS': 'Shorts',
    'ADVERTISING': 'Anúncios'
  };
  return labels[source] || source;
};

// Formatar dispositivo
const formatDevice = (device: string) => {
  const labels = {
    'MOBILE': '📱 Mobile',
    'DESKTOP': '💻 Desktop',
    'TV': '📺 TV',
    'TABLET': '📱 Tablet',
    'GAME_CONSOLE': '🎮 Console',
    'UNKNOWN': '❓ Outros'
  };
  return labels[device] || device;
};

// Formatar faixa etária
const formatAgeGroup = (age: string) => {
  const labels = {
    'age13-17': '13-17 anos',
    'age18-24': '18-24 anos',
    'age25-34': '25-34 anos',
    'age35-44': '35-44 anos',
    'age45-54': '45-54 anos',
    'age55-64': '55-64 anos',
    'age65-': '65+ anos'
  };
  return labels[age] || age;
};

// Formatar gênero
const formatGender = (gender: string) => {
  const labels = {
    'MALE': '👨 Masculino',
    'FEMALE': '👩 Feminino',
    'USER_SPECIFIED_OTHER': '⚧ Outro'
  };
  return labels[gender] || gender;
};

// Formatar números
const formatNumber = (num: number) => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

// Processar demographics por idade
const processAgeGroups = (demographics: any[]) => {
  const ageGroups = {};
  demographics?.forEach(d => {
    if (!ageGroups[d.age_group]) {
      ageGroups[d.age_group] = 0;
    }
    ageGroups[d.age_group] += d.percentage;
  });

  return Object.entries(ageGroups)
    .map(([group, percentage]) => ({ group, percentage }))
    .sort((a, b) => b.percentage - a.percentage);
};

// Processar demographics por gênero
const processGender = (demographics: any[]) => {
  const genders = {};
  demographics?.forEach(d => {
    if (!genders[d.gender]) {
      genders[d.gender] = 0;
    }
    genders[d.gender] += d.percentage;
  });

  return Object.entries(genders)
    .map(([gender, percentage]) => ({ gender, percentage }))
    .sort((a, b) => b.percentage - a.percentage);
};

// Cores para gráficos
const COLORS = ['#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#6B7280'];
```

### 6. Modal de Vídeos
```tsx
const VideosModal = ({ channelId, channelName, onClose }) => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVideos();
  }, [channelId]);

  const fetchVideos = async () => {
    try {
      const response = await fetch(`/api/monetization/videos?channel_id=${channelId}&limit=20`);
      const data = await response.json();
      setVideos(data.videos || []);
    } catch (error) {
      console.error('Erro ao buscar vídeos:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Top 20 Vídeos - {channelName}</DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          </div>
        ) : (
          <div className="space-y-3">
            {videos.map((video, idx) => (
              <div key={video.video_id} className="flex items-center gap-4 p-3 border rounded-lg hover:bg-gray-50">
                <span className="text-lg font-bold text-gray-400 w-8">{idx + 1}</span>

                <div className="flex-1">
                  <a
                    href={`https://youtube.com/watch?v=${video.video_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-medium text-blue-600 hover:underline"
                  >
                    {video.title || video.video_id}
                  </a>
                  <div className="flex gap-4 mt-1 text-xs text-gray-500">
                    <span>📺 {formatNumber(video.views)} views</span>
                    <span>💰 R$ {video.revenue?.toFixed(2)}</span>
                    <span>⏱️ {video.avg_retention}% retenção</span>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-sm font-bold text-purple-600">
                    RPM: R$ {video.rpm?.toFixed(2)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
```

## INTEGRAÇÃO NA ABA MONETIZAÇÃO

No componente da aba de Monetização, adicione:

```tsx
import AdvancedAnalyticsModal from './AdvancedAnalyticsModal';

// No componente:
const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);

// No JSX, após os cards de métricas:
<div className="flex justify-end mt-6">
  <Button
    onClick={() => setShowAnalyticsModal(true)}
    className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold px-6 py-3 rounded-lg shadow-lg flex items-center gap-2"
  >
    <BarChart3 className="w-5 h-5" />
    📊 Analytics Avançado
  </Button>
</div>

{showAnalyticsModal && (
  <AdvancedAnalyticsModal
    open={showAnalyticsModal}
    onClose={() => setShowAnalyticsModal(false)}
    period={selectedPeriod} // Usar o período já selecionado na aba
    subnicho={selectedSubnicho}
    lingua={selectedLingua}
  />
)}
```

## OBSERVAÇÕES IMPORTANTES

1. **Responsividade**: Todos os componentes devem ser responsivos (mobile-first)
2. **Cache**: Implementar cache de 6h para dados (até 5h da manhã)
3. **Loading States**: Sempre mostrar loading enquanto busca dados
4. **Error Handling**: Tratar erros e mostrar mensagens apropriadas
5. **Filtros Sincronizados**: Usar os mesmos filtros da aba de monetização
6. **Performance**: Usar lazy loading para cards quando houver muitos canais

## CORES E ESTILO

- Primary: Purple (#8B5CF6)
- Secondary: Blue (#3B82F6)
- Success: Green (#10B981)
- Warning: Yellow (#F59E0B)
- Error: Red (#EF4444)
- Neutral: Gray (#6B7280)

Use gradientes purple-to-blue para elementos importantes.

## TESTE

Após implementar, teste:
1. Abrir modal com diferentes períodos
2. Trocar entre tabs
3. Clicar em canal individual
4. Abrir modal de vídeos
5. Verificar responsividade mobile