from crewai import Crew
from langchain_openai import OpenAI
from dotenv import load_dotenv
import os
import re
import datetime
import warnings
import io
import contextlib
import json

warnings.filterwarnings("ignore")

class _SilentToolError(Exception):
    pass

from agents.agents.web_search_agent import create_web_search_agent
from agents.agents.financial_research_agent import create_financial_research_agent
from agents.agents.financial_analysis_agent import create_financial_analysis_agent
from agents.agents.report_agent import create_report_agent

from tasks.web_search_task import create_web_search_task
from tasks.financial_research_task import create_financial_research_task
from tasks.financial_analysis_task import create_financial_analysis_task
from tasks.reporting_task import create_chunked_reporting_tasks

from tools import create_search_tool, create_financial_data_tool
from agents.agents.report_utils import format_final_report

load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    raise RuntimeError(
        "Missing OPENAI_API_KEY. Create a .env file with OPENAI_API_KEY=your_key or set the environment variable."
    )

if not os.getenv("SERPAPI_API_KEY"):
    print("Warning: SERPAPI_API_KEY not set. The app will fall back to DuckDuckGo for search.")

# ---------------------------
# Debug logging helpers
# ---------------------------
DEBUG_LOG_FILE = "debug_reporting_outputs.txt"

def log_debug(section_name, content):
    """Append debug info to file with clear separators."""
    try:
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n\n=== {section_name} | {datetime.datetime.now().isoformat()} ===\n")
            if isinstance(content, (list, tuple)):
                for i, item in enumerate(content, 1):
                    f.write(f"\n--- Item {i} ---\n{str(item)}\n")
            else:
                f.write(str(content) + "\n")
    except Exception as e:
        # Keep logging failures from breaking the app
        print(f"[LOGGING WARNING] Could not write debug log for '{section_name}': {e}")

def _text_of(task) -> str:
    out = getattr(task, "output", "")
    return out.raw if hasattr(out, "raw") else str(out or "")

def _extract_bullets(text: str, max_items: int | None = None) -> list[str]:
    lines = []
    for line in (text or "").splitlines():
        l = line.strip()
        if not l:
            continue
        if l.startswith(("-", "•", "*")):
            l = "- " + l.lstrip("•*-").strip()
            lines.append(l)
    if not lines:
        chunks = re.split(r"(?<=[\.\!\?])\s+", text.strip())
        for c in chunks:
            c = c.strip("-•* ").strip()
            if len(c) > 8:
                lines.append(f"- {c}")
    if max_items is not None:
        lines = lines[:max_items]
    return lines

def _dedupe_urls(urls: list[str]) -> list[str]:
    cleaned = []
    seen = set()
    for u in urls:
        u = (u or "").strip().strip(").,];")
        if not u.lower().startswith(("http://", "https://")):
            continue
        key = u.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(u)
    return cleaned
def _text_of(task) -> str:
    out = getattr(task, "output", "")
    return out.raw if hasattr(out, "raw") else str(out or "")

def _extract_bullets(text: str, max_items: int | None = None) -> list[str]:
    lines = []
    for line in (text or "").splitlines():
        l = line.strip()
        if not l:
            continue
        if l.startswith(("-", "•", "*")):
            l = "- " + l.lstrip("•*-").strip()
            lines.append(l)
    if not lines:
        chunks = re.split(r"(?<=[\.\!\?])\s+", text.strip())
        for c in chunks:
            c = c.strip("-•* ").strip()
            if len(c) > 8:
                lines.append(f"- {c}")
    if max_items is not None:
        lines = lines[:max_items]
    return lines

def _dedupe_urls(urls: list[str]) -> list[str]:
    cleaned = []
    seen = set()
    for u in urls:
        u = (u or "").strip().strip(").,];")
        if not u.lower().startswith(("http://", "https://")):
            continue
        key = u.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(u)
    return cleaned


# ---------------------------
# Formatting cleanup helpers
# ---------------------------
def clean_corrupted_numbers(text: str) -> str:
    if not isinstance(text, str):
        return text
    # Ta bort tusentalskomma inne i tal, men rör inte radbrytningar
    text = re.sub(r'(?<=\d),(?=\d)', '', text)
    # Komprimera endast space/tab, inte \n
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def normalize_md_spacing(text: str) -> str:
    """
    Normalize Markdown spacing:
    - Remove trailing spaces per line
    - Limit multiple blank lines to 2
    """
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)  # max 2 linebreaks
    return text.strip()

def _strip_md_links(text: str) -> str:
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)     # ![alt](url) -> alt
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)     # [label](url) -> label
    return text

def _sanitize_line(line: str) -> str:
    line = _strip_md_links(line)
    line = re.sub(r'^\s*#{1,6}\s*', '', line)                  # ta bort # rubriker i början av raden
    line = re.sub(r'[*_`>]+', '', line)                        # enkel MD-städning
    line = re.sub(r'\s+', ' ', line).strip()
    return line

def _looks_like_source(line: str) -> bool:
    l = line.lower()
    if l.startswith(("source:", "källa:", "link:", "url:", "published", "ref:")):
        return True
    if re.fullmatch(r'https?://\S+', line.strip(), flags=re.IGNORECASE):
        return True
    return False

def _extract_bullets_strict(text: str) -> list[str]:
    """Plocka ENDAST ut riktiga bullets/numrerade listor från texten."""
    out = []
    for raw in (text or "").splitlines():
        if re.match(r'^\s*([-•*]|\d+[.)])\s+', raw):
            out.append(raw)
    return out

def _fallback_sentence_bullets(text: str, limit: int) -> list[str]:
    """Om inga bullets hittas: välj meningsbitar som innehåller siffror/kvartal/valuta."""
    # grov men bra nog
    candidates = re.split(r'(?<=[\.\!\?])\s+', text or "")
    keep = []
    pat = re.compile(r'(?:\bQ[1-4]\s?\d{4}\b|\b\d+(\.\d+)?%|\bSEK\b|\bUSD\b|\bEUR\b|\b\d{3,})')
    for c in candidates:
        c = _sanitize_line(c)
        if len(c) < 8: 
            continue
        if pat.search(c) and not _looks_like_source(c):
            keep.append(f"- {c}")
        if len(keep) >= limit:
            break
    return keep

def _normalize_bullets(lines: list[str], max_items: int) -> list[str]:
    out, seen = [], set()
    pending = None  # håll rubrik som slutar med ":" tills vi ser nästa rad

    def _emit(text: str):
        t = text.strip()
        if not t or len(t) < 8:
            return
        if _looks_like_source(t):
            return
        if len(t) > 240:
            t = t[:240].rstrip() + "…"
        key = t.lower()
        if key in seen:
            return
        seen.add(key)
        out.append(f"- {t}")

    for raw in lines:
        l = raw.strip()
        l = re.sub(r'^\s*(?:[-•*]|\d+[.)])\s+', '', l)  # ta bort bullet/nummer i början
        l = _sanitize_line(l)
        # ta bort ensamt bindestreck i slutet
        l = re.sub(r'\s*[-–—]\s*$', '', l)

        if not l:
            continue

        if pending is not None:
            # slå ihop pending rubrik + nuvarande rad
            combined = f"{pending} {l}"
            _emit(combined)
            pending = None
        elif l.endswith(":"):
            # spara rubrik för att slå ihop med nästa rad
            pending = l.rstrip(":").strip() + ":"
        else:
            _emit(l)

        if max_items and len(out) >= max_items:
            break

    # om sista var rubrik utan efterföljare – emit ändå
    if pending is not None and (not max_items or len(out) < max_items):
        _emit(pending.rstrip(":"))

    return out


def _silent_kickoff(crew, label: str):
    """Kör crew.kickoff() tyst; loggar stdout/stderr till debugfilen."""
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        result = crew.kickoff()
    out_txt, err_txt = buf_out.getvalue().strip(), buf_err.getvalue().strip()
    if out_txt:
        log_debug(f"{label} STDOUT", out_txt)
    if err_txt:
        log_debug(f"{label} STDERR", err_txt)
    return result

def resolve_ticker(company: str) -> list[str]:
    c = (company or "").strip().lower()
    # Start-aliasar – fyll gärna på allt eftersom
    aliases = {
        "ericsson": ["ERIC", "ERIC-B.ST", "ERICB.ST", "ERIC A", "ERIC-B"],
        "tesla": ["TSLA"],
        "apple": ["AAPL"],
        "microsoft": ["MSFT"],
        "alphabet": ["GOOGL", "GOOG"],
        "amazon": ["AMZN"],
        "nvidia": ["NVDA"],
        "meta": ["META"],
        "ibm": ["IBM"],
        "intel": ["INTC"],
    }
    # Greppa även “telefonaktiebolaget l m ericsson”
    if "ericsson" in c or "telefonaktiebolaget" in c:
        return aliases["ericsson"]
    return aliases.get(c, [])

_QUART_RE = re.compile(r"\bQ([1-4])\s*([12]\d{3})\b|\b([12]\d{3})\s*Q([1-4])\b", re.I)

def _label_from_ts(x) -> str:
    """Timestamp/str -> 'Q# YYYY'."""
    if isinstance(x, pd.Timestamp):
        p = pd.Period(x, freq="Q")
        return f"Q{p.quarter} {p.year}"
    s = str(x)
    m = _QUART_RE.search(s)
    if m:
        if m.group(1) and m.group(2):
            return f"Q{int(m.group(1))} {int(m.group(2))}"
        if m.group(3) and m.group(4):
            return f"Q{int(m.group(4))} {int(m.group(3))}"
    # fall back: försök tolka datum → period
    try:
        ts = pd.to_datetime(s)
        return _label_from_ts(ts)
    except Exception:
        return s  # lämna oförändrad om inte tolkningsbart

def _parse_quarterly_json_block(*texts: str) -> dict | None:
    """Plocka JSON mellan markörerna om det finns."""
    for t in texts:
        if not t:
            continue
        m = re.search(
            r"===\s*QUARTERLY DATA\s*\(returned\)\s*===\s*(\{.*?\})\s*===\s*END\s*===",
            t,
            flags=re.S | re.I,
        )
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
    return None

def _normalize_quarterly_from_tool(obj) -> dict:
    """
    Normalisera vad 'financial_data_tool' råkar returnera till:
    {
      'quarterly_financials': { 'Total Revenue': {'Q2 2025': 82000000000, ...}, ... }
    }
    Tillåt: DataFrame, dict med Timestamp-nycklar, etc.
    """
    out = {"quarterly_financials": {}}
    if obj is None:
        return out
    # yfinance-liknande: df i obj.get('quarterly_financials') eller direkt df
    qf = obj.get("quarterly_financials") if isinstance(obj, dict) else obj
    if qf is None or (hasattr(qf, "empty") and getattr(qf, "empty")):
        return out

    if isinstance(qf, pd.DataFrame):
        # index=metrics, columns=Timestamps
        metrics = ["Total Revenue", "Net Income", "EBITDA", "Operating Income", "Gross Profit"]
        cols = list(qf.columns)
        labels = [_label_from_ts(c) for c in cols]
        for m in metrics:
            if m in qf.index:
                series = qf.loc[m].to_dict()
                out["quarterly_financials"][m] = {
                    lbl: int(series[dt]) for lbl, dt in zip(labels, cols)
                    if pd.notna(series[dt])
                }
        return out

    if isinstance(qf, dict):
        # Kan vara {metric: {quarter_label|Timestamp: value}} eller {quarter: {metric: value}}
        # Gör om alla quarter-nycklar till 'Q# YYYY'
        # 1) Om nycklar ser ut som metrics
        maybe_metric_keys = list(qf.keys())[:5]
        if any(k for k in maybe_metric_keys if isinstance(k, str) and any(w in k.lower() for w in ["revenue","income","ebit"])):
            norm = {}
            for metric, series in qf.items():
                if isinstance(series, dict):
                    norm[metric] = { _label_from_ts(k): int(v) for k, v in series.items() if v is not None }
            out["quarterly_financials"] = norm
            return out
        # 2) Annars: {quarter: {metric: value}}
        acc = {}
        for qlabel, md in qf.items():
            lbl = _label_from_ts(qlabel)
            if isinstance(md, dict):
                for metric, val in md.items():
                    if val is None: 
                        continue
                    acc.setdefault(metric, {})[lbl] = int(val)
        out["quarterly_financials"] = acc
        return out

    # okänt format → returnera tom struktur
    return out

def _merge_quarterly_payloads(tool_norm: dict, block_obj: dict | None) -> dict:
    """
    Slår ihop:
      - tool_norm: {'quarterly_financials': {...}}
      - block_obj: kan innehålla 'quarterly_financials' och/eller 'quarters' list[dict]
    Returnerar en payload som UI:t gillar.
    """
    result = {"quarterly_financials": {}, "quarters": []}

    # 1) från tool
    if tool_norm and tool_norm.get("quarterly_financials"):
        result["quarterly_financials"] = tool_norm["quarterly_financials"]

    # 2) från block
    if block_obj:
        # a) quarters-lista (redan radformat)
        if isinstance(block_obj.get("quarters"), list):
            result["quarters"] = block_obj["quarters"]
        # b) quarterly_financials från blocket → merge
        if isinstance(block_obj.get("quarterly_financials"), dict):
            for metric, series in block_obj["quarterly_financials"].items():
                result["quarterly_financials"].setdefault(metric, {}).update(series)

        # c) källor (om du vill föra upp dem)
        # (lämnas till din befintliga sources-logic)
    return result

def _extract_quarterly_json_block(*texts: str) -> dict | None:
    """Hittar JSON mellan '=== QUARTERLY DATA (returned) ===' och '=== END ==='."""
    pat = re.compile(
        r"===\s*QUARTERLY DATA\s*\(returned\)\s*===\s*(\{.*?\})\s*===\s*END\s*===",
        re.S | re.I,
    )
    for t in texts:
        if not t:
            continue
        m = pat.search(t)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
    return None

# ---------------------------
# Main pipeline
# ---------------------------
def run_company_analysis(company_name: str):
    """
    Run a comprehensive company analysis using CrewAI agents.
    Returns: (report_text, sources, quarterly_data)
    """
    try:
        # Clear old logs & start
        open(DEBUG_LOG_FILE, "w", encoding="utf-8").close()
        log_debug("START ANALYSIS", f"Company: {company_name}")

        # Initialize LLM
        llm = OpenAI(
            temperature=0.7,
            model="gpt-4o-mini"
        )
        log_debug("LLM CONFIG", {"temperature": 0.7, "model": "gpt-4o-mini"})

        # Create tools
        search_tool = create_search_tool(os.getenv("SERPAPI_API_KEY"))
        financial_data_tool = create_financial_data_tool()
        log_debug("TOOLS CREATED", {
            "search_tool": str(type(search_tool)),
            "financial_data_tool": str(type(financial_data_tool))
        })

        # Create agents
        web_search_agent = create_web_search_agent(llm, tools=[search_tool])
        financial_research_agent = create_financial_research_agent(llm, tools=[financial_data_tool, search_tool])
        financial_analysis_agent = create_financial_analysis_agent(llm, tools=[financial_data_tool, search_tool])
        report_agent = create_report_agent(llm)
        log_debug("AGENTS CREATED", [
            getattr(web_search_agent, "role", "web_search_agent"),
            getattr(financial_research_agent, "role", "financial_research_agent"),
            getattr(financial_analysis_agent, "role", "financial_analysis_agent"),
            getattr(report_agent, "role", "report_agent"),
        ])

        # Create research tasks
        web_search_task = create_web_search_task(web_search_agent, company_name)
        financial_research_task = create_financial_research_task(
            financial_research_agent,
            company_name,
            dependencies=[web_search_task]
        )
        financial_analysis_task = create_financial_analysis_task(
            financial_analysis_agent,
            company_name,
            dependencies=[web_search_task, financial_research_task]
        )
        log_debug("RESEARCH TASKS CREATED", [
            getattr(web_search_task, "description", "web_search_task"),
            getattr(financial_research_task, "description", "financial_research_task"),
            getattr(financial_analysis_task, "description", "financial_analysis_task"),
        ])

        # Run research crew
        research_crew = Crew(
            agents=[
                web_search_agent,
                financial_research_agent,
                financial_analysis_agent
            ],
            tasks=[
                web_search_task,
                financial_research_task,
                financial_analysis_task
            ],
            verbose=True
        )
        research_result = _silent_kickoff(research_crew, "RESEARCH CREW")
        log_debug("RESEARCH CREW RAW OUTPUTS", [
            t.raw if hasattr(t, "raw") else str(t) for t in getattr(research_result, "tasks_output", [])
        ])

        # Collect research sources
        sources = []
        for task in [web_search_task, financial_research_task, financial_analysis_task]:
            txt = _text_of(task)
            if txt:
                sources.extend(re.findall(r'https?://[^\s\)\]]+', txt))
        sources = _dedupe_urls(sources)
        log_debug("COLLECTED SOURCES (strict dedupe)", sources)

        web_text = _text_of(web_search_task)
        finres_text = _text_of(financial_research_task)
        finanal_text = _text_of(financial_analysis_task)

        raw_insights = _extract_bullets_strict(web_text + "\n" + finres_text)
        raw_highlights = _extract_bullets_strict(finanal_text)

        key_insights_bullets = _normalize_bullets(raw_insights, max_items=4)
        if not key_insights_bullets:
            key_insights_bullets = _fallback_sentence_bullets(web_text + "\n" + finres_text, limit=4)

        financial_highlights_bullets = _normalize_bullets(raw_highlights, max_items=6)
        if not financial_highlights_bullets:
            financial_highlights_bullets = _fallback_sentence_bullets(finanal_text, limit=6)


        reporting_tasks = create_chunked_reporting_tasks(
            agent=report_agent,
            company_name=company_name,
            dependencies=[web_search_task, financial_research_task, financial_analysis_task],
            sources=sources
        )

        # Run reporting crew
        reporting_crew = Crew(
            agents=[report_agent],
            tasks=reporting_tasks,
            verbose=True
        )
        reporting_result = _silent_kickoff(reporting_crew, "REPORTING CREW")
        raw_reporting_outputs = [t.raw if hasattr(t, "raw") else str(t) for t in getattr(reporting_result, "tasks_output", [])]
        log_debug("REPORTING CREW RAW OUTPUTS", raw_reporting_outputs)

        # Samla bara Exec Summary & Recommendations från rapportagenten
        section_outputs = {"Executive Summary": "", "Recommendations": ""}
        for result in reporting_result.tasks_output:
            output_text = result.raw if hasattr(result, "raw") else str(result)
            if "--- End of Executive Summary ---" in output_text:
                section_outputs["Executive Summary"] = output_text
            elif "--- End of Recommendations ---" in output_text:
                section_outputs["Recommendations"] = output_text

        # Bygg slutrapporten med deterministiska sektioner
        parts = []
        if section_outputs["Executive Summary"]:
            parts.append(section_outputs["Executive Summary"].strip())

        if key_insights_bullets:
            parts.append(
            "Key Research Insights\n"
            + "\n".join(key_insights_bullets)
            + "\n\n--- End of Key Research Insights ---"
        )

        if financial_highlights_bullets:
            parts.append(
            "Financial Analysis Highlights\n"
            + "\n".join(financial_highlights_bullets)
            + "\n\n--- End of Financial Analysis ---"
        )

        if section_outputs["Recommendations"]:
            parts.append(section_outputs["Recommendations"].strip())

        if sources:
            parts.append("Sources\n" + "\n".join(f"- {u}" for u in sources) + "\n\n--- End of Report ---")

        final_report_raw = "\n\n".join(parts)
        final_report = normalize_md_spacing(clean_corrupted_numbers(final_report_raw))
        log_debug("FINAL REPORT (raw)", final_report_raw)
        log_debug("FINAL REPORT (cleaned)", final_report)

        # === Quarterly data: först försök hämta från analysens JSON‑block ===
        block_obj = _extract_quarterly_json_block(
            finres_text,
            finanal_text,
            final_report  # om du senare väljer att inkludera blocket i rapporten
        )

        quarterly_data = None

        if block_obj:
            quarterly_data = {
                # standardnycklar som app.py/quarterly_df förväntar sig
                "quarterly_financials": block_obj.get("quarterly_financials", {}),
                "quarters": block_obj.get("quarters", []),
            }
            log_debug("QUARTERLY DATA (from JSON block)", {
                "series_keys": list(quarterly_data["quarterly_financials"].keys()),
                "rows": len(quarterly_data["quarters"]),
            })
        else:
            # fallback: kör verktyget precis som tidigare
            try:
                if hasattr(financial_data_tool, "run"):
                    tool_raw = financial_data_tool.run(company_name)
                elif callable(financial_data_tool):
                    tool_raw = financial_data_tool(company_name)
                elif isinstance(financial_data_tool, dict) and callable(financial_data_tool.get("function")):
                    tool_raw = financial_data_tool["function"](company_name)
                else:
                    raise TypeError("Unsupported financial_data_tool type")

                # mappa till standardnycklar om möjligt
                if isinstance(tool_raw, dict):
                    quarterly_data = {
                        "quarterly_financials": tool_raw.get("quarterly_financials_norm")
                                              or tool_raw.get("quarterly_financials")
                                              or {},
                        "quarters": tool_raw.get("quarters") or [],
                    }
                else:
                    quarterly_data = None
                log_debug("QUARTERLY DATA (from tool)", quarterly_data or "None")
            except Exception as e:
                log_debug("QUARTERLY DATA (tool) ERROR", str(e))
                quarterly_data = None

        log_debug("QUARTERLY DATA (returned)", quarterly_data if quarterly_data is not None else "No data")


        return final_report, sources, quarterly_data

    except Exception as e:
        log_debug("FATAL ERROR", str(e))
        return f"Error analyzing {company_name}: {str(e)}", [], None


def extract_sources_from_outputs(crew_result):
    """
    Extract sources from crew execution results.
    """
    all_sources = []
    tasks_outputs_list = []
    if hasattr(crew_result, "tasks_output") and crew_result.tasks_output:
        try:
            tasks_outputs_list = [t.raw if hasattr(t, "raw") else str(t) for t in crew_result.tasks_output]
        except Exception:
            tasks_outputs_list = []
    elif isinstance(crew_result, dict):
        tasks_outputs_list = [
            crew_result.get("web_search_task", ""),
            crew_result.get("financial_research_task", ""),
            crew_result.get("financial_analysis_task", ""),
            crew_result.get("reporting_task", ""),
        ]

    for output in tasks_outputs_list[:2]:
        if output:
            urls = re.findall(r'https?://[^\s\)]+', output)
            all_sources.extend(urls)

            source_patterns = [
                r'Source:\s*([^\n]+)',
                r'According to\s+([^,\n]+)',
                r'from\s+([^,\n]+)',
                r'published\s+by\s+([^,\n]+)',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Report|News|Press|Media))',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Q[0-9]+\s+[0-9]{4})',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+[0-9]{4}\s+(?:Report|Financial|Earnings))'
            ]

            for pattern in source_patterns:
                matches = re.findall(pattern, output, re.IGNORECASE)
                all_sources.extend(matches)

    cleaned_sources = []
    seen_sources = set()

    for src in all_sources:
        src = src.strip()
        if len(src) < 10:
            continue
        if src.endswith((':', ',', '.', ')', ']', '}')):
            src = src.rstrip(':,.)]}').strip()

        normalized = src.lower().replace('*', '').replace('(', '').replace(')', '').strip()
        if normalized not in seen_sources and src and len(src) >= 10:
            cleaned_sources.append(src)
            seen_sources.add(normalized)

    return cleaned_sources if cleaned_sources else ["Sources extracted from agent outputs"]


if __name__ == "__main__":
    company_name = "Ericsson"
    report, sources, quarterly_data = run_company_analysis(company_name)

    print("\n--- Final Report ---\n")
    print(report)

    print("\n--- Quarterly Data Available ---\n")
    if quarterly_data is not None:
        print("Quarterly financial data retrieved successfully")
        print(quarterly_data.head() if hasattr(quarterly_data, 'head') else quarterly_data)
    else:
        print("No quarterly data available")





