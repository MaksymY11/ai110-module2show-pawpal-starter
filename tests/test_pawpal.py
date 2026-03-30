"""Tests for PawPal+ core logic."""

import pytest
from datetime import date, time, timedelta
from pawpal_system import Pet, Task, TaskList, Owner, Scheduler, detect_cross_pet_conflicts


class TestTaskCompletion:
    def test_mark_complete_changes_status(self):
        task = Task("t1", "Morning walk", "walk", 30, "high")
        assert task.completed is False
        task.mark_complete()
        assert task.completed is True


class TestTaskAddition:
    def test_add_task_increases_count(self):
        pet = Pet("Mochi", "dog", 3)
        task_list = TaskList(pet)
        assert len(task_list.tasks) == 0
        task_list.add_task(Task("t1", "Breakfast", "feeding", 10, "high"))
        assert len(task_list.tasks) == 1
        task_list.add_task(Task("t2", "Walk", "walk", 30, "medium"))
        assert len(task_list.tasks) == 2


# ---- Helpers to reduce boilerplate ----------------------------------------

def _make_owner(minutes=120, start=time(7, 0), end=time(12, 0)):
    return Owner("Alice", minutes, start, end)


def _make_task(tid, name, duration, priority="medium", category="walk",
               recurring=False, recurrence="", due=None, pref_time="morning"):
    return Task(tid, name, category, duration, priority,
                is_recurring=recurring, recurrence=recurrence,
                due_date=due, preferred_time=pref_time)


# ---- Sorting Correctness --------------------------------------------------

class TestSortingCorrectness:
    """Verify Scheduler.sort_by_time returns tasks in chronological order."""

    def test_tasks_sorted_chronologically(self):
        """Three tasks added out of order should be returned earliest-first."""
        owner = _make_owner(minutes=180)
        pet = Pet("Mochi", "dog", 3)
        tl = TaskList(pet)
        tl.add_task(_make_task("t1", "Lunch walk", 30, "low"))
        tl.add_task(_make_task("t2", "Breakfast", 10, "high"))
        tl.add_task(_make_task("t3", "Grooming", 20, "medium"))

        sched = Scheduler(owner, tl)
        sched.generate_plan()
        sorted_tasks = sched.sort_by_time()

        start_times = [s.strftime("%H:%M") for _, s in sorted_tasks]
        assert start_times == sorted(start_times), (
            f"Tasks not in chronological order: {start_times}"
        )

    def test_sort_with_no_plan_returns_empty(self):
        """Sorting before generating a plan should return an empty list."""
        owner = _make_owner()
        tl = TaskList(Pet("Mochi", "dog", 3))
        sched = Scheduler(owner, tl)
        assert sched.sort_by_time() == []

    def test_sort_single_task(self):
        """A single scheduled task is trivially sorted."""
        owner = _make_owner(minutes=60)
        tl = TaskList(Pet("Mochi", "dog", 3))
        tl.add_task(_make_task("t1", "Walk", 30, "high"))

        sched = Scheduler(owner, tl)
        sched.generate_plan()
        sorted_tasks = sched.sort_by_time()

        assert len(sorted_tasks) == 1
        assert sorted_tasks[0][0].name == "Walk"


# ---- Recurrence Logic ------------------------------------------------------

class TestRecurrenceLogic:
    """Confirm recurring-task completion creates the correct next occurrence."""

    def test_daily_recurrence_creates_next_day_task(self):
        """Completing a daily task should produce a new task due tomorrow."""
        pet = Pet("Mochi", "dog", 3)
        tl = TaskList(pet)
        today = date.today()
        tl.add_task(_make_task("t1", "Morning walk", 30, "high",
                               recurring=True, recurrence="daily", due=today))

        next_task = tl.complete_task("t1")

        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)
        assert next_task.completed is False
        assert next_task.is_recurring is True

    def test_weekly_recurrence_creates_next_week_task(self):
        """Completing a weekly task should produce a new task due in 7 days."""
        pet = Pet("Whiskers", "cat", 5)
        tl = TaskList(pet)
        today = date.today()
        tl.add_task(_make_task("t1", "Grooming", 45, "medium",
                               recurring=True, recurrence="weekly", due=today))

        next_task = tl.complete_task("t1")

        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)

    def test_non_recurring_task_returns_none(self):
        """Completing a one-off task should NOT create a next occurrence."""
        pet = Pet("Mochi", "dog", 3)
        tl = TaskList(pet)
        tl.add_task(_make_task("t1", "Vet visit", 60, "high"))

        result = tl.complete_task("t1")

        assert result is None
        assert len(tl.tasks) == 1  # no new task appended

    def test_complete_nonexistent_task_returns_none(self):
        """Completing a task ID that doesn't exist should return None safely."""
        tl = TaskList(Pet("Mochi", "dog", 3))
        assert tl.complete_task("bogus_id") is None


# ---- Conflict Detection ----------------------------------------------------

class TestConflictDetection:
    """Verify that overlapping time slots are flagged as conflicts."""

    def test_identical_start_times_flagged(self):
        """Two tasks starting at the exact same time must produce a warning."""
        owner = _make_owner(minutes=120)
        pet = Pet("Mochi", "dog", 3)
        tl = TaskList(pet)
        tl.add_task(_make_task("t1", "Walk", 30, "high"))
        tl.add_task(_make_task("t2", "Feed", 15, "high"))

        sched = Scheduler(owner, tl)
        plan = sched.generate_plan()

        # Force both tasks to the same start time to simulate a conflict
        plan.scheduled_tasks = [
            (tl.tasks[0], time(8, 0)),
            (tl.tasks[1], time(8, 0)),
        ]

        warnings = sched.detect_conflicts()
        assert len(warnings) == 1
        assert "Walk" in warnings[0]
        assert "Feed" in warnings[0]

    def test_no_conflict_when_tasks_are_sequential(self):
        """Back-to-back tasks with no overlap should produce zero warnings."""
        owner = _make_owner(minutes=120)
        pet = Pet("Mochi", "dog", 3)
        tl = TaskList(pet)
        tl.add_task(_make_task("t1", "Walk", 30, "high"))
        tl.add_task(_make_task("t2", "Feed", 15, "medium"))

        sched = Scheduler(owner, tl)
        sched.generate_plan()

        warnings = sched.detect_conflicts()
        assert warnings == []

    def test_cross_pet_conflict_detected(self):
        """Overlapping tasks for different pets should be flagged."""
        owner = _make_owner(minutes=120)

        tl1 = TaskList(Pet("Mochi", "dog", 3))
        tl1.add_task(_make_task("t1", "Dog walk", 30, "high"))
        sched1 = Scheduler(owner, tl1)
        sched1.generate_plan()

        tl2 = TaskList(Pet("Whiskers", "cat", 5))
        tl2.add_task(_make_task("t2", "Cat groom", 20, "high"))
        sched2 = Scheduler(owner, tl2)
        sched2.generate_plan()

        # Both plans start at 07:00 by default — guaranteed overlap
        warnings = detect_cross_pet_conflicts([sched1, sched2])
        assert len(warnings) == 1
        assert "Mochi" in warnings[0]
        assert "Whiskers" in warnings[0]

    def test_no_cross_pet_conflict_when_staggered(self):
        """Non-overlapping tasks across pets should produce zero warnings."""
        owner = _make_owner(minutes=120)

        tl1 = TaskList(Pet("Mochi", "dog", 3))
        tl1.add_task(_make_task("t1", "Dog walk", 30, "high"))
        sched1 = Scheduler(owner, tl1)
        sched1.generate_plan()

        tl2 = TaskList(Pet("Whiskers", "cat", 5))
        tl2.add_task(_make_task("t2", "Cat groom", 20, "high"))
        sched2 = Scheduler(owner, tl2)
        plan2 = sched2.generate_plan()
        # Move cat task after dog walk ends (07:30)
        plan2.scheduled_tasks = [(tl2.tasks[0], time(7, 30))]

        warnings = detect_cross_pet_conflicts([sched1, sched2])
        assert warnings == []
