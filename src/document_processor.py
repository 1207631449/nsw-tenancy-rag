"""
Document Processor - 处理法律文档
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from .config import config


@dataclass
class DocumentChunk:
    """文档块"""
    id: str
    content: str
    metadata: Dict[str, Any]
    source: str
    section: str = ""
    title: str = ""


class DocumentProcessor:
    """处理法律文档，切分成合适的块"""

    def __init__(self):
        self.chunk_size = config.chunk_size
        self.chunk_overlap = config.chunk_overlap

    def process_legislation(self, text: str, source: str) -> List[DocumentChunk]:
        """
        处理法律条文 - 按 Section 切分
        """
        chunks = []

        # 匹配 Section 模式
        section_pattern = r'(\d+[A-Z]?\.\s+[A-Z][^\.]+(?:\.[^\.]+)*)'

        sections = re.split(section_pattern, text)

        current_section = ""
        current_title = ""

        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                section_num = sections[i].strip()
                content = sections[i + 1].strip()

                # 提取 section 编号
                match = re.match(r'(\d+[A-Z]?)', section_num)
                if match:
                    current_section = f"Section {match.group(1)}"

                # 提取标题
                title_match = re.search(r'\d+[A-Z]?\.\s+([A-Z][^\.]+)', section_num)
                if title_match:
                    current_title = title_match.group(1).strip()

                chunk = DocumentChunk(
                    id=f"{source}_{current_section}",
                    content=f"{section_num}\n\n{content}",
                    metadata={
                        "source": source,
                        "section": current_section,
                        "title": current_title,
                        "type": "legislation"
                    },
                    source=source,
                    section=current_section,
                    title=current_title
                )
                chunks.append(chunk)

        return chunks

    def process_guide(self, text: str, source: str, url: str = "") -> List[DocumentChunk]:
        """
        处理官方指南 - 按段落/主题切分
        """
        chunks = []

        # 按段落分割
        paragraphs = text.split('\n\n')

        current_chunk = []
        current_length = 0
        chunk_idx = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果段落太长，进一步切分
            if len(para) > self.chunk_size:
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk, source, chunk_idx, url, "guide"
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                    current_chunk = []

                # 切分长段落
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    if len(sentence) > self.chunk_size:
                        # 强制切分
                        for i in range(0, len(sentence), self.chunk_size - self.chunk_overlap):
                            chunk_text = sentence[i:i + self.chunk_size]
                            chunk = DocumentChunk(
                                id=f"{source}_{chunk_idx}",
                                content=chunk_text,
                                metadata={
                                    "source": source,
                                    "url": url,
                                    "type": "guide"
                                },
                                source=source
                            )
                            chunks.append(chunk)
                            chunk_idx += 1
                    else:
                        current_chunk.append(sentence)
                        current_length += len(sentence)

                        if current_length >= self.chunk_size:
                            chunk = self._create_chunk(
                                current_chunk, source, chunk_idx, url, "guide"
                            )
                            chunks.append(chunk)
                            chunk_idx += 1
                            current_chunk = []
                            current_length = 0
            else:
                current_chunk.append(para)
                current_length += len(para)

                if current_length >= self.chunk_size:
                    chunk = self._create_chunk(
                        current_chunk, source, chunk_idx, url, "guide"
                    )
                    chunks.append(chunk)
                    chunk_idx += 1
                    current_chunk = []
                    current_length = 0

        # 处理剩余内容
        if current_chunk:
            chunk = self._create_chunk(
                current_chunk, source, chunk_idx, url, "guide"
            )
            chunks.append(chunk)

        return chunks

    def process_case(self, text: str, case_name: str, url: str = "") -> List[DocumentChunk]:
        """
        处理判例 - 按争议点/判决切分
        """
        chunks = []

        # 提取关键部分
        sections = {
            "background": "",
            "issues": "",
            "decision": "",
            "reasons": ""
        }

        # 简单的段落分割
        paragraphs = text.split('\n\n')

        current_section = "background"
        current_content = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 检测章节标题
            para_lower = para.lower()
            if "issue" in para_lower or "question" in para_lower:
                if current_content:
                    sections[current_section] = '\n\n'.join(current_content)
                current_section = "issues"
                current_content = []
            elif "decision" in para_lower or "order" in para_lower:
                if current_content:
                    sections[current_section] = '\n\n'.join(current_content)
                current_section = "decision"
                current_content = []
            elif "reason" in para_lower:
                if current_content:
                    sections[current_section] = '\n\n'.join(current_content)
                current_section = "reasons"
                current_content = []

            current_content.append(para)

        if current_content:
            sections[current_section] = '\n\n'.join(current_content)

        # 创建 chunks
        for section_name, content in sections.items():
            if content:
                chunk = DocumentChunk(
                    id=f"{case_name}_{section_name}",
                    content=f"[{section_name.upper()}]\n\n{content}",
                    metadata={
                        "source": case_name,
                        "section": section_name,
                        "url": url,
                        "type": "case"
                    },
                    source=case_name,
                    section=section_name
                )
                chunks.append(chunk)

        return chunks

    def _create_chunk(
        self,
        paragraphs: List[str],
        source: str,
        chunk_idx: int,
        url: str,
        doc_type: str
    ) -> DocumentChunk:
        """创建文档块"""
        content = '\n\n'.join(paragraphs)
        return DocumentChunk(
            id=f"{source}_{chunk_idx}",
            content=content,
            metadata={
                "source": source,
                "url": url,
                "type": doc_type
            },
            source=source
        )

    def save_chunks(self, chunks: List[DocumentChunk], output_path: Path):
        """保存处理后的 chunks"""
        data = [
            {
                "id": chunk.id,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "source": chunk.source,
                "section": chunk.section,
                "title": chunk.title
            }
            for chunk in chunks
        ]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_chunks(self, input_path: Path) -> List[DocumentChunk]:
        """加载处理后的 chunks"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return [
            DocumentChunk(
                id=item["id"],
                content=item["content"],
                metadata=item["metadata"],
                source=item["source"],
                section=item.get("section", ""),
                title=item.get("title", "")
            )
            for item in data
        ]


# 示例数据 - 用于 MVP 测试
SAMPLE_DOCUMENTS = [
    {
        "id": "rta_2010_s41",
        "content": """Section 41 Rent increases

(1) A landlord may increase the rent payable under a residential tenancy agreement only if:
(a) the tenant is given written notice of the increase at least 60 days before the increase takes effect, and
(b) the rent is not increased within a period of 12 months after the last increase.

(2) The notice must specify:
(a) the amount of the increased rent, and
(b) the day from which the increased rent is payable.

(3) A rent increase that does not comply with this section is not payable and the tenant may recover any amount paid as a result of such an increase.

(4) This section does not apply to a fixed term agreement unless the agreement provides for rent increases during the term.""",
        "metadata": {
            "source": "Residential Tenancies Act 2010",
            "section": "Section 41",
            "title": "Rent increases",
            "type": "legislation",
            "url": "https://legislation.nsw.gov.au/view/html/inforce/current/act-2010-042#sec41"
        }
    },
    {
        "id": "rta_2010_s63",
        "content": """Section 63 Landlord's obligation to maintain premises

(1) A landlord must maintain the residential premises in a reasonable state of repair, having regard to the age of, the rent paid for and the prospective life of the premises.

(2) A landlord's obligation to maintain the premises does not apply to the extent that the need for repair arises from the tenant's failure to maintain the premises in a reasonable state of cleanliness or to use the premises in a proper manner.

Maximum penalty: 10 penalty units.

(3) A landlord is not in breach of this section if the landlord has complied with a tenant's request for urgent repairs within a reasonable time after receiving the request.""",
        "metadata": {
            "source": "Residential Tenancies Act 2010",
            "section": "Section 63",
            "title": "Landlord's obligation to maintain premises",
            "type": "legislation",
            "url": "https://legislation.nsw.gov.au/view/html/inforce/current/act-2010-042#sec63"
        }
    },
    {
        "id": "rta_2010_s55",
        "content": """Section 55 Entry with tenant's consent

(1) A landlord, or the landlord's agent, may enter the residential premises at any time with the tenant's consent.

(2) A landlord, or the landlord's agent, may enter the residential premises without the tenant's consent if:

(a) the tenant has advised the landlord, or the landlord's agent, that the tenant will be absent from the residential premises and the entry is made during the tenant's absence, or

(b) there are reasonable grounds for the landlord, or the landlord's agent, to believe that the tenant has abandoned the residential premises, or

(c) the entry is made on a day, or within a period, specified in a notice given under section 56, 57, 58 or 59.

(3) A landlord, or the landlord's agent, must not remain at the residential premises for longer than is necessary to achieve the purpose of the entry.

Maximum penalty: 10 penalty units.""",
        "metadata": {
            "source": "Residential Tenancies Act 2010",
            "section": "Section 55",
            "title": "Entry with tenant's consent",
            "type": "legislation",
            "url": "https://legislation.nsw.gov.au/view/html/inforce/current/act-2010-042#sec55"
        }
    },
    {
        "id": "fair_trading_bond",
        "content": """Bond (押金) 指南

## 什么是 Bond？

Bond 是租客在入住前支付给房东的押金，作为履行租约义务的担保。在 NSW，Bond 不是直接交给房东保管，而是必须存入 NSW Fair Trading 的 Rental Bond Board。

## Bond 的金额

- 最高 4 周租金（如果周租金 ≤ $900）
- 如果周租金 > $900，金额由房东和租客协商

## Bond 的退还

租约结束时，Bond 的退还需要：

1. **双方同意**: 房东和租客填写并签署 Bond 退款申请表
2. **Fair Trading 处理**: 通常 2-3 个工作日到账

## 如果有争议

如果房东和租客对 Bond 的退还金额有争议：

1. 尝试协商解决
2. 联系 NSW Fair Trading 寻求调解
3. 申请 NCAT (NSW Civil and Administrative Tribunal) 仲裁

## 重要提示

- 房东必须在收到 Bond 后 10 天内存入 Fair Trading
- 房东不能要求额外押金
- 保留好 Bond receipt，这是你的凭证

## 联系方式

- NSW Fair Trading: 13 32 20
- Rental Bond Board: 1800 300 020
- Tenants NSW: 1800 251 101""",
        "metadata": {
            "source": "Fair Trading NSW - Bond Guide",
            "type": "guide",
            "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/bond"
        }
    },
    {
        "id": "fair_trading_repairs",
        "content": """维修和保养 (Repairs and Maintenance)

## 房东的责任

根据 NSW 法律，房东必须：

1. 保持房屋处于合理维修状态
2. 确保所有设施（电器、管道、屋顶等）正常工作
3. 遵守建筑和健康安全标准

## 租客的责任

租客必须：

1. 保持房屋清洁
2. 小心使用设施
3. 及时报告需要维修的问题

## 报告维修问题

1. **书面通知房东** - 保留副本作为证据
2. **给予合理时间** - 非紧急维修通常 14 天
3. **跟进** - 如果没有回应，再次联系

## 紧急维修

如果情况紧急（如水管爆裂、停电、燃气泄漏）：

1. 立即通知房东/中介
2. 如果无法联系，可以自行安排维修
3. 紧急维修费用最高可报销 $1000

## 如果房东拒绝维修

1. 发送正式书面通知
2. 向 NSW Fair Trading 投诉
3. 申请 NCAT 命令

## 联系方式

- NSW Fair Trading: 13 32 20
- Tenants NSW: 1800 251 101
- Emergency repairs hotline: 联系房东或中介""",
        "metadata": {
            "source": "Fair Trading NSW - Repairs Guide",
            "type": "guide",
            "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/during-a-tenancy/repairs-and-maintenance"
        }
    },
    {
        "id": "fair_trading_ending",
        "content": """结束租约 (Ending a Tenancy)

## 固定期租约 (Fixed-term)

在固定期内结束租约：

1. **提前通知房东** - 越早越好
2. **可能需要支付违约金** - 通常到找到新租客为止的租金
3. **房东有义务减少损失** - 必须积极寻找新租客

## 周期租约 (Periodic)

周期租约结束需要：

- **租客**: 提前 21 天书面通知
- **房东**: 提前 90 天书面通知（无理由）

## 房东可以驱逐的情况

房东可以在以下情况给予 30 天通知：

1. 房东或家属要入住
2. 房屋要出售
3. 房屋要拆除或翻修
4. 租客违约（如欠租、损坏房屋）

## 退房检查

1. 清洁房屋
2. 移除所有物品
3. 归还钥匙
4. 与房东一起检查
5. 拍照留证

## Bond 退还

- 填写退款申请表
- 双方签字
- 提交至 Fair Trading

## 重要提示

- 保留所有书面通知的副本
- 退房前拍照记录房屋状况
- 如果有争议，可以申请 NCAT

## 联系方式

- NSW Fair Trading: 13 32 20
- Tenants NSW: 1800 251 101""",
        "metadata": {
            "source": "Fair Trading NSW - Ending Tenancy Guide",
            "type": "guide",
            "url": "https://www.fairtrading.nsw.gov.au/housing-and-property/renting/ending-a-tenancy"
        }
    }
]


def create_sample_data():
    """创建示例数据"""
    processor = DocumentProcessor()

    chunks = [
        DocumentChunk(
            id=doc["id"],
            content=doc["content"],
            metadata=doc["metadata"],
            source=doc["metadata"]["source"],
            section=doc["metadata"].get("section", ""),
            title=doc["metadata"].get("title", "")
        )
        for doc in SAMPLE_DOCUMENTS
    ]

    output_path = config.processed_data_dir / "sample_chunks.json"
    processor.save_chunks(chunks, output_path)

    print(f"Created {len(chunks)} sample chunks at {output_path}")
    return chunks


if __name__ == "__main__":
    create_sample_data()
