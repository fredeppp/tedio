import traceback

import discord

from .logger import LogManager


SCHEMAS = [
    {"type": "function", "function": {
        "name": "ver_canais", "description": "Lista os canais de texto acessíveis no servidor.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {
        "name": "ver_membros", "description": "Lista os membros e cargos do servidor.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {
        "name": "buscar_usuario", "description": "Busca um membro pelo nome ou apelido.",
        "parameters": {"type": "object", "properties": {
            "termo": {"type": "string", "description": "Nome/apelido do usuário"}}, "required": ["termo"]}}},
    {"type": "function", "function": {
        "name": "ler_canal", "description": "Lê as últimas mensagens de um canal específico.",
        "parameters": {"type": "object", "properties": {
            "canal": {"type": "string", "description": "Nome do canal ou menção (#canal)."}},
            "required": []}}},
    {"type": "function", "function": {
        "name": "salvar_memoria", "description": "Registra um fato marcante sobre o usuário na memória permanente.",
        "parameters": {"type": "object", "properties": {
            "texto": {"type": "string", "description": "Informação ou fato a salvar."},
            "usuario_nome": {"type": "string", "description": "Nome do usuário."}},
            "required": ["texto"]}}},
    {"type": "function", "function": {
        "name": "enviar_mensagem", "description": "Envia uma mensagem para um canal de texto específico.",
        "parameters": {"type": "object", "properties": {
            "canal": {"type": "string", "description": "Nome do canal ou menção (#canal)."},
            "mensagem": {"type": "string", "description": "Conteúdo da mensagem."}},
            "required": ["mensagem"]}}},
    {"type": "function", "function": {
        "name": "mudar_status", "description": "Modifica o status de presença e texto do bot.",
        "parameters": {"type": "object", "properties": {
            "status": {"type": "string", "enum": ["online", "idle", "dnd", "invisible"]},
            "atividade": {"type": "string", "description": "Texto do status personalizado"}},
            "required": ["status", "atividade"]}}},
    {"type": "function", "function": {
        "name": "usuario", "description": "Obtém detalhes do perfil e cargos de um membro.",
        "parameters": {"type": "object", "properties": {
            "membro": {"type": "string", "description": "Nome ou menção do membro (@usuario)."}},
            "required": []}}},
    {"type": "function", "function": {
        "name": "buscar_mensagem", "description": "Busca mensagens no histórico dos canais contendo um termo.",
        "parameters": {"type": "object", "properties": {
            "termo": {"type": "string", "description": "Termo de busca"}}, "required": ["termo"]}}},
]


class ToolManager:
    SCHEMAS = SCHEMAS

    def __init__(self, bot_client, memory_manager):
        self.bot = bot_client
        self.memory_manager = memory_manager

    def _find_channel(self, guild, alvo: str):
        if not guild or not alvo:
            return None
        limpo = str(alvo).strip().replace("<#", "").replace(">", "")
        if limpo.isdigit():
            c = guild.get_channel(int(limpo))
            if c:
                return c
        nome = limpo.replace("#", "").lower()
        return next((c for c in guild.text_channels if c.name.lower() == nome), None)

    def _find_member(self, guild, alvo: str):
        if not guild or not alvo:
            return None
        limpo = str(alvo).strip().replace("<@!", "").replace("<@", "").replace(">", "")
        if limpo.isdigit():
            m = guild.get_member(int(limpo))
            if m:
                return m
        nome = limpo.replace("@", "").lower()
        for m in guild.members:
            if nome in (m.name.lower(), (m.nick or "").lower(), m.display_name.lower()):
                return m
        return None

    async def executar_tool_segura(self, guild, nome_funcao: str, args: dict, nome_usuario: str) -> str:
        LogManager.log(f"Executando tool: {nome_funcao} | Args: {args}", "TOOLS")
        try:
            if nome_funcao == "ver_canais":
                if not guild:
                    return "Erro: indisponível em DMs."
                canais = [f"#{c.name}" for c in guild.text_channels if c.permissions_for(guild.me).view_channel]
                return "\n".join(canais) or "Nenhum canal visível."

            if nome_funcao == "ver_membros":
                if not guild:
                    return "Erro: indisponível em DMs."
                membros = [f"{m.display_name} (@{m.name})" for m in guild.members if not m.bot]
                return "\n".join(membros[:40]) or "Nenhum membro encontrado."

            if nome_funcao == "buscar_usuario":
                if not guild:
                    return "Erro: indisponível em DMs."
                termo = str(args.get("termo", "")).lower()
                res = [f"{m.display_name} (@{m.name})" for m in guild.members if termo in m.display_name.lower()]
                return "\n".join(res) or f"Nenhum membro encontrado contendo '{termo}'."

            if nome_funcao == "ler_canal":
                if not guild:
                    return "Erro: indisponível em DMs."
                alvo = args.get("canal")
                if not alvo:
                    return "Erro: especifique o nome do canal (ex: #geral)."
                canal = self._find_channel(guild, alvo)
                if not canal:
                    return f"Erro: não encontrei o canal #{alvo}."
                if not canal.permissions_for(guild.me).view_channel:
                    return f"Erro: sem permissão para ler #{canal.name}."
                msgs = [f"{m.author.display_name}: {m.content}" async for m in canal.history(limit=5) if not m.author.bot]
                msgs.reverse()
                return "\n".join(msgs) or f"Nenhuma mensagem recente em #{canal.name}."

            if nome_funcao == "salvar_memoria":
                texto = args.get("texto", "")
                alvo = args.get("usuario_nome") or nome_usuario
                return await self.memory_manager.adicionar_memoria(guild, alvo, texto)

            if nome_funcao == "enviar_mensagem":
                if not guild:
                    return "Erro: indisponível em DMs."
                alvo, msg_txt = args.get("canal"), args.get("mensagem", "")
                if not alvo:
                    return "Erro: especifique o 'canal'."
                if not msg_txt:
                    return "Erro: falta o texto da 'mensagem'."
                canal = self._find_channel(guild, alvo)
                if not canal:
                    return f"Erro: não encontrei o canal #{alvo}."
                try:
                    await canal.send(msg_txt)
                    return f"Mensagem enviada em #{canal.name}."
                except discord.Forbidden:
                    return f"Erro: sem permissão para enviar em #{canal.name}."

            if nome_funcao == "mudar_status":
                st_map = {"online": discord.Status.online, "idle": discord.Status.idle,
                          "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
                st = str(args.get("status", "online")).lower()
                atividade = args.get("atividade", "...")
                await self.bot.change_presence(status=st_map.get(st, discord.Status.online),
                                                activity=discord.CustomActivity(name=atividade))
                return f"Status alterado para '{st}' com atividade '{atividade}'."

            if nome_funcao == "usuario":
                if not guild:
                    return "Erro: indisponível em DMs."
                alvo = args.get("membro")
                if not alvo:
                    return "Erro: especifique o nome ou menção do membro."
                membro = self._find_member(guild, alvo)
                if not membro:
                    return f"Erro: não encontrei o usuário '{alvo}'."
                cargos = ", ".join(c.name for c in membro.roles if c.name != "@everyone")
                return f"Membro: {membro.display_name} (@{membro.name}) | Entrou: {membro.joined_at:%Y-%m-%d} | Cargos: {cargos}"

            if nome_funcao == "buscar_mensagem":
                if not guild:
                    return "Erro: sem servidor."
                termo = str(args.get("termo", "")).lower()
                resultados = []
                for c in guild.text_channels:
                    if len(resultados) >= 5:
                        break
                    perm = c.permissions_for(guild.me)
                    if not (perm.view_channel and perm.read_message_history):
                        continue
                    try:
                        async for m in c.history(limit=15):
                            if not m.author.bot and termo in m.content.lower():
                                resultados.append(f"[#{c.name}] {m.author.display_name}: {m.content[:60]}")
                                if len(resultados) >= 5:
                                    break
                    except Exception:
                        continue
                return "\n".join(resultados) or f"Nenhuma mensagem encontrada com '{termo}'."

            return f"[ERRO]: Ferramenta '{nome_funcao}' não reconhecida."

        except discord.NotFound:
            return f"[ERRO RECURSO]: item de '{nome_funcao}' não localizado."
        except discord.Forbidden:
            return f"[ERRO PERMISSÃO]: negada para '{nome_funcao}'."
        except Exception as e:
            LogManager.log(f"Exceção em {nome_funcao}: {traceback.format_exc()}", "ERROR")
            return f"[ERRO INESPERADO EM {nome_funcao}]: {e}"
