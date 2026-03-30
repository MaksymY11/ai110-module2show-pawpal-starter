"""Tests for PawPal+ core logic."""

import pytest
from pawpal_system import Pet, Task, TaskList


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
