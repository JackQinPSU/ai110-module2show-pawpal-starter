"""
PawPal+ Streamlit UI.

Connects to pawpal_system.py for all scheduling logic.
Run with:  streamlit run app.py
"""

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling for busy owners.")

# ---------------------------------------------------------------------------
# Session state — persist Owner across Streamlit reruns
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None   # created when owner name is submitted

# ---------------------------------------------------------------------------
# Sidebar — owner + pet setup
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Owner Setup")
    with st.form("owner_form"):
        owner_name = st.text_input("Your name", value="Jordan")
        submitted = st.form_submit_button("Set owner")
        if submitted and owner_name.strip():
            if st.session_state.owner is None or st.session_state.owner.name != owner_name.strip():
                st.session_state.owner = Owner(owner_name.strip())
            st.success(f"Owner set to {st.session_state.owner.name}")

    if st.session_state.owner:
        st.divider()
        st.header("Add a Pet")
        with st.form("pet_form"):
            pet_name    = st.text_input("Pet name",  value="Mochi")
            pet_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
            pet_age     = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
            add_pet_btn = st.form_submit_button("Add pet")
            if add_pet_btn and pet_name.strip():
                existing = [p.name.lower() for p in st.session_state.owner.get_pets()]
                if pet_name.strip().lower() in existing:
                    st.warning(f"{pet_name} is already in your roster.")
                else:
                    st.session_state.owner.add_pet(Pet(pet_name.strip(), pet_species, int(pet_age)))
                    st.success(f"Added {pet_name}!")

        # List current pets
        pets = st.session_state.owner.get_pets()
        if pets:
            st.divider()
            st.subheader("Your Pets")
            for p in pets:
                st.write(f"**{p.name}** — {p.species}, age {p.age} ({len(p.get_tasks())} tasks)")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

if st.session_state.owner is None:
    st.info("Enter your name in the sidebar to get started.")
    st.stop()

owner    = st.session_state.owner
pets     = owner.get_pets()
scheduler = Scheduler(owner)

if not pets:
    st.info("Add at least one pet in the sidebar to begin scheduling.")
    st.stop()

# ---------------------------------------------------------------------------
# Add Task
# ---------------------------------------------------------------------------

st.header("Add a Task")

with st.form("task_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        task_pet   = st.selectbox("Pet", [p.name for p in pets])
        task_desc  = st.text_input("Description", value="Morning walk")
    with col2:
        task_time  = st.text_input("Time (HH:MM)", value="07:30")
        task_dur   = st.number_input("Duration (min)", min_value=1, max_value=480, value=20)
    with col3:
        task_pri   = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        task_freq  = st.selectbox("Frequency", ["once", "daily", "weekly"])

    add_task_btn = st.form_submit_button("Add task")
    if add_task_btn:
        # Basic time validation
        parts = task_time.strip().split(":")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            st.error("Time must be in HH:MM format (e.g. 09:00).")
        else:
            target_pet = next(p for p in pets if p.name == task_pet)
            target_pet.add_task(Task(
                description=task_desc.strip(),
                time=task_time.strip(),
                duration_minutes=int(task_dur),
                priority=task_pri,
                frequency=task_freq,
            ))
            st.success(f"Added '{task_desc}' to {task_pet}'s schedule.")

st.divider()

# ---------------------------------------------------------------------------
# Conflict warnings
# ---------------------------------------------------------------------------

conflicts = scheduler.detect_conflicts()
if conflicts:
    for (p_a, t_a), (p_b, t_b) in conflicts:
        st.warning(
            f"**Time conflict at {t_a.time}:** "
            f"{p_a}'s '{t_a.description}' overlaps with {p_b}'s '{t_b.description}'"
        )

# ---------------------------------------------------------------------------
# Today's Schedule
# ---------------------------------------------------------------------------

st.header("Today's Schedule")

# Filter controls
col_f1, col_f2 = st.columns(2)
with col_f1:
    pet_filter = st.selectbox("Filter by pet", ["All"] + [p.name for p in pets])
with col_f2:
    status_filter = st.selectbox("Filter by status", ["All", "Pending", "Completed"])

# Build the filtered schedule
schedule = scheduler.get_daily_schedule()

if pet_filter != "All":
    schedule = [(p, t) for p, t in schedule if p == pet_filter]

if status_filter == "Pending":
    schedule = [(p, t) for p, t in schedule if not t.completed]
elif status_filter == "Completed":
    schedule = [(p, t) for p, t in schedule if t.completed]

if not schedule:
    st.info("No tasks match your filters.")
else:
    # Render each task as a card row
    header_cols = st.columns([1, 2, 3, 1, 1, 1, 1])
    for col, label in zip(header_cols, ["Time", "Pet", "Task", "Duration", "Priority", "Frequency", "Done?"]):
        col.markdown(f"**{label}**")

    st.divider()

    for pet_name, task in schedule:
        cols = st.columns([1, 2, 3, 1, 1, 1, 1])
        cols[0].write(task.time)
        cols[1].write(pet_name)
        cols[2].write(task.description)
        cols[3].write(f"{task.duration_minutes}m")

        # Priority badge colour
        pri_colours = {"high": "red", "medium": "orange", "low": "green"}
        cols[4].markdown(f":{pri_colours.get(task.priority, 'gray')}[{task.priority}]")

        cols[5].write(task.frequency)

        if task.completed:
            cols[6].success("Done")
        else:
            if cols[6].button("Mark done", key=f"done_{task.id}"):
                scheduler.mark_task_complete(task.id)
                st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------

all_tasks = owner.get_all_tasks()
total     = len(all_tasks)
done      = sum(1 for _, t in all_tasks if t.completed)
pending   = total - done

m1, m2, m3 = st.columns(3)
m1.metric("Total tasks", total)
m2.metric("Completed", done)
m3.metric("Pending", pending)
