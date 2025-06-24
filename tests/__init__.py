"""
Pakiet testów dla Systemu Śledzenia Celów i Postępów
"""

import sys
import os

# Dodanie ścieżki do głównego pakietu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Globalne zmienne testowe
TEST_DATA_DIR = "test_data"
TEMP_FILES_DIR = "temp_test_files"
MOCK_USER_DATA = {
    'username': 'test_user',
    'email': 'test@example.com',
    'full_name': 'Test User'
}

# Helper funkcje dla testów
def create_test_goal_data():
    """Utworzenie testowych danych celu"""
    return {
        'title': 'Test Goal',
        'description': 'Test goal description',
        'target_value': 100.0,
        'current_value': 50.0,
        'category': 'Test',
        'status': 'aktywny'
    }

def cleanup_test_files():
    """Czyszczenie plików testowych"""
    import shutil
    for directory in [TEST_DATA_DIR, TEMP_FILES_DIR]:
        if os.path.exists(directory):
            shutil.rmtree(directory)

__all__ = [
    'TEST_DATA_DIR', 'TEMP_FILES_DIR', 'MOCK_USER_DATA',
    'create_test_goal_data', 'cleanup_test_files'
]
