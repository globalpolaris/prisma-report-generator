import sqlite3

def create_db():
    try:
        conn = sqlite3.connect('prisma_report.db')
        cursor = conn.cursor()
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS waas_files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT,
                        timestamp TEXT
                        )''')
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS runtime_files (
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

def insert_file(filename, table, timestamp):
    try:
        conn = sqlite3.connect('prisma_report.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO {} (filename, timestamp) VALUES (?, ?)".format(table), (filename, timestamp))
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
def get_files(table):
    try:
        conn = sqlite3.connect('prisma_report.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM {}".format(table))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        if "no such table" in str(e):
            print("Table not found, creating...")
            create_db()
            print("Tabel created successfully")
        conn.close()
        return []

def delete_file(filename, table):
    try:
        conn = sqlite3.connect('prisma_report.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM {} WHERE filename=?".format(table), (filename,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()