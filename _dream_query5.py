import sqlite3
import os

DB = os.path.expanduser(r"~\.local\share\mimocode\mimocode.db")
PID = "543857b2-07e1-48f0-b6df-0ff860d9b440"

conn = sqlite3.connect(DB)
c = conn.cursor()

# Get session IDs for this project
c.execute("SELECT id FROM session WHERE project_id=?", (PID,))
session_ids = [r[0] for r in c.fetchall()]
placeholders = ",".join("?" * len(session_ids))

# Find user messages with rule/decision keywords
keywords = ["always", "never", "remember", "rule", "decision", "decided",
            "repeat", "every time", "must", "blocking", "strict"]

# Build SQL with safe placeholder string (only ? marks, no user data)
KW_QUERY = """
        SELECT m.id, m.session_id,
               datetime(m.time_created/1000, 'unixepoch') as created,
               json_extract(p.data, '$.text') as text
        FROM message m
        JOIN part p ON p.message_id = m.id
        WHERE m.session_id IN (%s)
          AND json_extract(m.data, '$.role') = 'user'
          AND json_extract(p.data, '$.type') = 'text'
          AND LOWER(json_extract(p.data, '$.text')) LIKE ?
        ORDER BY m.time_created
        LIMIT 3
    """ % placeholders

print("=== USER MESSAGES WITH RULE/DECISION KEYWORDS ===")
for kw in keywords:
    c.execute(KW_QUERY, session_ids + [f"%{kw}%"])
    rows = c.fetchall()
    if rows:
        print(f"\n  Keyword: '{kw}'")
        for row in rows:
            text = (row[3][:250] if row[3] else "N/A").replace("\n", " ")
            print(f"    [{row[2]}] sid={row[1][:20]}: {text}")

# Search for Hinglish/Hindi content markers
print("\n=== HINGLISH/HINDI CONTENT IN USER MESSAGES ===")
HINDI_QUERY = """
    SELECT m.session_id,
           datetime(m.time_created/1000, 'unixepoch') as created,
           json_extract(p.data, '$.text') as text
    FROM message m
    JOIN part p ON p.message_id = m.id
    WHERE m.session_id IN (%s)
      AND json_extract(m.data, '$.role') = 'user'
      AND json_extract(p.data, '$.type') = 'text'
    ORDER BY m.time_created
""" % placeholders

c.execute(HINDI_QUERY, session_ids)

hindi_count = 0
for row in c.fetchall():
    text = row[2] or ""
    # Simple Hindi marker: common Hinglish words
    hindi_markers = ["kaise", "kya", "hai", "he", "kar", "karva", "bata", "bhai",
                     "muje", "sahi", "chahiye", "mein", "mene", "jise", "usko",
                     "konsi", "konsa", "kaha", "kab", "kyu", "kyun", "hoga",
                     "jan", "bujh", "bol", "bolu", "bolo", "chal", "ho"]
    if any(m in text.lower() for m in hindi_markers):
        hindi_count += 1
        if hindi_count <= 5:
            print(f"  [{row[1][:20]}] {row[0]}: {text[:150].replace(chr(10), ' ')}")

print(f"\n  Total Hinglish messages: {hindi_count}")

# Find repeated errors in bash tool output
print("\n=== REPEATED BASH ERRORS ===")
ERROR_QUERY = """
    SELECT json_extract(p.data, '$.state.output') as output
    FROM message m
    JOIN part p ON p.message_id = m.id
    WHERE m.session_id IN (%s)
      AND json_extract(m.data, '$.role') = 'assistant'
      AND json_extract(p.data, '$.type') = 'tool'
      AND json_extract(p.data, '$.tool') = 'bash'
    ORDER BY m.time_created
""" % placeholders

c.execute(ERROR_QUERY, session_ids)

errors = {}
for row in c.fetchall():
    if row[0]:
        for line in row[0].split('\n'):
            line = line.strip()
            if line and ('error' in line.lower() or 'traceback' in line.lower()):
                key = line[:100]
                errors[key] = errors.get(key, 0) + 1

for err, count in sorted(errors.items(), key=lambda x: -x[1])[:8]:
    print(f"  [{count}x] {err}")
