from typing import List, Dict, Any, Optional
import httpx
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# 加载环境变量
load_dotenv()

# 配置LangSearch API端点
LANGSEARCH_API_BASE = "https://api.langsearch.com"
WEB_SEARCH_ENDPOINT = f"{LANGSEARCH_API_BASE}/v1/web-search"
RERANK_ENDPOINT = f"{LANGSEARCH_API_BASE}/v1/rerank"
API_KEY = os.getenv("LANGSEARCH_API_KEY")

# 创建MCP服务器
mcp = FastMCP("LangSearch MCP")

@mcp.resource("langsearch://config")
def get_config() -> str:
    """获取LangSearch配置信息"""
    return f"""
    LangSearch API配置:
    - API Base: {LANGSEARCH_API_BASE}
    - Web Search Endpoint: {WEB_SEARCH_ENDPOINT}
    - Rerank Endpoint: {RERANK_ENDPOINT}
    """

@mcp.tool()
async def web_search(query: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    """
    执行网络搜索查询
    
    Args:
        query: 搜索查询
        limit: 返回结果数量限制
        offset: 结果偏移量
    
    Returns:
        搜索结果
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WEB_SEARCH_ENDPOINT,
                json={
                    "query": query,
                    "limit": limit,
                    "offset": offset
                },
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def rerank_documents(query: str, documents: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    对文档列表进行重排序
    
    Args:
        query: 搜索查询
        documents: 文档列表，每个文档必须包含text字段
    
    Returns:
        重排序结果
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RERANK_ENDPOINT,
                json={
                    "query": query,
                    "documents": documents
                },
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.prompt()
def search_prompt(query: str) -> str:
    """
    创建一个搜索提示模板
    
    Args:
        query: 搜索查询
    """
    return f"""
请使用LangSearch进行以下搜索查询:

查询: {query}

您可以使用web_search工具执行这个查询，然后分析结果。
    """

@mcp.prompt()
def rerank_prompt(query: str) -> str:
    """
    创建一个重排序提示模板
    
    Args:
        query: 重排序查询
    """
    return f"""
请使用LangSearch对文档进行重排序:

查询: {query}

首先使用web_search工具获取初始结果，然后使用rerank_documents工具对结果进行重排序以提高相关性。
    """

def run_server():
    """Command-line entry point to run the MCP server."""
    print("Starting LangSearch MCP server via stdio...")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    run_server()
