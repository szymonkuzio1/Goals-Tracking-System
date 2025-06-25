"""
Moduł API - interfejs do integracji z zewnętrznymi systemami
Obsługa importu/eksportu, webhooks i REST API endpoints
"""
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union, Callable
from functools import reduce
from .models.goal import Goal, PersonalGoal, BusinessGoal
import hashlib
DEFAULT_USER = "default"

# Zmienne globalne konfiguracyjne API
API_VERSION = "1.0.0"
SUPPORTED_FORMATS = {"json", "csv", "xml", "txt"}
MAX_IMPORT_SIZE = 10_000_000  # wielkość w bajtach
RATE_LIMIT_REQUESTS = 100
DEFAULT_EXPORT_ENCODING = "utf-8"

# Mapowania formatów
MIME_TYPES = {
    'json': 'application/json',
    'csv': 'text/csv',
    'xml': 'application/xml',
    'txt': 'text/plain'
}


class APIManager:
    """
    Klasa zarządzania API systemu śledzenia celów
    """

    def __init__(self, data_manager=None, goal_manager=None):
        self.data_manager = data_manager
        self.goal_manager = goal_manager
        self._api_key = self._generate_api_key()  # prywatny klucz API
        self._request_count = 0  # licznik requestów
        self._registered_webhooks = []  # lista webhooków
        self._import_validators = {}  # słownik walidatorów importu
        self._export_formatters = {}  # słownik formaterów eksportu

        # Inicjalizacja domyślnych formaterów i walidatorów
        self._initialize_default_handlers()

    def _generate_api_key(self) -> str:
        """Prywatna metoda generowania klucza API"""
        timestamp = str(datetime.now().timestamp())
        hash_object = hashlib.sha256(timestamp.encode())
        return hash_object.hexdigest()[:32]

    def _initialize_default_handlers(self) -> None:
        """Prywatna metoda inicjalizacji domyślnych handlerów"""

        def _default_json_validator(data: Any) -> tuple[bool, str]:
            """Wewnętrzna funkcja walidacji JSON"""
            try:
                if isinstance(data, str):
                    json.loads(data)
                elif isinstance(data, dict) or isinstance(data, list):
                    json.dumps(data)
                else:
                    return False, "Nieprawidłowy typ danych JSON"
                return True, "JSON prawidłowy"
            except json.JSONDecodeError as e:
                return False, f"Błąd JSON: {e}"
            except Exception as e:
                return False, f"Nieoczekiwany błąd: {e}"

        def _default_csv_validator(data: str) -> tuple[bool, str]:
            """Wewnętrzna funkcja walidacji CSV"""
            try:
                lines = data.strip().split('\n')
                if len(lines) < 2:
                    return False, "CSV musi zawierać nagłówek i przynajmniej jeden wiersz danych"

                # Sprawdzenie spójności liczby kolumn
                header_cols = len(lines[0].split(','))
                for i, line in enumerate(lines[1:], 2):
                    if len(line.split(',')) != header_cols:
                        return False, f"Niezgodna liczba kolumn w wierszu {i}"

                return True, "CSV prawidłowy"
            except Exception as e:
                return False, f"Błąd walidacji CSV: {e}"

        # Rejestracja domyślnych walidatorów
        self._import_validators['json'] = _default_json_validator
        self._import_validators['csv'] = _default_csv_validator

    def _check_rate_limit(self) -> bool:
        """Prywatna metoda sprawdzania limitu requestów"""
        if self._request_count >= RATE_LIMIT_REQUESTS:
            return False
        self._request_count += 1
        return True

    def register_webhook(self, event_type: str, callback_url: str,
                         secret_key: str = None) -> str:
        """Rejestracja webhook dla eventów systemu"""

        def _generate_webhook_id() -> str:
            """Wewnętrzna funkcja generowania ID webhook"""
            timestamp = str(datetime.now().timestamp())
            content = f"{event_type}_{callback_url}_{timestamp}"
            return hashlib.md5(content.encode()).hexdigest()[:16]

        try:
            assert isinstance(event_type, str) and event_type.strip(), "Typ eventu wymagany"
            assert isinstance(callback_url, str) and callback_url.strip(), "URL callback wymagany"

            webhook_id = _generate_webhook_id()

            webhook_config = {
                'id': webhook_id,
                'event_type': event_type,
                'callback_url': callback_url,
                'secret_key': secret_key,
                'created_at': datetime.now().isoformat(),
                'is_active': True,
                'request_count': 0,
                'last_triggered': None
            }

            self._registered_webhooks.append(webhook_config)

            print(f"✅ Webhook zarejestrowany: {webhook_id} dla eventu '{event_type}'")
            return webhook_id

        except AssertionError as e:
            print(f"❌ Błąd rejestracji webhook: {e}")
            return ""
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd rejestracji webhook: {e}")
            return ""

    def trigger_webhook(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Wyzwolenie webhook dla konkretnego eventu"""

        def _prepare_webhook_payload(webhook: Dict, data: Dict) -> Dict:
            """Wewnętrzna funkcja przygotowania payload webhook"""
            return {
                'webhook_id': webhook['id'],
                'event_type': event_type,
                'event_data': data,
                'timestamp': datetime.now().isoformat(),
                'api_version': API_VERSION
            }

        def _sign_payload(payload: Dict, secret_key: str) -> str:
            """Wewnętrzna funkcja podpisywania payload"""
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hashlib.sha256(f"{secret_key}{payload_str}".encode()).hexdigest()
            return f"sha256={signature}"

        try:
            # Filtrowanie webhooków dla danego typu eventu
            matching_webhooks = list(filter(
                lambda w: w['event_type'] == event_type and w['is_active'],
                self._registered_webhooks
            ))

            if not matching_webhooks:
                print(f"ℹ️ Brak aktywnych webhooków dla eventu '{event_type}'")
                return True

            success_count = 0

            for webhook in matching_webhooks:
                try:
                    # Przygotowanie payload
                    payload = _prepare_webhook_payload(webhook, event_data)

                    # Podpisanie jeśli secret_key dostępny
                    headers = {'Content-Type': 'application/json'}
                    if webhook['secret_key']:
                        headers['X-Signature'] = _sign_payload(payload, webhook['secret_key'])

                    # Symulacja wysłania HTTP request (w rzeczywistej implementacji użyj requests)
                    print(f"🔗 Webhook wywołany: {webhook['callback_url']}")
                    print(f"   Payload: {json.dumps(payload, indent=2)}")

                    # Aktualizacja statystyk webhook
                    webhook['request_count'] += 1
                    webhook['last_triggered'] = datetime.now().isoformat()

                    success_count += 1

                except Exception as e:
                    print(f"❌ Błąd wywołania webhook {webhook['id']}: {e}")

            print(f"✅ Pomyślnie wywołano {success_count}/{len(matching_webhooks)} webhooków")
            return success_count > 0

        except Exception as e:
            print(f"❌ Błąd wyzwalania webhooków: {e}")
            return False

    def import_goals_from_json(self, json_data: Union[str, Dict]) -> Dict[str, Any]:
        """Import celów z formatu JSON"""

        def _validate_goal_structure(goal_dict: Dict) -> tuple[bool, List[str]]:
            """Wewnętrzna funkcja walidacji struktury celu"""
            required_fields = ['title', 'description', 'target_value']
            errors = []

            for field in required_fields:
                if field not in goal_dict:
                    errors.append(f"Brak wymaganego pola: {field}")
                elif not goal_dict[field]:
                    errors.append(f"Pole {field} nie może być puste")

            # Walidacja typu danych
            if 'target_value' in goal_dict:
                try:
                    float(goal_dict['target_value'])
                except (ValueError, TypeError):
                    errors.append("target_value musi być liczbą")

            return len(errors) == 0, errors

        def _convert_imported_goal(goal_data: Dict) -> Dict:
            """Wewnętrzna funkcja konwersji importowanego celu"""
            converted_goal = {
                'title': str(goal_data.get('title', '')).strip(),
                'description': str(goal_data.get('description', '')).strip(),
                'target_value': float(goal_data.get('target_value', 0)),
                'current_value': float(goal_data.get('current_value', 0)),
                'category': str(goal_data.get('category', 'Importowany')).strip(),
                'status': str(goal_data.get('status', 'aktywny')).strip()
            }

            # Obsługa dat
            if 'created_date' in goal_data:
                try:
                    if isinstance(goal_data['created_date'], str):
                        converted_goal['created_date'] = datetime.fromisoformat(
                            goal_data['created_date'].replace('Z', '+00:00')
                        )
                    else:
                        converted_goal['created_date'] = datetime.now()
                except:
                    converted_goal['created_date'] = datetime.now()
            else:
                converted_goal['created_date'] = datetime.now()

            return converted_goal

        try:
            if not self._check_rate_limit():
                return {'success': False, 'error': 'Przekroczony limit requestów'}

            # Parsowanie JSON jeśli string
            if isinstance(json_data, str):
                try:
                    parsed_data = json.loads(json_data)
                except json.JSONDecodeError as e:
                    return {'success': False, 'error': f'Nieprawidłowy JSON: {e}'}
            else:
                parsed_data = json_data

            # Sprawdzenie czy to lista celów
            if isinstance(parsed_data, dict) and 'goals' in parsed_data:
                goals_to_import = parsed_data['goals']
            elif isinstance(parsed_data, list):
                goals_to_import = parsed_data
            else:
                return {'success': False, 'error': 'Nieprawidłowa struktura danych'}

            # Walidacja każdego celu
            import_results = {
                'total_goals': len(goals_to_import),
                'imported_successfully': 0,
                'failed_imports': 0,
                'errors': []
            }

            for i, goal_data in enumerate(goals_to_import):
                try:
                    # Walidacja struktury
                    is_valid, validation_errors = _validate_goal_structure(goal_data)

                    if not is_valid:
                        import_results['errors'].append(f"Cel {i + 1}: {', '.join(validation_errors)}")
                        import_results['failed_imports'] += 1
                        continue

                    # Konwersja i dodanie celu
                    converted_goal = _convert_imported_goal(goal_data)

                    # Tworzenie obiektu celu
                    from .models.goal import Goal
                    goal = Goal(
                        converted_goal['title'],
                        converted_goal['description'],
                        converted_goal['target_value'],
                        converted_goal['category']
                    )
                    goal.current_value = converted_goal['current_value']
                    goal.status = converted_goal['status']
                    goal.created_date = converted_goal['created_date']

                    # Dodanie do systemu
                    if self.goal_manager and self.goal_manager.add_goal(DEFAULT_USER, goal):
                        import_results['imported_successfully'] += 1
                    else:
                        import_results['failed_imports'] += 1
                        import_results['errors'].append(f"Cel {i + 1}: Nie udało się dodać do systemu")

                except Exception as e:
                    import_results['failed_imports'] += 1
                    import_results['errors'].append(f"Cel {i + 1}: {str(e)}")

            # Wyzwolenie webhook
            self.trigger_webhook('goals_imported', {
                'username': DEFAULT_USER,
                'results': import_results
            })

            import_results['success'] = import_results['imported_successfully'] > 0
            return import_results

        except Exception as e:
            return {'success': False, 'error': f'Błąd importu: {e}'}

    def import_goals_from_csv(self, csv_data: str, field_mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """Import celów z formatu CSV"""

        def _parse_csv_data(csv_content: str) -> List[Dict[str, str]]:
            """Wewnętrzna funkcja parsowania CSV"""
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                raise ValueError("CSV musi zawierać nagłówek i dane")

            reader = csv.DictReader(lines)
            return list(reader)

        def _map_csv_fields(csv_row: Dict[str, str], mapping: Dict[str, str]) -> Dict[str, Any]:
            """Wewnętrzna funkcja mapowania pól CSV"""
            mapped_data = {}

            # Domyślne mapowanie
            default_mapping = {
                'title': 'title',
                'description': 'description',
                'target_value': 'target_value',
                'current_value': 'current_value',
                'category': 'category',
                'status': 'status'
            }

            # Użycie dostarczonego mapowania lub domyślnego
            field_map = mapping if mapping else default_mapping

            for goal_field, csv_field in field_map.items():
                if csv_field in csv_row:
                    mapped_data[goal_field] = csv_row[csv_field]

            return mapped_data

        try:
            if not self._check_rate_limit():
                return {'success': False, 'error': 'Przekroczony limit requestów'}

            # Walidacja CSV
            is_valid, validation_message = self._import_validators['csv'](csv_data)
            if not is_valid:
                return {'success': False, 'error': validation_message}

            # Parsowanie CSV
            csv_rows = _parse_csv_data(csv_data)

            import_results = {
                'total_goals': len(csv_rows),
                'imported_successfully': 0,
                'failed_imports': 0,
                'errors': []
            }

            for i, row in enumerate(csv_rows):
                try:
                    # Mapowanie pól
                    mapped_goal = _map_csv_fields(row, field_mapping)

                    # Konwersja typów
                    if 'target_value' in mapped_goal:
                        mapped_goal['target_value'] = float(mapped_goal['target_value'])
                    if 'current_value' in mapped_goal:
                        mapped_goal['current_value'] = float(mapped_goal.get('current_value', 0))

                    # Import jako JSON
                    json_result = self.import_goals_from_json([mapped_goal])

                    if json_result.get('success'):
                        import_results['imported_successfully'] += 1
                    else:
                        import_results['failed_imports'] += 1
                        import_results['errors'].append(f"Wiersz {i + 1}: {json_result.get('error', 'Nieznany błąd')}")

                except Exception as e:
                    import_results['failed_imports'] += 1
                    import_results['errors'].append(f"Wiersz {i + 1}: {str(e)}")

            import_results['success'] = import_results['imported_successfully'] > 0
            return import_results

        except Exception as e:
            return {'success': False, 'error': f'Błąd importu CSV: {e}'}

    def export_goals_to_json(self, filter_criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """Eksport celów do formatu JSON"""

        def _apply_filters(goals: List, criteria: Dict) -> List:
            """Wewnętrzna funkcja filtrowania celów"""
            if not criteria:
                return goals

            filtered_goals = goals

            # Filtr według statusu
            if 'status' in criteria:
                filtered_goals = list(filter(
                    lambda g: g.get('status', '').lower() == criteria['status'].lower(),
                    filtered_goals
                ))

            # Filtr według kategorii
            if 'category' in criteria:
                filtered_goals = list(filter(
                    lambda g: g.get('category', '').lower() == criteria['category'].lower(),
                    filtered_goals
                ))

            # Filtr według zakresu dat
            if 'date_from' in criteria or 'date_to' in criteria:
                def date_filter(goal):
                    goal_date = goal.get('created_date')
                    if not goal_date:
                        return False

                    if isinstance(goal_date, str):
                        try:
                            goal_date = datetime.fromisoformat(goal_date.replace('Z', '+00:00'))
                        except:
                            return False

                    if 'date_from' in criteria:
                        date_from = datetime.fromisoformat(criteria['date_from'])
                        if goal_date < date_from:
                            return False

                    if 'date_to' in criteria:
                        date_to = datetime.fromisoformat(criteria['date_to'])
                        if goal_date > date_to:
                            return False

                    return True

                filtered_goals = list(filter(date_filter, filtered_goals))

            return filtered_goals

        def _prepare_export_data(goals: List[Dict]) -> Dict[str, Any]:
            """Wewnętrzna funkcja przygotowania danych do eksportu"""
            # Konwersja dat do string
            export_goals = []
            for goal in goals:
                export_goal = goal.copy()

                # Konwersja dat
                date_fields = ['created_date', 'deadline']
                for field in date_fields:
                    if field in export_goal and export_goal[field]:
                        if isinstance(export_goal[field], datetime):
                            export_goal[field] = export_goal[field].isoformat()

                export_goals.append(export_goal)

            return {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'api_version': API_VERSION,
                    'username': DEFAULT_USER,
                    'total_goals': len(export_goals),
                    'filter_criteria': filter_criteria or {}
                },
                'goals': export_goals
            }

        try:
            if not self._check_rate_limit():
                return {'success': False, 'error': 'Przekroczony limit requestów'}

            if not self.goal_manager:
                return {'success': False, 'error': 'Goal Manager niedostępny'}

            # Pobranie celów użytkownika
            user_goals = self.goal_manager.get_user_goals(DEFAULT_USER)

            if not user_goals:
                return {
                    'success': True,
                    'data': {'metadata': {'total_goals': 0}, 'goals': []},
                    'message': 'Brak celów do eksportu'
                }

            # Konwersja do słowników
            goals_data = [goal.to_dict() for goal in user_goals]

            # Aplikacja filtrów
            filtered_goals = _apply_filters(goals_data, filter_criteria)

            # Przygotowanie danych eksportu
            export_data = _prepare_export_data(filtered_goals)

            # Wyzwolenie webhook
            self.trigger_webhook('goals_exported', {
                'username': DEFAULT_USER,
                'format': 'json',
                'goals_count': len(filtered_goals)
            })

            return {
                'success': True,
                'data': export_data,
                'format': 'json',
                'mime_type': MIME_TYPES['json']
            }

        except Exception as e:
            return {'success': False, 'error': f'Błąd eksportu JSON: {e}'}

    def export_goals_to_csv(self, filter_criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """Eksport celów do formatu CSV"""

        def _convert_to_csv(goals_data: List[Dict]) -> str:
            """Wewnętrzna funkcja konwersji do CSV"""
            if not goals_data:
                return "title,description,target_value,current_value,category,status,created_date\n"

            # Określenie wszystkich kolumn
            all_columns = set()
            for goal in goals_data:
                all_columns.update(goal.keys())

            # Sortowanie kolumn
            sorted_columns = sorted(all_columns)

            # Tworzenie CSV
            csv_lines = [','.join(sorted_columns)]

            for goal in goals_data:
                row_values = []
                for col in sorted_columns:
                    value = goal.get(col, '')
                    # Escape wartości zawierające przecinki
                    if ',' in str(value):
                        value = f'"{value}"'
                    row_values.append(str(value))
                csv_lines.append(','.join(row_values))

            return '\n'.join(csv_lines)

        try:
            # Eksport do JSON
            json_result = self.export_goals_to_json(filter_criteria)

            if not json_result.get('success'):
                return json_result

            goals_data = json_result['data']['goals']

            # Konwersja do CSV
            csv_content = _convert_to_csv(goals_data)

            return {
                'success': True,
                'data': csv_content,
                'format': 'csv',
                'mime_type': MIME_TYPES['csv'],
                'goals_count': len(goals_data)
            }

        except Exception as e:
            return {'success': False, 'error': f'Błąd eksportu CSV: {e}'}

    def export_goals_to_xml(self, filter_criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """Eksport celów do formatu XML"""

        def _convert_to_xml(goals_data: List[Dict], metadata: Dict) -> str:
            """Wewnętrzna funkcja konwersji do XML"""
            root = ET.Element('goals_export')

            # Metadata
            metadata_elem = ET.SubElement(root, 'metadata')
            for key, value in metadata.items():
                meta_elem = ET.SubElement(metadata_elem, key)
                meta_elem.text = str(value)

            # Goals
            goals_elem = ET.SubElement(root, 'goals')

            for goal_data in goals_data:
                goal_elem = ET.SubElement(goals_elem, 'goal')

                for key, value in goal_data.items():
                    field_elem = ET.SubElement(goal_elem, key)
                    field_elem.text = str(value) if value is not None else ''

            return ET.tostring(root, encoding='unicode', method='xml')

        try:
            # Eksport do JSON
            json_result = self.export_goals_to_json(filter_criteria)

            if not json_result.get('success'):
                return json_result

            export_data = json_result['data']
            goals_data = export_data['goals']
            metadata = export_data['metadata']

            # Konwersja do XML
            xml_content = _convert_to_xml(goals_data, metadata)

            return {
                'success': True,
                'data': xml_content,
                'format': 'xml',
                'mime_type': MIME_TYPES['xml'],
                'goals_count': len(goals_data)
            }

        except Exception as e:
            return {'success': False, 'error': f'Błąd eksportu XML: {e}'}

    def get_api_statistics(self) -> Dict[str, Any]:
        """Statystyki API"""
        try:
            # Statystyki webhooków - użycie programowania funkcyjnego
            active_webhooks = list(filter(lambda w: w['is_active'], self._registered_webhooks))
            total_webhook_requests = reduce(
                lambda acc, w: acc + w.get('request_count', 0),
                self._registered_webhooks,
                0
            )

            # Grupowanie webhooków według typu eventu
            webhook_types = {}
            for webhook in self._registered_webhooks:
                event_type = webhook['event_type']
                webhook_types[event_type] = webhook_types.get(event_type, 0) + 1

            return {
                'api_version': API_VERSION,
                'api_key': self._api_key[:8] + '...',  # Partial key dla bezpieczeństwa
                'request_count': self._request_count,
                'rate_limit': RATE_LIMIT_REQUESTS,
                'supported_formats': list(SUPPORTED_FORMATS),
                'webhooks': {
                    'total_registered': len(self._registered_webhooks),
                    'active_webhooks': len(active_webhooks),
                    'total_requests': total_webhook_requests,
                    'types_distribution': webhook_types
                },
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': f'Błąd pobierania statystyk API: {e}'}

    def validate_import_data(self, data: Union[str, Dict, List],
                             format_type: str) -> Dict[str, Any]:
        """Walidacja danych importu"""
        try:
            if format_type not in SUPPORTED_FORMATS:
                return {
                    'valid': False,
                    'errors': [f'Nieobsługiwany format: {format_type}'],
                    'format': format_type
                }

            # Sprawdzenie rozmiaru danych
            data_size = len(str(data).encode('utf-8'))
            if data_size > MAX_IMPORT_SIZE:
                return {
                    'valid': False,
                    'errors': [f'Dane za duże: {data_size} bajtów (max: {MAX_IMPORT_SIZE})'],
                    'format': format_type
                }

            # Walidacja według formatu
            if format_type in self._import_validators:
                is_valid, message = self._import_validators[format_type](data)

                return {
                    'valid': is_valid,
                    'errors': [message] if not is_valid else [],
                    'format': format_type,
                    'data_size_bytes': data_size
                }
            else:
                return {
                    'valid': True,
                    'errors': [],
                    'format': format_type,
                    'data_size_bytes': data_size,
                    'warning': f'Brak dedykowanego walidatora dla formatu {format_type}'
                }

        except Exception as e:
            return {
                'valid': False,
                'errors': [f'Błąd walidacji: {e}'],
                'format': format_type
            }

    def register_custom_validator(self, format_type: str, validator_func: Callable[[Any], tuple[bool, str]]) -> bool:
        """Rejestracja niestandardowego walidatora"""
        try:
            assert callable(validator_func), "Walidator musi być funkcją"

            self._import_validators[format_type] = validator_func
            print(f"✅ Zarejestrowano walidator dla formatu: {format_type}")
            return True

        except Exception as e:
            print(f"❌ Błąd rejestracji walidatora: {e}")
            return False

    def get_supported_formats(self) -> Dict[str, Dict[str, Any]]:
        """Informacje o obsługiwanych formatach"""
        return {
            format_name: {
                'mime_type': MIME_TYPES.get(format_name, 'application/octet-stream'),
                'has_validator': format_name in self._import_validators,
                'supports_import': format_name in ['json', 'csv'],
                'supports_export': format_name in ['json', 'csv', 'xml', 'txt']
            }
            for format_name in SUPPORTED_FORMATS
        }

    def reset_api_statistics(self) -> bool:
        """Reset statystyk API"""
        try:
            self._request_count = 0

            # Reset statystyk webhooków
            for webhook in self._registered_webhooks:
                webhook['request_count'] = 0
                webhook['last_triggered'] = None

            print("✅ Statystyki API zresetowane")
            return True

        except Exception as e:
            print(f"❌ Błąd resetowania statystyk: {e}")
            return False
