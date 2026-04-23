import os
import warnings
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader

# ==================== 全局抑制警告 ====================
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 抑制 ChromaDB 内部的 telemetry 警告
warnings.filterwarnings("ignore", module="chromadb.telemetry")

class VectorSearchService:
    def __init__(self, db_path: str = None):
        # 使用绝对路径，避免权限问题
        if db_path is None:
            base_dir = Path(__file__).parent.absolute()
            db_path = base_dir / "chroma_storage"
        else:
            db_path = Path(db_path)

        db_path.mkdir(parents=True, exist_ok=True)

        # 初始化客户端（双重关闭遥测）
        self.client = chromadb.PersistentClient(
            path=str(db_path),
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 初始化 CLIP 多模态模型
        self.embedding_function = OpenCLIPEmbeddingFunction()
        self.data_loader = ImageLoader()

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name="keep_notes_collection",
            embedding_function=self.embedding_function,
            data_loader=self.data_loader,
            metadata={"hnsw:space": "cosine"}   # 推荐用于图片相似度
        )

        print(f"✅ ChromaDB 初始化成功，存储路径: {db_path}")

    def add_note(self, doc_id: str, text: str, metadata: dict = None):
        """添加文本笔记（使用 upsert 防止重复ID报错）"""
        if metadata is None:
            metadata = {}

        self.collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata]
        )
        print(f"已添加/更新笔记: {doc_id}")

    def add_image(self, image_id: str, image_path: str, metadata: dict = None):
        """添加图片（推荐用于你的大模型图片搜索）"""
        if metadata is None:
            metadata = {"type": "image"}

        self.collection.upsert(
            ids=[image_id],
            uris=[image_path],           # 直接传图片路径
            metadatas=[metadata]
        )
        print(f"已添加图片: {image_id} -> {image_path}")

    def search(self, query: str, n_results: int = 5):
        """支持文本或图片搜索"""
        try:
            results = self.collection.query(
                query_texts=[query] if isinstance(query, str) else None,
                query_uris=[query] if isinstance(query, str) and query.endswith(('.jpg', '.png', '.jpeg')) else None,
                n_results=n_results
            )
            return results
        except Exception as e:
            print(f"搜索出错: {e}")
            return None


if __name__ == "__main__":
    service = VectorSearchService()

    # 测试添加文本
    service.add_note(
        doc_id="note_1",
        text="这是关于绘图模糊的解决办法",
        metadata={"type": "markdown", "tags": "绘画"}
    )
    service.add_note(
        doc_id="note_2",
        text="这是关于python绘图模糊的解决办法",
        metadata={"type": "markdown", "tags": "pyside6"}
    )

    # 测试搜索
    print("\n搜索结果:")
    print(service.search("编程", n_results=3))