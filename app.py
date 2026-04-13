from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = 'gym-tracker-secret-key'

RPE_HEAVY_THRESHOLD = 6  # RPE at or below this triggers "go heavier" suggestion

with app.app_context():
    init_db()


# --- Home: Log a Set ---

@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM equipment ORDER BY name")
    equipment_list = cur.fetchall()
    conn.close()
    preselect_id = request.args.get('exercise_id', type=int)
    return render_template('index.html', equipment_list=equipment_list, preselect_id=preselect_id)


@app.route('/log', methods=['POST'])
def log_set():
    equipment_id = request.form.get('equipment_id')
    weight       = request.form.get('weight')
    weight_unit  = request.form.get('weight_unit', 'kg')
    reps         = request.form.get('reps')
    rpe          = request.form.get('rpe')
    notes        = request.form.get('notes', '').strip()
    logged_at    = datetime.now().isoformat(sep=' ', timespec='seconds')

    errors = []
    if not equipment_id:
        errors.append("Please select an exercise.")
    try:
        w = float(weight)
        if w <= 0:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("Please enter a valid weight.")
        w = None
    try:
        r = int(reps)
        if r <= 0:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("Please enter a valid rep count.")
        r = None
    try:
        rpe_val = int(rpe)
        if not (1 <= rpe_val <= 10):
            raise ValueError
    except (TypeError, ValueError):
        errors.append("RPE must be between 1 and 10.")
        rpe_val = None

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('index'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO workout_sets
           (equipment_id, weight, weight_unit, reps, rpe, logged_at, notes)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (int(equipment_id), w, weight_unit, r, rpe_val, logged_at, notes or None)
    )
    conn.commit()
    conn.close()

    if rpe_val <= RPE_HEAVY_THRESHOLD:
        flash(
            f"Set logged! RPE {rpe_val} is low — consider going heavier next session.",
            'warning'
        )
    else:
        flash("Set logged!", 'success')

    return redirect(url_for('index'))


# --- History ---

@app.route('/history')
def history():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """SELECT ws.id, e.name AS exercise, ws.weight, ws.weight_unit,
                  ws.reps, ws.rpe, ws.logged_at, ws.notes
           FROM workout_sets ws
           JOIN equipment e ON ws.equipment_id = e.id
           ORDER BY ws.logged_at DESC
           LIMIT 300"""
    )
    rows = cur.fetchall()
    conn.close()

    # Group: date -> exercise -> sets
    grouped = {}
    for row in rows:
        date_str = row['logged_at'][:10]
        exercise = row['exercise']
        grouped.setdefault(date_str, {}).setdefault(exercise, []).append(row)

    grouped_list = [
        (date, list(exercises.items()))
        for date, exercises in sorted(grouped.items(), reverse=True)
    ]

    return render_template('history.html', grouped_list=grouped_list)


@app.route('/delete/<int:set_id>', methods=['POST'])
def delete_set(set_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM workout_sets WHERE id = %s", (set_id,))
    conn.commit()
    conn.close()
    flash("Set deleted.", 'info')
    return redirect(url_for('history'))


# --- Equipment Management ---

@app.route('/equipment')
def equipment():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, is_custom FROM equipment ORDER BY name")
    equipment_list = cur.fetchall()
    conn.close()
    return render_template('equipment.html', equipment_list=equipment_list)


@app.route('/equipment/add', methods=['POST'])
def add_equipment():
    name = request.form.get('name', '').strip()
    if not name:
        flash("Please enter an exercise name.", 'danger')
        return redirect(url_for('equipment'))

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO equipment (name, is_custom) VALUES (%s, 1)",
            (name,)
        )
        conn.commit()
        flash(f"'{name}' added.", 'success')
    except Exception:
        conn.rollback()
        flash(f"'{name}' already exists.", 'warning')
    finally:
        conn.close()

    return redirect(url_for('equipment'))


@app.route('/equipment/delete/<int:equipment_id>', methods=['POST'])
def delete_equipment(equipment_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT is_custom FROM equipment WHERE id = %s", (equipment_id,)
    )
    row = cur.fetchone()
    if row and row['is_custom'] == 1:
        cur.execute("DELETE FROM equipment WHERE id = %s", (equipment_id,))
        conn.commit()
        flash("Exercise removed.", 'info')
    else:
        flash("Cannot delete built-in exercises.", 'warning')
    conn.close()
    return redirect(url_for('equipment'))


# --- Overview ---

LBS_TO_KG = 0.453592

@app.route('/overview')
def overview():
    conn = get_db()
    cur = conn.cursor()

    # All exercises for the dropdown
    cur.execute("SELECT id, name FROM equipment ORDER BY name")
    equipment_list = cur.fetchall()

    selected_id   = request.args.get('exercise_id', type=int)
    selected_name = None
    sessions      = [None, None]   # always two slots; None = no data
    chart_data    = None           # populated when an exercise is selected

    if selected_id:
        # Resolve display name
        cur.execute("SELECT name FROM equipment WHERE id = %s", (selected_id,))
        row = cur.fetchone()
        if row:
            selected_name = row['name']

        # Find the last 2 distinct calendar dates for the Topic-1 panel
        cur.execute(
            """SELECT DISTINCT DATE(logged_at) AS session_date
               FROM workout_sets
               WHERE equipment_id = %s
               ORDER BY session_date DESC
               LIMIT 2""",
            (selected_id,)
        )
        date_rows = cur.fetchall()

        for i, date_row in enumerate(date_rows):
            session_date = str(date_row['session_date'])
            cur.execute(
                """SELECT weight, weight_unit, reps, rpe
                   FROM workout_sets
                   WHERE equipment_id = %s
                     AND DATE(logged_at) = %s
                   ORDER BY logged_at ASC""",
                (selected_id, session_date)
            )
            sets = cur.fetchall()
            sessions[i] = {'date': session_date, 'sets': sets}

        # --- Chart: last 6 session dates ---
        cur.execute(
            """SELECT DISTINCT DATE(logged_at) AS session_date
               FROM workout_sets
               WHERE equipment_id = %s
               ORDER BY session_date DESC
               LIMIT 6""",
            (selected_id,)
        )
        chart_dates = [str(r['session_date']) for r in cur.fetchall()]
        chart_dates.reverse()   # oldest → newest left to right

        # For each date fetch sets in order
        chart_sessions = []
        for session_date in chart_dates:
            cur.execute(
                """SELECT weight, weight_unit, reps
                   FROM workout_sets
                   WHERE equipment_id = %s
                     AND DATE(logged_at) = %s
                   ORDER BY logged_at ASC""",
                (selected_id, session_date)
            )
            raw_sets = cur.fetchall()
            sets_out = []
            for s in raw_sets:
                weight_kg = float(s['weight']) * (LBS_TO_KG if s['weight_unit'] == 'lbs' else 1.0)
                load      = round(s['reps'] * weight_kg, 1)
                sets_out.append({
                    'reps':   s['reps'],
                    'weight': float(s['weight']),
                    'unit':   s['weight_unit'],
                    'load':   load,
                })
            chart_sessions.append({'date': session_date, 'sets': sets_out})

        # How many set-slots do we need across all sessions?
        max_sets = max((len(s['sets']) for s in chart_sessions), default=0)

        chart_data = {
            'dates':       chart_dates,
            'sessions':    chart_sessions,
            'max_sets':    max_sets,
        }

    conn.close()
    return render_template(
        'overview.html',
        equipment_list=equipment_list,
        selected_id=selected_id,
        selected_name=selected_name,
        sessions=sessions,
        chart_data=chart_data,
    )


# --- Entry point ---

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
