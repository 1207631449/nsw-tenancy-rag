"""
FastAPI Backend - API 接口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag_pipeline import create_rag_pipeline, RAGPipeline, RAGResponse


# 初始化
app = FastAPI(
    title="NSW Tenancy Law RAG API",
    description="为澳洲留学生提供 NSW 租房法律问题咨询的 RAG 系统",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局 pipeline
pipeline: RAGPipeline = None


@app.on_event("startup")
async def startup():
    """启动时初始化"""
    global pipeline
    pipeline = create_rag_pipeline()


# 请求模型
class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    include_sources: Optional[bool] = True


class Source(BaseModel):
    source: str
    section: Optional[str] = ""
    url: Optional[str] = ""
    relevance: float


class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence: float


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


# API 端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "NSW Tenancy Law RAG API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """查询接口"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        response = pipeline.query(
            question=request.question,
            top_k=request.top_k,
            include_sources=request.include_sources
        )

        return QueryResponse(
            answer=response.answer,
            sources=[
                Source(**src) for src in response.sources
            ],
            confidence=response.confidence
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest):
    """多轮对话接口"""
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")

    try:
        # 获取最后一条用户消息
        last_message = request.messages[-1]
        if last_message.role != "user":
            raise HTTPException(status_code=400, detail="Last message must be from user")

        response = pipeline.query(last_message.content)

        return {
            "role": "assistant",
            "content": response.answer
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/examples")
async def examples():
    """获取示例问题"""
    return {
        "examples": [
            "房东可以随意涨房租吗？",
            "房东不退押金怎么办？",
            "房东拒绝维修怎么办？",
            "我可以提前退租吗？",
            "房东可以随时进入我的房间吗？",
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
