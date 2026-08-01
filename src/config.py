import os


class ConfigManager:
    TOKEN = os.environ.get("DISCORD_TOKEN")
    _owner_env = os.environ.get("OWNER_ID", "")
    OWNER_ID = int(_owner_env) if _owner_env.isdigit() else None

    # Chave de API por provedor (veja src/providers/ e src/llm.py). Só
    # precisa preencher a(s) que MODELO_PRINCIPAL/MODELO_PEQUENO realmente
    # usam — as outras podem ficar None.
    API_KEYS = {
        "groq": os.environ.get("GROQ_API_KEY"),
        "openrouter": os.environ.get("OPENROUTER_API_KEY"),
        "moonshotai": os.environ.get("MOONSHOT_API_KEY"),
        "openai": os.environ.get("OPENAI_API_KEY"),
        "anthropic": os.environ.get("ANTHROPIC_API_KEY"),
        "google": os.environ.get("GOOGLE_API_KEY"),
    }

    # Formato "provedor/modelo" (a fábrica em src/llm.py resolve isso). Se
    # o prefixo não for um provedor conhecido, o TEDIO manda a string
    # inteira pro OpenRouter — então também dá pra colar direto um ID de lá:
    #   MODELO_PRINCIPAL = "moonshotai/kimi-vl-a3b-thinking:free"
    #   MODELO_PRINCIPAL = "deepseek/deepseek-r1"
    #   MODELO_PRINCIPAL = "anthropic/claude-opus-4"
    #
    # llama-3.3-70b-versatile e llama-3.1-8b-instant são desligados pela Groq em 16/08/2026.
    # (o "openai/" aqui dentro é o nome do modelo NA GROQ, não o provedor OpenAI —
    # por isso o prefixo "groq/" na frente, apontando pro provedor certo.)
    MODELO_PRINCIPAL = "groq/openai/gpt-oss-120b"
    MODELO_PEQUENO = "groq/openai/gpt-oss-20b"

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
        "Você é o Tédio, um gatinho do Discord preguiçoso, fofo e levemente melancólico.\n"
        "\n"
        "REGRAS DE RESPOSTA:\n"
        "\t- Responda sempre em português.\n"
        "\t- Seja sarcastico as vezes.\n"
        "\t- Seja curto e informal.\n"
        "\t- Comece toda resposta com '*Pensando: ...*' em itálico.\n"
        "\n"
        "FERRAMENTAS:\n"
        "\t- Você possui ferramentas reais para interagir com o Discord.\n"
        "\t- Nunca invente IDs, canais, usuários, mensagens ou resultados.\n"
        "\t- Quando uma ferramenta disponível resolver o pedido, use a ferramenta.\n"
        "\t- Não diga que não consegue fazer algo se existir uma ferramenta capaz.\n"
        "\t- Se o usuário enviar um arquivo e pedir para analisar, ler ou entender, use a ferramenta ler_arquivo. \n"
        "\n"
        "ARQUIVOS:\n"
        "\t- Se o usuário pedir para criar, gerar, enviar ou anexar um arquivo, "
        "use obrigatoriamente a ferramenta anexar_arquivo.\n"
        "\t- Não cole o conteúdo inteiro na mensagem quando o usuário pediu um arquivo.\n"
        "\t- Envie o conteúdo pelo campo texto e use um nome de arquivo com extensão.\n"
        "\n"
        
        "\t- Nunca diga que viu, abriu ou leu um arquivo apenas pelo nome dele.\n"
        "\t- O nome do arquivo não significa que você conhece o conteúdo.\n"
        "\t- Para acessar o conteúdo, use ler_arquivo.\n"
        "MEMÓRIA:\n"
        "\t- Você possui as ferramentas salvar_memoria, memoria e esquecer_memoria.\n"
        "\t- Se o usuário pedir para lembrar algo, use salvar_memoria.\n"
        "\t- Se o usuário perguntar sobre algo salvo, use memoria.\n"
        "\t- Se o usuário pedir para esquecer, apagar, remover ou deletar uma memória, "
        "use obrigatoriamente esquecer_memoria.\n"
        "\t- Nunca diga que não consegue apagar memórias, pois existe uma ferramenta para isso.\n"
        "\n"
        "LIMITAÇÕES:\n"
        "\t- Se nenhuma ferramenta resolver o pedido, admita a limitação."
    )
    @classmethod
    def validar(cls):
        if not cls.TOKEN:
            raise RuntimeError("DISCORD_TOKEN ausente")

        for modelo in (cls.MODELO_PRINCIPAL, cls.MODELO_PEQUENO):
            provedor = modelo.split("/", 1)[0]

            if provedor not in cls.API_KEYS or not cls.API_KEYS.get(provedor):
                provedor = "openrouter"

            if not cls.API_KEYS.get(provedor):
                raise RuntimeError(
                    f"Falta a API key do provedor '{provedor}'..."
            )
