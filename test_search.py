"""
测试 ChromaDB 搜索功能
"""
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from gui.data.ChromaDBManager import get_chroma_manager

manager = get_chroma_manager()
results = manager.search('网卡', n_results=10)

print("Content results count:", len(results.get('content_results', [])))
print("Filename results count:", len(results.get('filename_results', [])))

print("\nContent results paths:")
for r in results.get('content_results', []):
    metadata = r.get('metadata', {})
    file_path = metadata.get('file_path', 'N/A')
    score = r.get('score', 0)
    print(f"  - {file_path} (score: {score:.2f})")

print("\nFilename results paths:")
for r in results.get('filename_results', []):
    metadata = r.get('metadata', {})
    file_path = metadata.get('file_path', 'N/A')
    score = r.get('score', 0)
    print(f"  - {file_path} (score: {score:.2f})")
