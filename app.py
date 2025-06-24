import streamlit as st
from langchain_core.messages import HumanMessage
#from client import app, config
from agent.graph import app, config
import time

# 设置页面配置
st.set_page_config(
    page_title="🍎 Apple 产品技术支持助手",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #667eea;
    }
    .assistant-message {
        background-color: #e8f4fd;
        border-left-color: #1f77b4;
    }
    .process-step {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.25rem 0;
        font-size: 0.9rem;
    }
    .streaming-text {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        white-space: pre-wrap;
        word-wrap: break-word;
        line-height: 1.6;
    }
    .footer-fixed {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #f8f9fa;
        border-top: 1px solid #dee2e6;
        text-align: center;
        padding: 10px 0;
        z-index: 999;
        color: #666;
        font-size: 0.9rem;
    }
    .main-content {
        padding-bottom: 60px;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown("""
<div class="main-header">
    <h1>🍎 Apple 产品技术支持助手</h1>
    <p>专业的Apple产品技术支持，基于官方文档提供准确回答</p>
</div>
""", unsafe_allow_html=True)

# 主内容容器
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("🔧 系统信息")
    st.info("✅ LangGraph Agent 已启动")
    st.info("✅ Apple官方文档搜索")
    st.info("✅ 智能查询生成")
    st.info("✅ 流式输出支持")
    
    st.header("📋 使用说明")
    st.markdown("""
    1. 在下方输入您的Apple产品相关问题
    2. 系统会自动生成搜索关键字
    3. 从Apple官方文档获取信息
    4. 为您提供专业的中文回答
    5. 支持实时流式输出体验
    
    **示例问题:**
    - 苹果手机怎么连接蓝牙耳机？
    - iPhone如何连接Apple Watch？
    - 什么是Apple Business Manager？
    - iPad怎么分屏操作？
    """)
    
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.rerun()

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示聊天历史
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>👤 您:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>🤖 助手:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
        
        # 显示处理步骤（如果有的话）
        if "steps" in message:
            with st.expander("🔍 查看处理步骤", expanded=False):
                for step in message["steps"]:
                    st.markdown(f"""
                    <div class="process-step">
                        {step}
                    </div>
                    """, unsafe_allow_html=True)

# 聊天输入
if prompt := st.chat_input("请输入您的Apple产品相关问题..."):
    # 添加用户消息到历史
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 显示用户消息
    st.markdown(f"""
    <div class="chat-message user-message">
        <strong>👤 您:</strong><br>
        {prompt}
    </div>
    """, unsafe_allow_html=True)
    
    # 显示处理状态和流式输出
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        
        try:
            # 准备输入消息
            messages = [HumanMessage(content=prompt)]
            
            # 存储流式输出的内容
            streaming_content = ""
            processing_steps = []
            current_step = ""
            
            # 使用流式调用
            status_placeholder.markdown("🔄 **正在处理您的请求...**")
            
            # 流式处理
            for chunk in app.stream({"messages": messages}, config=config):
                # 处理每个节点的输出
                for node_name, node_output in chunk.items():
                    if "messages" in node_output:
                        latest_message = node_output["messages"][-1]
                        
                        # 根据节点类型显示不同的状态
                        if node_name == "query_generation":
                            current_step = f"🔍 **生成搜索查询:** {latest_message.content}"
                            processing_steps.append(current_step)
                            status_placeholder.markdown(current_step)
                            time.sleep(0.5)  # 让用户看到这个步骤
                            
                        elif node_name == "tools":
                            current_step = "🌐 **正在搜索Apple官方文档...**"
                            processing_steps.append(current_step)
                            status_placeholder.markdown(current_step)
                            time.sleep(0.5)
                            
                        elif node_name == "agent":
                            # 这是最终的回答
                            current_step = "✍️ **正在生成回答...**"
                            status_placeholder.markdown(current_step)
                            
                            # 模拟流式输出文本
                            final_answer = latest_message.content
                            streaming_content = ""
                            
                            # 逐字符显示（模拟打字效果）
                            # for i, char in enumerate(final_answer):
                            #     streaming_content += char
                            #     message_placeholder.markdown(f"""
                            #     <div class="streaming-text">
                            #     {streaming_content}
                            #     </div>
                            #     """, unsafe_allow_html=True)
                            for i, char in enumerate(final_answer):
                                streaming_content += char
                                message_placeholder.markdown(f"""
                                {streaming_content}
                                """)
                                
                                # 控制打字速度
                                if i % 5 == 0:  # 每5个字符暂停一次
                                    time.sleep(0.05)
                            
                            # 清除状态显示
                            status_placeholder.empty()
                            
                            # 显示最终格式化的回答
                            message_placeholder.markdown(final_answer)
                            
                            # 收集所有处理步骤
                            processing_steps.append("✅ **回答生成完成**")
                            
                            # 添加助手回答到历史
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": final_answer,
                                "steps": processing_steps
                            })
                            
                            break
            
        except Exception as e:
            error_msg = f"❌ 处理请求时发生错误: {str(e)}"
            message_placeholder.markdown(error_msg)
            status_placeholder.empty()
            
            # 添加错误消息到历史
            st.session_state.messages.append({
                "role": "assistant", 
                "content": error_msg
            })

# 结束主内容容器
st.markdown('</div>', unsafe_allow_html=True)

# 固定页脚
st.markdown("""
<div class="footer-fixed">
    🍎 Apple 产品技术支持助手 | 基于官方文档提供准确信息 | Powered by LangGraph + Ollama | 🔄 流式输出
</div>
""", unsafe_allow_html=True) 
