"""
Fábrica de provedores de LLM.

Formato esperado pra ConfigManager.MODELO_PRINCIPAL / MODELO_PEQUENO:

    "<provedor>/<modelo>"

Exemplos:
    "groq/openai/gpt-oss-120b"          -> provedor nativo Groq
    "openai/gpt-5"                      -> provedor nativo OpenAI
    "anthropic/claude-opus-4"           -> provedor nativo Anthropic
    "google/gemini-2.5-pro"             -> provedor nativo Google
    "moonshot/kimi-v1-a3b-thinking"     -> provedor nativo Moonshot

Se o primeiro pedaço não bater com nenhum provedor conhecido, o TEDIO
assume que é um ID de modelo do OpenRouter (que já usa esse mesmo formato
"namespace/modelo" pros IDs dele) e manda pra lá com a string inteira.
Então isso também funciona sem precisar prefixar nada:

    "moonshotai/kimi-vl-a3b-thinking:free"  -> cai no OpenRouter
    "deepseek/deepseek-r1"                  -> cai no OpenRouter
    "qwen/qwen3-235b-a22b"                  -> cai no OpenRouter

Pra adicionar um provedor novo: crie src/providers/algumacoisa.py com uma
classe que implementa BaseProvider (veja providers/base.py) e registre ela
em PROVIDER_CLASSES abaixo, com a chave de API correspondente em
ConfigManager.API_KEYS.
"""

import asyncio

from .config import ConfigManager
from .providers.groq import GroqProvider
from .providers.openrouter import OpenRouterProvider
from .providers.moonshot import MoonshotProvider
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
from .providers.google import GoogleProvider

PROVIDER_CLASSES = {
    "groq": GroqProvider,
    "openrouter": OpenRouterProvider,
    "moonshot": MoonshotProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
}

_instancias = {}


def _obter_provider(nome: str):
    if nome not in _instancias:
        classe = PROVIDER_CLASSES.get(nome)
        if not classe:
            raise RuntimeError(f"Provedor de LLM desconhecido: '{nome}'.")
        api_key = ConfigManager.API_KEYS.get(nome)
        if not api_key:
            raise RuntimeError(
                f"Falta a API key do provedor '{nome}'. Defina em "
                f"ConfigManager.API_KEYS['{nome}'] (ou na env var correspondente)."
            )
        _instancias[nome] = classe(api_key=api_key)
    return _instancias[nome]


def resolver(model_string: str):
    """'groq/llama-3.3-70b-versatile' -> (instância do GroqProvider, 'llama-3.3-70b-versatile')."""
    if "/" not in model_string:
        raise RuntimeError(
            f"MODEL inválido: '{model_string}'. Use 'provedor/modelo' "
            "(ex: 'groq/llama-3.3-70b-versatile') ou um ID do OpenRouter "
            "(ex: 'moonshotai/kimi-vl-a3b-thinking:free')."
        )

    prefixo, resto = model_string.split("/", 1)
    if prefixo in PROVIDER_CLASSES:
        return _obter_provider(prefixo), resto

    # Prefixo desconhecido: trata a string inteira como um ID de modelo do
    # OpenRouter, que é quem cobre a esmagadora maioria dos modelos que não
    # têm provedor nativo aqui (deepseek, qwen, mistral, llama, etc).
    return _obter_provider("openrouter"), model_string


async def achat(model_string: str, **kwargs):
    """Versão assíncrona de provider.chat(), pronta pra usar no agent.py."""
    provider, model_id = resolver(model_string)
    return await asyncio.to_thread(provider.chat, model=model_id, **kwargs)
