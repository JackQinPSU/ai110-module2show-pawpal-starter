"""
Automated test suite for PawPal+ (pawpal_system.py).

Run with:  python -m pytest
"""

import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_owner_with_pets():
    """Return a fully wired Owner > Pet > Task structure for reuse."""
    owner = Owner("Jordan")

    dog = Pet("Mochi", "dog", 3)
    dog.add_task(Task("Evening walk",    "18:00", 30, "high",   "daily"))
    dog.add_task(Task("Morning walk",    "07:30", 20, "high",   "daily"))
    dog.add_task(Task("Flea medication", "09:00",  5, "high",   "weekly"))

    cat = Pet("Luna", "cat", 5)
    cat.add_task(Task("Feeding",  "07:00", 10, "high",   "daily"))
    cat.add_task(Task("Playtime", "09:00", 15, "medium", "daily"))   # same time as Flea med -> conflict

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner, dog, cat


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

class TestTask:
    def test_mark_complete_sets_flag(self):
        """mark_complete() must flip completed to True."""
        task = Task("Walk", "08:00", 20, "high", "daily")
        assert task.completed is False
        task.mark_complete()
        assert task.completed is True

    def test_mark_complete_is_idempotent(self):
        """Calling mark_complete() twice should not error and stay True."""
        task = Task("Walk", "08:00", 20, "high", "daily")
        task.mark_complete()
        task.mark_complete()
        assert task.completed is True


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

class TestPet:
    def test_add_task_increases_count(self):
        """add_task() must increase the pet's task list length by 1."""
        pet = Pet("Mochi", "dog", 3)
        assert len(pet.get_tasks()) == 0
        pet.add_task(Task("Walk", "08:00", 20, "high", "once"))
        assert len(pet.get_tasks()) == 1

    def test_remove_task_by_id(self):
        """remove_task() returns True and shrinks list when ID exists."""
        pet = Pet("Mochi", "dog", 3)
        task = Task("Walk", "08:00", 20, "high", "once")
        pet.add_task(task)
        result = pet.remove_task(task.id)
        assert result is True
        assert len(pet.get_tasks()) == 0

    def test_remove_task_missing_id_returns_false(self):
        """remove_task() returns False for an unknown ID."""
        pet = Pet("Mochi", "dog", 3)
        assert pet.remove_task("nonexistent") is False


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

class TestOwner:
    def test_add_pet_increases_count(self):
        owner = Owner("Jordan")
        assert len(owner.get_pets()) == 0
        owner.add_pet(Pet("Mochi", "dog", 3))
        assert len(owner.get_pets()) == 1

    def test_get_all_tasks_returns_pet_task_tuples(self):
        owner, dog, cat = make_owner_with_pets()
        all_tasks = owner.get_all_tasks()
        # Every item is a 2-tuple of (str, Task)
        for pet_name, task in all_tasks:
            assert isinstance(pet_name, str)
            assert isinstance(task, Task)

    def test_get_all_tasks_count(self):
        owner, dog, cat = make_owner_with_pets()
        total = len(dog.get_tasks()) + len(cat.get_tasks())
        assert len(owner.get_all_tasks()) == total

    def test_owner_with_no_pets_returns_empty(self):
        owner = Owner("Empty")
        assert owner.get_all_tasks() == []


# ---------------------------------------------------------------------------
# Scheduler: sorting
# ---------------------------------------------------------------------------

class TestSchedulerSorting:
    def test_sort_by_time_chronological(self):
        """Tasks added out of order must come back sorted by HH:MM."""
        owner, dog, cat = make_owner_with_pets()
        scheduler = Scheduler(owner)
        schedule = scheduler.get_daily_schedule()
        times = [task.time for _, task in schedule]
        assert times == sorted(times)

    def test_sort_empty_list(self):
        owner = Owner("Empty")
        scheduler = Scheduler(owner)
        assert scheduler.get_daily_schedule() == []


# ---------------------------------------------------------------------------
# Scheduler: filtering
# ---------------------------------------------------------------------------

class TestSchedulerFiltering:
    def test_filter_by_pet_name(self):
        owner, dog, cat = make_owner_with_pets()
        scheduler = Scheduler(owner)
        mochi_tasks = scheduler.filter_by_pet("Mochi")
        assert all(p == "Mochi" for p, _ in mochi_tasks)
        assert len(mochi_tasks) == len(dog.get_tasks())

    def test_filter_by_pet_case_insensitive(self):
        owner, dog, _ = make_owner_with_pets()
        scheduler = Scheduler(owner)
        assert len(scheduler.filter_by_pet("mochi")) == len(dog.get_tasks())

    def test_filter_by_pet_unknown_returns_empty(self):
        owner, _, _ = make_owner_with_pets()
        scheduler = Scheduler(owner)
        assert scheduler.filter_by_pet("Nemo") == []

    def test_filter_by_status_pending(self):
        owner, _, _ = make_owner_with_pets()
        scheduler = Scheduler(owner)
        pending = scheduler.filter_by_status(completed=False)
        assert all(not t.completed for _, t in pending)

    def test_filter_by_status_completed(self):
        owner, dog, _ = make_owner_with_pets()
        dog.get_tasks()[0].mark_complete()
        scheduler = Scheduler(owner)
        done = scheduler.filter_by_status(completed=True)
        assert len(done) == 1
        assert done[0][1].completed is True


# ---------------------------------------------------------------------------
# Scheduler: conflict detection
# ---------------------------------------------------------------------------

class TestSchedulerConflicts:
    def test_detects_same_time_conflict(self):
        """Flea medication (09:00) and Playtime (09:00) must be flagged."""
        owner, _, _ = make_owner_with_pets()
        scheduler = Scheduler(owner)
        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) == 1
        (p_a, t_a), (p_b, t_b) = conflicts[0]
        assert t_a.time == t_b.time == "09:00"

    def test_no_conflict_when_times_differ(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog", 3)
        pet.add_task(Task("Walk",    "07:00", 20, "high", "daily"))
        pet.add_task(Task("Feeding", "08:00", 10, "high", "daily"))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Scheduler: recurring tasks
# ---------------------------------------------------------------------------

class TestSchedulerRecurrence:
    def test_daily_task_creates_next_day_instance(self):
        """Completing a daily task must add a new task due tomorrow."""
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog", 3)
        today = date.today()
        task = Task("Walk", "07:30", 20, "high", "daily", due_date=today)
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        scheduler.mark_task_complete(task.id)

        tasks = pet.get_tasks()
        assert len(tasks) == 2
        new_task = tasks[1]
        assert new_task.completed is False
        assert new_task.due_date == today + timedelta(days=1)

    def test_weekly_task_creates_next_week_instance(self):
        """Completing a weekly task must add a new task due in 7 days."""
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog", 3)
        today = date.today()
        task = Task("Flea med", "09:00", 5, "high", "weekly", due_date=today)
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        scheduler.mark_task_complete(task.id)

        new_task = pet.get_tasks()[1]
        assert new_task.due_date == today + timedelta(weeks=1)

    def test_once_task_does_not_recur(self):
        """Completing a 'once' task must NOT add a new task."""
        owner = Owner("Jordan")
        pet = Pet("Luna", "cat", 5)
        task = Task("Vet visit", "10:00", 60, "high", "once")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        scheduler.mark_task_complete(task.id)

        assert len(pet.get_tasks()) == 1   # still just the original

    def test_mark_unknown_task_returns_false(self):
        owner = Owner("Jordan")
        owner.add_pet(Pet("Mochi", "dog", 3))
        scheduler = Scheduler(owner)
        assert scheduler.mark_task_complete("bad-id") is False
