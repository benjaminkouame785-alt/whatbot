"""
WhatsApp Remote Command Bot
---------------------------
Permet d'exécuter des commandes Linux sur TON ordinateur en envoyant un
message WhatsApp, via l'API Twilio WhatsApp.

SECURITE (ne pas désactiver) :
  1. Seuls les numéros listés dans AUTHORIZED_NUMBERS peuvent envoyer des commandes.
  2. Chaque message doit commencer par le mot de passe secret (SECRET_PASSPHRASE).
  3. Une liste de commandes dangereuses est bloquée (BLOCKED_PATTERNS).
  4. Chaque commande a un timeout pour éviter qu'un process bloque le bot.
  5. Toutes les commandes et résultats sont journalisés (visibles sur le dashboard).

Lance ce fichier avec : python app.py
Puis expose-le sur internet (ngrok, ou un VPS) pour que Twilio puisse l'appeler.
"""

import os
import re
import time
import subprocess
import threading
from collections import deque
from datetime import datetime

from flask import Flask, request, render_template, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

AUTHORIZED_NUMBERS = set(
    n.strip() for n in os.environ.get("AUTHORIZED_NUMBERS", "").split(",") if n.strip()
)
SECRET_PASSPHRASE = os.environ.get("SECRET_PASSPHRASE", "")
WORKDIR = os.environ.get("BOT_WORKDIR", os.path.expanduser("~"))
COMMAND_TIMEOUT = int(os.environ.get("COMMAND_TIMEOUT", "25"))
MAX_REPLY_LEN = 1500
LOG_HISTORY = deque(maxlen=200)
LOG_LOCK = threading.Lock()

BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/(\s|$)",
    r"rm\s+-rf\s+\*",
    r"mkfs",
    r":\(\)\s*\{.*:\|:.*\};",
    r"dd\s+if=.*of=/dev/",
    r">\s*/dev/sd",
    r"shutdown",
    r"\breboot\b",
    r"\bpoweroff\b",
    r"\bhalt\b",
    r"chmod\s+-R\s+777\s+/",
    r"\bpasswd\b",
    r"\bmkpasswd\b",
]
BLOCKED_RE = re.compile("|".join(BLOCKED_PATTERNS), re.IGNORECASE)


def log_event(kind, sender, text):
    with LOG_LOCK:
        LOG_HISTORY.appendleft({
            "time": datetime.now().strftime("%H:%M:%S"),
            "kind": kind,
            "sender": sender,
            "text": text,
        })


def is_blocked(command: str) -> bool:
    return bool(BLOCKED_RE.search(command))


def run_command(command: str) -> str:
    """Exécute une commande shell et retourne stdout+stderr tronqués."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
        )
        output = (result.stdout or "") + (result.stderr or "")
        output = output.strip() or f"(aucune sortie, code retour {result.returncode})"
    except subprocess.TimeoutExpired:
        output = f"⏱️ Timeout dépassé ({COMMAND_TIMEOUT}s), commande interrompue."
    except Exception as e:
        output = f"Erreur d'exécution : {e}"

    if len(output) > MAX_REPLY_LEN:
        output = output[:MAX_REPLY_LEN] + "\n…(sortie tronquée)"
    return output


@app.route("/webhook", methods=["POST"])
def webhook():
    sender = request.values.get("From", "")
    body = request.values.get("Body", "").strip()
    resp = MessagingResponse()

    if sender not in AUTHORIZED_NUMBERS:
        log_event("denied", sender, body)
        resp.message("⛔ Numéro non autorisé.")
        return str(resp)

    if SECRET_PASSPHRASE:
        prefix = SECRET_PASSPHRASE + " "
        if not body.startswith(prefix):
            log_event("denied", sender, "(mot de passe manquant/incorrect)")
            resp.message("🔒 Format attendu : <mot_de_passe> <commande>")
            return str(resp)
        command = body[len(prefix):].strip()
    else:
        command = body

    if not command:
        resp.message("Commande vide.")
        return str(resp)

    log_event("in", sender, command)

    if is_blocked(command):
        log_event("blocked", sender, command)
        resp.message("🚫 Commande bloquée pour raisons de sécurité.")
        return str(resp)

    output = run_command(command)
    log_event("out", sender, output)
    resp.message(f"$ {command}\n\n{output}")
    return str(resp)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/logs")
def api_logs():
    with LOG_LOCK:
        return jsonify(list(LOG_HISTORY))


@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": time.time()})


if __name__ == "__main__":
    if not AUTHORIZED_NUMBERS:
        print("⚠️  Aucun numéro dans AUTHORIZED_NUMBERS : personne ne pourra utiliser le bot.")
    if not SECRET_PASSPHRASE:
        print("⚠️  Aucun SECRET_PASSPHRASE défini : c'est fortement déconseillé.")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
