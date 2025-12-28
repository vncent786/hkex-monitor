from pathlib import Path
p1 = Path("files\ghi.txt")
print(type(p1))

if not p1.exists():
    with open(p1, 'w') as file:
        file.write('Content 3')

