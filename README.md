# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

Beyond basic priority-based plan generation, PawPal+ includes three additional scheduling features:

- **Sorting and filtering** — `Scheduler.sort_by_time()` reorders scheduled tasks chronologically using a lambda key on "HH:MM" format. `filter_tasks()` lets you search across multiple pets by completion status, pet name, or both (AND logic).
- **Recurring task automation** — Tasks marked as `"daily"` or `"weekly"` automatically spawn a new instance when completed. `TaskList.complete_task()` uses `timedelta` to calculate the next due date (today + 1 day for daily, today + 7 days for weekly) and appends it to the task list.
- **Conflict detection** — `Scheduler.detect_conflicts()` checks for time overlaps within a single pet's schedule using the interval overlap test (`start_a < end_b AND start_b < end_a`). `detect_cross_pet_conflicts()` extends this across multiple pets, since one owner cannot care for two pets simultaneously.
