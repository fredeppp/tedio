import discord

NOME = "mudar_status"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Modifica o status de presença e texto do bot.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["online", "idle", "dnd", "invisible"]},
                "atividade": {"type": "string", "description": "Texto do status personalizado"},
            },
            "required": ["status", "atividade"],
        },
    },
}

_STATUS_MAP = {
    "online": discord.Status.online,
    "idle": discord.Status.idle,
    "dnd": discord.Status.dnd,
    "invisible": discord.Status.invisible,
}


async def executar(ctx, args) -> str:
    st = str(args.get("status", "online")).lower()
    atividade = args.get("atividade", "...")
    await ctx.bot.change_presence(
        status=_STATUS_MAP.get(st, discord.Status.online),
        activity=discord.CustomActivity(name=atividade),
    )
    return f"Status alterado para '{st}' com atividade '{atividade}'."
