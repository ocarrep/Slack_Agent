# Slack Anomaly Agent

Agent IA qui surveille le canal Slack **#sap** et crée automatiquement des tickets d'anomalie dans Jira (projet **HELP**) lorsqu'un message décrit un bug ou un dysfonctionnement logiciel.

## Architecture

```
Slack (#sap) → Agent (polling) → Claude (classification) → Jira (ticket Anomalie)
```

### Modules

| Module | Rôle |
|--------|------|
| `src/slack_monitor.py` | Poll le canal Slack et récupère les nouveaux messages |
| `src/classifier.py` | Utilise Claude pour classifier si un message est une anomalie |
| `src/jira_client.py` | Crée un ticket de type "Anomalie" dans le projet HELP |
| `src/agent.py` | Orchestrateur principal qui relie les trois modules |

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copier `.env.example` vers `.env` et remplir les valeurs :

```bash
cp .env.example .env
```

Variables requises :
- `SLACK_BOT_TOKEN` : Token du bot Slack (scopes: `channels:history`, `users:read`)
- `JIRA_EMAIL` / `JIRA_API_TOKEN` : Identifiants API Jira Cloud
- `ANTHROPIC_API_KEY` : Clé API Anthropic (Claude)

## Utilisation

```bash
python main.py
```

L'agent va :
1. Surveiller le canal #sap toutes les 60 secondes (configurable)
2. Analyser chaque nouveau message avec Claude
3. Si le message est classé comme anomalie (confiance > 70%), créer un ticket Jira

## Classification

Claude évalue chaque message selon ces critères :
- **Anomalie** : message d'erreur, comportement inattendu, données incorrectes, crash, timeout
- **Pas une anomalie** : question, discussion, demande de fonctionnalité, maintenance planifiée

Le ticket Jira créé contient : titre, résumé IA, sévérité estimée, message original et auteur.
