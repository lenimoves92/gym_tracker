"""Workout-type classification of exercises — single source: exercise_types.json.

Keys are the stored exercise names (equipment.name). The type is display/filter
metadata only; stored names and history matching (by equipment_id) are unaffected.
Regenerate the JSON with tools/import_exercise_types.py when the Excel matrix changes.
"""
import json
from pathlib import Path

_data = json.loads((Path(__file__).resolve().parent / 'exercise_types.json').read_text(encoding='utf-8'))

WORKOUT_TYPES = _data['types']        # code -> label, e.g. 'Q' -> 'Quick'
EXERCISE_TYPES = _data['exercises']   # exercise name -> code


def type_of(name):
    """Type code for an exercise name, or None if it has no assignment."""
    return EXERCISE_TYPES.get(name)


def with_type(name):
    """'Pulldown' -> 'Pulldown (Q)'; unassigned names are returned unchanged."""
    code = type_of(name)
    return f"{name} ({code})" if code else name
