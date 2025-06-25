"""
Testy funkcjonalne - testowanie scenariuszy użytkownika
"""
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from goal_tracker.logic import GoalManager
from goal_tracker.data import DataManager
from goal_tracker.models.goal import Goal, PersonalGoal, BusinessGoal


class TestFunctionalScenarios(unittest.TestCase):
    """Testy funkcjonalne głównych scenariuszy"""

    def setUp(self):
        """Przygotowanie środowiska testowego"""
        self.test_dir = tempfile.mkdtemp()
        self.data_manager = DataManager(self.test_dir)
        self.goal_manager = GoalManager(self.data_manager)
        self.test_user = "default"

    def tearDown(self):
        """Czyszczenie po testach"""
        if self.test_dir:
            shutil.rmtree(self.test_dir)

    def test_add_and_view_goals_workflow(self):
        """Test 1: Scenariusz dodawania i przeglądania celów"""
        # Dodanie różnych typów celów
        goals = [
            Goal("Cel ogólny", "Opis ogólny", 100.0),
            PersonalGoal("Cel osobisty", "Opis osobisty", 50.0),
            BusinessGoal("Cel biznesowy", "Opis biznesowy", 200.0)
        ]

        for goal in goals:
            result = self.goal_manager.add_goal(self.test_user, goal)
            self.assertTrue(result)

        # Sprawdzenie czy wszystkie cele zostały dodane
        user_goals = self.goal_manager.get_user_goals(self.test_user)
        self.assertEqual(len(user_goals), 3)

        # Sprawdzenie typów
        goal_types = [goal.get_goal_type() for goal in user_goals]
        self.assertIn("Ogólny", goal_types)
        self.assertIn("Osobisty", goal_types)
        self.assertIn("Biznesowy", goal_types)

    def test_progress_tracking_workflow(self):
        """Test 2: Scenariusz śledzenia postępu"""
        goal = Goal("Test Progress", "Opis", 100.0)
        self.goal_manager.add_goal(self.test_user, goal)

        # Sekwencja aktualizacji postępu
        progress_values = [25.0, 50.0, 75.0, 100.0]
        for value in progress_values:
            result = self.goal_manager.update_goal_progress(
                self.test_user, goal.id, value, f"Progress to {value}"
            )
            self.assertTrue(result)

        # Sprawdzenie finalnego stanu
        updated_goals = self.goal_manager.get_user_goals(self.test_user)
        final_goal = updated_goals[0]

        self.assertEqual(final_goal.current_value, 100.0)
        self.assertEqual(final_goal.status, "zakończony")
        self.assertEqual(len(final_goal.get_history()), 4)

    def test_goal_filtering_workflow(self):
        """Test 3: Scenariusz filtrowania celów"""
        # Przygotowanie różnych celów
        goals_data = [
            ("Aktywny cel 1", "aktywny", 30.0),
            ("Aktywny cel 2", "aktywny", 60.0),
            ("Zakończony cel", "zakończony", 100.0),
            ("Wstrzymany cel", "wstrzymany", 20.0)
        ]

        for title, status, progress in goals_data:
            goal = Goal(title, "Opis", 100.0)
            goal.update_progress(progress)
            if status != "aktywny":
                goal.status = status
            self.goal_manager.add_goal(self.test_user, goal)

        # Test filtrowania według statusu
        active_goals = self.goal_manager.get_goals_by_status(self.test_user, "aktywny")
        completed_goals = self.goal_manager.get_goals_by_status(self.test_user, "zakończony")
        paused_goals = self.goal_manager.get_goals_by_status(self.test_user, "wstrzymany")

        self.assertEqual(len(active_goals), 2)
        self.assertEqual(len(completed_goals), 1)
        self.assertEqual(len(paused_goals), 1)

    def test_goal_search_workflow(self):
        """Test 4: Scenariusz wyszukiwania celów"""
        search_goals = [
            ("Python Programming", "Learn Python basics"),
            ("JavaScript Course", "Master JS fundamentals"),
            ("Database Design", "Learn SQL and NoSQL"),
            ("Web Development", "Build responsive websites")
        ]

        for title, description in search_goals:
            goal = Goal(title, description, 100.0)
            self.goal_manager.add_goal(self.test_user, goal)

        # Test wyszukiwania po tytule
        python_results = self.goal_manager.search_goals(self.test_user, "Python")
        self.assertEqual(len(python_results), 1)
        self.assertIn("Python", python_results[0].title)

        # Test wyszukiwania po opisie
        learn_results = self.goal_manager.search_goals(self.test_user, "Learn")
        self.assertEqual(len(learn_results), 2)

    def test_goal_management_workflow(self):
        """Test 5: Scenariusz zarządzania celami"""
        goal = Goal("Management Test", "Opis", 100.0)
        self.goal_manager.add_goal(self.test_user, goal)

        # Test usuwania celu
        result = self.goal_manager.remove_goal(self.test_user, goal.id)
        self.assertTrue(result)

        # Sprawdzenie czy cel został usunięty
        user_goals = self.goal_manager.get_user_goals(self.test_user)
        self.assertEqual(len(user_goals), 0)

    def test_data_persistence_workflow(self):
        """Test 6: Scenariusz persistencji danych"""
        goal = Goal("Persistence Test", "Test zapisu", 100.0)
        self.goal_manager.add_goal(self.test_user, goal)

        # Zapis do pliku
        goals_data = [g.to_dict() for g in self.goal_manager.get_user_goals(self.test_user)]
        result = self.data_manager.save_goals_data(goals_data, self.test_user)
        self.assertTrue(result)

        # Odczyt z pliku
        loaded_data = self.data_manager.load_goals_data(self.test_user)
        self.assertEqual(len(loaded_data), 1)
        self.assertEqual(loaded_data[0]['title'], "Persistence Test")

    def test_goal_type_filtering_workflow(self):
        """Test 7: Scenariusz filtrowania według typu"""
        # Dodanie celów różnych typów
        goals = [
            Goal("Ogólny 1", "Opis", 100.0),
            Goal("Ogólny 2", "Opis", 100.0),
            PersonalGoal("Osobisty 1", "Opis", 100.0),
            BusinessGoal("Biznesowy 1", "Opis", 100.0)
        ]

        for goal in goals:
            self.goal_manager.add_goal(self.test_user, goal)

        # Test filtrowania
        general_goals = self.goal_manager.get_goals_by_type(self.test_user, "Ogólny")
        personal_goals = self.goal_manager.get_goals_by_type(self.test_user, "Osobisty")
        business_goals = self.goal_manager.get_goals_by_type(self.test_user, "Biznesowy")

        self.assertEqual(len(general_goals), 2)
        self.assertEqual(len(personal_goals), 1)
        self.assertEqual(len(business_goals), 1)

    def test_backup_and_restore_workflow(self):
        """Test 8: Scenariusz kopii zapasowej"""
        goal = Goal("Backup Test", "Test backup", 100.0)
        self.goal_manager.add_goal(self.test_user, goal)

        # Test tworzenia kopii zapasowej
        result = self.goal_manager.backup_data()
        self.assertTrue(result)

        # Sprawdzenie czy kopia została utworzona
        backup_list = self.data_manager.get_backup_list()
        self.assertGreater(len(backup_list), 0)

    def test_goal_completion_workflow(self):
        """Test 9: Scenariusz ukończenia celu z debugowaniem"""
        goal = Goal("Completion Test", "Test ukończenia", 100.0)
        self.goal_manager.add_goal(self.test_user, goal)

        progress_values = [25.0, 50.0, 75.0, 100.0]
        for i, progress in enumerate(progress_values):
            print(f"Aktualizacja {i + 1}: {progress}")
            result = self.goal_manager.update_goal_progress(self.test_user, goal.id, progress)
            self.assertTrue(result)

            # Sprawdź historię po każdej aktualizacji
            current_history = goal.get_history()
            print(f"Historia po aktualizacji {i + 1}: {len(current_history)} wpisów")

            # Oczekiwana liczba wpisów = i+1
            expected_count = i + 1
            self.assertEqual(len(current_history), expected_count,
                             f"Po aktualizacji {i + 1} oczekiwano {expected_count} wpisów, "
                             f"ale mamy {len(current_history)}")

        # Finalne sprawdzenie
        updated_goals = self.goal_manager.get_user_goals(self.test_user)
        completed_goal = updated_goals[0]

        history = completed_goal.get_history()
        print(f"Finalna historia: {len(history)} wpisów")
        print(f"Historia: {history}")

        self.assertEqual(len(history), 4)

    def test_multiple_users_isolation(self):
        """Test 10: Scenariusz izolacji między użytkownikami"""
        user1 = "user1"
        user2 = "user2"

        # Dodanie celów dla różnych użytkowników
        goal1 = Goal("User1 Goal", "Opis", 100.0)
        goal2 = Goal("User2 Goal", "Opis", 100.0)

        self.goal_manager.add_goal(user1, goal1)
        self.goal_manager.add_goal(user2, goal2)

        # Sprawdzenie izolacji
        user1_goals = self.goal_manager.get_user_goals(user1)
        user2_goals = self.goal_manager.get_user_goals(user2)

        self.assertEqual(len(user1_goals), 1)
        self.assertEqual(len(user2_goals), 1)
        self.assertEqual(user1_goals[0].title, "User1 Goal")
        self.assertEqual(user2_goals[0].title, "User2 Goal")


if __name__ == '__main__':
    unittest.main(verbosity=2)
