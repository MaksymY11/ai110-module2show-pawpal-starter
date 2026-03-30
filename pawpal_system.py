"""
pawpal_system.py
Logic layer for PawPal+ — all backend classes live here.
"""

from dataclasses import dataclass, field
from datetime import date, time
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
