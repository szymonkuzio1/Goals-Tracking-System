"""
Moduł formatowania danych wyjściowych
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Globalne zmienne formatowania
CURRENCY_SYMBOL = "zł"
DATE_FORMAT_DISPLAY = "%d.%m.%Y"
DATETIME_FORMAT_DISPLAY = "%d.%m.%Y %H:%M"
PROGRESS_BAR_LENGTH = 20


def format_progress_bar(current: float, target: float, length: int = PROGRESS_BAR_LENGTH) -> str:
    """
    Formatowanie paska postępu
    """

    def _calculate_filled_length(current_val: float, target_val: float, bar_length: int) -> int:
        """Wewnętrzna funkcja obliczania długości wypełnienia"""
        if target_val <= 0:
            return 0
        percentage = min(current_val / target_val, 1.0)
        return int(percentage * bar_length)

    try:
        assert target > 0, "Wartość docelowa musi być większa niż 0"
        assert length > 0, "Długość paska musi być większa niż 0"

        filled_length = _calculate_filled_length(current, target, length)
        percentage = min((current / target) * 100, 100)

        # Tworzenie paska postępu
        filled_bar = "█" * filled_length
        empty_bar = "░" * (length - filled_length)
        bar = filled_bar + empty_bar

        # Formatowanie z procentami
        return f"[{bar}] {percentage:.1f}% ({current:.1f}/{target:.1f})"

    except (AssertionError, ZeroDivisionError) as e:
        return f"[{'░' * length}] Błąd: {str(e)}"
    except Exception as e:
        return f"[{'░' * length}] Błąd formatowania: {str(e)}"


def format_date_display(date_obj: Union[datetime, str], include_time: bool = False) -> str:
    """Formatowanie daty do wyświetlenia"""

    def _parse_date_string(date_str: str) -> Optional[datetime]:
        """Wewnętrzna funkcja parsowania daty z łańcucha"""
        formats_to_try = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%d.%m.%Y',
            '%d/%m/%Y'
        ]

        for fmt in formats_to_try:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    try:
        # Konwersja do datetime jeśli to string
        if isinstance(date_obj, str):
            parsed_date = _parse_date_string(date_obj)
            if parsed_date is None:
                return "Nieprawidłowy format daty"
            date_obj = parsed_date

        # Sprawdzenie czy to datetime
        if not isinstance(date_obj, datetime):
            return "Nieprawidłowy typ daty"

        # Formatowanie
        if include_time:
            formatted = date_obj.strftime(DATETIME_FORMAT_DISPLAY)
        else:
            formatted = date_obj.strftime(DATE_FORMAT_DISPLAY)

        # Dodanie informacji o czasie relatywnym
        now = datetime.now()
        diff = now - date_obj

        if abs(diff.days) == 0:
            time_info = "dziś"
        elif diff.days == 1:
            time_info = "wczoraj"
        elif diff.days == -1:
            time_info = "jutro"
        elif diff.days > 0:
            time_info = f"{diff.days} dni temu"
        else:
            time_info = f"za {abs(diff.days)} dni"

        return f"{formatted} ({time_info})"

    except Exception as e:
        return f"Błąd formatowania daty: {str(e)}"


def format_goal_summary(goal_data: Dict[str, Any]) -> str:
    """Formatowanie podsumowania celu"""

    def _build_status_indicator(status: str) -> str:
        """Wewnętrzna funkcja budowania wskaźnika statusu"""
        status_indicators = {
            'aktywny': '🟢',
            'zakończony': '✅',
            'wstrzymany': '⏸️',
            'przeterminowany': '🔴'
        }
        return status_indicators.get(status.lower(), '❓')

    def _format_category_badge(category: str) -> str:
        """Wewnętrzna funkcja formatowania etykiety kategorii"""
        return f"[{category.upper()}]"

    try:
        # Sprawdzenie wymaganych pól
        required_fields = ['title', 'current_value', 'target_value']
        for field in required_fields:
            if field not in goal_data:
                return f"Brak wymaganego pola: {field}"

        title = str(goal_data['title']).strip()
        current = float(goal_data['current_value'])
        target = float(goal_data['target_value'])
        status = goal_data.get('status', 'aktywny')
        goal_type = goal_data.get('goal_type', 'Ogólny')

        # Obliczenie procentu postępu
        progress_percent = (current / target * 100) if target > 0 else 0

        # Budowanie podsumowania
        status_indicator = _build_status_indicator(status)
        type_badge = f"[{goal_type.upper()}]"
        progress_bar = format_progress_bar(current, target, 15)

        # Formatowanie głównej linii
        summary_lines = [
            f"{status_indicator} {title} {type_badge}",
            f"   {progress_bar}",
        ]

        # Dodanie informacji o terminie jeśli istnieje
        if 'deadline' in goal_data and goal_data['deadline']:
            deadline_str = format_date_display(goal_data['deadline'])
            summary_lines.append(f"   📅 Termin: {deadline_str}")

        # Dodanie opisu jeśli istnieje
        if 'description' in goal_data and goal_data['description']:
            desc = str(goal_data['description']).strip()
            if len(desc) > 50:
                desc = desc[:47] + "..."
            summary_lines.append(f"   💭 {desc}")

        return "\n".join(summary_lines)

    except Exception as e:
        return f"Błąd formatowania podsumowania celu: {str(e)}"


def format_currency(amount: float, currency: str = CURRENCY_SYMBOL) -> str:
    """
    Formatowanie kwoty w walucie
    """
    try:
        # Formatowanie z separatorami tysięcy
        if abs(amount) >= 1000:
            formatted_amount = f"{amount:,.2f}".replace(',', ' ')
        else:
            formatted_amount = f"{amount:.2f}"

        return f"{formatted_amount} {currency}"

    except Exception as e:
        return f"Błąd formatowania kwoty: {str(e)}"


class ProgressFormatter:
    """
    Klasa do formatowania postępów
    """

    def __init__(self, bar_length: int = 20):
        self.bar_length = bar_length

    def format_simple_progress(self, current: float, target: float) -> str:
        """Formatowanie postępu"""
        return format_progress_bar(current, target, self.bar_length)
