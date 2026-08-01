import os
import io
import json
import uuid
import shutil
import zipfile

import discord
import chromadb
from chromadb.utils import embedding_functions

from .logger import LogManager
from .config import ConfigManager

BACKUP_FILENAME = "chroma_backup.zip"


class MemoryManager:
    """Memória semântica em ChromaDB, com log legível e backup em zip no canal do Discord."""

    def __init__(self):
        self._init_client()
        self.canal_state = self._carregar_canal_state()

    def _init_client(self):
        self._client = chromadb.PersistentClient(path=ConfigManager.CHROMA_PATH)
        self._ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self._client.get_or_create_collection(
            name=ConfigManager.CHROMA_COLLECTION, embedding_function=self._ef
        )

    def _carregar_canal_state(self) -> dict:
        if not os.path.exists(ConfigManager.CANAL_STATE_FILE):
            return {}
        try:
            with open(ConfigManager.CANAL_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _salvar_canal_state(self):
        tmp = ConfigManager.CANAL_STATE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.canal_state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, ConfigManager.CANAL_STATE_FILE)

    # ---------- leitura / escrita de fatos ----------

    def obter_memorias(self, usuario: str) -> list:
        res = self.collection.get(where={"usuario": usuario})
        return res.get("documents") or []

    def obter_memorias_relevantes(self, usuario: str, pergunta: str, k: int = 3) -> list:
        if self.collection.count() == 0:
            return []
        res = self.collection.query(query_texts=[pergunta], n_results=k, where={"usuario": usuario})
        docs = res.get("documents") or [[]]
        return docs[0]

    async def adicionar_memoria(self, guild, usuario: str, texto: str) -> str:
        if texto in self.obter_memorias(usuario):
            return "Esta informação já está salva na minha memória."

        fato_id = f"{usuario}:{uuid.uuid4().hex[:8]}"
        self.collection.add(ids=[fato_id], documents=[texto], metadatas=[{"usuario": usuario}])
        LogManager.log(f"Memória vetorial registrada para {usuario}: {texto}", "MEMORY")

        if guild:
            await self._sincronizar_canal(guild, usuario)
            await self.fazer_backup(guild)

        return f"Memória memorizada: '{texto}'"

    # ---------- painel legível por usuário no canal ----------

    async def _sincronizar_canal(self, guild, usuario: str):
        try:
            canal = await self._garantir_canal(guild)
            if not canal:
                return
            fatos = self.obter_memorias(usuario)
            conteudo = f"**{usuario}:**\n" + "\n".join(f"- {f}" for f in fatos)

            msg_id = self.canal_state.get(usuario)
            msg = None
            if msg_id:
                try:
                    msg = await canal.fetch_message(msg_id)
                except Exception:
                    msg = None

            if msg:
                await msg.edit(content=conteudo[:2000])
            else:
                msg = await canal.send(conteudo[:2000])
                self.canal_state[usuario] = msg.id
                self._salvar_canal_state()
        except Exception as e:
            LogManager.log(f"Falha ao sincronizar canal de memória: {e}", "ERROR")

    async def _garantir_canal(self, guild):
        canal = discord.utils.get(guild.text_channels, name=ConfigManager.NOME_CANAL_MEMORIA)
        if canal:
            return canal
        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            return await guild.create_text_channel(
                ConfigManager.NOME_CANAL_MEMORIA,
                overwrites=overwrites,
                topic="Log e backup da memória vetorial do agente Tédio (ChromaDB)."
            )
        except Exception as e:
            LogManager.log(f"Erro ao criar canal de memória: {e}", "ERROR")
            return None

    # ---------- backup / restauração do chroma_data no canal ----------

    async def fazer_backup(self, guild) -> bool:
        if not guild:
            return False
        try:
            canal = await self._garantir_canal(guild)
            if not canal:
                return False

            buf = io.BytesIO()
            base = ConfigManager.CHROMA_PATH
            if not os.path.isdir(base):
                return False

            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for raiz, _, arquivos in os.walk(base):
                    for nome in arquivos:
                        caminho = os.path.join(raiz, nome)
                        zf.write(caminho, os.path.relpath(caminho, base))
            buf.seek(0)

            antigos = [m async for m in canal.history(limit=50)
                       if any(a.filename == BACKUP_FILENAME for a in m.attachments)]

            await canal.send(
                content=f"🗄️ Backup da memória vetorial ({self.collection.count()} fatos).",
                file=discord.File(fp=buf, filename=BACKUP_FILENAME)
            )
            for m in antigos:
                try:
                    await m.delete()
                except Exception:
                    pass

            LogManager.log("Backup do chroma_data enviado ao canal de memória.", "MEMORY")
            return True
        except Exception as e:
            LogManager.log(f"Falha ao fazer backup da memória: {e}", "ERROR")
            return False

    async def restaurar_backup_se_vazio(self, guild) -> bool:
        if self.collection.count() > 0:
            return False
        return await self._restaurar(guild)

    async def restaurar_backup_forcado(self, guild) -> bool:
        return await self._restaurar(guild)

    async def _restaurar(self, guild) -> bool:
        if not guild:
            return False
        canal = await self._garantir_canal(guild)
        if not canal:
            return False

        anexo = None
        async for msg in canal.history(limit=50):
            for a in msg.attachments:
                if a.filename == BACKUP_FILENAME:
                    anexo = a
                    break
            if anexo:
                break

        if not anexo:
            LogManager.log("Nenhum backup de memória encontrado no canal.", "MEMORY")
            return False

        try:
            dados = await anexo.read()
            shutil.rmtree(ConfigManager.CHROMA_PATH, ignore_errors=True)
            with zipfile.ZipFile(io.BytesIO(dados)) as zf:
                zf.extractall(ConfigManager.CHROMA_PATH)
            self._init_client()
            LogManager.log(f"Memória restaurada do backup do Discord ({self.collection.count()} fatos).", "MEMORY")
            return True
        except Exception as e:
            LogManager.log(f"Falha ao restaurar backup de memória: {e}", "ERROR")
            return False

    def remover_memoria(self, usuario: str, texto: str):
        res = self.collection.get(
            where={"usuario": usuario}
        )

        removidas = 0
        palavras = texto.lower().split()

        for doc_id, doc in zip(res["ids"], res["documents"]):
            if all(p in doc.lower() for p in palavras):
                self.collection.delete(ids=[doc_id])

                LogManager.log(
                    f"Memória removida de {usuario}: {doc}",
                    "MEMORY"
                )

                removidas += 1

        return removidas > 0