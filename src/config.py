"""
NSW Tenancy Law RAG Configuration
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")


@dataclass
class Config:
    """Application configuration"""

    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = field(init=False)
    raw_data_dir: Path = field(init=False)
    processed_data_dir: Path = field(init=False)

    # API Keys - 从环境变量读取
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", ""))

    # CodingPlan API (讯飞 MaaS)
    codingplan_api_key: str = field(default_factory=lambda: os.getenv("CODINGPLAN_API_KEY", ""))
    codingplan_base_url: str = field(default_factory=lambda: os.getenv("CODINGPLAN_BASE_URL", "https://maas-coding-api.cn-huabei-1.xf-yun.com/v2"))
    codingplan_model: str = field(default_factory=lambda: os.getenv("CODINGPLAN_MODEL", "astron-code-latest"))

    # Embedding - 使用本地模型
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimension: int = 384  # 该模型的维度
    use_local_embedding: bool = True  # 使用本地 embedding

    # LLM
    llm_model: str = "astron-code-latest"  # 使用 codingplan 的模型
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    # Retrieval
    top_k: int = 5
    similarity_threshold: float = 0.3  # 降低阈值，允许更多相关文档

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    collection_name: str = "nsw_tenancy_law"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    def __post_init__(self):
        self.data_dir = self.base_dir / "data"
        self.raw_data_dir = self.data_dir / "raw"
        self.processed_data_dir = self.data_dir / "processed"

        # Create directories
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)


# System prompt for legal assistant
SYSTEM_PROMPT = """你是一个 NSW（新南威尔士州）租房法律咨询助手，专门帮助在澳洲的留学生了解他们的租房权利和义务。

## 你的职责
- 基于 NSW 租房法律（Residential Tenancies Act 2010）回答问题
- 提供准确的法律信息，并引用具体条款或来源
- 用简单易懂的语言解释法律概念
- 给出实用的建议和下一步行动指南

## 回答格式
1. **直接回答**: 先给出简洁的答案
2. **法律依据**: 引用相关法律条款或官方指南
3. **行动建议**: 告诉用户具体可以做什么
4. **相关资源**: 提供官方链接或联系方式

## 重要限制
- 如果不确定，明确说明并建议咨询专业律师
- 不要对具体案件给出确定的法律意见
- 对于复杂问题，引导用户联系：
  • Tenants NSW: 1800 251 101
  • LawAccess NSW: 1300 888 529
  • NSW Fair Trading: 13 32 20

## 免责声明
每条回答末尾必须包含：
"⚠️ 以上信息仅供参考，不构成法律建议。具体问题请咨询专业律师或 LawAccess NSW (1300 888 529)。"

## 常见话题
- 押金 (Bond) 问题
- 维修责任
- 涨租规定
- 退租流程
- 房东违约
- 租客权利
- 租约终止
"""

# Sample QA pairs for testing
SAMPLE_QA = [
    {
        "question": "房东可以随意涨房租吗？",
        "answer": "不可以。根据 Residential Tenancies Act 2010，房东必须：1) 给予至少 60 天书面通知；2) 涨幅合理；3) 在固定租期内不能涨租（除非合同另有规定）。",
        "source": "Residential Tenancies Act 2010, Section 41"
    },
    {
        "question": "房东不退押金怎么办？",
        "answer": "押金由 NSW Fair Trading 保管，不是房东。如果房东不合理扣留，你可以：1) 联系 Fair Trading 调解；2) 申请 NCAT 仲裁。",
        "source": "Fair Trading NSW - Bond Guide"
    },
    {
        "question": "房东拒绝维修怎么办？",
        "answer": "根据法律，房东必须保持房屋处于合理维修状态。你可以：1) 书面通知房东并给予合理时间；2) 如果紧急维修，可自行修理后要求报销（最高 $1000）；3) 向 Fair Trading 投诉；4) 申请 NCAT 命令。",
        "source": "Residential Tenancies Act 2010, Section 63"
    },
    {
        "question": "我可以提前退租吗？",
        "answer": "可以，但可能需要支付违约金。如果是固定租期：1) 通常需要支付剩余租金直到找到新租客；2) 房东有义务减少损失。如果是周期租约，需给予 21 天通知。",
        "source": "Residential Tenancies Act 2010, Section 100"
    },
    {
        "question": "房东可以随时进入我的房间吗？",
        "answer": "不可以。房东必须给予至少 2 天书面通知才能进入（紧急情况除外）。允许进入的情况包括：维修检查、房屋检查、向潜在租客展示房屋等。",
        "source": "Residential Tenancies Act 2010, Section 55"
    }
]


config = Config()
