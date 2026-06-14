"""
services.py
Couche de services contenant la logique métier de l'application.
Fait le pont entre les modèles et la base de données.
"""

from typing import Optional, List
from database import DatabaseManager
from models import Goal, Task


class GoalService:
    """
    Service de gestion des Goals et de leurs tâches associées.
    Implémente le pattern Façade pour simplifier l'accès aux données.
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db: DatabaseManager = db_manager

    # ───────────────────────────────────────────────
    # Gestion des Goals
    # ───────────────────────────────────────────────

    def create_goal(
        self,
        title: str,
        description: str = "",
        target_date: Optional[str] = None,
        priority: str = "Moyenne"
    ) -> Goal:
        """
        Crée un nouveau goal avec validation des données.
        """
        if not title or not title.strip():
            raise ValueError("Le titre du goal est obligatoire")

        goal_id = self.db.create_goal(
            title=title.strip(),
            description=description.strip(),
            target_date=target_date,
            priority=priority
        )
        row = self.db.get_goal_by_id(goal_id)
        return Goal.from_db_row(row)

    def get_goal(self, goal_id: int) -> Optional[Goal]:
        """Récupère un goal par ID."""
        row = self.db.get_goal_by_id(goal_id)
        return Goal.from_db_row(row) if row else None

    def list_goals(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Goal]:
        """
        Liste tous les goals avec filtres optionnels.
        """
        rows = self.db.get_all_goals(
            status_filter=status,
            priority_filter=priority,
            search_query=search
        )
        return [Goal.from_db_row(row) for row in rows]

    def update_goal(
        self,
        goal_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        target_date: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None
    ) -> Goal:
        """
        Met à jour un goal. Si le statut passe à 'Terminé', 
        met automatiquement toutes les tâches à 'Terminée'.
        """
        success = self.db.update_goal(
            goal_id=goal_id,
            title=title,
            description=description,
            target_date=target_date,
            priority=priority,
            status=status
        )
        if not success:
            raise ValueError(f"Goal {goal_id} non trouvé")

        # Si le goal est marqué comme terminé, terminer toutes les tâches
        if status == "Terminé":
            tasks = self.list_tasks(goal_id)
            for task in tasks:
                if not task.is_completed:
                    self.db.update_task(task.id, status="Terminée")

        row = self.db.get_goal_by_id(goal_id)
        return Goal.from_db_row(row)

    def delete_goal(self, goal_id: int) -> bool:
        """Supprime un goal et toutes ses tâches."""
        return self.db.delete_goal(goal_id)

    # ───────────────────────────────────────────────
    # Gestion des Tasks
    # ───────────────────────────────────────────────

    def create_task(
        self,
        goal_id: int,
        name: str,
        description: str = ""
    ) -> Task:
        """
        Crée une nouvelle tâche pour un goal.
        Met à jour le statut du goal à 'En cours' si nécessaire.
        """
        if not name or not name.strip():
            raise ValueError("Le nom de la tâche est obligatoire")

        # Vérifier que le goal existe
        goal = self.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} non trouvé")

        task_id = self.db.create_task(
            goal_id=goal_id,
            name=name.strip(),
            description=description.strip()
        )

        # Si le goal était 'Non commencé', le passer à 'En cours'
        if goal.status == "Non commencé":
            self.db.update_goal(goal_id, status="En cours")

        row = self.db.get_task_by_id(task_id)
        return Task.from_db_row(row)

    def get_task(self, task_id: int) -> Optional[Task]:
        """Récupère une tâche par ID."""
        row = self.db.get_task_by_id(task_id)
        return Task.from_db_row(row) if row else None

    def list_tasks(self, goal_id: int) -> List[Task]:
        """Liste toutes les tâches d'un goal."""
        rows = self.db.get_tasks_by_goal_id(goal_id)
        return [Task.from_db_row(row) for row in rows]

    def update_task(
        self,
        task_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> Task:
        """
        Met à jour une tâche. Met à jour le statut du goal parent si besoin.
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Tâche {task_id} non trouvée")

        # Si on marque la tâche comme terminée
        if status == "Terminée" and not task.is_completed:
            # Vérifier si c'était la dernière tâche non terminée
            progress = self.get_goal_progress(task.goal_id)
            if progress["completed_tasks"] + 1 >= progress["total_tasks"]:
                # Toutes les tâches sont terminées → Goal terminé
                self.db.update_goal(task.goal_id, status="Terminé")

        success = self.db.update_task(
            task_id=task_id,
            name=name,
            description=description,
            status=status
        )
        if not success:
            raise ValueError("Échec de la mise à jour")

        row = self.db.get_task_by_id(task_id)
        return Task.from_db_row(row)

    def delete_task(self, task_id: int) -> bool:
        """Supprime une tâche."""
        return self.db.delete_task(task_id)

    def complete_task(self, task_id: int) -> Task:
        """Marque une tâche comme terminée (shortcut)."""
        return self.update_task(task_id, status="Terminée")

    # ───────────────────────────────────────────────
    # Progression et Statistiques
    # ───────────────────────────────────────────────

    def get_goal_progress(self, goal_id: int) -> dict:
        """
        Calcule la progression d'un goal.
        Retourne : {total_tasks, completed_tasks, percentage}
        """
        return self.db.get_goal_progress(goal_id)

    def get_dashboard_stats(self) -> dict:
        """
        Récupère les statistiques globales pour le tableau de bord.
        """
        return self.db.get_dashboard_stats()