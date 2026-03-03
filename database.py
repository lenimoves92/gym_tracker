import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'gym.db')

PREDEFINED_EQUIPMENT = [
    "Barbell Squat", "Barbell Bench Press", "Barbell Deadlift",
    "Barbell Overhead Press", "Pull-Up / Chin-Up", "Dumbbell Curl",
    "Dumbbell Lateral Raise", "Dumbbell Row", "Leg Press",
    "Leg Curl", "Leg Extension", "Lat Pulldown", "Cable Row",
    "Cable Fly", "Chest Press Machine", "Shoulder Press Machine",
    "Tricep Pushdown", "Dip", "Romanian Deadlift",
    "Hip Thrust", "Treadmill (Cardio)"
]


def get_db():
    """Open a database connection. Rows are accessible like dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and seed predefined equipment if not already present."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL UNIQUE,
            is_custom INTEGER NOT NULL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS workout_sets (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            weight       REAL NOT NULL,
            weight_unit  TEXT NOT NULL DEFAULT 'kg',
            reps         INTEGER NOT NULL,
            rpe          INTEGER NOT NULL,
            logged_at    TEXT NOT NULL,
            notes        TEXT,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        )
    """)

    count = cur.execute("SELECT COUNT(*) FROM equipment").fetchone()[0]
    if count == 0:
        for name in PREDEFINED_EQUIPMENT:
            cur.execute(
                "INSERT INTO equipment (name, is_custom) VALUES (?, 0)",
                (name,)
            )

    conn.commit()
    conn.close()
