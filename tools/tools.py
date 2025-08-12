# tools.py
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from langchain_community.utilities import SerpAPIWrapper, DuckDuckGoSearchAPIWrapper


def create_search_tool(api_key: str | None):
    """Create a web search tool that prefers SerpAPI and falls back to DuckDuckGo.
    
    Returns a dictionary format compatible with CrewAI.
    """
    serpapi_search = None
    if api_key:
        try:
            serpapi_search = SerpAPIWrapper(serpapi_api_key=api_key)
        except Exception as e:
            print(f"[SearchTool] Could not initialize SerpAPI: {e}. Falling back to DuckDuckGo only.")

    duckduckgo_search = DuckDuckGoSearchAPIWrapper()

    def try_serpapi(query: str) -> str:
        if serpapi_search is None:
            raise RuntimeError("SerpAPI is unavailable")
        return serpapi_search.run(query)

    def web_search(query: str) -> str:
        """Search the web for up-to-date information using SerpAPI with DuckDuckGo fallback."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(try_serpapi, query)
            try:
                print(f"[SearchTool] Trying SerpAPI for query: {query}")
                return future.result(timeout=5)
            except (TimeoutError, Exception) as e:
                print(f"[SearchTool] SerpAPI failed with error: {e}. Falling back to DuckDuckGo...")
                try:
                    return duckduckgo_search.run(query)
                except Exception as e2:
                    print(f"[SearchTool] DuckDuckGo also failed: {e2}")
                    return "Search failed with both SerpAPI and DuckDuckGo."

    # Return in dictionary format as suggested by CrewAI error
    return {
        "name": "web_search",
        "description": "Search the web for up-to-date information using SerpAPI with DuckDuckGo fallback.",
        "function": web_search
    }


if __name__ == "__main__":
    # Test the tool directly from .env
    API_KEY = os.getenv("SERPAPI_API_KEY")
    search_tool = create_search_tool(API_KEY)
    print(search_tool["function"]("Tesla latest financial results"))
