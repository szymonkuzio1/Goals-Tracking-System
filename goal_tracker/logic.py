"""
Moduł logiki biznesowej systemu śledzenia celów
Zawiera główne algorytmy zarządzania celami i analizę danych
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set

from .models.goal import Goal, PersonalGoal, BusinessGoal
from .utils.validators import validate_goal_data, validate_progress_value

# Zmienne globalne konfiguracyjne
MAX_GOALS = 50
MIN_PROGRESS_INTERVAL_HOURS = 1
DEFAULT_ANALYSIS_PERIOD_DAYS = 30
ACHIEVEMENT_THRESHOLDS = {
    'beginner': 25.0,
    'intermediate': 50.0,
    'advanced': 75.0,
    'expert': 100.0
}


class GoalManager:
    """
    Główna klasa zarządzania celami i postępami
    """

    def __init__(self, data_manager=None):
        self._goals_storage = {}  # prywatny słownik: {user_id: [Goal]}
        self._data_manager = data_manager
        self._last_backup_time = None  # czas ostatniej kopii zapasowej

    def _validate_user_goal_limit(self, username: str) -> bool:
        """Prywatna metoda sprawdzania limitu celów"""
        user_goals = self._goals_storage.get(username, [])
        return len(user_goals) < MAX_GOALS

    def add_goal(self, username: str, goal: Goal) -> bool:
        """Dodanie nowego celu do systemu"""

        try:
            assert isinstance(goal, Goal), "Obiekt musi być instancją klasy Goal"
            assert len(username.strip()) > 0, "Nazwa użytkownika nie może być pusta"

            # Sprawdzenie limitu celów
            if not self._validate_user_goal_limit(username):
                raise ValueError(f"Przekroczono limit {MAX_GOALS} celów")

            # Walidacja danych celu
            goal_data = goal.to_dict()
            is_valid, errors = validate_goal_data(goal_data)

            if not is_valid:
                raise ValueError(f"Nieprawidłowe dane celu: {', '.join(errors)}")

            # Dodanie celu do storage
            if username not in self._goals_storage:
                self._goals_storage[username] = []

            self._goals_storage[username].append(goal)

            # Zapis do pliku jeśli data_manager dostępny
            if self._data_manager:
                try:
                    goals_data = [g.to_dict() for g in self._goals_storage[username]]
                    self._data_manager.save_goals_data(goals_data, username)
                except Exception as e:
                    print(f"Ostrzeżenie: Nie udało się zapisać do pliku: {e}")

            print(f"✅ Cel '{goal.title}' dodany pomyślnie dla użytkownika {username}")
            return True

        except (AssertionError, ValueError) as e:
            print(f"❌ Błąd dodawania celu: {e}")
            return False
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd: {e}")
            return False

    def get_user_goals(self, username: str) -> List[Goal]:
        """Pobranie wszystkich celów użytkownika"""
        try:
            return self._goals_storage.get(username, []).copy()
        except Exception as e:
            print(f"Błąd pobierania celów: {e}")
            return []

    def get_user_goals_count(self, username: str) -> int:
        """Liczba celów użytkownika"""
        return len(self._goals_storage.get(username, []))

    def update_goal_progress(self, username: str, goal_id: str, new_value: float, note: str = "") -> bool:
        """Aktualizacja postępu konkretnego celu"""

        def _find_goal_by_id(goals: List[Goal], target_id: str) -> Optional[Goal]:
            """Wewnętrzna funkcja wyszukiwania celu po ID"""
            for goal in goals:
                if goal.id == target_id:
                    return goal
            return None

        def _check_progress_interval(goal: Goal) -> bool:
            """Wewnętrzna funkcja sprawdzania interwału aktualizacji"""
            if not hasattr(goal, '_last_update') or goal._last_update is None:
                return True

            time_diff = datetime.now() - goal._last_update
            return time_diff.total_seconds() / 3600 >= MIN_PROGRESS_INTERVAL_HOURS

        try:
            user_goals = self._goals_storage.get(username, [])
            goal = _find_goal_by_id(user_goals, goal_id)

            if not goal:
                raise ValueError(f"Nie znaleziono celu o ID: {goal_id}")

            # Sprawdzenie interwału aktualizacji
            if not _check_progress_interval(goal):
                print(f"⚠️ Możesz aktualizować postęp maksymalnie co {MIN_PROGRESS_INTERVAL_HOURS} godzin(y)")
                return False

            # Walidacja nowej wartości
            is_valid, message = validate_progress_value(new_value, goal.target_value)
            if not is_valid:
                raise ValueError(message)

            # Aktualizacja postępu
            old_value = goal.current_value
            if goal.update_progress(new_value):

                # Oznaczenie czasu ostatniej aktualizacji
                goal._last_update = datetime.now()

                print(f"✅ Postęp zaktualizowany: {old_value} → {new_value}")

                # Sprawdzenie kamieni milowych dla celów biznesowych
                if isinstance(goal, BusinessGoal):
                    achieved_milestones = goal.check_milestones()
                    for milestone in achieved_milestones:
                        print(f"🎉 Osiągnięto kamień milowy: {milestone}")

                return True
            else:
                return False

        except (ValueError, AssertionError) as e:
            print(f"❌ Błąd aktualizacji postępu: {e}")
            return False
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd aktualizacji: {e}")
            return False

    def remove_goal(self, username: str, goal_id: str) -> bool:
        """Usunięcie celu"""
        try:
            user_goals = self._goals_storage.get(username, [])

            # Filtrowanie - usunięcie celu o podanym ID
            updated_goals = list(filter(lambda g: g.id != goal_id, user_goals))

            if len(updated_goals) == len(user_goals):
                print(f"❌ Nie znaleziono celu o ID: {goal_id}")
                return False

            self._goals_storage[username] = updated_goals

            print(f"✅ Cel usunięty pomyślnie")
            return True

        except Exception as e:
            print(f"❌ Błąd usuwania celu: {e}")
            return False

    def load_goals_from_data_manager(self, username: str = "default") -> bool:
        """
        Załadowanie celów z DataManager do GoalManager
        """
        try:
            if not self._data_manager:
                print("❌ Brak dostępnego DataManager")
                return False

            # Załadowanie danych celów z pliku
            goals_data = self._data_manager.load_goals_data(username)

            if not goals_data:
                print("ℹ️ Brak celów do załadowania")
                return True

            # Konwersja słowników na obiekty Goal
            loaded_goals = []
            for goal_dict in goals_data:
                try:
                    # Określenie typu celu na podstawie goal_type
                    goal_type = goal_dict.get('goal_type', 'Ogólny')

                    if goal_type == 'Osobisty':
                        goal = PersonalGoal(
                            goal_dict['title'],
                            goal_dict['description'],
                            goal_dict['target_value']
                        )
                    elif goal_type == 'Biznesowy':
                        goal = BusinessGoal(
                            goal_dict['title'],
                            goal_dict['description'],
                            goal_dict['target_value']
                        )
                    else:
                        goal = Goal(
                            goal_dict['title'],
                            goal_dict['description'],
                            goal_dict['target_value']
                        )

                    # Ustawienie dodatkowe właściwości
                    goal.id = goal_dict.get('id', goal.id)
                    goal.current_value = goal_dict.get('current_value', 0.0)
                    goal.status = goal_dict.get('status', 'aktywny')

                    # Ustawienie daty
                    if 'created_date' in goal_dict and goal_dict['created_date']:
                        if isinstance(goal_dict['created_date'], str):
                            goal.created_date = datetime.fromisoformat(
                                goal_dict['created_date'].replace('Z', '+00:00')
                            )
                        else:
                            goal.created_date = goal_dict['created_date']

                    if 'deadline' in goal_dict and goal_dict['deadline']:
                        if isinstance(goal_dict['deadline'], str):
                            goal.deadline = datetime.fromisoformat(
                                goal_dict['deadline'].replace('Z', '+00:00')
                            )
                        else:
                            goal.deadline = goal_dict['deadline']

                    # Ustawienie historię
                    goal._history = goal_dict.get('history', [])

                    loaded_goals.append(goal)

                except Exception as e:
                    print(f"⚠️ Błąd ładowania celu '{goal_dict.get('title', 'Nieznany')}': {e}")
                    continue

            # Dodanie celu do storage
            if username not in self._goals_storage:
                self._goals_storage[username] = []

            self._goals_storage[username].extend(loaded_goals)

            print(f"✅ Załadowano {len(loaded_goals)} celów do GoalManager")
            return True

        except Exception as e:
            print(f"❌ Błąd ładowania celów do GoalManager: {e}")
            return False

    def get_goals_by_type(self, username: str, goal_type: str) -> List[Goal]:
        """Pobranie celów według typu - użycie filter()"""
        try:
            user_goals = self._goals_storage.get(username, [])
            return list(filter(lambda g: g.get_goal_type().lower() == goal_type.lower(), user_goals))
        except Exception as e:
            print(f"Błąd filtrowania według typu: {e}")
            return []

    def get_goals_by_status(self, username: str, status: str) -> List[Goal]:
        """Pobranie celów według statusu z filter()"""
        try:
            user_goals = self._goals_storage.get(username, [])
            return list(filter(lambda g: g.status.lower() == status.lower(), user_goals))
        except Exception as e:
            print(f"Błąd filtrowania według statusu: {e}")
            return []

    def search_goals(self, username: str, search_term: str) -> List[Goal]:
        """Wyszukiwanie celów po nazwie/opisie z filter()"""

        def _matches_search_term(goal: Goal, term: str) -> bool:
            """Wewnętrzna funkcja sprawdzania dopasowania"""
            term_lower = term.lower()
            return (term_lower in goal.title.lower() or
                    term_lower in goal.description.lower())

        try:
            user_goals = self._goals_storage.get(username, [])
            return list(filter(lambda g: _matches_search_term(g, search_term), user_goals))
        except Exception as e:
            print(f"Błąd wyszukiwania celów: {e}")
            return []

    def backup_data(self) -> bool:
        """Tworzenie kopii zapasowej danych"""
        try:
            if not self._data_manager:
                print("❌ Brak dostępnego managera danych")
                return False

            backup_data = {
                'goals_storage': {},
                'backup_timestamp': datetime.now().isoformat()
            }

            # Konwersja celów do formatu słownikowego
            for username, goals in self._goals_storage.items():
                backup_data['goals_storage'][username] = [goal.to_dict() for goal in goals]

            # Zapis kopii zapasowej
            backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            success = self._data_manager.save_backup(backup_data, backup_filename)

            if success:
                self._last_backup_time = datetime.now()
                print(f"✅ Kopia zapasowa utworzona: {backup_filename}")
                return True
            else:
                print("❌ Nie udało się utworzyć kopii zapasowej")
                return False

        except Exception as e:
            print(f"❌ Błąd tworzenia kopii zapasowej: {e}")
            return False

