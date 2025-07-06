import os


import json
import os
from pathlib import Path

class JsonEditor:
    def __init__(self):
        self.data = {}
        self._loaded = False

    def load(self):
        """赋值json"""
        self.data = {
            "node": {
                "version": "1.0.0.0.0",
                "id": "e7e13a6b-b07c-4365-b468-25626cb9dea4",
                "detail_info": {
                    "modified_time": 1734057255,
                    "content_type": "dir",
                    "created_time": 1734057255,
                    "title": "java interview",
                    "has_children": False,
                    "order": 1,
                    "max_order_num_by_child_dir":0,
                    "info_sort": "order",
                    "bg_color": "",
                    "open_dir_icon": ":images/folder-orange-open.png",
                    "close_dir_icon": ":images/folder-orange.png",
                    "adds_on_icon": "",
                    "font_color": ""
                }
            }
        }
        return self.data

    def modify(self, func):
        """传入一个修改函数，对数据进行修改"""
        if not self._loaded:
            raise RuntimeError("JSON not loaded. Call load() first.")
        self.data = func(self.data)
        return self

    def write(self, output_path=None):
        """写入到文件，output_path 为空则覆盖原文件"""
        target = Path(output_path)
        with target.open('w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        return self

    def writeByData(self, output_path=None, data=None):
        """写入到文件，output_path 为空则覆盖原文件"""
        self.data = data
        self.write(output_path)
        return self

    def get_data(self):
        """返回当前 JSON 数据"""
        return self.data

    def set_data(self, new_data):
        """替换当前 JSON 数据"""
        self.data = new_data
        self._loaded = True
        return self

    '''
    读取json文件的内容
    '''
    def read_notebook_if_dir(self, folder_path):
        if folder_path is not None:
            meta_path = os.path.join(folder_path, ".metadata.json")
            if not os.path.exists(meta_path):
                return "未知笔记"

            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("node", {}).get("detail_info", {}).get("content_type", "")

    '''读取这文件的detail_info信息'''
    def read_file_metadata_infos(self, folder_path):
        if folder_path is not None:
            meta_path = os.path.join(folder_path, ".metadata.json")
            if not os.path.exists(meta_path):
                return None

            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("node", {}).get("detail_info", {})


    '''读取node的节点'''
    def read_node_infos(self, folder_path):
        if folder_path is not None:
            meta_path = os.path.join(folder_path, ".metadata.json")
            if not os.path.exists(meta_path):
                return "未知笔记"

            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data

'''判断是否有文件夹 在一个文件夹下面'''
def has_subfolder(folder_path):
    # 列出文件夹中的所有项
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        # 检查是否为文件夹
        if os.path.isdir(item_path):
            return True
    return False

def traverse_folder(path, indent=0):
    try:
        # 获取指定路径下的所有文件和文件夹
        flag_dir = True
        for item in os.listdir(path):
            # 构建完整的路径
            item_path = os.path.join(path, item)
            # 判断是否为文件夹
            if 'page.html' in item_path:
                flag_dir = False
                new_item_path = os.path.join(path, '.note.html')
                try:
                    os.rename(item_path, new_item_path)
                    # 创建新的json文件
                    json_editor = JsonEditor()
                    data = json_editor.load()
                    data['node']['detail_info']['content_type'] = 'file'
                    new_file_meta = os.path.join(path, '.metadata.json')
                    json_editor.writeByData(new_file_meta, data)
                    print('  ' * indent + f'已将 {item} 重命名为 .note.html')
                except Exception as e:
                    print('  ' * indent + f'重命名 {item} 失败: {str(e)}')
            # 存在这个就删除
            if 'note.xml' in item_path:
                os.remove(item_path)
        # 是文件夹 就直接的创建
        if flag_dir:
            # 创建新的json文件
            json_editor = JsonEditor()
            data = json_editor.load()
            if has_subfolder(path):
                data['node']['detail_info']['has_children'] = True
            new_path_meta = os.path.join(path, '.metadata.json')
            json_editor.writeByData(new_path_meta, data)

            for item in os.listdir(path):
                # 构建完整的路径
                item_path = os.path.join(path, item)
                # 判断交给上面得做
                traverse_folder(item_path, indent + 1)
    except PermissionError as ps2:
        print('  ' * indent + f'无权限访问: {path},错误信息是：{ps2}')
    except Exception as e:
        print('  ' * indent + f'错误: {path} - {str(e)}')


def main():
    # 指定要遍历的文件夹路径
    folder_path = r"C:\Users\Dell\Desktop\MySoftwareNote"

    # 检查路径是否存在
    if not os.path.exists(folder_path):
        print("错误: 指定的路径不存在！")
        return

    # 检查是否为文件夹
    if not os.path.isdir(folder_path):
        print("错误: 指定的路径不是文件夹！")
        return

    print(f"\n开始遍历文件夹: {folder_path}")
    print("=" * 50)
    traverse_folder(folder_path)


if __name__ == "__main__":
    main()