NOME = "buscar_usuario"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Busca um membro pelo nome ou apelido.",
        "parameters": {
            "type": "object",
            "properties": {"termo": {"type": "string", "description": "Nome/apelido do usuário"}},
            "required": ["termo"],
        },
    },
}


async def executar(ctx, args) -> str:
    if not ctx.guild:
        return "Erro: indisponível em DMs."
    termo = str(args.get("termo", "")).lower()
    res = [f"{m.display_name} (@{m.name})" for m in ctx.guild.members if termo in m.display_name.lower()]
    return "\n".join(res) or f"Nenhum membro encontrado contendo '{termo}'."
