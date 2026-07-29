import sqlite3
import os

DB = os.path.expanduser(r"~\.local\share\mimocode\mimocode.db")
PID = "543857b2-07e1-48f0-b6df-0ff860d9b440"

conn = sqlite3.connect(DB)
c = conn.cursor()

# 1. List recent sessions
print("=== RECENT SESSIONS ===")
c.execute("SELECT id, title, time_created FROM session WHERE project_id=? ORDER BY time_created DESC LIMIT 15", (PID,))
for row in c.fetchall():
    print(f"  {row[0]} | {row[1][:80] if row[1] else 'N/A'} | {row[2]}")

# 2. For each of last 7 days, count sessions
print("\n=== SESSION COUNT BY DATE (last 7 days) ===")
c.execute("""
    SELECT date(time_created) as d, count(*)
    FROM session
    WHERE project_id=? AND time_created >= datetime('now', '-7 days')
    GROUP BY d ORDER BY d
""", (PID,))
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]} sessions")
