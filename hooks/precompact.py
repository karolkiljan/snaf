import json
import sys
import os

data = json.load(sys.stdin)
trigger = data.get("trigger", "")
cwd = data.get("cwd", os.getcwd())

notes_file = os.path.join(cwd, ".claude", "compact_notes.md")

if not os.path.exists(notes_file):
    sys.exit(0)

with open(notes_file) as f:
    notes = f.read().strip()

if not notes:
    sys.exit(0)

print(notes)

os.remove(notes_file)
