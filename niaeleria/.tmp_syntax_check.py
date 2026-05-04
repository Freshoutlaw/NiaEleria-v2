from pathlib import Path
import py_compile

root = Path('.')
errors = []
for path in sorted(root.rglob('*.py')):
    if path.name.startswith('.tmp_syntax_check'):
        continue
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        errors.append((path, str(exc)))

print(len(errors), 'syntax errors found')
for path, err in errors:
    print(path)
    print(err)
