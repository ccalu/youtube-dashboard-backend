import { useState } from 'react';
import { ExternalLink, Newspaper, Shield, AlertTriangle, CreditCard } from 'lucide-react';
import PubTab from './PubTab';
import { ProxysTab } from './ProxysTab';
import { DesmonetizadosTab } from './DesmonetizadosTab';
import { AdsenseTab } from './AdsenseTab';

const SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1XL6VhOTVVMmfGNqPyJra2T8KjfFbtJ1o16OZkytvCPc/edit?gid=1449741920#gid=1449741920';

type SubTab = 'pub' | 'proxys' | 'desmonetizados' | 'adsense';

const SUB_TABS: { id: SubTab; label: string; icon: React.ElementType; color: string }[] = [
  { id: 'pub', label: 'PUB', icon: Newspaper, color: 'teal' },
  { id: 'proxys', label: 'Proxys', icon: Shield, color: 'blue' },
  { id: 'desmonetizados', label: 'Desmonetizados', icon: AlertTriangle, color: 'red' },
  { id: 'adsense', label: 'Adsense', icon: CreditCard, color: 'amber' },
];

const TAB_COLORS: Record<string, { active: string; hover: string; border: string }> = {
  teal: { active: 'bg-teal-500/20 text-teal-400 border-teal-500', hover: 'hover:bg-teal-500/10 hover:text-teal-400', border: 'border-teal-500/30' },
  blue: { active: 'bg-blue-500/20 text-blue-400 border-blue-500', hover: 'hover:bg-blue-500/10 hover:text-blue-400', border: 'border-blue-500/30' },
  red: { active: 'bg-red-500/20 text-red-400 border-red-500', hover: 'hover:bg-red-500/10 hover:text-red-400', border: 'border-red-500/30' },
  amber: { active: 'bg-amber-500/20 text-amber-400 border-amber-500', hover: 'hover:bg-amber-500/10 hover:text-amber-400', border: 'border-amber-500/30' },
};

export function PerfisTab() {
  const [activeSubTab, setActiveSubTab] = useState<SubTab>('pub');

  return (
    <div className="space-y-4">
      {/* Header with sub-tabs + spreadsheet link */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        {/* Sub-tabs */}
        <div className="flex gap-1.5 p-1 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          {SUB_TABS.map((tab) => {
            const isActive = activeSubTab === tab.id;
            const colors = TAB_COLORS[tab.color];
            return (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 border ${
                  isActive
                    ? `${colors.active}`
                    : `text-white/50 border-transparent ${colors.hover}`
                }`}
              >
                <tab.icon className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Spreadsheet link */}
        <a
          href={SPREADSHEET_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white/50 hover:text-white/80 bg-white/[0.03] border border-white/[0.06] hover:border-white/[0.12] transition-all"
        >
          <ExternalLink className="h-3 w-3" />
          Abrir Planilha
        </a>
      </div>

      {/* Sub-tab content */}
      {activeSubTab === 'pub' && <PubTab />}
      {activeSubTab === 'proxys' && <ProxysTab />}
      {activeSubTab === 'desmonetizados' && <DesmonetizadosTab />}
      {activeSubTab === 'adsense' && <AdsenseTab />}
    </div>
  );
}
