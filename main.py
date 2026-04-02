"""
main.py -- CLI demo script for PawPal+.

Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def print_schedule(schedule: list, title: str = "Today's Schedule") -> None:
    """Pretty-print a (pet_name, Task) schedule to the terminal."""
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print("=" * 50)
    if not schedule:
        print("  (no tasks)")
    for pet_name, task in schedule:
        status = "DONE" if task.completed else "TODO"
        print(
            f"  [{status}] {task.time}  {pet_name:<10}  "
            f"{task.description:<25}  {task.duration_minutes}min  "
            f"[{task.priority}]  [{task.frequency}]"
        )
    print("=" * 50)


def main() -> None:
    # --- Set up owner and pets ---
    owner = Owner("Jordan")

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)

    owner.add_pet(mochi)
    owner.add_pet(luna)

    # --- Add tasks (intentionally out of chronological order) ---
    mochi.add_task(Task("Evening walk",  "18:00", 30, "high",   "daily"))
    mochi.add_task(Task("Morning walk",  "07:30", 20, "high",   "daily"))
    mochi.add_task(Task("Flea medication","09:00", 5,  "high",   "weekly"))
    mochi.add_task(Task("Dental chew",   "20:00", 5,  "low",    "daily"))

    luna.add_task(Task("Feeding",        "07:00", 10, "high",   "daily"))
    luna.add_task(Task("Playtime",       "09:00", 15, "medium", "daily"))   # <- conflict with Mochi at 09:00
    luna.add_task(Task("Grooming",       "14:00", 20, "medium", "once"))

    scheduler = Scheduler(owner)

    # --- Full sorted schedule ---
    print_schedule(scheduler.get_daily_schedule())

    # --- Conflict detection ---
    conflicts = scheduler.detect_conflicts()
    print("\n--- Conflict Warnings ---")
    if conflicts:
        for (pet_a, task_a), (pet_b, task_b) in conflicts:
            print(
                f"  [CONFLICT] {pet_a}'s '{task_a.description}' and "
                f"{pet_b}'s '{task_b.description}' are both scheduled at {task_a.time}"
            )
    else:
        print("  No conflicts found.")

    # --- Filter by pet ---
    print_schedule(scheduler.filter_by_pet("Mochi"), title="Mochi's Tasks")

    # --- Filter pending (incomplete) tasks ---
    print_schedule(scheduler.filter_by_status(completed=False), title="Pending Tasks")

    # --- Mark a recurring task complete and show auto-rescheduling ---
    morning_walk_id = mochi.get_tasks()[1].id   # "Morning walk" task
    print(f"\nMarking 'Morning walk' (id={morning_walk_id}) as complete...")
    scheduler.mark_task_complete(morning_walk_id)
    print(f"Mochi now has {len(mochi.get_tasks())} tasks (one new recurring instance added).")
    print_schedule(scheduler.filter_by_pet("Mochi"), title="Mochi's Tasks (after completion)")


if __name__ == "__main__":
    main()
