"""
Moduł analizy postępów
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional


class Progress:
    """
    Klasa reprezentująca wpis postępu
    """

    def __init__(self, goal_id: str, value: float, note: str = ""):
        assert len(goal_id.strip()) > 0, "ID celu nie może być pusty"
        assert value >= 0, "Wartość postępu nie może być ujemna"

        self.goal_id = goal_id
        self.value = value
        self.note = note.strip()
        self.timestamp = datetime.now()
        self.id = self._generate_progress_id()

    def _generate_progress_id(self) -> str:
        """Prywatna metoda generowania ID wpisu postępu"""
        import uuid
        return f"prog_{str(uuid.uuid4())[:8]}"

    def to_dict(self) -> Dict:
        """Konwersja do słownika"""
        return {
            'id': self.id,
            'goal_id': self.goal_id,
            'value': self.value,
            'note': self.note,
            'timestamp': self.timestamp.isoformat()
        }

    def get_formatted_entry(self) -> str:
        """Sformatowany wpis postępu"""
        date_str = self.timestamp.strftime("%Y-%m-%d %H:%M")
        note_part = f" - {self.note}" if self.note else ""
        return f"[{date_str}] Wartość: {self.value}{note_part}"
