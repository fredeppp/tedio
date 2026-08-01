from .base import BaseProvider


class GroqProvider(BaseProvider):
    """
    A Groq usa um SDK próprio, mas o formato de resposta já é idêntico ao
    da OpenAI — por isso não herda de OpenAICompatibleProvider (client
    diferente), mas também não precisa normalizar nada.
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)
        from groq import Groq
        self.client = Groq(api_key=api_key)

    def chat(self, *, model: str, messages: list, tools: list = None, tool_choice=None, **kwargs):
        payload = {"model": model, "messages": messages, **kwargs}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice or "auto"
        return self.client.chat.completions.create(**payload)
