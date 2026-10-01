"""Main Data Layer"""

import sqlite3

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

if __name__ == "__main__":
    init_db()