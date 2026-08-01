import re
import json
import asyncio

from . import llm
from .config import ConfigManager
from .logger import LogManager
from .tools import ToolManager
from .ui import ToolApprovalView
#chamar_llm_com_fallback

# Mantido apenas para referência/compatibilidade (não é mais usado no roteamento,
# que agora é feito por substring em rotear_intencao).
PALAVRAS_ACAO = {
    "canal", "canais",
    "membro", "membros",
    "usuario", "usuário",
    "status",
    "dormir",
    "online",
    "memoria", "memória",
    "lembre", "guarde",
    "pesquisar",
    "buscar",
    "enviar",
    "falar",
    "servidor",
    "cargo", "cargos",
    "id",

    # arquivos
    "arquivo",
    "arquivo.py",
    "criar",
    "cria",
    "gerar",
    "gera",
    "anexar",
    "anexo",
    "mandar",
    "baixar",
    "download",
}
CUMPRIMENTOS_SIMPLES = {"oi", "olá", "ola", "opa", "eai", "e aí", "tudo bem", "boa tarde", "bom dia", "boa noite"}

# Alguns modelos, sob pressão de contexto, descrevem a chamada de função como texto
# (ex: <function=nome{"arg": "valor"}></function>) em vez de retornar tool_calls estruturado.
# Isso é tratado como rede de segurança: extrai, confirma e executa como uma tool real.
PSEUDO_FUNC_RE = re.compile(r"<function=(?P<name>\w+)(?P<args>\{.*?\})?\s*/?>\s*(?:</function>)?", re.DOTALL)

# Gatilhos de roteamento por substring (pegam "teste.py", "arquivo chamado teste.py", etc,
# que o antigo matching por palavra inteira perdia).
USAR_TRIGGERS = False
#como vc pode ver isso apenas deixa o modelos desidir se vai usar as tool ⬇ ⬇ ⬇ 
#comp_final
GATILHOS_ACAO = [
    "canal", "canais",
    "membro", "membros",
    "usuario", "usuário",
    "status",
    "dormir",
    "online",
    "memoria", "memória",
    "lembre", "guarde",
    "pesquisar",
    "buscar",
    "enviar",
    "falar",
    "servidor",
    "cargo", "cargos",
    " id ",

    # arquivos
    "arquivo",
    "criar",
    "cria",
    "gerar",
    "gera",
    "anexar",
    "anexo",
    "mandar",
    "baixar",
    "download",
    ".py",
    ".lua",
    ".txt",
    ".json",
    ".js",
    ".ts",
    ".md",
]


class AgentManager:
    def __init__(self, memory_manager, tool_manager: ToolManager):
        self.memory_manager = memory_manager
        self.tool_manager = tool_manager
        self.historico_canais = {}
        self.ultima_entrada = ""
        self.ultima_saida = ""

    def rotear_intencao(self, texto: str) -> bool:
        texto_low = f" {texto.lower()} "
        if not USAR_TRIGGERS:
            return True  
        return any(gatilho in texto_low for gatilho in GATILHOS_ACAO)

    def selecionar_modelo(self, mensagem: str, precisa_tools: bool) -> str:
        msg = mensagem.strip().lower()
        if precisa_tools and not ConfigManager.MODELO_PEQUENO_TOOLS:
            return ConfigManager.MODELO_PRINCIPAL
        palavras = msg.split()
        simples = (
            msg in CUMPRIMENTOS_SIMPLES or
            any(r in msg for r in ["kkk", "hahah", "rsrs"]) or
            "opinião" in msg or "acha" in msg or
            (not precisa_tools and len(palavras) <= 10)
        )
        return ConfigManager.MODELO_PEQUENO if simples else ConfigManager.MODELO_PRINCIPAL

    def extrair_tempo_espera(self, erro_str: str) -> float:
        m = re.search(r"try again in (\d+)m([\d.]+)s", erro_str)
        if m:
            return float(m.group(1)) * 60 + float(m.group(2))
        m = re.search(r"try again in ([\d.]+)s", erro_str)
        return float(m.group(1)) if m else 5.0

    async def chamar_llm_com_fallback(self, modelo_preferencial: str, kwargs: dict):

        modelos = [modelo_preferencial]
        if modelo_preferencial != ConfigManager.MODELO_PEQUENO:
            modelos.append(ConfigManager.MODELO_PEQUENO)

        ultimo_erro = None
        for modelo in modelos:
            tentativa = kwargs.copy()
            if modelo == ConfigManager.MODELO_PEQUENO and not ConfigManager.MODELO_PEQUENO_TOOLS:
                tentativa.pop("tools", None)
                tentativa.pop("tool_choice", None)
            try:
                LogManager.log(f"Chamando LLM [{modelo}]...", "AGENT")
                comp = await llm.achat(modelo, **tentativa)
                if getattr(comp, "usage", None):
                    LogManager.registrar_tokens(comp.usage.total_tokens)
                return comp
            except Exception as e:
                erro_txt, ultimo_erro = str(e), e
                if "429" not in erro_txt and "rate_limit" not in erro_txt.lower():
                    raise
                espera = self.extrair_tempo_espera(erro_txt)
                LogManager.log(f"Rate limit em [{modelo}]. Espera: {espera:.1f}s", "WARNING")
                if espera <= 8.0 and modelo == ConfigManager.MODELO_PEQUENO:
                    await asyncio.sleep(espera)
                    try:
                        comp = await llm.achat(modelo, **tentativa)
                        if getattr(comp, "usage", None):
                            LogManager.registrar_tokens(comp.usage.total_tokens)
                        return comp
                    except Exception as e_retry:
                        ultimo_erro = e_retry
                continue

        LogManager.log(
            f"DEBUG REQUEST [{modelo}] tools={'tools' in tentativa} choice={tentativa.get('tool_choice')}",
            "DEBUG"
        )
        raise ultimo_erro

    async def resumir_historico_se_necessario(self, canal_id: int):
        historico = self.historico_canais.get(canal_id, [])
        if len(historico) <= ConfigManager.LIMITE_MENSAGENS_HISTORICO:
            return

        corpo, resumo_existente, offset = historico[1:], "", 0
        if corpo and corpo[0].get("role") == "system" and corpo[0].get("content", "").startswith("[RESUMO]:"):
            resumo_existente = corpo[0]["content"].replace("[RESUMO]:", "").strip()
            offset = 1

        a_resumir = corpo[offset:-ConfigManager.MENSAGENS_MANTIDAS_RESUMO]
        mantidas = corpo[-ConfigManager.MENSAGENS_MANTIDAS_RESUMO:]
        if not a_resumir:
            return

        texto = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in a_resumir if m.get("content"))
        prompt = f"Resuma em no máximo 50 palavras:\n{texto}"
        if resumo_existente:
            prompt = f"Resumo anterior: {resumo_existente}\n{prompt}"

        try:
            res = await llm.achat(
                ConfigManager.MODELO_PEQUENO,
                messages=[{"role": "system", "content": "Você é um resumidor sucinto."},
                          {"role": "user", "content": prompt}]
            )
            if getattr(res, "usage", None):
                LogManager.registrar_tokens(res.usage.total_tokens)
            novo_resumo = res.choices[0].message.content.strip()
            self.historico_canais[canal_id] = (
                [historico[0]] + [{"role": "system", "content": f"[RESUMO]: {novo_resumo}"}] + mantidas
            )
            LogManager.log(f"Histórico do canal {canal_id} resumido.", "AGENT")
        except Exception as e:
            LogManager.log(f"Falha ao resumir histórico: {e}", "ERROR")

    def _extrair_pseudo_tool_calls(self, texto: str):
        achados = []
        for m in PSEUDO_FUNC_RE.finditer(texto or ""):
            args_raw = m.group("args") or "{}"
            try:
                args = json.loads(args_raw)
            except Exception:
                args = {}
            achados.append((m.group("name"), args))
        return achados

    async def confirmar_tool(self, message, nome_fn: str, args: dict) -> bool:
        if ConfigManager.TOOL_MODE == "disabled":
            return False
        if ConfigManager.TOOL_MODE == "auto" or nome_fn not in ConfigManager.TOOLS_REQUIRE_CONFIRM:
            return True

        import discord
        embed = discord.Embed(
            title="😴 Minha preguiça chegou ao limite",
            description="Preciso usar meus poderes pra resolver isso. Posso fazer?",
            color=discord.Color.orange()
        )
        embed.add_field(name="Ferramenta", value=f"`{nome_fn}`", inline=False)
        embed.add_field(name="Dados", value=f"```json\n{json.dumps(args, indent=2, ensure_ascii=False)[:900]}\n```", inline=False)

        view = ToolApprovalView(author=message.author, tool_name=nome_fn)
        await message.channel.send(embed=embed, view=view)
        await view.wait()

        LogManager.log(f"{'Autorizado' if view.is_approved else 'Recusado'} por {message.author}: {nome_fn}", "TOOLS")
        return bool(view.is_approved)

    async def processar_mensagem(self, message, mensagem_texto: str) -> str:
        canal_id = message.channel.id
        guild = message.guild
        nome_usuario = message.author.display_name
        self.ultima_entrada = mensagem_texto

        memorias = self.memory_manager.obter_memorias_relevantes(nome_usuario, mensagem_texto)
        str_memoria = f"\n[Fatos sobre {nome_usuario}: {'; '.join(memorias)}]" if memorias else ""

        if canal_id not in self.historico_canais:
            self.historico_canais[canal_id] = [{"role": "system", "content": ConfigManager.SYSTEM_PROMPT + str_memoria}]

        self.historico_canais[canal_id].append({"role": "user", "content": f"{nome_usuario}: {mensagem_texto}"})
        await self.resumir_historico_se_necessario(canal_id)

        precisa_tools = self.rotear_intencao(mensagem_texto)
        modelo_atual = self.selecionar_modelo(mensagem_texto, precisa_tools)
        limite_passos = (ConfigManager.MODELO_PEQUENO_MAX_STEPS if modelo_atual == ConfigManager.MODELO_PEQUENO
                          else ConfigManager.MODELO_GRANDE_MAX_STEPS)
        tools_ativas = precisa_tools and (ConfigManager.MODELO_PEQUENO_TOOLS if modelo_atual == ConfigManager.MODELO_PEQUENO else True)

        LogManager.log(f"Modelo: {modelo_atual} | Tools: {tools_ativas} | Max steps: {limite_passos}", "AGENT")

        sessao = list(self.historico_canais[canal_id])
        resposta_final = ""

        try:
            for _ in range(limite_passos):
                kwargs = {"messages": sessao}
                if tools_ativas:
                    kwargs["tools"] = ToolManager.SCHEMAS
                    kwargs["tool_choice"] = "auto"
                

                comp = await self.chamar_llm_com_fallback(modelo_atual, kwargs)
                msg = comp.choices[0].message
                tool_calls = getattr(msg, "tool_calls", None)

                if not tool_calls:
                    pseudo = self._extrair_pseudo_tool_calls(msg.content)
                    if not pseudo:
                        resposta_final = msg.content or ""
                        break

                    LogManager.log(f"Tool call descrito como texto (não estruturado): {pseudo}", "WARNING")
                    texto_limpo = PSEUDO_FUNC_RE.sub("", msg.content or "").strip()
                    sessao.append({"role": "assistant", "content": texto_limpo or None})

                    for nome_fn, args_fn in pseudo:
                        autorizado = await self.confirmar_tool(message, nome_fn, args_fn)
                        res_tool = ("Ação cancelada: o usuário recusou a execução desta ferramenta." if not autorizado
                                    else await self.tool_manager.executar_tool_segura(guild, nome_fn, args_fn, nome_usuario))
                        sessao.append({"role": "user",
                                       "content": f"[Resultado da ferramenta {nome_fn}]: {res_tool}"})
                    continue

                sessao.append({
                    "role": "assistant", "content": msg.content or None,
                    "tool_calls": [{"id": tc.id, "type": "function",
                                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                                    for tc in tool_calls]
                })

                for tc in tool_calls:
                    nome_fn = tc.function.name
                    try:
                        args_fn = json.loads(tc.function.arguments)
                    except Exception:
                        args_fn = {}

                    autorizado = await self.confirmar_tool(message, nome_fn, args_fn)
                    res_tool = ("Ação cancelada: o usuário recusou a execução desta ferramenta." if not autorizado
                                else await self.tool_manager.executar_tool_segura(guild, nome_fn, args_fn, nome_usuario))

                    sessao.append({"role": "tool", "tool_call_id": tc.id, "name": nome_fn, "content": str(res_tool)})

            # Se o loop terminou porque estourou limite_passos com tool_calls pendentes
            # (sem nunca cair no "break" acima), força uma resposta final SEM tools ativas,
            # para nunca cair no erro "Tool choice is none, but model called a tool" nem
            # deixar a resposta vazia.
            if not resposta_final:
                comp_final = await self.chamar_llm_com_fallback(
                    modelo_atual,
                    {
                        "messages": sessao,
                        
                    }
                )
                resposta_final = comp_final.choices[0].message.content or ""

        except Exception as e:
            LogManager.log(f"Falha crítica no pipeline de IA: {e}", "ERROR")
            resposta_final = ("*Pensando: Minha energia acabou...*\n*(bocejo)* Minha cota de pensamentos "
                               "estourou na nuvem... me deixa dormir um pouco zZZz")

        self.historico_canais[canal_id].append({"role": "assistant", "content": resposta_final})
        self.ultima_saida = resposta_final
        return resposta_final
        #chamar_llm_com_fallback
        # tools_ativas
        #comp_final