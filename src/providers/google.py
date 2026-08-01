"""
Provedor Google (Gemini), via SDK google-genai.

Assim como a Anthropic, o Gemini fala um formato próprio, diferente do
formato OpenAI que o resto do TEDIO usa internamente:

  - roles são "user" e "model" (não "assistant");
  - uma tool call vira uma Part com function_call, e o resultado volta como
    uma Part com function_response — casada pelo NOME da tool (o Gemini
    não gera um id de tool call como a OpenAI/Anthropic fazem).

Esse provedor traduz o histórico (formato OpenAI) pro formato do Gemini, e
a resposta de volta pro formato normalizado.
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


class GoogleProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        from google import genai
        self.client = genai.Client(api_key=api_key)

    @staticmethod
    def _converter_tools(tools):
        if not tools:
            return None
        declaracoes = []
        for t in tools:
            fn = t["function"]
            declaracoes.append({
                "name": fn["name"],
                "description": fn.get("description", ""),
                "parameters": fn.get("parameters") or {"type": "object", "properties": {}},
            })
        return declaracoes

    @staticmethod
    def _converter_mensagens(messages):
        from google.genai import types

        system_partes = []
        contents = []
        ultimo_foi_tool_result = False

        for m in messages:
            role = m.get("role")

            if role == "system":
                if m.get("content"):
                    system_partes.append(m["content"])
                ultimo_foi_tool_result = False

            elif role == "user":
                contents.append(types.Content(role="user", parts=[types.Part(text=m.get("content") or "")]))
                ultimo_foi_tool_result = False

            elif role == "assistant":
                parts = []
                if m.get("content"):
                    parts.append(types.Part(text=m["content"]))
                for tc in m.get("tool_calls") or []:
                    try:
                        args = json.loads(tc["function"]["arguments"])
                    except Exception:
                        args = {}
                    parts.append(types.Part(function_call=types.FunctionCall(name=tc["function"]["name"], args=args)))
                if parts:
                    contents.append(types.Content(role="model", parts=parts))
                ultimo_foi_tool_result = False

            elif role == "tool":
                parte = types.Part(function_response=types.FunctionResponse(
                    name=m.get("name", ""),
                    response={"resultado": m.get("content") or ""},
                ))
                # Junta resultados de tool consecutivos num único turno
                # "user", igual a Anthropic faz com tool_result.
                if ultimo_foi_tool_result and contents:
                    contents[-1].parts.append(parte)
                else:
                    contents.append(types.Content(role="user", parts=[parte]))
                    ultimo_foi_tool_result = True

        return "\n".join(system_partes), contents

    def chat(self, *, model: str, messages: list, tools: list = None, tool_choice=None, **kwargs):
        from google.genai import types

        system_text, contents = self._converter_mensagens(messages)

        config_kwargs = {}
        if system_text:
            config_kwargs["system_instruction"] = system_text
        declaracoes = self._converter_tools(tools)
        if declaracoes:
            config_kwargs["tools"] = [types.Tool(function_declarations=declaracoes)]
        if "max_tokens" in kwargs:
            config_kwargs["max_output_tokens"] = kwargs.pop("max_tokens")

        resp = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs) if config_kwargs else None,
        )

        texto, tool_calls = None, []
        candidato = resp.candidates[0] if resp.candidates else None
        partes = candidato.content.parts if (candidato and candidato.content and candidato.content.parts) else []
        for i, parte in enumerate(partes):
            if getattr(parte, "text", None):
                texto = (texto or "") + parte.text
            fc = getattr(parte, "function_call", None)
            if fc:
                tool_calls.append(NormalizedToolCall(
                    id=f"gemini_call_{i}",
                    function=NormalizedFunction(name=fc.name, arguments=json.dumps(dict(fc.args or {}))),
                ))

        msg = NormalizedMessage(content=texto, tool_calls=tool_calls or None)
        uso = getattr(resp, "usage_metadata", None)
        total = uso.total_token_count if uso else 0
        return NormalizedCompletion(choices=[NormalizedChoice(message=msg)], usage=NormalizedUsage(total_tokens=total))
