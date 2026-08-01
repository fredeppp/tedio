NOME = "buscar_mensagem"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Busca mensagens no histórico dos canais contendo um termo.",
        "parameters": {
            "type": "object",
            "properties": {"termo": {"type": "string", "description": "Termo de busca"}},
            "required": ["termo"],
        },
    },
}


async def executar(ctx, args) -> str:
    if not ctx.guild:
        return "Erro: sem servidor."
    termo = str(args.get("termo", "")).lower()
    resultados = []
    for c in ctx.guild.text_channels:
        if len(resultados) >= 5:
            break
        perm = c.permissions_for(ctx.guild.me)
        if not (perm.view_channel and perm.read_message_history):
            continue
        try:
            async for m in c.history(limit=15):
                if not m.author.bot and termo in m.content.lower():
                    resultados.append(f"[#{c.name}] {m.author.display_name}: {m.content[:60]}")
                    if len(resultados) >= 5:
                        break
        except Exception:
            continue
    return "\n".join(resultados) or f"Nenhuma mensagem encontrada com '{termo}'."
