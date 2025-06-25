"""
Moduł z klasami celów
"""
from datetime import datetime
from typing import List, Dict, Optional


class Goal:
    """
    Klasa bazowa dla celów
    """

    def __init__(self, title: str, description: str, target_value: float):
        # Asercje do walidacji danych
        assert len(title.strip()) > 0, "Tytuł celu nie może być pusty"
        assert target_value > 0, "Wartość docelowa musi być większa niż 0"

        self.id = self._generate_id()
        self.title = title.strip()
        self.description = description.strip()
        self.target_value = target_value
        self.current_value = 0.0
        self.status = "aktywny"
        self.created_date = datetime.now()
        self.deadline = None
        self._history = []

    def get_goal_type(self) -> str:
        """Zwraca typ celu"""
        return "Ogólny"

    def _generate_id(self) -> str:
        """Prywatna metoda generowania ID"""
        import uuid
        return str(uuid.uuid4())[:8]

    def update_progress(self, new_value: float) -> bool:
        """Aktualizacja postępu celu"""
        try:
            assert new_value >= 0, "Wartość postępu nie może być ujemna"

            old_value = self.current_value
            self.current_value = new_value

            # Sprawdzenie czy cel został osiągnięty
            if self.current_value >= self.target_value and self.status == "aktywny":
                self.status = "zakończony"

            history_entry = {
                'date': datetime.now(),
                'old_value': old_value,
                'new_value': new_value
            }
            self._history.append(history_entry)

            return True

        except Exception as e:
            print(f"Błąd aktualizacji postępu: {e}")
            return False

    def get_progress_percentage(self) -> float:
        """Obliczenie procentowego postępu"""
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)

    def get_progress_info(self) -> str:
        """Formatowanie informacji o postępie"""
        percentage = self.get_progress_percentage()
        return f"{self.title}: {self.current_value}/{self.target_value} ({percentage:.1f}%)"

    def get_history(self) -> List[Dict]:
        """Dostęp do historii zmian (tylko do odczytu)"""
        return self._history.copy()

    def to_dict(self) -> Dict:
        """Konwersja do słownika dla zapisu do pliku"""

        def _safe_serialize(obj):
            """Serializacja dowolnego obiektu"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif obj is None:
                return None
            else:
                return str(obj)

        try:
            result = {
                'id': str(self.id),
                'title': str(self.title),
                'description': str(self.description),
                'target_value': float(self.target_value),
                'current_value': float(self.current_value),
                'goal_type': str(self.get_goal_type()),
                'status': str(self.status),
                'created_date': _safe_serialize(self.created_date),
                'deadline': _safe_serialize(self.deadline),
                'history': []
            }

            # Serializacja historii
            for entry in self._history:
                try:
                    if isinstance(entry, dict):
                        safe_entry = {
                            'date': _safe_serialize(entry.get('date')),
                            'old_value': float(entry.get('old_value', 0)),
                            'new_value': float(entry.get('new_value', 0))
                        }
                        result['history'].append(safe_entry)
                except Exception as e:
                    print(f"⚠️ Błąd serializacji wpisu historii: {e}")
                    # Pomiń problematyczny wpis
                    continue

            # Test końcowy serializacji
            import json
            json.dumps(result)

            return result

        except Exception as e:
            print(f"❌ Krytyczny błąd w to_dict(): {e}")
            # Fallback - absolutnie podstawowa struktura
            return {
                'id': str(getattr(self, 'id', 'unknown')),
                'title': str(getattr(self, 'title', 'unknown')),
                'description': str(getattr(self, 'description', '')),
                'target_value': float(getattr(self, 'target_value', 0)),
                'current_value': float(getattr(self, 'current_value', 0)),
                'goal_type': 'Ogólny',
                'status': 'aktywny',
                'created_date': datetime.now().isoformat(),
                'deadline': None,
                'history': []
            }

class PersonalGoal(Goal):
    """
    Cel osobisty - dziedziczenie po klasie Goal
    """

    def __init__(self, title: str, description: str, target_value: float):
        super().__init__(title, description, target_value)

    def get_goal_type(self) -> str:
        """Zwraca typ celu"""
        return "Osobisty"

class BusinessGoal(Goal):
    """
    Cel biznesowy - dziedziczenie po klasie Goal
    """

    def __init__(self, title: str, description: str, target_value: float):
        super().__init__(title, description, target_value)

    def get_goal_type(self) -> str:
        """Zwraca typ celu"""
        return "Biznesowy"

