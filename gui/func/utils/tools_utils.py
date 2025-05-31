import os
import json
import time
import uuid

from gui.func.utils.json_utils import JsonEditor

'''
读取父类的id
'''
def read_parent_id(path):
    parent_path = os.path.dirname(path)
    meta_file = os.path.join(parent_path, ".metadata.json")
    if os.path.exists(meta_file):
        with open(meta_file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)["node"]["id"]
            except Exception:
                return 0
    return 0
'''
创建metadata.json文件 文件是file类型
'''
def create_metadata_file_under_dir(file_path , content_type = 'file'):
    # 3. 创建空文件 .metadata.json
    # 创建编辑器并加载
    editor = JsonEditor().load()
    # 直接修改字段
    data = editor.get_data()
    # 加上id
    id = str(uuid.uuid4())
    data['node']['id'] = id
    timestamp = int(time.time())  # 创建时间
    data['node']['detail_info']['created_time'] = timestamp
    # 创建文件类型 这里是创建的文件
    data['node']['detail_info']['content_type'] = content_type
    folder_name = os.path.basename(file_path)  # 创建名字
    data['node']['detail_info']['title'] = folder_name
    parent_id = read_parent_id(file_path)
    data['node']['detail_info']['parent_id'] = parent_id
    # 写入到原文件或新文件
    metadata_path = os.path.join(file_path, ".metadata.json")
    if not os.path.exists(metadata_path):
        editor.write(metadata_path)
'''
创建metadata.json文件 文件是dir类型
'''
def create_metadata_dir_under_dir(file_path ):
    # 3. 创建空文件 .metadata.json
    # 创建编辑器并加载
    editor = JsonEditor().load()
    # 直接修改字段
    data = editor.get_data()
    # 加上id
    id = str(uuid.uuid4())
    data['node']['id'] = id
    timestamp = int(time.time())  # 创建时间
    data['node']['detail_info']['created_time'] = timestamp
    # 创建文件类型 这里是创建的文件
    data['node']['detail_info']['content_type'] = 'dir'
    folder_name = os.path.basename(file_path)  # 创建名字
    data['node']['detail_info']['title'] = folder_name
    parent_id = read_parent_id(file_path)
    data['node']['detail_info']['parent_id'] = parent_id
    # 写入到原文件或新文件
    metadata_path = os.path.join(file_path, ".metadata.json")
    if not os.path.exists(metadata_path):
        editor.write(metadata_path)

# 扫描这个路径下面的文件名字 并且找到这个文件
def scan_supported_files(path, exts):
    for root, dirs, files in os.walk(path):
        for file in files:
            ext = os.path.splitext(file)[1].lower().lstrip('.')
            if ext in exts:
                return os.path.join(root, file)


if __name__ == '__main__':
    remp = read_parent_id('C:/Users/Dell/Desktop/temp/log/test6')
    print(remp)