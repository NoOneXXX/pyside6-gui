import os
import json

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
