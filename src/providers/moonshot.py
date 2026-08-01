from .base import OpenAICompatibleProvider


class MoonshotProvider(OpenAICompatibleProvider):
    """
    API própria da Moonshot AI (modelos Kimi), formato OpenAI-compatible.

    Conta internacional -> api.moonshot.ai
    Conta .cn (China)    -> api.moonshot.cn

    Se você usa a conta .cn, troque o base_url abaixo (ou vire uma segunda
    classe MoonshotCNProvider registrada em src/llm.py com outra chave de
    provedor, ex: "moonshot_cn").
    """

    base_url = "https://api.moonshot.ai/v1"
