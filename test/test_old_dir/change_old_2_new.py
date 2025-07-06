import os
from pathlib import Path

output_path = r"C:/Users/Dell/Desktop/MySoftwareNote/.metadata.json"
try:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('{"test": "data"}')
    print("写入成功")
except PermissionError as e:
    print(f"权限错误: {e}")
    print("请检查文件夹权限、以管理员身份运行或防病毒软件设置")
except Exception as e:
    print(f"其他错误: {e}")