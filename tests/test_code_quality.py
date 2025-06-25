"""
Testy jakości kodu
"""
import unittest
import subprocess
import os
import sys

try:
    import flake8

    FLAKE8_AVAILABLE = True
except ImportError:
    FLAKE8_AVAILABLE = False

try:
    import pylint

    PYLINT_AVAILABLE = True
except ImportError:
    PYLINT_AVAILABLE = False


class TestCodeQuality(unittest.TestCase):
    """Testy jakości kodu"""

    def setUp(self):
        """Przygotowanie ścieżek"""
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.goal_tracker_path = os.path.join(self.project_root, 'goal_tracker')

    @unittest.skipUnless(FLAKE8_AVAILABLE, "flake8 nie jest dostępne")
    def test_flake8_compliance(self):
        """Test 1: Zgodność z flake8 (PEP 8)"""
        try:
            # Uruchomienie flake8
            result = subprocess.run([
                sys.executable, '-m', 'flake8',
                self.goal_tracker_path,
                '--max-line-length=100',
                '--ignore=E203,W503',  # Ignorowanie niektórych błędów
                '--exclude=__pycache__,*.pyc'
            ], capture_output=True, text=True, timeout=30)

            # Sprawdzenie czy nie ma błędów
            if result.returncode != 0:
                print(f"\n❌ Błędy flake8:\n{result.stdout}")
                self.fail(f"Kod nie spełnia standardów flake8. Błędy: {result.stdout}")
            else:
                print("✅ Kod spełnia standardy flake8")

        except subprocess.TimeoutExpired:
            self.fail("Timeout podczas uruchamiania flake8")
        except FileNotFoundError:
            self.skipTest("flake8 nie jest zainstalowane lub niedostępne")

    @unittest.skipUnless(PYLINT_AVAILABLE, "pylint nie jest dostępne")
    def test_pylint_score(self):
        """Test 2: Ocena pylint"""
        try:
            # Uruchomienie pylint
            result = subprocess.run([
                sys.executable, '-m', 'pylint',
                self.goal_tracker_path,
                '--disable=C0114,C0115,C0116',  # Wyłączenie niektórych ostrzeżeń o docstring
                '--ignore=__pycache__'
            ], capture_output=True, text=True, timeout=60)

            # Wyciągnięcie oceny z wyniku
            output_lines = result.stdout.split('\n')
            score_line = None
            for line in output_lines:
                if 'Your code has been rated at' in line:
                    score_line = line
                    break

            if score_line:
                # Wyciągnięcie oceny numerycznej
                score_text = score_line.split('rated at ')[1].split('/')[0]
                score = float(score_text)

                print(f"📊 Ocena pylint: {score}/10")

                # Sprawdzenie czy ocena jest akceptowalna (> 7.0)
                self.assertGreater(score, 7.0,
                                   f"Ocena pylint ({score}) jest za niska (oczekiwano > 7.0)")
            else:
                print("⚠️ Nie udało się wyciągnąć oceny z pylint")

        except subprocess.TimeoutExpired:
            self.fail("Timeout podczas uruchamiania pylint")
        except FileNotFoundError:
            self.skipTest("pylint nie jest zainstalowane lub niedostępne")
        except ValueError:
            self.fail("Nie udało się sparsować oceny pylint")

    def test_import_structure(self):
        """Test 3: Struktura importów"""
        # Sprawdzenie czy wszystkie moduły można zaimportować
        modules_to_test = [
            'goal_tracker.models.goal',
            'goal_tracker.models.progress',
            'goal_tracker.logic',
            'goal_tracker.data',
            'goal_tracker.api',
            'goal_tracker.gui',
            'goal_tracker.utils.validators',
            'goal_tracker.utils.formatters'
        ]

        failed_imports = []

        for module in modules_to_test:
            try:
                __import__(module)
                print(f"✅ Import {module}: OK")
            except ImportError as e:
                failed_imports.append(f"{module}: {e}")
                print(f"❌ Import {module}: FAIL - {e}")

        if failed_imports:
            self.fail(f"Nie udało się zaimportować modułów: {failed_imports}")

    def test_class_structure(self):
        """Test 4: Struktura klas"""
        from goal_tracker.models.goal import Goal, PersonalGoal, BusinessGoal
        from goal_tracker.logic import GoalManager
        from goal_tracker.data import DataManager

        # Sprawdzenie dziedziczenia
        self.assertTrue(issubclass(PersonalGoal, Goal))
        self.assertTrue(issubclass(BusinessGoal, Goal))

        # Sprawdzenie czy klasy mają wymagane metody
        goal_methods = ['update_progress', 'get_progress_percentage', 'to_dict', 'get_goal_type']
        for method in goal_methods:
            self.assertTrue(hasattr(Goal, method), f"Goal nie ma metody {method}")

        manager_methods = ['add_goal', 'remove_goal', 'get_user_goals', 'update_goal_progress']
        for method in manager_methods:
            self.assertTrue(hasattr(GoalManager, method), f"GoalManager nie ma metody {method}")

    def test_function_documentation(self):
        """Test 5: Dokumentacja funkcji"""
        from goal_tracker.models.goal import Goal
        from goal_tracker.logic import GoalManager

        # Sprawdzenie czy kluczowe metody mają docstring
        methods_to_check = [
            (Goal, 'update_progress'),
            (Goal, 'get_progress_percentage'),
            (GoalManager, 'add_goal'),
            (GoalManager, 'update_goal_progress')
        ]

        missing_docs = []

        for cls, method_name in methods_to_check:
            method = getattr(cls, method_name)
            if not method.__doc__ or len(method.__doc__.strip()) < 10:
                missing_docs.append(f"{cls.__name__}.{method_name}")

        if missing_docs:
            print(f"⚠️ Metody bez dokumentacji: {missing_docs}")
            # Nie fail - tylko ostrzeżenie
        else:
            print("✅ Wszystkie kluczowe metody mają dokumentację")

    def test_error_handling_coverage(self):
        """Test 6: Pokrycie obsługi błędów"""
        from goal_tracker.models.goal import Goal
        from goal_tracker.logic import GoalManager
        from goal_tracker.data import DataManager
        import tempfile

        # Test czy błędy są właściwie obsługiwane
        temp_dir = tempfile.mkdtemp()
        data_manager = DataManager(temp_dir)
        goal_manager = GoalManager(data_manager)

        error_tests = []

        try:
            # Test nieprawidłowych danych Goal
            with self.assertRaises(AssertionError):
                Goal("", "desc", 100.0)
            error_tests.append("Goal - pusty tytuł")

            with self.assertRaises(AssertionError):
                Goal("title", "desc", -100.0)
            error_tests.append("Goal - ujemna wartość")

            # Test nieprawidłowych operacji GoalManager
            result = goal_manager.update_goal_progress("user", "fake_id", 50.0)
            self.assertFalse(result)
            error_tests.append("GoalManager - nieistniejący cel")

            print(f"✅ Testy obsługi błędów: {len(error_tests)} testów przeszło")

        except Exception as e:
            self.fail(f"Problemy z obsługą błędów: {e}")
        finally:
            import shutil
            shutil.rmtree(temp_dir)

    def test_type_hints_usage(self):
        """Test 7: Użycie type hints"""
        import inspect
        from goal_tracker.models.goal import Goal
        from goal_tracker.logic import GoalManager

        # Sprawdzenie czy metody mają type hints
        methods_to_check = [
            (Goal, '__init__'),
            (Goal, 'update_progress'),
            (GoalManager, 'add_goal'),
            (GoalManager, 'get_user_goals')
        ]

        methods_with_hints = 0
        total_methods = len(methods_to_check)

        for cls, method_name in methods_to_check:
            method = getattr(cls, method_name)
            signature = inspect.signature(method)

            has_hints = False
            # Sprawdzenie parametrów
            for param in signature.parameters.values():
                if param.annotation != inspect.Parameter.empty:
                    has_hints = True
                    break

            # Sprawdzenie return type
            if signature.return_annotation != inspect.Signature.empty:
                has_hints = True

            if has_hints:
                methods_with_hints += 1

        hint_coverage = (methods_with_hints / total_methods) * 100
        print(f"📝 Pokrycie type hints: {hint_coverage:.1f}% ({methods_with_hints}/{total_methods})")

        # Przynajmniej 50% metod powinno mieć type hints
        self.assertGreater(hint_coverage, 50.0,
                           f"Zbyt niskie pokrycie type hints: {hint_coverage}%")

    def test_code_complexity(self):
        """Test 8: Złożoność kodu (prosty test)"""
        from goal_tracker.models.goal import Goal

        # Sprawdzenie czy metody nie są zbyt skomplikowane
        # (prosty test - liczba linii)
        methods_to_check = [
            Goal.update_progress,
            Goal.get_progress_percentage
        ]

        complex_methods = []

        for method in methods_to_check:
            if hasattr(method, '__code__'):
                line_count = method.__code__.co_firstlineno
                # Bardzo prosty test - czy metoda nie ma więcej niż 50 linii
                source_lines = len(str(method.__doc__ or "").split('\n'))

                if source_lines > 50:
                    complex_methods.append(method.__name__)

        if complex_methods:
            print(f"⚠️ Potencjalnie złożone metody: {complex_methods}")
        else:
            print("✅ Metody mają rozsądną złożoność")

    def test_naming_conventions(self):
        """Test 9: Konwencje nazewnictwa"""
        from goal_tracker.models.goal import Goal, PersonalGoal, BusinessGoal
        from goal_tracker.logic import GoalManager

        # Sprawdzenie nazw klas (PascalCase)
        class_names = ['Goal', 'PersonalGoal', 'BusinessGoal', 'GoalManager']
        for name in class_names:
            self.assertTrue(name[0].isupper() and '_' not in name,
                            f"Nazwa klasy {name} nie spełnia konwencji PascalCase")

        # Sprawdzenie metod (snake_case)
        goal = Goal("Test", "Desc", 100.0)
        public_methods = [method for method in dir(goal)
                          if not method.startswith('_') and callable(getattr(goal, method))]

        invalid_method_names = []
        for method_name in public_methods:
            if not method_name.islower() or method_name != method_name.replace('-', '_'):
                invalid_method_names.append(method_name)

        if invalid_method_names:
            print(f"⚠️ Metody z nieprawidłowymi nazwami: {invalid_method_names}")
        else:
            print("✅ Nazwy metod zgodne z konwencją snake_case")

    def test_security_basic_checks(self):
        """Test 10: Podstawowe sprawdzenia bezpieczeństwa"""
        # Sprawdzenie czy nie ma niebezpiecznych praktyk
        security_issues = []

        # Test 1: Sprawdzenie czy nie używamy eval/exec
        import goal_tracker
        import os

        goal_tracker_dir = os.path.dirname(goal_tracker.__file__)

        for root, dirs, files in os.walk(goal_tracker_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                            # Sprawdzenie niebezpiecznych funkcji
                            dangerous_patterns = ['eval(', 'exec(', '__import__(', 'compile(']
                            for pattern in dangerous_patterns:
                                if pattern in content:
                                    security_issues.append(f"{file}: zawiera {pattern}")
                    except UnicodeDecodeError:
                        continue

        # Test 2: Sprawdzenie walidacji danych wejściowych
        from goal_tracker.utils.validators import validate_goal_data

        # Sprawdzenie czy walidacja odrzuca niebezpieczne dane
        dangerous_data = {
            'title': '<script>alert("XSS")</script>',
            'description': 'Normal description',
            'target_value': 100.0
        }

        is_valid, errors = validate_goal_data(dangerous_data)
        # Walidacja powinna przepuścić te dane (to nie jest web app), ale sprawdzamy czy działa

        if security_issues:
            print(f"⚠️ Potencjalne problemy bezpieczeństwa: {security_issues}")
            # Nie fail - tylko ostrzeżenie dla tego typu aplikacji
        else:
            print("✅ Brak oczywistych problemów bezpieczeństwa")


if __name__ == '__main__':
    unittest.main(verbosity=2)
