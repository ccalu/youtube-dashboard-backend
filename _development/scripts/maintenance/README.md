# Scripts de Manutenção

Esta pasta contém scripts de manutenção e utilitários do sistema.

## Arquivos:
- **remove_banned_channels.py** - Remove canais banidos do banco de dados
- **sync.py** - Sincroniza código com GitHub e atualiza Railway

## Uso:
```bash
python scripts/maintenance/remove_banned_channels.py
python scripts/maintenance/sync.py
```

## Importante:
- Scripts aqui são para manutenção ativa do sistema
- Não colocar testes temporários aqui
- Scripts obsoletos devem ir para `/legacy/`