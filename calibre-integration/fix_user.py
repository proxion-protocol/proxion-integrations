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
        
        print("--- Patching User Settings ---")
        # Check current state
        cur.execute("SELECT name, view_settings FROM user WHERE name='cafetechne'")
        user = cur.fetchone()
        if user:
            print(f"Current view_settings: {user['view_settings']}")
        
        # Update view_settings to empty json object if None or empty
        cur.execute("UPDATE user SET view_settings='{}' WHERE name='cafetechne'")
        con.commit()
        
        print("✅ User 'cafetechne' patched with default view_settings='{}'")
        
        # Verify
        cur.execute("SELECT name, view_settings FROM user WHERE name='cafetechne'")
        user = cur.fetchone()
        print(f"New view_settings: {user['view_settings']}")
        
        con.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
