"""
RAG Pipeline - 主流程
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .config import config, SYSTEM_PROMPT
from .document_processor import DocumentChunk, SAMPLE_DOCUMENTS, create_sample_data
from .embeddings import VectorStoreManager
from .llm_client import LLMClient


@dataclass
class RAGResponse:
    """RAG 响应"""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float


class ConversationHistory:
    """对话历史管理"""

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.history: List[Dict[str, str]] = []

    def add(self, role: str, content: str):
        """添加对话"""
        self.history.append({"role": role, "content": content})
        # 保持历史长度
        if len(self.history) > self.max_turns * 2:
            self.history = self.history[-self.max_turns * 2:]

    def get_context(self, last_n: int = 3) -> str:
        """获取最近 n 轮对话作为上下文"""
        if not self.history:
            return ""

        recent = self.history[-last_n * 2:] if len(self.history) >= last_n * 2 else self.history
        parts = []
        for msg in recent:
            role_cn = "用户" if msg["role"] == "user" else "助手"
            parts.append(f"{role_cn}: {msg['content']}")

        return "\n".join(parts)

    def clear(self):
        """清空历史"""
        self.history = []


class RAGPipeline:
    """RAG 主流程"""

    def __init__(self, use_sample_data: bool = True, use_qdrant: bool = False):
        self.vector_store = VectorStoreManager(use_qdrant=use_qdrant)
        self.llm_client = LLMClient()
        self.conversation = ConversationHistory()

        if use_sample_data:
            self._load_sample_data()

    def _load_sample_data(self):
        """加载示例数据"""
        documents = [
            {
                "id": doc["id"],
                "content": doc["content"],
                **doc["metadata"]
            }
            for doc in SAMPLE_DOCUMENTS
        ]
        self.vector_store.index_documents(documents)
        print(f"Loaded {len(documents)} sample documents")

    def index_documents(self, documents: List[Dict]):
        """索引自定义文档"""
        formatted_docs = [
            {
                "id": doc.get("id", f"doc_{i}"),
                "content": doc["content"],
                **doc.get("metadata", {})
            }
            for i, doc in enumerate(documents)
        ]
        self.vector_store.index_documents(formatted_docs)
        print(f"Indexed {len(formatted_docs)} documents")

    def query(
        self,
        question: str,
        top_k: int = 5,
        include_sources: bool = True,
        use_history: bool = True
    ) -> RAGResponse:
        """处理用户问题"""
        # 1. 检索相关文档
        search_results = self.vector_store.search(question, top_k=top_k)

        if not search_results:
            return RAGResponse(
                answer="抱歉，我没有找到相关的法律信息。建议您联系 Tenants NSW (1800 251 101) 或 LawAccess NSW (1300 888 529) 获取帮助。",
                sources=[],
                confidence=0.0
            )

        # 2. 构建上下文
        context_parts = []
        sources = []

        for result in search_results:
            doc = result["document"]
            score = result["score"]

            if score >= config.similarity_threshold:
                context_parts.append(f"【{doc.get('source', 'Unknown')}】\n{doc['content']}")
                sources.append({
                    "source": doc.get("source", "Unknown"),
                    "section": doc.get("section", ""),
                    "url": doc.get("url", ""),
                    "relevance": score
                })

        if not context_parts:
            return RAGResponse(
                answer="抱歉，我没有找到足够相关的信息。建议您联系 Tenants NSW (1800 251 101) 获取专业帮助。",
                sources=[],
                confidence=0.0
            )

        context = "\n\n---\n\n".join(context_parts)

        # 3. 获取对话历史
        history_context = ""
        if use_history and self.conversation.history:
            history_context = f"\n\n【对话历史】\n{self.conversation.get_context(last_n=2)}\n"

        # 4. 生成回答
        full_context = f"{history_context}\n【参考资料】\n{context}" if history_context else context
        answer = self.llm_client.generate_answer(question, full_context)

        # 5. 保存对话历史
        self.conversation.add("user", question)
        self.conversation.add("assistant", answer)

        # 6. 计算置信度
        confidence = sum(s["relevance"] for s in sources) / len(sources) if sources else 0.0

        return RAGResponse(
            answer=answer,
            sources=sources if include_sources else [],
            confidence=confidence
        )

    def chat(self, message: str, history: List[Dict] = None) -> str:
        """聊天接口（用于 Gradio）"""
        # 如果有外部历史，先加载
        if history:
            self.conversation.clear()
            for h in history:
                self.conversation.add(h.get("role", "user"), h.get("content", ""))

        response = self.query(message)
        return response.answer

    def clear_history(self):
        """清空对话历史"""
        self.conversation.clear()


def create_rag_pipeline(use_qdrant: bool = False) -> RAGPipeline:
    """创建 RAG pipeline 实例"""
    return RAGPipeline(use_sample_data=True, use_qdrant=use_qdrant)


if __name__ == "__main__":
    # 测试
    pipeline = create_rag_pipeline()

    test_questions = [
        "房东可以随意涨房租吗？",
        "房东不退押金怎么办？",
        "房东拒绝维修怎么办？",
    ]

    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"问题: {question}")
        print(f"{'='*60}")

        response = pipeline.query(question)

        print(f"\n回答:\n{response.answer}")
        print(f"\n置信度: {response.confidence:.2f}")

        if response.sources:
            print("\n来源:")
            for src in response.sources:
                print(f"  - {src['source']} {src.get('section', '')} (相关性: {src['relevance']:.2f})")
