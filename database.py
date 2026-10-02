"""Main Data Layer"""

import sqlite3
import json

# provides access to the database
def get_db():
    connection = sqlite3.connect("database.db")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection

# Initializing the database based on "schema.sql"
def init_db():
    connection = get_db()   

    with open("schema.sql") as f:
        connection.executescript(f.read())
    connection.commit()
    connection.close()

# Populates subjects with options based on subjects.json
def set_subjects():
    # Loads data from subject.json
    with open("data/subjects.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    subjects = data["subjects"] # access to subject dicts

    # Start connection to db
    connection = get_db()

    # Each subject based on the json is added to db
    for subject in subjects:
        connection.execute("INSERT OR IGNORE INTO subjects (subject_name, level, total_topics) VALUES (?,?,?)", 
                           (subject["subject_name"], subject["level"], subject["total_topics"]))
        # IGNORE avoids error from UNIQUE (constraint within the database creation)

    connection.commit()
    connection.close()

# Populates grade boundaries based on grade_boundaries.json
def set_grade_boundaries():
    # Loads data from grade_boundaries.json
    with open("data/grade_boundaries.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    grade_boundaries = data["grade_boundaries"] # access to grade boundaries dicts

    # Start connection to db
    connection = get_db()
    cursor = connection.cursor()

    # Each subject's grade boundaries are added to db
    for subject in grade_boundaries:
        # finds subject id based on subject name and level
        cursor.execute("""SELECT subject_id FROM subjects
                          WHERE subject_name=? AND level=?""",
                       (subject["subject_name"], subject["level"]))

        subject_row = cursor.fetchone()

        # skips subject if it isn't found in subjects
        if subject_row is None:
            continue

        subject_id = subject_row["subject_id"]

        # adds each grade boundary for the subject
        for grade, lower_boundary in subject["boundaries"].items():
            grade = int(grade)

            # checks if boundary is already in database
            cursor.execute("""SELECT boundary_id FROM grade_boundaries
                              WHERE subject_id=? AND exam_year=? AND exam_session=? AND grade=?""",
                           (subject_id, subject["exam_year"], subject["exam_session"], grade))

            existing_boundary = cursor.fetchone()

            if existing_boundary is None:
                cursor.execute("""INSERT INTO grade_boundaries
                                  (subject_id, exam_year, exam_session, grade, lower_boundary)
                                  VALUES (?,?,?,?,?)""",
                               (subject_id, subject["exam_year"],
                                subject["exam_session"], grade,
                                lower_boundary))

    connection.commit()
    connection.close()

if __name__ == "__main__":
    init_db()
    set_subjects()
    set_grade_boundaries()