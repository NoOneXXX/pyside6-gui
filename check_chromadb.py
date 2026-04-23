"""
ChromaDB 数据库查看工具
用于检查数据库中的集合和数据
"""

import os
import sys
from pathlib import Path

# 设置环境变量
os.environ["ANONYMIZED_TELEMETRY"] = "False"

def check_chromadb():
    """检查 ChromaDB 数据库状态"""
    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        
        print("=" * 60)
        print("ChromaDB 数据库检查工具")
        print("=" * 60)
        print(f"ChromaDB 版本: {chromadb.__version__}")
        print()
        
        # 数据库路径
        db_path = Path(__file__).parent / "gui" / "data" / "chroma_storage"
        print(f"数据库路径: {db_path}")
        print(f"路径存在: {db_path.exists()}")
        print()
        
        if not db_path.exists():
            print("❌ 数据库目录不存在！")
            print("   请先运行程序创建数据库或添加一些笔记文件。")
            return
        
        # 初始化客户端
        client = chromadb.PersistentClient(
            path=str(db_path),
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 获取所有集合
        print("-" * 60)
        print("📁 集合列表:")
        print("-" * 60)
        
        try:
            collections = client.list_collections()
            if not collections:
                print("   没有集合")
            else:
                for collection_name in collections:
                    print(f"   • {collection_name}")
        except Exception as e:
            print(f"   获取集合列表失败: {e}")
        
        print()
        
        # 检查 notes_content 集合
        print("-" * 60)
        print("📄 notes_content 集合详情:")
        print("-" * 60)
        
        try:
            notes_collection = client.get_collection(name="notes_content")
            count = notes_collection.count()
            print(f"   文档数量: {count}")
            
            if count > 0:
                # 获取所有数据
                all_data = notes_collection.get()
                print(f"\n   存储的文档:")
                for i, (doc_id, metadata) in enumerate(zip(all_data['ids'], all_data['metadatas'])):
                    file_name = metadata.get('file_name', 'Unknown') if metadata else 'Unknown'
                    file_path = metadata.get('file_path', 'N/A') if metadata else 'N/A'
                    file_type = metadata.get('file_type', 'N/A') if metadata else 'N/A'
                    print(f"   {i+1}. {file_name}")
                    print(f"      ID: {doc_id}")
                    print(f"      路径: {file_path}")
                    print(f"      类型: {file_type}")
                    print()
            else:
                print("   集合为空，没有索引的文档")
                
        except Exception as e:
            print(f"   ❌ 获取 notes_content 集合失败: {e}")
        
        print()
        
        # 检查 notes_metadata 集合
        print("-" * 60)
        print("📋 notes_metadata 集合详情:")
        print("-" * 60)
        
        try:
            metadata_collection = client.get_collection(name="notes_metadata")
            count = metadata_collection.count()
            print(f"   文档数量: {count}")
            
            if count > 0:
                all_data = metadata_collection.get()
                print(f"\n   存储的元数据:")
                for i, (doc_id, metadata) in enumerate(zip(all_data['ids'], all_data['metadatas'])):
                    file_name = metadata.get('file_name', 'Unknown') if metadata else 'Unknown'
                    print(f"   {i+1}. {file_name}")
            else:
                print("   集合为空，没有索引的元数据")
                
        except Exception as e:
            print(f"   ❌ 获取 notes_metadata 集合失败: {e}")
        
        print()
        print("=" * 60)
        print("检查完成")
        print("=" * 60)
        
        # 测试搜索
        print("\n🔍 测试搜索功能:")
        test_query = input("   输入搜索关键词 (直接回车跳过): ").strip()
        
        if test_query:
            try:
                # 初始化嵌入函数
                device = "cuda" if __import__('torch').cuda.is_available() else "cpu"
                text_ef = SentenceTransformerEmbeddingFunction(
                    model_name="BAAI/bge-small-zh-v1.5",
                    device=device
                )
                
                # 重新获取集合并设置嵌入函数
                notes_collection = client.get_collection(
                    name="notes_content",
                    embedding_function=text_ef
                )
                
                results = notes_collection.query(
                    query_texts=[test_query],
                    n_results=5
                )
                
                print(f"\n   搜索结果:")
                if results['ids'] and results['ids'][0]:
                    for i, (doc_id, metadata, distance) in enumerate(zip(
                        results['ids'][0], 
                        results['metadatas'][0] if results['metadatas'] else [],
                        results['distances'][0] if results['distances'] else []
                    )):
                        file_name = metadata.get('file_name', 'Unknown') if metadata else 'Unknown'
                        score = 1 - distance if distance else 0
                        print(f"   {i+1}. {file_name} (相似度: {score:.2f})")
                else:
                    print("   没有找到匹配的结果")
                    
            except Exception as e:
                print(f"   ❌ 搜索失败: {e}")
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("   请确保已安装 ChromaDB: pip install chromadb")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_chromadb()
