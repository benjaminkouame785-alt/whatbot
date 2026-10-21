# WA-SHELL — Bot WhatsApp pour exécuter des commandes Linux à distance

Envoie des commandes depuis WhatsApp et reçois la réponse dans la conversation. Le projet inclut un tableau de bord web.

> **Attention :** ce bot peut exécuter des commandes sur la machine où il tourne. Ne le rends pas accessible publiquement avant d'avoir configuré l'authentification, un mot de passe fort et HTTPS. N'ajoute jamais ton fichier `.env` au dépôt.

## Fichiers du projet

- `app.py` : serveur Flask et webhook Twilio
- `requirements.txt` : dépendances Python
- `templates/dashboard.html` : tableau de bord
- `.env.example` : modèle de configuration sans secrets

## Installation

Python 3.10+ recommandé.

```bash
python -m venv venv
# Windows :
venv\Scripts\activate
# Linux/macOS :
source venv/bin/activate

pip install -r requirements.txt
```

Copie `.env.example` vers `.env`, puis modifie les valeurs :
- `AUTHORIZED_NUMBERS` : ton numéro autorisé au format `whatsapp:+225...`
- `SECRET_PASSPHRASE` : un mot de passe long et unique
- `BOT_WORKDIR` : le dossier dans lequel les commandes seront exécutées
- `PORT` : port HTTP, 5000 par défaut

Lance ensuite :

```bash
python app.py
```

Le tableau de bord est disponible sur `http://localhost:5000/`. Le webhook Twilio est `/webhook`. Pour recevoir les messages, configure le WhatsApp Sandbox Twilio et une URL HTTPS publique pointant vers `/webhook`.

## Sécurité indispensable

- Configure un numéro autorisé et un mot de passe avant de lancer le bot.
- Utilise uniquement un environnement que tu possèdes ou que tu es autorisé à administrer.
- N'expose pas directement ce serveur sur Internet sans HTTPS et contrôles de sécurité supplémentaires.
- Les filtres de commandes interdites ne remplacent pas une liste stricte de commandes autorisées.
- Ne pousse jamais `.env`, des identifiants Twilio ou d'autres secrets sur GitHub.
