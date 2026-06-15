"""
models/goal.py
Modèles Goal et Task - basés sur le fichier original de l'utilisateur.
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Goal:
    """Représente un objectif personnel."""
    id: int
    title: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    target_date: Optional[datetime] = None
    priority: str = "Moyenne"
    status: str = "Non commencé"
    color: str = "#3B82F6"
    image_path: Optional[str] = None

    VALID_PRIORITIES = {"Faible", "Moyenne", "Haute"}
    VALID_STATUSES = {"Non commencé", "En cours", "Terminé"}

    def __post_init__(self):
        if self.priority not in self.VALID_PRIORITIES:
            raise ValueError(f"Priorité invalide : {self.priority}")
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Statut invalide : {self.status}")

    @property
    def is_completed(self) -> bool:
        return self.status == "Terminé"

    @property
    def is_overdue(self) -> bool:
        if self.target_date is None:
            return False
        return datetime.now() > self.target_date and not self.is_completed

    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> "Goal":
        """Crée un Goal à partir d'une ligne SQLite."""
        return cls(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            target_date=datetime.fromisoformat(row["target_date"]) if row["target_date"] else None,
            priority=row["priority"],
            status=row["status"],
            color=row["color"] if row["color"] else "#3B82F6",
            image_path=row["image_path"] if row["image_path"] else None
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "priority": self.priority,
            "status": self.status,
            "color": self.color,
            "image_path": self.image_path
        }


@dataclass
class Task:
    """Représente une tâche associée à un Goal."""
    id: int
    goal_id: int
    name: str
    description: str = ""
    status: str = "À faire"
    created_at: datetime = field(default_factory=datetime.now)

    VALID_STATUSES = {"À faire", "En cours", "Terminée"}

    def __post_init__(self):
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Statut de tâche invalide : {self.status}")

    @property
    def is_completed(self) -> bool:
        return self.status == "Terminée"

    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> "Task":
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
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }
