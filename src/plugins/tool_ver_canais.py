NOME = "ver_canais"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Lista os canais de texto acessíveis no servidor.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}


async def executar(ctx, args) -> str:
    if not ctx.guild:
        return "Erro: indisponível em DMs."
    canais = [f"#{c.name}" for c in ctx.guild.text_channels if c.permissions_for(ctx.guild.me).view_channel]
    return "\n".join(canais) or "Nenhum canal visível."
