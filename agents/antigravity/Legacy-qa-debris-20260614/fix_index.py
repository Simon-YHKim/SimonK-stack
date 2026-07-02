
import os
import re

file_path = r'E:\2ndB\src\app\index.tsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for the sources query part
# supabase\n        .from("sources")\n        .select(...)\n        .eq(...)\n        .order("created_at", ...)
pattern = r'(\.from\("sources"\).*?\.order\(")(created_at)(")'

new_content, count = re.subn(pattern, r'\1captured_at\3', content, flags=re.DOTALL)

if count > 0:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Successfully fixed {count} occurrences in index.tsx")
else:
    print("Could not find sources query with created_at in index.tsx")
