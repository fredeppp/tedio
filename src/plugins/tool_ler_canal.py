NOME = "ler_canal"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Lê as últimas mensagens de um canal específico.",
        "parameters": {
            "type": "object",
            "properties": {"canal": {"type": "string", "description": "Nome do canal ou menção (#canal)."}},
            "required": [],
        },
    },
}


async def executar(ctx, args) -> str:
    if not ctx.guild:
        return "Erro: indisponível em DMs."
    alvo = args.get("canal")
    if not alvo:
        return "Erro: especifique o nome do canal (ex: #geral)."
    canal = ctx.find_channel(alvo)
    if not canal:
        return f"Erro: não encontrei o canal #{alvo}."
    if not canal.permissions_for(ctx.guild.me).view_channel:
        return f"Erro: sem permissão para ler #{canal.name}."
    msgs = [f"{m.author.display_name}: {m.content}" async for m in canal.history(limit=5) if not m.author.bot]
    msgs.reverse()
    return "\n".join(msgs) or f"Nenhuma mensagem recente em #{canal.name}."
