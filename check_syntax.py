import ast
import traceback

file_path = 'app_dashboard.py'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    ast.parse(source)
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax Error: {e}")
    print(f"Line: {e.lineno}, Offset: {e.offset}")
    print(f"Text: {e.text}")
except Exception as e:
    traceback.print_exc()
