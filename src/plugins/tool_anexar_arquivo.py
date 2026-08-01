import io

import discord

NOME = "anexar_arquivo"

SCHEMA = {
    "type": "function",
    "function": {
        "name": NOME,
        "description": "Anexa um arquivo no Discord.",
        "parameters": {
            "type": "object",
            "properties": {
                "canal": {"type": "string", "description": "Nome do canal ou menção (#canal)."},
                "texto": {"type": "string", "description": "Conteúdo do arquivo."},
                "nome": {"type": "string", "description": "Nome do arquivo."},
            },
            "required": ["canal", "texto"],
        },
    },
}


async def executar(ctx, args) -> str:
    if not ctx.guild:
        return "Erro: indisponível em DMs."

    alvo = args.get("canal")
    texto = args.get("texto", "")
    nome = args.get("nome", "arquivo.txt")

    if not alvo:
        return "Erro: especifique o canal."

    canal = ctx.find_channel(alvo)
    if not canal:
        return f"Erro: não encontrei o canal #{alvo}."
    if len(texto) > 8000000:
        return "Erro: arquivo muito grande."

    arquivo = discord.File(io.BytesIO(texto.encode("utf-8")), filename=nome)
    await canal.send("Aqui está o arquivo:", file=arquivo)

    return f"Arquivo {nome} enviado em #{canal.name}."
