NOME = "salvar_memoria"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Registra um fato marcante sobre o usuário na memória permanente.",
        "parameters": {
            "type": "object",
            "properties": {
                "texto": {"type": "string", "description": "Informação ou fato a salvar."},
                "usuario_nome": {"type": "string", "description": "Nome do usuário."},
            },
            "required": ["texto"],
        },
    },
}


async def executar(ctx, args) -> str:
    texto = args.get("texto", "")
    alvo = args.get("usuario_nome") or ctx.nome_usuario
    return await ctx.memory_manager.adicionar_memoria(ctx.guild, alvo, texto)
