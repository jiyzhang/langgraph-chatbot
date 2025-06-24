import requests
import os
from langchain.tools import tool
import datetime
import json
from dotenv import load_dotenv

load_dotenv()

LANGSEARCH_API_KEY = os.getenv("LANGSEARCH_API_KEY")

# Define LangSearch Web Search tool
@tool
def langsearch_websearch_tool(query: str, count: int = 2) -> str:
    """
    Perform web search using LangSearch Web Search API.

    Parameters:
    - query: Search keywords
    - count: Number of search results to return

    Returns:
    - Detailed information of search results, including web page title, web page URL, web page content, web page publication time, etc.
    """
    
    url = "https://api.langsearch.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {LANGSEARCH_API_KEY}",  # Please replace with your API key
        "Content-Type": "application/json"
    }
    data = {
        "query": query,
        "freshness": "noLimit",  # Search time range, e.g., "oneDay", "oneWeek", "oneMonth", "oneYear", "noLimit"
        "summary": True,          # Whether to return a long text summary
        "count": count
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        json_response = response.json()
        try:
            if json_response["code"] != 200 or not json_response["data"]:
                return f"Search API request failed, reason: {response.msg or 'Unknown error'}"
            
            webpages = json_response["data"]["webPages"]["value"]
            if not webpages:
                return "No relevant results found."
            formatted_results = ""
            # formatted_results = json.dumps(webpages, indent=4)
            for idx, page in enumerate(webpages, start=1):
                formatted_results += (
                    f"Citation: {idx}\n"
                    f"Title: {page['name']}\n"
                    f"URL: {page['url']}\n"
                    f"Content: {page['summary']}\n"
                )
            
            return formatted_results.strip()
        except Exception as e:
            return f"Search API request failed, reason: Failed to parse search results {str(e)}"
    else:
        return f"Search API request failed, status code: {response.status_code}, error message: {response.text}"

# # Create LangChain tools
# tools = [Tool(
#     name="LangSearchWebSearch",
#     func=langsearch_websearch_tool,
#     description="Use LangSearch Web Search API to search internet web pages. The input should be a search query string, and the output will return detailed information of search results, including web page title, web page URL, web page content, web page publication time, etc."
# )]


if __name__ == "__main__":
    result = langsearch_websearch_tool.invoke({"query": "what is Apple Business Manager? site:support.apple.com"})
    print(result)