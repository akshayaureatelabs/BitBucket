import sqlite3
import os
from datetime import datetime, timedelta

DB = os.path.expanduser(r"~\.local\share\mimocode\mimocode.db")
PID = "543857b2-07e1-48f0-b6df-0ff860d9b440"

conn = sqlite3.connect(DB)
c = conn.cursor()

# Convert timestamps and filter last 7 days
seven_days_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

print(f"=== SESSIONS SINCE {seven_days_ago} ===")
c.execute("""
    SELECT id, title, time_created,
           datetime(time_created/1000, 'unixepoch') as created_utc
    FROM session 
    WHERE project_id=?
    ORDER BY time_created DESC
""", (PID,))

sessions = []
for row in c.fetchall():
    sid, title, ts, created = row
    if created and created >= seven_days_ago:
        sessions.append((sid, title[:100] if title else "N/A", created))
        print(f"  {sid} | {title[:80] if title else 'N/A'} | {created}")

print(f"\nTotal: {len(sessions)} sessions in last 7 days")

# Also list ALL sessions (all time count)
c.execute("SELECT count(*) FROM session WHERE project_id=?", (PID,))
total = c.fetchone()[0]
print(f"Total all-time: {total} sessions")
