"""
System Śledzenia Celów i Postępów
Główny pakiet aplikacji
"""

from .models.goal import Goal, PersonalGoal, BusinessGoal
from .models.progress import Progress
from .utils.validators import validate_goal_data
from .utils.formatters import format_progress_bar, format_goal_summary

# Zmienne globalne konfiguracyjne
APP_NAME = "System Śledzenia Celów i Postępów"
VERSION = "1.0.0"
DEFAULT_DATA_PATH = "data/"
MAX_GOALS_PER_USER = 50
DEBUG_MODE = False

# Eksportowane klasy i funkcje
__all__ = [
    # Modele
    'Goal', 'PersonalGoal', 'BusinessGoal',
    'Progress',
    # Narzędzia
    'validate_goal_data',
    'format_progress_bar', 'format_goal_summary',
    # Konfiguracja
    'APP_NAME', 'VERSION', 'DEFAULT_DATA_PATH', 'MAX_GOALS_PER_USER'
]

def get_app_info() -> dict:
    """Zwraca informacje o aplikacji"""
    return {
        'name': APP_NAME,
        'version': VERSION,
        'debug_mode': DEBUG_MODE,
        'max_goals_per_user': MAX_GOALS_PER_USER
    }

def set_debug_mode(enabled: bool) -> None:
    """Ustawienie trybu debugowania"""
    global DEBUG_MODE
    DEBUG_MODE = enabled
