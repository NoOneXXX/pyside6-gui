import os
import shutil
from pathlib import Path

def check_file_dir_exist(str_path=None):
    # Check if a file exists
    file_path = Path(str_path)
    if file_path.is_file() or file_path.is_dir():
        return True
    return False

def copy_and_overwrite(file_path, target_file_path):
    shutil.copy2(file_path, target_file_path)  # Copy the file (with metadata)

def get_parent_path(file_path):
    if file_path:
        return Path(file_path).absolute().parent
    return None

if __name__ == '__main__':
    # dd = check_file_dir_exist('C:\\22.log')
    dd = get_parent_path('C:\\22.log')
    print(dd)