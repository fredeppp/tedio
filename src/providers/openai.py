from .base import OpenAICompatibleProvider


class OpenAIProvider(OpenAICompatibleProvider):
    base_url = "https://api.openai.com/v1"
