import logging
import json
from google import genai

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Tu es un agent spécialisé dans la détection d'anomalies logicielles.

On te fournit un message provenant d'un canal Slack d'entreprise (#sap).
Tu dois déterminer si ce message décrit une **anomalie logicielle** (bug, erreur, dysfonctionnement, problème technique, comportement inattendu d'un logiciel ou d'un système).

Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour :
{
  "is_anomaly": true/false,
  "confidence": 0.0 à 1.0,
  "title": "Titre court de l'anomalie (si anomalie, sinon null)",
  "summary": "Résumé structuré du problème (si anomalie, sinon null)",
  "severity": "critical" | "high" | "medium" | "low" | null
}

Critères pour qualifier une anomalie :
- Message d'erreur ou code d'erreur mentionné
- Comportement inattendu d'une application ou d'un système
- Données incorrectes, manquantes ou incohérentes
- Problème de performance (lenteur, timeout, crash)
- Régression par rapport au fonctionnement normal

NE PAS qualifier comme anomalie :
- Questions générales ou demandes d'information
- Discussions, salutations, messages sociaux
- Demandes de fonctionnalités nouvelles
- Messages de déploiement ou maintenance planifiée
"""


class AnomalyClassifier:
    """Uses Gemini to classify Slack messages as software anomalies or not."""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def classify(self, message_text: str, author: str) -> dict:
        """Classify a message and return structured result."""
        user_prompt = f"Auteur : {author}\nMessage : {message_text}"

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "max_output_tokens": 512,
                },
            )
            content = response.text
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(content)
            logger.info(
                "Classification: is_anomaly=%s, confidence=%.2f",
                result.get("is_anomaly"),
                result.get("confidence", 0),
            )
            return result
        except json.JSONDecodeError:
            logger.error("Failed to parse classifier response: %s", content)
            return {"is_anomaly": False, "confidence": 0, "title": None, "summary": None, "severity": None}
        except Exception as e:
            logger.error("Gemini API error: %s", e)
            return {"is_anomaly": False, "confidence": 0, "title": None, "summary": None, "severity": None}
