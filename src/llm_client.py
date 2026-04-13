"""
LLM Client - 调用 LLM 生成回答
"""

from typing import Optional
from openai import OpenAI

from .config import config, SYSTEM_PROMPT


class LLMClient:
    """LLM 客户端 - 支持 CodingPlan API"""

    def __init__(self, api_key: Optional[str] = None):
        # 优先使用 CodingPlan API
        if config.codingplan_api_key:
            self.client = OpenAI(
                api_key=config.codingplan_api_key,
                base_url=config.codingplan_base_url
            )
            self.model = config.codingplan_model
        else:
            # 回退到 OpenAI
            client_kwargs = {"api_key": api_key or config.openai_api_key}
            if config.openai_base_url:
                client_kwargs["base_url"] = config.openai_base_url
            self.client = OpenAI(**client_kwargs)
            self.model = config.llm_model
        
        self.temperature = config.llm_temperature
        self.max_tokens = config.llm_max_tokens

    def generate_answer(
        self,
        question: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """基于上下文生成回答"""
        prompt = system_prompt or SYSTEM_PROMPT

        user_message = f"""基于以下法律信息回答问题。如果信息不足，请明确说明。

## 相关法律信息

{context}

## 问题

{question}

## 回答要求

1. 先给出直接、简洁的回答
2. 引用具体的法律条款或来源
3. 提供实用的行动建议
4. 如果不确定，建议咨询专业律师
5. 末尾添加免责声明"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        return response.choices[0].message.content

    def chat(
        self,
        messages: list,
        system_prompt: Optional[str] = None
    ) -> str:
        """多轮对话"""
        prompt = system_prompt or SYSTEM_PROMPT

        full_messages = [{"role": "system", "content": prompt}] + messages

        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        return response.choices[0].message.content
