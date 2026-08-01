NOME = "ver_membros"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Lista os membros e cargos do servidor.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}


async def executar(ctx, args) -> str:
    if not ctx.guild:
        return "Erro: indisponível em DMs."
    membros = [f"{m.display_name} (@{m.name})" for m in ctx.guild.members if not m.bot]
    return "\n".join(membros[:40]) or "Nenhum membro encontrado."
