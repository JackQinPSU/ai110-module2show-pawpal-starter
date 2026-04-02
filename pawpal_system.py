"""
PawPal+ - Core logic layer.

Classes:
    Task      -- A single pet care activity.
    Pet       -- A pet with a list of tasks.
    Owner     -- An owner who manages multiple pets.
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
        self.completed = True

    def __repr__(self) -> str:
        status = "DONE" if self.completed else "TODO"
        return (
            f"[{status}] {self.time} | {self.description} "
            f"({self.duration_minutes}min, {self.priority}, {self.frequency})"
        )


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
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by its ID. Returns True if found and removed."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks.pop(i)
                return True
        return False

    def get_tasks(self) -> list:
        """Return this pet's task list."""
        return self.tasks

    def __repr__(self) -> str:
        return f"Pet({self.name!r}, {self.species}, age={self.age}, tasks={len(self.tasks)})"


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
        self.pets.append(pet)

    def get_pets(self) -> list:
        """Return all pets belonging to this owner."""
        return self.pets

    def get_all_tasks(self) -> list:
        """Return every (pet_name, Task) pair across all pets."""
        result = []
        for pet in self.pets:
            for task in pet.get_tasks():
                result.append((pet.name, task))
        return result

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
        return self.sort_by_time(self.owner.get_all_tasks())

    def sort_by_time(self, tasks: list) -> list:
        """Sort a list of (pet_name, Task) tuples chronologically by task time."""
        return sorted(tasks, key=lambda item: item[1].time)

    def filter_by_pet(self, pet_name: str) -> list:
        """Return tasks that belong to the named pet (case-insensitive)."""
        return [
            (p, t)
            for p, t in self.owner.get_all_tasks()
            if p.lower() == pet_name.lower()
        ]

    def filter_by_status(self, completed: bool) -> list:
        """Return tasks filtered by completion status."""
        return [
            (p, t)
            for p, t in self.owner.get_all_tasks()
            if t.completed == completed
        ]

    def detect_conflicts(self) -> list:
        """
        Detect tasks sharing the same scheduled time.

        Returns a list of conflict pairs:
            [((pet_a, task_a), (pet_b, task_b)), ...]
        """
        seen: dict = {}
        conflicts = []
        for pet_name, task in self.owner.get_all_tasks():
            key = task.time
            if key in seen:
                conflicts.append((seen[key], (pet_name, task)))
            else:
                seen[key] = (pet_name, task)
        return conflicts

    def mark_task_complete(self, task_id: str) -> bool:
        """Mark a task done and auto-schedule the next occurrence if recurring."""
        for pet in self.owner.get_pets():
            for task in pet.get_tasks():
                if task.id == task_id:
                    task.mark_complete()
                    if task.frequency in ("daily", "weekly"):
                        self._generate_recurring_task(pet, task)
                    return True
        return False

    def _generate_recurring_task(self, pet: Pet, completed_task: Task) -> None:
        """Create the next occurrence of a recurring task and add it to the pet."""
        delta = (
            timedelta(days=1)
            if completed_task.frequency == "daily"
            else timedelta(weeks=1)
        )
        next_task = Task(
            description=completed_task.description,
            time=completed_task.time,
            duration_minutes=completed_task.duration_minutes,
            priority=completed_task.priority,
            frequency=completed_task.frequency,
            due_date=completed_task.due_date + delta,
        )
        pet.add_task(next_task)
