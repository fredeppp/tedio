import discord

NOME = "enviar_mensagem"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Envia uma mensagem para um canal de texto específico.",
        "parameters": {
            "type": "object",
            "properties": {
                "canal": {"type": "string", "description": "Nome do canal ou menção (#canal)."},
                "mensagem": {"type": "string", "description": "Conteúdo da mensagem."},
            },
            "required": ["mensagem"],
        },
    },
}


async def executar(ctx, args) -> str:
    if not ctx.guild:
        return "Erro: indisponível em DMs."
    alvo, msg_txt = args.get("canal"), args.get("mensagem", "")
    if not alvo:
        return "Erro: especifique o 'canal'."
    if not msg_txt:
        return "Erro: falta o texto da 'mensagem'."
    canal = ctx.find_channel(alvo)
    if not canal:
        return f"Erro: não encontrei o canal #{alvo}."
    try:
        await canal.send(msg_txt)
        return f"Mensagem enviada em #{canal.name}."
    except discord.Forbidden:
        return f"Erro: sem permissão para enviar em #{canal.name}."
