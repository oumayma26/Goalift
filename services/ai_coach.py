"""
services/ai_coach.py
Service de coach IA via Ollama (local, 100% offline).
Sans dependance externe — utilise urllib (inclus dans Python).
"""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass
from datetime import datetime


OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:1b"


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AICoachService:
    """
    Service coach IA via Ollama.
    Gere les conversations, la generation de plans, l'analyse SMART.
    """

    SYSTEM_PROMPT = """Tu es GoalCoach, un coach productivite expert et bienveillant.
Tu aides l'utilisateur a atteindre ses objectifs en :
- Decomposant les objectifs complexes en etapes concretes
- Motivant et encourageant (jamais jugement)
- Proposant des habitudes adaptees
- Analysant les obstacles et proposant des solutions
- Reformulant les objectifs vagues en objectifs SMART

Reponds de maniere concise (max 3-4 phrases sauf si plan detaille demande).
Utilise des emojis pour rendre tes reponses engageantes.
Si l'utilisateur parle en arabe, reponds en arabe.
"""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self._history: List[ChatMessage] = []
        self._add_system_message()

    def _add_system_message(self):
        self._history.append(ChatMessage(role="system", content=self.SYSTEM_PROMPT))

    def _build_messages(self) -> List[Dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self._history]

    def _post_json(self, endpoint: str, data: dict, timeout: int = 60) -> dict:
        """Envoie une requete POST JSON a Ollama."""
        url = f"{OLLAMA_URL}{endpoint}"
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError:
            raise ConnectionError("Ollama n'est pas demarre")
        except urllib.error.HTTPError as e:
            raise Exception(f"Erreur HTTP {e.code}: {e.reason}")

    def is_available(self) -> bool:
        """Verifie si Ollama est demarre."""
        try:
            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.status == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """Liste les modeles disponibles localement."""
        try:
            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def chat(self, message: str) -> str:
        """Envoie un message et retourne la reponse complete."""
        self._history.append(ChatMessage(role="user", content=message))

        try:
            data = self._post_json("/api/chat", {
                "model": self.model,
                "messages": self._build_messages(),
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 500,
                }
            })
            reply = data.get("message", {}).get("content", "Desole, je n'ai pas pu generer de reponse.")
            self._history.append(ChatMessage(role="assistant", content=reply))
            return reply

        except ConnectionError:
            return "Ollama n'est pas demarre. Lance-le avec : `ollama run llama3.2:1b`"
        except Exception as e:
            return f"Erreur : {str(e)}"

    def chat_stream(self, message: str) -> Generator[str, None, None]:
        """Envoie un message et yield la reponse token par token."""
        self._history.append(ChatMessage(role="user", content=message))

        url = f"{OLLAMA_URL}/api/chat"
        payload = json.dumps({
            "model": self.model,
            "messages": self._build_messages(),
            "stream": True,
            "options": {
                "temperature": 0.7,
                "num_predict": 500,
            }
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            full_reply = ""
            with urllib.request.urlopen(req, timeout=60) as response:
                for line in response:
                    line = line.decode("utf-8").strip()
                    if line:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            full_reply += chunk
                            yield chunk

            self._history.append(ChatMessage(role="assistant", content=full_reply))

        except urllib.error.URLError:
            yield "Ollama n'est pas demarre.\n\nLance-le avec : `ollama run llama3.2:1b`"
        except Exception as e:
            yield f"Erreur : {str(e)}"

    def generate_smart_goal(self, raw_goal: str, deadline: Optional[str] = None) -> Dict[str, str]:
        """Transforme un objectif vague en objectif SMART + plan d'action."""
        prompt = f"""Transforme cet objectif en format SMART et propose un plan d'action.

Objectif de l'utilisateur : {raw_goal}
{"Deadline : " + deadline if deadline else ""}

Reponds UNIQUEMENT en JSON valide avec cette structure exacte :
{{
    "title": "titre SMART court",
    "description": "description detaillee",
    "specific": "comment est-il specifique ?",
    "measurable": "comment mesurer le progres ?",
    "achievable": "pourquoi est-il realiste ?",
    "relevant": "pourquoi est-il important ?",
    "time_bound": "quelle est la deadline ?",
    "tasks": ["tache 1", "tache 2", "tache 3"],
    "habits": ["habitude 1", "habitude 2"],
    "color": "#3B82F6",
    "priority": "Moyenne"
}}

Ne mets AUCUN texte hors du JSON."""

        try:
            data = self._post_json("/api/generate", {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.3,
                    "num_predict": 800,
                }
            })
            raw_json = data.get("response", "{}")
            return json.loads(raw_json)

        except Exception as e:
            return {
                "title": raw_goal,
                "description": "",
                "tasks": [],
                "habits": [],
                "error": str(e)
            }

    def generate_tasks_from_goal(self, goal_title: str, goal_desc: str = "", count: int = 5) -> List[str]:
        """Genere une liste de taches a partir d'un objectif."""
        prompt = f"""Decompose cet objectif en {count} taches concretes et actionnables.

Objectif : {goal_title}
Description : {goal_desc}

Reponds UNIQUEMENT une liste de taches, une par ligne, sans numerotation, sans texte introductif."""

        try:
            data = self._post_json("/api/generate", {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.5,
                    "num_predict": 300,
                }
            })
            text = data.get("response", "")
            tasks = [t.strip("- ") for t in text.strip().split("\n") if t.strip()]
            return tasks[:count]

        except Exception:
            return []

    def analyze_journal(self, entries: List[str]) -> Dict[str, any]:
        """Analyse un journal quotidien et retourne des insights."""
        combined = "\n".join([f"- {e}" for e in entries[-7:]])

        prompt = f"""Analyse ces entrees de journal et donne des insights.

Entrees :
{combined}

Reponds en JSON :
{{
    "sentiment": "positif/neutre/negatif",
    "mood_score": 7,
    "themes": ["travail", "sante"],
    "obstacles": ["manque de temps"],
    "wins": ["progres note"],
    "suggestion": "conseil personnalise"
}}"""

        try:
            data = self._post_json("/api/generate", {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.4, "num_predict": 400}
            })
            return json.loads(data.get("response", "{}"))
        except Exception:
            return {"sentiment": "neutre", "suggestion": "Continue a tenir ton journal !"}

    def clear_history(self):
        """Reinitialise la conversation."""
        self._history = []
        self._add_system_message()

    def get_history(self) -> List[ChatMessage]:
        """Retourne l'historique (sans le system prompt)."""
        return [m for m in self._history if m.role != "system"]