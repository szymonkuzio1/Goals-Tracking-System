"""
Testy jednostkowe dla modułu logiki
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from goal_tracker.logic import GoalManager
from goal_tracker.models.goal import Goal, PersonalGoal, BusinessGoal
from goal_tracker.models.progress import Progress


class TestGoalManager(unittest.TestCase):
    """
    Klasa testów dla GoalManager
    """

    def setUp(self):
        """Przygotowanie managera celów"""
        self.mock_data_manager = Mock()
        self.goal_manager = GoalManager(self.mock_data_manager)
        self.test_username = "test_user"

    def _create_test_goals(self, count=3):
        """Wewnętrzna metoda tworzenia testowych celów"""
        goals = []
        for i in range(count):
            goal = Goal(f"Test Goal {i + 1}", f"Description {i + 1}", 100.0, "Test")
            goal.update_progress(i * 20)  # 0, 20, 40 postępu
            goals.append(goal)
        return goals

    def test_add_goal_valid(self):
        """Test dodawania prawidłowego celu"""
        goal = Goal("Test Goal", "Test description", 100.0, "Test")

        result = self.goal_manager.add_goal(self.test_username, goal)
        self.assertTrue(result)

        # Sprawdzenie czy cel został dodany
        user_goals = self.goal_manager.get_user_goals(self.test_username)
        self.assertEqual(len(user_goals), 1)
        self.assertEqual(user_goals[0].title, "Test Goal")

    def test_add_goal_invalid_object(self):
        """Test dodawania nieprawidłowego obiektu jako cel"""
        result = self.goal_manager.add_goal(self.test_username, "not a goal")
        self.assertFalse(result)

    def test_add_goal_empty_username(self):
        """Test dodawania celu z pustą nazwą użytkownika"""
        goal = Goal("Test Goal", "Test description", 100.0, "Test")

        result = self.goal_manager.add_goal("", goal)
        self.assertFalse(result)

        result = self.goal_manager.add_goal("   ", goal)
        self.assertFalse(result)

    def test_goals_limit_enforcement(self):
        """Test egzekwowania limitu celów"""
        # Dodanie maksymalnej liczby celów
        for i in range(50):  # MAX_GOALS_PER_USER = 50
            goal = Goal(f"Goal {i}", "Description", 100.0, "Test")
            result = self.goal_manager.add_goal(self.test_username, goal)
            self.assertTrue(result)

        # Próba dodania 51. celu
        extra_goal = Goal("Extra Goal", "Description", 100.0, "Test")
        result = self.goal_manager.add_goal(self.test_username, extra_goal)
        self.assertFalse(result)

    def test_update_goal_progress_valid(self):
        """Test aktualizacji postępu celu"""
        goal = Goal("Test Goal", "Test description", 100.0, "Test")
        self.goal_manager.add_goal(self.test_username, goal)

        result = self.goal_manager.update_goal_progress(
            self.test_username, goal.id, 50.0, "Progress update"
        )
        self.assertTrue(result)

        # Sprawdzenie czy postęp został zaktualizowany
        user_goals = self.goal_manager.get_user_goals(self.test_username)
        updated_goal = user_goals[0]
        self.assertEqual(updated_goal.current_value, 50.0)

    def test_update_goal_progress_nonexistent_goal(self):
        """Test aktualizacji postępu nieistniejącego celu"""
        result = self.goal_manager.update_goal_progress(
            self.test_username, "nonexistent_id", 50.0
        )
        self.assertFalse(result)

    def test_update_goal_progress_invalid_value(self):
        """Test aktualizacji postępu z nieprawidłową wartością"""
        goal = Goal("Test Goal", "Test description", 100.0, "Test")
        self.goal_manager.add_goal(self.test_username, goal)

        # Test wartości ujemnej
        result = self.goal_manager.update_goal_progress(
            self.test_username, goal.id, -10.0
        )
        self.assertFalse(result)

    @patch('goal_tracker.logic.datetime')
    def test_progress_interval_enforcement(self, mock_datetime):
        """Test egzekwowania interwału między aktualizacjami"""
        # Ustawienie czasu
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = base_time

        goal = Goal("Test Goal", "Test description", 100.0, "Test")
        self.goal_manager.add_goal(self.test_username, goal)

        # Pierwsza aktualizacja
        result = self.goal_manager.update_goal_progress(
            self.test_username, goal.id, 25.0
        )
        self.assertTrue(result)

        # Próba aktualizacji za wcześnie (30 minut później)
        mock_datetime.now.return_value = base_time + timedelta(minutes=30)
        result = self.goal_manager.update_goal_progress(
            self.test_username, goal.id, 50.0
        )
        self.assertFalse(result)

        # Aktualizacja po odpowiednim czasie (2 godziny później)
        mock_datetime.now.return_value = base_time + timedelta(hours=2)
        result = self.goal_manager.update_goal_progress(
            self.test_username, goal.id, 50.0
        )
        self.assertTrue(result)

    def test_remove_goal(self):
        """Test usuwania celu"""
        goal = Goal("Test Goal", "Test description", 100.0, "Test")
        self.goal_manager.add_goal(self.test_username, goal)

        # Sprawdzenie czy cel istnieje
        user_goals = self.goal_manager.get_user_goals(self.test_username)
        self.assertEqual(len(user_goals), 1)

        # Usunięcie celu
        result = self.goal_manager.remove_goal(self.test_username, goal.id)
        self.assertTrue(result)

        # Sprawdzenie czy cel został usunięty
        user_goals = self.goal_manager.get_user_goals(self.test_username)
        self.assertEqual(len(user_goals), 0)

    def test_remove_nonexistent_goal(self):
        """Test usuwania nieistniejącego celu"""
        result = self.goal_manager.remove_goal(self.test_username, "nonexistent_id")
        self.assertFalse(result)

    def test_get_goals_by_category(self):
        """Test filtrowania celów według kategorii"""
        # Dodanie celów z różnymi kategoriami
        categories = ["Praca", "Zdrowie", "Praca", "Edukacja"]
        for i, category in enumerate(categories):
            goal = Goal(f"Goal {i}", "Description", 100.0, category)
            self.goal_manager.add_goal(self.test_username, goal)

        # Test filtrowania
        work_goals = self.goal_manager.get_goals_by_category(self.test_username, "Praca")
        self.assertEqual(len(work_goals), 2)

        health_goals = self.goal_manager.get_goals_by_category(self.test_username, "Zdrowie")
        self.assertEqual(len(health_goals), 1)

        # Test case insensitive
        work_goals_lower = self.goal_manager.get_goals_by_category(self.test_username, "praca")
        self.assertEqual(len(work_goals_lower), 2)

    def test_get_goals_by_status(self):
        """Test filtrowania celów według statusu"""
        goals = self._create_test_goals(3)

        for goal in goals:
            self.goal_manager.add_goal(self.test_username, goal)

        # Zmiana statusu jednego celu
        goals[1].status = "wstrzymany"

        # Test filtrowania
        active_goals = self.goal_manager.get_goals_by_status(self.test_username, "aktywny")
        self.assertEqual(len(active_goals), 2)

        paused_goals = self.goal_manager.get_goals_by_status(self.test_username, "wstrzymany")
        self.assertEqual(len(paused_goals), 1)

    def test_search_goals(self):
        """Test wyszukiwania celów"""
        # Dodanie testowych celów
        goals_data = [
            ("Nauka Pythona", "Nauka programowania w Pythonie"),
            ("Bieganie maraton", "Przygotowanie do maratonu"),
            ("Czytanie książek", "Przeczytanie 50 książek"),
            ("Python dla zaawansowanych", "Pogłębianie wiedzy o Python")
        ]

        for title, description in goals_data:
            goal = Goal(title, description, 100.0, "Test")
            self.goal_manager.add_goal(self.test_username, goal)

        # Test wyszukiwania po tytule
        python_goals = self.goal_manager.search_goals(self.test_username, "Python")
        self.assertEqual(len(python_goals), 2)

        # Test wyszukiwania po opisie
        reading_goals = self.goal_manager.search_goals(self.test_username, "książek")
        self.assertEqual(len(reading_goals), 1)

        # Test case insensitive
        running_goals = self.goal_manager.search_goals(self.test_username, "bieganie")
        self.assertEqual(len(running_goals), 1)

    def test_get_top_performing_goals(self):
        """Test pobierania najlepszych celów"""
        goals = self._create_test_goals(5)

        for goal in goals:
            self.goal_manager.add_goal(self.test_username, goal)

        # Test pobierania top 3
        top_goals = self.goal_manager.get_top_performing_goals(self.test_username, 3)
        self.assertEqual(len(top_goals), 3)

        # Sprawdzenie sortowania (najwyższy postęp pierwszy)
        self.assertGreaterEqual(top_goals[0][1], top_goals[1][1])
        self.assertGreaterEqual(top_goals[1][1], top_goals[2][1])

    def test_generate_recommendations(self):
        """Test generowania rekomendacji"""
        # Dodanie celów z różnym postępem
        goals_data = [
            ("Low Progress Goal 1", 5.0),  # Niski postęp
            ("Low Progress Goal 2", 10.0),  # Niski postęp
            ("Medium Progress Goal", 45.0),  # Średni postęp
            ("High Progress Goal", 85.0)  # Wysoki postęp
        ]

        for title, progress in goals_data:
            goal = Goal(title, "Description", 100.0, "Test")
            goal.update_progress(progress)
            self.goal_manager.add_goal(self.test_username, goal)

        # Ustawienie jednego celu jako wstrzymany
        user_goals = self.goal_manager.get_user_goals(self.test_username)
        user_goals[0].status = "wstrzymany"

        recommendations = self.goal_manager.generate_recommendations(self.test_username)

        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

        # Sprawdzenie czy rekomendacje zawierają oczekiwane treści
        recommendations_text = " ".join(recommendations)
        self.assertIn("niskim postępem", recommendations_text)
        self.assertIn("wstrzymanych", recommendations_text)

    def test_get_user_statistics(self):
        """Test pobierania statystyk użytkownika"""
        goals = self._create_test_goals(4)

        for goal in goals:
            self.goal_manager.add_goal(self.test_username, goal)

        # Oznaczenie jednego celu jako zakończony
        user_goals = self.goal_manager.get_user_goals(self.test_username)
        user_goals[0].status = "zakończony"

        stats = self.goal_manager.get_user_statistics(self.test_username)

        self.assertIn('total_goals', stats)
        self.assertIn('active_goals', stats)
        self.assertIn('completed_goals', stats)
        self.assertIn('average_progress', stats)

        self.assertEqual(stats['total_goals'], 4)
        self.assertEqual(stats['completed_goals'], 1)
        self.assertEqual(stats['active_goals'], 3)

    def test_backup_data(self):
        """Test tworzenia kopii zapasowej"""
        # Dodanie testowych danych
        goal = Goal("Test Goal", "Description", 100.0, "Test")
        self.goal_manager.add_goal(self.test_username, goal)

        # Mock metody save_backup
        self.mock_data_manager.save_backup.return_value = True

        result = self.goal_manager.backup_data()
        self.assertTrue(result)

        # Sprawdzenie czy save_backup został wywołany
        self.mock_data_manager.save_backup.assert_called_once()

    def test_get_system_health(self):
        """Test sprawdzania zdrowia systemu"""
        # Dodanie testowych danych
        goals = self._create_test_goals(3)
        for goal in goals:
            self.goal_manager.add_goal(self.test_username, goal)

        health = self.goal_manager.get_system_health()

        self.assertIn('status', health)
        self.assertIn('total_users', health)
        self.assertIn('total_goals', health)
        self.assertIn('average_system_progress', health)

        self.assertEqual(health['status'], 'healthy')
        self.assertEqual(health['total_users'], 1)
        self.assertEqual(health['total_goals'], 3)


class TestGoalManagerWithBusinessLogic(unittest.TestCase):
    """
    Testy logiki biznesowej dla różnych typów celów
    """

    def setUp(self):
        """Przygotowanie managera z różnymi typami celów"""
        self.goal_manager = GoalManager()
        self.test_username = "business_user"

    def test_business_goal_milestones(self):
        """Test obsługi kamieni milowych w celach biznesowych"""
        business_goal = BusinessGoal(
            "Wzrost sprzedaży", "Zwiększenie sprzedaży o 50%",
            50.0, "Sprzedaż", 100000.0
        )

        # Dodanie kamieni milowych
        business_goal.add_milestone("Pierwszy kwartał", 25.0)
        business_goal.add_milestone("Połowa roku", 50.0)
        business_goal.add_milestone("Trzeci kwartał", 75.0)

        self.goal_manager.add_goal(self.test_username, business_goal)

        # Aktualizacja postępu do 30% (powinien osiągnąć pierwszy milestone)
        result = self.goal_manager.update_goal_progress(
            self.test_username, business_goal.id, 15.0  # 30% z 50
        )
        self.assertTrue(result)

        # Sprawdzenie osiągnięć kamieni milowych
        achieved = business_goal.check_milestones()
        self.assertEqual(len(achieved), 1)
        self.assertIn("Pierwszy kwartał", achieved)

    def test_personal_goal_motivation(self):
        """Test obsługi motywacji w celach osobistych"""
        personal_goal = PersonalGoal(
            "Bieganie", "Biegać codziennie", 30.0, "wysoki", True
        )

        self.goal_manager.add_goal(self.test_username, personal_goal)

        # Dodanie notatek motywacyjnych
        personal_goal.add_motivation_note("Świetny start!")
        personal_goal.add_motivation_note("Czuję się coraz lepiej")

        # Sprawdzenie podsumowania motywacji
        summary = personal_goal.get_motivation_summary()
        self.assertIn("Czuję się coraz lepiej", summary)

    def test_mixed_goals_statistics(self):
        """Test statystyk dla mieszanych typów celów"""
        # Dodanie różnych typów celów
        goals = [
            Goal("Cel ogólny", "Opis", 100.0, "Ogólny"),
            PersonalGoal("Cel osobisty", "Opis", 100.0, "średni", False),
            BusinessGoal("Cel biznesowy", "Opis", 100.0, "IT", 50000.0)
        ]

        for goal in goals:
            goal.update_progress(30.0)  # 30% postępu dla każdego
            self.goal_manager.add_goal(self.test_username, goal)

        stats = self.goal_manager.get_user_statistics(self.test_username)

        self.assertEqual(stats['total_goals'], 3)
        self.assertAlmostEqual(stats['average_progress'], 30.0, places=1)

        # Sprawdzenie rozkładu kategorii
        category_dist = stats['category_distribution']
        self.assertIn('Ogólny', category_dist)
        self.assertIn('Osobisty', category_dist)
        self.assertIn('Biznesowy', category_dist)


if __name__ == '__main__':
    unittest.main(verbosity=2)
