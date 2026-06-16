"""
services/habit_service.py
Service pour les habitudes.
"""

import json
from datetime import date
from typing import Dict, List, Optional

from database import DatabaseManager


class HabitService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_habit(self, **kwargs) -> int:
        return self.db.create_habit(**kwargs)

    def get_habit(self, habit_id: int) -> Optional[dict]:
        row = self.db.get_habit_by_id(habit_id)
        return dict(row) if row else None

    def list_habits(self) -> List[dict]:
        """Récupère les habitudes avec les noms de goal/tâche."""
        rows = self.db.get_all_habits()
        habits = []
        for row in rows:
            habit = dict(row)
            
            # Récupérer le nom du goal
            if habit.get("goal_id"):
                goal = self.db.get_goal_by_id(habit["goal_id"])
                habit["goal_title"] = goal["title"] if goal else None
            
            # Récupérer le nom de la tâche
            if habit.get("task_id"):
                task = self.db.get_task_by_id(habit["task_id"])
                habit["task_name"] = task["name"] if task else None
            
            habits.append(habit)
        
        return habits

    def update_habit(self, habit_id: int, **kwargs) -> bool:
        return self.db.update_habit(habit_id, **kwargs)

    def archive_habit(self, habit_id: int) -> bool:
        return self.db.archive_habit(habit_id)

    def delete_habit(self, habit_id: int) -> bool:
        return self.db.delete_habit(habit_id)

    def toggle_log(self, habit_id: int, log_date: str, status: str) -> None:
        self.db.create_or_update_habit_log(habit_id, log_date, status)

    def delete_log(self, habit_id: int, log_date: str) -> None:
        self.db.delete_habit_log(habit_id, log_date)

    def get_logs_for_month(self, year: int, month: int) -> Dict[int, Dict[str, str]]:
        """Retourne {habit_id: {"2026-06-15": "done", ...}}."""
        import calendar
        _, last_day = calendar.monthrange(year, month)
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month:02d}-{last_day:02d}"

        result: Dict[int, Dict[str, str]] = {}
        habits = self.list_habits()

        for habit in habits:
            logs = self.db.get_habit_logs(habit["id"], start, end)
            result[habit["id"]] = {
                log["log_date"]: log["status"]
                for log in logs
            }

        return result

    def get_habit_stats(self, habit_id: int, year: int, month: int) -> dict:
        return self.db.get_habit_month_stats(habit_id, year, month)

    def get_current_streak(self, habit_id: int) -> int:
        """Calcule la série actuelle de jours consécutifs réussis."""
        habit = self.get_habit(habit_id)
        if not habit:
            return 0

        today = date.today()
        streak = 0
        current = today

        while True:
            date_iso = current.isoformat()
            log = self.db.get_habit_log_for_date(habit_id, date_iso)

            if log and log["status"] == "done":
                streak += 1
                current -= __import__('datetime').timedelta(days=1)
            else:
                # Vérifier si c'est un jour où l'habitude n'est pas attendue
                weekday = current.weekday()  # 0=lundi
                freq = habit.get("frequency", "daily")

                if freq == "custom" and habit.get("target_days"):
                    target_days = json.loads(habit["target_days"])
                    if weekday not in target_days:
                        current -= __import__('datetime').timedelta(days=1)
                        continue

                break

        return streak