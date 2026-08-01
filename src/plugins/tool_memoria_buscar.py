NOME = "memoria"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Busca informações salvas na memória vetorial do usuário.",
        "parameters": {
            "type": "object",
            "properties": {
                "busca": {
                    "type": "string",
                    "description": "O que procurar na memória."
                }
            },
            "required": ["busca"],
        },
    },
}


async def executar(ctx, args):
    memoria = ctx.memory_manager

    busca = args.get("busca")

    if not busca:
        return "Erro: informe o que deve ser procurado."

    usuario = str(ctx.user.id)

    resultados = memoria.obter_memorias_relevantes(
        usuario,
        busca,
        k=5
    )

    if not resultados:
        return f"Nenhuma memória encontrada sobre '{busca}'."

    return "Memórias encontradas:\n" + "\n".join(
        f"- {r}" for r in resultados
    )