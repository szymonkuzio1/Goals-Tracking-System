"""
Testy pamięci
"""
import unittest
import tempfile
import shutil
import gc
import sys

try:
    from memory_profiler import profile, memory_usage
    import psutil

    MEMORY_TESTING_AVAILABLE = True
except ImportError:
    MEMORY_TESTING_AVAILABLE = False
    print("⚠️ Brak bibliotek memory_profiler/psutil. Zainstaluj: pip install memory-profiler psutil")

from goal_tracker.models.goal import Goal, PersonalGoal, BusinessGoal
from goal_tracker.logic import GoalManager
from goal_tracker.data import DataManager


@unittest.skipUnless(MEMORY_TESTING_AVAILABLE, "memory_profiler nie jest dostępne")
class TestMemoryUsage(unittest.TestCase):
    """Testy wykorzystania pamięci"""

    def setUp(self):
        """Przygotowanie środowiska"""
        self.test_dir = tempfile.mkdtemp()
        self.data_manager = DataManager(self.test_dir)
        self.goal_manager = GoalManager(self.data_manager)
        self.test_user = "default"
        gc.collect()  # Czyszczenie pamięci przed testami

    def tearDown(self):
        """Czyszczenie"""
        if self.test_dir:
            shutil.rmtree(self.test_dir)
        gc.collect()

    def get_memory_usage(self):
        """Pomocnicza funkcja do pomiaru pamięci"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB

    def test_goal_creation_memory_usage(self):
        """Test 1: Zużycie pamięci przy tworzeniu celów"""
        initial_memory = self.get_memory_usage()

        # Tworzenie 1000 celów
        for i in range(1000):
            goal = Goal(f"Memory Test Goal {i}", f"Description {i}", 100.0)
            self.goal_manager.add_goal(self.test_user, goal)

        final_memory = self.get_memory_usage()
        memory_increase = final_memory - initial_memory

        # Sprawdzenie czy wzrost pamięci jest rozsądny (< 50MB dla 1000 celów)
        self.assertLess(memory_increase, 50.0,
                        f"Tworzenie 1000 celów zwiększyło pamięć o {memory_increase:.2f}MB "
                        f"(oczekiwano < 50MB)")

        print(f"💾 Wzrost pamięci dla 1000 celów: {memory_increase:.2f}MB")

    def test_memory_leak_detection(self):
        """Test 2: Wykrywanie wycieków pamięci"""
        initial_memory = self.get_memory_usage()

        # Cykl tworzenia i usuwania celów
        for cycle in range(10):
            # Dodaj cele
            goals = []
            for i in range(100):
                goal = Goal(f"Leak Test {cycle}_{i}", f"Desc {i}", 100.0)
                self.goal_manager.add_goal(self.test_user, goal)
                goals.append(goal)

            # Usuń cele
            for goal in goals:
                self.goal_manager.remove_goal(self.test_user, goal.id)

            # Wymuś czyszczenie pamięci
            gc.collect()

        final_memory = self.get_memory_usage()
        memory_increase = final_memory - initial_memory

        # Po cyklach tworzenia/usuwania pamięć powinna wrócić do poziomu początkowego
        self.assertLess(memory_increase, 5.0,
                        f"Po cyklach tworzenia/usuwania pamięć wzrosła o {memory_increase:.2f}MB "
                        f"(oczekiwano < 5MB - możliwy wyciek)")

        print(f"🔍 Test wycieku pamięci: wzrost {memory_increase:.2f}MB")

    def test_large_data_memory_efficiency(self):
        """Test 3: Efektywność pamięciowa dużych danych"""

        def create_large_dataset():
            for i in range(5000):
                goal = Goal(f"Large Data Goal {i}", f"Very long description {i}" * 10, 100.0)
                goal.update_progress(i % 100)
                self.goal_manager.add_goal(self.test_user, goal)

        # Pomiar zużycia pamięci podczas tworzenia dużego zestawu
        memory_before = self.get_memory_usage()
        mem_usage = memory_usage(create_large_dataset, interval=0.1)
        memory_after = self.get_memory_usage()

        max_memory = max(mem_usage)
        final_increase = memory_after - memory_before

        # Sprawdzenie czy zużycie pamięci jest rozsądne
        self.assertLess(final_increase, 200.0,
                        f"5000 celów zwiększyło pamięć o {final_increase:.2f}MB "
                        f"(oczekiwano < 200MB)")

        print(f"📊 Zużycie pamięci dla 5000 celów: {final_increase:.2f}MB (max: {max_memory:.2f}MB)")

    def test_data_serialization_memory(self):
        """Test 4: Zużycie pamięci podczas serializacji"""
        # Przygotowanie danych
        for i in range(1000):
            goal = Goal(f"Serialization Test {i}", f"Description {i}", 100.0)
            goal.update_progress(i % 100)
            self.goal_manager.add_goal(self.test_user, goal)

        def serialize_data():
            goals = self.goal_manager.get_user_goals(self.test_user)
            goals_data = [g.to_dict() for g in goals]
            return self.data_manager.save_goals_data(goals_data, self.test_user)

        # Pomiar pamięci podczas serializacji
        memory_before = self.get_memory_usage()
        mem_usage = memory_usage(serialize_data, interval=0.1)
        memory_after = self.get_memory_usage()

        max_memory_during = max(mem_usage)

        # Sprawdzenie czy serializacja nie powoduje ekstremalnego wzrostu pamięci
        memory_spike = max_memory_during - memory_before
        self.assertLess(memory_spike, 100.0,
                        f"Serializacja 1000 celów spowodowała wzrost pamięci o {memory_spike:.2f}MB "
                        f"(oczekiwano < 100MB)")

        print(f"💾 Wzrost pamięci podczas serializacji: {memory_spike:.2f}MB")

    def test_goal_history_memory_impact(self):
        """Test 5: Wpływ historii celów na pamięć"""
        goal = Goal("History Memory Test", "Test wpływu historii", 100.0)
        self.goal_manager.add_goal(self.test_user, goal)

        memory_before = self.get_memory_usage()

        # Dodanie dużej liczby wpisów historii
        for i in range(1000):
            self.goal_manager.update_goal_progress(self.test_user, goal.id, float(i % 100))

        memory_after = self.get_memory_usage()
        memory_increase = memory_after - memory_before

        # Sprawdzenie wpływu historii na pamięć
        self.assertLess(memory_increase, 10.0,
                        f"1000 wpisów historii zwiększyło pamięć o {memory_increase:.2f}MB "
                        f"(oczekiwano < 10MB)")

        # Sprawdzenie czy historia została zapisana
        updated_goal = self.goal_manager.get_user_goals(self.test_user)[0]
        self.assertEqual(len(updated_goal.get_history()), 1000)

        print(f"📝 Wpływ historii na pamięć: {memory_increase:.2f}MB")

    def test_multiple_goal_types_memory(self):
        """Test 6: Zużycie pamięci różnych typów celów"""
        memory_before = self.get_memory_usage()

        # Tworzenie różnych typów celów
        for i in range(500):
            if i % 3 == 0:
                goal = Goal(f"General {i}", f"Desc {i}", 100.0)
            elif i % 3 == 1:
                goal = PersonalGoal(f"Personal {i}", f"Desc {i}", 100.0)
            else:
                goal = BusinessGoal(f"Business {i}", f"Desc {i}", 100.0)

            self.goal_manager.add_goal(self.test_user, goal)

        memory_after = self.get_memory_usage()
        memory_increase = memory_after - memory_before

        # Sprawdzenie czy różne typy celów nie powodują nadmiernego zużycia pamięci
        self.assertLess(memory_increase, 30.0,
                        f"500 celów różnych typów zwiększyło pamięć o {memory_increase:.2f}MB "
                        f"(oczekiwano < 30MB)")

        print(f"🎯 Zużycie pamięci dla różnych typów celów: {memory_increase:.2f}MB")

    def test_data_loading_memory_efficiency(self):
        """Test 7: Efektywność pamięciowa ładowania danych"""
        # Najpierw utwórz i zapisz dane
        for i in range(1000):
            goal = Goal(f"Load Test Goal {i}", f"Description {i}", 100.0)
            self.goal_manager.add_goal(self.test_user, goal)

        goals = self.goal_manager.get_user_goals(self.test_user)
        goals_data = [g.to_dict() for g in goals]
        self.data_manager.save_goals_data(goals_data, self.test_user)

        # Wyczyść pamięć
        self.goal_manager = GoalManager(self.data_manager)
        gc.collect()

        def load_data():
            return self.goal_manager.load_goals_from_data_manager(self.test_user)

        # Pomiar pamięci podczas ładowania
        memory_before = self.get_memory_usage()
        mem_usage = memory_usage(load_data, interval=0.1)
        memory_after = self.get_memory_usage()

        memory_increase = memory_after - memory_before

        # Sprawdzenie efektywności ładowania
        self.assertLess(memory_increase, 50.0,
                        f"Ładowanie 1000 celów zwiększyło pamięć o {memory_increase:.2f}MB "
                        f"(oczekiwano < 50MB)")

        print(f"📁 Zużycie pamięci podczas ładowania: {memory_increase:.2f}MB")

    def test_concurrent_operations_memory(self):
        """Test 8: Pamięć podczas operacji współbieżnych (symulacja)"""
        memory_before = self.get_memory_usage()

        # Symulacja wielu użytkowników
        users = [f"user_{i}" for i in range(20)]

        for user in users:
            for i in range(50):
                goal = Goal(f"Concurrent Goal {i}", f"Description {i}", 100.0)
                self.goal_manager.add_goal(user, goal)

        memory_after = self.get_memory_usage()
        memory_increase = memory_after - memory_before

        total_goals = 20 * 50  # 1000 celów

        # Sprawdzenie czy operacje współbieżne nie powodują nadmiernego zużycia pamięci
        self.assertLess(memory_increase, 80.0,
                        f"{total_goals} celów dla {len(users)} użytkowników zwiększyło pamięć "
                        f"o {memory_increase:.2f}MB (oczekiwano < 80MB)")

        print(f"👥 Symulacja wielu użytkowników: {memory_increase:.2f}MB")

    def test_memory_cleanup_after_operations(self):
        """Test 9: Czyszczenie pamięci po operacjach"""
        initial_memory = self.get_memory_usage()

        # Seria operacji
        for i in range(100):
            goal = Goal(f"Cleanup Test {i}", f"Description {i}", 100.0)
            self.goal_manager.add_goal(self.test_user, goal)

            # Aktualizuj postęp
            self.goal_manager.update_goal_progress(self.test_user, goal.id, 50.0)

            # Usuń cel
            self.goal_manager.remove_goal(self.test_user, goal.id)

        # Wymuś czyszczenie pamięci
        gc.collect()

        final_memory = self.get_memory_usage()
        memory_difference = final_memory - initial_memory

        # Po operacjach i czyszczeniu pamięć powinna być bliska początkowej
        self.assertLess(abs(memory_difference), 3.0,
                        f"Po operacjach i czyszczeniu różnica pamięci: {memory_difference:.2f}MB "
                        f"(oczekiwano < 3MB)")

        print(f"🧹 Efektywność czyszczenia pamięci: {memory_difference:.2f}MB")

    def test_system_memory_limits(self):
        """Test 10: Limity pamięci systemu"""
        # Sprawdź dostępną pamięć
        available_memory = psutil.virtual_memory().available / 1024 / 1024  # MB

        if available_memory < 500:  # Jeśli mniej niż 500MB dostępnej pamięci
            self.skipTest("Niewystarczająca ilość dostępnej pamięci dla testu")

        initial_memory = self.get_memory_usage()

        # Test z dużą liczbą celów (ale bezpieczną dla systemu)
        safe_limit = min(2000, int(available_memory / 10))  # Bezpieczny limit

        for i in range(safe_limit):
            goal = Goal(f"Memory Limit Test {i}", f"Description {i}", 100.0)
            self.goal_manager.add_goal(self.test_user, goal)

        final_memory = self.get_memory_usage()
        memory_per_goal = (final_memory - initial_memory) / safe_limit

        # Sprawdzenie czy pamięć na cel jest rozsądna
        self.assertLess(memory_per_goal, 0.1,  # < 0.1MB na cel
                        f"Pamięć na cel: {memory_per_goal:.4f}MB (oczekiwano < 0.1MB)")

        print(f"🎯 Pamięć na cel: {memory_per_goal:.4f}MB (testowano {safe_limit} celów)")


if __name__ == '__main__':
    unittest.main(verbosity=2)
