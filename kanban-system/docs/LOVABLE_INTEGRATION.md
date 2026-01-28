# Guia de Integração - Lovable

## 📍 IMPORTANTE: Layout e Posicionamento

### Localização da Nova Aba
A aba **"Kanban"** deve ser adicionada na seção **Ferramentas**, ABAIXO de "Histórico de Coletas":

```
Ferramentas
  ├── Histórico de Coletas
  ├── Kanban (NOVA ABA AQUI) ←
  └── Outras ferramentas...
```

### Layout Visual
Este sistema segue EXATAMENTE o mesmo padrão visual da aba **"Tabela"**:
- Mesmos cards expansíveis
- Mesmas cores de subnichos
- Mesmos emojis e bandeiras
- Mesmo estilo de expansão/colapso

## 🎨 Estrutura de Navegação

```
1º Nível: Dois Cards Principais
┌─────────────────┐  ┌─────────────────┐
│ 💰 MONETIZADOS  │  │ 📍 NÃO MONET.   │
│    (9 canais)   │  │   (54 canais)   │
└─────────────────┘  └─────────────────┘
         ↓                    ↓
      [clique]             [clique]
         ↓                    ↓

2º Nível: Subnichos Expansíveis
├── 📁 Terror (3 canais)
├── 📁 Guerras (2 canais)
└── 📁 Mistérios (4 canais)
         ↓
      [clique]
         ↓

3º Nível: Lista de Canais com Status
├── 🇧🇷 Dark Terror BR    [🟡 Em Teste há 49d]
├── 🇺🇸 Scary Stories US  [🟢 Com Tração há 13d]
└── 🇪🇸 Terror España     [🟠 Em Andamento há 8d]
         ↓
      [clique]
         ↓

4º Nível: Modal do Kanban Individual
[Abre modal com quadro Kanban do canal]
```

## 📦 Passo a Passo de Implementação

### Passo 1: Adicionar Rota no Menu

No arquivo de rotas/navegação principal:

```jsx
// Adicionar na seção Ferramentas, após Histórico de Coletas
{
  label: 'Kanban',
  icon: '🎯', // ou use um ícone do Lucide
  path: '/ferramentas/kanban',
  component: KanbanView
}
```

### Passo 2: Criar a Página

Crie o arquivo `pages/Ferramentas/Kanban.jsx`:

```jsx
import React from 'react';
import KanbanView from '../../components/Kanban/KanbanView';

const KanbanPage = () => {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Sistema Kanban
        </h1>
        <p className="text-gray-500 mt-1">
          Gerencie o status e estratégias dos canais
        </p>
      </div>

      <KanbanView />
    </div>
  );
};

export default KanbanPage;
```

### Passo 3: Adicionar Componentes

Copie os seguintes arquivos para `components/Kanban/`:

1. **KanbanView.tsx** - Componente principal com cards e navegação
2. **KanbanBoard.tsx** - Modal do Kanban individual

### Passo 4: Ajustar URLs da API

No arquivo `KanbanView.tsx`, ajuste a URL base da API:

```jsx
// Desenvolvimento
const API_URL = 'http://localhost:8000';

// Produção (Railway)
const API_URL = 'https://youtube-dashboard-backend-production.up.railway.app';
```

### Passo 5: Estilos e Cores

Use as mesmas classes do Tailwind CSS da aba Tabela:

```jsx
// Cards principais
className="bg-white rounded-lg shadow-sm border border-gray-200"

// Subnichos
className="px-6 py-4 hover:bg-gray-50 cursor-pointer"

// Tags de status
className="px-3 py-1 rounded-full text-xs font-medium"

// Cores dos status (EXATAMENTE como definido)
const STATUS_COLORS = {
  'em_teste_inicial': { bg: 'bg-yellow-100', text: 'text-yellow-800' },
  'demonstrando_tracao': { bg: 'bg-green-100', text: 'text-green-800' },
  'em_andamento': { bg: 'bg-orange-100', text: 'text-orange-800' },
  // etc...
};
```

## 🔧 Configurações Necessárias

### Variáveis de Ambiente

Adicione ao `.env` do Lovable:

```env
VITE_API_URL=https://youtube-dashboard-backend-production.up.railway.app
```

### Permissões CORS

O backend já está configurado para aceitar requisições do Lovable.

## 🎯 Features Implementadas

### 1. Navegação Hierárquica
- ✅ Cards expansíveis (Monetizados/Não Monetizados)
- ✅ Subnichos colapsáveis
- ✅ Lista de canais com bandeiras e status

### 2. Kanban Individual
- ✅ Drag & drop para mudar status
- ✅ CRUD completo de notas
- ✅ 6 cores de notas disponíveis
- ✅ Reordenação de notas (drag & drop)
- ✅ Histórico com soft delete

### 3. Visual e UX
- ✅ Mesmo layout da aba Tabela
- ✅ Emojis e bandeiras de idioma
- ✅ Tags coloridas de status
- ✅ Contador de dias no status

## 🚨 Pontos de Atenção

1. **Filtro tipo="nosso"**: O sistema mostra APENAS os 63 canais próprios, não os minerados

2. **Status por Monetização**:
   - Não monetizados: 4 status possíveis
   - Monetizados: 3 status possíveis

3. **Bandeiras de Idioma**: Mapeamento já incluído no componente:
```jsx
'portuguese' → '🇧🇷'
'english' → '🇺🇸'
'spanish' → '🇪🇸'
// etc...
```

4. **Responsividade**: Componentes já preparados para mobile

## 📊 Dados de Teste

Para testar antes do backend estar pronto:

```jsx
// Mock de estrutura
const mockStructure = {
  monetizados: {
    total: 9,
    subnichos: {
      'Terror': {
        nome: 'Terror',
        total: 3,
        canais: [
          {
            id: 1,
            nome: 'Dark Terror BR',
            lingua: 'portuguese',
            kanban_status: 'em_crescimento',
            status_label: 'Em Crescimento',
            status_color: 'green',
            dias_no_status: 15,
            total_notas: 2
          }
        ]
      }
    }
  },
  nao_monetizados: {
    total: 54,
    subnichos: {
      // similar structure
    }
  }
};
```

## ✅ Checklist de Implementação

- [ ] Adicionar rota no menu Ferramentas
- [ ] Criar página Kanban
- [ ] Copiar componentes KanbanView e KanbanBoard
- [ ] Ajustar URLs da API
- [ ] Testar navegação hierárquica
- [ ] Testar modal do Kanban individual
- [ ] Testar drag & drop de status
- [ ] Testar CRUD de notas
- [ ] Testar histórico
- [ ] Deploy e teste em produção

## 🆘 Troubleshooting

### Erro: "Canal não encontrado"
- Verificar se o canal é tipo="nosso"
- Verificar se as tabelas foram criadas no Supabase

### Drag & drop não funciona
- Verificar se o evento está sendo capturado corretamente
- Testar em diferentes navegadores

### Cores não aparecem
- Verificar se Tailwind está configurado
- Verificar se as classes estão no safelist

## 📝 Notas Finais

Este sistema foi desenvolvido especificamente para o **Micha** gerenciar os canais. Não há campos de autor pois é uma ferramenta dedicada.

O layout segue EXATAMENTE o padrão da aba Tabela para manter consistência visual.

Qualquer dúvida, consulte o código de referência em `kanban-system/frontend/`.