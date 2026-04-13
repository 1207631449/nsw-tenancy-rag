"""
Embeddings - 生成文档向量
支持本地模型和 OpenAI API
"""

from typing import List, Optional
import numpy as np
from openai import OpenAI

from .config import config


class LocalEmbeddingGenerator:
    """使用本地 sentence-transformers 生成 embeddings"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.embedding_model
        self._model = None

    @property
    def model(self):
        """延迟加载模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Loading local embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "请安装 sentence-transformers: pip install sentence-transformers"
                )
        return self._model

    def generate(self, texts: List[str]) -> np.ndarray:
        """生成文本的 embedding 向量"""
        if not texts:
            return np.array([])

        embeddings = self.model.encode(texts, show_progress_bar=False)
        return np.array(embeddings)

    def generate_single(self, text: str) -> np.ndarray:
        """生成单个文本的 embedding"""
        embedding = self.model.encode([text], show_progress_bar=False)[0]
        return np.array(embedding)


class OpenAIEmbeddingGenerator:
    """使用 OpenAI 生成 embeddings"""

    def __init__(self, api_key: Optional[str] = None):
        client_kwargs = {"api_key": api_key or config.openai_api_key}
        if config.openai_base_url:
            client_kwargs["base_url"] = config.openai_base_url
        self.client = OpenAI(**client_kwargs)
        self.model = config.embedding_model
        self.dimension = config.embedding_dimension

    def generate(self, texts: List[str]) -> np.ndarray:
        """生成文本的 embedding 向量"""
        if not texts:
            return np.array([])

        # 批量处理
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            response = self.client.embeddings.create(
                model=self.model,
                input=batch
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return np.array(all_embeddings)

    def generate_single(self, text: str) -> np.ndarray:
        """生成单个文本的 embedding"""
        response = self.client.embeddings.create(
            model=self.model,
            input=[text]
        )
        return np.array(response.data[0].embedding)


class EmbeddingGenerator:
    """统一的 Embedding 生成器"""

    def __init__(self, api_key: Optional[str] = None):
        if config.use_local_embedding:
            self._generator = LocalEmbeddingGenerator()
        else:
            self._generator = OpenAIEmbeddingGenerator(api_key)
        self.dimension = config.embedding_dimension

    def generate(self, texts: List[str]) -> np.ndarray:
        """生成文本的 embedding 向量"""
        return self._generator.generate(texts)

    def generate_single(self, text: str) -> np.ndarray:
        """生成单个文本的 embedding"""
        return self._generator.generate_single(text)


class SimpleVectorStore:
    """简单的内存向量存储（用于 MVP）"""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vectors: np.ndarray = np.array([])
        self.documents: List[dict] = []

    def add(self, vectors: np.ndarray, documents: List[dict]):
        """添加向量和文档"""
        if len(self.vectors) == 0:
            self.vectors = vectors
        else:
            self.vectors = np.vstack([self.vectors, vectors])

        self.documents.extend(documents)

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[dict]:
        """搜索最相似的文档"""
        if len(self.vectors) == 0:
            return []

        # 计算余弦相似度
        query_vector = query_vector.reshape(1, -1)
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        normalized = self.vectors / (norms + 1e-10)
        query_norm = np.linalg.norm(query_vector)
        query_normalized = query_vector / (query_norm + 1e-10)

        similarities = np.dot(normalized, query_normalized.T).flatten()

        # 获取 top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "document": self.documents[idx],
                "score": float(similarities[idx])
            })

        return results

    def clear(self):
        """清空存储"""
        self.vectors = np.array([])
        self.documents = []


class QdrantVectorStore:
    """Qdrant 向量存储（生产环境）"""

    def __init__(self, collection_name: str = "nsw_tenancy_law", dimension: int = 384):
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        self.collection_name = collection_name
        self.dimension = dimension

        # 使用本地文件存储（无需 Docker）
        self.client = QdrantClient(path="./data/qdrant_storage")

        # 创建 collection（如果不存在）
        try:
            self.client.get_collection(collection_name)
            print(f"Loaded existing Qdrant collection: {collection_name}")
        except Exception:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE
                )
            )
            print(f"Created new Qdrant collection: {collection_name}")

    def add(self, vectors: np.ndarray, documents: List[dict]):
        """添加向量和文档"""
        from qdrant_client.models import PointStruct
        import uuid

        points = []
        for i, (vector, doc) in enumerate(zip(vectors, documents)):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vector.tolist(),
                payload=doc
            ))

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Indexed {len(points)} documents to Qdrant")

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[dict]:
        """搜索最相似的文档"""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=top_k
        )

        return [
            {
                "document": hit.payload,
                "score": hit.score
            }
            for hit in results
        ]

    def clear(self):
        """清空存储"""
        self.client.delete_collection(self.collection_name)
        from qdrant_client.models import Distance, VectorParams
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.dimension,
                distance=Distance.COSINE
            )
        )


class VectorStoreManager:
    """向量存储管理器"""

    def __init__(self, use_qdrant: bool = False):
        self.use_qdrant = use_qdrant
        self.embedding_generator = EmbeddingGenerator()

        if use_qdrant:
            self.store = QdrantVectorStore(
                collection_name=config.collection_name,
                dimension=config.embedding_dimension
            )
        else:
            self.store = SimpleVectorStore(dimension=config.embedding_dimension)

    def index_documents(self, documents: List[dict]):
        """索引文档"""
        texts = [doc["content"] for doc in documents]
        vectors = self.embedding_generator.generate(texts)
        self.store.add(vectors, documents)

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """搜索相关文档"""
        query_vector = self.embedding_generator.generate_single(query)
        return self.store.search(query_vector, top_k)

    def clear(self):
        """清空索引"""
        self.store.clear()
