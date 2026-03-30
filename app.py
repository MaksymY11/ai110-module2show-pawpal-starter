import streamlit as st
from datetime import time
from pawpal_system import Pet, Task, TaskList, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state — persist objects across reruns
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pet" not in st.session_state:
    st.session_state.pet = None
if "task_list" not in st.session_state:
    st.session_state.task_list = None
if "task_counter" not in st.session_state:
    st.session_state.task_counter = 0

# ---------------------------------------------------------------------------
# Owner & Pet setup
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet Profile")

owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available minutes per day", min_value=10, max_value=480, value=90)
col_start, col_end = st.columns(2)
with col_start:
    start_time = st.time_input("Preferred start time", value=time(7, 0))
with col_end:
    end_time = st.time_input("Preferred end time", value=time(12, 0))

pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
pet_age = st.number_input("Pet age", min_value=0, max_value=30, value=3)
pet_notes = st.text_input("Notes about your pet", value="")

if st.button("Save Profile"):
    st.session_state.owner = Owner(owner_name, available_minutes, start_time, end_time)
    st.session_state.pet = Pet(pet_name, species, pet_age, pet_notes)
    st.session_state.task_list = TaskList(st.session_state.pet)
    st.session_state.task_counter = 0
    st.success(f"Profile saved! {st.session_state.pet.get_summary()}")

st.divider()

# ---------------------------------------------------------------------------
# Add tasks
# ---------------------------------------------------------------------------
st.subheader("Tasks")

if st.session_state.task_list is None:
    st.info("Save an owner & pet profile above before adding tasks.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["high", "medium", "low"], index=0)

    category = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment", "other"])

    if st.button("Add task"):
        st.session_state.task_counter += 1
        task = Task(
            task_id=f"t{st.session_state.task_counter}",
            name=task_title,
            category=category,
            duration_minutes=int(duration),
            priority=priority,
        )
        st.session_state.task_list.add_task(task)
        st.success(f"Added: {task.name} ({task.duration_minutes} min, {task.priority})")

    if st.session_state.task_list.tasks:
        st.write("Current tasks:")
        st.table([t.to_dict() for t in st.session_state.task_list.tasks])
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Generate schedule
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None or st.session_state.task_list is None:
        st.warning("Please save a profile and add tasks first.")
    elif not st.session_state.task_list.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(st.session_state.owner, st.session_state.task_list)
        plan = scheduler.generate_plan()
        st.text(plan.display())
        st.divider()
        st.markdown("**Scheduler Explanation**")
        st.text(scheduler.explain_plan())
