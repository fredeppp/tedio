from datetime import datetime
from threading import Thread

from flask import Flask, jsonify

from .config import ConfigManager
from .logger import LogManager

app_flask = Flask(__name__)


@app_flask.route("/")
def home():
    return jsonify({
        "status": "online",
        "bot": "Tédio AI Discord Agent",
        "tokens_hoje": LogManager.tokens_hoje,
        "timestamp": datetime.now().isoformat()
    })


def _rodar():
    app_flask.run(host="0.0.0.0", port=ConfigManager.PORTA_FLASK)


def iniciar_servidor_web():
    Thread(target=_rodar, daemon=True).start()
    LogManager.log(f"Servidor Flask ativo na porta {ConfigManager.PORTA_FLASK}.", "FLASK")
