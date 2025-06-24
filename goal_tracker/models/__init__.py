"""
Pakiet modeli do Systemu Śledzenia Celów i Postępów
"""

from .goal import Goal, PersonalGoal, BusinessGoal
from .progress import Progress

__all__ = [
    'Goal', 'PersonalGoal', 'BusinessGoal',
    'Progress'
]
