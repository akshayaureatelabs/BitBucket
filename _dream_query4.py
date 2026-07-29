import sqlite3
import os

DB = os.path.expanduser(r"~\.local\share\mimocode\mimocode.db")

conn = sqlite3.connect(DB)
c = conn.cursor()

# Check schema
print("=== TABLES ===")
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
for row in c.fetchall():
    print(f"  {row[0]}")

print("\n=== SESSION SCHEMA ===")
c.execute("PRAGMA table_info(session)")
for row in c.fetchall():
    print(f"  {row}")

print("\n=== MESSAGE SCHEMA ===")
c.execute("PRAGMA table_info(message)")
for row in c.fetchall():
    print(f"  {row}")

print("\n=== PART SCHEMA ===")
c.execute("PRAGMA table_info(part)")
for row in c.fetchall():
    print(f"  {row}")
