import streamlit as st
from pathlib import Path
from main import run_company_analysis, DEBUG_LOG_FILE

st.set_page_config(page_title="Company Analyzer", layout="wide")
st.title("📊 Company Analyzer")

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

        # Download full report as markdown
        st.download_button(
            "⬇️ Download report (.md)",
            data=report.encode("utf-8"),
            file_name=f"{company.replace(' ', '_')}_report.md",
            mime="text/markdown"
        )

    with col2:
        st.subheader("Sources")
        if sources:
            for u in sources:
                st.markdown(f"- [{u}]({u})")
        else:
            st.write("_No sources available._")

        # Chart (if any)
        try:
            from chart_utils import make_quarterly_chart
            fig = make_quarterly_chart(quarterly_data)
            if fig:
                st.subheader("Quarterly Revenue")
                st.pyplot(fig, use_container_width=True)
            else:
                st.info("No chartable quarterly data.")
        except Exception as e:
            st.caption(f"Chart unavailable: {e}")

        # Debug log
        with st.expander("Debug log (last ~5k chars)"):
            try:
                text = Path(DEBUG_LOG_FILE).read_text(encoding="utf-8")
                st.code(text[-5000:] if len(text) > 5000 else text)
            except Exception:
                st.write("_No debug log available._")
