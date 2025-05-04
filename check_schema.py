import sqlite3
import os

DATABASE_FILENAME = 'fixmate.db'
TABLE_TO_CHECK = 'users'

# Construct the absolute path to the database file
db_path = os.path.abspath(DATABASE_FILENAME)
print(f"Attempting to check schema for table '{TABLE_TO_CHECK}' in database:")
print(f"'{db_path}'\n")

if not os.path.exists(db_path):
    print(f"ERROR: Database file not found at the expected location.")
else:
    conn = None # Initialize connection variable
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print(f"Columns in table '{TABLE_TO_CHECK}':")
        # Use PRAGMA table_info to get column details
        cursor.execute(f"PRAGMA table_info({TABLE_TO_CHECK});")
        columns = cursor.fetchall()

        if not columns:
            print(f" -> Table '{TABLE_TO_CHECK}' not found or is empty.")
        else:
            # The column name is the second item (index 1) in each row returned by PRAGMA table_info
            for column in columns:
                print(f" -> {column[1]}") # column[1] is the column name

    except sqlite3.Error as e:
        print(f"An error occurred while accessing the database: {e}")

    finally:
        if conn:
            conn.close()
            # print("\nDatabase connection closed.")