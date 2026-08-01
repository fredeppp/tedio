NOME = "usuario"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Obtém detalhes do perfil e cargos de um membro.",
        "parameters": {
            "type": "object",
            "properties": {"membro": {"type": "string", "description": "Nome ou menção do membro (@usuario)."}},
            "required": [],
        },
    },
}


async def executar(ctx, args) -> str:
    if not ctx.guild:
        return "Erro: indisponível em DMs."
    alvo = args.get("membro")
    if not alvo:
        return "Erro: especifique o nome ou menção do membro."
    membro = ctx.find_member(alvo)
    if not membro:
        return f"Erro: não encontrei o usuário '{alvo}'."
    cargos = ", ".join(c.name for c in membro.roles if c.name != "@everyone")
    return f"Membro: {membro.display_name} (@{membro.name}) | Entrou: {membro.joined_at:%Y-%m-%d} | Cargos: {cargos}"
