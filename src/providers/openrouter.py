from .base import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    """
    Hub com um monte de modelos atrás da MESMA API. O "modelo" é sempre no
    formato "namespace/nome", ex:

        moonshotai/kimi-vl-a3b-thinking:free
        deepseek/deepseek-r1
        qwen/qwen3-235b-a22b
        google/gemini-2.5-pro

    Em src/llm.py, qualquer MODEL cujo prefixo não bata com um provedor
    nativo (groq/openrouter/moonshot/openai/anthropic/google) cai aqui
    automaticamente, então dá pra colar qualquer ID copiado do site do
    OpenRouter direto no config.py sem precisar prefixar nada.
    """

    base_url = "https://openrouter.ai/api/v1"
