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
                    "info_sort": "order",
                    "bg_color": "",
                    "open_dir_icon": ":images/folder-orange-open.png",
                    "close_dir_icon": ":images/folder-orange.png",
                    "adds_on_icon": "",
                    "font_color": ""
                }
            }
        }
        return self

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
                return "未知笔记"

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

if __name__ == '__main__':
    # 使用示例
    # def add_tag(data):
    #     data['tag'] = 'new'
    #     return data
    # JsonEditor('../../ui/metadata.json').load().modify(add_tag).write('output.json')



    # 创建编辑器并加载
    # editor = JsonEditor().load()
    #
    # # 直接修改字段
    # data = editor.get_data()
    # data['tag'] = 'new'
    # data['priority'] = 5
    #
    # # 写入到原文件或新文件
    # editor.write('output.json')
    dir_path = 'C:/Users/Dell/Desktop'
    name = 'te'
    file_path = os.path.join(dir_path, name)
    print(file_path)
    os.makedirs(file_path, exist_ok=True)

