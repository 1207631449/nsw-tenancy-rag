# 🏠 NSW Tenancy Law RAG System

> 为澳洲留学生提供专业的 NSW 租房法律问题咨询

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 功能特点

- 🔍 **智能问答** - 基于 RAG 的租房法律咨询
- 📄 **合同审查** - 自动检测合同条款合规性
- 📚 **知识库** - 包含 NSW 租赁法、官方指南、判例等
- 🌐 **Web UI** - 友好的 Gradio 界面

## 📋 知识库内容

| 类别 | 内容 |
|------|------|
| **法律条文** | Residential Tenancies Act 2010 关键条款 |
| **官方指南** | Fair Trading NSW 租房指南 |
| **判例** | NCAT 实际仲裁案例 |
| **FAQ** | 常见问题解答 |
| **合规检查** | 合同条款合规性知识 |

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/nsw-tenancy-rag.git
cd nsw-tenancy-rag
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

### 4. 运行

```bash
python app/gradio_app.py
```

访问 http://127.0.0.1:7860

## 📁 项目结构

```
nsw-tenancy-rag/
├── app/
│   └── gradio_app.py          # Gradio Web UI
├── src/
│   ├── config.py              # 配置管理
│   ├── document_processor.py  # 文档处理
│   ├── embeddings.py          # Embedding 生成
│   ├── llm_client.py          # LLM 客户端
│   └── rag_pipeline.py        # RAG 主流程
├── data/
│   ├── raw/                   # 原始数据
│   └── processed/             # 处理后的数据
├── scripts/
│   └── *.py                   # 数据收集脚本
├── .env.example               # 环境变量模板
├── requirements.txt           # Python 依赖
└── README.md
```

## 🔧 配置说明

### LLM 配置

1. 访问大模型厂商注册账号，示例使用讯飞Maas平台coding plan
2. 获取 API Key
3. 在 `.env` 中配置：

```env
CODINGPLAN_API_KEY=your_api_key_here
```

### Embedding 模型

使用本地 embedding 模型，无需额外 API：

- 模型：`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- 维度：384
- 支持中英文

## 📖 使用指南

### 法律问答

直接输入问题，例如：
- "房东可以随意涨房租吗？"
- "房东不退押金怎么办？"
- "我可以提前退租吗？"

### 合同审查

1. 点击 **"合同审查"** 标签页
2. 粘贴合同内容
3. 点击 **"分析合同"**

系统会自动检测：
- 押金是否超过法定上限
- 涨租条款是否合规
- 终止条款是否合法
- 维修责任是否合理
- 是否存在非法收费

## 📞 求助热线

- **NSW Fair Trading**: 13 32 20
- **Tenants NSW**: 1800 251 101
- **Law Access NSW**: 1300 888 529

## ⚠️ 免责声明

本系统仅供参考，不构成法律建议。如有具体法律问题，请咨询专业律师。

## 📄 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

Made with ❤️ for international students in NSW
