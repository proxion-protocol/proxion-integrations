import sqlite3
import os
import uuid

DB_PATH = "config/app.db"

def main():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found")
        return

    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        # Check for admin role value
        cur.execute("SELECT role FROM user WHERE name='admin'")
        admin = cur.fetchone()
        admin_role = admin['role'] if admin else 1
        print(f"Admin Role Value: {admin_role}")
        
        # Check if user exists
        cur.execute("SELECT * FROM user WHERE name='cafetechne'")
        user = cur.fetchone()
        
        if user:
            print("User 'cafetechne' already exists.")
        else:
            print("Creating user 'cafetechne'...")
            # Generate a random password hash (dummy) since we use SSO
            # Calibre uses pbkdf2 usually, but for SSO only name matches.
            # We strictly need valid columns.
            cur.execute("""
                INSERT INTO user (name, email, role, password, locale, sidebar_view, kobo_only_shelves_sync)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('cafetechne', 'cafetechne@proxion.local', admin_role, 'pbkdf2:sha256:dummy', 'en', 1, 0))
            con.commit()
            print("✅ User 'cafetechne' created successfully!")
            
        con.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
