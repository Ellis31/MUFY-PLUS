import streamlit as st
import calendar
from datetime import datetime, date
import json
import os

# =========================================================
# CONFIG
# =========================================================
TASK_FILE = "tasks.json"

PRIORITY_ICON = {
    "High": "🔴 High",
    "Medium": "🟡 Medium",
    "Low": "🟢 Low"
}

PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

# =========================================================
# DATA HANDLING
# =========================================================
def load_tasks():
    """Load tasks safely and fix missing fields automatically"""
    if not os.path.exists(TASK_FILE):
        return {}

    with open(TASK_FILE, "r") as f:
        tasks = json.load(f)

    # Auto-fix old tasks (important for avoiding KeyError)
    for d in tasks:
        for t in tasks[d]:
            if "priority" not in t:
                t["priority"] = "Low"
            if "time" not in t:
                t["time"] = "00:00"

    return tasks


def save_tasks(tasks):
    """Save tasks to JSON file"""
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=4)


# =========================================================
# TASK FUNCTIONS
# =========================================================
def add_task(tasks, task_date, task_text, priority, task_time):
    d = str(task_date)

    if d not in tasks:
        tasks[d] = []

    tasks[d].append({
        "task": task_text,
        "completed": False,
        "priority": priority,
        "time": task_time.strftime("%H:%M")
    })

    save_tasks(tasks)


def complete_task(tasks, task_date, index):
    tasks[task_date][index]["completed"] = True
    save_tasks(tasks)


def delete_task(tasks, task_date, task_text, task_time):
    """Safe delete (works even after sorting/filtering)"""
    if task_date not in tasks:
        return

    tasks[task_date] = [
        t for t in tasks[task_date]
        if not (t["task"] == task_text and t.get("time") == task_time)
    ]

    if len(tasks[task_date]) == 0:
        del tasks[task_date]

    save_tasks(tasks)


# =========================================================
# LOGIC HELPERS
# =========================================================
def sort_tasks(task_list):
    return sorted(task_list, key=lambda x: PRIORITY_ORDER.get(x["priority"], 2))


def is_overdue(task_date_str, task):
    task_date = datetime.strptime(task_date_str, "%Y-%m-%d").date()
    return task_date < date.today() and not task["completed"]


def check_reminders(tasks, selected_date):
    """Popup reminder when task time matches current time"""
    now = datetime.now().strftime("%H:%M")
    key = str(selected_date)

    if key not in tasks:
        return

    for task in tasks[key]:
        if not task["completed"] and task.get("time") == now:
            st.warning(f"🔔 Reminder: {task['task']} ({task['time']})")


# =========================================================
# CALENDAR VIEW
# =========================================================
def render_calendar(year, month, tasks):
    st.subheader(f"📅 {calendar.month_name[month]} {year}")

    cal = calendar.monthcalendar(year, month)

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)

    for i, d in enumerate(days):
        cols[i].markdown(f"**{d}**")

    for week in cal:
        cols = st.columns(7)

        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                d = date(year, month, day)
                key = str(d)

                task_list = tasks.get(key, [])

                display = f"### {day}\n"

                for t in task_list:
                    icon = PRIORITY_ICON.get(t["priority"], "🟢 Low")
                    time = t.get("time", "00:00")
                    status = "✔️" if t["completed"] else ""

                    display += f"{icon} [{time}] {t['task']} {status}\n"

                cols[i].markdown(display)


# =========================================================
# MAIN APP
# =========================================================
def main():
    st.set_page_config(page_title="To-Do Calendar", layout="wide")

    st.title("📅 Smart To-Do Calendar App")

    tasks = load_tasks()

    # ---------------- SIDEBAR ----------------
    st.sidebar.header("Controls")

    year = st.sidebar.number_input("Year", 2020, 2100, datetime.now().year)

    month = st.sidebar.selectbox(
        "Month",
        range(1, 13),
        format_func=lambda x: calendar.month_name[x]
    )

    selected_date = st.sidebar.date_input("Select Date")

    st.sidebar.divider()

    # ---------------- ADD TASK ----------------
    st.sidebar.subheader("➕ Add Task")

    task_date = st.sidebar.date_input("Task Date")
    task_text = st.sidebar.text_input("Task")

    priority = st.sidebar.selectbox("Priority", ["High", "Medium", "Low"])

    task_time = st.sidebar.time_input("Task Time")

    if st.sidebar.button("Add Task"):
        if task_text.strip():
            add_task(tasks, task_date, task_text, priority, task_time)
            st.sidebar.success("Task added!")
            st.rerun()
        else:
            st.sidebar.warning("Please enter a task")

    st.divider()

    # ---------------- REMINDERS ----------------
    check_reminders(tasks, selected_date)

    # ---------------- CALENDAR ----------------
    render_calendar(year, month, tasks)

    st.divider()

    # ---------------- DAILY VIEW ----------------
    st.subheader("📋 Tasks for Selected Date")

    key = str(selected_date)

    if key not in tasks:
        st.info("No tasks for this date.")
    else:
        tasks[key] = sort_tasks(tasks[key])

        for i, task in enumerate(tasks[key]):

            icon = PRIORITY_ICON.get(task["priority"], "🟢 Low")
            time = task.get("time", "00:00")

            col1, col2, col3 = st.columns([5, 1, 1])

            label = f"{icon} [{time}] {task['task']}"

            if is_overdue(key, task):
                label += " ⚠️ OVERDUE"

            if task["completed"]:
                col1.markdown(f"~~{label}~~ ✔️")
            else:
                col1.write(label)

            if not task["completed"]:
                if col2.button("✔️", key=f"c_{key}_{i}"):
                    complete_task(tasks, key, i)
                    st.rerun()

            if col3.button("🗑", key=f"d_{key}_{i}"):
                delete_task(tasks, key, task["task"], time)
                st.rerun()


if __name__ == "__main__":
    main()