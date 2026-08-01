from datetime import datetime
from threading import Thread

from flask import Flask, jsonify, render_template_string

from .config import ConfigManager
from .logger import LogManager


app_flask = Flask(__name__)

# Versão segura do HTML com animação procedural real e logs coloridos dinâmicos
HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>TEDIO Dashboard - Terminal</title>

<style>
    /* Estilo Terminal Raiz */
    body {
        background: #000;
        color: #0f0;
        font-family: "Courier New", Courier, monospace;
        margin: 0;
        padding: 20px;
        height: 100vh;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
    }

    h1 {
        font-size: 1.2rem;
        border-bottom: 1px dashed #0f0;
        padding-bottom: 10px;
        margin-top: 0;
    }

    .container {
        display: flex;
        gap: 20px;
        flex: 1;
        overflow: hidden;
    }

    .panel {
        border: 1px solid #333;
        padding: 15px;
        display: flex;
        flex-direction: column;
    }

    .status-panel {
        width: 300px;
        min-width: 300px;
    }

    .logs-panel {
        flex: 1;
    }

    h3 {
        margin: 0 0 15px 0;
        font-size: 1rem;
        color: #fff;
    }

    #status {
        line-height: 1.6;
        margin-bottom: auto;
    }

    #logs {
        white-space: pre-wrap;
        word-wrap: break-word;
        color: #ccc;
        overflow-y: auto;
        flex: 1;
        padding-right: 10px;
    }

    /* Bonsai Terminal */
    #bonsai {
        color: #0a0;
        white-space: pre;
        font-size: 14px;
        margin-top: 20px;
        border-top: 1px dashed #333;
        padding-top: 15px;
    }

    /* Scrollbar minimalista */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #0f0; }
</style>
</head>
<body>

<h1>root@tedio-sys:~# ./dashboard.sh</h1>

<div class="container">
    <div class="panel status-panel">
        <h3>[ STATUS ]</h3>
        <div id="status">Iniciando sistema...</div>
        
        <div id="bonsai"></div>
    </div>

    <div class="panel logs-panel">
        <h3>[ LOGS ]</h3>
        <div id="logs">Aguardando dados...</div>
    </div>
</div>

<script>
// --- BONSAI PROCEDURAL FRACTAL (ANIMADO) ---
let gradeBonsai = [];
let filaPassos = [];
let animacaoInterval;
const LARGURA = 40;
const ALTURA = 16;

function iniciarBonsai() {
    gradeBonsai = [];
    filaPassos = [];
    
    // 1. Cria a grade vazia
    for (let i = 0; i < ALTURA; i++) {
        let linha = [];
        for (let j = 0; j < LARGURA; j++) {
            linha.push(" ");
        }
        gradeBonsai.push(linha);
    }

    let meio = Math.floor(LARGURA / 2);

    // 2. Renderiza o vaso instantaneamente
    for(let b = meio - 6; b <= meio + 6; b++) gradeBonsai[ALTURA - 2][b] = "=";
    gradeBonsai[ALTURA - 2][meio - 7] = "[";
    gradeBonsai[ALTURA - 2][meio + 7] = "]";
    gradeBonsai[ALTURA - 1][meio - 6] = "\\\\";
    gradeBonsai[ALTURA - 1][meio + 6] = "/";
    for(let b = meio - 5; b <= meio + 5; b++) gradeBonsai[ALTURA - 1][b] = "_";

    // 3. Função para registrar o rastro dos galhos na fila (Sem travar o navegador)
    function tracaLinha(x0, y0, x1, y1, char) {
        let dx = Math.abs(x1 - x0);
        let dy = Math.abs(y1 - y0);
        let sx = (x0 < x1) ? 1 : -1;
        let sy = (y0 < y1) ? 1 : -1;
        let err = dx - dy;

        while (true) {
            if (x0 >= 0 && x0 < LARGURA && y0 >= 0 && y0 < ALTURA) {
                filaPassos.push({x: x0, y: y0, c: char});
            }
            if (x0 === x1 && y0 === y1) break;
            let e2 = 2 * err;
            if (e2 > -dy) { err -= dy; x0 += sx; }
            if (e2 < dx) { err += dx; y0 += sy; }
        }
    }

    // 4. Lógica fractal
    function ramificar(x, y, angulo, tamanho, prof) {
        if (prof === 0) {
            const folhas = ["@", "#", "*", "&", "%"];
            for (let fy = -1; fy <= 1; fy++) {
                for (let fx = -2; fx <= 2; fx++) {
                    if (Math.random() > 0.4) {
                        let nx = Math.round(x + fx);
                        let ny = Math.round(y + fy);
                        if (nx >= 0 && nx < LARGURA && ny >= 0 && ny < ALTURA) {
                            filaPassos.push({x: nx, y: ny, c: folhas[Math.floor(Math.random() * folhas.length)]});
                        }
                    }
                }
            }
            return;
        }

        let xFim = Math.round(x + Math.cos(angulo) * tamanho);
        let yFim = Math.round(y - Math.sin(angulo) * tamanho);
        
        let charGalho = "|";
        if (angulo > 1.8) charGalho = "\\\\";
        else if (angulo < 1.3) charGalho = "/";

        tracaLinha(Math.round(x), Math.round(y), xFim, yFim, charGalho);

        let mutacao = 0.2 + (Math.random() * 0.4);
        let encolhe = 0.6 + (Math.random() * 0.2);

        ramificar(xFim, yFim, angulo - mutacao, tamanho * encolhe, prof - 1);
        ramificar(xFim, yFim, angulo + mutacao, tamanho * encolhe, prof - 1);
        
        if (Math.random() > 0.6) {
            ramificar(xFim, yFim, angulo + (Math.random() - 0.5) * 0.2, tamanho * encolhe * 0.8, prof - 1);
        }
    }

    // Processa a árvore toda nos bastidores e joga na fila
    ramificar(meio, ALTURA - 3, Math.PI / 2, 5, 3);
    
    renderizarBonsai();
    
    // Inicia a animação de crescimento (30ms por frame)
    clearInterval(animacaoInterval);
    animacaoInterval = setInterval(animarCrescimento, 30);
}

function renderizarBonsai() {
    let texto = "";
    for (let i = 0; i < gradeBonsai.length; i++) {
        texto += gradeBonsai[i].join("") + "\\n";
    }
    document.getElementById("bonsai").innerText = texto;
}

function animarCrescimento() {
    // Se acabaram os passos, para a animação e agenda o recomeço
    if (filaPassos.length === 0) {
        clearInterval(animacaoInterval);
        setTimeout(iniciarBonsai, 15000); // Fica parado 15 segs e depois gera outra árvore
        return;
    }
    
    // Velocidade de crescimento: desenha 3 caracteres por "frame"
    let velocidade = 3; 
    for(let i = 0; i < velocidade; i++){
        if(filaPassos.length === 0) break;
        let passo = filaPassos.shift();
        gradeBonsai[passo.y][passo.x] = passo.c;
    }
    
    renderizarBonsai();
}

// Inicia a primeira semente
iniciarBonsai();


// --- SISTEMA DE ATUALIZACAO DOS LOGS E STATUS ---
async function atualizar() {
    // Atualiza Status
    try {
        let resStatus = await fetch("/api/status");
        let dados = await resStatus.json();

        let bot = dados.bot || 'N/A';
        let status = dados.status || 'N/A';
        let tokens = dados.tokens_hoje || 0;
        let time = dados.timestamp || 'N/A';

        document.getElementById("status").innerHTML = 
            "> Bot........: " + bot + "<br>" +
            "> Status.....: " + status + "<br>" +
            "> Tokens hoje: " + tokens + "<br>" +
            "> Atualizado.: " + time;
            
    } catch (erro) {
        document.getElementById("status").innerHTML = "> Erro ao carregar status.";
    }

    // Atualiza Logs Coloridos
    try {
        let resLogs = await fetch("/api/logs");
        let dadosLogs = await resLogs.json();
        let divLogs = document.getElementById("logs");

        if (dadosLogs.logs && Array.isArray(dadosLogs.logs)) {
            let htmlLogs = "";
            
            // Loop passando por cada log individualmente para definir sua cor
            for (let i = 0; i < dadosLogs.logs.length; i++) {
                let linha = dadosLogs.logs[i];
                let cor = "#ccc"; // Cinza padrão
                
                if (linha.indexOf("[ERROR]") !== -1) cor = "#f00";
                else if (linha.indexOf("[AGENT]") !== -1) cor = "#0ff";
                else if (linha.indexOf("[MEMORY]") !== -1) cor = "#ff0";

                htmlLogs += "<span style='color: " + cor + ";'>" + linha + "</span><br>";
            }
            
            // Injeta o HTML em vez de Texto simples para as tags de cor funcionarem
            divLogs.innerHTML = htmlLogs;
        } else {
            divLogs.innerHTML = "Nenhum log no momento.";
        }

        // Auto-scroll
        divLogs.scrollTop = divLogs.scrollHeight;
    } catch (erro) {
        document.getElementById("logs").innerHTML = "> Erro de conexao com /api/logs.";
    }
}

// Continua atualizando a interface
setInterval(atualizar, 2000);
atualizar();
</script>

</body>
</html>
"""


@app_flask.route("/")
def home():
    return render_template_string(HTML)


@app_flask.route("/api/status")
def api_status():
    return jsonify({
        "bot": "Tédio AI Discord Agent",
        "status": "online",
        "tokens_hoje": LogManager.tokens_hoje,
        "requisicoes": LogManager.requisicoes_hoje,
        "timestamp": datetime.now().isoformat()
    })


@app_flask.route("/api/logs")
def api_logs():
    return jsonify({
        "logs": LogManager.obter_logs(50)
    })


def _rodar():
    app_flask.run(
        host="0.0.0.0",
        port=ConfigManager.PORTA_FLASK
    )


def iniciar_servidor_web():
    Thread(
        target=_rodar,
        daemon=True
    ).start()

    LogManager.log(
        f"Servidor Flask ativo na porta {ConfigManager.PORTA_FLASK}.",
        "FLASK"
    )