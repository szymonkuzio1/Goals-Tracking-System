"""
Moduł tekstowego interfejsu użytkownika
Obsługa wyświetlania menu i formularzy
"""
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from .models.goal import Goal, PersonalGoal, BusinessGoal
from .utils.formatters import (
    format_progress_bar, format_goal_summary,
    format_date_display, ProgressFormatter
)
from .utils.validators import validate_goal_data, validate_progress_value


class GoalTrackerGUI:
    """
    Klasa interfejsu użytkownika dla systemu śledzenia celów
    """

    def __init__(self):
        self._screen_width = 50  # prywatna szerokość ekranu (ilość '=')
        self._progress_formatter = ProgressFormatter()
        self._colors = {  # prywatny słownik kolorów
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'goal': '🎯',
            'progress': '📈'
        }

    def _clear_screen(self) -> None:
        """Prywatna metoda czyszczenia ekranu"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _print_header(self, title: str, width: int = None) -> None:
        """Prywatna metoda wyświetlania nagłówka"""
        if width is None:
            width = self._screen_width

        print("=" * width)
        print(f"{title:^{width}}")
        print("=" * width)

    def _print_separator(self, char: str = "-", width: int = None) -> None:
        """Prywatna metoda wyświetlania separatora"""
        if width is None:
            width = self._screen_width
        print(char * width)

    def _get_user_input(self, prompt: str, input_type: str = "str", required: bool = True) -> Any:
        """Prywatna metoda pobierania danych od użytkownika z walidacją"""

        def _convert_input(value: str, target_type: str) -> Any:
            """Wewnętrzna funkcja konwersji typu"""
            if target_type == "int":
                return int(value)
            elif target_type == "float":
                return float(value)
            elif target_type == "bool":
                return value.lower() in ['yes', 'y', 'tak', 't', '1', 'true']
            else:
                return value.strip()

        while True:
            try:
                user_input = input(f"{prompt}: ").strip()

                # Sprawdzenie wymaganego pola
                if required and not user_input:
                    print(f"{self._colors['error']} To pole jest wymagane!")
                    continue

                # Możliwość pominięcia niewymaganych pól
                if not required and not user_input:
                    return None

                # Konwersja typu
                converted_value = _convert_input(user_input, input_type)
                return converted_value

            except ValueError as e:
                print(f"{self._colors['error']} Nieprawidłowy format danych: {e}")
            except KeyboardInterrupt:
                print(f"\n{self._colors['warning']} Operacja przerwana")
                return None

    def _display_goals_table(self, goals: List[Goal]) -> None:
        """Prywatna metoda wyświetlania tabeli celów"""
        if not goals:
            print(f"{self._colors['info']} Brak celów do wyświetlenia")
            return

        # Nagłówek tabeli
        print(f"{'Nr':<4} {'Tytuł':<25} {'Typ':<15} {'Postęp':<20} {'Status':<12}")
        self._print_separator()

        # Wyświetlanie celów
        for i, goal in enumerate(goals, 1):
            progress_bar = format_progress_bar(goal.current_value, goal.target_value, 15)
            status_icon = self._colors['success'] if goal.status == 'zakończony' else self._colors['goal']

            print(f"{i:<4} {goal.title[:24]:<25} {goal.get_goal_type():<15} "
                  f"{progress_bar:<20} {status_icon} {goal.status:<10}")

    def show_goals_list(self, goals: List[Goal]) -> None:
        """Wyświetlenie listy celów użytkownika"""
        try:
            self._clear_screen()
            self._print_header("📋 LISTA TWOICH CELÓW")

            if not goals:
                print(f"\n{self._colors['info']} Nie masz jeszcze żadnych celów!")
                print("💡 Użyj opcji 'Dodaj nowy cel' aby rozpocząć.")
                input("\nNaciśnij Enter aby kontynuować...")
                return

            # Sortowanie celów - użycie sorted() z lambda
            sorted_goals = sorted(goals, key=lambda g: g.get_progress_percentage(), reverse=True)

            print(f"\nLiczba celów: {len(goals)}")
            print(f"Aktywnych: {len(list(filter(lambda g: g.status == 'aktywny', goals)))}")
            print(f"Zakończonych: {len(list(filter(lambda g: g.status == 'zakończony', goals)))}")
            print()

            # Wyświetlenie tabeli
            self._display_goals_table(sorted_goals)

            # Menu opcji
            print(f"\n{self._colors['info']} Opcje:")
            print("1. Pokaż szczegóły celu")
            print("2. Filtruj cele")
            print("0. Powrót do menu głównego")

            choice = self._get_user_input("Wybierz opcję (0-2)", "str", False)

            if choice == "1":
                self._show_goal_details_interactive(sorted_goals)
            elif choice == "2":
                self._filter_goals_interactive(goals)

        except Exception as e:
            print(f"{self._colors['error']} Błąd wyświetlania listy celów: {e}")
            input("Naciśnij Enter aby kontynuować...")

    def _show_goal_details_interactive(self, goals: List[Goal]) -> None:
        """Prywatna metoda interaktywnego wyświetlania szczegółów celu"""
        try:
            goal_num = self._get_user_input("Podaj numer celu", "int")

            if 1 <= goal_num <= len(goals):
                goal = goals[goal_num - 1]

                print(f"\n{self._colors['goal']} SZCZEGÓŁY CELU")
                self._print_separator()
                print(f"Tytuł: {goal.title}")
                print(f"Opis: {goal.description}")
                print(f"Kategoria: {goal.category}")
                print(f"Status: {goal.status}")
                print(f"Postęp: {format_progress_bar(goal.current_value, goal.target_value)}")
                print(f"Data utworzenia: {format_date_display(goal.created_date)}")

                if hasattr(goal, 'deadline') and goal.deadline:
                    print(f"Termin realizacji: {format_date_display(goal.deadline)}")

                # Historia postępów
                history = goal.get_history()
                if history:
                    print(f"\n📈 Historia postępów ({len(history)} wpisów):")
                    for entry in history[-5:]:  # Ostatnie 5 wpisów
                        date_str = entry['date'].strftime("%d.%m.%Y %H:%M")
                        print(f"  • {date_str}: {entry['old_value']} → {entry['new_value']}")

            else:
                print(f"{self._colors['error']} Nieprawidłowy numer celu!")

        except Exception as e:
            print(f"{self._colors['error']} Błąd wyświetlania szczegółów: {e}")

        input("\nNaciśnij Enter aby kontynuować...")

    def _filter_goals_interactive(self, goals: List[Goal]) -> None:
        """Prywatna metoda interaktywnego filtrowania celów"""
        try:
            print(f"\n{self._colors['info']} FILTROWANIE CELÓW")
            print("1. Po statusie")
            print("2. Po typie celu")
            print("3. Po nazwie")
            print("4. Po postępie")

            filter_choice = self._get_user_input("Wybierz typ filtra (1-4)", "str")

            filtered_goals = []

            if filter_choice == "1":
                status = self._get_user_input("Podaj status (aktywny/zakończony/wstrzymany)", "str")
                filtered_goals = list(filter(lambda g: g.status.lower() == status.lower(), goals))

            elif filter_choice == "2":
                category = self._get_user_input("Podaj kategorię", "str")
                filtered_goals = list(filter(lambda g: category.lower() in g.category.lower(), goals))

            elif filter_choice == "3":
                search_term = self._get_user_input("Podaj fragment nazwy", "str")
                filtered_goals = list(filter(lambda g: search_term.lower() in g.title.lower(), goals))

            elif filter_choice == "4":
                min_progress = self._get_user_input("Minimalny postęp (%)", "float")
                filtered_goals = list(filter(lambda g: g.get_progress_percentage() >= min_progress, goals))

            if filtered_goals:
                print(f"\n{self._colors['success']} Znaleziono {len(filtered_goals)} celów:")
                self._display_goals_table(filtered_goals)
            else:
                print(f"{self._colors['warning']} Brak celów spełniających kryteria")

        except Exception as e:
            print(f"{self._colors['error']} Błąd filtrowania: {e}")

        input("\nNaciśnij Enter aby kontynuować...")

    def add_new_goal_interactive(self, goal_manager, username: str) -> None:
        """Interaktywne dodawanie nowego celu"""

        def _get_goal_type() -> str:
            """Wewnętrzna funkcja wyboru typu celu"""
            print("Typy celów:")
            print("1. Cel ogólny")
            print("2. Cel osobisty")
            print("3. Cel biznesowy")

            while True:
                choice = self._get_user_input("Wybierz typ celu (1-3)", "str")
                if choice in ["1", "2", "3"]:
                    return choice
                print(f"{self._colors['error']} Nieprawidłowy wybór!")

        def _create_goal_by_type(goal_type: str, goal_data: Dict) -> Goal:
            """Wewnętrzna funkcja tworzenia celu według typu"""
            if goal_type == "1":  # Ogólny
                return Goal(goal_data['title'], goal_data['description'], goal_data['target_value'])
            elif goal_type == "2":  # Osobisty
                return PersonalGoal(goal_data['title'], goal_data['description'], goal_data['target_value'])
            else:  # Biznesowy
                return BusinessGoal(goal_data['title'], goal_data['description'], goal_data['target_value'])

        try:
            self._clear_screen()
            self._print_header("➕ DODAWANIE NOWEGO CELU")

            # Zbieranie podstawowych danych
            goal_data = {}
            goal_data['title'] = self._get_user_input("Tytuł celu", "str")
            goal_data['description'] = self._get_user_input("Opis celu", "str")
            goal_data['target_value'] = self._get_user_input("Wartość docelowa", "float")

            # Walidacja danych
            is_valid, errors = validate_goal_data(goal_data)
            if not is_valid:
                print(f"{self._colors['error']} Błędy walidacji:")
                for error in errors:
                    print(f"  • {error}")
                input("Naciśnij Enter aby kontynuować...")
                return

            # Wybór typu celu
            goal_type = _get_goal_type()

            # Tworzenie celu
            goal = _create_goal_by_type(goal_type, goal_data)

            # Opcjonalny termin realizacji
            deadline_str = self._get_user_input("Termin realizacji (YYYY-MM-DD, DD.MM.YYYY lub DD/MM/YYYY, opcjonalnie)", "str", False)
            if deadline_str:
                try:
                    goal.deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
                except ValueError:
                    print(f"{self._colors['warning']} Nieprawidłowy format daty, termin pominięty")

            # Dodanie celu do managera
            if goal_manager.add_goal(username, goal):
                print(f"\n{self._colors['success']} Cel '{goal.title}' został dodany pomyślnie!")

                # Wyświetlenie podsumowania
                print(f"\n{self._colors['info']} Podsumowanie:")
                print(format_goal_summary(goal.to_dict()))
            else:
                print(f"{self._colors['error']} Nie udało się dodać celu!")

        except KeyboardInterrupt:
            print(f"\n{self._colors['warning']} Dodawanie celu przerwane")
        except Exception as e:
            print(f"{self._colors['error']} Błąd dodawania celu: {e}")

        input("\nNaciśnij Enter aby kontynuować...")

    def update_goal_progress_interactive(self, goal_manager, username: str) -> None:
        """Interaktywna aktualizacja postępu celu"""

        def _select_goal_for_update(goals: List[Goal]) -> Optional[Goal]:
            """Wewnętrzna funkcja wyboru celu do aktualizacji"""
            print(f"\n{self._colors['info']} Wybierz cel do aktualizacji:")

            # Filtrowanie tylko aktywnych celów
            active_goals = list(filter(lambda g: g.status == 'aktywny', goals))

            if not active_goals:
                print(f"{self._colors['warning']} Brak aktywnych celów do aktualizacji!")
                return None

            self._display_goals_table(active_goals)

            goal_num = self._get_user_input("Podaj numer celu (0 = anuluj)", "int")

            if goal_num == 0:
                return None
            elif 1 <= goal_num <= len(active_goals):
                return active_goals[goal_num - 1]
            else:
                print(f"{self._colors['error']} Nieprawidłowy numer celu!")
                return None

        try:
            self._clear_screen()
            self._print_header("📈 AKTUALIZACJA POSTĘPU CELU")

            # Pobranie celów użytkownika
            user_goals = goal_manager.get_user_goals(username)

            if not user_goals:
                print(f"{self._colors['info']} Nie masz jeszcze żadnych celów!")
                input("Naciśnij Enter aby kontynuować...")
                return

            # Wybór celu
            selected_goal = _select_goal_for_update(user_goals)
            if not selected_goal:
                return

            # Wyświetlenie aktualnego stanu
            print(f"\n{self._colors['goal']} Wybrany cel: {selected_goal.title}")
            print(f"Aktualny postęp: {selected_goal.current_value}/{selected_goal.target_value}")
            print(format_progress_bar(selected_goal.current_value, selected_goal.target_value))

            # Opcje aktualizacji
            print(f"\n{self._colors['info']} Opcje aktualizacji:")
            print("1. Ustaw nową wartość")
            print("2. Dodaj do aktualnej wartości")
            print("3. Odejmij od aktualnej wartości")

            update_type = self._get_user_input("Wybierz opcję (1-3)", "str")

            new_value = selected_goal.current_value

            if update_type == "1":
                new_value = self._get_user_input("Nowa wartość", "float")
            elif update_type == "2":
                add_value = self._get_user_input("Wartość do dodania", "float")
                new_value = selected_goal.current_value + add_value
            elif update_type == "3":
                sub_value = self._get_user_input("Wartość do odjęcia", "float")
                new_value = selected_goal.current_value - sub_value
            else:
                print(f"{self._colors['error']} Nieprawidłowa opcja!")
                return

            # Walidacja nowej wartości
            is_valid, message = validate_progress_value(new_value, selected_goal.target_value)
            if not is_valid:
                print(f"{self._colors['error']} {message}")
                input("Naciśnij Enter aby kontynuować...")
                return

            # Opcjonalna notatka
            note = self._get_user_input("Notatka (opcjonalnie)", "str", False) or ""

            # Aktualizacja postępu
            if selected_goal.update_progress(new_value):
                # Dodanie do managera postępów
                goal_manager.add_progress_entry(selected_goal.id, new_value, note)

                print(f"\n{self._colors['success']} Postęp zaktualizowany pomyślnie!")

                # Wyświetlenie nowego stanu
                print(f"\nNowy stan celu:")
                print(format_progress_bar(selected_goal.current_value, selected_goal.target_value))

                # Sprawdzenie czy cel został osiągnięty
                if selected_goal.status == 'zakończony':
                    print(f"\n{self._colors['success']} 🎉 GRATULACJE! Cel został osiągnięty!")

                    # Opcjonalne dodanie notatki osiągnięcia
                    if hasattr(selected_goal, 'add_motivation_note'):
                        celebration_note = self._get_user_input("Dodaj notatkę o osiągnięciu (opcjonalnie)", "str",
                                                                False)
                        if celebration_note:
                            selected_goal.add_motivation_note(f"🎉 Cel osiągnięty: {celebration_note}")
            else:
                print(f"{self._colors['error']} Nie udało się zaktualizować postępu!")

        except KeyboardInterrupt:
            print(f"\n{self._colors['warning']} Aktualizacja przerwana")
        except Exception as e:
            print(f"{self._colors['error']} Błąd aktualizacji postępu: {e}")

        input("\nNaciśnij Enter aby kontynuować...")

    def manage_goals_interactive(self, goal_manager, username: str) -> None:
        """Interaktywne zarządzanie celami"""

        def _edit_goal_interactive(goals: List[Goal]) -> None:
            """Wewnętrzna funkcja edycji celu"""
            if not goals:
                print(f"{self._colors['info']} Brak celów do edycji")
                return

            self._display_goals_table(goals)
            goal_num = self._get_user_input("Podaj numer celu do edycji (0 = anuluj)", "int")

            if goal_num == 0:
                return
            elif 1 <= goal_num <= len(goals):
                goal = goals[goal_num - 1]

                print(f"\n{self._colors['info']} Edycja celu: {goal.title}")
                print("Zostaw puste aby zachować aktualną wartość")

                new_title = self._get_user_input(f"Nowy tytuł [{goal.title}]", "str", False)
                new_description = self._get_user_input(f"Nowy opis [{goal.description}]", "str", False)
                new_category = self._get_user_input(f"Nowa kategoria [{goal.category}]", "str", False)

                # Aktualizacja pól
                if new_title:
                    goal.title = new_title
                if new_description:
                    goal.description = new_description
                if new_category:
                    goal.category = new_category

                print(f"{self._colors['success']} Cel zaktualizowany pomyślnie!")
            else:
                print(f"{self._colors['error']} Nieprawidłowy numer celu!")

        def _delete_goal_interactive(goals: List[Goal]) -> None:
            """Wewnętrzna funkcja usuwania celu"""
            if not goals:
                print(f"{self._colors['info']} Brak celów do usunięcia")
                return

            self._display_goals_table(goals)
            goal_num = self._get_user_input("Podaj numer celu do usunięcia (0 = anuluj)", "int")

            if goal_num == 0:
                return
            elif 1 <= goal_num <= len(goals):
                goal = goals[goal_num - 1]

                # Potwierdzenie usunięcia
                confirm = self._get_user_input(f"Czy na pewno usunąć cel '{goal.title}'? (tak/nie)", "str")

                if confirm.lower() in ['tak', 'yes', 'y', 't']:
                    if goal_manager.remove_goal(username, goal.id):
                        print(f"{self._colors['success']} Cel '{goal.title}' został usunięty!")
                    else:
                        print(f"{self._colors['error']} Nie udało się usunąć celu!")
                else:
                    print(f"{self._colors['info']} Usuwanie anulowane")
            else:
                print(f"{self._colors['error']} Nieprawidłowy numer celu!")

        try:
            while True:
                self._clear_screen()
                self._print_header("⚙️ ZARZĄDZANIE CELAMI")

                print("1. ✏️ Edytuj cel ✏️")
                print("2. 🗑️ Usuń cel 🗑️")
                print("3. ⏸️ Wstrzymaj/Wznów cel ⏸️")
                print("4. 🔄 Zmień status celu 🔄")
                print("5. 📋 Duplikuj cel 📋")
                print("0. 🔙 Powrót do menu głównego 🔙")

                choice = self._get_user_input("Wybierz opcję (0-5)", "str")

                if choice == "0":
                    break

                # Pobranie aktualnych celów
                user_goals = goal_manager.get_user_goals(username)

                if choice == "1":
                    _edit_goal_interactive(user_goals)
                elif choice == "2":
                    _delete_goal_interactive(user_goals)
                elif choice == "3":
                    self._toggle_goal_status_interactive(user_goals)
                elif choice == "4":
                    self._change_goal_status_interactive(user_goals)
                elif choice == "5":
                    self._duplicate_goal_interactive(user_goals, goal_manager, username)
                else:
                    print(f"{self._colors['error']} Nieprawidłowa opcja!")

                if choice != "0":
                    input("\nNaciśnij Enter aby kontynuować...")

        except Exception as e:
            print(f"{self._colors['error']} Błąd w zarządzaniu celami: {e}")
            input("Naciśnij Enter aby kontynuować...")

    def _toggle_goal_status_interactive(self, goals: List[Goal]) -> None:
        """Prywatna metoda przełączania statusu celu"""
        if not goals:
            print(f"{self._colors['info']} Brak celów")
            return

        active_goals = list(filter(lambda g: g.status in ['aktywny', 'wstrzymany'], goals))

        if not active_goals:
            print(f"{self._colors['info']} Brak celów do zmiany statusu")
            return

        self._display_goals_table(active_goals)
        goal_num = self._get_user_input("Podaj numer celu (0 = anuluj)", "int")

        if goal_num == 0:
            return
        elif 1 <= goal_num <= len(active_goals):
            goal = active_goals[goal_num - 1]

            if goal.status == 'aktywny':
                goal.status = 'wstrzymany'
                print(f"{self._colors['success']} Cel '{goal.title}' wstrzymany")
            else:
                goal.status = 'aktywny'
                print(f"{self._colors['success']} Cel '{goal.title}' wznowiony")
        else:
            print(f"{self._colors['error']} Nieprawidłowy numer celu!")

    def _change_goal_status_interactive(self, goals: List[Goal]) -> None:
        """Prywatna metoda zmiany statusu celu"""
        if not goals:
            print(f"{self._colors['info']} Brak celów")
            return

        self._display_goals_table(goals)
        goal_num = self._get_user_input("Podaj numer celu (0 = anuluj)", "int")

        if goal_num == 0:
            return
        elif 1 <= goal_num <= len(goals):
            goal = goals[goal_num - 1]

            print(f"\nAktualny status: {goal.status}")
            print("Dostępne statusy:")
            print("1. aktywny")
            print("2. wstrzymany")
            print("3. zakończony")

            status_choice = self._get_user_input("Wybierz nowy status (1-3)", "str")

            status_map = {"1": "aktywny", "2": "wstrzymany", "3": "zakończony"}
            new_status = status_map.get(status_choice)

            if new_status:
                goal.status = new_status
                print(f"{self._colors['success']} Status celu '{goal.title}' zmieniony na '{new_status}'")
            else:
                print(f"{self._colors['error']} Nieprawidłowy wybór statusu!")
        else:
            print(f"{self._colors['error']} Nieprawidłowy numer celu!")

    def _duplicate_goal_interactive(self, goals: List[Goal], goal_manager, username: str) -> None:
        """Prywatna metoda duplikowania celu"""
        if not goals:
            print(f"{self._colors['info']} Brak celów do duplikowania")
            return

        self._display_goals_table(goals)
        goal_num = self._get_user_input("Podaj numer celu do duplikowania (0 = anuluj)", "int")

        if goal_num == 0:
            return
        elif 1 <= goal_num <= len(goals):
            original_goal = goals[goal_num - 1]

            # Tworzenie kopii celu
            new_title = self._get_user_input(f"Tytuł nowego celu [{original_goal.title} - Kopia]", "str", False)
            if not new_title:
                new_title = f"{original_goal.title} - Kopia"

            # Tworzenie nowego celu na podstawie oryginalnego
            if isinstance(original_goal, PersonalGoal):
                new_goal = PersonalGoal(
                    new_title,
                    original_goal.description,
                    original_goal.target_value,
                    original_goal.priority,
                    original_goal.is_habit
                )
            elif isinstance(original_goal, BusinessGoal):
                new_goal = BusinessGoal(
                    new_title,
                    original_goal.description,
                    original_goal.target_value,
                    original_goal.department,
                    original_goal.budget
                )
            else:
                new_goal = Goal(
                    new_title,
                    original_goal.description,
                    original_goal.target_value,
                    original_goal.category
                )

            # Dodanie do managera
            if goal_manager.add_goal(username, new_goal):
                print(f"{self._colors['success']} Cel '{new_title}' został utworzony jako kopia!")
            else:
                print(f"{self._colors['error']} Nie udało się utworzyć kopii celu!")
        else:
            print(f"{self._colors['error']} Nieprawidłowy numer celu!")

    def _show_app_info(self) -> None:
        """Prywatna metoda wyświetlania informacji o aplikacji"""
        from . import APP_NAME, VERSION

        print(f"\n{self._colors['info']} INFORMACJE O APLIKACJI")
        self._print_separator()
        print(f"Nazwa: {APP_NAME}")
        print(f"Wersja: {VERSION}")
        print(f"Język: Python 3.x")
        print(f"Autor: [Twoje imię]")
        print(f"Data kompilacji: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"\n💡 System śledzenia celów i postępów")
        print("📚 Projekt edukacyjny - Python Programming")
