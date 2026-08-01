NOME = "ler_arquivo"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Lê o conteúdo de um arquivo enviado recentemente pelo usuário.",
        "parameters": {
            "type": "object",
            "properties": {
                "nome": {
                    "type": "string",
                    "description": "Nome do arquivo que deve ser lido."
                }
            },
            "required": ["nome"],
        },
    },
}


async def executar(ctx, args) -> str:
    nome = args.get("nome")

    if not nome:
        return "Erro: informe o nome do arquivo."

    if not ctx.guild:
        return "Erro: arquivos indisponíveis fora de servidor."

    # procura nos últimos canais/mensagens acessíveis
    for canal in ctx.guild.text_channels:

        try:
            async for msg in canal.history(limit=20):

                for anexo in msg.attachments:

                    if anexo.filename.lower() == nome.lower():

                        # limite anti-explosão de tokens
                        if anexo.size > 100_000:
                            return (
                                f"O arquivo '{nome}' é muito grande "
                                "para ser lido diretamente."
                            )

                        dados = await anexo.read()

                        texto = dados.decode(
                            "utf-8",
                            errors="ignore"
                        )

                        return (
                            f"Conteúdo do arquivo '{nome}':\n\n"
                            f"{texto[:5000]}"
                        )

        except Exception:
            continue

    return f"Não encontrei o arquivo '{nome}'."