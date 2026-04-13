"""
Gradio UI - Web 界面
"""

import os
import sys

# 设置环境变量
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
sys.stdout.reconfigure(encoding='utf-8')

import gradio as gr
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag_pipeline import create_rag_pipeline
import json

# 全局 pipeline
pipeline = None
DOC_COUNT = 0


def initialize():
    """初始化"""
    global pipeline, DOC_COUNT
    if pipeline is None:
        print("Creating RAG pipeline...")
        pipeline = create_rag_pipeline(use_qdrant=False)
        
        # 加载文档 - 优先使用完整数据，回退到示例数据
        data_path = Path(__file__).parent.parent / "data" / "processed" / "all_chunks.json"
        sample_path = Path(__file__).parent.parent / "data" / "processed" / "sample_data.json"
        
        if data_path.exists():
            print(f"Loading documents from {data_path}")
            with open(data_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)
        elif sample_path.exists():
            print(f"Loading sample documents from {sample_path}")
            with open(sample_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)
        else:
            print(f"Warning: No data files found")
            documents = []
        
        if documents:
            pipeline.vector_store.clear()
            pipeline.index_documents(documents)
            DOC_COUNT = len(documents)
            print(f"Loaded {DOC_COUNT} documents")
    
    return pipeline


def chat(message, history):
    """处理消息 - Gradio 6.0 格式"""
    if not message or not message.strip():
        return history, ""
    
    try:
        print(f"Processing query: {message[:50]}...")
        response = pipeline.query(message)
        reply = response.answer
        
        if response.sources:
            reply += "\n\n---\n\n**📚 参考来源:**\n"
            for src in response.sources[:3]:
                reply += f"- {src['source']}\n"
        
        # Gradio 6.0 格式：使用字典
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": reply}
        ]
        return history, ""
    except Exception as e:
        print(f"Error: {e}")
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": f"❌ 错误: {str(e)}"}
        ]
        return history, ""


def analyze_contract(contract_text):
    """分析合同合规性"""
    if not contract_text or not contract_text.strip():
        return "请粘贴租房合同内容..."
    
    try:
        # 使用 RAG 查询相关法律
        prompt = f"""请分析以下租房合同条款是否合规，指出可能存在的问题：

合同内容：
{contract_text[:3000]}

请从以下角度分析：
1. 押金条款是否合规
2. 涨租条款是否合规
3. 终止条款是否合规
4. 维修责任是否合规
5. 其他可能的问题

请用中文回答，并引用相关法律依据。"""
        
        response = pipeline.query(prompt)
        return response.answer
    except Exception as e:
        return f"❌ 分析出错: {str(e)}"


def clear_chat():
    """清空"""
    if pipeline:
        pipeline.clear_history()
    return [], ""


# UI
if __name__ == "__main__":
    print("=" * 60)
    print("Starting NSW Tenancy Law RAG Gradio UI")
    print("=" * 60)
    
    # 初始化
    initialize()
    
    print("Creating Gradio interface...")
    
    with gr.Blocks(title="NSW 租房法律咨询") as demo:
        # 标题
        gr.Markdown("""
        # 🏠 NSW 租房法律咨询助手
        
        为澳洲留学生提供专业的租房法律问题咨询
        
        ---
        """)
        
        # 状态栏
        status_md = gr.Markdown(f"""
        > ✅ 已加载 **{DOC_COUNT}** 个法律文档 | 🤖 LLM: GLM5 | 📊 Embedding: 本地模型
        """)
        
        # 创建标签页
        with gr.Tabs():
            # Tab 1: 问答
            with gr.TabItem("💬 法律问答"):
                # 聊天区域 - Gradio 6.0 默认 messages 格式
                chatbot = gr.Chatbot(height=400, label="对话")
                
                # 输入区域
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="💬 输入您的租房法律问题...",
                        show_label=False,
                        scale=4
                    )
                    submit = gr.Button("发送 ✨", variant="primary", scale=1)
                
                # 清空按钮
                clear = gr.Button("🗑️ 清空对话", variant="secondary")
                
                # 常见问题
                gr.Markdown("### 💡 常见问题（点击快速提问）")
                
                with gr.Row():
                    ex1 = gr.Button("🏠 房东可以随意涨房租吗？")
                    ex2 = gr.Button("💰 房东不退押金怎么办？")
                    ex3 = gr.Button("🔧 房东拒绝维修怎么办？")
                
                with gr.Row():
                    ex4 = gr.Button("🚪 我可以提前退租吗？")
                    ex5 = gr.Button("🔑 房东可以随时进入我的房间吗？")
                    ex6 = gr.Button("📋 二房东有什么风险？")
            
            # Tab 2: 合同审查
            with gr.TabItem("📄 合同审查"):
                gr.Markdown("""
                ### 📋 合同合规性检查
                
                粘贴您的租房合同内容，系统将自动分析条款是否合规。
                
                **支持检查：**
                - 押金条款
                - 涨租条款
                - 终止条款
                - 维修责任
                - 非法收费
                """)
                
                contract_input = gr.Textbox(
                    label="粘贴合同内容",
                    placeholder="请粘贴租房合同内容...\n\n例如：\n- 押金：8周租金\n- 房东可随时涨租\n- 提前退租押金不退...",
                    lines=10
                )
                
                analyze_btn = gr.Button("🔍 分析合同", variant="primary")
                contract_output = gr.Textbox(label="分析结果", lines=15)
                
                analyze_btn.click(analyze_contract, contract_input, contract_output)
        
        # 底部信息
        gr.Markdown("""
        ---
        
        ⚠️ **免责声明**: 本系统仅供参考，不构成法律建议。如有具体法律问题，请咨询专业律师。
        
        📞 **求助热线**: NSW Fair Trading: 13 32 20 | Tenants NSW: 1800 251 101
        """)
        
        # 事件绑定
        msg.submit(chat, [msg, chatbot], [chatbot, msg])
        submit.click(chat, [msg, chatbot], [chatbot, msg])
        clear.click(clear_chat, None, [chatbot, msg])
        
        # 示例按钮事件
        ex1.click(lambda: "房东可以随意涨房租吗？", None, msg)
        ex2.click(lambda: "房东不退押金怎么办？", None, msg)
        ex3.click(lambda: "房东拒绝维修怎么办？", None, msg)
        ex4.click(lambda: "我可以提前退租吗？", None, msg)
        ex5.click(lambda: "房东可以随时进入我的房间吗？", None, msg)
        ex6.click(lambda: "二房东有什么风险？", None, msg)
    
    print("Launching Gradio server...")
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True
    )
