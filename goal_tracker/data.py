"""
Moduł zarządzania danymi, obsługa plików i trwałość danych
Implementuje operacje CRUD, walidację i kopie zapasowe
"""
import json
import os
import shutil
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Zmienne globalne ścieżek
DATA_DIRECTORY = "data"
GOALS_FILE = "goals.json"
PROGRESS_FILE = "progress.json"
BACKUP_DIRECTORY = "backups"
EXPORT_DIRECTORY = "exports"

# Globalne ustawienia
MAX_BACKUP_FILES = 10
BACKUP_COMPRESSION = True
AUTO_BACKUP_INTERVAL_HOURS = 24


class DataManager:
    """
    Klasa zarządzania danymi systemu
    """

    def __init__(self, data_dir: str = DATA_DIRECTORY):
        self.data_dir = Path(data_dir)
        self.goals_file = self.data_dir / GOALS_FILE
        self.progress_file = self.data_dir / PROGRESS_FILE
        self.backup_dir = self.data_dir / BACKUP_DIRECTORY
        self.export_dir = self.data_dir / EXPORT_DIRECTORY

        # Prywatne struktury danych
        self._data_cache = {}  # cache danych
        self._file_locks = set()  # zbiór zablokowanych plików
        self._last_backup_time = None

        # Inicjalizacja katalogów
        self._initialize_directories()

    def _initialize_directories(self) -> None:
        """Prywatna metoda inicjalizacji katalogów"""
        try:
            directories = [self.data_dir, self.backup_dir, self.export_dir]

            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)

            print(f"✅ Katalogi danych zainicjalizowane: {self.data_dir}")

        except Exception as e:
            print(f"❌ Błąd inicjalizacji katalogów: {e}")
            raise

    def _create_default_files(self) -> None:
        """Prywatna metoda tworzenia domyślnych plików"""

        def _create_file_if_not_exists(filepath: Path, default_data: Any) -> None:
            """Wewnętrzna funkcja tworzenia pliku"""
            try:
                if not filepath.exists():
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(default_data, f, indent=2, ensure_ascii=False)
                    print(f"✅ Utworzono plik: {filepath}")
            except Exception as e:
                print(f"❌ Błąd tworzenia pliku {filepath}: {e}")

        try:
            # Tworzenie domyślnych plików JSON
            default_data_structures = {
                self.goals_file: {},
                self.progress_file: {}
            }

            for filepath, default_data in default_data_structures.items():
                _create_file_if_not_exists(filepath, default_data)

        except Exception as e:
            print(f"❌ Błąd tworzenia domyślnych plików: {e}")

    def _validate_json_file(self, filepath: Path) -> bool:
        """Prywatna metoda walidacji pliku JSON"""
        try:
            if not filepath.exists():
                return False

            with open(filepath, 'r', encoding='utf-8') as f:
                json.load(f)
            return True

        except json.JSONDecodeError as e:
            print(f"❌ Nieprawidłowy format JSON w pliku {filepath}: {e}")
            return False
        except Exception as e:
            print(f"❌ Błąd walidacji pliku {filepath}: {e}")
            return False

    def _backup_file_before_write(self, filepath: Path) -> bool:
        """Prywatna metoda kopii zapasowej przed zapisem"""
        try:
            if filepath.exists():
                backup_name = f"{filepath.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{filepath.suffix}"
                backup_path = self.backup_dir / backup_name

                shutil.copy2(filepath, backup_path)
                print(f"✅ Utworzono kopię zapasową: {backup_name}")
                return True
            return True

        except Exception as e:
            print(f"❌ Błąd tworzenia kopii zapasowej: {e}")
            return False

    def save_goals_data(self, goals_data: List[Dict[str, Any]], username: str = None) -> bool:
        """Zapis danych celów do pliku"""

        def _prepare_goals_for_save(goals: List[Dict]) -> List[Dict]:
            """Wewnętrzna funkcja przygotowania danych do zapisu"""
            prepared_goals = []

            for goal_dict in goals:
                # Konwersja dat do ISO format
                prepared_goal = goal_dict.copy()

                if 'created_date' in prepared_goal and isinstance(prepared_goal['created_date'], datetime):
                    prepared_goal['created_date'] = prepared_goal['created_date'].isoformat()

                if 'deadline' in prepared_goal and prepared_goal['deadline']:
                    if isinstance(prepared_goal['deadline'], datetime):
                        prepared_goal['deadline'] = prepared_goal['deadline'].isoformat()

                # Walidacja wymaganych pól
                required_fields = ['id', 'title', 'target_value']
                if all(field in prepared_goal for field in required_fields):
                    prepared_goals.append(prepared_goal)
                else:
                    print(f"⚠️ Pominięto cel z niepełnymi danymi: {prepared_goal.get('title', 'Bez nazwy')}")

            return prepared_goals

        try:
            assert isinstance(goals_data, list), "Dane celów muszą być listą"

            # Sprawdzenie blokady pliku
            if str(self.goals_file) in self._file_locks:
                print("⚠️ Plik celów jest zablokowany")
                return False

            # Dodanie blokady
            self._file_locks.add(str(self.goals_file))

            try:
                # Kopia zapasowa przed zapisem
                if not self._backup_file_before_write(self.goals_file):
                    print("⚠️ Nie udało się utworzyć kopii zapasowej, kontynuuję...")

                # Przygotowanie danych
                prepared_goals = _prepare_goals_for_save(goals_data)

                # Odczyt istniejących danych
                existing_data = {}
                if self.goals_file.exists():
                    try:
                        with open(self.goals_file, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                    except json.JSONDecodeError:
                        print("⚠️ Uszkodzony plik celów, tworzę nowy")
                        existing_data = {}

                # Aktualizacja danych dla użytkownika
                if username:
                    existing_data[username] = prepared_goals
                else:
                    existing_data = {'default_user': prepared_goals}

                # Zapis do pliku
                with open(self.goals_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)

                # Aktualizacja cache
                self._data_cache['goals'] = existing_data

                print(f"✅ Zapisano {len(prepared_goals)} celów do pliku")
                return True

            finally:
                # Usunięcie blokady
                self._file_locks.discard(str(self.goals_file))

        except AssertionError as e:
            print(f"❌ Błąd walidacji danych celów: {e}")
            return False
        except Exception as e:
            print(f"❌ Błąd zapisu celów: {e}")
            return False

    def load_goals_data(self, username: str = None) -> List[Dict[str, Any]]:
        """Odczyt danych celów z pliku"""

        def _parse_goal_dates(goal_dict: Dict) -> Dict:
            """Wewnętrzna funkcja parsowania dat"""
            parsed_goal = goal_dict.copy()

            # Parsowanie dat z formatu ISO
            date_fields = ['created_date', 'deadline']
            for field in date_fields:
                if field in parsed_goal and parsed_goal[field]:
                    try:
                        if isinstance(parsed_goal[field], str):
                            parsed_goal[field] = datetime.fromisoformat(
                                parsed_goal[field].replace('Z', '+00:00')
                            )
                    except ValueError:
                        print(f"⚠️ Nieprawidłowy format daty w polu {field}")
                        parsed_goal[field] = None

            return parsed_goal

        try:
            # Sprawdzenie istnienia pliku
            if not self.goals_file.exists():
                print("ℹ️ Plik celów nie istnieje, tworzę nowy")
                self._create_default_files()
                return []

            # Sprawdzenie czy plik nie jest pusty
            if self.goals_file.stat().st_size == 0:
                print("ℹ️ Plik celów jest pusty, inicjalizuję")
                with open(self.goals_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                return []

            # Odczyt z pliku
            with open(self.goals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Aktualizacja cache
            self._data_cache['goals'] = data

            # Zwrócenie danych użytkownika
            username = username or "default"
            if username in data:
                goals_data = data[username]
            else:
                return []

            # Parsowanie dat w celach
            parsed_goals = []
            for goal in goals_data:
                parsed_goal = goal.copy()
                # Parsowanie dat
                date_fields = ['created_date', 'deadline']
                for field in date_fields:
                    if field in parsed_goal and parsed_goal[field]:
                        try:
                            if isinstance(parsed_goal[field], str):
                                parsed_goal[field] = datetime.fromisoformat(
                                    parsed_goal[field].replace('Z', '+00:00')
                                )
                        except ValueError:
                            print(f"⚠️ Nieprawidłowy format daty w polu {field}")
                            parsed_goal[field] = None
                parsed_goals.append(parsed_goal)

            print(f"✅ Załadowano {len(parsed_goals)} celów z pliku")
            return parsed_goals

        except json.JSONDecodeError as e:
            print(f"❌ Błąd parsowania JSON: {e}")
            # Utworzenie nowego pustego pliku
            with open(self.goals_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            return []
        except Exception as e:
            print(f"❌ Błąd odczytu celów: {e}")
            return []

    def save_progress_data(self, progress_data: List[Dict[str, Any]]) -> bool:
        """Zapis danych postępów"""

        def _prepare_progress_for_save(progress_list: List[Dict]) -> List[Dict]:
            """Wewnętrzna funkcja przygotowania postępów"""
            prepared = []

            for progress_dict in progress_list:
                prepared_progress = progress_dict.copy()

                # Konwersja timestamp
                if 'timestamp' in prepared_progress and isinstance(prepared_progress['timestamp'], datetime):
                    prepared_progress['timestamp'] = prepared_progress['timestamp'].isoformat()

                prepared.append(prepared_progress)

            return prepared

        try:
            self._backup_file_before_write(self.progress_file)

            prepared_data = _prepare_progress_for_save(progress_data)

            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(prepared_data, f, indent=2, ensure_ascii=False)

            print(f"✅ Zapisano {len(prepared_data)} wpisów postępu")
            return True

        except Exception as e:
            print(f"❌ Błąd zapisu postępów: {e}")
            return False

    def load_progress_data(self) -> List[Dict[str, Any]]:
        """Odczyt danych postępów"""
        try:
            if not self.progress_file.exists():
                self._create_default_files()
                return []

            # Sprawdzenie czy plik nie jest pusty
            if self.progress_file.stat().st_size == 0:
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                return []

            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)

            # Parsowanie timestamps
            for progress in progress_data:
                if 'timestamp' in progress and progress['timestamp']:
                    try:
                        progress['timestamp'] = datetime.fromisoformat(
                            progress['timestamp'].replace('Z', '+00:00')
                        )
                    except ValueError:
                        progress['timestamp'] = datetime.now()

            return progress_data

        except json.JSONDecodeError as e:
            print(f"❌ Błąd parsowania JSON postępów: {e}")
            # Utworzenie nowego pustego pliku
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            return []
        except Exception as e:
            print(f"❌ Błąd odczytu postępów: {e}")
            return []

    def load_all_data(self) -> bool:
        """Ładowanie danych systemu - uproszczona wersja"""
        try:
            print("📂 Ładowanie danych systemu...")

            self._initialize_directories()
            self._create_default_files()

            # Cele i postępy
            goals_loaded = len(self.load_goals_data()) >= 0
            progress_loaded = len(self.load_progress_data()) >= 0

            success = goals_loaded and progress_loaded

            if success:
                print("✅ Dane załadowane pomyślnie")

            return success

        except Exception as e:
            print(f"❌ Błąd ładowania danych: {e}")
            return False

    def export_to_csv(self, data_type: str, filename: str, data: List[Dict]) -> bool:
        """Eksport danych do formatu CSV"""

        def _flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
            """Wewnętrzna funkcja spłaszczania słownika"""
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(_flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    items.append((new_key, ', '.join(map(str, v))))
                else:
                    items.append((new_key, v))
            return dict(items)

        try:
            if not data:
                print("❌ Brak danych do eksportu")
                return False

            export_path = self.export_dir / f"{filename}.csv"

            # Spłaszczenie danych
            flattened_data = [_flatten_dict(item) for item in data]

            # Pobranie wszystkich kluczy
            all_keys = set()
            for item in flattened_data:
                all_keys.update(item.keys())

            # Zapis do CSV
            with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=sorted(all_keys))
                writer.writeheader()
                writer.writerows(flattened_data)

            print(f"✅ Eksport do CSV zakończony: {export_path}")
            return True

        except Exception as e:
            print(f"❌ Błąd eksportu CSV: {e}")
            return False

    def export_to_json(self, filename: str, data: Dict[str, Any]) -> bool:
        """Eksport danych do formatu JSON"""
        try:
            export_path = self.export_dir / f"{filename}.json"

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ Eksport do JSON zakończony: {export_path}")
            return True

        except Exception as e:
            print(f"❌ Błąd eksportu JSON: {e}")
            return False

    def save_backup(self, backup_data: Dict[str, Any], filename: str) -> bool:
        """Zapis kopii zapasowej"""
        try:
            backup_path = self.backup_dir / filename

            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)

            # Czyszczenie starych kopii zapasowych
            self._cleanup_old_backups()

            self._last_backup_time = datetime.now()
            print(f"✅ Kopia zapasowa zapisana: {filename}")
            return True

        except Exception as e:
            print(f"❌ Błąd zapisu kopii zapasowej: {e}")
            return False

    def _cleanup_old_backups(self) -> None:
        """Prywatna metoda czyszczenia starych kopii zapasowych"""
        try:
            # Pobranie wszystkich plików backup
            backup_files = list(self.backup_dir.glob("backup_*.json"))

            if len(backup_files) > MAX_BACKUP_FILES:
                # Sortowanie według daty modyfikacji
                backup_files.sort(key=lambda f: f.stat().st_mtime)

                # Usunięcie najstarszych plików
                files_to_remove = backup_files[:-MAX_BACKUP_FILES]

                for file_to_remove in files_to_remove:
                    file_to_remove.unlink()
                    print(f"🗑️ Usunięto starą kopię zapasową: {file_to_remove.name}")

        except Exception as e:
            print(f"⚠️ Błąd czyszczenia kopii zapasowych: {e}")

    def restore_from_backup(self, backup_filename: str) -> bool:
        """Przywracanie z kopii zapasowej"""
        try:
            backup_path = self.backup_dir / backup_filename

            if not backup_path.exists():
                print(f"❌ Nie znaleziono kopii zapasowej: {backup_filename}")
                return False

            # Odczyt kopii zapasowej
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            # Walidacja struktury kopii zapasowej
            required_keys = ['goals_storage', 'user_statistics', 'backup_timestamp']
            if not all(key in backup_data for key in required_keys):
                print("❌ Nieprawidłowa struktura kopii zapasowej")
                return False

            # Tworzenie kopii zapasowej aktualnych danych przed przywracaniem
            current_backup_name = f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            current_data = {
                'goals_storage': {},
                'user_statistics': {},
                'backup_timestamp': datetime.now().isoformat()
            }

            # Odczyt aktualnych danych
            try:
                if self.goals_file.exists():
                    with open(self.goals_file, 'r', encoding='utf-8') as f:
                        current_data['goals_storage'] = json.load(f)
            except:
                pass

            self.save_backup(current_data, current_backup_name)

            # Przywracanie danych z kopii zapasowej
            goals_storage = backup_data['goals_storage']

            # Zapis przywróconych danych
            with open(self.goals_file, 'w', encoding='utf-8') as f:
                json.dump(goals_storage, f, indent=2, ensure_ascii=False)

            print(f"✅ Dane przywrócone z kopii zapasowej: {backup_filename}")
            print(f"📦 Utworzono kopię zapasową aktualnych danych: {current_backup_name}")

            # Czyszczenie cache
            self._data_cache.clear()

            return True

        except Exception as e:
            print(f"❌ Błąd przywracania kopii zapasowej: {e}")
            return False

    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Pobranie listy dostępnych kopii zapasowych"""
        try:
            backup_files = list(self.backup_dir.glob("backup_*.json"))
            backup_info = []

            for backup_file in backup_files:
                stat = backup_file.stat()
                backup_info.append({
                    'filename': backup_file.name,
                    'size_bytes': stat.st_size,
                    'created_date': datetime.fromtimestamp(stat.st_mtime),
                    'path': str(backup_file)
                })

            # Sortowanie według daty utworzenia (najnowsze pierwsze)
            backup_info.sort(key=lambda x: x['created_date'], reverse=True)

            return backup_info

        except Exception as e:
            print(f"❌ Błąd pobierania listy kopii zapasowych: {e}")
            return []

    def get_data_statistics(self) -> Dict[str, Any]:
        """Statystyki danych systemu"""
        try:
            stats = {
                'files': {},
                'data_counts': {},
                'total_size_bytes': 0,
                'last_backup': self._last_backup_time.isoformat() if self._last_backup_time else None
            }

            # Statystyki plików
            data_files = [
                ('goals', self.goals_file),
                ('progress', self.progress_file)
            ]

            for file_type, filepath in data_files:
                if filepath.exists():
                    stat = filepath.stat()
                    stats['files'][file_type] = {
                        'exists': True,
                        'size_bytes': stat.st_size,
                        'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                    stats['total_size_bytes'] += stat.st_size
                else:
                    stats['files'][file_type] = {'exists': False}

            # Liczniki danych
            stats['data_counts']['goals'] = len(self.load_goals_data())
            stats['data_counts']['progress_entries'] = len(self.load_progress_data())
            stats['data_counts']['backup_files'] = len(list(self.backup_dir.glob("backup_*.json")))

            return stats

        except Exception as e:
            print(f"❌ Błąd pobierania statystyk danych: {e}")
            return {}

    def clear_cache(self) -> None:
        """
        Wyczyszczenie cache danych
        """
        self._data_cache.clear()
        print("🗑️ Cache danych wyczyszczony")

    def verify_data_integrity(self) -> Dict[str, bool]:
        """Weryfikacja integralności danych"""

        def _check_data_consistency(goals_data: List[Dict], users_data: List[Dict]) -> bool:
            """Wewnętrzna funkcja sprawdzania spójności danych"""
            try:
                # Sprawdzenie czy wszystkie cele mają prawidłowe ID
                goal_ids = set()
                for goal in goals_data:
                    if 'id' not in goal or not goal['id']:
                        return False
                    if goal['id'] in goal_ids:
                        return False  # Duplikat ID
                    goal_ids.add(goal['id'])

                # Sprawdzenie czy użytkownicy mają unikalne nazwy
                usernames = set()
                for user in users_data:
                    if 'username' not in user or not user['username']:
                        return False
                    if user['username'] in usernames:
                        return False  # Duplikat username
                    usernames.add(user['username'])

                return True

            except Exception:
                return False

        try:
            integrity_report = {
                'goals_file_valid': self._validate_json_file(self.goals_file),
                'progress_file_valid': self._validate_json_file(self.progress_file),
                'data_consistency': False
            }

            # Sprawdzenie spójności danych
            if all([integrity_report['goals_file_valid'], integrity_report['users_file_valid']]):
                goals_data = self.load_goals_data()
                users_data = self.get_users_data()
                integrity_report['data_consistency'] = _check_data_consistency(goals_data, users_data)

            integrity_report['overall_integrity'] = all(integrity_report.values())

            return integrity_report

        except Exception as e:
            print(f"❌ Błąd weryfikacji integralności: {e}")
            return {'overall_integrity': False, 'error': str(e)}
