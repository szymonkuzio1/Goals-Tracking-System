"""
Testy jednostkowe dla modułu zarządzania danymi
"""
import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
from pathlib import Path

from goal_tracker.data import DataManager
from goal_tracker.models.goal import Goal


class TestDataManager(unittest.TestCase):
    """
    Klasa testów dla DataManager
    """

    def setUp(self):
        """Przygotowanie środowiska testowego"""
        # Utworzenie tymczasowego katalogu
        self.test_dir = tempfile.mkdtemp()
        self.data_manager = DataManager(self.test_dir)

        # Testowe dane
        self.test_goal_data = {
            'id': 'test_goal_1',
            'title': 'Test Goal',
            'description': 'Test description',
            'target_value': 100.0,
            'current_value': 50.0,
            'category': 'Test',
            'status': 'aktywny',
            'created_date': datetime.now().isoformat()
        }

        self.test_user_data = {
            'id': 'test_user_1',
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'created_date': datetime.now().isoformat()
        }

    def tearDown(self):
        """Czyszczenie po testach"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_initialize_directories(self):
        """Test inicjalizacji katalogów"""
        # Sprawdzenie czy katalogi zostały utworzone
        self.assertTrue(self.data_manager.data_dir.exists())
        self.assertTrue(self.data_manager.backup_dir.exists())
        self.assertTrue(self.data_manager.export_dir.exists())

    def test_save_goals_data_valid(self):
        """Test zapisu prawidłowych danych celów"""
        goals_data = [self.test_goal_data]
        username = "testuser"

        result = self.data_manager.save_goals_data(goals_data, username)
        self.assertTrue(result)

        # Sprawdzenie czy plik został utworzony
        self.assertTrue(self.data_manager.goals_file.exists())

        # Sprawdzenie zawartości pliku
        with open(self.data_manager.goals_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        self.assertIn(username, saved_data)
        self.assertEqual(len(saved_data[username]), 1)
        self.assertEqual(saved_data[username][0]['title'], 'Test Goal')

    def test_save_goals_data_invalid(self):
        """Test zapisu nieprawidłowych danych celów"""
        # Test z nieprawidłowym typem danych
        result = self.data_manager.save_goals_data("not a list", "testuser")
        self.assertFalse(result)

        # Test z niepełnymi danymi celu
        incomplete_goal = {'title': 'Incomplete Goal'}  # Brak wymaganych pól
        result = self.data_manager.save_goals_data([incomplete_goal], "testuser")
        self.assertTrue(result)  # Powinien kontynuować, ale pominąć niepełny cel

    def test_load_goals_data_existing_file(self):
        """Test odczytu istniejącego pliku celów"""
        # Najpierw zapisz dane
        goals_data = [self.test_goal_data]
        username = "testuser"
        self.data_manager.save_goals_data(goals_data, username)

        # Następnie odczytaj
        loaded_data = self.data_manager.load_goals_data(username)

        self.assertEqual(len(loaded_data), 1)
        self.assertEqual(loaded_data[0]['title'], 'Test Goal')
        self.assertIsInstance(loaded_data[0]['created_date'], datetime)

    def test_load_goals_data_nonexistent_file(self):
        """Test odczytu nieistniejącego pliku celów"""
        loaded_data = self.data_manager.load_goals_data("nonexistent_user")
        self.assertEqual(loaded_data, [])

    @patch('builtins.open', side_effect=json.JSONDecodeError("Invalid JSON", "doc", 0))
    def test_load_goals_data_corrupted_file(self, mock_open):
        """Test odczytu uszkodzonego pliku JSON"""
        # Utworzenie pliku (żeby istniał)
        self.data_manager.goals_file.touch()

        loaded_data = self.data_manager.load_goals_data("testuser")
        self.assertEqual(loaded_data, [])

    def test_save_user_data(self):
        """Test zapisu danych użytkownika"""
        result = self.data_manager.save_user_data(self.test_user_data)
        self.assertTrue(result)

        # Sprawdzenie czy plik został utworzony
        self.assertTrue(self.data_manager.users_file.exists())

        # Sprawdzenie zawartości
        with open(self.data_manager.users_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        self.assertIn(self.test_user_data['username'], saved_data)

    def test_save_user_data_invalid(self):
        """Test zapisu nieprawidłowych danych użytkownika"""
        # Test bez nazwy użytkownika
        invalid_user = {'email': 'test@example.com'}
        result = self.data_manager.save_user_data(invalid_user)
        self.assertFalse(result)

        # Test z nieprawidłowym typem
        result = self.data_manager.save_user_data("not a dict")
        self.assertFalse(result)

    def test_load_user_data(self):
        """Test odczytu danych użytkownika"""
        # Zapisz dane użytkownika
        self.data_manager.save_user_data(self.test_user_data)

        # Odczytaj dane
        loaded_user = self.data_manager.load_user_data(self.test_user_data['username'])

        self.assertIsNotNone(loaded_user)
        self.assertEqual(loaded_user['username'], self.test_user_data['username'])
        self.assertEqual(loaded_user['email'], self.test_user_data['email'])
        self.assertIsInstance(loaded_user['created_date'], datetime)

    def test_load_user_data_nonexistent(self):
        """Test odczytu nieistniejącego użytkownika"""
        loaded_user = self.data_manager.load_user_data("nonexistent")
        self.assertIsNone(loaded_user)

    def test_get_users_data(self):
        """Test pobierania wszystkich użytkowników"""
        # Dodanie kilku użytkowników
        users = [
            {**self.test_user_data, 'username': 'user1', 'id': 'id1'},
            {**self.test_user_data, 'username': 'user2', 'id': 'id2'},
            {**self.test_user_data, 'username': 'user3', 'id': 'id3'}
        ]

        for user in users:
            self.data_manager.save_user_data(user)

        all_users = self.data_manager.get_user_data()
        self.assertEqual(len(all_users), 3)

        usernames = [user['username'] for user in all_users]
        self.assertIn('user1', usernames)
        self.assertIn('user2', usernames)
        self.assertIn('user3', usernames)

    def test_save_progress_data(self):
        """Test zapisu danych postępów"""
        progress_data = [
            {
                'id': 'progress1',
                'goal_id': 'goal1',
                'value': 25.0,
                'note': 'First progress',
                'timestamp': datetime.now()
            },
            {
                'id': 'progress2',
                'goal_id': 'goal1',
                'value': 50.0,
                'note': 'Second progress',
                'timestamp': datetime.now()
            }
        ]

        result = self.data_manager.save_progress_data(progress_data)
        self.assertTrue(result)

        # Sprawdzenie pliku
        self.assertTrue(self.data_manager.progress_file.exists())

    def test_load_progress_data(self):
        """Test odczytu danych postępów"""
        progress_data = [
            {
                'id': 'progress1',
                'goal_id': 'goal1',
                'value': 25.0,
                'note': 'Test progress',
                'timestamp': datetime.now()
            }
        ]

        # Zapisz i odczytaj
        self.data_manager.save_progress_data(progress_data)
        loaded_progress = self.data_manager.load_progress_data()

        self.assertEqual(len(loaded_progress), 1)
        self.assertEqual(loaded_progress[0]['goal_id'], 'goal1')
        self.assertEqual(loaded_progress[0]['value'], 25.0)
        self.assertIsInstance(loaded_progress[0]['timestamp'], datetime)

    def test_backup_file_before_write(self):
        """Test tworzenia kopii zapasowej przed zapisem"""
        # Utworzenie pliku do backup
        test_content = {"test": "data"}
        with open(self.data_manager.goals_file, 'w') as f:
            json.dump(test_content, f)

        # Test metody backup
        result = self.data_manager._backup_file_before_write(self.data_manager.goals_file)
        self.assertTrue(result)

        # Sprawdzenie czy kopia została utworzona
        backup_files = list(self.data_manager.backup_dir.glob("goals_backup_*.json"))
        self.assertGreater(len(backup_files), 0)

    def test_validate_json_file(self):
        """Test walidacji plików JSON"""
        # Test prawidłowego pliku JSON
        valid_data = {"test": "data"}
        with open(self.data_manager.goals_file, 'w') as f:
            json.dump(valid_data, f)

        result = self.data_manager._validate_json_file(self.data_manager.goals_file)
        self.assertTrue(result)

        # Test nieprawidłowego pliku JSON
        with open(self.data_manager.goals_file, 'w') as f:
            f.write("invalid json content {")

        result = self.data_manager._validate_json_file(self.data_manager.goals_file)
        self.assertFalse(result)

        # Test nieistniejącego pliku
        nonexistent_file = Path(self.test_dir) / "nonexistent.json"
        result = self.data_manager._validate_json_file(nonexistent_file)
        self.assertFalse(result)

    def test_export_to_csv(self):
        """Test eksportu do formatu CSV"""
        test_data = [
            {'name': 'Goal 1', 'progress': 50, 'category': 'Work'},
            {'name': 'Goal 2', 'progress': 75, 'category': 'Health'},
            {'name': 'Goal 3', 'progress': 25, 'category': 'Education'}
        ]

        result = self.data_manager.export_to_csv("goals", "test_export", test_data)
        self.assertTrue(result)

        # Sprawdzenie czy plik został utworzony
        export_file = self.data_manager.export_dir / "test_export.csv"
        self.assertTrue(export_file.exists())

        # Sprawdzenie zawartości
        with open(export_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('name', content)
            self.assertIn('progress', content)
            self.assertIn('Goal 1', content)

    def test_export_to_json(self):
        """Test eksportu do formatu JSON"""
        test_data = {
            'goals': [
                {'name': 'Goal 1', 'progress': 50},
                {'name': 'Goal 2', 'progress': 75}
            ],
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_goals': 2
            }
        }

        result = self.data_manager.export_to_json("test_export", test_data)
        self.assertTrue(result)

        # Sprawdzenie pliku
        export_file = self.data_manager.export_dir / "test_export.json"
        self.assertTrue(export_file.exists())

        # Sprawdzenie zawartości
        with open(export_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            self.assertIn('goals', loaded_data)
            self.assertEqual(len(loaded_data['goals']), 2)

    def test_save_backup(self):
        """Test zapisu kopii zapasowej"""
        backup_data = {
            'goals_storage': {'user1': [self.test_goal_data]},
            'user_statistics': {},
            'backup_timestamp': datetime.now().isoformat()
        }

        result = self.data_manager.save_backup(backup_data, "test_backup.json")
        self.assertTrue(result)

        # Sprawdzenie pliku
        backup_file = self.data_manager.backup_dir / "test_backup.json"
        self.assertTrue(backup_file.exists())

    def test_cleanup_old_backups(self):
        """Test czyszczenia starych kopii zapasowych"""
        # Utworzenie wielu plików backup
        for i in range(15):  # Więcej niż MAX_BACKUP_FILES (10)
            backup_name = f"backup_{i:04d}.json"
            backup_file = self.data_manager.backup_dir / backup_name
            backup_file.write_text('{"test": "data"}')

        # Wywołanie czyszczenia
        self.data_manager._cleanup_old_backups()

        # Sprawdzenie czy zostało tylko 10 plików
        backup_files = list(self.data_manager.backup_dir.glob("backup_*.json"))
        self.assertLessEqual(len(backup_files), 10)

    def test_restore_from_backup(self):
        """Test przywracania z kopii zapasowej"""
        # Utworzenie kopii zapasowej
        backup_data = {
            'goals_storage': {'user1': [self.test_goal_data]},
            'user_statistics': {},
            'backup_timestamp': datetime.now().isoformat()
        }

        backup_filename = "restore_test_backup.json"
        self.data_manager.save_backup(backup_data, backup_filename)

        # Przywracanie
        result = self.data_manager.restore_from_backup(backup_filename)
        self.assertTrue(result)

        # Sprawdzenie czy dane zostały przywrócone
        self.assertTrue(self.data_manager.goals_file.exists())

        with open(self.data_manager.goals_file, 'r') as f:
            restored_data = json.load(f)
            self.assertIn('user1', restored_data)

    def test_get_backup_list(self):
        """Test pobierania listy kopii zapasowych"""
        # Utworzenie kilku kopii zapasowych
        backup_files = ["backup_001.json", "backup_002.json", "backup_003.json"]

        for filename in backup_files:
            backup_file = self.data_manager.backup_dir / filename
            backup_file.write_text('{"test": "data"}')

        backup_list = self.data_manager.get_backup_list()

        self.assertEqual(len(backup_list), 3)
        self.assertIsInstance(backup_list[0], dict)
        self.assertIn('filename', backup_list[0])
        self.assertIn('size_bytes', backup_list[0])
        self.assertIn('created_date', backup_list[0])

    def test_get_data_statistics(self):
        """Test pobierania statystyk danych"""
        # Utworzenie przykładowych danych
        self.data_manager.save_goals_data([self.test_goal_data], "testuser")
        self.data_manager.save_user_data(self.test_user_data)

        stats = self.data_manager.get_data_statistics()

        self.assertIn('files', stats)
        self.assertIn('data_counts', stats)
        self.assertIn('total_size_bytes', stats)

        # Sprawdzenie statystyk plików
        self.assertIn('goals', stats['files'])
        self.assertIn('users', stats['files'])

        # Sprawdzenie liczników danych
        self.assertGreaterEqual(stats['data_counts']['goals'], 0)
        self.assertGreaterEqual(stats['data_counts']['users'], 0)

    def test_verify_data_integrity(self):
        """Test weryfikacji integralności danych"""
        # Dodanie prawidłowych danych
        self.data_manager.save_goals_data([self.test_goal_data], "testuser")
        self.data_manager.save_user_data(self.test_user_data)

        integrity_report = self.data_manager.verify_data_integrity()

        self.assertIn('goals_file_valid', integrity_report)
        self.assertIn('users_file_valid', integrity_report)
        self.assertIn('progress_file_valid', integrity_report)
        self.assertIn('overall_integrity', integrity_report)

        # Z prawidłowymi danymi wszystko powinno być OK
        self.assertTrue(integrity_report['goals_file_valid'])
        self.assertTrue(integrity_report['users_file_valid'])

    def test_clear_cache(self):
        """Test czyszczenia cache"""
        # Dodanie czegoś do cache
        self.data_manager._data_cache['test'] = 'data'

        # Czyszczenie
        self.data_manager.clear_cache()

        # Sprawdzenie czy cache jest pusty
        self.assertEqual(len(self.data_manager._data_cache), 0)

    def test_load_all_data(self):
        """Test ładowania wszystkich danych systemu"""
        # Utworzenie przykładowych danych
        self.data_manager.save_goals_data([self.test_goal_data], "testuser")
        self.data_manager.save_user_data(self.test_user_data)

        result = self.data_manager.load_all_data()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
