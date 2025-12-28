from pathlib import Path

root_dir = Path('files')
file_paths = root_dir.iterdir()

for path in file_paths:
    new_filename = "new-" + path.stem + path.suffix
    new_filepath = path.with_name(new_filename)
    path.rename(new_filepath)