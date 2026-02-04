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
        
        cur.execute("SELECT config_calibre_dir FROM settings")
        row = cur.fetchone()
        print("--- Calibre Library Path ---")
        print(f"Configured Directory: '{row['config_calibre_dir']}'")
        
        con.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
