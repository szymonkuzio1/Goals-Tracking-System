"""
Testy jednostkowe dla podstawowych klas systemu
"""
import unittest
from datetime import datetime
import tempfile
import shutil

from goal_tracker.models.goal import Goal, PersonalGoal, BusinessGoal
from goal_tracker.models.progress import Progress
from goal_tracker.logic import GoalManager
from goal_tracker.data import DataManager


class TestGoalModels(unittest.TestCase):
    """Testy jednostkowe modeli celów"""

    def test_goal_creation_valid(self):
        """Test 1: Tworzenie celu z prawidłowymi danymi"""
        goal = Goal("Test Goal", "Description", 100.0)

        self.assertEqual(goal.title, "Test Goal")
        self.assertEqual(goal.description, "Description")
        self.assertEqual(goal.target_value, 100.0)
        self.assertEqual(goal.current_value, 0.0)
        self.assertEqual(goal.status, "aktywny")
        self.assertIsNotNone(goal.id)
        self.assertEqual(goal.get_goal_type(), "Ogólny")

    def test_goal_creation_invalid_title(self):
        """Test 2: Tworzenie celu z nieprawidłowym tytułem"""
        with self.assertRaises(AssertionError):
            Goal("", "Description", 100.0)

        with self.assertRaises(AssertionError):
            Goal("   ", "Description", 100.0)

    def test_goal_creation_invalid_target(self):
        """Test 3: Tworzenie celu z nieprawidłową wartością docelową"""
        with self.assertRaises(AssertionError):
            Goal("Title", "Description", 0.0)

        with self.assertRaises(AssertionError):
            Goal("Title", "Description", -10.0)

    def test_personal_goal_type(self):
        """Test 4: Sprawdzenie typu celu osobistego"""
        goal = PersonalGoal("Personal Goal", "Description", 100.0)
        self.assertEqual(goal.get_goal_type(), "Osobisty")

    def test_business_goal_type(self):
        """Test 5: Sprawdzenie typu celu biznesowego"""
        goal = BusinessGoal("Business Goal", "Description", 100.0)
        self.assertEqual(goal.get_goal_type(), "Biznesowy")

    def test_goal_progress_update(self):
        """Test 6: Aktualizacja postępu celu"""
        goal = Goal("Test", "Desc", 100.0)

        result = goal.update_progress(50.0)
        self.assertTrue(result)
        self.assertEqual(goal.current_value, 50.0)

        # Test historii
        history = goal.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['new_value'], 50.0)

    def test_goal_completion(self):
        """Test 7: Automatyczne oznaczanie celu jako zakończony"""
        goal = Goal("Test", "Desc", 100.0)

        goal.update_progress(100.0)
        self.assertEqual(goal.status, "zakończony")

        goal2 = Goal("Test2", "Desc", 100.0)
        goal2.update_progress(150.0)
        self.assertEqual(goal2.status, "zakończony")

    def test_goal_progress_percentage(self):
        """Test 8: Obliczanie procentowego postępu"""
        goal = Goal("Test", "Desc", 100.0)

        self.assertEqual(goal.get_progress_percentage(), 0.0)

        goal.update_progress(25.0)
        self.assertEqual(goal.get_progress_percentage(), 25.0)

        goal.update_progress(150.0)
        self.assertEqual(goal.get_progress_percentage(), 100.0)  # Max 100%

    def test_goal_to_dict(self):
        """Test 9: Konwersja celu do słownika"""
        goal = Goal("Test", "Desc", 100.0)
        goal.update_progress(25.0)

        goal_dict = goal.to_dict()

        required_keys = ['id', 'title', 'description', 'target_value',
                         'current_value', 'goal_type', 'status', 'created_date']
        for key in required_keys:
            self.assertIn(key, goal_dict)

        self.assertEqual(goal_dict['goal_type'], "Ogólny")
        self.assertEqual(goal_dict['current_value'], 25.0)

    def test_progress_model(self):
        """Test 10: Model Progress"""
        progress = Progress("goal123", 25.5, "Test note")

        self.assertEqual(progress.goal_id, "goal123")
        self.assertEqual(progress.value, 25.5)
        self.assertEqual(progress.note, "Test note")
        self.assertIsNotNone(progress.id)
        self.assertIsInstance(progress.timestamp, datetime)


if __name__ == '__main__':
    unittest.main(verbosity=2)
