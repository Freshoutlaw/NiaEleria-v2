from pathlib import Path
from typing import List

root = Path('.')
py_files: List[Path] = sorted(p for p in root.rglob('*.py') if p.is_file())
marker = 'from __future__ import annotations'

for path in py_files:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    if any(line.strip() == marker for line in lines[:5]):
        continue

    insert_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#!'):
            insert_idx = i + 1
            continue
        if stripped.startswith('from __future__ import'):
            insert_idx = i + 1
            continue
        if stripped and not stripped.startswith('#'):
            break

    new_lines = lines[:insert_idx] + [marker] + lines[insert_idx:]
    path.write_text('\n'.join(new_lines) + ('\n' if text.endswith('\n') else ''), encoding='utf-8')
    print(f'Updated: {path}')
