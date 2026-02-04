import sqlite3
import os

DB_PATH = "config/app.db"

def main():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found")
        return

    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        print("--- Checking Schema ---")
        cur.execute("PRAGMA table_info(user)")
        columns = cur.fetchall()
        for col in columns:
            print(f"{col['cid']}: {col['name']} ({col['type']})")
            
        print("\n--- Checking Users (Dump) ---")
        cur.execute("SELECT * FROM user")
        users = cur.fetchall()
        for u in users:
            # Print available keys using the Row object
            print(dict(u))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
