from .logger import LogManager
from .web import iniciar_servidor_web
from .bot import DiscordManager

if __name__ == "__main__":
    LogManager.log("Inicializando Tédio Bot...", "SYSTEM")
    iniciar_servidor_web()
    DiscordManager().iniciar()
