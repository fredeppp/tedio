#!/usr/bin/env python3
"""Baixa os módulos do Tédio Bot de um repositório GitHub (versão/tag/branch à escolha) e executa."""
import os
import sys
import subprocess
import urllib.request

GITHUB_REPO = os.environ.get("GITHUB_REPO", "seu-usuario/tedio-bot")
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}"

MANIFEST = [
    "src/__init__.py",
    "src/config.py",
    "src/logger.py",
    "src/ui.py",
    "src/memory.py",
    "src/tools.py",
    "src/agent.py",
    "src/bot.py",
    "src/web.py",
    "src/main.py",
    "requirements.txt",
]


def escolher_versao() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    if os.environ.get("TEDIO_VERSION"):
        return os.environ["TEDIO_VERSION"]
    return input("Versão/tag/branch a baixar [main]: ").strip() or "main"


def baixar_arquivo(versao: str, caminho: str) -> bool:
    url = f"{BASE_URL}/{versao}/{caminho}"
    destino = os.path.join(".", caminho)
    os.makedirs(os.path.dirname(destino) or ".", exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            dados = resp.read()
        with open(destino, "wb") as f:
            f.write(dados)
        print(f"[OK] {caminho}")
        return True
    except Exception as e:
        print(f"[FALHA] {caminho}: {e}")
        return False


def instalar_dependencias():
    if os.path.exists("requirements.txt"):
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"], check=False)


def main():
    versao = escolher_versao()
    print(f"Baixando Tédio Bot ({GITHUB_REPO}@{versao})...")

    if not all(baixar_arquivo(versao, f) for f in MANIFEST):
        print("Um ou mais arquivos falharam. Abortando.")
        sys.exit(1)

    instalar_dependencias()
    print("Iniciando bot...")
    subprocess.run([sys.executable, "-m", "src.main"])


if __name__ == "__main__":
    main()
