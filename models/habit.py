"""
models/habit.py
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Set
from enum import Enum


class HabitFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"      # ex: 3 fois par semaine, pas importe quels jours
    CUSTOM = "custom"      # ex: lundi, mercredi, vendredi


class LogStatus(str, Enum):
    DONE = "done"
    MISSED = "missed"
    PARTIAL = "partial"   # ex: "j'ai fait 10min au lieu de 30min"


@dataclass
class HabitLog:
    id: int
    habit_id: int
    date: date
    status: LogStatus
    note: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Habit:
    id: int
    title: str
    description: Optional[str] = None
    goal_id: Optional[int] = None          # FK vers Goal, nullable
    frequency: HabitFrequency = HabitFrequency.DAILY
    target_days: Optional[Set[int]] = None   # {0,2,4} = lun/mer/ven (0=lundi)
    color: str = "#3B82F6"
    icon: Optional[str] = None               # "🏃", "📖", "🕌"
    created_at: datetime = field(default_factory=datetime.now)
    archived_at: Optional[datetime] = None
    
    # Computed (pas stocké en DB)
    logs: List[HabitLog] = field(default_factory=list)
    
    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None
    
    def get_status_for_date(self, target_date: date) -> Optional[LogStatus]:
        """Retourne le statut d'un jour donné."""
        for log in self.logs:
            if log.date == target_date:
                return log.status
        return None
    
    def get_month_completion(self, year: int, month: int) -> dict:
        """Stats pour un mois donné."""
        from calendar import monthrange
        total_days = monthrange(year, month)[1]
        
        done = 0
        missed = 0
        total_expected = 0
        
        for day in range(1, total_days + 1):
            current_date = date(year, month, day)
            # Vérifier si cette habitude est attendue ce jour-là
            if not self._is_expected_on(current_date):
                continue
                
            total_expected += 1
            status = self.get_status_for_date(current_date)
            if status == LogStatus.DONE:
                done += 1
            elif status == LogStatus.MISSED:
                missed += 1
        
        return {
            "done": done,
            "missed": missed,
            "pending": total_expected - done - missed,
            "rate": round(done / total_expected * 100, 1) if total_expected else 0
        }
    
    def _is_expected_on(self, target_date: date) -> bool:
        """Cette habitude doit-elle être faite ce jour-là ?"""
        if self.frequency == HabitFrequency.DAILY:
            return True
        if self.frequency == HabitFrequency.CUSTOM and self.target_days:
            return target_date.weekday() in self.target_days
        # WEEKLY: on vérifie au moment du log si la cible hebdo est atteinte
        return True
    
    @property
    def current_streak(self) -> int:
        """Nombre de jours consécutifs réussis."""
        streak = 0
        current = date.today()
        
        while True:
            if not self._is_expected_on(current):
                current -= timedelta(days=1)
                continue
                
            status = self.get_status_for_date(current)
            if status == LogStatus.DONE:
                streak += 1
                current -= timedelta(days=1)
            else:
                break
        
        return streak