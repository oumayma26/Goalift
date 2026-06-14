"""
models.py
Modèles de données représentant les entités Goals et Tasks.
Utilise des dataclasses pour un code propre et typé.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Goal:
    """
    Représente un objectif personnel.
    """
    id: int
    title: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    target_date: Optional[datetime] = None
    priority: str = "Moyenne"  # Faible, Moyenne, Haute
    status: str = "Non commencé"  # Non commencé, En cours, Terminé

    # Constantes pour validation
    VALID_PRIORITIES = {"Faible", "Moyenne", "Haute"}
    VALID_STATUSES = {"Non commencé", "En cours", "Terminé"}

    def __post_init__(self):
        """Validation post-instanciation."""
        if self.priority not in self.VALID_PRIORITIES:
            raise ValueError(f"Priorité invalide : {self.priority}")
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Statut invalide : {self.status}")

    @property
    def is_completed(self) -> bool:
        """Vérifie si le goal est terminé."""
        return self.status == "Terminé"

    @property
    def is_overdue(self) -> bool:
        """Vérifie si le goal a dépassé sa date cible."""
        if self.target_date is None:
            return False
        return datetime.now() > self.target_date and not self.is_completed

    @classmethod
    def from_db_row(cls, row) -> "Goal":
        """Crée un Goal à partir d'une ligne SQLite."""
        return cls(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            target_date=datetime.fromisoformat(row["target_date"]) if row["target_date"] else None,
            priority=row["priority"],
            status=row["status"]
        )

    def to_dict(self) -> dict:
        """Sérialise le goal en dictionnaire."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "priority": self.priority,
            "status": self.status
        }


@dataclass
class Task:
    """
    Représente une tâche associée à un Goal.
    """
    id: int
    goal_id: int
    name: str
    description: str = ""
    status: str = "À faire"  # À faire, En cours, Terminée
    created_at: datetime = field(default_factory=datetime.now)

    VALID_STATUSES = {"À faire", "En cours", "Terminée"}

    def __post_init__(self):
        """Validation post-instanciation."""
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Statut de tâche invalide : {self.status}")

    @property
    def is_completed(self) -> bool:
        """Vérifie si la tâche est terminée."""
        return self.status == "Terminée"

    @classmethod
    def from_db_row(cls, row) -> "Task":
        """Crée une Task à partir d'une ligne SQLite."""
        return cls(
            id=row["id"],
            goal_id=row["goal_id"],
            name=row["name"],
            description=row["description"] or "",
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

    def to_dict(self) -> dict:
        """Sérialise la tâche en dictionnaire."""
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }