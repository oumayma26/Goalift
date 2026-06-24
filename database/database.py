"""
database.py
Couche d'accès aux données SQLite.
"""

import sqlite3
import os
import sys
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from datetime import datetime, timedelta
from utils.paths import get_db_path



class DatabaseManager:
    """
    Gestionnaire singleton de la base de données SQLite.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = os.path.join(get_db_path(), "database.db")
        
        # Chemin absolu normalisé
        self.db_path: str = str(Path(db_path).resolve())
        
        # Création du dossier parent
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[DatabaseManager] DB path: {self.db_path}")
        print(f"[DatabaseManager] DB dir: {db_dir}")
        print(f"[DatabaseManager] DB dir exists: {db_dir.exists()}")
        
        self._init_database()

    @contextmanager
    def _get_connection(self):
        print(f"[DatabaseManager] Connecting to: {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Initialise le schéma de la base de données."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # ─── TABLES PRINCIPALES ───
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
                    color TEXT DEFAULT '#3B82F6',
                    image_path TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vision_board (
                    goal_id INTEGER PRIMARY KEY,
                    motivation_text TEXT DEFAULT '',
                    pos_x REAL DEFAULT 0,
                    pos_y REAL DEFAULT 0,
                    width INTEGER DEFAULT 300,
                    height INTEGER DEFAULT 220,
                    font_size INTEGER DEFAULT 13,
                    text_position TEXT DEFAULT 'bottom',
                    text_color TEXT DEFAULT '#FFFFFF',
                    text_bold INTEGER DEFAULT 1,
                    celebrated INTEGER DEFAULT 0,
                    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vision_board_texts (
                    id INTEGER PRIMARY KEY,
                    text TEXT NOT NULL,
                    x REAL DEFAULT 100,
                    y REAL DEFAULT 100,
                    font_family TEXT DEFAULT 'Arial',
                    font_size INTEGER DEFAULT 16,
                    bold INTEGER DEFAULT 0,
                    italic INTEGER DEFAULT 0,
                    color TEXT DEFAULT '#1E293B',
                    background TEXT,
                    opacity INTEGER DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vision_board_mood (
                    id INTEGER PRIMARY KEY,
                    image_path TEXT NOT NULL,
                    title TEXT DEFAULT '',
                    x REAL DEFAULT 100,
                    y REAL DEFAULT 100,
                    width REAL DEFAULT 280,
                    height REAL DEFAULT 190,
                    color TEXT DEFAULT '#3B82F6',
                    rotation REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # ─── INDEXES ───
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_goal_id ON tasks(goal_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_goals_created_at ON goals(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at)
            """)

            # ─── MIGRATION : colonnes color et image_path ───
            try:
                cursor.execute("SELECT color FROM goals LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE goals ADD COLUMN color TEXT DEFAULT '#3B82F6'")
                cursor.execute("ALTER TABLE goals ADD COLUMN image_path TEXT")

            # ─── HABITS ───
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    goal_id INTEGER REFERENCES goals(id) ON DELETE SET NULL,
                    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
                    frequency TEXT DEFAULT 'daily' 
                        CHECK(frequency IN ('daily', 'weekly', 'custom')),
                    target_days TEXT,
                    color TEXT DEFAULT '#3B82F6',
                    icon TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    archived_at TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS habit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
                    log_date TEXT NOT NULL,
                    status TEXT NOT NULL
                        CHECK(status IN ('done', 'missed', 'partial')),
                    note TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(habit_id, log_date)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_habits_task ON habits(task_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_habit_logs_date ON habit_logs(habit_id, log_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_habits_goal ON habits(goal_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_habits_archived ON habits(archived_at)
            """)

            # ─── WIRD ───
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wirds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    icon TEXT DEFAULT '📿',
                    color TEXT DEFAULT '#3B82F6',
                    schedule_type TEXT DEFAULT 'daily'
                        CHECK(schedule_type IN ('daily', 'fajr', 'dhuhr', 'asr', 'maghrib', 'isha', 'custom')),
                    target_days TEXT,
                    is_template INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    archived_at TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wird_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wird_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    icon TEXT DEFAULT '✨',
                    target_count INTEGER DEFAULT 1,
                    unit TEXT DEFAULT 'fois',
                    duration_seconds INTEGER,
                    order_index INTEGER DEFAULT 0,
                    is_optional INTEGER DEFAULT 0,
                    FOREIGN KEY (wird_id) REFERENCES wirds(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wird_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wird_id INTEGER NOT NULL,
                    session_date TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    total_duration_seconds INTEGER DEFAULT 0,
                    items_completed INTEGER DEFAULT 0,
                    items_total INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'in_progress'
                        CHECK(status IN ('in_progress', 'completed', 'abandoned')),
                    mood_after INTEGER,
                    note TEXT,
                    FOREIGN KEY (wird_id) REFERENCES wirds(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wird_session_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    completed_at TEXT,
                    actual_count INTEGER DEFAULT 1,
                    duration_seconds INTEGER,
                    status TEXT DEFAULT 'completed'
                        CHECK(status IN ('completed', 'skipped', 'partial')),
                    note TEXT,
                    FOREIGN KEY (session_id) REFERENCES wird_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (item_id) REFERENCES wird_items(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wirds_active ON wirds(is_active, archived_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wird_items_wird ON wird_items(wird_id, order_index)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wird_sessions_date ON wird_sessions(wird_id, session_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wird_session_logs ON wird_session_logs(session_id, item_id)")

            print(f"✅ Base de données initialisée : {self.db_path}")

    def create_goal(
        self,
        title: str,
        description: str = "",
        target_date: Optional[str] = None,
        priority: str = "Moyenne",
        status: str = "Non commencé",
        color: str = "#3B82F6",
        image_path: Optional[str] = None
    ) -> int:
        """Crée un nouveau goal et retourne son ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO goals (title, description, target_date, priority, status, color, image_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, description, target_date, priority, status, color, image_path, now, now))
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
        search_query: Optional[str] = None,
        exclude_status: Optional[str] = None
    ) -> list[sqlite3.Row]:
        """
        Récupère tous les goals avec filtres optionnels.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM goals WHERE 1=1"
            params: list = []

            if status_filter:
                query += " AND status = ?"
                params.append(status_filter)
            if exclude_status:
                query += " AND status != ?"
                params.append(exclude_status)
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
        status: Optional[str] = None,
        color: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> bool:
        """Met à jour un goal existant."""
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
            if color is not None:
                updates.append("color = ?")
                params.append(color)
            if image_path is not None:
                updates.append("image_path = ?")
                params.append(image_path)

            if not updates:
                return False

            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(goal_id)

            query = f"UPDATE goals SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            return cursor.rowcount > 0

    def delete_goal(self, goal_id: int) -> bool:
        """Supprime un goal et toutes ses tâches associées."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
            return cursor.rowcount > 0

    def create_task(
        self,
        goal_id: int,
        name: str,
        description: str = "",
        status: str = "À faire"
    ) -> int:
        """Crée une nouvelle tâche."""
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
        """Récupère toutes les tâches d'un goal."""
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
        """Met à jour une tâche."""
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

    def get_dashboard_stats(self) -> dict:
        """Statistiques globales."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM goals")
            total_goals = cursor.fetchone()[0]

            cursor.execute("SELECT status, COUNT(*) FROM goals GROUP BY status")
            goals_by_status = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT COUNT(*) FROM tasks")
            total_tasks = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Terminée'")
            completed_tasks = cursor.fetchone()[0]

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
        """Progression d'un goal."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE goal_id = ?", (goal_id,))
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

    def get_goals_by_year(self, year: int) -> dict:
        """Stats goals pour une année."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            year_start = f"{year}-01-01T00:00:00"
            year_end = f"{year + 1}-01-01T00:00:00"

            cursor.execute("""
                SELECT COUNT(*) FROM goals 
                WHERE created_at >= ? AND created_at < ?
            """, (year_start, year_end))
            created = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM goals 
                WHERE status = 'Terminé' 
                AND updated_at >= ? AND updated_at < ?
            """, (year_start, year_end))
            completed = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM goals 
                WHERE status = 'En cours' 
                AND created_at >= ? AND created_at < ?
            """, (year_start, year_end))
            in_progress = cursor.fetchone()[0]

            return {
                "created": created,
                "completed": completed,
                "in_progress": in_progress
            }

    def get_goals_by_month(self, year: int, month: int) -> dict:
        """Stats goals pour un mois."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            month_start = f"{year}-{month:02d}-01T00:00:00"
            if month == 12:
                month_end = f"{year + 1}-01-01T00:00:00"
            else:
                month_end = f"{year}-{month + 1:02d}-01T00:00:00"

            cursor.execute("""
                SELECT COUNT(*) FROM goals 
                WHERE status = 'En cours' 
                AND created_at >= ? AND created_at < ?
            """, (month_start, month_end))
            in_progress = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM goals 
                WHERE created_at >= ? AND created_at < ?
            """, (month_start, month_end))
            created = cursor.fetchone()[0]

            return {
                "in_progress": in_progress,
                "created": created
            }

    def get_daily_progress_last_30_days(self) -> list[dict]:
        """Tâches terminées par jour sur 30 jours."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            end_date = datetime.now()
            start_date = end_date - timedelta(days=29)

            results = []
            for i in range(30):
                current = start_date + timedelta(days=i)
                day_start = current.replace(hour=0, minute=0, second=0).isoformat()
                day_end = current.replace(hour=23, minute=59, second=59).isoformat()

                cursor.execute("""
                    SELECT COUNT(*) FROM tasks 
                    WHERE status = 'Terminée' 
                    AND updated_at >= ? AND updated_at <= ?
                """, (day_start, day_end))
                count = cursor.fetchone()[0]

                results.append({
                    "date": current.strftime("%d/%m"),
                    "full_date": current.strftime("%Y-%m-%d"),
                    "completed_tasks": count
                })

            return results

    def get_goals_distribution_by_status(self) -> dict:
        """Répartition par statut."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM goals 
                GROUP BY status
            """)
            return {row[0]: row[1] for row in cursor.fetchall()}


    # ═══════════════════════════════════════════════════
    # HABITS
    # ═══════════════════════════════════════════════════

    def create_habit(
        self,
        title: str,
        description: Optional[str] = None,
        goal_id: Optional[int] = None,
        task_id: Optional[int] = None,
        frequency: str = "daily",
        target_days: Optional[str] = None,
        color: str = "#3B82F6",
        icon: Optional[str] = None
    ) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO habits (title, description, goal_id, task_id, frequency, target_days, color, icon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, description, goal_id, task_id, frequency, target_days, color, icon))
            return cursor.lastrowid

    def get_habit_by_id(self, habit_id: int) -> Optional[sqlite3.Row]:
        """Récupère une habitude par son ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM habits WHERE id = ?", (habit_id,))
            return cursor.fetchone()

    def get_all_habits(self, include_archived: bool = False) -> list[sqlite3.Row]:
        """Récupère toutes les habitudes actives."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if include_archived:
                cursor.execute("SELECT * FROM habits ORDER BY created_at DESC")
            else:
                cursor.execute("""
                    SELECT * FROM habits 
                    WHERE archived_at IS NULL 
                    ORDER BY created_at DESC
                """)
            return cursor.fetchall()

    def get_habits_by_goal_id(self, goal_id: int) -> list[sqlite3.Row]:
        """Habitudes liées à un goal."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM habits 
                WHERE goal_id = ? AND archived_at IS NULL
                ORDER BY created_at DESC
            """, (goal_id,))
            return cursor.fetchall()

    def update_habit(
        self,
        habit_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        goal_id: Optional[int] = None,
        task_id: Optional[int] = None,
        frequency: Optional[str] = None,
        target_days: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None
    ) -> bool:
        """Met à jour une habitude."""
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
            if goal_id is not None:
                updates.append("goal_id = ?")
                params.append(goal_id)

            if task_id is not None:
                updates.append("task_id = ?")
                params.append(task_id)
            if frequency is not None:
                updates.append("frequency = ?")
                params.append(frequency)
            if target_days is not None:
                updates.append("target_days = ?")
                params.append(target_days)
            if color is not None:
                updates.append("color = ?")
                params.append(color)
            if icon is not None:
                updates.append("icon = ?")
                params.append(icon)

            if not updates:
                return False

            params.append(habit_id)
            query = f"UPDATE habits SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            return cursor.rowcount > 0

    def archive_habit(self, habit_id: int) -> bool:
        """Archive une habitude (soft delete)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "UPDATE habits SET archived_at = ? WHERE id = ?",
                (now, habit_id)
            )
            return cursor.rowcount > 0

    def delete_habit(self, habit_id: int) -> bool:
        """Supprime définitivement une habitude et ses logs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
            return cursor.rowcount > 0

    # ═══════════════════════════════════════════════════
    # HABIT LOGS
    # ═══════════════════════════════════════════════════

    def create_or_update_habit_log(
        self,
        habit_id: int,
        log_date: str,
        status: str,
        note: Optional[str] = None
    ) -> int:
        """Crée ou met à jour un log (upsert)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO habit_logs (habit_id, log_date, status, note)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(habit_id, log_date) DO UPDATE SET
                    status = excluded.status,
                    note = excluded.note
            """, (habit_id, log_date, status, note))
            return cursor.lastrowid

    def get_habit_logs(
        self,
        habit_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[sqlite3.Row]:
        """Récupère les logs d'une habitude, optionnellement filtrés par date."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM habit_logs WHERE habit_id = ?"
            params = [habit_id]

            if start_date:
                query += " AND log_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND log_date <= ?"
                params.append(end_date)

            query += " ORDER BY log_date"
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_habit_log_for_date(self, habit_id: int, log_date: str) -> Optional[sqlite3.Row]:
        """Log spécifique pour une date."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM habit_logs 
                WHERE habit_id = ? AND log_date = ?
            """, (habit_id, log_date))
            return cursor.fetchone()

    def delete_habit_log(self, habit_id: int, log_date: str) -> bool:
        """Supprime un log spécifique."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM habit_logs 
                WHERE habit_id = ? AND log_date = ?
            """, (habit_id, log_date))
            return cursor.rowcount > 0

    def get_habit_month_stats(self, habit_id: int, year: int, month: int) -> dict:
        """Stats pour un mois donné."""
        from calendar import monthrange
        total_days = monthrange(year, month)[1]

        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month:02d}-{total_days:02d}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM habit_logs
                WHERE habit_id = ? AND log_date >= ? AND log_date <= ?
                GROUP BY status
            """, (habit_id, start, end))

            stats = {row[0]: row[1] for row in cursor.fetchall()}
            done = stats.get("done", 0)
            missed = stats.get("missed", 0)
            partial = stats.get("partial", 0)

            return {
                "done": done,
                "missed": missed,
                "partial": partial,
                "total_logged": done + missed + partial,
                "rate": round(done / total_days * 100, 1) if total_days else 0
            }

    # ═══════════════════════════════════════════════════
    # WIRD METHODS
    # ═══════════════════════════════════════════════════

    def create_wird(
        self,
        title: str,
        description: Optional[str] = None,
        icon: str = "📿",
        color: str = "#3B82F6",
        schedule_type: str = "daily",
        target_days: Optional[str] = None,
        is_template: bool = False
    ) -> int:
        """Crée un nouveau Wird (programme spirituel)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO wirds (title, description, icon, color, schedule_type, target_days, is_template)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, description, icon, color, schedule_type, target_days, 1 if is_template else 0))
            return cursor.lastrowid

    def add_wird_item(
        self,
        wird_id: int,
        title: str,
        description: Optional[str] = None,
        icon: str = "✨",
        target_count: int = 1,
        unit: str = "fois",
        duration_seconds: Optional[int] = None,
        order_index: int = 0,
        is_optional: bool = False
    ) -> int:
        """Ajoute un item à un Wird."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO wird_items (wird_id, title, description, icon, target_count, unit, duration_seconds, order_index, is_optional)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (wird_id, title, description, icon, target_count, unit, duration_seconds, order_index, 1 if is_optional else 0))
            return cursor.lastrowid

    def get_wird_by_id(self, wird_id: int) -> Optional[sqlite3.Row]:
        """Récupère un Wird avec ses items."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM wirds WHERE id = ?", (wird_id,))
            return cursor.fetchone()

    def get_wird_items(self, wird_id: int) -> list[sqlite3.Row]:
        """Récupère tous les items d'un Wird, ordonnés."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM wird_items 
                WHERE wird_id = ? 
                ORDER BY order_index ASC
            """, (wird_id,))
            return cursor.fetchall()

    def get_all_wirds(self, include_templates: bool = False, include_archived: bool = False) -> list[sqlite3.Row]:
        """Récupère tous les Wirds actifs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM wirds WHERE 1=1"
            params = []

            if not include_templates:
                query += " AND is_template = 0"
            if not include_archived:
                query += " AND archived_at IS NULL"

            query += " ORDER BY is_template DESC, created_at DESC"
            cursor.execute(query, params)
            return cursor.fetchall()

    def update_wird(self, wird_id: int, **kwargs) -> bool:
        """Met à jour un Wird."""
        allowed = ['title', 'description', 'icon', 'color', 'schedule_type', 'target_days', 'is_active']
        updates = []
        params = []

        for key, value in kwargs.items():
            if key in allowed:
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return False

        params.append(wird_id)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE wirds SET {', '.join(updates)} WHERE id = ?", params)
            return cursor.rowcount > 0

    def delete_wird(self, wird_id: int) -> bool:
        """Supprime un Wird (cascade sur items et sessions)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM wirds WHERE id = ?", (wird_id,))
            return cursor.rowcount > 0

    def archive_wird(self, wird_id: int) -> bool:
        """Archive un Wird."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("UPDATE wirds SET archived_at = ? WHERE id = ?", (now, wird_id))
            return cursor.rowcount > 0

    # ═══════════════════════════════════════════════════
    # WIRD SESSION METHODS
    # ═══════════════════════════════════════════════════

    def start_wird_session(self, wird_id: int) -> int:
        """Démarre une nouvelle session de Wird."""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Vérifier si session déjà en cours aujourd'hui
            cursor.execute("""
                SELECT id FROM wird_sessions 
                WHERE wird_id = ? AND session_date = ? AND status = 'in_progress'
            """, (wird_id, today))
            existing = cursor.fetchone()
            if existing:
                return existing["id"]

            # Compter les items
            cursor.execute("SELECT COUNT(*) FROM wird_items WHERE wird_id = ?", (wird_id,))
            total_items = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO wird_sessions (wird_id, session_date, started_at, items_total, status)
                VALUES (?, ?, ?, ?, 'in_progress')
            """, (wird_id, today, now.isoformat(), total_items))
            return cursor.lastrowid

    def complete_wird_item(self, session_id: int, item_id: int, 
                        actual_count: int = 1, duration_seconds: Optional[int] = None,
                        note: Optional[str] = None) -> int:
        """Marque un item comme complété dans la session."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO wird_session_logs (session_id, item_id, completed_at, actual_count, duration_seconds, status, note)
                VALUES (?, ?, ?, ?, ?, 'completed', ?)
            """, (session_id, item_id, now, actual_count, duration_seconds, note))

            # Mettre à jour le compteur de la session
            cursor.execute("""
                UPDATE wird_sessions 
                SET items_completed = items_completed + 1
                WHERE id = ?
            """, (session_id,))

            return cursor.lastrowid

    def skip_wird_item(self, session_id: int, item_id: int, note: Optional[str] = None) -> None:
        """Marque un item comme sauté."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO wird_session_logs (session_id, item_id, completed_at, status, note)
                VALUES (?, ?, ?, 'skipped', ?)
            """, (session_id, item_id, datetime.now().isoformat(), note))

    def complete_wird_session(self, session_id: int, mood_after: Optional[int] = None, 
                            note: Optional[str] = None) -> bool:
        """Finalise une session."""
        now = datetime.now()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Calculer la durée totale
            cursor.execute("SELECT started_at FROM wird_sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                started = datetime.fromisoformat(row["started_at"])
                duration = int((now - started).total_seconds())

                cursor.execute("""
                    UPDATE wird_sessions 
                    SET completed_at = ?, total_duration_seconds = ?, status = 'completed', mood_after = ?, note = ?
                    WHERE id = ?
                """, (now.isoformat(), duration, mood_after, note, session_id))
                return cursor.rowcount > 0
            return False

    def get_wird_session_progress(self, session_id: int) -> dict:
        """Récupère la progression d'une session en cours."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ws.*, w.title as wird_title, w.color, w.icon
                FROM wird_sessions ws
                JOIN wirds w ON ws.wird_id = w.id
                WHERE ws.id = ?
            """, (session_id,))
            session = cursor.fetchone()

            if not session:
                return {}

            cursor.execute("""
                SELECT wi.*, wsl.status as log_status, wsl.actual_count, wsl.note as log_note
                FROM wird_items wi
                LEFT JOIN wird_session_logs wsl ON wsl.item_id = wi.id AND wsl.session_id = ?
                WHERE wi.wird_id = ?
                ORDER BY wi.order_index
            """, (session_id, session["wird_id"]))
            items = cursor.fetchall()

            completed = sum(1 for i in items if i["log_status"] == "completed")
            skipped = sum(1 for i in items if i["log_status"] == "skipped")

            return {
                "session": dict(session),
                "items": [dict(i) for i in items],
                "completed_count": completed,
                "skipped_count": skipped,
                "remaining_count": session["items_total"] - completed - skipped,
                "percentage": round((completed / session["items_total"]) * 100, 1) if session["items_total"] > 0 else 0
            }

    def get_wird_stats(self, wird_id: int, days: int = 30) -> dict:
        """Statistiques d'un Wird sur N jours."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_sessions,
                    AVG(total_duration_seconds) as avg_duration,
                    AVG(mood_after) as avg_mood
                FROM wird_sessions
                WHERE wird_id = ? AND session_date >= ?
            """, (wird_id, start_date))
            stats = cursor.fetchone()

            # Streak actuel
            cursor.execute("""
                SELECT session_date, status 
                FROM wird_sessions 
                WHERE wird_id = ? 
                ORDER BY session_date DESC
            """, (wird_id,))
            sessions = cursor.fetchall()

            streak = 0
            for s in sessions:
                if s["status"] == "completed":
                    streak += 1
                else:
                    break

            return {
                "total_sessions": stats["total_sessions"] or 0,
                "completed_sessions": stats["completed_sessions"] or 0,
                "completion_rate": round((stats["completed_sessions"] / stats["total_sessions"]) * 100, 1) if stats["total_sessions"] else 0,
                "avg_duration_seconds": round(stats["avg_duration"] or 0),
                "avg_mood": round(stats["avg_mood"] or 0, 1),
                "current_streak": streak
            }

    def get_today_sessions(self) -> list[sqlite3.Row]:
        """Récupère toutes les sessions du jour."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ws.*, w.title, w.icon, w.color
                FROM wird_sessions ws
                JOIN wirds w ON ws.wird_id = w.id
                WHERE ws.session_date = ?
                ORDER BY ws.started_at DESC
            """, (today,))
            return cursor.fetchall()

    def seed_wird_templates(self) -> None:
        """Crée les templates de Wird par défaut."""
        templates = [
            {
                "title": "Wird du Matin (Adhkar Sabah)",
                "icon": "☀️",
                "color": "#F59E0B",
                "schedule_type": "daily",
                "items": [
                    ("Ayat al-Kursi", "1x", 1, "fois", 60, "📖"),
                    ("Surah Al-Ikhlas", "3x", 3, "fois", 30, "📖"),
                    ("Surah Al-Falaq", "3x", 3, "fois", 30, "📖"),
                    ("Surah An-Nas", "3x", 3, "fois", 30, "📖"),
                    ("SubhanAllah", "33x", 33, "fois", 60, "🌟"),
                    ("Alhamdulillah", "33x", 33, "fois", 60, "🌟"),
                    ("Allahu Akbar", "34x", 34, "fois", 60, "🌟"),
                    ("La ilaha illallah", "1x", 1, "fois", 15, "☝️"),
                    ("Hasbunallahu wa ni'mal wakeel", "7x", 7, "fois", 30, "🛡️"),
                ]
            },
            {
                "title": "Wird du Soir (Adhkar Masaa)",
                "icon": "🌙",
                "color": "#6366F1",
                "schedule_type": "daily",
                "items": [
                    ("Ayat al-Kursi", "1x", 1, "fois", 60, "📖"),
                    ("Surah Al-Ikhlas", "3x", 3, "fois", 30, "📖"),
                    ("Surah Al-Falaq", "3x", 3, "fois", 30, "📖"),
                    ("Surah An-Nas", "3x", 3, "fois", 30, "📖"),
                    ("Bismillahilladhi la yadurru...", "3x", 3, "fois", 30, "🛡️"),
                    ("Raditu billahi rabba...", "3x", 3, "fois", 30, "❤️"),
                    ("SubhanAllah wa bihamdihi", "100x", 100, "fois", 120, "🌟"),
                ]
            },
            {
                "title": "Wird Post-Prière",
                "icon": "🤲",
                "color": "#10B981",
                "schedule_type": "daily",
                "items": [
                    ("Astaghfirullah", "3x", 3, "fois", 15, "🤍"),
                    ("Allahumma anta as-salam...", "1x", 1, "fois", 15, "🕊️"),
                    ("SubhanAllah", "33x", 33, "fois", 45, "🌟"),
                    ("Alhamdulillah", "33x", 33, "fois", 45, "🌟"),
                    ("Allahu Akbar", "34x", 34, "fois", 45, "🌟"),
                    ("La ilaha illallah wahdahu...", "1x", 1, "fois", 15, "☝️"),
                ]
            },
            {
                "title": "Wird Tahajjud",
                "icon": "🌌",
                "color": "#8B5CF6",
                "schedule_type": "custom",
                "target_days": None,
                "items": [
                    ("Witr + Shaf' + 2 rak'a", "1x", 1, "fois", 300, "🌙"),
                    ("Dua Qunut", "1x", 1, "fois", 60, "📖"),
                    ("Dua personnalisée", "1x", 1, "fois", 120, "🤲"),
                    ("Istighfar prolongé", "100x", 100, "fois", 180, "🤍"),
                ]
            },
            {
                "title": "Wird Jumu'a",
                "icon": "🕌",
                "color": "#EC4899",
                "schedule_type": "custom",
                "target_days": "5",
                "items": [
                    ("Ghusl", "1x", 1, "fois", 600, "🚿"),
                    ("Surah Al-Kahf", "1x", 1, "fois", 900, "📖"),
                    ("Salat Doha", "2 rak'a", 1, "fois", 300, "☀️"),
                    ("Beaucoup de Salat sur le Prophète ﷺ", "100x", 100, "fois", 300, "💚"),
                    ("Dua entre Dhuhr et Asr", "1x", 1, "fois", 300, "🤲"),
                ]
            },
        ]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Vérifier si templates existent déjà
            cursor.execute("SELECT COUNT(*) FROM wirds WHERE is_template = 1")
            if cursor.fetchone()[0] > 0:
                return

            for template in templates:
                cursor.execute("""
                    INSERT INTO wirds (title, icon, color, schedule_type, target_days, is_template)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (template["title"], template["icon"], template["color"], 
                    template["schedule_type"], template.get("target_days")))
                wird_id = cursor.lastrowid

                for idx, (title, desc, count, unit, duration, icon) in enumerate(template["items"]):
                    cursor.execute("""
                        INSERT INTO wird_items (wird_id, title, description, icon, target_count, unit, duration_seconds, order_index)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (wird_id, title, desc, icon, count, unit, duration, idx))

            conn.commit()
            print(f"✅ {len(templates)} templates Wird créés")