import sqlite3

# Initializing the database based on "schema.sql"
def init_db():
    connection = sqlite3.connect("database.db")
    connection.execute("PRAGMA foreign_keys = ON")
    with open("schema.sql") as f:
        connection.executescript(f.read())
    connection.commit()
    connection.close()


init_db()