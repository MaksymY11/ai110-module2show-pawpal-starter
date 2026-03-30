"""
main.py — Testing ground for PawPal+ logic.
Run with: python main.py
"""

from datetime import time
from pawpal_system import Pet, Task, TaskList, Owner, Scheduler


# --- Owner ---
owner = Owner("Jordan", 90, time(7, 0), time(12, 0))

# --- Pets ---
mochi = Pet("Mochi", "dog", 3, "loves walks and belly rubs")
whiskers = Pet("Whiskers", "cat", 5, "indoor only, very picky eater")

print(mochi.get_summary())
print(whiskers.get_summary())
print()

# --- Tasks for Mochi ---
mochi_tasks = TaskList(mochi)
mochi_tasks.add_task(Task("m1", "Morning walk", "walk", 30, "high"))
mochi_tasks.add_task(Task("m2", "Breakfast", "feeding", 10, "high"))
mochi_tasks.add_task(Task("m3", "Brush coat", "grooming", 15, "medium"))

# --- Tasks for Whiskers ---
whiskers_tasks = TaskList(whiskers)
whiskers_tasks.add_task(Task("w1", "Breakfast", "feeding", 10, "high"))
whiskers_tasks.add_task(Task("w2", "Play with laser pointer", "enrichment", 20, "medium"))
whiskers_tasks.add_task(Task("w3", "Administer flea meds", "medication", 5, "high"))

# --- Generate and print schedules ---
for task_list in [mochi_tasks, whiskers_tasks]:
    scheduler = Scheduler(owner, task_list)
    plan = scheduler.generate_plan()

    print("=" * 50)
    print(plan.display())
    print()
    print(scheduler.explain_plan())
    print()
