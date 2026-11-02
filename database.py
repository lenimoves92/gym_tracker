import os
from contextlib import contextmanager
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
        cursor_factory=psycopg2.extras.RealDictCursor,
        connect_timeout=10  # fail fast instead of hanging if the DB is unreachable
    )
    return conn


@contextmanager
def db_cursor():
    """Yield a cursor. Commits on success, rolls back on error, always closes the connection."""
    conn = get_db()
    try:
        with conn:  # psycopg2: commit on success, rollback on exception (does not close)
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()


def init_db():
    """Seed predefined equipment if the table is empty.
    Tables must already exist — create them in the Supabase SQL editor.
    """
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM equipment")
        count = cur.fetchone()["count"]
        if count == 0:
            for name in PREDEFINED_EQUIPMENT:
                cur.execute(
                    "INSERT INTO equipment (name, is_custom) VALUES (%s, 0)",
                    (name,)
                )
