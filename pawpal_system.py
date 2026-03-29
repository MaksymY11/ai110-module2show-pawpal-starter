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
        pass


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
        pass

    def reset_for_new_day(self) -> None:
        """Reset completed status for a fresh day."""
        pass

    def to_dict(self) -> dict:
        """Serialize task to a dictionary."""
        pass


# ---------------------------------------------------------------------------
# Regular classes — stateful objects with behaviour
# ---------------------------------------------------------------------------

class Owner:
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
        pass

    def get_schedule_window(self) -> tuple[time, time]:
        """Return the (start, end) time window as a tuple."""
        pass


class TaskList:
    def __init__(self, pet: Pet):
        self.pet = pet
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a new task to the list."""
        pass

    def remove_task(self, task_id: str) -> None:
        """Remove a task by its ID."""
        pass

    def edit_task(self, task_id: str, **kwargs) -> None:
        """Update one or more attributes of a task by its ID."""
        pass

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks that have not been completed."""
        pass

    def get_tasks_by_priority(self) -> list[Task]:
        """Return all tasks sorted by priority (high → medium → low)."""
        pass


class DailyPlan:
    def __init__(self, plan_date: date):
        self.date = plan_date
        self.scheduled_tasks: list[tuple[Task, time]] = []  # (task, start_time)
        self.skipped_tasks: list[tuple[Task, str]] = []     # (task, reason)
        self.total_duration_minutes: int = 0

    def display(self) -> str:
        """Format the plan as a human-readable string for the UI."""
        pass

    def get_skipped_summary(self) -> str:
        """Explain which tasks were skipped and why."""
        pass


class Scheduler:
    def __init__(self, owner: Owner, task_list: TaskList):
        self.owner = owner
        self.task_list = task_list
        self.generated_plan: Optional[DailyPlan] = None

    def generate_plan(self) -> DailyPlan:
        """
        Build a DailyPlan by scheduling tasks within the owner's
        available time window, ordered by priority.
        """
        pass

    def can_fit_task(self, task: Task, remaining_minutes: int) -> bool:
        """Return True if the task fits within the remaining time budget."""
        pass

    def explain_plan(self) -> str:
        """Return a plain-language summary of the scheduling decisions made."""
        pass
