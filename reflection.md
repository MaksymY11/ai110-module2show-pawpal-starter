# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
  - User should be able to add their and their pet's info.
  - User should be able to add and edit tasks, select tasks priority and duration.
  - The app should generate daily schedule for user based on the information above.
- What classes did you include, and what responsibilities did you assign to each?
  - class Owner:
    - name
    - free_time (in minutes, total time they have for pet per day)
    - start_time (when owner wants to start tasks)
    - end_time (when owner wants to end tasks)
    - update_freetime() (adjust time constraints per day)
    - get_schedule_window() (returns time window as a tuple)
  - class Pet:
    - name
    - breed
    - age
    - notes (on medication, anxious around strangers, ...)
    - get_summary() (returns human-readable description of pet)
  - class Task:
    - task_id
    - name
    - category
    - duration_min
    - priority
    - is_recurring
    - preferred_time (optional preference like morning, afternoo, evening)
    - completed
    - mark_complete()
    - reset() (ran if task is recurring -> resets completed to False for next day)
    - to_dict() (serialize for storage or display)
  - class TaskList
    - tasks (list of Task obj)
    - pet (reference to associated Pet obj)
    - add_task(task)
    - remove_task(task_id)
    - edit_task(task_id, \*\*kwargs)
    - get_pending_tasks()
    - get_tasks_by_priority()
  - class DailyPlan
    - date
    - scheduled_tasks (ordered list of Task, start_time tuples)
    - skipped_tasks
    - total_duration_min
    - display()
    - get_skipped_summary() (explain what was left out and why)
  - class Scheduler
    - owner (ref to Owner obj)
    - task_list (ref to TaskList obj)
    - generated_plan (most recently generated DailyPlan)
    - generate_plan() (return a DailyPlan)
    - can_fit_task(task, remaining_min)
    - explain_plan() (plain language summary of scheduling decisions)

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
  - My scheduler uses a greedy priority-first strategy. It will always schedule the highest-priority task without considering what comes after. For example, If Jordan has 35 min left, and one task is high priority and needs 30 min, and there are tow medium priority tasks that take 15 minutes each, my scheduler would pick 30 min task, skipping two 15 minute ones.
- Why is that tradeoff reasonable for this scenario?
  - In pet care, not all tasks are equal. Missing a medication dose or skipping breakfast has real health consequences, while pushing a grooming session to tomorrow doesn't. A greedy priority-first approach is reasonable here because the cost of skipping a high-priority task is far greater than the cost of skipping multiple low-priority ones.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
