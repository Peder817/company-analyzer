import streamlit as st
from pathlib import Path
from main import run_company_analysis, DEBUG_LOG_FILE

st.set_page_config(page_title="Company Analyzer", layout="wide")
st.title("📊 Company Analyzer")

if "analysis" not in st.session_state:
    st.session_state["analysis"] = None


def parse_sections(report: str) -> dict:
    """Plocka ut sektioner via våra markörer/rubriker."""
    import re
    out = {
        "Executive Summary": "",
        "Key Research Insights": "",
        "Financial Analysis Highlights": "",
        "Recommendations": "",
        "Sources": "",
    }
    if not report:
        return out

    def grab(name, end_marker):
        # 1) försök marker
        m = re.search(rf"(?im)^\s*{re.escape(name)}\s*$", report)
        if m:
            start = m.end()
            end = report.find(end_marker, start)
            if end != -1:
                return report[m.start(): end + len(end_marker)].strip()
        # 2) fallback: rubrik till nästa rubrik
        heads = [
            r"(?im)^\s*Executive Summary\s*$",
            r"(?im)^\s*Key Research Insights\s*$",
            r"(?im)^\s*Financial Analysis Highlights\s*$",
            r"(?im)^\s*Recommendations\s*$",
            r"(?im)^\s*Sources\s*$",
        ]
        m2 = re.search(rf"(?im)^\s*{re.escape(name)}\s*$", report)
        if not m2:
            return ""
        start = m2.end()
        nextpos = len(report)
        for h in heads:
            m3 = re.search(h, report[start:])
            if m3:
                cand = start + m3.start()
                if cand < nextpos:
                    nextpos = cand
        body = report[m2.start():nextpos].strip()
        return (body + f"\n\n{end_marker}").strip() if body else ""

    out["Executive Summary"] = grab("Executive Summary", "--- End of Executive Summary ---")
    out["Key Research Insights"] = grab("Key Research Insights", "--- End of Key Research Insights ---")
    out["Financial Analysis Highlights"] = grab("Financial Analysis Highlights", "--- End of Financial Analysis ---")
    out["Recommendations"] = grab("Recommendations", "--- End of Recommendations ---")
    # Sources: visa alltid separat i UI från käll-listan vi får tillbaka
    return out

company = st.text_input("Company", value="Ericsson", help="Ex: Ericsson, Tesla, Apple")
run = st.button("Generate report", type="primary")

if run and company.strip():
    with st.spinner("Analyzing…"):
        report, sources, quarterly_data = run_company_analysis(company.strip())
    # spara i sessionen så det överlever reruns
    st.session_state["analysis"] = {
        "company": company.strip(),
        "report": report,
        "sources": sources,
        "quarterly_data": quarterly_data,
    }

data = st.session_state.get("analysis")
if data:
    company_saved = data["company"]
    report = data["report"]
    sources = data["sources"]
    quarterly_data = data["quarterly_data"]

    sections = parse_sections(report)

    # ===== Layout =====
    col1, col2 = st.columns([2, 1])

    with col1:
        if sections["Executive Summary"]:
            st.subheader("Executive Summary")
            st.markdown(sections["Executive Summary"])

        if sections["Key Research Insights"]:
            st.subheader("Key Research Insights")
            st.markdown(sections["Key Research Insights"])

        if sections["Financial Analysis Highlights"]:
            st.subheader("Financial Analysis Highlights")
            st.markdown(sections["Financial Analysis Highlights"])

        if sections["Recommendations"]:
            st.subheader("Recommendations")
            st.markdown(sections["Recommendations"])

        st.download_button(
            "⬇️ Download report (.md)",
            data=report.encode("utf-8"),
            file_name=f"{company_saved.replace(' ', '_')}_report.md",
            mime="text/markdown"
        )

    with col2:
        st.subheader("Sources")
        if sources:
            for u in sources:
                st.markdown(f"- [{u}]({u})")
        else:
            st.write("_No sources available._")

        # === Chart (metric selector + fallback) ===
        st.subheader("Quarterly chart")

        with st.expander("Chart debug", expanded=False):
            st.write("Har explicit quarterly_data?", isinstance(quarterly_data, dict))
            if isinstance(quarterly_data, dict):
                # visa bara det vi bryr oss om
                st.json({
                    "quarterly_financials": quarterly_data.get("quarterly_financials") or quarterly_data.get("quarterly_financials_norm") or {},
                    "quarters": quarterly_data.get("quarters", []),
                })

        try:
            import chart_utils as cu

            # Välj bästa källa: quarters-lista om finns, annars hela dicten
            q_payload = None
            if isinstance(quarterly_data, dict):
                if quarterly_data.get("quarters"):
                    q_payload = {"quarters": quarterly_data["quarters"]}
                else:
                    q_payload = quarterly_data

            df = cu.quarterly_df(q_payload if q_payload is not None else report)

            candidate_metrics = ["revenue", "net_income", "ebitda"]
            available = [m for m in candidate_metrics if m in df.columns]

            if not available:
                st.info("Hittade inga metriker att plotta.")
            else:
                c1, c2 = st.columns([1, 1.2])
                with c1:
                    metric = st.radio("Metric", available, index=0, horizontal=True, key="metric_selector")
                with c2:
                    smooth = st.toggle("7‑punkters glidande medelvärde", value=False, key="metric_smooth")

                df_plot = df.sort_values("quarter").reset_index(drop=True).copy()
                title = metric.replace("_"," ").title()
                if smooth:
                    smoothed_col = f"{metric}_smoothed"
                    df_plot[smoothed_col] = df_plot[metric].rolling(window=7, min_periods=1).mean()
                    df_plot = df_plot.rename(columns={smoothed_col: metric})
                    title += " (smoothed)"

                if hasattr(cu, "metric_chart"):
                    st.altair_chart(cu.metric_chart(df_plot, metric=metric, title=title), use_container_width=True)
                else:
                    st.altair_chart(cu.revenue_chart(df_plot), use_container_width=True)

        except Exception as e:
            st.warning(f"Kunde inte rita diagram: {e}")

        # Debug log
        with st.expander("Debug log (last ~5k chars)"):
            try:
                text = Path(DEBUG_LOG_FILE).read_text(encoding="utf-8")
                st.code(text[-5000:] if len(text) > 5000 else text)
            except Exception:
                st.write("_No debug log available._")

if st.button("Reset page"):
    st.session_state["analysis"] = None
    st.rerun()