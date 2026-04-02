"""
PawPal+ - Core logic layer.

Classes:
    Task    -- A single pet care activity.
    Pet     -- A pet with a list of tasks.
    Owner   -- An owner who manages multiple pets.
    Scheduler -- Retrieves, sorts, filters, and manages tasks.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
import uuid


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a single pet care activity."""

    description: str
    time: str                   # "HH:MM" 24-hour format
    duration_minutes: int
    priority: str               # "low" | "medium" | "high"
    frequency: str              # "once" | "daily" | "weekly"
    completed: bool = False
    due_date: date = field(default_factory=date.today)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        pass

    def __repr__(self) -> str:
        return f"Task({self.time}, {self.description!r}, {self.priority})"


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Stores pet details and a list of associated tasks."""

    name: str
    species: str
    age: int
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        pass

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by its ID. Returns True if found and removed."""
        pass

    def get_tasks(self) -> list:
        """Return this pet's task list."""
        pass

    def __repr__(self) -> str:
        return f"Pet({self.name!r}, {self.species}, age={self.age})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.pets: list = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's collection."""
        pass

    def get_pets(self) -> list:
        """Return all pets belonging to this owner."""
        pass

    def get_all_tasks(self) -> list:
        """Return every (pet_name, Task) pair across all pets."""
        pass

    def __repr__(self) -> str:
        return f"Owner({self.name!r}, pets={len(self.pets)})"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Retrieves, organises, and manages tasks across all pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def get_daily_schedule(self) -> list:
        """Return all tasks sorted by time for today's schedule."""
        pass

    def sort_by_time(self, tasks: list) -> list:
        """Sort a list of (pet_name, Task) tuples by task time."""
        pass

    def filter_by_pet(self, pet_name: str) -> list:
        """Return tasks that belong to the named pet."""
        pass

    def filter_by_status(self, completed: bool) -> list:
        """Return tasks filtered by completion status."""
        pass

    def detect_conflicts(self) -> list:
        """Detect tasks sharing the same scheduled time. Returns conflict pairs."""
        pass

    def mark_task_complete(self, task_id: str) -> bool:
        """Mark a task done and auto-schedule the next occurrence if recurring."""
        pass

    def _generate_recurring_task(self, pet: Pet, completed_task: Task) -> None:
        """Create the next occurrence of a recurring task and add it to the pet."""
        pass
