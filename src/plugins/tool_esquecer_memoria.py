NOME = "esquecer_memoria"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Remove uma informação da memória permanente.",
        "parameters": {
            "type": "object",
            "properties": {
                "busca": {
                    "type": "string",
                    "description": "Informação que deve ser esquecida."
                }
            },
            "required": ["busca"],
        },
    },
}


async def executar(ctx, args):
    busca = args.get("busca") or args.get("texto")

    if not busca:
        return "Nenhuma memória informada."

    sucesso = ctx.memory_manager.remover_memoria(
        ctx.nome_usuario,
        busca
    )

    if sucesso:
        return f"Memória esquecida: {busca}"

    return "Não encontrei essa memória."