import json
from typing import Annotated, TypedDict, List, Sequence
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch


from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from agent.langsearch_tool import langsearch_websearch_tool

from dotenv import load_dotenv

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


##########
## 1. Query Generation
### 用户使用自然语言输入，根据输入，生成搜索查询关键字
def query_generation_node(state: AgentState) -> AgentState:
    system_prompt = """
    你是一个搜索查询生成助手，根据用户输入，生成用于搜索引擎使用的搜索查询关键字，关键字可以有多个，确保能够搜速到用户关心的话题。
    用户使用中文输入，提取出的搜索关键字为英文，因为技术文档是英文的。如果用户中英文混合输入，则英文部分是关键字的一部分
    搜索范围限定为 site:support.apple.com
    
    举例如下：
    User: 苹果手机怎么连接蓝牙耳机？
    Assistant: iPhone Bluetooth connection guide site:support.apple.com

    User: 什么是Apple Business Manager？
    Assistant: Apple Business Manager site:support.apple.com
    """
    # llm = ChatOllama(model="Qwen2.5-14B-Instruct:latest")
    llm = ChatOllama(model="qwen2.5:3b")
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm.invoke(messages)
    print(f"🔍 生成搜索查询: {response.content}")
    return {"messages": [response]}
#########



@tool
def search_web(query: str) -> str:
    """Search the web for information with Tavily."""
    search = TavilySearch(max_results=3, include_raw_content=True)
    return search.run(query) 



tools = [langsearch_websearch_tool]
llm = ChatOllama(model="qwen2.5:7b")
llm_with_tools = llm.bind_tools(tools)


def agent_node(state: AgentState) -> AgentState:
    system_prompt = """
    你是一个专业的Apple产品技术专家，服务于中国客户, 需要将输入的英文文档，整理成中文回答，并给出参考链接。
    必须使用中文来回答，否则用户会给差评，从而导致你的工作被取消。
    """
    web_search_result = state["messages"][-1].content
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=web_search_result)]
    response = llm.invoke(messages)
    return {"messages": [response]}



# def agent_node(state: AgentState) -> AgentState:
#     system_prompt = """
#     你是一个专业的Apple产品技术专家，服务于中国客户。
#     你必须使用工具来搜索相关信息，不要依赖自己的知识。
#     必须使用中文来回答，否则用户会给差评，从而导致你的工作被取消。
#     """

#     # 获取搜索查询（来自query_generation_node）
#     search_query = state["messages"][-1].content
#     search_instruction = f"必须立即使用工具搜索：{search_query}"
#     messages = [
#         SystemMessage(content=system_prompt),
#         HumanMessage(content=search_instruction)
#     ]
#     response = llm_with_tools.invoke(messages)
    
#     return {"messages": [response]}

# tools_by_name = {tool.name: tool for tool in tools}

# Define our tool node
# def tool_node(state: AgentState):
#     print("🔧 正在调用搜索工具...")
#     outputs = []
#     for tool_call in state["messages"][-1].tool_calls:
#         print(f"🌐 搜索查询: {tool_call['args']['query']}")
#         tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
#         outputs.append(
#             ToolMessage(
#                 content=json.dumps(tool_result),
#                 name=tool_call["name"],
#                 tool_call_id=tool_call["id"],
#             )
#         )
#     print("✅ 搜索完成，正在生成回答...")
#     return {"messages": outputs}

def tool_node(state: AgentState):
    print("🔧 正在调用搜索工具...")
    outputs = []

    query = state["messages"][-1].content
    print(f"🌐 搜索查询: {query}")
    tool_result = langsearch_websearch_tool.invoke(query, count=1)

    outputs.append(
        ToolMessage(
            content=json.dumps(tool_result),
            name=langsearch_websearch_tool.name,
           tool_call_id="tool-1",
        )
    )
    print("✅ 搜索完成，正在生成回答...")
    return {"messages": outputs}

# Define the conditional edge that determines whether to call tools or end
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    # If there are tool calls, go to tool node
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    # Otherwise, we finish
    else:
        return "end"

# langchain_llm = ChatOllama(model="qwen2.5:1.5b")


# Build the graph
graph = StateGraph(AgentState)

# # Add nodes
# graph.add_node("query_generation", query_generation_node)
# graph.add_node("agent", agent_node)
# graph.add_node("tools", tool_node)

# # Add edges
# graph.add_edge(START, "query_generation")
# graph.add_edge("query_generation", "agent")
# graph.add_conditional_edges(
#     "agent",
#     should_continue,
#     {"tools": "tools", "end": END},
# )
# # Add edge from tools back to agent
# graph.add_edge("tools", "agent")

graph.add_node("query_generation", query_generation_node)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "query_generation")
# graph.add_edge("query_generation", "agent")
# graph.add_conditional_edges(
#     "agent", should_continue, {"tools": "tools", "end": END})
graph.add_edge("query_generation", "tools")
graph.add_edge("tools", "agent")
graph.add_edge("agent", END)

app = graph.compile()

# 配置递归限制
config = {"recursion_limit": 10}

# Helper function for formatting the stream nicely
def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()



def run_agent():
    print("\n ===== Langgraph Agent =====\n")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            break
        messages = [HumanMessage(content=user_input)]
        result = app.invoke({"messages": messages}, config=config)

        print("\n===== Assistant =====\n")
        print(result["messages"][-1].content)


if __name__ == "__main__":
    run_agent()
