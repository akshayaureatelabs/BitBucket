import sqlite3
import os

DB = os.path.expanduser(r"~\.local\share\mimocode\mimocode.db")
PID = "543857b2-07e1-48f0-b6df-0ff860d9b440"

conn = sqlite3.connect(DB)
c = conn.cursor()

# Get user messages from main sessions (not checkpoint-writer) in last 7 days
c.execute("""
    SELECT s.id, s.title, s.time_created,
           datetime(s.time_created/1000, 'unixepoch') as created
    FROM session s
    WHERE s.project_id=?
      AND s.time_created >= 1784205293256
      AND s.title NOT LIKE '%checkpoint-writer%'
    ORDER BY s.time_created
""", (PID,))

main_sessions = c.fetchall()
print("=== MAIN SESSIONS (non-checkpoint-writer) ===")
for s in main_sessions:
    print(f"  {s[0]} | {s[1][:60] if s[1] else 'N/A'} | {s[3]}")

# Get all user messages from main sessions
for s in main_sessions:
    sid = s[0]
    print(f"\n=== USER MESSAGES: {s[1][:50]} ({s[3]}) ===")
    c.execute("""
        SELECT datetime(m.time_created/1000, 'unixepoch') as created,
               json_extract(p.data, '$.text') as text
        FROM message m
        JOIN part p ON p.message_id = m.id
        WHERE m.session_id = ?
          AND json_extract(m.data, '$.role') = 'user'
          AND json_extract(p.data, '$.type') = 'text'
          AND LENGTH(json_extract(p.data, '$.text')) > 20
        ORDER BY m.time_created
    """, (sid,))
    for row in c.fetchall():
        text = (row[1][:300] if row[1] else "").replace("\n", " ")
        print(f"  [{row[0]}] {text}")
