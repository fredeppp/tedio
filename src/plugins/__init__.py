"""
Autoload de plugins de tool.

Toda tool do Tédio é um arquivo `tool_*.py` dentro desta pasta, com o
seguinte contrato:

    NOME = "nome_da_tool"          # precisa bater com o nome usado no SCHEMA
    SCHEMA = {...}                 # schema no formato OpenAI function-calling
    async def executar(ctx, args) -> str: ...

Esse módulo escaneia a pasta, importa todo arquivo que começa com "tool_"
e registra a tool automaticamente. Para adicionar uma tool nova:

    1. Crie src/plugins/tool_algumacoisa.py seguindo o contrato acima.
    2. Pronto. Não precisa editar este arquivo nem o ToolManager.

Um plugin mal formado (sem NOME/SCHEMA/executar, ou com erro de import) é
ignorado com um log de erro, em vez de derrubar o bot inteiro.
"""

import importlib
import pkgutil

from ..logger import LogManager

PLUGINS: dict[str, object] = {}
SCHEMAS: list[dict] = []


def _carregar_plugins() -> None:
    PLUGINS.clear()
    SCHEMAS.clear()

    for _, nome_modulo, _ in pkgutil.iter_modules(__path__):
        if not nome_modulo.startswith("tool_"):
            continue

        try:
            modulo = importlib.import_module(f".{nome_modulo}", package=__name__)
        except Exception as e:
            LogManager.log(f"Falha ao importar plugin '{nome_modulo}': {e}", "ERROR")
            continue

        nome = getattr(modulo, "NOME", None)
        schema = getattr(modulo, "SCHEMA", None)
        executar = getattr(modulo, "executar", None)

        if not nome or not schema or not callable(executar):
            LogManager.log(
                f"Plugin '{nome_modulo}' ignorado: falta NOME, SCHEMA ou executar().",
                "WARNING",
            )
            continue

        if nome in PLUGINS:
            LogManager.log(
                f"Plugin '{nome_modulo}' ignorado: já existe uma tool chamada '{nome}'.",
                "WARNING",
            )
            continue

        PLUGINS[nome] = modulo
        SCHEMAS.append(schema)


_carregar_plugins()
print("TOOLS CARREGADAS:", list(PLUGINS.keys()))