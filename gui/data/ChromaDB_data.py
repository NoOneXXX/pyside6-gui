import os
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader


class VectorSearchService:
    def __init__(self, db_path="./chroma_storage"):
        # 1. 初始化持久化客户端（数据存本地文件夹）
        self.client = chromadb.PersistentClient(path=db_path)

        # 2. 初始化多模态模型（CLIP）- 用于同时处理文本和图片
        # 提示：第一次运行会下载约 600MB-1GB 的模型权重
        self.embedding_function = OpenCLIPEmbeddingFunction()
        self.data_loader = ImageLoader()

        # 3. 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name="keep_notes_collection",
            embedding_function=self.embedding_function,
            data_loader=self.data_loader
        )

    def add_note(self, doc_id, text, metadata):
        """添加纯文本笔记"""
        self.collection.add(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata]
        )

    def add_image(self, img_id, img_path, metadata):
        """添加图片"""
        self.collection.add(
            ids=[img_id],
            uris=[img_path],
            metadatas=[metadata]
        )

    def search(self, query_text, n_results=5):
        """搜索（支持用文字搜文字，或者用文字搜图片）"""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results


# --- 测试代码 ---
if __name__ == "__main__":
    service = VectorSearchService()

    # 模拟添加数据
    service.add_note("note_1", "这是关于PySide6绘图模糊的解决办法", {"type": "markdown"})
    # service.add_image("img_1", "C:/path/to/your/screenshot.jpg", {"type": "image"})

    # 搜索
    print("搜索结果:", service.search("绘图显示"))