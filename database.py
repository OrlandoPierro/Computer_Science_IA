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

if __name__ == "__main__":
    init_db()
    set_subjects()