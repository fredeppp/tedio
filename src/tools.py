import traceback

import discord

from .logger import LogManager
from .plugins import PLUGINS, SCHEMAS
from .plugins.base import ToolContext


class ToolManager:
    """
    Ponte entre o agente e as tools.

    O ToolManager NÃO sabe mais o que cada tool faz — isso agora é
    responsabilidade de cada plugin em src/plugins/tool_*.py. Para criar uma
    tool nova, basta adicionar um arquivo lá; este arquivo não precisa ser
    tocado. Veja src/plugins/__init__.py para o contrato que um plugin
    precisa seguir.
    """

    SCHEMAS = SCHEMAS

    def __init__(self, bot_client, memory_manager):
        self.bot = bot_client
        self.memory_manager = memory_manager

    async def executar_tool_segura(self, guild, nome_funcao: str, args: dict, nome_usuario: str) -> str:
        LogManager.log(f"Executando tool: {nome_funcao} | Args: {args}", "TOOLS")

        plugin = PLUGINS.get(nome_funcao)
        if not plugin:
            return f"[ERRO]: Ferramenta '{nome_funcao}' não reconhecida."

        ctx = ToolContext(
            bot=self.bot,
            memory_manager=self.memory_manager,
            guild=guild,
            nome_usuario=nome_usuario,
        )

        try:
            return await plugin.executar(ctx, args)
        except discord.NotFound:
            return f"[ERRO RECURSO]: item de '{nome_funcao}' não localizado."
        except discord.Forbidden:
            return f"[ERRO PERMISSÃO]: negada para '{nome_funcao}'."
        except Exception as e:
            LogManager.log(f"Exceção em {nome_funcao}: {traceback.format_exc()}", "ERROR")
            return f"[ERRO INESPERADO EM {nome_funcao}]: {e}"
