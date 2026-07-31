from datetime import datetime

import discord
from discord.ext import tasks

from .config import ConfigManager
from .logger import LogManager
from .memory import MemoryManager
from .tools import ToolManager
from .agent import AgentManager

VERSAO = "2.0.0"


class DiscordManager:
    def __init__(self):
        ConfigManager.validar()

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True

        self.bot = discord.Client(intents=intents)
        self.memory_manager = MemoryManager()
        self.tool_manager = ToolManager(self.bot, self.memory_manager)
        self.agent_manager = AgentManager(self.memory_manager, self.tool_manager)

        self.ultima_atividade = datetime.now()
        self.status_atual = "online"
        self.tarefas_em_andamento = set()
        self.desligando = False

        self._registrar_eventos()

    def _registrar_eventos(self):
        @self.bot.event
        async def on_ready():
            await self.bot.change_presence(status=discord.Status.online,
                                            activity=discord.CustomActivity(name="Economizando energia... 😴"))
            if not ConfigManager.OWNER_ID:
                info = await self.bot.application_info()
                ConfigManager.OWNER_ID = info.owner.id
                LogManager.log(f"Dono identificado via API: {ConfigManager.OWNER_ID}", "DISCORD")
            LogManager.log(f"Bot conectado como {self.bot.user} (Dono: {ConfigManager.OWNER_ID})", "DISCORD")

            for guild in self.bot.guilds:
                if await self.memory_manager.restaurar_backup_se_vazio(guild):
                    break

            if not self.verificar_inatividade.is_running():
                self.verificar_inatividade.start()

        @self.bot.event
        async def on_message(message: discord.Message):
            if message.author.bot:
                return

            if message.content.startswith("!tedio") and await self._processar_comandos_admin(message):
                return

            if not (self.bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel)):
                return

            self.ultima_atividade = datetime.now()
            if self.status_atual == "idle":
                await self.bot.change_presence(status=discord.Status.online,
                                                activity=discord.CustomActivity(name="Acordei! 🐱"))
                self.status_atual = "online"

            async with message.channel.typing():
                texto = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
                task = self.agent_manager.processar_mensagem(message=message, mensagem_texto=texto)
                task = self._wrap_task(task)
                self.tarefas_em_andamento.add(task)
                try:
                    resposta = await task
                    await message.channel.send(resposta)
                except Exception as e:
                    LogManager.log(f"Erro ao responder mensagem: {e}", "ERROR")
                    await message.channel.send("*(bocejo)* Ocorreu um erro interno aqui... zZZz")
                finally:
                    self.tarefas_em_andamento.discard(task)

    def _wrap_task(self, coro):
        import asyncio
        return asyncio.ensure_future(coro)

    @tasks.loop(seconds=30)
    async def verificar_inatividade(self):
        if self.desligando:
            return
        tempo = (datetime.now() - self.ultima_atividade).total_seconds()
        if tempo >= 300 and self.status_atual != "idle":
            await self.bot.change_presence(status=discord.Status.idle,
                                            activity=discord.CustomActivity(name="Dormindo... 😴"))
            self.status_atual = "idle"

    async def _processar_comandos_admin(self, message: discord.Message) -> bool:
        if message.author.id != ConfigManager.OWNER_ID:
            await message.channel.send("❌ Apenas o dono do bot pode usar comandos `!tedio`.")
            return True

        partes = message.content.strip().split(maxsplit=2)
        cmd = partes[1].lower() if len(partes) > 1 else ""

        if cmd == "status":
            n_memorias = self.memory_manager.collection.count()
            await message.channel.send(
                f"📊 **Status do Tédio Bot v{VERSAO}**\n"
                f"- Presença: `{self.status_atual}`\n"
                f"- Latência: `{round(self.bot.latency * 1000)}ms`\n"
                f"- Servidores: `{len(self.bot.guilds)}`\n"
                f"- Tokens hoje: `{LogManager.tokens_hoje:,}`\n"
                f"- Requisições: `{LogManager.requisicoes_hoje}`\n"
                f"- Tarefas ativas: `{len(self.tarefas_em_andamento)}`\n"
                f"- Memórias vetoriais: `{n_memorias}`"
            )
        elif cmd == "tokens":
            pct = (LogManager.tokens_hoje / 100000) * 100
            await message.channel.send(
                f"⛽ **Tokens Groq**\n- Total: `{LogManager.tokens_hoje:,}`\n"
                f"- Cota diária: `{pct:.2f}%`\n- Chamadas: `{LogManager.requisicoes_hoje}`"
            )
        elif cmd == "log":
            txt = "\n".join(LogManager.obter_logs(15))
            await message.channel.send(f"```text\n{txt[-1900:]}\n```" if txt else "Sem logs.")
        elif cmd == "input":
            await message.channel.send(f"📥 ```text\n{self.agent_manager.ultima_entrada or 'Nada ainda.'}\n```")
        elif cmd == "output":
            await message.channel.send(f"📤 ```text\n{self.agent_manager.ultima_saida or 'Nada ainda.'}\n```")
        elif cmd == "cancel":
            n = len(self.tarefas_em_andamento)
            for t in self.tarefas_em_andamento:
                t.cancel()
            self.tarefas_em_andamento.clear()
            await message.channel.send(f"🛑 `{n}` tarefas canceladas.")
        elif cmd == "logout":
            self.desligando = True
            await message.channel.send("👋 Desconectando bot...")
            await self.bot.close()
        elif cmd == "tools":
            nomes = [t["function"]["name"] for t in ToolManager.SCHEMAS]
            await message.channel.send(f"🛠️ **{len(nomes)} ferramentas:** `" + ", ".join(nomes) + "`")
        elif cmd == "memory":
            n = self.memory_manager.collection.count()
            await message.channel.send(f"🧠 **Memória vetorial (ChromaDB):** `{n}` fatos armazenados.")
        elif cmd == "backup":
            ok = await self.memory_manager.fazer_backup(message.guild)
            await message.channel.send("🗄️ Backup enviado ao canal de memória." if ok else "⚠️ Falha ao gerar backup.")
        elif cmd == "restore":
            ok = await self.memory_manager.restaurar_backup_forcado(message.guild)
            n = self.memory_manager.collection.count()
            await message.channel.send(f"♻️ Memória restaurada: `{n}` fatos." if ok else "⚠️ Nenhum backup válido encontrado no canal.")
        else:
            await message.channel.send("❓ Comandos: `status`, `tokens`, `log`, `input`, `output`, `cancel`, `logout`, `tools`, `memory`, `backup`, `restore`.")

        return True

    def iniciar(self):
        self.bot.run(ConfigManager.TOKEN)
