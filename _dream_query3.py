import sqlite3
import os

DB = os.path.expanduser(r"~\.local\share\mimocode\mimocode.db")
PID = "543857b2-07e1-48f0-b6df-0ff860d9b440"

conn = sqlite3.connect(DB)
c = conn.cursor()

# Find user messages with rule/decision keywords in last 7 days
keywords = ["always", "never", "remember", "rule", "decision", "decided", "reason",
            "repeat", "again", "every time", "workflow", "blocking", "must", "should"]

print("=== USER MESSAGES WITH RULE KEYWORDS (last 7 days) ===")
for kw in keywords:
    c.execute("""
        SELECT m.id, m.session_id, 
               datetime(m.time_created/1000, 'unixepoch') as created,
               json_extract(p.data, '$.text') as text
        FROM message m
        JOIN part p ON p.message_id = m.id
        WHERE m.project_id = ?
          AND json_extract(m.data, '$.role') = 'user'
          AND m.time_created >= 1784205293256
          AND json_extract(p.data, '$.type') = 'text'
          AND LOWER(json_extract(p.data, '$.text')) LIKE ?
        ORDER BY m.time_created
        LIMIT 5
    """, (PID, f"%{kw}%"))
    rows = c.fetchall()
    if rows:
        print(f"\n  Keyword: '{kw}'")
        for row in rows:
            text = row[3][:200] if row[3] else "N/A"
            print(f"    [{row[2]}] {row[0]}: {text}")

# Find repeated error text
print("\n=== REPEATED ERROR TEXT IN TOOL OUTPUT ===")
c.execute("""
    SELECT json_extract(p.data, '$.state.output') as output
    FROM message m
    JOIN part p ON p.message_id = m.id
    WHERE m.project_id = ?
      AND json_extract(m.data, '$.role') = 'assistant'
      AND json_extract(p.data, '$.type') = 'tool'
      AND json_extract(p.data, '$.tool') = 'bash'
      AND m.time_created >= 1784205293256
    ORDER BY m.time_created
""", (PID,))

errors = {}
for row in c.fetchall():
    if row[0] and "error" in row[0].lower():
        # Extract first 100 chars of error lines
        for line in row[0].split('\n'):
            line = line.strip()
            if line and 'error' in line.lower():
                key = line[:80]
                errors[key] = errors.get(key, 0) + 1

for err, count in sorted(errors.items(), key=lambda x: -x[1])[:10]:
    print(f"  [{count}x] {err}")
