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
        
        cur.execute("SELECT config_public_reg, config_allow_reverse_proxy_header_login, config_reverse_proxy_login_header_name FROM settings")
        row = cur.fetchone()
        print("--- Calibre Database Settings ---")
        print(f"Public Registration (config_public_reg): {row['config_public_reg']}")
        print(f"Reverse Proxy Auth (config_allow_reverse_proxy_header_login): {row['config_allow_reverse_proxy_header_login']}")
        print(f"Header Name (config_reverse_proxy_login_header_name): '{row['config_reverse_proxy_login_header_name']}'")
        
        con.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
