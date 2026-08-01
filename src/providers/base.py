"""
Contrato comum a todo provedor de LLM.

O resto do TEDIO (agent.py) só entende um formato de resposta: o mesmo que
a Groq/OpenAI retornam:

    resposta.choices[0].message.content
    resposta.choices[0].message.tool_calls[i].id
    resposta.choices[0].message.tool_calls[i].function.name
    resposta.choices[0].message.tool_calls[i].function.arguments   (string JSON)
    resposta.usage.total_tokens

Provedores que já são "OpenAI-compatible" (Groq, OpenRouter, Moonshot,
OpenAI) devolvem o objeto cru do próprio SDK, que já vem nesse formato —
nenhuma tradução necessária.

Provedores com formato de resposta próprio (Anthropic, Google) usam as
classes Normalized* abaixo para se fazerem passar pelo mesmo formato. Assim
o agent.py nunca precisa saber com qual API está falando.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class NormalizedFunction:
    name: str
    arguments: str  # sempre uma string JSON, igual ao formato OpenAI


@dataclass
class NormalizedToolCall:
    id: str
    function: NormalizedFunction
    type: str = "function"


@dataclass
class NormalizedMessage:
    content: Optional[str]
    tool_calls: Optional[list] = None


@dataclass
class NormalizedChoice:
    message: NormalizedMessage


@dataclass
class NormalizedUsage:
    total_tokens: int = 0


@dataclass
class NormalizedCompletion:
    choices: list
    usage: Optional[NormalizedUsage] = None


class BaseProvider:
    """
    Toda API nova implementa isso. Só precisa de um método: chat().

    kwargs aceita qualquer parâmetro extra que o provedor específico
    suporte (temperature, max_tokens, etc) — o que não for reconhecido,
    cada provedor decide se ignora ou repassa pro SDK dele.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    def chat(self, *, model: str, messages: list, tools: Optional[list] = None,
              tool_choice=None, **kwargs):
        raise NotImplementedError


class OpenAICompatibleProvider(BaseProvider):
    """
    Base pra qualquer API que fala o "dialeto" da OpenAI (Groq, OpenRouter,
    Moonshot, a própria OpenAI, e no fundo boa parte do mercado). A única
    coisa que muda de um provedor pro outro é o base_url — a requisição e a
    resposta têm sempre o mesmo formato, então um único client cobre todos.

    Uma tool nova nesse molde é só:

        class NovoProvider(OpenAICompatibleProvider):
            base_url = "https://api.novoprovedor.com/v1"
    """

    base_url: Optional[str] = None

    def __init__(self, api_key: str):
        super().__init__(api_key)
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=self.base_url)

    def chat(self, *, model: str, messages: list, tools: Optional[list] = None,
              tool_choice=None, **kwargs):
        payload = {"model": model, "messages": messages, **kwargs}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice or "auto"
        return self.client.chat.completions.create(**payload)
