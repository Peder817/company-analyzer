import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from langchain_community.utilities import SerpAPIWrapper, DuckDuckGoSearchAPIWrapper
import yfinance as yf

# ------------------------------------------------------------
# Web Search Tool (SerpAPI + DuckDuckGo fallback)
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Smart Financial Data Tool (Company name → Ticker → Financial data)
# ------------------------------------------------------------
import yfinance as yf

def create_financial_data_tool():
    """Tool for fetching recent financial data by company name using Yahoo Finance."""

    def get_financial_data(company_name: str) -> dict:
        try:
            # 1. Försök hitta rätt ticker
            search = yf.Ticker(company_name)  # If company_name is already a ticker
            ticker = company_name.upper()

            # Om info saknas helt, prova via yfinance search
            if not search.info or search.info.get("regularMarketPrice") is None:
                try:
                    import requests
                    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={company_name}"
                    resp = requests.get(url, timeout=5)
                    data = resp.json()
                    if data.get("quotes"):
                        ticker = data["quotes"][0]["symbol"]
                        search = yf.Ticker(ticker)
                    else:
                        return {"error": f"No ticker found for company: {company_name}"}
                except Exception as e:
                    return {"error": f"Failed to find ticker for {company_name}: {e}"}

            # 2. Hämta senaste års- och kvartalsdata (max 2 år)
            price_history = search.history(period="2y").to_dict()

            data = {
                "ticker": ticker,
                "company_info": {
                    "shortName": search.info.get("shortName"),
                    "longName": search.info.get("longName"),
                    "sector": search.info.get("sector"),
                    "industry": search.info.get("industry"),
                    "country": search.info.get("country"),
                    "website": search.info.get("website"),
                    "marketCap": search.info.get("marketCap"),
                    "regularMarketPrice": search.info.get("regularMarketPrice"),
                },
                "quarterly_financials": search.quarterly_financials.to_dict(),
                "financials": search.financials.to_dict(),
                "quarterly_balance_sheet": search.quarterly_balance_sheet.to_dict(),
                "balance_sheet": search.balance_sheet.to_dict(),
                "quarterly_cashflow": search.quarterly_cashflow.to_dict(),
                "cashflow": search.cashflow.to_dict(),
                "price_history_2y": price_history
            }
            return data

        except Exception as e:
            return {"error": f"Failed to fetch financial data: {e}"}

    # Return in dictionary format as expected by CrewAI
    return {
        "name": "financial_data",
        "description": "Fetch recent financial data (last 2 years) for a given company name using Yahoo Finance.",
        "function": get_financial_data
    }
