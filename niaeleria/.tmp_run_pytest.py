import os
import subprocess
import sys

root = os.path.dirname(os.path.abspath(__file__))
os.chdir(root)
print('cwd:', root)
print('python:', sys.executable)
print('pytest version:')
subprocess.run([sys.executable, '-m', 'pytest', '--version'])
print('running tests...')
result = subprocess.run([sys.executable, '-m', 'pytest', '-q'], capture_output=True, text=True)
print('returncode:', result.returncode)
print('stdout:\n', result.stdout)
print('stderr:\n', result.stderr)
