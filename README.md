# Tédio Bot

## Estrutura
```
tedio-bot/
├── launcher.py          # baixa os módulos do GitHub e roda o bot
├── requirements.txt
└── src/
    ├── config.py         # variáveis de ambiente e constantes
    ├── logger.py         # logs em memória + contagem de tokens
    ├── ui.py              # botões de aprovação de ferramentas
    ├── memory.py         # memória vetorial (ChromaDB) espelhada no canal
    ├── tools.py           # schemas + execução segura das ferramentas
    ├── agent.py           # roteamento de modelo, loop de tools, resumo
    ├── bot.py             # eventos do Discord + comandos !tedio
    ├── web.py             # Flask keep-alive
    └── main.py            # ponto de entrada
```

## Rodar direto (sem launcher)
```bash
pip install -r requirements.txt
python -m src.main
```
Variáveis de ambiente necessárias: `DISCORD_TOKEN`, `GROQ_API_KEY`, `OWNER_ID` (opcional).

## Rodar via launcher (baixa do GitHub)
```bash
export GITHUB_REPO="seu-usuario/tedio-bot"   # repo com esta mesma estrutura em subpastas por tag/branch
python launcher.py v2.0.0                     # ou: TEDIO_VERSION=main python launcher.py
```
O launcher baixa cada arquivo do `MANIFEST` via `raw.githubusercontent.com/{repo}/{versao}/{arquivo}`,
instala `requirements.txt` e executa `python -m src.main`. Sem dependências externas — usa apenas `urllib`.

## Memória vetorial (ChromaDB)
- `memory.py` guarda cada fato como embedding em uma coleção persistente (`chroma_data/`).
- `obter_memorias_relevantes` faz busca semântica (`collection.query`) filtrada por usuário — não é mais
  apenas overlap de palavras-chave.
- Cada atualização também sincroniza um painel legível no canal `memoria-tedio` (edita a mesma mensagem
  por usuário, id guardado em `canal_state.json`) para auditoria manual.
- Usa `DefaultEmbeddingFunction` do ChromaDB (modelo local via onnxruntime) — não precisa de chave de API extra.
