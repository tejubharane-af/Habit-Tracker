import streamlit as st
import sqlite3
from datetime import date, timedelta

# --- 1. Page Configuration ---
st.set_page_config(page_title="Habit Tracker", page_icon="🔥", layout="centered")

# --- 2. Custom CSS for a Modern Web App Look ---
st.markdown("""
    <style>
    /* Background and main container */
    .stApp {
        background-color: #f4f7f6;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Hide default Streamlit header and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main card container */
    .block-container {
        max-width: 480px !important;
        background-color: #ffffff;
        padding: 2rem 2rem 2.5rem 2rem !important;
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 1px solid #eaeaea;
    }

    /* Header title and subtitle */
    .app-header {
        font-size: 28px;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 5px;
    }
    .app-sub {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 20px;
    }

    /* Habit card styling */
    .habit-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 12px 16px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .habit-card-done {
        background-color: #ecfdf5;
        border: 1px solid #a7f3d0;
    }

    /* Streak highlight box */
    .streak-box {
        background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
        border: 1px solid #fed7aa;
        border-radius: 18px;
        padding: 18px;
        text-align: center;
        margin: 20px 0;
    }
    .streak-title {
        font-size: 13px;
        color: #9a3412;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .streak-count {
        font-size: 32px;
        font-weight: 800;
        color: #ea580c;
        margin-top: 4px;
    }

    /* Weekly progress tracker boxes */
    .week-day {
        text-align: center;
        font-size: 13px;
        font-weight: 700;
        color: #475569;
        margin-bottom: 6px;
    }
    .day-box-done {
        width: 36px;
        height: 36px;
        background-color: #10b981;
        border-radius: 10px;
        margin: 0 auto;
        box-shadow: 0 3px 8px rgba(16, 185, 129, 0.3);
    }
    .day-box-empty {
        width: 36px;
        height: 36px;
        background-color: #e2e8f0;
        border-radius: 10px;
        margin: 0 auto;
    }

    /* Button styling */
    div.stButton > button {
        background-color: #10b981;
        color: white;
        border-radius: 12px;
        border: none;
        font-weight: 600;
        padding: 0.4rem 1rem;
        transition: 0.2s;
    }
    div.stButton > button:hover {
        background-color: #059669;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. Database Setup (SQLite) ---
def init_db():
    conn = sqlite3.connect("habits.db")
    c = conn.cursor()
    # Table to store habits and current streak
    c.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            streak INTEGER DEFAULT 0,
            last_done TEXT
        )
    """)
    # Table to track weekly progress logs (M T W T F S S)
    c.execute("""
        CREATE TABLE IF NOT EXISTS habit_logs (
            habit_id INTEGER,
            done_date TEXT,
            PRIMARY KEY (habit_id, done_date)
        )
    """)
    conn.commit()
    conn.close()

# --- 4. Streak Calculation Logic ---
def update_streak(last_done_str, streak):
    today = date.today()
    if not last_done_str:
        return 1
    last_done = date.fromisoformat(last_done_str)
    gap = (today - last_done).days
    if gap == 1:
        return streak + 1
    elif gap > 1:
        return 1
    else:
        return streak

# --- 5. Database CRUD Operations ---
def add_habit(name):
    conn = sqlite3.connect("habits.db")
    c = conn.cursor()
    c.execute("INSERT INTO habits (name, streak, last_done) VALUES (?, 0, NULL)", (name,))
    conn.commit()
    conn.close()

def delete_habit(habit_id):
    conn = sqlite3.connect("habits.db")
    c = conn.cursor()
    c.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    c.execute("DELETE FROM habit_logs WHERE habit_id = ?", (habit_id,))
    conn.commit()
    conn.close()

def get_habits():
    conn = sqlite3.connect("habits.db")
    c = conn.cursor()
    c.execute("SELECT id, name, streak, last_done FROM habits")
    rows = c.fetchall()
    conn.close()
    return rows

def toggle_habit(habit_id, is_checked, current_streak, last_done_str):
    conn = sqlite3.connect("habits.db")
    c = conn.cursor()
    today_str = date.today().isoformat()
    if is_checked:
        new_streak = update_streak(last_done_str, current_streak)
        c.execute("UPDATE habits SET streak = ?, last_done = ? WHERE id = ?", (new_streak, today_str, habit_id))
        c.execute("INSERT OR IGNORE INTO habit_logs (habit_id, done_date) VALUES (?, ?)", (habit_id, today_str))
    else:
        # Revert streak if today's checkbox is unchecked
        yesterday_str = (date.today() - timedelta(days=1)).isoformat()
        reverted_streak = max(0, current_streak - 1)
        prev_date = yesterday_str if reverted_streak > 0 else None
        c.execute("UPDATE habits SET streak = ?, last_done = ? WHERE id = ?", (reverted_streak, prev_date, habit_id))
        c.execute("DELETE FROM habit_logs WHERE habit_id = ? AND done_date = ?", (habit_id, today_str))
    conn.commit()
    conn.close()

def get_weekly_progress():
    conn = sqlite3.connect("habits.db")
    c = conn.cursor()
    today = date.today()
    # Get Monday's date for the current week
    start_of_week = today - timedelta(days=today.weekday())
    week_status = []
    for i in range(7):
        day = (start_of_week + timedelta(days=i)).isoformat()
        c.execute("SELECT COUNT(*) FROM habit_logs WHERE done_date = ?", (day,))
        count = c.fetchone()[0]
        week_status.append(count > 0)
    conn.close()
    return week_status

# --- 6. Main User Interface Layout ---
init_db()

# Top header and "+ Add" popover button
col_title, col_btn = st.columns([3, 1.3])
with col_title:
    st.markdown('<div class="app-header">My Habits</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="app-sub">{date.today().strftime("%A, %d %b %Y")}</div>', unsafe_allow_html=True)

with col_btn:
    st.write("")
    with st.popover("➕ Add"):
        with st.form("add_habit_form", clear_on_submit=True):
            new_habit = st.text_input("Habit Name", placeholder="💧 Drink water")
            if st.form_submit_button("Save"):
                if new_habit.strip():
                    add_habit(new_habit.strip())
                    st.rerun()

# Render list of habits
habits = get_habits()
today_str = date.today().isoformat()

if not habits:
    st.info("Click **➕ Add** above to create your first habit (e.g., 💧 Drink water, 📖 Read 20 min).")
else:
    for h_id, name, streak, last_done in habits:
        is_done_today = (last_done == today_str)
        c1, c2, c3 = st.columns([4, 1.2, 0.8])
        with c1:
            checked = st.checkbox(f"**{name}**", value=is_done_today, key=f"habit_{h_id}")
            if checked != is_done_today:
                toggle_habit(h_id, checked, streak, last_done)
                st.rerun()
        with c2:
            st.markdown(f"<div style='padding-top:5px; color:#ea580c; font-weight:700;'>🔥 {streak}d</div>", unsafe_allow_html=True)
        with c3:
            if st.button("🗑️", key=f"del_{h_id}", help="Delete habit"):
                delete_habit(h_id)
                st.rerun()

# Current best streak highlight card
max_streak = max([h[2] for h in habits], default=0)
st.markdown(f"""
    <div class="streak-box">
        <div class="streak-title">🔥 Current Streak</div>
        <div class="streak-count">{max_streak} days</div>
    </div>
""", unsafe_allow_html=True)

# Weekly progress tracker (M T W T F S S)
days_labels = ["M", "T", "W", "T", "F", "S", "S"]
week_data = get_weekly_progress()

cols = st.columns(7)
for idx, col in enumerate(cols):
    with col:
        st.markdown(f'<div class="week-day">{days_labels[idx]}</div>', unsafe_allow_html=True)
        box_class = "day-box-done" if week_data[idx] else "day-box-empty"
        st.markdown(f'<div class="{box_class}"></div>', unsafe_allow_html=True)
