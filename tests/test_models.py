"""
Testy jednostkowe dla modeli danych
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from goal_tracker.models.goal import Goal, PersonalGoal, BusinessGoal
from goal_tracker.models.progress import Progress

class TestGoalModel(unittest.TestCase):
    """
    Klasa testów dla modelu Goal
    """

    def setUp(self):
        """Przygotowanie danych testowych"""
        self.test_title = "Test Goal"
        self.test_description = "Test description"
        self.test_target = 100.0
        self.test_category = "Test Category"

    def _create_test_goal(self, title=None, target=None):
        """Wewnętrzna metoda tworzenia testowego celu"""
        return Goal(
            title or self.test_title,
            self.test_description,
            target or self.test_target,
            self.test_category
        )

    def test_goal_creation_valid_data(self):
        """Test tworzenia celu z prawidłowymi danymi"""
        goal = self._create_test_goal()

        # Asercje sprawdzające podstawowe właściwości
        self.assertEqual(goal.title, self.test_title)
        self.assertEqual(goal.description, self.test_description)
        self.assertEqual(goal.target_value, self.test_target)
        self.assertEqual(goal.current_value, 0.0)
        self.assertEqual(goal.status, "aktywny")
        self.assertIsNotNone(goal.id)

    def test_goal_creation_invalid_title(self):
        """Test tworzenia celu z nieprawidłowym tytułem"""
        # Test pustego tytułu
        with self.assertRaises(AssertionError):
            Goal("", self.test_description, self.test_target)

        # Test tytułu tylko ze spacjami
        with self.assertRaises(AssertionError):
            Goal("   ", self.test_description, self.test_target)

    def test_goal_creation_invalid_target_value(self):
        """Test tworzenia celu z nieprawidłową wartością docelową"""
        # Test wartości zerowej
        with self.assertRaises(AssertionError):
            Goal(self.test_title, self.test_description, 0)

        # Test wartości ujemnej
        with self.assertRaises(AssertionError):
            Goal(self.test_title, self.test_description, -10)

    def test_update_progress_valid(self):
        """Test aktualizacji postępu z prawidłowymi danymi"""
        goal = self._create_test_goal()

        # Test aktualizacji postępu
        result = goal.update_progress(25.0)
        self.assertTrue(result)
        self.assertEqual(goal.current_value, 25.0)

        # Sprawdzenie historii
        history = goal.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['old_value'], 0.0)
        self.assertEqual(history[0]['new_value'], 25.0)

    def test_update_progress_invalid(self):
        """Test aktualizacji postępu z nieprawidłowymi danymi"""
        goal = self._create_test_goal()

        # Test wartości ujemnej
        result = goal.update_progress(-10.0)
        self.assertFalse(result)
        self.assertEqual(goal.current_value, 0.0)

    def test_goal_completion(self):
        """Test automatycznego oznaczania celu jako zakończony"""
        goal = self._create_test_goal()

        # Aktualizacja do 100% postępu
        goal.update_progress(100.0)
        self.assertEqual(goal.status, "zakończony")

        # Test przekroczenia celu
        goal2 = self._create_test_goal()
        goal2.update_progress(150.0)
        self.assertEqual(goal2.status, "zakończony")

    def test_progress_percentage_calculation(self):
        """Test obliczania procentowego postępu"""
        goal = self._create_test_goal()

        # Test 0% postępu
        self.assertEqual(goal.get_progress_percentage(), 0.0)

        # Test 50% postępu
        goal.update_progress(50.0)
        self.assertEqual(goal.get_progress_percentage(), 50.0)

        # Test 100% postępu
        goal.update_progress(100.0)
        self.assertEqual(goal.get_progress_percentage(), 100.0)

        # Test przekroczenia 100%
        goal.update_progress(150.0)
        self.assertEqual(goal.get_progress_percentage(), 100.0)  # Max 100%

    def test_goal_to_dict(self):
        """Test konwersji celu do słownika"""
        goal = self._create_test_goal()
        goal.update_progress(25.0)

        goal_dict = goal.to_dict()

        # Sprawdzenie kluczy
        required_keys = ['id', 'title', 'description', 'target_value',
                         'current_value', 'category', 'status', 'created_date']
        for key in required_keys:
            self.assertIn(key, goal_dict)

        # Sprawdzenie wartości
        self.assertEqual(goal_dict['title'], self.test_title)
        self.assertEqual(goal_dict['current_value'], 25.0)


class TestPersonalGoal(unittest.TestCase):
    """
    Klasa testów dla PersonalGoal
    """

    def setUp(self):
        """Przygotowanie danych testowych"""
        self.personal_goal = PersonalGoal(
            "Bieganie", "Biegać 5km dziennie", 100.0, "wysoki", True
        )

    def test_personal_goal_creation(self):
        """Test tworzenia celu osobistego"""
        self.assertEqual(self.personal_goal.category, "Osobisty")
        self.assertEqual(self.personal_goal.priority, "wysoki")
        self.assertTrue(self.personal_goal.is_habit)

    def test_add_motivation_note(self):
        """Test dodawania notatek motywacyjnych"""
        note = "Świetny trening dzisiaj!"
        self.personal_goal.add_motivation_note(note)

        summary = self.personal_goal.get_motivation_summary()
        self.assertIn(note, summary)

    def test_empty_motivation_note(self):
        """Test dodawania pustej notatki motywacyjnej"""
        self.personal_goal.add_motivation_note("")
        self.personal_goal.add_motivation_note("   ")

        summary = self.personal_goal.get_motivation_summary()
        self.assertEqual(summary, "Brak notatek motywacyjnych")


class TestBusinessGoal(unittest.TestCase):
    """
    Klasa testów dla BusinessGoal
    """

    def setUp(self):
        """Przygotowanie danych testowych"""
        self.business_goal = BusinessGoal(
            "Zwiększenie sprzedaży", "Zwiększyć sprzedaż o 20%",
            120.0, "Sprzedaż", 50000.0
        )

    def test_business_goal_creation(self):
        """Test tworzenia celu biznesowego"""
        self.assertEqual(self.business_goal.category, "Biznesowy")
        self.assertEqual(self.business_goal.department, "Sprzedaż")
        self.assertEqual(self.business_goal.budget, 50000.0)

    def test_add_stakeholder(self):
        """Test dodawania interesariuszy"""
        stakeholders = ["Jan Kowalski", "Anna Nowak", "Piotr Wiśniewski"]

        for stakeholder in stakeholders:
            self.business_goal.add_stakeholder(stakeholder)

        goal_stakeholders = self.business_goal.get_stakeholders()
        self.assertEqual(len(goal_stakeholders), 3)

        # Test użycie set() - duplikaty są ignorowane
        self.business_goal.add_stakeholder("Jan Kowalski")
        self.assertEqual(len(self.business_goal.get_stakeholders()), 3)

    def test_milestones_management(self):
        """Test zarządzania kamieniami milowymi"""
        # Dodanie kamieni milowych
        self.business_goal.add_milestone("Pierwsze 25%", 25.0)
        self.business_goal.add_milestone("Połowa drogi", 50.0)
        self.business_goal.add_milestone("Prawie koniec", 75.0)

        # Test nieprawidłowego procentu
        with self.assertRaises(AssertionError):
            self.business_goal.add_milestone("Nieprawidłowy", 150.0)

        # Test sprawdzania osiągnięć
        self.business_goal.update_progress(30.0)  # 25% postępu
        achieved = self.business_goal.check_milestones()

        self.assertEqual(len(achieved), 1)
        self.assertIn("Pierwsze 25%", achieved)


class TestProgressModel(unittest.TestCase):
    """
    Klasa testów dla modelu Progress
    """

    def test_progress_creation(self):
        """Test tworzenia wpisu postępu"""
        progress = Progress("goal123", 25.5, "Dobry postęp")

        self.assertEqual(progress.goal_id, "goal123")
        self.assertEqual(progress.value, 25.5)
        self.assertEqual(progress.note, "Dobry postęp")
        self.assertIsNotNone(progress.id)
        self.assertIsInstance(progress.timestamp, datetime)

    def test_progress_invalid_data(self):
        """Test tworzenia postępu z nieprawidłowymi danymi"""
        # Puste ID celu
        with self.assertRaises(AssertionError):
            Progress("", 25.0)

        # Ujemna wartość
        with self.assertRaises(AssertionError):
            Progress("goal123", -5.0)

    def test_progress_formatting(self):
        """Test formatowania wpisu postępu"""
        progress = Progress("goal123", 25.5, "Test note")
        formatted = progress.get_formatted_entry()

        self.assertIn("25.5", formatted)
        self.assertIn("Test note", formatted)
        self.assertIn(progress.timestamp.strftime("%Y-%m-%d"), formatted)

if __name__ == '__main__':
    # Uruchomienie wszystkich testów
    unittest.main(verbosity=2)
