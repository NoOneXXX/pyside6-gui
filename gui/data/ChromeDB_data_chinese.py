import os
import warnings
from pathlib import Path

import torch
import chromadb
# 引入嵌入函数
from chromadb.utils.embedding_functions import (
    OpenCLIPEmbeddingFunction,
    SentenceTransformerEmbeddingFunction
)
from chromadb.utils.data_loaders import ImageLoader

# ==================== 环境配置 ====================
os.environ["ANONYMIZED_TELEMETRY"] = "False"
# 抑制部分库的冗余警告
warnings.filterwarnings("ignore", category=UserWarning)


class VectorSearchService:
    def __init__(self, db_path: str = None):
        # 1. 自动检测硬件设备 (CUDA/CPU)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if db_path is None:
            db_path = Path(__file__).parent.absolute() / "chroma_storage"
        else:
            db_path = Path(db_path)
        db_path.mkdir(parents=True, exist_ok=True)

        # 2. 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=str(db_path),
            settings=chromadb.Settings(anonymized_telemetry=False)
        )

        # 3. 初始化【中文语义模型】用于文本 (使用 BGE 并在指定设备运行)
        # 该模型会自动下载到本地缓存
        self.text_ef = SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-small-zh-v1.5",
            device=self.device
        )

        # 4. 初始化【多模态模型】用于图片 (同步使用检测到的设备)
        self.image_ef = OpenCLIPEmbeddingFunction(device=self.device)
        self.image_loader = ImageLoader()

        # ---------------- 核心优化：创建/获取两个集合 ----------------
        # 文本集合：专门处理 Markdown 笔记、代码描述等
        self.text_col = self.client.get_or_create_collection(
            name="note_text_collection",
            embedding_function=self.text_ef,
            metadata={"hnsw:space": "cosine"}
        )

        # 图片集合：专门处理 UI 截图、图片笔记
        self.image_col = self.client.get_or_create_collection(
            name="note_image_collection",
            embedding_function=self.image_ef,
            data_loader=self.image_loader,
            metadata={"hnsw:space": "cosine"}
        )

        print(f"✅ 双引擎初始化成功。运行设备: {self.device.upper()}")

    def add_note(self, doc_id: str, text: str, metadata: dict = None):
        """添加纯文本笔记"""
        self.text_col.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata or {}]
        )
        print(f"📝 文本已索引: {doc_id}")

    def add_image(self, image_id: str, image_path: str, metadata: dict = None):
        """添加图片（双重索引策略）"""
        # A. 在图片引擎存入原始路径，用于图文匹配
        self.image_col.upsert(
            ids=[image_id],
            uris=[image_path],
            metadatas=[metadata or {"type": "image"}]
        )
        # B. 增强搜索：如果 metadata 里有文字描述，也同步存入文本引擎
        if metadata and "description" in metadata:
            self.text_col.upsert(
                ids=[f"img_desc_{image_id}"],
                documents=[metadata["description"]],
                metadatas=[{"ref_id": image_id, "type": "img_desc"}]
            )
        print(f"🖼️ 图片已索引: {image_id}")

    def search(self, query: str, n_results: int = 5):
        """
        智能路由搜索：
        - 如果输入是图片路径，执行图片相似度搜索
        - 如果输入是文字，执行语义搜索
        """
        is_image_query = query.lower().endswith(('.jpg', '.png', '.jpeg'))

        if is_image_query:
            print(f"🔍 正在执行【图片】语义搜索: {query}")
            return self.image_col.query(query_uris=[query], n_results=n_results)
        else:
            print(f"🔍 正在执行【文本】语义搜索: {query}")
            return self.text_col.query(query_texts=[query], n_results=n_results)


# ==================== 测试运行 ====================
if __name__ == "__main__":
    # 初始化服务
    service = VectorSearchService()

    # 1. 模拟添加笔记
    service.add_note("n1", "这是关于绘图模糊的解决办法", {"tags": "drawing"})
    service.add_note("n2", "这是关于python编程绘图的笔记", {"tags": "pyside6"})

    # 2. 测试文本检索
    # 在 BGE 模型下，“画画”和“绘图”会产生很高的相似度，即使字面上没有“画画”
    search_term = "画画"
    print(f"\n--- 正在检索关键词: {search_term} ---")

    results = service.search(search_term, n_results=2)

    if results and results['documents']:
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            print(f">> 匹配结果: {doc} | 标签: {meta.get('tags')}")
    else:
        print("未找到匹配内容。")