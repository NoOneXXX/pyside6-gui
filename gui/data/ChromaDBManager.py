"""
ChromaDBManager - 笔记向量数据库管理器

功能：
- 支持 Markdown 和 HTML 文件的向量索引
- 异步批量插入机制（队列满10条或5分钟触发）
- 中文语义搜索支持（使用 BGE 模型）
- 文件变更监听和自动重新索引

设计模式：
- 单例模式：确保全局唯一的数据库连接
- 生产者-消费者模式：异步处理索引队列
- 定时器机制：定期刷新队列
"""

import os
import re
import time
import warnings
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from queue import Queue, Empty

import torch
import chromadb
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction,
    OpenCLIPEmbeddingFunction
)
from chromadb.utils.data_loaders import ImageLoader
from bs4 import BeautifulSoup

# ==================== 环境配置 ====================
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# 使用 Hugging Face 镜像源加速下载
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", module="chromadb.telemetry")


@dataclass
class IndexTask:
    """索引任务数据类"""
    file_path: str
    file_type: str  # 'markdown' 或 'html'
    action: str = 'update'  # 'update' 或 'delete'
    timestamp: float = field(default_factory=time.time)


class ChromaDBManager:
    """
    ChromaDB 管理器 - 处理笔记文件的向量索引
    
    特性：
    1. 双集合设计：文本集合（笔记内容）+ 元数据集合（文件信息）
    2. 异步批量插入：队列满10条或5分钟自动触发
    3. 中文语义搜索：基于 BGE 中文嵌入模型
    4. 增量更新：支持文件变更监听
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # 配置常量
    BATCH_SIZE = 10  # 批量插入阈值
    FLUSH_INTERVAL = 300  # 5分钟 = 300秒
    MAX_QUEUE_SIZE = 1000  # 最大队列容量
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None, note_db=None):
        """
        初始化 ChromaDB 管理器

        Args:
            db_path: 数据库存储路径，默认在 chroma_storage 目录
            note_db: NoteDB 实例，用于读取索引队列
        """
        if self._initialized:
            return

        try:
            self.note_db = note_db

            # 1. 自动检测硬件设备
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

            # 2. 设置数据库路径
            if db_path is None:
                db_path = Path(__file__).parent.absolute() / "chroma_storage"
            else:
                db_path = Path(db_path)
            db_path.mkdir(parents=True, exist_ok=True)
            self.db_path = str(db_path)

            # 3. 初始化 ChromaDB 客户端
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=chromadb.Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # 4. 初始化中文语义模型 (BGE) 用于文本
            self.text_ef = SentenceTransformerEmbeddingFunction(
                model_name="BAAI/bge-small-zh-v1.5",
                device=self.device
            )

            # 5. 图片模型按需初始化，避免纯文本搜索时加载 OpenCLIP 造成卡顿
            self.image_ef = None
            self.image_loader = None
            self.image_collection = None

            # 6. 创建/获取集合
            # 文本集合：存储笔记内容的向量
            self.notes_collection = self.client.get_or_create_collection(
                name="notes_content",
                embedding_function=self.text_ef,
                metadata={
                    "hnsw:space": "cosine",
                    "description": "笔记内容向量集合"
                }
            )

            # 元数据集合：存储文件元数据（非向量索引）
            self.metadata_collection = self.client.get_or_create_collection(
                name="notes_metadata",
                embedding_function=self.text_ef,
                metadata={
                    "hnsw:space": "cosine",
                    "description": "笔记元数据集合"
                }
            )

            # 6. 初始化异步队列
            self._task_queue = Queue(maxsize=self.MAX_QUEUE_SIZE)
            self._queue_lock = threading.Lock()
            self._flush_timer = None
            self._stop_event = threading.Event()
            self._worker_thread = None
            self._is_running = False

            # 7. 统计信息
            self._stats = {
                "total_indexed": 0,
                "total_deleted": 0,
                "last_flush_time": None,
                "errors": []
            }

            self._initialized = True
            print(f"✅ ChromaDBManager 初始化成功 | 设备: {self.device.upper()} | 路径: {self.db_path}")

        except Exception as e:
            print(f"❌ ChromaDBManager 初始化失败: {e}")
            # 重置初始化标志，允许下次重试
            self._initialized = False
            raise
    
    # ==================== 队列管理 ====================
    
    def start(self):
        """启动异步处理线程"""
        if self._is_running:
            return
            
        self._is_running = True
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._worker_thread.start()
        self._start_flush_timer()
        print("🚀 异步索引服务已启动")
    
    def stop(self):
        """停止异步处理线程"""
        if not self._is_running:
            return
            
        self._is_running = False
        self._stop_event.set()
        
        # 取消定时器
        if self._flush_timer:
            self._flush_timer.cancel()
        
        # 最后一次刷新队列
        self._flush_queue()
        
        # 等待工作线程结束
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
        
        print("🛑 异步索引服务已停止")
    
    def _start_flush_timer(self):
        """启动定时刷新定时器"""
        def timer_callback():
            if self._is_running and not self._stop_event.is_set():
                self._check_and_flush()
                self._start_flush_timer()
        
        self._flush_timer = threading.Timer(self.FLUSH_INTERVAL, timer_callback)
        self._flush_timer.daemon = True
        self._flush_timer.start()
    
    def _check_and_flush(self):
        """检查队列并触发刷新（定时调用）"""
        queue_size = self.get_queue_size()
        if queue_size > 0:
            print(f"⏰ 定时触发刷新，队列大小: {queue_size}")
            self._flush_queue()
    
    def get_queue_size(self) -> int:
        """获取当前队列大小"""
        with self._queue_lock:
            return self._task_queue.qsize()
    
    def add_to_queue(self, file_path: str, file_type: str = None, action: str = 'update') -> bool:
        """
        添加文件到索引队列
        
        Args:
            file_path: 文件路径
            file_type: 文件类型 ('markdown' 或 'html')，自动检测
            action: 操作类型 ('update' 或 'delete')
        
        Returns:
            bool: 是否成功添加
        """
        # 自动检测文件类型
        if file_type is None:
            file_type = self._detect_file_type(file_path)
        
        task = IndexTask(
            file_path=file_path,
            file_type=file_type,
            action=action
        )
        
        try:
            with self._queue_lock:
                self._task_queue.put(task, block=False)
            
            # 检查是否达到批量阈值
            if self.get_queue_size() >= self.BATCH_SIZE:
                print(f"📦 队列达到阈值 ({self.BATCH_SIZE})，触发批量插入")
                threading.Thread(target=self._flush_queue, daemon=True).start()
            
            return True
        except Exception as e:
            print(f"❌ 添加任务到队列失败: {e}")
            self._stats["errors"].append((time.time(), str(e)))
            return False
    
    def _detect_file_type(self, file_path: str) -> str:
        """根据文件路径检测文件类型"""
        ext = Path(file_path).suffix.lower()
        if ext in ['.md', '.markdown']:
            return 'markdown'
        elif ext in ['.html', '.htm']:
            return 'html'
        else:
            return 'unknown'
    
    def _process_loop(self):
        """工作线程主循环"""
        while not self._stop_event.is_set():
            try:
                # 等待任务，超时1秒
                task = self._task_queue.get(timeout=1)
                self._process_single_task(task)
            except Empty:
                continue
            except Exception as e:
                print(f"❌ 处理任务出错: {e}")
                self._stats["errors"].append((time.time(), str(e)))
    
    def _process_single_task(self, task: IndexTask):
        """处理单个任务"""
        try:
            if task.action == 'delete':
                self._delete_from_index(task.file_path)
            else:
                self._index_file(task.file_path, task.file_type)
        except Exception as e:
            print(f"❌ 处理文件失败 {task.file_path}: {e}")
            self._stats["errors"].append((time.time(), str(e)))
    
    def _flush_queue(self):
        """刷新队列，批量处理所有待处理任务"""
        tasks = []
        with self._queue_lock:
            while not self._task_queue.empty() and len(tasks) < self.BATCH_SIZE * 2:
                try:
                    tasks.append(self._task_queue.get(block=False))
                except Empty:
                    break
        
        if not tasks:
            return
        
        print(f"🔄 开始批量处理 {len(tasks)} 个任务...")
        
        # 按文件路径去重，保留最新的
        unique_tasks = {}
        for task in tasks:
            unique_tasks[task.file_path] = task
        
        # 批量处理
        update_tasks = [t for t in unique_tasks.values() if t.action == 'update']
        delete_tasks = [t for t in unique_tasks.values() if t.action == 'delete']
        
        # 批量删除
        if delete_tasks:
            self._batch_delete([t.file_path for t in delete_tasks])
        
        # 批量索引
        if update_tasks:
            self._batch_index(update_tasks)
        
        self._stats["last_flush_time"] = datetime.now()
        print(f"✅ 批量处理完成 | 更新: {len(update_tasks)} | 删除: {len(delete_tasks)}")
    
    # ==================== 文件索引核心方法 ====================

    def _ensure_image_collection(self):
        """按需初始化图片集合和 OpenCLIP 模型。"""
        if self.image_collection is not None:
            return

        self.image_ef = OpenCLIPEmbeddingFunction(device=self.device)
        self.image_loader = ImageLoader()
        self.image_collection = self.client.get_or_create_collection(
            name="notes_images",
            embedding_function=self.image_ef,
            data_loader=self.image_loader,
            metadata={
                "hnsw:space": "cosine",
                "description": "图片向量集合"
            }
        )
    
    def _index_file(self, file_path: str, file_type: str):
        """索引单个文件"""
        if not os.path.exists(file_path):
            print(f"⚠️ 文件不存在: {file_path}")
            return

        # 读取文件内容
        content = self._read_file_content(file_path, file_type)
        if not content or not content.strip():
            print(f"⚠️ 文件内容为空: {file_path}")
            return

        # 提取纯文本（去除HTML标签等）
        plain_text = self._extract_plain_text(content, file_type)

        # 生成文档ID（基于文件路径的哈希）
        doc_id = self._generate_doc_id(file_path)

        # 准备元数据
        stat = os.stat(file_path)
        metadata = {
            "file_path": file_path,
            "file_type": file_type,
            "file_name": Path(file_path).name,
            "modified_time": stat.st_mtime,
            "indexed_time": time.time(),
            "content_length": len(plain_text)
        }

        # 插入到集合
        self.notes_collection.upsert(
            ids=[doc_id],
            documents=[plain_text],
            metadatas=[metadata]
        )

        # 同时索引元数据（用于文件名搜索）
        meta_doc_id = f"meta_{doc_id}"
        self.metadata_collection.upsert(
            ids=[meta_doc_id],
            documents=[metadata["file_name"]],
            metadatas=[metadata]
        )

        # 提取并索引图片
        if file_type == 'markdown':
            self._index_images_from_markdown(file_path, content)

        self._stats["total_indexed"] += 1
        print(f"📝 已索引: {Path(file_path).name}")

    def _index_images_from_markdown(self, md_file_path: str, content: str):
        """从 Markdown 文件中提取并索引图片"""
        import re

        # 查找 Markdown 图片引用 ![alt](path)
        md_images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        # 查找 HTML 图片标签 <img src="path">
        html_images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)

        base_dir = os.path.dirname(md_file_path)

        # 处理 Markdown 格式图片
        for alt_text, img_path in md_images:
            self._index_single_image(img_path, base_dir, md_file_path, alt_text)

        # 处理 HTML 格式图片
        for img_path in html_images:
            self._index_single_image(img_path, base_dir, md_file_path, "")

    def _index_single_image(self, img_path: str, base_dir: str, source_file: str, alt_text: str = ""):
        """索引单个图片"""
        # 转换为绝对路径
        if not os.path.isabs(img_path):
            img_path = os.path.normpath(os.path.join(base_dir, img_path))

        # 检查图片是否存在
        if not os.path.exists(img_path):
            return

        # 检查是否是支持的图片格式
        ext = os.path.splitext(img_path)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return

        try:
            self._ensure_image_collection()

            # 生成图片ID
            img_id = self._generate_doc_id(img_path)

            # 准备元数据
            metadata = {
                "image_path": img_path,
                "source_file": source_file,
                "alt_text": alt_text,
                "indexed_time": time.time()
            }

            # 插入到图片集合（使用 CLIP 模型自动生成嵌入）
            self.image_collection.upsert(
                ids=[img_id],
                uris=[img_path],
                metadatas=[metadata]
            )

            print(f"🖼️ 已索引图片: {Path(img_path).name}")

        except Exception as e:
            print(f"❌ 索引图片失败 {img_path}: {e}")
    
    def _batch_index(self, tasks: List[IndexTask]):
        """批量索引文件"""
        ids = []
        documents = []
        metadatas = []
        meta_ids = []
        meta_documents = []
        meta_metadatas = []
        
        for task in tasks:
            try:
                if not os.path.exists(task.file_path):
                    continue
                
                content = self._read_file_content(task.file_path, task.file_type)
                if not content or not content.strip():
                    continue
                
                plain_text = self._extract_plain_text(content, task.file_type)
                doc_id = self._generate_doc_id(task.file_path)
                stat = os.stat(task.file_path)
                
                metadata = {
                    "file_path": task.file_path,
                    "file_type": task.file_type,
                    "file_name": Path(task.file_path).name,
                    "modified_time": stat.st_mtime,
                    "indexed_time": time.time(),
                    "content_length": len(plain_text)
                }
                
                ids.append(doc_id)
                documents.append(plain_text)
                metadatas.append(metadata)
                
                meta_ids.append(f"meta_{doc_id}")
                meta_documents.append(metadata["file_name"])
                meta_metadatas.append(metadata)
                
                self._stats["total_indexed"] += 1
                
            except Exception as e:
                print(f"❌ 索引文件失败 {task.file_path}: {e}")
                self._stats["errors"].append((time.time(), str(e)))
        
        # 批量插入
        if ids:
            try:
                self.notes_collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                self.metadata_collection.upsert(
                    ids=meta_ids,
                    documents=meta_documents,
                    metadatas=meta_metadatas
                )
            except Exception as e:
                print(f"❌ 批量插入失败: {e}")
                self._stats["errors"].append((time.time(), str(e)))
    
    def _delete_from_index(self, file_path: str):
        """从索引中删除文件"""
        doc_id = self._generate_doc_id(file_path)
        try:
            self.notes_collection.delete(ids=[doc_id])
            self.metadata_collection.delete(ids=[f"meta_{doc_id}"])
            self._stats["total_deleted"] += 1
            print(f"🗑️ 已删除索引: {Path(file_path).name}")
        except Exception as e:
            print(f"❌ 删除索引失败: {e}")
    
    def _batch_delete(self, file_paths: List[str]):
        """批量删除索引"""
        ids = [self._generate_doc_id(fp) for fp in file_paths]
        meta_ids = [f"meta_{doc_id}" for doc_id in ids]
        try:
            self.notes_collection.delete(ids=ids)
            self.metadata_collection.delete(ids=meta_ids)
            self._stats["total_deleted"] += len(file_paths)
            print(f"🗑️ 批量删除 {len(file_paths)} 个索引")
        except Exception as e:
            print(f"❌ 批量删除失败: {e}")
    
    # ==================== 文件内容处理 ====================
    
    def _read_file_content(self, file_path: str, file_type: str) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except Exception as e:
                print(f"❌ 读取文件失败 {file_path}: {e}")
                return ""
        except Exception as e:
            print(f"❌ 读取文件失败 {file_path}: {e}")
            return ""
    
    def _extract_plain_text(self, content: str, file_type: str) -> str:
        """从内容中提取纯文本"""
        if file_type == 'html':
            # 使用 BeautifulSoup 去除 HTML 标签
            soup = BeautifulSoup(content, 'html.parser')
            # 移除 script 和 style 标签
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
        elif file_type == 'markdown':
            # 简单的 Markdown 标签去除
            text = self._strip_markdown(content)
        else:
            text = content
        
        # 清理空白字符
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return '\n'.join(chunk for chunk in chunks if chunk)
    
    def _strip_markdown(self, text: str) -> str:
        """去除 Markdown 标记"""
        # 去除代码块
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # 去除标题标记
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # 去除强调标记
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # 去除链接和图片
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # 去除列表标记
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # 去除引用标记
        text = re.sub(r'^\s*>\s+', '', text, flags=re.MULTILINE)
        
        # 去除水平线
        text = re.sub(r'^\s*[-=]{3,}\s*$', '', text, flags=re.MULTILINE)
        
        return text
    
    def _generate_doc_id(self, file_path: str) -> str:
        """基于文件路径生成文档ID"""
        import hashlib
        return hashlib.md5(file_path.encode('utf-8')).hexdigest()
    
    # ==================== 搜索功能 ====================
    
    def search(self, query: str, n_results: int = 10, 
               file_type: str = None, 
               search_in_content: bool = True,
               search_in_filename: bool = True,
               search_images: bool = True) -> Dict:
        """
        搜索笔记
        
        Args:
            query: 搜索关键词
            n_results: 返回结果数量
            file_type: 过滤文件类型 ('markdown', 'html', None表示全部)
            search_in_content: 是否在内容中搜索
            search_in_filename: 是否在文件名中搜索
            search_images: 是否在图片集合中搜索
        
        Returns:
            搜索结果字典
        """
        results = {
            "content_results": [],
            "filename_results": [],
            "image_results": [],
            "total_results": 0
        }
        
        # 在内容中搜索
        if search_in_content:
            try:
                where_filter = {"file_type": file_type} if file_type else None
                content_results = self.notes_collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter
                )
                results["content_results"] = self._format_results(content_results)
            except Exception as e:
                print(f"❌ 内容搜索失败: {e}")
        
        # 在文件名中搜索
        if search_in_filename:
            try:
                where_filter = {"file_type": file_type} if file_type else None
                filename_results = self.metadata_collection.query(
                    query_texts=[query],
                    n_results=min(n_results, 5),
                    where=where_filter
                )
                results["filename_results"] = self._format_results(filename_results)
            except Exception as e:
                print(f"❌ 文件名搜索失败: {e}")
        
        # 在图片中搜索（使用 CLIP 模型）
        if search_images:
            try:
                self._ensure_image_collection()
                image_results = self.image_collection.query(
                    query_texts=[query],
                    n_results=n_results
                )
                results["image_results"] = self._format_image_results(image_results)
            except Exception as e:
                print(f"❌ 图片搜索失败: {e}")

        results["total_results"] = len(results["content_results"]) + len(results["filename_results"]) + len(results.get("image_results", []))
        return results

    def _format_image_results(self, raw_results: Dict) -> List[Dict]:
        """格式化图片搜索结果"""
        formatted = []
        if not raw_results or not raw_results.get('ids'):
            return formatted

        ids = raw_results['ids'][0] if raw_results['ids'] else []
        uris = raw_results.get('uris', [[]])[0] if raw_results.get('uris') else []
        metadatas = raw_results['metadatas'][0] if raw_results.get('metadatas') else []
        distances = raw_results['distances'][0] if raw_results.get('distances') else []

        for i in range(len(ids)):
            formatted.append({
                "id": ids[i],
                "image_path": uris[i] if i < len(uris) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "score": 1 - distances[i] if i < len(distances) else 0,
                "type": "image"
            })

        return formatted
    
    def _format_results(self, raw_results: Dict) -> List[Dict]:
        """格式化搜索结果"""
        formatted = []
        if not raw_results or not raw_results.get('ids'):
            return formatted
        
        ids = raw_results['ids'][0] if raw_results['ids'] else []
        documents = raw_results['documents'][0] if raw_results.get('documents') else []
        metadatas = raw_results['metadatas'][0] if raw_results.get('metadatas') else []
        distances = raw_results['distances'][0] if raw_results.get('distances') else []
        
        for i in range(len(ids)):
            formatted.append({
                "id": ids[i],
                "document": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "score": 1 - distances[i] if i < len(distances) else 0  # 转换为相似度分数
            })
        
        return formatted
    
    # ==================== 与 NoteDB 集成 ====================
    
    def sync_from_note_db(self):
        """从 NoteDB 的索引队列同步待处理任务"""
        if self.note_db is None:
            print("⚠️ NoteDB 未配置，无法同步")
            return
        
        try:
            # 获取队列大小
            queue_size = self.note_db.get_queue_size()
            if queue_size == 0:
                return
            
            print(f"🔄 从 NoteDB 同步 {queue_size} 个待处理任务...")
            
            # 读取队列中的所有任务
            cursor = self.note_db.conn.execute(
                'SELECT rel_path, action FROM indexing_queue ORDER BY timestamp'
            )
            tasks = cursor.fetchall()
            
            # 添加到本地队列
            for rel_path, action in tasks:
                self.add_to_queue(rel_path, action=action or 'update')
            
            # 清空 NoteDB 队列
            self.note_db.conn.execute('DELETE FROM indexing_queue')
            self.note_db.conn.commit()
            
            print(f"✅ 已同步 {len(tasks)} 个任务到本地队列")
            
        except Exception as e:
            print(f"❌ 同步 NoteDB 失败: {e}")
    
    # ==================== 统计和管理 ====================
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "queue_size": self.get_queue_size(),
            "total_indexed": self._stats["total_indexed"],
            "total_deleted": self._stats["total_deleted"],
            "last_flush_time": self._stats["last_flush_time"],
            "error_count": len(self._stats["errors"]),
            "recent_errors": self._stats["errors"][-5:] if self._stats["errors"] else []
        }
    
    def get_collection_stats(self) -> Dict:
        """获取集合统计信息"""
        try:
            notes_count = self.notes_collection.count()
            metadata_count = self.metadata_collection.count()
            return {
                "notes_collection_count": notes_count,
                "metadata_collection_count": metadata_count,
                "total_vectors": notes_count + metadata_count
            }
        except Exception as e:
            return {"error": str(e)}
    
    def reset_collection(self):
        """重置集合（清空所有数据）"""
        try:
            self.client.delete_collection("notes_content")
            self.client.delete_collection("notes_metadata")
            
            # 重新创建
            self.notes_collection = self.client.get_or_create_collection(
                name="notes_content",
                embedding_function=self.text_ef,
                metadata={"hnsw:space": "cosine"}
            )
            self.metadata_collection = self.client.get_or_create_collection(
                name="notes_metadata",
                embedding_function=self.text_ef,
                metadata={"hnsw:space": "cosine"}
            )
            
            self._stats["total_indexed"] = 0
            self._stats["total_deleted"] = 0
            print("✅ 集合已重置")
        except Exception as e:
            print(f"❌ 重置集合失败: {e}")


# ==================== 便捷函数 ====================

def get_chroma_manager(db_path: str = None, note_db=None) -> ChromaDBManager:
    """获取 ChromaDBManager 单例实例"""
    return ChromaDBManager(db_path=db_path, note_db=note_db)


# ==================== 测试运行 ====================
if __name__ == "__main__":
    # 初始化管理器
    manager = get_chroma_manager()
    
    # 启动服务
    manager.start()
    
    # 测试文件路径（请根据实际情况修改）
    test_md_path = "test_document.md"
    test_html_path = "test_document.html"
    
    # 创建测试文件

    
    # 添加文件到队列
    manager.add_to_queue("test_document.md", 'markdown')
    manager.add_to_queue("test_document1.md", 'markdown')
    manager.add_to_queue("test_document3.md", 'markdown')
    
    # 等待处理
    time.sleep(2)
    
    # 手动触发刷新
    manager._flush_queue()
    
    # 测试搜索
    print("\n--- 搜索测试 ---")
    results = manager.search("网卡", n_results=5)
    print(f"找到 {results['total_results']} 个结果")
    
    for result in results['content_results']:
        print(f"  - {result['metadata'].get('file_name', 'Unknown')} (相似度: {result['score']:.2f})")
    
    # 打印统计
    print("\n--- 统计信息 ---")
    print(manager.get_stats())
    print(manager.get_collection_stats())
    
    # 停止服务
    manager.stop()

