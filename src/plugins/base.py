"""
Objeto de contexto passado para toda tool ao ser executada.

Em vez de cada plugin receber (guild, args, nome_usuario) soltos, tudo que
uma tool pode precisar (guild, bot, memory_manager, quem chamou) fica
agrupado aqui. Se um dia uma tool nova precisar de mais alguma coisa (ex:
acesso a outro manager), basta adicionar um atributo aqui em vez de mexer
na assinatura de todas as tools.

Os helpers find_channel/find_member também moraram no ToolManager antigo;
agora vivem aqui porque várias tools (ler_canal, enviar_mensagem, usuario,
anexar_arquivo, buscar_mensagem) precisam deles.
"""


class ToolContext:
    def __init__(self, bot, memory_manager, guild, nome_usuario: str):
        self.bot = bot
        self.memory_manager = memory_manager
        self.guild = guild
        self.nome_usuario = nome_usuario

    def find_channel(self, alvo: str):
        guild = self.guild
        if not guild or not alvo:
            return None
        limpo = str(alvo).strip().replace("<#", "").replace(">", "")
        if limpo.isdigit():
            c = guild.get_channel(int(limpo))
            if c:
                return c
        nome = limpo.replace("#", "").lower()
        return next((c for c in guild.text_channels if c.name.lower() == nome), None)

    def find_member(self, alvo: str):
        guild = self.guild
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
