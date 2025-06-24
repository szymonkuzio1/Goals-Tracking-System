"""
Testy integracyjne całego systemu
"""
import unittest
import tempfile
import shutil
import os
from datetime import datetime

from goal_tracker.logic import GoalManager
from goal_tracker.data import DataManager
from goal_tracker.models.goal import Goal, PersonalGoal, BusinessGoal
from goal_tracker.api import APIManager


class TestSystemIntegration(unittest.TestCase):
    """
    Testy integracyjne całego systemu
    """

    def setUp(self):
        """Przygotowanie kompletnego środowiska testowego"""
        # Utworzenie tymczasowego katalogu
        self.test_dir = tempfile.mkdtemp()

        # Inicjalizacja wszystkich komponentów
        self.data_manager = DataManager(self.test_dir)
        self.goal_manager = GoalManager(self.data_manager)
        self.api_manager = APIManager(self.data_manager, self.goal_manager)

        # Testowe dane
        self.test_username = "integration_user"
        self.test_email = "integration@test.com"

    def tearDown(self):
        """Czyszczenie po testach"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_complete_user_workflow(self):
        """Test kompletnego workflow użytkownika"""
        # 1. Utworzenie użytkownika
        user = self.user_manager.create_user(
            self.test_username, self.test_email, "Integration Test User"
        )
        self.assertIsNotNone(user)

        # 2. Zapis danych użytkownika
        user_data = user.to_dict()
        result = self.data_manager.save_user_data(user_data)
        self.assertTrue(result)

        # 3. Dodanie różnych typów celów
        goals = [
            Goal("Cel ogólny", "Ogólny cel testowy", 100.0, "Test"),
            PersonalGoal("Bieganie", "Biegać codziennie", 30.0, "wysoki", True),
            BusinessGoal("ROI", "Zwiększenie ROI o 25%", 25.0, "Finanse", 50000.0)
        ]

        for goal in goals:
            result = self.goal_manager.add_goal(self.test_username, goal)
            self.assertTrue(result)
            user.add_goal_id(goal.id)

        # 4. Aktualizacja postępów
        user_goals = self.goal_manager.get_user_goals(self.test_username)
        for i, goal in enumerate(user_goals):
            progress = (i + 1) * 20  # 20, 40, 60
            result = self.goal_manager.update_goal_progress(
                self.test_username, goal.id, progress, f"Progress update {i + 1}"
            )
            self.assertTrue(result)

        # 5. Sprawdzenie statystyk
        stats = self.goal_manager.get_user_statistics(self.test_username)
        self.assertEqual(stats['total_goals'], 3)
        self.assertGreater(stats['average_progress'], 0)

        # 6. Test kopii zapasowej
        result = self.goal_manager.backup_data()
        self.assertTrue(result)

        # 7. Test eksportu przez API
        export_result = self.api_manager.export_goals_to_json(self.test_username)
        self.assertTrue(export_result['success'])
        self.assertEqual(len(export_result['data']['goals']), 3)

    def test_data_persistence_workflow(self):
        """Test trwałości danych"""
        # 1. Utworzenie i zapis danych
        user = self.user_manager.create_user(self.test_username, self.test_email)
        self.data_manager.save_user_data(user.to_dict())

        goal = Goal("Persistence Test", "Test trwałości danych", 100.0, "Test")
        self.goal_manager.add_goal(self.test_username, goal)

        # Zapis celów
        user_goals = self.goal_manager.get_user_goals(self.test_username)
        goals_data = [g.to_dict() for g in user_goals]
        self.data_manager.save_goals_data(goals_data, self.test_username)

        # 2. Utworzenie nowego managera (symulacja restartu aplikacji)
        new_data_manager = DataManager(self.test_dir)
        new_goal_manager = GoalManager(new_data_manager)

        # 3. Odczyt zapisanych danych
        loaded_goals = new_data_manager.load_goals_data(self.test_username)
        self.assertEqual(len(loaded_goals), 1)
        self.assertEqual(loaded_goals[0]['title'], "Persistence Test")

        loaded_user = new_data_manager.load_user_data(self.test_username)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(loaded_user['username'], self.test_username)

    def test_api_import_export_workflow(self):
        """Test workflow importu i eksportu przez API"""
        # 1. Przygotowanie danych do importu
        import_data = {
            "goals": [
                {
                    "title": "Imported Goal 1",
                    "description": "First imported goal",
                    "target_value": 100.0,
                    "current_value": 25.0,
                    "category": "Import",
                    "status": "aktywny"
                },
                {
                    "title": "Imported Goal 2",
                    "description": "Second imported goal",
                    "target_value": 50.0,
                    "current_value": 10.0,
                    "category": "Import",
                    "status": "aktywny"
                }
            ]
        }

        # 2. Import przez API
        import_result = self.api_manager.import_goals_from_json(import_data, self.test_username)
        self.assertTrue(import_result['success'])
        self.assertEqual(import_result['imported_successfully'], 2)

        # 3. Sprawdzenie czy cele zostały dodane
        user_goals = self.goal_manager.get_user_goals(self.test_username)
        self.assertEqual(len(user_goals), 2)

        # 4. Eksport przez API
        export_result = self.api_manager.export_goals_to_json(self.test_username)
        self.assertTrue(export_result['success'])
        exported_goals = export_result['data']['goals']
        self.assertEqual(len(exported_goals), 2)

        # 5. Test eksportu CSV
        csv_export_result = self.api_manager.export_goals_to_csv(self.test_username)
        self.assertTrue(csv_export_result['success'])
        self.assertIn('title', csv_export_result['data'])
        self.assertIn('description', csv_export_result['data'])

    def test_error_handling_integration(self):
        """Test obsługi błędów w całym systemie"""
        # 1. Test nieprawidłowych danych użytkownika
        invalid_user = self.user_manager.create_user("ab", "invalid_email")  # Za krótka nazwa, zły email
        self.assertIsNone(invalid_user)

        # 2. Test nieprawidłowych danych celu
        invalid_goal = Goal("", "Description", -10.0)  # Pusty tytuł, ujemna wartość docelowa
        # Powinno rzucić AssertionError przy tworzeniu

        # 3. Test importu nieprawidłowych danych
        invalid_import_data = {
            "goals": [
                {
                    "title": "",  # Pusty tytuł
                    "description": "Invalid goal",
                    "target_value": "not_a_number"  # Nieprawidłowy typ
                }
            ]
        }

        import_result = self.api_manager.import_goals_from_json(invalid_import_data, self.test_username)
        self.assertFalse(import_result['success'])
        self.assertEqual(import_result['imported_successfully'], 0)

        # 4. Test aktualizacji nieistniejącego celu
        result = self.goal_manager.update_goal_progress(
            self.test_username, "nonexistent_goal_id", 50.0
        )
        self.assertFalse(result)

    def test_webhook_integration(self):
        """Test integracji webhooków z akcjami systemu"""
        # 1. Rejestracja webhook
        webhook_id = self.api_manager.register_webhook(
            "goals_imported",
            "http://example.com/webhook",
            "secret_key_123"
        )
        self.assertNotEqual(webhook_id, "")

        # 2. Import danych (powinien wyzwolić webhook)
        import_data = {
            "goals": [{
                "title": "Webhook Test Goal",
                "description": "Goal to test webhook",
                "target_value": 100.0,
                "category": "Test"
            }]
        }

        import_result = self.api_manager.import_goals_from_json(import_data, self.test_username)
        self.assertTrue(import_result['success'])

        # 3. Sprawdzenie statystyk webhook
        api_stats = self.api_manager.get_api_statistics()
        self.assertGreater(api_stats['webhooks']['total_requests'], 0)

    def test_large_dataset_performance(self):
        """Test wydajności z dużym zestawem danych"""
        # Utworzenie dużej liczby celów
        goals_count = 100

        for i in range(goals_count):
            goal = Goal(f"Performance Goal {i}", f"Description {i}", 100.0, f"Category {i % 5}")
            goal.update_progress(i % 100)  # Różne postępy

            result = self.goal_manager.add_goal(self.test_username, goal)
            self.assertTrue(result)

        # Test pobierania wszystkich celów
        user_goals = self.goal_manager.get_user_goals(self.test_username)
        self.assertEqual(len(user_goals), goals_count)

        # Test filtrowania
        category_0_goals = self.goal_manager.get_goals_by_category(self.test_username, "Category 0")
        self.assertEqual(len(category_0_goals), 20)  # 100 / 5 = 20

        # Test wyszukiwania
        search_results = self.goal_manager.search_goals(self.test_username, "Performance Goal 1")
        self.assertGreaterEqual(len(search_results), 10)  # Goal 1, 10, 11, 12, ..., 19

        # Test eksportu dużego zestawu
        export_result = self.api_manager.export_goals_to_json(self.test_username)
        self.assertTrue(export_result['success'])
        self.assertEqual(len(export_result['data']['goals']), goals_count)

        # Test statystyk
        stats = self.goal_manager.get_user_statistics(self.test_username)
        self.assertEqual(stats['total_goals'], goals_count)

    def test_concurrent_operations_simulation(self):
        """Test symulacji operacji współbieżnych"""
        # Symulacja wielu użytkowników
        users = []
        for i in range(5):
            username = f"concurrent_user_{i}"
            email = f"user{i}@test.com"
            user = self.user_manager.create_user(username, email)
            users.append((username, user))

        # Każdy użytkownik dodaje cele
        for username, user in users:
            for j in range(10):
                goal = Goal(f"Goal {j} for {username}", "Description", 100.0, "Concurrent")
                result = self.goal_manager.add_goal(username, goal)
                self.assertTrue(result)

        # Sprawdzenie izolacji danych między użytkownikami
        for username, user in users:
            user_goals = self.goal_manager.get_user_goals(username)
            self.assertEqual(len(user_goals), 10)

            # Sprawdzenie że cele należą do właściwego użytkownika
            for goal in user_goals:
                self.assertIn(username, goal.title)

        # Test statystyk systemowych
        system_health = self.goal_manager.get_system_health()
        self.assertEqual(system_health['total_users'], 5)
        self.assertEqual(system_health['total_goals'], 50)  # 5 użytkowników * 10 celów

    def test_backup_restore_integration(self):
        """Test integracji kopii zapasowej i przywracania"""
        # 1. Utworzenie danych
        user = self.user_manager.create_user(self.test_username, self.test_email)
        self.data_manager.save_user_data(user.to_dict())

        goals = [
            Goal("Backup Goal 1", "First goal", 100.0, "Backup"),
            Goal("Backup Goal 2", "Second goal", 50.0, "Backup")
        ]

        for goal in goals:
            self.goal_manager.add_goal(self.test_username, goal)

        # 2. Utworzenie kopii zapasowej
        backup_result = self.goal_manager.backup_data()
        self.assertTrue(backup_result)

        # 3. Modyfikacja danych
        new_goal = Goal("New Goal After Backup", "Added after backup", 75.0, "New")
        self.goal_manager.add_goal(self.test_username, new_goal)

        # Sprawdzenie że mamy 3 cele
        user_goals = self.goal_manager.get_user_goals(self.test_username)
        self.assertEqual(len(user_goals), 3)

        # 4. Pobranie listy kopii zapasowych
        backup_list = self.data_manager.get_backup_list()
        self.assertGreater(len(backup_list), 0)

        # 5. Przywracanie z kopii zapasowej
        latest_backup = backup_list[0]['filename']
        restore_result = self.data_manager.restore_from_backup(latest_backup)
        self.assertTrue(restore_result)

        # 6. Sprawdzenie czy dane zostały przywrócone
        # (W rzeczywistej implementacji trzeba by przeładować cele do goal_managera)
        # Tu tylko sprawdzamy czy plik został przywrócony
        self.assertTrue(self.data_manager.goals_file.exists())


class TestPerformanceMetrics(unittest.TestCase):
    """
    Testy wydajności systemu
    """

    def setUp(self):
        """Przygotowanie środowiska wydajności"""
        self.test_dir = tempfile.mkdtemp()
        self.data_manager = DataManager(self.test_dir)
        self.goal_manager = GoalManager(self.data_manager)

    def tearDown(self):
        """Czyszczenie"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_goal_creation_performance(self):
        """Test wydajności tworzenia celów"""
        import time

        start_time = time.time()

        # Tworzenie 1000 celów
        for i in range(1000):
            goal = Goal(f"Performance Goal {i}", f"Description {i}", 100.0, "Performance")
            self.goal_manager.add_goal("perf_user", goal)

        end_time = time.time()
        execution_time = end_time - start_time

        # Powinno zakończyć się w rozsądnym czasie (< 5 sekund)
        self.assertLess(execution_time, 5.0)

        # Sprawdzenie czy wszystkie cele zostały dodane
        user_goals = self.goal_manager.get_user_goals("perf_user")
        self.assertEqual(len(user_goals), 1000)

    def test_search_performance(self):
        """Test wydajności wyszukiwania"""
        import time

        # Przygotowanie danych
        for i in range(500):
            goal = Goal(f"Search Goal {i}", f"Description with keyword {i}", 100.0, f"Cat{i % 10}")
            self.goal_manager.add_goal("search_user", goal)

        start_time = time.time()

        # Wykonanie 100 wyszukiwań
        for i in range(100):
            results = self.goal_manager.search_goals("search_user", f"keyword {i}")

        end_time = time.time()
        execution_time = end_time - start_time

        # Powinno zakończyć się szybko (< 2 sekundy)
        self.assertLess(execution_time, 2.0)


if __name__ == '__main__':
    # Uruchomienie testów integracyjnych
    unittest.main(verbosity=2)
