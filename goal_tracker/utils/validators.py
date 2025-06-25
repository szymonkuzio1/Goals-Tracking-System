"""
Moduł walidacji danych wejściowych
"""
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from functools import reduce

def validate_goal_data(goal_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Walidacja danych celu"""
    errors = []

    def _validate_required_fields(data: Dict) -> List[str]:
        """Wewnętrzna funkcja walidacji wymaganych pól"""
        required_fields = ['title', 'description', 'target_value']
        missing_fields = []

        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(f"Brak wymaganego pola: {field}")

        return missing_fields

    try:
        # Sprawdzenie typu danych
        if not isinstance(goal_data, dict):
            return False, ["Dane celu muszą być słownikiem"]

        # Sprawdzenie wymaganych pól
        required_errors = _validate_required_fields(goal_data)
        errors.extend(required_errors)

        # Walidacja tytułu
        if 'title' in goal_data:
            title = str(goal_data['title']).strip()
            if len(title) < 3:
                errors.append("Tytuł musi mieć min. 3 znaki")
            elif len(title) > 100:
                errors.append("Tytuł może mieć max. 100 znaków")

        # Walidacja wartości docelowej
        if 'target_value' in goal_data:
            try:
                target = float(goal_data['target_value'])
                if target <= 0:
                    errors.append("Wartość docelowa musi być większa niż 0")
                elif target > 1000000:
                    errors.append("Wartość docelowa jest za duża (max 1,000,000)")
            except (ValueError, TypeError):
                errors.append("Wartość docelowa musi być liczbą")

        # Walidacja terminu realizacji
        if 'deadline' in goal_data and goal_data['deadline']:
            deadline_value = goal_data['deadline']

            if isinstance(deadline_value, str):
                if 'T' not in deadline_value and len(deadline_value) <= 10:
                    deadline_valid, deadline_msg = validate_date_format(deadline_value)
                    if not deadline_valid:
                        errors.append(f"Nieprawidłowy termin: {deadline_msg}")

        return len(errors) == 0, errors

    except Exception as e:
        return False, [f"Błąd walidacji danych celu: {str(e)}"]


def validate_progress_value(current_value: Any, target_value: float) -> Tuple[bool, str]:
    """Walidacja wartości postępu"""
    try:
        # Konwersja do float
        progress = float(current_value)

        # Sprawdzenie czy nie jest ujemna
        if progress < 0:
            return False, "Wartość postępu nie może być ujemna"

        if progress > 999999:
            return False, "Wartość postępu jest za duża (max 999,999)"

        return True, "Wartość postępu poprawna"

    except (ValueError, TypeError):
        return False, "Wartość postępu musi być liczbą"
    except Exception as e:
        return False, f"Błąd walidacji postępu: {str(e)}"


def validate_date_format(date_string: str) -> Tuple[bool, str]:
    """
    Walidacja formatu daty
    Obsługiwane formaty: YYYY-MM-DD, DD.MM.YYYY, DD/MM/YYYY
    """

    def _parse_date_formats(date_str: str) -> Optional[datetime]:
        """Wewnętrzna funkcja parsowania różnych formatów dat"""
        formats_to_try = [
            '%Y-%m-%d',  # 2025-12-31
            '%d.%m.%Y',  # 31.12.2025
            '%d/%m/%Y',  # 31/12/2025
            '%Y-%m-%d %H:%M:%S',  # 2025-12-31 23:59:59
            '%d.%m.%Y %H:%M'  # 31.12.2025 23:59
        ]

        for date_format in formats_to_try:
            try:
                return datetime.strptime(date_str.strip(), date_format)
            except ValueError:
                continue

        return None

    try:
        if not isinstance(date_string, str) or not date_string.strip():
            return False, "Data nie może być pusta"

        parsed_date = _parse_date_formats(date_string)

        if parsed_date is None:
            return False, "Nieprawidłowy format daty. Użyj: YYYY-MM-DD, DD.MM.YYYY lub DD/MM/YYYY"

        # Sprawdzenie czy data nie jest z przeszłości (dla terminów)
        if parsed_date.date() < date.today():
            return False, "Data nie może być z przeszłości"

        # Sprawdzenie czy data nie jest za daleko w przyszłości (10 lat)
        max_future_date = date.today().replace(year=date.today().year + 10)
        if parsed_date.date() > max_future_date:
            return False, "Data jest za daleko w przyszłości (max 10 lat)"

        return True, "Data poprawna"

    except Exception as e:
        return False, f"Błąd walidacji daty: {str(e)}"


class DataValidator:
    """
    Klasa do walidacji złożonych struktur danych
    """

    def __init__(self):
        self._validation_rules = {}  # prywatny słownik reguł walidacji
        self._error_messages = []  # prywatna lista komunikatów błędów

    def add_validation_rule(self, field_name: str, validator_func, error_message: str = "") -> None:
        """Dodanie reguły walidacji dla pola"""
        self._validation_rules[field_name] = {
            'validator': validator_func,
            'error_message': error_message or f"Błąd walidacji pola {field_name}"
        }

    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Walidacja danych według zdefiniowanych reguł"""
        self._error_messages.clear()

        # Iteracja po regułach walidacji
        for field_name, rule in self._validation_rules.items():
            if field_name in data:
                try:
                    is_valid = rule['validator'](data[field_name])
                    if not is_valid:
                        self._error_messages.append(rule['error_message'])
                except Exception as e:
                    self._error_messages.append(f"Błąd walidacji {field_name}: {str(e)}")

        return len(self._error_messages) == 0, self._error_messages.copy()

    def validate_multiple_records(self, records: List[Dict[str, Any]]) -> Dict[int, List[str]]:
        """Walidacja wielu rekordów - map() i enumerate"""

        def _validate_single_record(record_with_index: Tuple[int, Dict]) -> Tuple[int, List[str]]:
            """Wewnętrzna funkcja walidacji pojedynczego rekordu"""
            index, record = record_with_index
            is_valid, errors = self.validate_data(record)
            return index, errors if not is_valid else []

        # Użycie map() do walidacji wszystkich rekordów
        indexed_records = enumerate(records)
        validation_results = map(_validate_single_record, indexed_records)

        # Filtrowanie tylko rekordów z błędami - filter()
        records_with_errors = filter(lambda result: len(result[1]) > 0, validation_results)

        return dict(records_with_errors)

    def get_validation_summary(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Podsumowanie walidacji - użycie programowania funkcyjnego"""
        validation_results = self.validate_multiple_records(records)

        # Liczba rekordów z błędami
        records_with_errors = len(validation_results)

        # Całkowita liczba błędów - użycie reduce()
        total_errors = reduce(
            lambda acc, errors: acc + len(errors),
            validation_results.values(),
            0
        )

        # Najczęstsze błędy - użycie funkcji lambda
        all_errors = []
        for errors in validation_results.values():
            all_errors.extend(errors)

        # Grupowanie błędów
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1

        # Sortowanie błędów według częstotliwości
        most_common_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'total_records': len(records),
            'valid_records': len(records) - records_with_errors,
            'invalid_records': records_with_errors,
            'total_errors': total_errors,
            'success_rate': ((len(records) - records_with_errors) / len(records) * 100) if records else 0,
            'most_common_errors': most_common_errors
        }

    def clear_rules(self) -> None:
        """Wyczyszczenie reguł walidacji"""
        self._validation_rules.clear()
        self._error_messages.clear()

# Funkcje pomocnicze wykorzystujące programowanie funkcyjne
def filter_valid_goals(goals_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtrowanie poprawnych celów - filter()"""

    def _is_valid_goal(goal: Dict[str, Any]) -> bool:
        """Wewnętrzna funkcja sprawdzania poprawności celu"""
        is_valid, _ = validate_goal_data(goal)
        return is_valid

    return list(filter(_is_valid_goal, goals_data))


def get_validation_statistics(data_list: List[Any], validator_func) -> Dict[str, int]:
    """Statystyki walidacji - map(), filter()"""
    # Mapowanie funkcji walidacji
    validation_results = list(map(validator_func, data_list))

    # Filtrowanie poprawnych i niepoprawnych
    valid_results = list(filter(lambda result: result[0], validation_results))
    invalid_results = list(filter(lambda result: not result[0], validation_results))

    return {
        'total': len(data_list),
        'valid': len(valid_results),
        'invalid': len(invalid_results),
        'success_rate': len(valid_results) / len(data_list) * 100 if data_list else 0
    }
