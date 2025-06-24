"""
Główny plik uruchomieniowy systemu
"""
import sys
import os
from datetime import datetime

from .gui import GoalTrackerGUI
from .logic import GoalManager
from .data import DataManager

# Zmienne globalne
DATA_MANAGER = None
GOAL_MANAGER = None
GUI = None
DEFAULT_USER = "default"  # Jeden domyślny użytkownik

def initialize_system() -> bool:
    """Inicjalizacja systemu"""
    global DATA_MANAGER, GOAL_MANAGER, GUI

    try:
        print("🚀 Inicjalizacja Systemu Śledzenia Celów...")

        if not os.path.exists("data"):
            os.makedirs("data")

        DATA_MANAGER = DataManager()
        GOAL_MANAGER = GoalManager(DATA_MANAGER)
        GUI = GoalTrackerGUI()

        DATA_MANAGER.load_all_data()

        if GOAL_MANAGER.load_goals_from_data_manager(DEFAULT_USER):
            goals_count = len(GOAL_MANAGER.get_user_goals(DEFAULT_USER))
            if goals_count > 0:
                print(f"✅ Załadowano {goals_count} celów do systemu")

        print("✅ System zainicjalizowany pomyślnie!")
        return True

    except Exception as e:
        print(f"❌ Błąd inicjalizacji systemu: {e}")
        return False

def main_menu_loop() -> None:
    """Główna pętla menu aplikacji"""
    try:
        while True:
            print("\n" + "="*50)
            print("🎯 SYSTEM ŚLEDZENIA CELÓW I POSTĘPÓW 🎯")
            print("="*50)
            print("1. 📋 Przeglądaj cele 📋")
            print("2. ➕ Dodaj nowy cel ➕")
            print("3. 📈 Aktualizuj postęp 📈")
            print("4. ⚙️ Zarządzaj celami ⚙️")
            print("5. 💾 Zapisz dane 💾")
            print("0. 🚪 Wyjście 🚪")
            print("="*50)

            choice = input("Wybierz opcję (0-5): ").strip()

            if choice == "0":
                break
            elif choice == "1":
                GUI.show_goals_list(GOAL_MANAGER.get_user_goals(DEFAULT_USER))
            elif choice == "2":
                GUI.add_new_goal_interactive(GOAL_MANAGER, DEFAULT_USER)
            elif choice == "3":
                GUI.update_goal_progress_interactive(GOAL_MANAGER, DEFAULT_USER)
            elif choice == "4":
                GUI.manage_goals_interactive(GOAL_MANAGER, DEFAULT_USER)
            elif choice == "5":
                save_data()
            else:
                print("❌ Nieprawidłowa opcja!")

    except KeyboardInterrupt:
        print("\n\n👋 Program przerwany przez użytkownika")

def save_data() -> None:
    """Zapis danych"""
    try:
        print("💾 Zapisywanie danych...")
        user_goals = GOAL_MANAGER.get_user_goals(DEFAULT_USER)

        if user_goals:
            goals_data = [goal.to_dict() for goal in user_goals]
            DATA_MANAGER.save_goals_data(goals_data, DEFAULT_USER)
            print(f"✅ Zapisano {len(goals_data)} celów")
        else:
            print("ℹ️ Brak celów do zapisania")

    except Exception as e:
        print(f"❌ Błąd zapisu danych: {e}")

def main() -> None:
    """Główna funkcja aplikacji"""
    try:
        print("=" * 60)
        print("🎯 SYSTEM ŚLEDZENIA CELÓW I POSTĘPÓW 🎯")
        print("   Wersja 1.0.0")
        print("=" * 60)

        if not initialize_system():
            sys.exit(1)

        main_menu_loop()

    except KeyboardInterrupt:
        print("\n\n⚡ Program przerwany (Ctrl+C)")
    except Exception as e:
        print(f"💥 Błąd aplikacji: {e}")
    finally:
        save_data()
        print("👋 Do widzenia!")

if __name__ == "__main__":
    main()
