import os
import psycopg2
import psycopg2.extras

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
    """Open a Supabase (PostgreSQL) connection. Rows are accessible like dicts."""
    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn


def init_db():
    """Seed predefined equipment if the table is empty.
    Tables must already exist — create them in the Supabase SQL editor.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM equipment")
    count = cur.fetchone()["count"]
    if count == 0:
        for name in PREDEFINED_EQUIPMENT:
            cur.execute(
                "INSERT INTO equipment (name, is_custom) VALUES (%s, 0)",
                (name,)
            )
    conn.commit()
    cur.close()
    conn.close()
