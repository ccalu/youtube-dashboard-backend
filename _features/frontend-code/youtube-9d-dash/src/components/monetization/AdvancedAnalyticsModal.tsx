import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  BarChart3, 
  Search, 
  TrendingUp, 
  Smartphone, 
  Video, 
  ArrowLeft,
  ChevronRight,
  Loader2,
  Users
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { getSubnichoEmoji } from '@/utils/subnichoEmojis';

// Fixed subnicho order (same as TabelaCanais)
const SUBNICHO_ORDER = [
  'Histórias Sombrias',
  'Relatos de Guerra',
  'Terror',
  'Mistérios',
  'Mentalidade Masculina e Finanças',
  'Pessoas Desaparecidas',
  'Psicologia & Mindset',
  'Notícias e Atualidade',
  'Conspiração',
  'Empreendedorismo',
  'Guerras e Civilizações',
  'Histórias Motivacionais',
  'Antiguidade',
];

// Types
interface TrafficSource {
  source: string;
  source_type?: string;
  views: number;
  percentage: number;
}

interface SearchTerm {
  term: string;
  search_term?: string;
  views: number;
}

interface Device {
  device: string;
  device_type?: string;
  views: number;
  percentage: number;
}

interface Demographic {
  age_group: string;
  gender: string;
  percentage: number;
  views?: number;
}

// New API structure for demographics
interface DemographicsNewStructure {
  by_age?: { age_group: string; percentage: number }[];
  by_gender?: { gender: string; percentage: number }[];
}

type DemographicsData = Record<string, number> | Demographic[] | DemographicsNewStructure;

interface SuggestedVideo {
  source_video_id: string;
  source_video_title?: string;
  source_channel_name?: string;
  views_generated: number;
}

interface SubnichoData {
  subnicho: string;
  channel_count: number;
  traffic_sources: TrafficSource[];
  top_search_terms: SearchTerm[];
  devices: Device[];
  demographics?: DemographicsData;
}

interface ChannelFromAPI {
  channel_id: string;
  name: string;
  subnicho?: string;
  language: string;
  period_total: {
    revenue: number;
    views: number;
    rpm: number;
    last_update: string;
    last_update_formatted: string;
    badge: 'real' | 'estimate';
  };
}

interface SubnichoFromChannels {
  name: string;
  color: string;
  channels: ChannelFromAPI[];
}

interface ChannelData {
  id: string;
  channel_id: string;
  name: string;
  channel_name?: string;
  subnicho: string;
  lingua?: string;
  performance_score?: number;
  traffic_sources: TrafficSource[];
  search_terms: SearchTerm[];
  devices: Device[];
  demographics: DemographicsData;
  suggested_videos: SuggestedVideo[];
}

interface AnalyticsAdvancedData {
  subnichos: SubnichoData[];
}

interface AdvancedAnalyticsModalProps {
  open: boolean;
  onClose: () => void;
  period: string;
  subnicho?: string | null;
  lingua?: string | null;
}

// Helper functions
const normalizeString = (str: string) =>
  str.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

// getSubnichoEmoji now imported from @/utils/subnichoEmojis

const formatTrafficSource = (source: string) => {
  const labels: Record<string, string> = {
    'YT_SEARCH': 'Busca YouTube',
    'RELATED_VIDEO': 'Vídeos Sugeridos',
    'BROWSE_FEATURES': 'Homepage/Browse',
    'BROWSE': 'Homepage/Browse',
    'EXTERNAL_URL': 'Links Externos',
    'EXT_URL': 'Links Externos',
    'END_SCREEN': 'Telas Finais',
    'NOTIFICATION': 'Notificações',
    'PLAYLIST': 'Playlists',
    'CHANNEL': 'Página do Canal',
    'YT_CHANNEL': 'Página do Canal',
    'YT_OTHER_PAGE': 'Outras Páginas YT',
    'NO_LINK_EMBEDDED': 'Embeds',
    'NO_LINK_OTHER': 'Outros (sem link)',
    'SHORTS': 'Shorts',
    'ADVERTISING': 'Anúncios',
    'SUBSCRIBER': 'Recomendados',
    'SUGGESTED': 'Sugeridos',
    'EXTERNAL': 'Externos',
    'HASHTAGS': 'Hashtags',
  };
  return labels[source] || source;
};

const formatDevice = (device: string) => {
  const normalizedDevice = device?.toUpperCase() || '';
  const labels: Record<string, string> = {
    'MOBILE': '📱 Mobile',
    'DESKTOP': '💻 Desktop',
    'TV': '📺 TV',
    'TABLET': '📱 Tablet',
    'GAME_CONSOLE': '🎮 Console',
    'UNKNOWN': '❓ Outros',
  };
  return labels[normalizedDevice] || device || 'Outros';
};

const formatNumber = (num: number) => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num?.toString() || '0';
};

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value || 0);
};

// Parse demographics from API object format to array
const parseDemographics = (demographics: Record<string, number> | Demographic[] | undefined): Demographic[] => {
  if (!demographics) return [];
  
  // If already an array, return as-is
  if (Array.isArray(demographics)) return demographics;
  
  // Parse object format: {"age65-_male": 25.78, "age55-64_female": 6.32, ...}
  return Object.entries(demographics)
    .map(([key, percentage]) => {
      const parts = key.split('_');
      const age_group = parts[0]; // e.g., "age65-", "age55-64"
      const gender = parts[1] || 'unknown'; // e.g., "male", "female"
      return { age_group, gender, percentage };
    })
    .sort((a, b) => b.percentage - a.percentage);
};

// Check if demographics has new structure
const isNewDemographicsStructure = (demographics: DemographicsData | undefined): demographics is DemographicsNewStructure => {
  if (!demographics) return false;
  return typeof demographics === 'object' && !Array.isArray(demographics) && ('by_age' in demographics || 'by_gender' in demographics);
};

// Aggregate demographics by age group
const aggregateDemographicsByAge = (demographics: DemographicsData | undefined): { label: string; percentage: number }[] => {
  if (!demographics) return [];
  
  // Handle new structure with by_age array
  if (isNewDemographicsStructure(demographics)) {
    return (demographics.by_age || []).map(item => ({
      label: item.age_group.replace('age', '').replace('-', ' - '),
      percentage: item.percentage
    })).sort((a, b) => b.percentage - a.percentage);
  }
  
  const ageGroups: Record<string, number> = {};
  
  if (Array.isArray(demographics)) {
    demographics.forEach(d => {
      const label = d.age_group.replace('age', '').replace('-', ' - ');
      ageGroups[label] = (ageGroups[label] || 0) + d.percentage;
    });
  } else {
    Object.entries(demographics).forEach(([key, value]) => {
      const age = key.split('_')[0];
      const label = age.replace('age', '').replace('-', ' - ');
      ageGroups[label] = (ageGroups[label] || 0) + value;
    });
  }
  
  return Object.entries(ageGroups)
    .map(([label, percentage]) => ({ label, percentage }))
    .sort((a, b) => b.percentage - a.percentage);
};

// Aggregate demographics by gender
const aggregateDemographicsByGender = (demographics: DemographicsData | undefined): { male: number; female: number } => {
  if (!demographics) return { male: 0, female: 0 };
  
  // Handle new structure with by_gender array
  if (isNewDemographicsStructure(demographics)) {
    let male = 0;
    let female = 0;
    (demographics.by_gender || []).forEach(item => {
      if (item.gender === 'male') male = item.percentage;
      else if (item.gender === 'female') female = item.percentage;
    });
    return { male, female };
  }
  
  let male = 0;
  let female = 0;
  
  if (Array.isArray(demographics)) {
    demographics.forEach(d => {
      if (d.gender === 'male') male += d.percentage;
      else if (d.gender === 'female') female += d.percentage;
    });
  } else {
    Object.entries(demographics).forEach(([key, value]) => {
      if (key.includes('male') && !key.includes('female')) male += value;
      else if (key.includes('female')) female += value;
    });
  }
  
  return { male, female };
};

const TRAFFIC_COLORS: Record<string, string> = {
  'YT_SEARCH': '#4285F4',
  'RELATED_VIDEO': '#EA4335',
  'BROWSE_FEATURES': '#FBBC04',
  'EXTERNAL_URL': '#34A853',
  'OTHER': '#9E9E9E',
};

const CHART_COLORS = ['#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#6B7280'];

const LANGUAGE_FLAGS: Record<string, string> = {
  pt: '🇧🇷',
  portuguese: '🇧🇷',
  português: '🇧🇷',
  en: '🇺🇸',
  english: '🇺🇸',
  es: '🇪🇸',
  spanish: '🇪🇸',
  espanhol: '🇪🇸',
  de: '🇩🇪',
  german: '🇩🇪',
  alemão: '🇩🇪',
  fr: '🇫🇷',
  french: '🇫🇷',
  francês: '🇫🇷',
  ko: '🇰🇷',
  korean: '🇰🇷',
  coreano: '🇰🇷',
  ar: '🇸🇦',
  arabic: '🇸🇦',
  árabe: '🇸🇦',
  arabe: '🇸🇦',
};

const getLanguageFlag = (lingua: string | undefined): string => {
  if (!lingua) return '🌐';
  const normalized = lingua.toLowerCase().trim();
  return LANGUAGE_FLAGS[normalized] || '🌐';
};

// Sort subnichos by fixed order
const sortSubnichos = <T extends { subnicho?: string; name?: string }>(items: T[]): T[] => {
  return [...items].sort((a, b) => {
    const nameA = a.subnicho || a.name || '';
    const nameB = b.subnicho || b.name || '';
    const indexA = SUBNICHO_ORDER.findIndex(s => normalizeString(s) === normalizeString(nameA));
    const indexB = SUBNICHO_ORDER.findIndex(s => normalizeString(s) === normalizeString(nameB));
    if (indexA === -1 && indexB === -1) return 0;
    if (indexA === -1) return 1;
    if (indexB === -1) return -1;
    return indexA - indexB;
  });
};

// Subnicho Card Component - matching TabelaCanais style
const SubnichoCard: React.FC<{ 
  data: SubnichoData;
  animationDelay?: number;
}> = ({ data, animationDelay = 0 }) => {
  const [collapsed, setCollapsed] = useState(true);
  const cores = obterCorSubnicho(data.subnicho);
  const color = cores.fundo;

  const hasData = (data.traffic_sources?.length > 0 || data.top_search_terms?.length > 0 || data.devices?.length > 0);

  return (
    <Card 
      className="overflow-hidden border-2 opacity-0 animate-fade-in-up"
      style={{ 
        animationDelay: `${animationDelay}ms`,
        borderColor: `${color}60`,
        backgroundColor: `${color}10`,
      }}
    >
      <CardHeader
        className="border-b-2 p-3 sm:p-4 cursor-pointer"
        style={{
          backgroundColor: `${color}25`,
          borderBottomColor: color,
        }}
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-2 sm:gap-3">
          <span className="text-lg sm:text-2xl flex-shrink-0">{getSubnichoEmoji(data.subnicho)}</span>
          <CardTitle className="text-sm sm:text-lg font-bold text-foreground truncate flex-1">{data.subnicho}</CardTitle>
          <Badge
            variant="secondary"
            className="text-xs border-2 font-bold px-2 py-1"
            style={{
              backgroundColor: `${color}50`,
              color: 'white',
              borderColor: color,
            }}
          >
            {data.channel_count} canais
          </Badge>
          <span className="text-foreground/80 text-sm font-medium">
            {collapsed ? '▼' : '▲'}
          </span>
        </div>
      </CardHeader>
      
      {!collapsed && (
        <CardContent className="p-4 space-y-4">
          {!hasData ? (
            <p className="text-sm text-foreground/70 text-center py-4">
              Dados de analytics não disponíveis para este período
            </p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Traffic Sources */}
              {data.traffic_sources?.length > 0 && (
                <Card className="border-2" style={{ borderColor: `${color}50`, backgroundColor: `${color}15` }}>
                  <CardHeader className="py-3 px-4" style={{ backgroundColor: `${color}30` }}>
                    <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
                      <TrendingUp className="w-4 h-4" />
                      Origem do Tráfego
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4">
                    <div className="space-y-2.5">
                      {data.traffic_sources.slice(0, 5).map((source, idx) => (
                        <div key={source.source || source.source_type} className="flex items-center justify-between">
                          <span className="text-sm flex items-center gap-2 text-foreground/90 font-medium">
                            <span className="w-5 text-center text-xs text-foreground/60 font-bold">{idx + 1}.</span>
                            <div
                              className="w-3 h-3 rounded-full flex-shrink-0"
                              style={{
                                backgroundColor: TRAFFIC_COLORS[source.source || source.source_type || ''] || '#9E9E9E',
                              }}
                            />
                            {formatTrafficSource(source.source || source.source_type || '')}
                          </span>
                          <Badge variant="outline" className="text-xs px-2 py-0.5 font-bold border-2" style={{ borderColor: `${color}60`, color: 'white', backgroundColor: `${color}40` }}>
                            {source.percentage?.toFixed(1)}%
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Top Search Terms */}
              {data.top_search_terms?.length > 0 && (
                <Card className="border-2" style={{ borderColor: `${color}50`, backgroundColor: `${color}15` }}>
                  <CardHeader className="py-3 px-4" style={{ backgroundColor: `${color}30` }}>
                    <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
                      <Search className="w-4 h-4" />
                      Top 5 Termos de Busca
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4">
                    <div className="space-y-2">
                      {data.top_search_terms.slice(0, 5).map((term, idx) => (
                        <div key={term.term || term.search_term} className="flex items-center justify-between text-sm gap-2">
                          <span className="truncate text-foreground/90 font-medium flex-1">
                            <span className="text-foreground/60 mr-2 font-bold">{idx + 1}.</span>
                            {term.term || term.search_term}
                          </span>
                          <Badge className="text-xs px-2 py-0.5 font-bold bg-blue-500/40 text-white border border-blue-400">
                            {formatNumber(term.views)}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Devices - 2 columns x 2 rows, sorted descending */}
              {data.devices?.length > 0 && (
                <Card className="border-2" style={{ borderColor: `${color}50`, backgroundColor: `${color}15` }}>
                  <CardHeader className="py-3 px-4" style={{ backgroundColor: `${color}30` }}>
                    <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
                      <Smartphone className="w-4 h-4" />
                      Dispositivos
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4">
                    <div className="grid grid-cols-2 gap-3">
                      {[...data.devices].sort((a, b) => (b.percentage || 0) - (a.percentage || 0)).slice(0, 4).map((device) => (
                        <div 
                          key={device.device || device.device_type} 
                          className="flex flex-col items-center p-3 rounded-lg border-2"
                          style={{ backgroundColor: `${color}25`, borderColor: `${color}50` }}
                        >
                          <div className="text-xl font-black text-white">{device.percentage?.toFixed(0)}%</div>
                          <div className="text-xs text-foreground/80 text-center font-semibold mt-1">
                            {formatDevice(device.device || device.device_type || '')}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Demographics - Two columns: Age + Gender (side by side with Devices) */}
              {data.demographics && (isNewDemographicsStructure(data.demographics) || (Array.isArray(data.demographics) ? data.demographics.length > 0 : Object.keys(data.demographics).length > 0)) && (
                <Card className="border-2" style={{ borderColor: `${color}50`, backgroundColor: `${color}15` }}>
                  <CardHeader className="py-3 px-4" style={{ backgroundColor: `${color}30` }}>
                    <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
                      <Users className="w-4 h-4" />
                      Dados Demográficos
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Age Distribution */}
                      <div className="p-3 rounded-lg border-2" style={{ backgroundColor: `${color}20`, borderColor: `${color}40` }}>
                        <h5 className="text-xs font-bold text-foreground/90 mb-3 flex items-center gap-2">
                          📊 Por Faixa Etária
                        </h5>
                        <div className="space-y-2.5">
                          {aggregateDemographicsByAge(data.demographics).slice(0, 6).map((item) => (
                            <div key={item.label}>
                              <div className="flex justify-between text-xs mb-1">
                                <span className="text-foreground/80 font-medium">{item.label} anos</span>
                                <span className="text-white font-bold">{item.percentage.toFixed(1)}%</span>
                              </div>
                              <div className="w-full bg-black/30 rounded-full h-2">
                                <div
                                  className="h-2 rounded-full bg-blue-500"
                                  style={{ width: `${Math.min(item.percentage, 100)}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Gender Distribution */}
                      <div className="p-3 rounded-lg border-2" style={{ backgroundColor: `${color}20`, borderColor: `${color}40` }}>
                        <h5 className="text-xs font-bold text-foreground/90 mb-3 flex items-center gap-2">
                          👥 Por Gênero
                        </h5>
                        {(() => {
                          const { male, female } = aggregateDemographicsByGender(data.demographics);
                          return (
                            <div className="space-y-3">
                              <div>
                                <div className="flex justify-between text-xs mb-1">
                                  <span className="text-foreground/80 font-medium">♂ Masculino</span>
                                  <span className="text-white font-bold">{male.toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-black/30 rounded-full h-3">
                                  <div
                                    className="h-3 rounded-full bg-blue-500"
                                    style={{ width: `${Math.min(male, 100)}%` }}
                                  />
                                </div>
                              </div>
                              <div>
                                <div className="flex justify-between text-xs mb-1">
                                  <span className="text-foreground/80 font-medium">♀ Feminino</span>
                                  <span className="text-white font-bold">{female.toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-black/30 rounded-full h-3">
                                  <div
                                    className="h-3 rounded-full bg-pink-500"
                                    style={{ width: `${Math.min(female, 100)}%` }}
                                  />
                                </div>
                              </div>
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
};

// Channels List grouped by subnicho with collapsed cards
const ChannelsList: React.FC<{
  subnichos: SubnichoFromChannels[];
  onSelectChannel: (channel: ChannelFromAPI, subnichoName: string) => void;
}> = ({ subnichos, onSelectChannel }) => {
  const [expandedSubnichos, setExpandedSubnichos] = useState<Set<string>>(new Set());
  const sortedSubnichos = sortSubnichos(subnichos);

  const toggleSubnicho = (name: string) => {
    setExpandedSubnichos(prev => {
      const newSet = new Set(prev);
      if (newSet.has(name)) {
        newSet.delete(name);
      } else {
        newSet.add(name);
      }
      return newSet;
    });
  };

  return (
    <div className="space-y-3">
      {sortedSubnichos.map((subnicho, idx) => {
        const cores = obterCorSubnicho(subnicho.name);
        const isExpanded = expandedSubnichos.has(subnicho.name);
        
        return (
          <Card 
            key={subnicho.name} 
            className="overflow-hidden border-2 opacity-0 animate-fade-in-up"
            style={{ 
              animationDelay: `${idx * 100}ms`,
              borderColor: `${cores.fundo}60`,
              backgroundColor: `${cores.fundo}10`,
            }}
          >
            <CardHeader
              className="border-b-2 p-3 sm:p-4 cursor-pointer"
              style={{
                backgroundColor: `${cores.fundo}25`,
                borderBottomColor: cores.fundo,
              }}
              onClick={() => toggleSubnicho(subnicho.name)}
            >
              <div className="flex items-center gap-2 sm:gap-3">
                <span className="text-lg sm:text-2xl flex-shrink-0">{getSubnichoEmoji(subnicho.name)}</span>
                <CardTitle className="text-sm sm:text-lg font-bold text-foreground truncate flex-1">{subnicho.name}</CardTitle>
                <Badge
                  variant="secondary"
                  className="text-xs border-2 font-bold px-2 py-1"
                  style={{
                    backgroundColor: `${cores.fundo}50`,
                    color: 'white',
                    borderColor: cores.fundo,
                  }}
                >
                  {subnicho.channels.length} canais
                </Badge>
                <span className="text-foreground/80 text-sm font-medium">
                  {isExpanded ? '▲' : '▼'}
                </span>
              </div>
            </CardHeader>
            
            {isExpanded && (
              <CardContent className="p-3 space-y-2">
                {subnicho.channels.map((channel, channelIdx) => (
                  <Card
                    key={channel.channel_id}
                    className="p-3 cursor-pointer hover:shadow-md transition-all border-l-4"
                    style={{
                      backgroundColor: `${cores.fundo}20`,
                      borderLeftColor: cores.borda,
                    }}
                    onClick={() => onSelectChannel(channel, subnicho.name)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <span className="text-lg">{getLanguageFlag(channel.language)}</span>
                        <p className="font-medium text-sm truncate">{channel.name}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <p className="text-sm font-semibold text-green-500">{formatCurrency(channel.period_total.revenue)}</p>
                          <p className="text-[10px] text-muted-foreground">RPM: {formatCurrency(channel.period_total.rpm)}</p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-muted-foreground" />
                      </div>
                    </div>
                  </Card>
                ))}
              </CardContent>
            )}
          </Card>
        );
      })}
    </div>
  );
};

// Channel Details View Component
const ChannelDetailsView: React.FC<{
  channel: ChannelFromAPI;
  subnichoName: string;
  channelDetails: ChannelData | null;
  loading: boolean;
  onBack: () => void;
}> = ({ channel, subnichoName, channelDetails, loading, onBack }) => {
  const cores = obterCorSubnicho(subnichoName);

  return (
    <div className="space-y-4">
      <Button variant="ghost" onClick={onBack} className="mb-2">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Voltar para lista
      </Button>

      <Card
        className="border-2"
        style={{
          backgroundColor: `${cores.fundo}40`,
          borderColor: cores.borda,
        }}
      >
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span>{getLanguageFlag(channel.language)}</span>
              <span>{channel.name}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm">{getSubnichoEmoji(subnichoName)}</span>
              <Badge variant="secondary" style={{ backgroundColor: `${cores.fundo}40`, color: 'white' }}>
                {subnichoName}
              </Badge>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Revenue Info */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-lg bg-green-500/10 text-center border border-green-500/30">
              <p className="text-xs text-muted-foreground">Revenue</p>
              <p className="text-lg font-bold text-green-500">{formatCurrency(channel.period_total.revenue)}</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-500/10 text-center border border-blue-500/30">
              <p className="text-xs text-muted-foreground">Views</p>
              <p className="text-lg font-bold text-blue-500">{formatNumber(channel.period_total.views)}</p>
            </div>
            <div className="p-3 rounded-lg bg-yellow-500/10 text-center border border-yellow-500/30">
              <p className="text-xs text-muted-foreground">RPM</p>
              <p className="text-lg font-bold text-yellow-500">{formatCurrency(channel.period_total.rpm)}</p>
            </div>
          </div>

          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
            </div>
          ) : channelDetails ? (
            <div className="space-y-4">
              {/* First Row: Traffic Sources | Search Terms | Devices - 3 columns */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Traffic Sources */}
              {channelDetails.traffic_sources?.length > 0 && (
                <Card className="border-2" style={{ borderColor: `${cores.fundo}50`, backgroundColor: `${cores.fundo}15` }}>
                  <CardHeader className="py-2 px-3" style={{ backgroundColor: `${cores.fundo}30` }}>
                    <CardTitle className="text-xs font-bold flex items-center gap-2 text-foreground">
                      <TrendingUp className="w-3 h-3" />
                      Origem do Tráfego
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-3">
                    <div className="space-y-2">
                      {channelDetails.traffic_sources.slice(0, 4).map((source, idx) => (
                        <div key={`traffic-${idx}`} className="flex items-center gap-2 text-xs">
                          <div
                            className="w-2 h-2 rounded-full flex-shrink-0"
                            style={{ backgroundColor: CHART_COLORS[idx % CHART_COLORS.length] }}
                          />
                          <span className="text-foreground/90 font-medium truncate flex-1">
                            {formatTrafficSource(source.source || source.source_type || '')}
                          </span>
                          <Badge variant="outline" className="text-[10px] px-1.5 py-0 font-bold border" style={{ borderColor: `${cores.fundo}60`, color: 'white', backgroundColor: `${cores.fundo}40` }}>
                            {source.percentage?.toFixed(0)}%
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Search Terms */}
              {channelDetails.search_terms?.length > 0 && (
                <Card className="border-2" style={{ borderColor: `${cores.fundo}50`, backgroundColor: `${cores.fundo}15` }}>
                  <CardHeader className="py-2 px-3" style={{ backgroundColor: `${cores.fundo}30` }}>
                    <CardTitle className="text-xs font-bold flex items-center gap-2 text-foreground">
                      <Search className="w-3 h-3" />
                      Top 5 Termos de Busca
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-3">
                    <div className="space-y-1.5">
                      {channelDetails.search_terms.slice(0, 5).map((term, idx) => (
                        <div
                          key={`term-${idx}`}
                          className="flex items-center gap-2 text-xs"
                        >
                          <span className="text-foreground/60 font-bold w-4">{idx + 1}.</span>
                          <span className="text-foreground/90 font-medium truncate flex-1">
                            {term.term || term.search_term}
                          </span>
                          <Badge className="text-[10px] px-1.5 py-0 font-bold bg-blue-500/40 text-white border border-blue-400">
                            {formatNumber(term.views)}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Devices - 2 columns x 2 rows, sorted descending */}
              {channelDetails.devices?.length > 0 && (
                <Card className="border-2" style={{ borderColor: `${cores.fundo}50`, backgroundColor: `${cores.fundo}15` }}>
                  <CardHeader className="py-2 px-3" style={{ backgroundColor: `${cores.fundo}30` }}>
                    <CardTitle className="text-xs font-bold flex items-center gap-2 text-foreground">
                      <Smartphone className="w-3 h-3" />
                      Dispositivos
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-3">
                    <div className="grid grid-cols-2 gap-1.5">
                      {[...channelDetails.devices].sort((a, b) => (b.percentage || 0) - (a.percentage || 0)).slice(0, 4).map((device, idx) => {
                        const deviceKey = device.device || device.device_type || `device-${idx}`;
                        return (
                          <div 
                            key={`device-${idx}-${deviceKey}`}
                            className="flex flex-col items-center p-1.5 rounded-lg border"
                            style={{ backgroundColor: `${cores.fundo}25`, borderColor: `${cores.fundo}50` }}
                          >
                            <div className="text-sm font-black text-white">{device.percentage?.toFixed(0)}%</div>
                            <div className="text-[9px] text-foreground/80 text-center font-semibold">
                              {formatDevice(deviceKey)}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              )}
              </div>

              {/* Second Row: Demographics | Suggested Videos - 2 columns */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Demographics - Two columns: Age + Gender */}
              {channelDetails.demographics && (isNewDemographicsStructure(channelDetails.demographics) || (Array.isArray(channelDetails.demographics) ? channelDetails.demographics.length > 0 : Object.keys(channelDetails.demographics).length > 0)) && (
                <Card className="border-2" style={{ borderColor: `${cores.fundo}50`, backgroundColor: `${cores.fundo}15` }}>
                  <CardHeader className="py-3 px-4" style={{ backgroundColor: `${cores.fundo}30` }}>
                    <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
                      <Users className="w-4 h-4" />
                      Dados Demográficos
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Age Distribution */}
                      <div className="p-3 rounded-lg border-2" style={{ backgroundColor: `${cores.fundo}20`, borderColor: `${cores.fundo}40` }}>
                        <h5 className="text-xs font-bold text-foreground/90 mb-3 flex items-center gap-2">
                          📊 Por Faixa Etária
                        </h5>
                        <div className="space-y-2.5">
                          {aggregateDemographicsByAge(channelDetails.demographics).slice(0, 6).map((item) => (
                            <div key={item.label}>
                              <div className="flex justify-between text-xs mb-1">
                                <span className="text-foreground/80 font-medium">{item.label} anos</span>
                                <span className="text-white font-bold">{item.percentage.toFixed(1)}%</span>
                              </div>
                              <div className="w-full bg-black/30 rounded-full h-2">
                                <div
                                  className="h-2 rounded-full bg-blue-500"
                                  style={{ width: `${Math.min(item.percentage, 100)}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Gender Distribution */}
                      <div className="p-3 rounded-lg border-2" style={{ backgroundColor: `${cores.fundo}20`, borderColor: `${cores.fundo}40` }}>
                        <h5 className="text-xs font-bold text-foreground/90 mb-3 flex items-center gap-2">
                          👥 Por Gênero
                        </h5>
                        {(() => {
                          const { male, female } = aggregateDemographicsByGender(channelDetails.demographics);
                          return (
                            <div className="space-y-3">
                              <div>
                                <div className="flex justify-between text-xs mb-1">
                                  <span className="text-foreground/80 font-medium">♂ Masculino</span>
                                  <span className="text-white font-bold">{male.toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-black/30 rounded-full h-3">
                                  <div
                                    className="h-3 rounded-full bg-blue-500"
                                    style={{ width: `${Math.min(male, 100)}%` }}
                                  />
                                </div>
                              </div>
                              <div>
                                <div className="flex justify-between text-xs mb-1">
                                  <span className="text-foreground/80 font-medium">♀ Feminino</span>
                                  <span className="text-white font-bold">{female.toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-black/30 rounded-full h-3">
                                  <div
                                    className="h-3 rounded-full bg-pink-500"
                                    style={{ width: `${Math.min(female, 100)}%` }}
                                  />
                                </div>
                              </div>
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Suggested Videos */}
              {channelDetails.suggested_videos?.length > 0 && (
                <Card className="border-2" style={{ borderColor: `${cores.fundo}50`, backgroundColor: `${cores.fundo}15` }}>
                  <CardHeader className="py-3 px-4" style={{ backgroundColor: `${cores.fundo}30` }}>
                    <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
                      <Video className="w-4 h-4" />
                      Vídeos que Recomendam
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4">
                    <div className="space-y-2 max-h-[200px] overflow-y-auto">
                      {channelDetails.suggested_videos.slice(0, 10).map((video, idx) => (
                        <div
                          key={video.source_video_id}
                          className="flex items-center justify-between text-sm gap-2"
                        >
                          <span className="truncate flex-1 text-foreground/90 font-medium">
                            <span className="mr-2 text-foreground/60 font-bold">{idx + 1}.</span>
                            <a
                              href={`https://youtube.com/watch?v=${video.source_video_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-400 hover:underline hover:text-blue-300"
                            >
                              {video.source_video_title || video.source_video_id}
                            </a>
                          </span>
                          <Badge className="text-xs px-2 py-0.5 font-bold bg-green-500/40 text-white border border-green-400">
                            {formatNumber(video.views_generated)} views
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
              </div>
            </div>
          ) : (
            <p className="text-sm text-foreground/70 text-center py-4">
              Dados detalhados não disponíveis para este canal
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Main Modal Component
export const AdvancedAnalyticsModal: React.FC<AdvancedAnalyticsModalProps> = ({
  open,
  onClose,
  period,
  subnicho,
  lingua,
}) => {
  const [activeTab, setActiveTab] = useState('subnicho');
  const [analyticsData, setAnalyticsData] = useState<AnalyticsAdvancedData | null>(null);
  const [channelsData, setChannelsData] = useState<SubnichoFromChannels[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedChannel, setSelectedChannel] = useState<{ channel: ChannelFromAPI; subnichoName: string } | null>(null);
  const [channelDetails, setChannelDetails] = useState<ChannelData | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const API_BASE = 'https://youtube-dashboard-backend-production.up.railway.app';

  useEffect(() => {
    if (open) {
      fetchData();
    }
  }, [open, period, subnicho, lingua]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ period });
      if (subnicho) params.append('subnicho', subnicho);
      if (lingua && lingua !== 'all') params.append('lingua', lingua);

      // Fetch both analytics-advanced and channels data
      const [analyticsRes, channelsRes] = await Promise.all([
        fetch(`${API_BASE}/api/monetization/analytics-advanced?${params}`),
        fetch(`${API_BASE}/api/monetization/channels?${params}&type_filter=real_estimate`),
      ]);

      const analyticsResult = await analyticsRes.json();
      const channelsResult = await channelsRes.json();

      setAnalyticsData(analyticsResult);
      setChannelsData(channelsResult.subnichos || []);
    } catch (error) {
      console.error('Erro ao buscar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchChannelDetails = async (channelId: string) => {
    setLoadingDetails(true);
    try {
      const params = new URLSearchParams({
        period,
        channel_id: channelId,
      });

      const response = await fetch(`${API_BASE}/api/monetization/analytics-advanced?${params}`);
      const result = await response.json();
      
      // API returns data at root level with channel info separate
      // Map to ChannelData interface
      const channelData: ChannelData = {
        id: result.channel?.id || channelId,
        channel_id: result.channel?.id || channelId,
        name: result.channel?.name || '',
        channel_name: result.channel?.name || '',
        subnicho: result.channel?.subnicho || '',
        lingua: result.channel?.lingua,
        performance_score: result.channel?.performance_score,
        traffic_sources: result.traffic_sources || [],
        search_terms: result.top_search_terms || result.search_terms || [],
        devices: result.devices || [],
        demographics: result.demographics || [],
        suggested_videos: result.suggested_videos || [],
      };
      
      setChannelDetails(channelData);
    } catch (error) {
      console.error('Erro ao buscar detalhes do canal:', error);
      setChannelDetails(null);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleSelectChannel = (channel: ChannelFromAPI, subnichoName: string) => {
    setSelectedChannel({ channel, subnichoName });
    fetchChannelDetails(channel.channel_id);
  };

  const handleBack = () => {
    setSelectedChannel(null);
    setChannelDetails(null);
  };

  // Sort subnichos for display
  const sortedAnalyticsSubnichos = analyticsData?.subnichos ? sortSubnichos(analyticsData.subnichos) : [];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-500" />
            📊 Analytics Avançado - Canais Monetizados
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="subnicho">Por Subnicho</TabsTrigger>
            <TabsTrigger value="canais">Canais Individuais</TabsTrigger>
          </TabsList>

          {/* Tab 1: Por Subnicho */}
          <TabsContent value="subnicho" className="space-y-3 mt-4">
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
              </div>
            ) : sortedAnalyticsSubnichos.length > 0 ? (
              sortedAnalyticsSubnichos.map((sub, idx) => (
                <SubnichoCard key={sub.subnicho} data={sub} animationDelay={idx * 100} />
              ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Nenhum dado disponível para o período selecionado</p>
              </div>
            )}
          </TabsContent>

          {/* Tab 2: Canais Individuais */}
          <TabsContent value="canais" className="space-y-4 mt-4">
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
              </div>
            ) : selectedChannel ? (
              <ChannelDetailsView
                channel={selectedChannel.channel}
                subnichoName={selectedChannel.subnichoName}
                channelDetails={channelDetails}
                loading={loadingDetails}
                onBack={handleBack}
              />
            ) : channelsData.length > 0 ? (
              <ChannelsList subnichos={channelsData} onSelectChannel={handleSelectChannel} />
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Nenhum canal disponível para o período selecionado</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

// Button Component to trigger the modal
export const AdvancedAnalyticsButton: React.FC<{
  period: string;
  subnicho?: string | null;
  lingua?: string | null;
}> = ({ period, subnicho, lingua }) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="text-2xl hover:scale-110 transition-transform cursor-pointer"
        title="Analytics Avançado"
      >
        📊
      </button>
      <AdvancedAnalyticsModal
        open={open}
        onClose={() => setOpen(false)}
        period={period}
        subnicho={subnicho}
        lingua={lingua}
      />
    </>
  );
};
