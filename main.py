"""
main.py — Testing ground for PawPal+ logic.
Run with: python main.py
"""

from datetime import date, time
from pawpal_system import (
    Pet, Task, TaskList, Owner, Scheduler,
    filter_tasks, detect_cross_pet_conflicts,
)


# --- Owner ---
owner = Owner("Jordan", 90, time(7, 0), time(12, 0))

# --- Pets ---
mochi = Pet("Mochi", "dog", 3, "loves walks and belly rubs")
whiskers = Pet("Whiskers", "cat", 5, "indoor only, very picky eater")

print(mochi.get_summary())
print(whiskers.get_summary())
print()

# --- Tasks for Mochi (added out of priority order on purpose) ---
today = date.today()
mochi_tasks = TaskList(mochi)
mochi_tasks.add_task(Task("m1", "Brush coat", "grooming", 15, "medium"))
mochi_tasks.add_task(Task("m2", "Morning walk", "walk", 30, "high",
                          is_recurring=True, recurrence="daily", due_date=today))
mochi_tasks.add_task(Task("m3", "Breakfast", "feeding", 10, "high",
                          is_recurring=True, recurrence="daily", due_date=today))

# --- Tasks for Whiskers (added out of priority order on purpose) ---
whiskers_tasks = TaskList(whiskers)
whiskers_tasks.add_task(Task("w1", "Play with laser pointer", "enrichment", 20, "medium"))
whiskers_tasks.add_task(Task("w2", "Administer flea meds", "medication", 5, "high",
                             is_recurring=True, recurrence="weekly", due_date=today))
whiskers_tasks.add_task(Task("w3", "Breakfast", "feeding", 10, "high",
                             is_recurring=True, recurrence="daily", due_date=today))

# --- Generate, sort, and print schedules ---
schedulers = []
for task_list in [mochi_tasks, whiskers_tasks]:
    scheduler = Scheduler(owner, task_list)
    plan = scheduler.generate_plan()
    schedulers.append(scheduler)

    print("=" * 50)
    print("BEFORE sort_by_time():")
    print(plan.display())
    print()

    # Sort scheduled tasks chronologically by start time (HH:MM)
    scheduler.sort_by_time()

    print("AFTER sort_by_time():")
    print(plan.display())
    print()
    print(scheduler.explain_plan())
    print()

# --- Conflict detection demo ---
print("=" * 50)
print("CONFLICT DETECTION DEMO\n")

# Inject a deliberate same-pet overlap: add a task to Mochi's plan at 07:10,
# which overlaps with "Morning walk" (07:00-07:30 already scheduled).
mochi_scheduler = schedulers[0]
overlap_task = Task("m4", "Nail trim", "grooming", 15, "high")
mochi_scheduler.generated_plan.scheduled_tasks.append((overlap_task, time(7, 10)))

print("Same-pet conflict check (Mochi):")
mochi_conflicts = mochi_scheduler.detect_conflicts()
if mochi_conflicts:
    for warning in mochi_conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts found.")

# Cross-pet conflict check: Mochi and Whiskers both start at 07:00
print("\nCross-pet conflict check (Mochi + Whiskers):")
cross_conflicts = detect_cross_pet_conflicts(schedulers)
if cross_conflicts:
    for warning in cross_conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts found.")
print()

# --- Mark tasks complete (recurring ones auto-create next occurrence) ---
print("=" * 50)
print("RECURRING TASK DEMO\n")

# Non-recurring task — no new instance created
result = mochi_tasks.complete_task("m1")  # "Brush coat" (not recurring)
print(f"Completed 'Brush coat' (non-recurring) -> new task created: {result is not None}")

# Daily recurring task — next occurrence auto-created for tomorrow
result = mochi_tasks.complete_task("m2")  # "Morning walk" (daily)
print(f"Completed 'Morning walk' (daily) -> new task: {result.name}, due {result.due_date}")

# Weekly recurring task — next occurrence auto-created for next week
result = whiskers_tasks.complete_task("w2")  # "Administer flea meds" (weekly)
print(f"Completed 'Administer flea meds' (weekly) -> new task: {result.name}, due {result.due_date}")

# Show updated task lists
print(f"\nMochi's tasks after completing 2 ({len(mochi_tasks.tasks)} total):")
for t in mochi_tasks.tasks:
    status = "done" if t.completed else f"pending, due {t.due_date}" if t.due_date else "pending"
    print(f"  {t.task_id}: {t.name} [{status}]")

print(f"\nWhiskers' tasks after completing 1 ({len(whiskers_tasks.tasks)} total):")
for t in whiskers_tasks.tasks:
    status = "done" if t.completed else f"pending, due {t.due_date}" if t.due_date else "pending"
    print(f"  {t.task_id}: {t.name} [{status}]")
print()

# --- Filtering demo ---
print("=" * 50)
print("FILTER: All pending (incomplete) tasks across both pets")
for pet_name, task in filter_tasks([mochi_tasks, whiskers_tasks], completed=False):
    print(f"  [{pet_name}] {task.name} ({task.priority} priority)")

print()
print("FILTER: Only Whiskers' tasks")
for pet_name, task in filter_tasks([mochi_tasks, whiskers_tasks], pet_name="Whiskers"):
    status = "done" if task.completed else "pending"
    print(f"  [{pet_name}] {task.name} -- {status}")

print()
print("FILTER: Completed tasks across all pets")
for pet_name, task in filter_tasks([mochi_tasks, whiskers_tasks], completed=True):
    print(f"  [{pet_name}] {task.name} (completed)")
