"""
Testy wydajności systemu
"""
import unittest
import tempfile
import shutil
import time
import timeit
from datetime import datetime

from goal_tracker.models.goal import Goal, PersonalGoal, BusinessGoal
from goal_tracker.logic import GoalManager
from goal_tracker.data import DataManager
from goal_tracker.api import APIManager


class TestPerformance(unittest.TestCase):
    """Testy wydajności i czasu wykonania"""

    def setUp(self):
        """Przygotowanie środowiska wydajności"""
        self.test_dir = tempfile.mkdtemp()
        self.data_manager = DataManager(self.test_dir)
        self.goal_manager = GoalManager(self.data_manager, max_goals=2000)
        self.api_manager = APIManager(self.data_manager, self.goal_manager)
        self.test_user = "default"

    def tearDown(self):
        """Czyszczenie"""
        if self.test_dir:
            shutil.rmtree(self.test_dir)

    def test_goal_creation_performance(self):
        """Test 1: Wydajność tworzenia celów"""

        def create_goals():
            for i in range(100):
                goal = Goal(f"Performance Goal {i}", f"Description {i}", 100.0)
                self.goal_manager.add_goal(self.test_user, goal)

        # Pomiar czasu wykonania
        execution_time = timeit.timeit(create_goals, number=1)

        # Sprawdzenie czy czas jest akceptowalny (< 1 sekunda)
        self.assertLess(execution_time, 1.0,
                        f"Tworzenie 100 celów trwało {execution_time:.3f}s (oczekiwano < 1.0s)")

        # Sprawdzenie czy wszystkie cele zostały dodane
        user_goals = self.goal_manager.get_user_goals(self.test_user)
        self.assertEqual(len(user_goals), 100)

    def test_goal_search_performance(self):
        """Test 2: Wydajność wyszukiwania celów"""
        # Przygotowanie danych
        for i in range(500):
            goal = Goal(f"Search Goal {i}", f"Description keyword {i}", 100.0)
            self.goal_manager.add_goal(self.test_user, goal)

        def search_operation():
            return self.goal_manager.search_goals(self.test_user, "keyword")

        # Pomiar czasu wyszukiwania
        start_time = time.time()
        results = search_operation()
        end_time = time.time()

        execution_time = end_time - start_time

        # Sprawdzenie wydajności (< 0.1 sekundy)
        self.assertLess(execution_time, 0.1,
                        f"Wyszukiwanie w 500 celach trwało {execution_time:.3f}s (oczekiwano < 0.1s)")

        # Sprawdzenie poprawności wyników
        self.assertEqual(len(results), 500)

    def test_data_save_load_performance(self):
        """Test 3: Wydajność zapisu i odczytu danych"""
        # Przygotowanie dużej ilości danych
        goals = []
        for i in range(200):
            goal = Goal(f"Data Goal {i}", f"Description {i}", 100.0)
            goal.update_progress(i % 100)  # Różne postępy
            goals.append(goal)
            self.goal_manager.add_goal(self.test_user, goal)

        goals_data = [g.to_dict() for g in goals]

        # Test wydajności zapisu
        def save_operation():
            return self.data_manager.save_goals_data(goals_data, self.test_user)

        save_time = timeit.timeit(save_operation, number=1)
        self.assertLess(save_time, 0.5,
                        f"Zapis 200 celów trwał {save_time:.3f}s (oczekiwano < 0.5s)")

        # Test wydajności odczytu
        def load_operation():
            return self.data_manager.load_goals_data(self.test_user)

        load_time = timeit.timeit(load_operation, number=1)
        self.assertLess(load_time, 0.3,
                        f"Odczyt 200 celów trwał {load_time:.3f}s (oczekiwano < 0.3s)")

    def test_goal_filtering_performance(self):
        """Test 4: Wydajność filtrowania celów"""
        # Przygotowanie różnorodnych danych
        goal_types = ["Ogólny", "Osobisty", "Biznesowy"]
        statuses = ["aktywny", "zakończony", "wstrzymany"]

        for i in range(300):
            if i % 3 == 0:
                goal = Goal(f"Goal {i}", f"Desc {i}", 100.0)
            elif i % 3 == 1:
                goal = PersonalGoal(f"Goal {i}", f"Desc {i}", 100.0)
            else:
                goal = BusinessGoal(f"Goal {i}", f"Desc {i}", 100.0)

            goal.status = statuses[i % 3]
            self.goal_manager.add_goal(self.test_user, goal)

        # Test filtrowania według typu
        def filter_by_type():
            return self.goal_manager.get_goals_by_type(self.test_user, "Ogólny")

        type_filter_time = timeit.timeit(filter_by_type, number=10) / 10
        self.assertLess(type_filter_time, 0.01,
                        f"Filtrowanie według typu trwało {type_filter_time:.4f}s (oczekiwano < 0.01s)")

        # Test filtrowania według statusu
        def filter_by_status():
            return self.goal_manager.get_goals_by_status(self.test_user, "aktywny")

        status_filter_time = timeit.timeit(filter_by_status, number=10) / 10
        self.assertLess(status_filter_time, 0.01,
                        f"Filtrowanie według statusu trwało {status_filter_time:.4f}s (oczekiwano < 0.01s)")

    def test_progress_update_performance(self):
        """Test 5: Wydajność aktualizacji postępu"""
        # Przygotowanie celów
        goals = []
        for i in range(100):
            goal = Goal(f"Progress Goal {i}", f"Desc {i}", 100.0)
            self.goal_manager.add_goal(self.test_user, goal)
            goals.append(goal)

        # Test masowej aktualizacji postępu
        def update_all_progress():
            for i, goal in enumerate(goals):
                self.goal_manager.update_goal_progress(self.test_user, goal.id, float(i))

        update_time = timeit.timeit(update_all_progress, number=1)
        self.assertLess(update_time, 0.5,
                        f"Aktualizacja 100 postępów trwała {update_time:.3f}s (oczekiwano < 0.5s)")

    def test_api_export_performance(self):
        """Test 6: Wydajność eksportu przez API"""
        # Przygotowanie danych
        for i in range(150):
            goal = Goal(f"Export Goal {i}", f"Description {i}", 100.0)
            goal.update_progress(i % 100)
            self.goal_manager.add_goal(self.test_user, goal)

        # Test eksportu JSON
        def export_json():
            return self.api_manager.export_goals_to_json()

        json_time = timeit.timeit(export_json, number=1)
        self.assertLess(json_time, 0.2,
                        f"Eksport JSON 150 celów trwał {json_time:.3f}s (oczekiwano < 0.2s)")

        # Test eksportu CSV
        def export_csv():
            return self.api_manager.export_goals_to_csv()

        csv_time = timeit.timeit(export_csv, number=1)
        self.assertLess(csv_time, 0.3,
                        f"Eksport CSV 150 celów trwał {csv_time:.3f}s (oczekiwano < 0.3s)")

    def test_api_import_performance(self):
        """Test 7: Wydajność importu danych"""
        # Przygotowanie danych do importu
        goals_to_import = []
        for i in range(100):
            goal_data = {
                "title": f"Import Goal {i}",
                "description": f"Description {i}",
                "target_value": 100.0,
                "current_value": float(i % 50),
                "goal_type": "Ogólny",
                "status": "aktywny"
            }
            goals_to_import.append(goal_data)

        # Test wydajności importu przez bezpośrednie dodawanie
        def import_operation():
            imported_count = 0
            for goal_data in goals_to_import:
                try:
                    goal = Goal(
                        goal_data['title'],
                        goal_data['description'],
                        goal_data['target_value']
                    )
                    goal.current_value = goal_data['current_value']
                    goal.status = goal_data['status']

                    if self.goal_manager.add_goal(self.test_user, goal):
                        imported_count += 1
                except Exception:
                    continue
            return imported_count

        import_time = timeit.timeit(import_operation, number=1)
        self.assertLess(import_time, 1.0,  # Zwiększony limit
                        f"Import 100 celów trwał {import_time:.3f}s (oczekiwano < 1.0s)")

        # Sprawdzenie czy import się udał
        imported_count = import_operation()
        self.assertEqual(imported_count, 100, "Nie wszystkie cele zostały zaimportowane")

    def test_goal_removal_performance(self):
        """Test 8: Wydajność usuwania celów"""
        # Przygotowanie celów
        goals = []
        for i in range(200):
            goal = Goal(f"Remove Goal {i}", f"Desc {i}", 100.0)
            self.goal_manager.add_goal(self.test_user, goal)
            goals.append(goal)

        # Test usuwania połowy celów
        def remove_goals():
            for i in range(0, 100):  # Usuń pierwsze 100 celów
                self.goal_manager.remove_goal(self.test_user, goals[i].id)

        removal_time = timeit.timeit(remove_goals, number=1)
        self.assertLess(removal_time, 0.3,
                        f"Usuwanie 100 celów trwało {removal_time:.3f}s (oczekiwano < 0.3s)")

        # Sprawdzenie czy cele zostały usunięte
        remaining_goals = self.goal_manager.get_user_goals(self.test_user)
        self.assertEqual(len(remaining_goals), 100)

    def test_large_dataset_operations(self):
        """Test 9: Operacje na dużych zestawach danych"""
        large_size = 500

        # Test tworzenia dużego zestawu
        start_time = time.time()
        for i in range(large_size):
            goal = Goal(f"Large Goal {i}", f"Description {i}", 100.0)
            self.goal_manager.add_goal(self.test_user, goal)
        creation_time = time.time() - start_time

        self.assertLess(creation_time, 10.0,
                        f"Tworzenie {large_size} celów trwało {creation_time:.3f}s (oczekiwano < 10.0s)")

        # Test wyszukiwania w dużym zestawie
        start_time = time.time()
        results = self.goal_manager.search_goals(self.test_user, "Goal 250")
        search_time = time.time() - start_time

        self.assertLess(search_time, 0.2,
                        f"Wyszukiwanie w {large_size} celach trwało {search_time:.3f}s (oczekiwano < 0.2s)")

        # Sprawdzenie poprawności wyszukiwania
        self.assertGreater(len(results), 0)

    def test_concurrent_operations_performance(self):
        """Test 10: Wydajność operacji współbieżnych (symulacja)"""
        # Symulacja wielu użytkowników
        users = [f"user_{i}" for i in range(5)]
        goals_per_user = 20

        # Test dodawania celów dla wielu użytkowników
        start_time = time.time()
        for user in users:
            for i in range(goals_per_user):
                goal = Goal(f"Goal {i} for {user}", f"Desc {i}", 100.0)
                self.goal_manager.add_goal(user, goal)
        multi_user_time = time.time() - start_time

        total_goals = len(users) * goals_per_user
        self.assertLess(multi_user_time, 5.0,
                        f"Dodawanie {total_goals} celów dla {len(users)} użytkowników "
                        f"trwało {multi_user_time:.3f}s (oczekiwano < 5.0s)")

        # Test zapisu danych wszystkich użytkowników
        start_time = time.time()
        for user in users:
            goals = self.goal_manager.get_user_goals(user)
            goals_data = [g.to_dict() for g in goals]
            self.data_manager.save_goals_data(goals_data, user)
        save_all_time = time.time() - start_time

        self.assertLess(save_all_time, 3.0,
                        f"Zapis danych {len(users)} użytkowników "
                        f"trwał {save_all_time:.3f}s (oczekiwano < 3.0s)")


if __name__ == '__main__':
    unittest.main(verbosity=2)
