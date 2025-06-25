"""
Testy graniczne i błędne dane
"""
import unittest
import tempfile
import shutil
import json
from unittest.mock import patch, mock_open

from goal_tracker.models.goal import Goal, PersonalGoal, BusinessGoal
from goal_tracker.logic import GoalManager
from goal_tracker.data import DataManager
from goal_tracker.api import APIManager


class TestEdgeCases(unittest.TestCase):
    """Testy przypadków granicznych i błędnych danych"""

    def setUp(self):
        """Przygotowanie środowiska"""
        self.test_dir = tempfile.mkdtemp()
        self.data_manager = DataManager(self.test_dir)
        self.goal_manager = GoalManager(self.data_manager, max_goals=1000)
        self.api_manager = APIManager(self.data_manager, self.goal_manager)
        self.test_user = "default"

    def tearDown(self):
        """Czyszczenie"""
        if self.test_dir:
            shutil.rmtree(self.test_dir)

    def test_extreme_values_goals(self):
        """Test 1: Wartości ekstremalne dla celów"""
        # Test bardzo małych wartości
        tiny_goal = Goal("Tiny Goal", "Opis", 0.01)
        result = self.goal_manager.add_goal(self.test_user, tiny_goal)
        self.assertTrue(result)

        # Test bardzo dużych wartości
        huge_goal = Goal("Huge Goal", "Opis", 999999.99)
        result = self.goal_manager.add_goal(self.test_user, huge_goal)
        self.assertTrue(result)

        # Test granicy walidacji
        from goal_tracker.utils.validators import validate_goal_data
        large_goal_data = {
            'title': 'Large Goal',
            'description': 'Opis',
            'target_value': 1000001.0  # Powyżej ewentualnego limitu
        }

        is_valid, errors = validate_goal_data(large_goal_data)
        # Sprawdź czy walidacja ma jakieś limity
        if not is_valid:
            print(f"Walidacja odrzuciła dużą wartość: {errors}")

        # Test poprawnego celu na granicy
        valid_goal = Goal("Valid Large Goal", "Opis", 500000.0)
        result = self.goal_manager.add_goal(self.test_user, valid_goal)
        self.assertTrue(result)

    def test_unicode_and_special_characters(self):
        """Test 2: Znaki Unicode i specjalne"""
        # Test znaków Unicode
        unicode_goal = Goal("Cel 🎯 z emoji", "Opis z ąęćłńóśźż", 100.0)
        result = self.goal_manager.add_goal(self.test_user, unicode_goal)
        self.assertTrue(result)

        # Test długich tytułów w dozwolonym zakresie
        long_title = "A" * 100  # Dokładnie 100 znaków
        long_goal = Goal(long_title, "Poprawny opis", 100.0)  # ← Niepusty opis
        result = self.goal_manager.add_goal(self.test_user, long_goal)
        self.assertTrue(result)

        # Test z minimalnym opisem
        minimal_desc_goal = Goal("Tytuł minimalny", "X", 100.0)  # ← Minimalny opis (1 znak)
        result = self.goal_manager.add_goal(self.test_user, minimal_desc_goal)
        self.assertTrue(result)

        # Sprawdzenie że za długi tytuł jest odrzucany
        from goal_tracker.utils.validators import validate_goal_data
        long_goal_data = {
            'title': 'A' * 150,  # Za długi tytuł
            'description': 'Poprawny opis',  # ← Niepusty opis
            'target_value': 100.0
        }

        is_valid, errors = validate_goal_data(long_goal_data)
        self.assertFalse(is_valid)

    def test_boundary_progress_values(self):
        """Test 3: Graniczne wartości postępu"""
        goal = Goal("Progress Test", "Opis", 100.0)
        self.goal_manager.add_goal(self.test_user, goal)

        # Test wartości 0
        result = self.goal_manager.update_goal_progress(self.test_user, goal.id, 0.0)
        self.assertTrue(result)

        # Test wartości ujemnej (powinno być odrzucone)
        result = self.goal_manager.update_goal_progress(self.test_user, goal.id, -1.0)
        self.assertFalse(result)

        # Test wartości przekraczającej cel
        result = self.goal_manager.update_goal_progress(self.test_user, goal.id, 150.0)
        self.assertTrue(result)

        # Test bardzo dużej wartości
        result = self.goal_manager.update_goal_progress(self.test_user, goal.id, 1000000.0)
        self.assertFalse(result)  # Powinno być odrzucone przez walidację

    def test_corrupted_json_files(self):
        """Test 4: Uszkodzone pliki JSON"""
        goal = Goal("JSON Test", "Opis", 100.0)
        self.goal_manager.add_goal(self.test_user, goal)

        # Zapis prawidłowych danych
        goals = self.goal_manager.get_user_goals(self.test_user)
        goals_data = [g.to_dict() for g in goals]
        self.data_manager.save_goals_data(goals_data, self.test_user)

        # Uszkodzenie pliku JSON
        with open(self.data_manager.goals_file, 'w') as f:
            f.write("{ invalid json content")

        # Test odczytu uszkodzonego pliku
        loaded_data = self.data_manager.load_goals_data(self.test_user)
        self.assertEqual(loaded_data, [])  # Powinien zwrócić pustą listę

    def test_empty_and_nonexistent_files(self):
        """Test 5: Puste i nieistniejące pliki"""
        # Test nieistniejącego pliku
        loaded_data = self.data_manager.load_goals_data(self.test_user)
        self.assertEqual(loaded_data, [])

        # Test pustego pliku
        self.data_manager.goals_file.touch()  # Utworzenie pustego pliku
        loaded_data = self.data_manager.load_goals_data(self.test_user)
        self.assertEqual(loaded_data, [])

        # Test pliku z pustym obiektem JSON
        with open(self.data_manager.goals_file, 'w') as f:
            json.dump({}, f)
        loaded_data = self.data_manager.load_goals_data(self.test_user)
        self.assertEqual(loaded_data, [])

    def test_invalid_api_import_data(self):
        """Test 6: Nieprawidłowe dane importu API"""
        # Test pustych danych
        result = self.api_manager.import_goals_from_json({})
        self.assertFalse(result['success'])

        # Test nieprawidłowej struktury
        invalid_data = {"invalid": "structure"}
        result = self.api_manager.import_goals_from_json(invalid_data)
        self.assertFalse(result['success'])

        # Test celów z brakującymi polami
        incomplete_data = {
            "goals": [
                {"title": "Incomplete Goal"},  # Brak description i target_value
                {"description": "No title", "target_value": 100.0}  # Brak title
            ]
        }
        result = self.api_manager.import_goals_from_json(incomplete_data)
        self.assertEqual(result['imported_successfully'], 0)

    def test_goal_manager_limits(self):
        """Test 7: Limity GoalManager"""
        # Utworzenie managera z małym limitem dla tego testu
        limited_manager = GoalManager(self.data_manager, max_goals=3)  # Mały limit!

        # Dodanie maksymalnej liczby celów (3)
        for i in range(3):
            goal = Goal(f"Goal {i}", f"Opis {i}", 100.0)
            result = limited_manager.add_goal(self.test_user, goal)
            self.assertTrue(result)

        # Próba dodania kolejnego celu (4-ty - powinno być odrzucone)
        extra_goal = Goal("Extra Goal", "Opis", 100.0)
        result = limited_manager.add_goal(self.test_user, extra_goal)
        self.assertFalse(result)  # Teraz POWINNO być False

        # Sprawdzenie że są dokładnie 3 cele
        goals = limited_manager.get_user_goals(self.test_user)
        self.assertEqual(len(goals), 3)

    def test_nonexistent_goal_operations(self):
        """Test 8: Operacje na nieistniejących celach"""
        fake_id = "nonexistent_goal_id_123"

        # Test aktualizacji nieistniejącego celu
        result = self.goal_manager.update_goal_progress(self.test_user, fake_id, 50.0)
        self.assertFalse(result)

        # Test usuwania nieistniejącego celu
        result = self.goal_manager.remove_goal(self.test_user, fake_id)
        self.assertFalse(result)

    def test_invalid_date_formats(self):
        """Test 9: Nieprawidłowe formaty dat"""
        from goal_tracker.utils.validators import validate_date_format

        # Test nieprawidłowych formatów
        invalid_dates = [
            "2025-13-32",  # Nieprawidłowy miesiąc i dzień
            "2025/02/30",  # Nieprawidłowy dzień dla lutego
            "not-a-date",  # Nie jest datą
            "2025-02-",  # Niekompletna data
            ""  # Pusta data
        ]

        for invalid_date in invalid_dates:
            is_valid, message = validate_date_format(invalid_date)
            self.assertFalse(is_valid)
            self.assertIsInstance(message, str)

    def test_memory_intensive_operations(self):
        """Test 10: Operacje intensywne pamięciowo"""
        # Test z dużą liczbą celów
        large_number = 1000
        goals_data = []

        for i in range(large_number):
            goal_dict = {
                'id': f'goal_{i}',
                'title': f'Large Test Goal {i}',
                'description': f'Description for goal {i}' * 10,  # Długi opis
                'target_value': 100.0,
                'current_value': float(i % 100),
                'goal_type': 'Ogólny',
                'status': 'aktywny',
                'created_date': '2025-01-01T00:00:00',
                'deadline': None,
                'history': []
            }
            goals_data.append(goal_dict)

        # Test zapisu dużej ilości danych
        result = self.data_manager.save_goals_data(goals_data, self.test_user)
        self.assertTrue(result)

        # Test odczytu dużej ilości danych
        loaded_data = self.data_manager.load_goals_data(self.test_user)
        self.assertEqual(len(loaded_data), large_number)


if __name__ == '__main__':
    unittest.main(verbosity=2)
