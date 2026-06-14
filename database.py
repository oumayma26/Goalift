"""
database.py
Couche d'accès aux données SQLite avec gestion des connexions et schéma.
"""

import sqlite3
import os
from typing import Optional
from contextlib import contextmanager
from datetime import datetime


class DatabaseManager:
    """
    Gestionnaire singleton de la base de données SQLite.
    Gère la connexion, la création du schéma et les transactions.
    """

    def __init__(self, db_path: str = "database.db") -> None:
        self.db_path: str = db_path
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """
        Context manager pour gérer les connexions SQLite de manière sûre.
        Active le mode WAL pour de meilleures performances en lecture/écriture.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permet l'accès par nom de colonne
        conn.execute("PRAGMA foreign_keys = ON")  # Active les clés étrangères
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Initialise le schéma de la base de données si elle n'existe pas."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Table des Goals
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    target_date TEXT,
                    priority TEXT NOT NULL DEFAULT 'Moyenne' 
                        CHECK(priority IN ('Faible', 'Moyenne', 'Haute')),
                    status TEXT NOT NULL DEFAULT 'Non commencé'
                        CHECK(status IN ('Non commencé', 'En cours', 'Terminé')),
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table des Tasks (tâches associées à un Goal)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'À faire'
                        CHECK(status IN ('À faire', 'En cours', 'Terminée')),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
                )
            """)

            # Index pour optimiser les recherches
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_goal_id ON tasks(goal_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority)
            """)

            conn.commit()
            print(f"✅ Base de données initialisée : {self.db_path}")

    # ───────────────────────────────────────────────
    # Opérations CRUD pour les Goals
    # ───────────────────────────────────────────────

    def create_goal(
        self,
        title: str,
        description: str = "",
        target_date: Optional[str] = None,
        priority: str = "Moyenne",
        status: str = "Non commencé"
    ) -> int:
        """Crée un nouveau goal et retourne son ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO goals (title, description, target_date, priority, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, description, target_date, priority, status, now, now))
            return cursor.lastrowid

    def get_goal_by_id(self, goal_id: int) -> Optional[sqlite3.Row]:
        """Récupère un goal par son ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
            return cursor.fetchone()

    def get_all_goals(
        self,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> list[sqlite3.Row]:
        """
        Récupère tous les goals avec filtres optionnels.
        Supporte le filtrage par statut, priorité et recherche textuelle.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM goals WHERE 1=1"
            params: list = []

            if status_filter:
                query += " AND status = ?"
                params.append(status_filter)
            if priority_filter:
                query += " AND priority = ?"
                params.append(priority_filter)
            if search_query:
                query += " AND (title LIKE ? OR description LIKE ?)"
                params.extend([f"%{search_query}%", f"%{search_query}%"])

            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)
            return cursor.fetchall()

    def update_goal(
        self,
        goal_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        target_date: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None
    ) -> bool:
        """Met à jour un goal existant. Ne modifie que les champs fournis."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []

            if title is not None:
                updates.append("title = ?")
                params.append(title)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if target_date is not None:
                updates.append("target_date = ?")
                params.append(target_date)
            if priority is not None:
                updates.append("priority = ?")
                params.append(priority)
            if status is not None:
                updates.append("status = ?")
                params.append(status)

            if not updates:
                return False

            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(goal_id)

            query = f"UPDATE goals SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            return cursor.rowcount > 0

    def delete_goal(self, goal_id: int) -> bool:
        """Supprime un goal et toutes ses tâches associées (CASCADE)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
            return cursor.rowcount > 0

    # ───────────────────────────────────────────────
    # Opérations CRUD pour les Tasks
    # ───────────────────────────────────────────────

    def create_task(
        self,
        goal_id: int,
        name: str,
        description: str = "",
        status: str = "À faire"
    ) -> int:
        """Crée une nouvelle tâche associée à un goal."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO tasks (goal_id, name, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (goal_id, name, description, status, now, now))
            return cursor.lastrowid

    def get_task_by_id(self, task_id: int) -> Optional[sqlite3.Row]:
        """Récupère une tâche par son ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            return cursor.fetchone()

    def get_tasks_by_goal_id(self, goal_id: int) -> list[sqlite3.Row]:
        """Récupère toutes les tâches d'un goal spécifique."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tasks WHERE goal_id = ? ORDER BY created_at",
                (goal_id,)
            )
            return cursor.fetchall()

    def update_task(
        self,
        task_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> bool:
        """Met à jour une tâche existante."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if status is not None:
                updates.append("status = ?")
                params.append(status)

            if not updates:
                return False

            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(task_id)

            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        """Supprime une tâche."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0

    # ───────────────────────────────────────────────
    # Statistiques et Dashboard
    # ───────────────────────────────────────────────

    def get_dashboard_stats(self) -> dict:
        """
        Calcule les statistiques globales pour le tableau de bord.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Nombre total de goals
            cursor.execute("SELECT COUNT(*) FROM goals")
            total_goals = cursor.fetchone()[0]

            # Goals par statut
            cursor.execute(
                "SELECT status, COUNT(*) FROM goals GROUP BY status"
            )
            goals_by_status = {row[0]: row[1] for row in cursor.fetchall()}

            # Nombre total de tâches
            cursor.execute("SELECT COUNT(*) FROM tasks")
            total_tasks = cursor.fetchone()[0]

            # Tâches terminées
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Terminée'")
            completed_tasks = cursor.fetchone()[0]

            # Progression globale
            global_progress = 0
            if total_tasks > 0:
                global_progress = round((completed_tasks / total_tasks) * 100, 1)

            return {
                "total_goals": total_goals,
                "goals_completed": goals_by_status.get("Terminé", 0),
                "goals_in_progress": goals_by_status.get("En cours", 0),
                "goals_not_started": goals_by_status.get("Non commencé", 0),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "global_progress": global_progress
            }

    def get_goal_progress(self, goal_id: int) -> dict:
        """
        Calcule la progression d'un goal spécifique.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM tasks WHERE goal_id = ?",
                (goal_id,)
            )
            total = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM tasks WHERE goal_id = ? AND status = 'Terminée'",
                (goal_id,)
            )
            completed = cursor.fetchone()[0]

            percentage = 0
            if total > 0:
                percentage = round((completed / total) * 100, 1)

            return {
                "total_tasks": total,
                "completed_tasks": completed,
                "percentage": percentage
            }