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
    import yfinance as yf
    import pandas as pd
    import requests

    # --- små helpers för normalisering ---
    METRIC_MAP = {
        "total revenue": "revenue",
        "revenue": "revenue",
        "net sales": "revenue",
        "sales": "revenue",
        "turnover": "revenue",
        "net income": "net_income",
        "net profit": "net_income",
        "profit": "net_income",
        "ebitda": "ebitda",
        "adjusted ebitda": "ebitda",
    }

    def _q_label(x) -> str:
        if isinstance(x, pd.Timestamp):
            p = pd.Period(x, freq="Q")
            return f"Q{p.quarter} {p.year}"
        try:
            p = pd.Period(pd.to_datetime(str(x)), freq="Q")
            return f"Q{p.quarter} {p.year}"
        except Exception:
            return str(x)

    def _norm_metric(name: str) -> str | None:
        return METRIC_MAP.get(str(name).strip().lower())

    def _to_int(v):
        try:
            if pd.isna(v):
                return None
            return int(float(v))
        except Exception:
            return None

    def _normalize_quarterly_financials(df: pd.DataFrame) -> tuple[dict, list]:
        """Returnerar (series_dict, rows_list) där rows_list är för UI:t."""
        if df is None or df.empty:
            return {}, []
        cols = list(df.columns)
        labels = [_q_label(c) for c in cols]

        # 1) Series per metrik (behåll originalnamn så agenten kan citera)
        wanted = ["Total Revenue", "Revenue", "Net Income", "EBITDA", "Operating Income", "Gross Profit"]
        series_dict: dict[str, dict] = {}
        for metric in wanted:
            if metric in df.index:
                s = df.loc[metric]
                series = {}
                for lbl, col in zip(labels, cols):
                    val = _to_int(s.get(col))
                    if val is not None:
                        series[lbl] = val
                if series:
                    series_dict[metric] = series

        # 2) Radrformat (quarters) för diagrammet
        rows = []
        for lbl, col in zip(labels, cols):
            row = {"quarter": lbl}
            for idx in df.index:
                std = _norm_metric(idx)
                if not std:
                    continue
                val = _to_int(df.loc[idx, col])
                if val is not None:
                    row[std] = val
            if any(k in row for k in ("revenue", "net_income", "ebitda")):
                rows.append(row)

        # sortera äldst→nyast
        def _q_sort_key(qs: str):
            try:
                p = pd.Period(qs.replace("-", " "), freq="Q")
                return (p.year, p.quarter)
            except Exception:
                return (0, 0)
        rows = sorted(rows, key=lambda r: _q_sort_key(r["quarter"]))
        return series_dict, rows

    def get_financial_data(company_name: str) -> dict:
        try:
            # 1) hitta/gissa ticker
            ticker_symbol = company_name.upper()
            t = yf.Ticker(company_name)
            if not getattr(t, "info", None) or t.info.get("regularMarketPrice") is None:
                url = f"https://query1.finance.yahoo.com/v1/finance/search?q={company_name}"
                resp = requests.get(url, timeout=5)
                data = resp.json()
                if data.get("quotes"):
                    ticker_symbol = data["quotes"][0]["symbol"]
                    t = yf.Ticker(ticker_symbol)
                else:
                    return {"error": f"No ticker found for company: {company_name}"}

            # 2) hämta data
            qf_df = t.quarterly_financials  # index=metrics, columns=Timestamps (kan vara tom)
            series_dict, rows = _normalize_quarterly_financials(qf_df)

            # prisdata → str-nycklar (slipper Streamlit-varning)
            hist = t.history(period="2y")
            price_history = {k: {str(idx): v for idx, v in hist[k].dropna().items()} for k in hist.columns} if not hist.empty else {}

            # 3) bygg resultat — behåll dina gamla fält orörda
            data = {
                "ticker": ticker_symbol,
                "company_info": {
                    "shortName": t.info.get("shortName"),
                    "longName": t.info.get("longName"),
                    "sector": t.info.get("sector"),
                    "industry": t.info.get("industry"),
                    "country": t.info.get("country"),
                    "website": t.info.get("website"),
                    "marketCap": t.info.get("marketCap"),
                    "regularMarketPrice": t.info.get("regularMarketPrice"),
                },
                # originalfälten (kan innehålla Timestamps i nycklar – vi låter dem vara för bakåtkompat)
                "quarterly_financials": (qf_df.to_dict() if qf_df is not None and not qf_df.empty else {}),
                "financials": (t.financials.to_dict() if t.financials is not None and not t.financials.empty else {}),
                "quarterly_balance_sheet": (t.quarterly_balance_sheet.to_dict() if t.quarterly_balance_sheet is not None and not t.quarterly_balance_sheet.empty else {}),
                "balance_sheet": (t.balance_sheet.to_dict() if t.balance_sheet is not None and not t.balance_sheet.empty else {}),
                "quarterly_cashflow": (t.quarterly_cashflow.to_dict() if t.quarterly_cashflow is not None and not t.quarterly_cashflow.empty else {}),
                "cashflow": (t.cashflow.to_dict() if t.cashflow is not None and not t.cashflow.empty else {}),
                "price_history_2y": price_history,
                # nya fält för UI/agent
                "quarters": rows,                         # ← det här behöver din chart
                "quarterly_financials_norm": series_dict, # ← valfritt för analys-agenten
            }
            return data
        except Exception as e:
            return {"error": f"Failed to fetch financial data: {e}"}

    # CrewAI förväntar sig dict/BaseTool. Vi returnerar dict (som innan).
    return {
        "name": "financial_data",
        "description": "Fetch structured quarterly financials and price history.",
        "function": get_financial_data,
    }
