from collections import deque
from datetime import datetime


class LogManager:
    _buffer = deque(maxlen=200)
    tokens_hoje = 0
    requisicoes_hoje = 0

    @classmethod
    def log(cls, texto: str, nivel: str = "INFO"):
        linha = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [{nivel}] {texto}"
        cls._buffer.append(linha)
        print(linha)

    @classmethod
    def registrar_tokens(cls, qtd: int):
        cls.tokens_hoje += qtd
        cls.requisicoes_hoje += 1

    @classmethod
    def obter_logs(cls, n: int = 50):
        return list(cls._buffer)[-n:]
