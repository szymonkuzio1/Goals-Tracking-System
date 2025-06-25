"""
Testy integracyjne - współpraca między modułami
"""
import unittest
import tempfile
import shutil
import json
from unittest.mock import patch
from datetime import datetime

from goal_tracker.logic import GoalManager
from goal_tracker.data import DataManager
from goal_tracker.api import APIManager
from goal_tracker.models.goal import Goal, PersonalGoal, BusinessGoal


class TestSystemIntegration(unittest.TestCase):
    """Testy integracyjne całego systemu"""

    def setUp(self):
        """Przygotowanie kompletnego środowiska"""
        self.test_dir = tempfile.mkdtemp()
        self.data_manager = DataManager(self.test_dir)
        self.goal_manager = GoalManager(self.data_manager, max_goals=1000)
        self.api_manager = APIManager(self.data_manager, self.goal_manager)
        self.test_user = "default"

    def tearDown(self):
        """Czyszczenie po testach"""
        if self.test_dir:
            shutil.rmtree(self.test_dir)

    def test_full_system_workflow(self):
        """Test 1: Kompletny workflow systemu"""
        # 1. Dodanie celów przez GoalManager
        goals = [
            Goal("System Test 1", "Opis 1", 100.0),
            PersonalGoal("System Test 2", "Opis 2", 50.0),
            BusinessGoal("System Test 3", "Opis 3", 200.0)
        ]

        for goal in goals:
            result = self.goal_manager.add_goal(self.test_user, goal)
            self.assertTrue(result)

        # 2. Zapis przez DataManager
        user_goals = self.goal_manager.get_user_goals(self.test_user)
        goals_data = [goal.to_dict() for goal in user_goals]
        save_result = self.data_manager.save_goals_data(goals_data, self.test_user)
        self.assertTrue(save_result)

        # 3. Odczyt i weryfikacja
        loaded_data = self.data_manager.load_goals_data(self.test_user)
        self.assertEqual(len(loaded_data), 3)

        # 4. Eksport przez API
        export_result = self.api_manager.export_goals_to_json()
        self.assertTrue(export_result['success'])
        self.assertEqual(len(export_result['data']['goals']), 3)

    def test_data_manager_goal_manager_integration(self):
        """Test 2: Integracja DataManager z GoalManager"""
        # Utworzenie celu w GoalManager
        goal = Goal("Integration Test", "Test integracji", 100.0)
        self.goal_manager.add_goal(self.test_user, goal)

        # Zapis przez DataManager
        goals = self.goal_manager.get_user_goals(self.test_user)
        goals_data = [g.to_dict() for g in goals]
        self.data_manager.save_goals_data(goals_data, self.test_user)

        # Nowy GoalManager - symulacja restartu
        new_goal_manager = GoalManager(self.data_manager)
        new_goal_manager.load_goals_from_data_manager(self.test_user)

        # Sprawdzenie czy dane zostały załadowane
        loaded_goals = new_goal_manager.get_user_goals(self.test_user)
        self.assertEqual(len(loaded_goals), 1)
        self.assertEqual(loaded_goals[0].title, "Integration Test")

    def test_backup_restore_integration(self):
        """Test 3: Integracja kopii zapasowej z przywracaniem"""
        # Dodanie danych
        goals = [
            Goal("Backup Test 1", "Opis 1", 100.0),
            Goal("Backup Test 2", "Opis 2", 200.0)
        ]

        for goal in goals:
            self.goal_manager.add_goal(self.test_user, goal)

        # Zapis i backup
        user_goals = self.goal_manager.get_user_goals(self.test_user)
        goals_data = [g.to_dict() for g in user_goals]
        self.data_manager.save_goals_data(goals_data, self.test_user)

        backup_result = self.goal_manager.backup_data()
        self.assertTrue(backup_result)

        # Sprawdzenie listy kopii
        backup_list = self.data_manager.get_backup_list()
        self.assertGreater(len(backup_list), 0)

        # Test przywracania
        latest_backup = backup_list[0]['filename']
        restore_result = self.data_manager.restore_from_backup(latest_backup)
        self.assertTrue(restore_result)

    def test_multiple_format_export_integration(self):
        """Test 4: Integracja eksportu w różnych formatach"""
        # Dodanie celów
        goal = Goal("Export Test", "Test eksportu", 100.0)
        goal.update_progress(50.0)
        self.goal_manager.add_goal(self.test_user, goal)

        # Eksport JSON
        json_result = self.api_manager.export_goals_to_json()
        self.assertTrue(json_result['success'])
        self.assertIn('goals', json_result['data'])

        # Eksport CSV
        csv_result = self.api_manager.export_goals_to_csv()
        self.assertTrue(csv_result['success'])
        self.assertIn('title', csv_result['data'])
        self.assertIn('Export Test', csv_result['data'])

        # Eksport XML
        xml_result = self.api_manager.export_goals_to_xml()
        self.assertTrue(xml_result['success'])
        self.assertIn('<goal>', xml_result['data'])

    def test_data_validation_integration(self):
        """Test 5: Integracja walidacji danych"""
        # Test dodania nieprawidłowego celu
        with self.assertRaises(AssertionError):
            invalid_goal = Goal("", "Opis", 100.0)  # Pusty tytuł

        with self.assertRaises(AssertionError):
            invalid_goal = Goal("Tytuł", "Opis", -10.0)  # Ujemna wartość

        # Test prawidłowego celu
        valid_goal = Goal("Valid Goal", "Prawidłowy cel", 100.0)
        result = self.goal_manager.add_goal(self.test_user, valid_goal)
        self.assertTrue(result)

    def test_goal_type_system_integration(self):
        """Test 6: Integracja systemu typów celów"""
        # Dodanie różnych typów
        goals = [
            Goal("General", "Opis", 100.0),
            PersonalGoal("Personal", "Opis", 100.0),
            BusinessGoal("Business", "Opis", 100.0)
        ]

        for goal in goals:
            self.goal_manager.add_goal(self.test_user, goal)

        # Test filtrowania według typu
        general_goals = self.goal_manager.get_goals_by_type(self.test_user, "Ogólny")
        personal_goals = self.goal_manager.get_goals_by_type(self.test_user, "Osobisty")
        business_goals = self.goal_manager.get_goals_by_type(self.test_user, "Biznesowy")

        self.assertEqual(len(general_goals), 1)
        self.assertEqual(len(personal_goals), 1)
        self.assertEqual(len(business_goals), 1)

        # Test eksportu z typami
        export_result = self.api_manager.export_goals_to_json()
        exported_goals = export_result['data']['goals']

        goal_types = [goal['goal_type'] for goal in exported_goals]
        self.assertIn('Ogólny', goal_types)
        self.assertIn('Osobisty', goal_types)
        self.assertIn('Biznesowy', goal_types)

    def test_concurrent_operations_simulation(self):
        """Test 7: Symulacja operacji współbieżnych"""
        # Symulacja wielu operacji
        users = ["user1", "user2", "user3"]

        for user in users:
            for i in range(3):
                goal = Goal(f"Goal {i} for {user}", f"Opis {i}", 100.0)
                result = self.goal_manager.add_goal(user, goal)
                self.assertTrue(result)

        # Sprawdzenie izolacji danych
        for user in users:
            user_goals = self.goal_manager.get_user_goals(user)
            self.assertEqual(len(user_goals), 3)

            # Sprawdzenie że cele należą do właściwego użytkownika
            for goal in user_goals:
                self.assertIn(user, goal.title)

        # Test zapisu wszystkich użytkowników
        for user in users:
            goals = self.goal_manager.get_user_goals(user)
            goals_data = [g.to_dict() for g in goals]
            result = self.data_manager.save_goals_data(goals_data, user)
            self.assertTrue(result)

    def test_system_recovery_integration(self):
        """Test 8: Integracja odzyskiwania systemu"""
        # Dodanie danych
        goal = Goal("Recovery Test", "Test odzyskiwania", 100.0)
        goal.update_progress(50.0)
        add_result = self.goal_manager.add_goal(self.test_user, goal)
        self.assertTrue(add_result, "Nie udało się dodać celu")

        # Sprawdzenie czy cel został dodany
        initial_goals = self.goal_manager.get_user_goals(self.test_user)
        self.assertEqual(len(initial_goals), 1, "Cel nie został dodany")

        # Zapis z obsługą błędów serializacji
        try:
            goals_data = []
            for g in initial_goals:
                goal_dict = g.to_dict()
                # Test serializacji
                json.dumps(goal_dict, default=str)
                goals_data.append(goal_dict)

            save_result = self.data_manager.save_goals_data(goals_data, self.test_user)
            self.assertTrue(save_result, "Nie udało się zapisać danych")

        except Exception as e:
            self.fail(f"Błąd przygotowania danych do zapisu: {e}")

        # Symulacja awarii - nowy system
        try:
            new_data_manager = DataManager(self.test_dir)
            new_goal_manager = GoalManager(new_data_manager, max_goals=1000)

            # Próba załadowania
            load_result = new_goal_manager.load_goals_from_data_manager(self.test_user)
            recovered_goals = new_goal_manager.get_user_goals(self.test_user)

            # Obsługa pustej listy
            if len(recovered_goals) == 0:
                # Sprawdź zawartość pliku dla debugowania
                if new_data_manager.goals_file.exists():
                    with open(new_data_manager.goals_file, 'r') as f:
                        content = f.read()
                        print(f"DEBUG - zawartość pliku: {content}")

                self.fail("Nie udało się odzyskać żadnych celów")

            # Sprawdzenie poprawności odzyskanych danych
            self.assertEqual(len(recovered_goals), 1)
            self.assertEqual(recovered_goals[0].title, "Recovery Test")
            self.assertEqual(recovered_goals[0].current_value, 50.0)

        except Exception as e:
            self.fail(f"Błąd podczas odzyskiwania systemu: {e}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
