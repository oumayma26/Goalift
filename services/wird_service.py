"""
services/wird_service.py
Service pour la gestion des Wirds (programmes spirituels).
"""

from typing import Optional, List, Dict
from database.database import DatabaseManager


class WirdService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def create_wird(self, title: str, description: Optional[str] = None,
                    schedule_type: str = "daily", target_days: Optional[str] = None) -> int:
        """Crée un nouveau Wird utilisateur."""
        return self.db.create_wird(
            title=title,
            description=description,
            schedule_type=schedule_type,
            target_days=target_days
        )

    def add_item(self, wird_id: int, title: str, target_count: int = 1,
                 unit: str = "fois", icon: str = "✨", order_index: int = 0) -> int:
        """Ajoute un item à un Wird."""
        return self.db.add_wird_item(
            wird_id=wird_id,
            title=title,
            target_count=target_count,
            unit=unit,
            icon=icon,
            order_index=order_index
        )

    def get_active_wirds(self) -> List[Dict]:
        """Récupère les Wirds actifs avec stats."""
        wirds = self.db.get_all_wirds(include_templates=False)
        result = []
        for w in wirds:
            stats = self.db.get_wird_stats(w["id"], days=7)
            result.append({
                **dict(w),
                "stats": stats,
                "is_due_today": self._is_wird_due_today(w)
            })
        return result

    def _is_wird_due_today(self, wird: Dict) -> bool:
        from datetime import datetime
        today = datetime.now()
        if wird["schedule_type"] == "daily":
            return True
        if wird["schedule_type"] == "custom" and wird["target_days"]:
            weekday = today.weekday()
            target_days = [int(d) for d in wird["target_days"].split(",")]
            return weekday in target_days
        return True

    def start_session(self, wird_id: int) -> Dict:
        session_id = self.db.start_wird_session(wird_id)
        return self.db.get_wird_session_progress(session_id)

    def complete_item(self, session_id: int, item_id: int, count: Optional[int] = None) -> None:
        actual_count = count or 1
        self.db.complete_wird_item(session_id, item_id, actual_count=actual_count)

    def skip_item(self, session_id: int, item_id: int) -> None:
        self.db.skip_wird_item(session_id, item_id)

    def finish_session(self, session_id: int, mood: Optional[int] = None, note: Optional[str] = None) -> Dict:
        self.db.complete_wird_session(session_id, mood, note)
        return self.db.get_wird_stats(
            self.db.get_wird_session_progress(session_id)["session"]["wird_id"],
            days=7
        )