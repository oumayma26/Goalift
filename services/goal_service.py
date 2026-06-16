"""
services.py
Couche métier avec tri par progression, filtre terminés et images.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from database import DatabaseManager
from models.goal import Goal, Task


class GoalService:
    """
    Service de gestion des Goals et de leurs tâches associées.
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db: DatabaseManager = db_manager

    def create_goal(
        self,
        title: str,
        description: str = "",
        target_date: Optional[str] = None,
        priority: str = "Moyenne",
        color: str = "#3B82F6",
        image_path: Optional[str] = None
    ) -> Goal:
        """Crée un nouveau goal."""
        if not title or not title.strip():
            raise ValueError("Le titre du goal est obligatoire")

        goal_id = self.db.create_goal(
            title=title.strip(),
            description=description.strip(),
            target_date=target_date,
            priority=priority,
            color=color,
            image_path=image_path
        )
        print(f"Goal créé avec ID {goal_id}")
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
        search: Optional[str] = None,
        exclude_status: Optional[str] = None
    ) -> List[Goal]:
        """
        Liste les goals avec filtres.
        Le tri par progression est fait par l'appelant (main_window.py).
        """
        rows = self.db.get_all_goals(
            status_filter=status,
            exclude_status=exclude_status,
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
        status: Optional[str] = None,
        color: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> Goal:
        """Met à jour un goal."""
        success = self.db.update_goal(
            goal_id=goal_id,
            title=title,
            description=description,
            target_date=target_date,
            priority=priority,
            status=status,
            color=color,
            image_path=image_path
        )
        if not success:
            raise ValueError(f"Goal {goal_id} non trouvé")

        if status == "Terminé":
            tasks = self.list_tasks(goal_id)
            for task in tasks:
                if not task.is_completed:
                    self.db.update_task(task.id, status="Terminée")

        row = self.db.get_goal_by_id(goal_id)
        return Goal.from_db_row(row)

    def delete_goal(self, goal_id: int) -> bool:
        """Supprime un goal et son image."""
        goal = self.get_goal(goal_id)
        if goal and goal.image_path:
            self.delete_goal_image(goal.image_path)
        return self.db.delete_goal(goal_id)

    def create_task(
        self,
        goal_id: int,
        name: str,
        description: str = ""
    ) -> Task:
        """Crée une tâche."""
        if not name or not name.strip():
            raise ValueError("Le nom de la tâche est obligatoire")

        goal = self.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} non trouvé")

        task_id = self.db.create_task(
            goal_id=goal_id,
            name=name.strip(),
            description=description.strip()
        )

        if goal.status == "Non commencé":
            self.db.update_goal(goal_id, status="En cours")

        row = self.db.get_task_by_id(task_id)
        return Task.from_db_row(row)

    def get_task(self, task_id: int) -> Optional[Task]:
        """Récupère une tâche."""
        row = self.db.get_task_by_id(task_id)
        return Task.from_db_row(row) if row else None

    def list_tasks(self, goal_id: int) -> List[Task]:
        """Liste les tâches d'un goal."""
        rows = self.db.get_tasks_by_goal_id(goal_id)
        return [Task.from_db_row(row) for row in rows]

    def update_task(
        self,
        task_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> Task:
        """Met à jour une tâche."""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Tâche {task_id} non trouvée")

        if status == "Terminée" and not task.is_completed:
            progress = self.get_goal_progress(task.goal_id)
            if progress["completed_tasks"] + 1 >= progress["total_tasks"]:
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
        """Marque une tâche comme terminée."""
        return self.update_task(task_id, status="Terminée")

    def get_goal_progress(self, goal_id: int) -> dict:
        """Progression d'un goal."""
        return self.db.get_goal_progress(goal_id)

    def get_dashboard_stats(self) -> dict:
        """Stats globales."""
        return self.db.get_dashboard_stats()

    def get_yearly_stats(self) -> dict:
        """Stats annuelles."""
        current_year = datetime.now().year
        return self.db.get_goals_by_year(current_year)

    def get_monthly_stats(self) -> dict:
        """Stats mensuelles."""
        now = datetime.now()
        return self.db.get_goals_by_month(now.year, now.month)

    def get_daily_progress_30_days(self) -> list[dict]:
        """Progression 30 jours."""
        return self.db.get_daily_progress_last_30_days()

    def get_status_distribution(self) -> dict:
        """Répartition par statut."""
        return self.db.get_goals_distribution_by_status()

    # ───────────────────────────────────────────────
    # GESTION DES IMAGES
    # ───────────────────────────────────────────────

    def save_goal_image(self, goal_id: int, source_path: str) -> str:
        """
        Copie l'image dans le dossier assets et retourne le chemin relatif.
        """
        if not source_path or not os.path.exists(source_path):
            return None

        assets_dir = Path("assets/goals")
        assets_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(source_path).suffix
        filename = f"goal_{goal_id}{ext}"
        dest_path = assets_dir / filename

        shutil.copy2(source_path, dest_path)

        return str(dest_path)

    def delete_goal_image(self, image_path: str) -> None:
        """Supprime l'image du disque."""
        if image_path and os.path.exists(image_path):
            os.remove(image_path)