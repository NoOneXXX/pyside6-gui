from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer


# 1. 加载 embedding 模型
model = SentenceTransformer("BAAI/bge-small-zh-v1.5")

# 2. 连接 Milvus
client = MilvusClient(uri="http://127.0.0.1:19530")

print("Milvus 连接成功")

collection_name = "note_embedding_demo"

# 3. 获取真实向量维度
test_vector = model.encode("测试文本").tolist()
dimension = len(test_vector)

print("向量维度：", dimension)

# 4. 删除旧 collection，方便重复测试
if client.has_collection(collection_name):
    client.drop_collection(collection_name)

# 5. 创建 collection
client.create_collection(
    collection_name=collection_name,
    dimension=dimension,
    metric_type="COSINE"
)

print("Collection 创建成功")


# 6. 原始文本数据
notes = [
    {
        "id": 1,
        "title": "Python 学习笔记",
        "content": "Python 可以用来开发 GUI、爬虫、AI 应用。"
    },
    {
        "id": 2,
        "title": "Milvus 学习笔记",
        "content": "Milvus 是一个向量数据库，适合做语义搜索、相似度搜索。"
    },
    {
        "id": 3,
        "title": "Java 学习笔记",
        "content": "Java 常用于后端服务开发，比如 Spring Boot 项目。"
    }
]

# 7. 文本自动转向量
data = []

for note in notes:
    # 建议标题 + 正文一起转向量
    text = note["title"] + "\n" + note["content"]

    vector = model.encode(text).tolist()

    data.append({
        "id": note["id"],
        "vector": vector,
        "title": note["title"],
        "content": note["content"]
    })

# 8. 插入数据
result = client.insert(
    collection_name=collection_name,
    data=data
)

print("插入结果：", result)

# 9. 关键：刷新数据
client.flush(collection_name)

# 10. 关键：加载 collection
client.load_collection(collection_name)

print("数据 flush/load 完成")


# 11. 先用 query 看看数据是否真的在里面
rows = client.query(
    collection_name=collection_name,
    filter="id >= 1",
    output_fields=["id", "title", "content"],
    limit=10
)

print("普通查询结果：")
for row in rows:
    print(row)


# 12. 用户搜索文本
query_text = "python"

# 13. 搜索文本也转向量
query_vector = model.encode(query_text).tolist()

# 14. 向量搜索
search_result = client.search(
    collection_name=collection_name,
    data=[query_vector],
    limit=3,
    output_fields=["id", "title", "content"],
    search_params={
        "metric_type": "COSINE",
        "params": {}
    }
)

print("向量搜索结果：")

print(search_result)

for hits in search_result:
    for hit in hits:
        print("相似度：", hit["distance"])
        print("标题：", hit["entity"]["title"])
        print("内容：", hit["entity"]["content"])
        print("-" * 50)