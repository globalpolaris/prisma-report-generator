import sqlite3

def create_db():
    try:
        conn = sqlite3.connect('prisma_report.db')
        cursor = conn.cursor()
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT,
                        timestamp TEXT
                        )''')
        conn.commit()
        conn.close()
        return None
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.close()
        return str(e)

def insert_file(filename, timestamp):
    try:
        conn = sqlite3.connect('prisma_report.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO files (filename, timestamp) VALUES (?, ?)", (filename, timestamp))
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
def get_files():
    try:
        conn = sqlite3.connect('prisma_report.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.close()
        return []

def delete_file(filename):
    try:
        conn = sqlite3.connect('prisma_report.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files WHERE filename=?", (filename,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()