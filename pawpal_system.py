"""
pawpal_system.py
Logic layer for PawPal+ — all backend classes live here.
"""

from dataclasses import dataclass, field
from datetime import date, time, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Dataclasses — pure data objects
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    age: int
    notes: str = ""

    def get_summary(self) -> str:
        """Return a human-readable description of the pet."""
        summary = f"{self.name} is a {self.age}-year-old {self.species}"
        if self.notes:
            summary += f" -- {self.notes}"
        return summary


@dataclass
class Task:
    task_id: str
    name: str
    category: str          # walk | feeding | medication | grooming | enrichment | other
    duration_minutes: int
    priority: str          # high | medium | low
    is_recurring: bool = False
    recurrence: str = ""       # "daily" | "weekly" | ""
    due_date: Optional[date] = None
    preferred_time: str = ""   # morning | afternoon | evening
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done for today."""
        self.completed = True

    def reset_for_new_day(self) -> None:
        """Reset completed status for a fresh day."""
        self.completed = False

    def to_dict(self) -> dict:
        """Serialize task to a dictionary."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "category": self.category,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "is_recurring": self.is_recurring,
            "recurrence": self.recurrence,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "preferred_time": self.preferred_time,
            "completed": self.completed,
        }


# ---------------------------------------------------------------------------
# Regular classes — stateful objects with behaviour
# ---------------------------------------------------------------------------

class Owner:
    """Represents a pet owner with daily time constraints."""

    def __init__(
        self,
        name: str,
        available_minutes_per_day: int,
        preferred_start_time: time,
        preferred_end_time: time,
    ):
        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self.preferred_start_time = preferred_start_time
        self.preferred_end_time = preferred_end_time

    def update_availability(self, minutes: int) -> None:
        """Update how many minutes the owner has available today."""
        self.available_minutes_per_day = minutes

    def get_schedule_window(self) -> tuple[time, time]:
        """Return the (start, end) time window as a tuple."""
        return (self.preferred_start_time, self.preferred_end_time)


class TaskList:
    """Manages a collection of tasks associated with a single pet."""

    def __init__(self, pet: Pet):
        self.pet = pet
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a new task to the list."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task by its ID."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def edit_task(self, task_id: str, **kwargs) -> None:
        """Update one or more attributes of a task by its ID."""
        for task in self.tasks:
            if task.task_id == task_id:
                for key, value in kwargs.items():
                    setattr(task, key, value)
                return

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task complete. If it recurs, automatically create the next occurrence.

        Returns the newly created Task if one was generated, or None otherwise.
        """
        for task in self.tasks:
            if task.task_id == task_id:
                task.mark_complete()

                if task.is_recurring and task.recurrence in ("daily", "weekly"):
                    base_date = task.due_date if task.due_date else date.today()
                    if task.recurrence == "daily":
                        next_date = base_date + timedelta(days=1)
                    else:  # weekly
                        next_date = base_date + timedelta(weeks=1)

                    next_task = Task(
                        task_id=f"{task.task_id}_next",
                        name=task.name,
                        category=task.category,
                        duration_minutes=task.duration_minutes,
                        priority=task.priority,
                        is_recurring=task.is_recurring,
                        recurrence=task.recurrence,
                        due_date=next_date,
                        preferred_time=task.preferred_time,
                    )
                    self.tasks.append(next_task)
                    return next_task
                return None
        return None

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks that have not been completed."""
        return [t for t in self.tasks if not t.completed]

    def get_tasks_by_priority(self) -> list[Task]:
        """Return all tasks sorted by priority (high → medium → low)."""
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(self.tasks, key=lambda t: priority_order.get(t.priority, 3))


class DailyPlan:
    """Holds the scheduled and skipped tasks for a single day."""

    def __init__(self, plan_date: date):
        self.date = plan_date
        self.scheduled_tasks: list[tuple[Task, time]] = []  # (task, start_time)
        self.skipped_tasks: list[tuple[Task, str]] = []     # (task, reason)
        self.total_duration_minutes: int = 0

    def display(self) -> str:
        """Format the plan as a human-readable string for the UI."""
        lines = [f"Daily Plan for {self.date.strftime('%A, %B %d, %Y')}"]
        lines.append(f"Total scheduled time: {self.total_duration_minutes} minutes\n")

        if self.scheduled_tasks:
            lines.append("Scheduled Tasks:")
            for task, start in self.scheduled_tasks:
                status = "[x]" if task.completed else "[ ]"
                lines.append(
                    f"  {status} {start.strftime('%I:%M %p')} -- {task.name} "
                    f"({task.duration_minutes} min, {task.priority} priority)"
                )
        else:
            lines.append("No tasks scheduled.")

        if self.skipped_tasks:
            lines.append("\nSkipped Tasks:")
            for task, reason in self.skipped_tasks:
                lines.append(f"  SKIP {task.name} -- {reason}")

        return "\n".join(lines)

    def get_skipped_summary(self) -> str:
        """Explain which tasks were skipped and why."""
        if not self.skipped_tasks:
            return "All tasks were scheduled successfully!"
        lines = []
        for task, reason in self.skipped_tasks:
            lines.append(f"- {task.name}: {reason}")
        return "\n".join(lines)


class Scheduler:
    """Builds a priority-based daily plan within the owner's time constraints."""

    def __init__(self, owner: Owner, task_list: TaskList):
        self.owner = owner
        self.task_list = task_list
        self.generated_plan: Optional[DailyPlan] = None

    def generate_plan(self) -> DailyPlan:
        """Build a DailyPlan by scheduling pending tasks in priority order within the owner's time window."""
        from datetime import timedelta

        plan = DailyPlan(plan_date=date.today())
        remaining_minutes = self.owner.available_minutes_per_day
        start_time, end_time = self.owner.get_schedule_window()
        current_time = start_time

        # Get pending tasks sorted by priority (high first)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        pending = [t for t in self.task_list.tasks if not t.completed]
        pending.sort(key=lambda t: priority_order.get(t.priority, 3))

        for task in pending:
            if self.can_fit_task(task, remaining_minutes):
                # Check the task wouldn't run past the end time
                task_end = (
                    timedelta(hours=current_time.hour, minutes=current_time.minute)
                    + timedelta(minutes=task.duration_minutes)
                )
                end_limit = timedelta(hours=end_time.hour, minutes=end_time.minute)

                if task_end <= end_limit:
                    plan.scheduled_tasks.append((task, current_time))
                    plan.total_duration_minutes += task.duration_minutes
                    remaining_minutes -= task.duration_minutes
                    # Advance current_time
                    new_minutes = current_time.minute + task.duration_minutes
                    new_hour = current_time.hour + new_minutes // 60
                    new_minutes = new_minutes % 60
                    current_time = time(hour=new_hour, minute=new_minutes)
                else:
                    plan.skipped_tasks.append(
                        (task, f"Would exceed schedule window (ends at {end_time.strftime('%I:%M %p')})")
                    )
            else:
                plan.skipped_tasks.append(
                    (task, f"Not enough time remaining ({remaining_minutes} min left, needs {task.duration_minutes} min)")
                )

        self.generated_plan = plan
        return plan

    def sort_by_time(self) -> list[tuple[Task, time]]:
        """Sort the generated plan's scheduled tasks by their start time (HH:MM).

        Algorithm:
            Uses Python's built-in sorted() with a lambda key that converts
            each task's start time to a "HH:MM" string. Because "HH:MM" is
            zero-padded, lexicographic order equals chronological order.

        Time complexity: O(n log n) where n is the number of scheduled tasks.

        Returns:
            The sorted list of (Task, time) tuples. Also mutates the plan
            in place. Returns an empty list if no plan has been generated.
        """
        if self.generated_plan is None:
            return []
        self.generated_plan.scheduled_tasks = sorted(
            self.generated_plan.scheduled_tasks,
            key=lambda pair: pair[1].strftime("%H:%M"),
        )
        return self.generated_plan.scheduled_tasks

    def detect_conflicts(self) -> list[str]:
        """Check the generated plan for time overlaps between same-pet tasks.

        Algorithm:
            Brute-force pairwise comparison of all scheduled (task, time)
            entries. For each pair, computes end times via _add_minutes()
            and applies the interval overlap test:
                overlap = (start_a < end_b) AND (start_b < end_a)

        Time complexity: O(n^2) where n is the number of scheduled tasks.
            Acceptable for daily pet schedules (typically < 15 tasks).

        Returns:
            A list of human-readable warning strings. An empty list means
            no conflicts were found. Never raises an exception.
        """
        warnings: list[str] = []
        if self.generated_plan is None:
            return warnings

        scheduled = self.generated_plan.scheduled_tasks
        for i in range(len(scheduled)):
            task_a, start_a = scheduled[i]
            end_a = _add_minutes(start_a, task_a.duration_minutes)
            for j in range(i + 1, len(scheduled)):
                task_b, start_b = scheduled[j]
                end_b = _add_minutes(start_b, task_b.duration_minutes)
                # Overlap: A starts before B ends AND B starts before A ends
                if start_a < end_b and start_b < end_a:
                    warnings.append(
                        f"WARNING: '{task_a.name}' ({start_a.strftime('%I:%M %p')}-"
                        f"{end_a.strftime('%I:%M %p')}) overlaps with "
                        f"'{task_b.name}' ({start_b.strftime('%I:%M %p')}-"
                        f"{end_b.strftime('%I:%M %p')})"
                    )
        return warnings

    def can_fit_task(self, task: Task, remaining_minutes: int) -> bool:
        """Return True if the task fits within the remaining time budget."""
        return task.duration_minutes <= remaining_minutes

    def explain_plan(self) -> str:
        """Return a plain-language summary of the scheduling decisions made."""
        if self.generated_plan is None:
            return "No plan has been generated yet. Call generate_plan() first."

        plan = self.generated_plan
        lines = [f"Plan for {self.task_list.pet.name} on {plan.date.strftime('%B %d, %Y')}:"]
        lines.append(
            f"{self.owner.name} has {self.owner.available_minutes_per_day} minutes available "
            f"between {self.owner.preferred_start_time.strftime('%I:%M %p')} and "
            f"{self.owner.preferred_end_time.strftime('%I:%M %p')}.\n"
        )

        if plan.scheduled_tasks:
            lines.append(f"{len(plan.scheduled_tasks)} task(s) scheduled ({plan.total_duration_minutes} min total):")
            for task, start in plan.scheduled_tasks:
                lines.append(f"  - {task.name} at {start.strftime('%I:%M %p')} ({task.priority} priority, {task.duration_minutes} min)")

        if plan.skipped_tasks:
            lines.append(f"\n{len(plan.skipped_tasks)} task(s) could not be scheduled:")
            for task, reason in plan.skipped_tasks:
                lines.append(f"  - {task.name}: {reason}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _add_minutes(t: time, minutes: int) -> time:
    """Return a new time that is *minutes* after *t*.

    Algorithm:
        Converts the time to a timedelta for safe arithmetic (avoiding
        manual hour/minute overflow), then extracts hours and minutes
        back into a time object via divmod on total_seconds.

    Returns:
        A new datetime.time offset forward by the given minutes.
    """
    total = timedelta(hours=t.hour, minutes=t.minute) + timedelta(minutes=minutes)
    hours, remainder = divmod(int(total.total_seconds()), 3600)
    mins = remainder // 60
    return time(hour=hours, minute=mins)


def detect_cross_pet_conflicts(schedulers: list["Scheduler"]) -> list[str]:
    """Detect time overlaps across different pets' schedules.

    Since one owner handles all pets, a task for Mochi at 07:00 and a task
    for Whiskers at 07:00 is a real conflict the owner cannot fulfill.

    Algorithm:
        1. Flattens all scheduled (pet, task, start, end) slots from every
           Scheduler into a single list.
        2. Performs pairwise comparison, skipping pairs that belong to the
           same pet (those are handled by Scheduler.detect_conflicts()).
        3. Applies the standard interval overlap test on each cross-pet pair.

    Time complexity: O(n^2) where n is the total number of scheduled tasks
        across all pets. Same-pet pairs are skipped but still iterated over.

    Returns:
        A list of human-readable warning strings. An empty list means
        no cross-pet conflicts were found. Never raises an exception.
    """
    warnings: list[str] = []
    # Collect all (pet_name, task, start, end) from every scheduler
    all_slots: list[tuple[str, Task, time, time]] = []
    for sched in schedulers:
        if sched.generated_plan is None:
            continue
        pet = sched.task_list.pet.name
        for task, start in sched.generated_plan.scheduled_tasks:
            end = _add_minutes(start, task.duration_minutes)
            all_slots.append((pet, task, start, end))

    for i in range(len(all_slots)):
        pet_a, task_a, start_a, end_a = all_slots[i]
        for j in range(i + 1, len(all_slots)):
            pet_b, task_b, start_b, end_b = all_slots[j]
            if pet_a == pet_b:
                continue  # same-pet conflicts handled by detect_conflicts
            if start_a < end_b and start_b < end_a:
                warnings.append(
                    f"WARNING: [{pet_a}] '{task_a.name}' ({start_a.strftime('%I:%M %p')}-"
                    f"{end_a.strftime('%I:%M %p')}) overlaps with "
                    f"[{pet_b}] '{task_b.name}' ({start_b.strftime('%I:%M %p')}-"
                    f"{end_b.strftime('%I:%M %p')})"
                )
    return warnings

def filter_tasks(
    task_lists: list[TaskList],
    completed: Optional[bool] = None,
    pet_name: Optional[str] = None,
) -> list[tuple[str, Task]]:
    """Filter tasks across one or more TaskLists by completion status and/or pet name.

    Algorithm:
        Linear scan over every task in every TaskList. Each filter
        (completed, pet_name) is applied as an early-skip guard:
        if the value doesn't match, the task is excluded. When both
        filters are provided, both must match (AND logic). Pet name
        comparison is case-insensitive.

    Time complexity: O(L * T) where L is the number of TaskLists and
        T is the average number of tasks per list.

    Returns:
        A list of (pet_name, Task) tuples that match the criteria.
    """
    results: list[tuple[str, Task]] = []
    for tl in task_lists:
        if pet_name is not None and tl.pet.name.lower() != pet_name.lower():
            continue
        for task in tl.tasks:
            if completed is not None and task.completed != completed:
                continue
            results.append((tl.pet.name, task))
    return results
