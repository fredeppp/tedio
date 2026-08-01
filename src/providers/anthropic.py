"""
Provedor Anthropic (Claude).

A Messages API da Anthropic não fala o mesmo "dialeto" que o resto do
TEDIO usa internamente (o formato OpenAI). Diferenças principais:

  - o system prompt é um parâmetro separado ("system"), não uma mensagem
    com role="system" dentro da lista;
  - só existem os roles "user" e "assistant" (não existe role "tool");
  - uma tool call do assistant vira um bloco {"type": "tool_use", ...}
    dentro do content da mensagem, e o resultado da tool volta como um
    bloco {"type": "tool_result", ...} dentro de uma mensagem "user".

Esse provedor traduz o histórico (que chega no formato OpenAI, igual pro
resto do bot) pro formato da Anthropic, e traduz a resposta de volta pro
formato normalizado — assim o agent.py não precisa saber que está falando
com a Anthropic.
"""

import json

from .base import (
    BaseProvider,
    NormalizedChoice,
    NormalizedCompletion,
    NormalizedFunction,
    NormalizedMessage,
    NormalizedToolCall,
    NormalizedUsage,
)


class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)

    @staticmethod
    def _converter_tools(tools):
        if not tools:
            return None
        convertidas = []
        for t in tools:
            fn = t["function"]
            convertidas.append({
                "name": fn["name"],
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters") or {"type": "object", "properties": {}},
            })
        return convertidas

    @staticmethod
    def _converter_mensagens(messages):
        system_partes = []
        convertidas = []

        for m in messages:
            role = m.get("role")

            if role == "system":
                if m.get("content"):
                    system_partes.append(m["content"])

            elif role == "user":
                convertidas.append({"role": "user", "content": m.get("content") or ""})

            elif role == "assistant":
                blocos = []
                if m.get("content"):
                    blocos.append({"type": "text", "text": m["content"]})
                for tc in m.get("tool_calls") or []:
                    try:
                        args = json.loads(tc["function"]["arguments"])
                    except Exception:
                        args = {}
                    blocos.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": args,
                    })
                convertidas.append({"role": "assistant", "content": blocos or ""})

            elif role == "tool":
                bloco = {
                    "type": "tool_result",
                    "tool_use_id": m.get("tool_call_id"),
                    "content": m.get("content") or "",
                }
                # A Anthropic espera tool_results agrupados numa única
                # mensagem "user"; se o turno anterior já é isso, entra nele
                # em vez de abrir um novo (senão a API rejeita a conversa).
                anterior = convertidas[-1] if convertidas else None
                if anterior and anterior["role"] == "user" and isinstance(anterior["content"], list):
                    anterior["content"].append(bloco)
                else:
                    convertidas.append({"role": "user", "content": [bloco]})

        return "\n".join(system_partes), convertidas

    def chat(self, *, model: str, messages: list, tools: list = None, tool_choice=None, **kwargs):
        system_text, msgs = self._converter_mensagens(messages)

        payload = {
            "model": model,
            "max_tokens": kwargs.pop("max_tokens", 4096),
            "messages": msgs,
        }
        if system_text:
            payload["system"] = system_text

        tools_conv = self._converter_tools(tools)
        if tools_conv:
            payload["tools"] = tools_conv

        payload.update(kwargs)

        resp = self.client.messages.create(**payload)

        texto, tool_calls = None, []
        for bloco in resp.content:
            if bloco.type == "text":
                texto = (texto or "") + bloco.text
            elif bloco.type == "tool_use":
                tool_calls.append(NormalizedToolCall(
                    id=bloco.id,
                    function=NormalizedFunction(name=bloco.name, arguments=json.dumps(bloco.input)),
                ))

        msg = NormalizedMessage(content=texto, tool_calls=tool_calls or None)
        total = (resp.usage.input_tokens + resp.usage.output_tokens) if resp.usage else 0
        return NormalizedCompletion(choices=[NormalizedChoice(message=msg)], usage=NormalizedUsage(total_tokens=total))
