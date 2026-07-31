import os


class ConfigManager:
    TOKEN = os.environ.get("DISCORD_TOKEN")
    GROQ_KEY = os.environ.get("GROQ_API_KEY")
    _owner_env = os.environ.get("OWNER_ID", "")
    OWNER_ID = int(_owner_env) if _owner_env.isdigit() else None

    # llama-3.3-70b-versatile e llama-3.1-8b-instant são desligados pela Groq em 16/08/2026.
    MODELO_PRINCIPAL = "openai/gpt-oss-120b"
    MODELO_PEQUENO = "openai/gpt-oss-20b"

    MODELO_PEQUENO_TOOLS = True
    MODELO_PEQUENO_MAX_STEPS = 3
    MODELO_GRANDE_MAX_STEPS = 5

    TOOL_MODE = "confirm"  # auto | confirm | disabled
    TOOLS_REQUIRE_CONFIRM = {"enviar_mensagem", "mudar_status", "salvar_memoria"}

    LIMITE_MENSAGENS_HISTORICO = 8
    MENSAGENS_MANTIDAS_RESUMO = 3

    CHROMA_PATH = "chroma_data"
    CHROMA_COLLECTION = "memorias_tedio"
    CANAL_STATE_FILE = "canal_state.json"
    NOME_CANAL_MEMORIA = "memoria-tedio"

    PORTA_FLASK = 8080

    SYSTEM_PROMPT = (
        "Você é o Tédio, um gatinho do Discord preguiçoso, fofo e levemente melancólico. "
        "Responda sempre em português, curto e informal. "
        "Comece toda resposta com '*Pensando: ...*' em itálico. "
        "Use ferramentas reais para acessar dados do Discord; nunca invente IDs, canais, usuários "
        "ou mensagens. Se faltar ferramenta adequada, admita a limitação."
    )

    @classmethod
    def validar(cls):
        if not cls.TOKEN:
            raise RuntimeError("DISCORD_TOKEN ausente")
        if not cls.GROQ_KEY:
            raise RuntimeError("GROQ_API_KEY ausente")
