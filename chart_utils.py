# chart_utils.py
from __future__ import annotations

import json
import re
import pandas as pd
import altair as alt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

# =========================
# 1) Robust parser + enkel Altair-linje
# =========================

METRIC_ALIASES = {
    "revenue": ["total revenue", "revenue", "net sales", "sales", "turnover"],
    "net_income": ["net income", "net profit", "profit"],
    "ebitda": ["ebitda", "adjusted ebitda"],
}

def _normalize_metric_name(name: str) -> str | None:
    n = str(name).strip().lower()
    for std, alts in METRIC_ALIASES.items():
        if n == std or any(n == a for a in alts):
            return std
    return None

def _quarter_to_ts(q):
    import re, pandas as pd
    s = str(q).strip().upper()
    m1 = re.search(r"(Q[1-4])\s*[-_/ ]?\s*(\d{4})", s)
    m2 = re.search(r"(\d{4})\s*[-_/ ]?\s*Q([1-4])", s)
    if m1:
        qn = m1.group(1)[1]
        yy = m1.group(2)
        s_norm = f"{yy}Q{qn}"
    elif m2:
        s_norm = f"{m2.group(1)}Q{m2.group(2)}"
    else:
        # tillåt råa datumsträngar; försök parse:a
        try:
            return pd.to_datetime(s)
        except Exception:
            raise ValueError(f"Kan inte tolka kvartal: {q}")
    return pd.Period(s_norm, freq="Q").to_timestamp(how="end")

def _ensure_metric_index_quarter_columns(qf_data) -> pd.DataFrame:
    """
    Accepterar DataFrame/dict i olika orienteringar och returnerar
    df med index = metrics, columns = quarters.
    """
    import re, pandas as pd
    if isinstance(qf_data, pd.DataFrame):
        df = qf_data.copy()
    elif isinstance(qf_data, dict):
        df = pd.DataFrame(qf_data)
        # Om kolumner inte ser ut som kvartal men index gör det → transponera inte.
        # Om varken kolumner eller index ser ut som kvartal, låt den vara; nästa steg hanterar det.
    else:
        df = pd.DataFrame(qf_data)

    def looks_like_quarter(x):
        return bool(re.search(r"Q[1-4].*\d{4}|\d{4}.*Q[1-4]", str(x), re.I))

    cols_quarter = any(looks_like_quarter(c) for c in df.columns)
    idx_quarter  = any(looks_like_quarter(i) for i in df.index)

    # Vill ha quarters som columns → om index verkar vara quarters, transponera
    if idx_quarter and not cols_quarter:
        df = df.T

    return df


REQUIRED_COLS = ["quarter", "revenue"]

def _coerce_numeric(series):
    return pd.to_numeric(series, errors="coerce")

def quarterly_df(raw):
    """
    Returnerar DataFrame med kolumner: quarter (datetime64), revenue[, net_income, ebitda]
    Stödjer följande inputs:
      - list[dict] med nycklar: 'quarter','revenue' (ev. 'net_income','ebitda')
      - dict med nyckel 'quarters' -> list[dict]
      - dict med nyckel 'quarterly_financials' -> (DataFrame/dict)
          * Antas vara index=metrics, columns=quarters ELLER vice versa (auto-normaliseras)
      - dict som mappar quarter -> {metric: value} eller metric -> {quarter: value}
      - str som innehåller '=== QUARTERLY DATA (returned) ===' följt av JSON
    """
    import json, re, pandas as pd

    data = raw

    # 0) Om en lång text: extrahera JSON-block efter rubriken
    if isinstance(raw, str):
        m = re.search(
            r"===\s*QUARTERLY DATA\s*\(returned\).*?===\s*(.*?)\s*(?:(?:===)|\Z)",
            raw, flags=re.S | re.I
        )
        if m:
            candidate = m.group(1).strip()
            if candidate.upper() == "OK":
                raise ValueError("QUARTERLY DATA är 'OK' (inga data ännu).")
            try:
                data = json.loads(candidate)
            except json.JSONDecodeError:
                raise ValueError("Kunde inte tolka QUARTERLY DATA som JSON.")

    # 1) Fall: {"quarters": [...]}
    if isinstance(data, dict) and "quarters" in data:
        rows = data["quarters"]
        df = pd.DataFrame(rows)

    # 2) Fall: {"quarterly_financials": <df|dict>} (din nuvarande struktur)
    elif isinstance(data, dict) and "quarterly_financials" in data:
        qf = data["quarterly_financials"]
        qf_df = _ensure_metric_index_quarter_columns(qf)

        # Bygg radbaserad tabell: en rad per quarter
        out_rows = []
        for q in qf_df.columns:
            row = {"quarter": q}
            # hitta alias per metric
            for std_name, aliases in METRIC_ALIASES.items():
                # leta i index efter någon alias
                for ix in qf_df.index:
                    norm = _normalize_metric_name(ix)
                    if norm == std_name:
                        val = qf_df.loc[ix, q]
                        row[std_name] = pd.to_numeric(val, errors="coerce")
                # om inget träff: lämna tomt
            out_rows.append(row)
        df = pd.DataFrame(out_rows)

    # 3) Fall: dict som antingen {quarter: {metric: val}} eller {metric: {quarter: val}}
    elif isinstance(data, dict):
        # Heuristik: om nycklar ser ut som quarters → tolka som {quarter: {...}}
        keys = list(data.keys())
        def looks_like_quarter(x):
            return bool(re.search(r"Q[1-4].*\d{4}|\d{4}.*Q[1-4]", str(x), re.I))
        if any(looks_like_quarter(k) for k in keys):
            # { "Q2 2025": {"Revenue": 82e9, ...}, ... }
            rows = []
            for q, metrics in data.items():
                row = {"quarter": q}
                if isinstance(metrics, dict):
                    for k, v in metrics.items():
                        norm = _normalize_metric_name(k)
                        if norm:
                            row[norm] = pd.to_numeric(v, errors="coerce")
                rows.append(row)
            df = pd.DataFrame(rows)
        else:
            # antag {metric: {quarter: val}}
            qf_df = _ensure_metric_index_quarter_columns(data)
            out_rows = []
            for q in qf_df.columns:
                row = {"quarter": q}
                for ix in qf_df.index:
                    norm = _normalize_metric_name(ix)
                    if norm:
                        row[norm] = pd.to_numeric(qf_df.loc[ix, q], errors="coerce")
                out_rows.append(row)
            df = pd.DataFrame(out_rows)

    # 4) Fall: list[dict]
    elif isinstance(data, list):
        df = pd.DataFrame(data)

    else:
        raise ValueError(f"Oväntat format för quarterly data: {type(data).__name__}")

    if "quarter" not in df.columns:
        raise ValueError("Saknar kolumn 'quarter' efter normalisering.")

    # Tidsaxel
    df["quarter"] = df["quarter"].apply(_quarter_to_ts)

    # Säkerställ numerik
    for c in ["revenue", "net_income", "ebitda"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Sortera och rensa tomma rader
    df = df.sort_values("quarter").reset_index(drop=True)
    if {"revenue", "net_income", "ebitda"}.isdisjoint(df.columns):
        # inga kända metriker hittades – låt altair-del hantera detta
        pass

    return df


def revenue_chart(df: pd.DataFrame):
    """Enkel Altair-linje för revenue."""
    tooltip_cols = [c for c in ["quarter", "revenue", "net_income", "ebitda"] if c in df.columns]
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("quarter:T", title="Quarter"),
            y=alt.Y("revenue:Q", title="Revenue (USD, bn)"),
            tooltip=tooltip_cols,
        )
        .properties(height=280)
    )

def metric_chart(df: pd.DataFrame, metric: str, title: str | None = None):
    """Generisk Altair-tidsserie för valfri metrikkolumn i df."""
    if metric not in df.columns:
        raise ValueError(f"Metriken '{metric}' finns inte i DataFrame.")
    ttl = title or metric.replace("_", " ").title()
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("quarter:T", title="Quarter"),
            y=alt.Y(f"{metric}:Q", title=ttl),
            tooltip=[alt.Tooltip("quarter:T")] + [c for c in df.columns if c != "quarter"]
        )
        .properties(height=300)
    )


# =========================
# 2) Din befintliga Matplotlib‑fallback (oförändrad)
# =========================

def make_quarterly_chart(data):
    """Return a matplotlib figure for revenue by quarter if possible, else None."""
    try:
        if data is None:
            return None
        if isinstance(data, dict) and data.get("error"):
            return None

        df = data
        cols = list(getattr(df, "columns", []))
        if not cols:
            return None

        lower = {c.lower(): c for c in cols}
        date_col = next((lower[k] for k in ["date", "quarter", "period", "fiscal_quarter"] if k in lower), None)
        rev_col = None
        for c in cols:
            lc = c.lower()
            if any(k in lc for k in ["revenue", "net sales", "sales", "turnover"]):
                rev_col = c
                break

        if not date_col or not rev_col:
            return None

        dfx = df[[date_col, rev_col]].dropna()
        if dfx.empty:
            return None

        fig, ax = plt.subplots()
        ax.plot(dfx[date_col], dfx[rev_col], marker="o")
        ax.set_title("Revenue by Quarter")
        ax.set_xlabel(date_col)
        ax.set_ylabel(rev_col)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return fig
    except Exception:
        return None

# =========================
# 3) Rättade Plotly‑hjälpare (standard: index=metric, columns=quarter)
# =========================

def _ensure_metric_index_quarter_columns(qf_data) -> pd.DataFrame:
    """
    Gör om till DataFrame med index=metrics och columns=quarters om möjligt.
    Accepterar dict, list, DataFrame i olika orienteringar.
    """
    if isinstance(qf_data, pd.DataFrame):
        df = qf_data.copy()
    elif isinstance(qf_data, dict):
        # Om det ser ut som {metric: {quarter: value}}
        # blir index=metric, columns=quarter
        df = pd.DataFrame(qf_data)
        # Om vi istället fick {quarter: {metric: value}}, transponera
        # Heuristik: om kolumnnamn ser ut som kvartal, så är quarters=columns redan
        # annars transponera
        sample_cols = list(df.columns)[:4]
        looks_like_quarter = any(re.search(r"Q[1-4].*\d{4}|\d{4}.*Q[1-4]", str(c), re.I) for c in sample_cols)
        if not looks_like_quarter:
            df = df.T
    else:
        # Försök en generisk to-DataFrame
        df = pd.DataFrame(qf_data)

    # Om quarters ligger i index och metrics i kolumner -> transponera
    if any(re.search(r"Q[1-4].*\d{4}|\d{4}.*Q[1-4]", str(i), re.I) for i in df.index):
        df = df.T

    return df

def create_quarterly_comparison_chart(quarterly_data: dict, company_name: str):
    """
    Jämför flera nyckelmetrikers utveckling över de senaste 8 kvartalen.
    Antagande: index=metrics, columns=quarters (nyast -> äldst eller tvärtom; vi sorterar).
    """
    try:
        if "quarterly_financials" not in quarterly_data:
            return None

        qf_df = _ensure_metric_index_quarter_columns(quarterly_data["quarterly_financials"])

        # Sortera kvartal efter tidsordning via heuristik
        def _q_key(q):
            s = str(q)
            m1 = re.search(r"Q([1-4]).*?(\d{4})", s)
            m2 = re.search(r"(\d{4}).*?Q([1-4])", s)
            if m1:
                return (int(m1.group(2)), int(m1.group(1)))
            if m2:
                return (int(m2.group(1)), int(m2.group(2)))
            return (0, 0)

        quarters_sorted = sorted(qf_df.columns, key=_q_key)
        latest_quarters = quarters_sorted[-8:]  # senaste 8

        metrics = ["Total Revenue", "Net Income", "Gross Profit", "Operating Income"]

        # Bygg DataFrame för subplots
        df_plot = []
        for q in latest_quarters:
            row = {"Quarter": q}
            for m in metrics:
                if m in qf_df.index:
                    row[m] = qf_df.loc[m, q]
            df_plot.append(row)
        df = pd.DataFrame(df_plot)

        # Skala till miljarder
        for col in metrics:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce") / 1e9

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Revenue (Billions)", "Net Income (Billions)",
                            "Gross Profit (Billions)", "Operating Income (Billions)"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        metric_list = metrics
        for i, metric in enumerate(metric_list):
            if metric in df.columns:
                r = (i // 2) + 1
                c = (i % 2) + 1
                fig.add_bar(
                    x=df["Quarter"], y=df[metric], name=metric,
                    hovertemplate=f'{metric}: $%{{y:.2f}}B<br>Quarter: %{{x}}<extra></extra>',
                    row=r, col=c
                )

        fig.update_layout(
            title=f"{company_name} - Quarterly Financial Performance Comparison",
            height=600,
            showlegend=False,
            title_x=0.5
        )
        fig.update_xaxes(tickangle=45)
        return fig

    except Exception as e:
        print(f"Error creating chart: {str(e)}")
        return None

def create_year_over_year_chart(quarterly_data: dict, company_name: str):
    """
    Jämför senaste kvartalet vs samma kvartal för ett år sedan.
    Antagande: index=metrics, columns=quarters.
    """
    try:
        if "quarterly_financials" not in quarterly_data:
            return None

        qf_df = _ensure_metric_index_quarter_columns(quarterly_data["quarterly_financials"])

        def _q_key(q):
            s = str(q)
            m1 = re.search(r"Q([1-4]).*?(\d{4})", s)
            m2 = re.search(r"(\d{4}).*?Q([1-4])", s)
            if m1:
                return (int(m1.group(2)), int(m1.group(1)))
            if m2:
                return (int(m2.group(1)), int(m2.group(2)))
            return (0, 0)

        quarters_sorted = sorted(qf_df.columns, key=_q_key)
        if len(quarters_sorted) < 5:
            return None

        latest_q = quarters_sorted[-1]
        year_ago_q = quarters_sorted[-5]  # fyra kvartal bak

        metrics = ["Total Revenue", "Net Income", "Gross Profit", "Operating Income"]
        metric_names = []
        current_values = []
        previous_values = []

        for m in metrics:
            if m in qf_df.index:
                cur = pd.to_numeric(qf_df.loc[m, latest_q], errors="coerce")
                prev = pd.to_numeric(qf_df.loc[m, year_ago_q], errors="coerce")
                if pd.notna(cur) and pd.notna(prev):
                    metric_names.append(m.replace("Total ", ""))
                    current_values.append(cur / 1e9)
                    previous_values.append(prev / 1e9)

        if not current_values:
            return None

        fig = go.Figure()
        fig.add_bar(
            name=f"{latest_q}",
            x=metric_names, y=current_values,
            hovertemplate="%{x}: $%{y:.2f}B<br>Quarter: " + str(latest_q) + "<extra></extra>"
        )
        fig.add_bar(
            name=f"{year_ago_q}",
            x=metric_names, y=previous_values,
            hovertemplate="%{x}: $%{y:.2f}B<br>Quarter: " + str(year_ago_q) + "<extra></extra>"
        )

        fig.update_layout(
            title=f"{company_name} - Year-over-Year Comparison<br>{latest_q} vs {year_ago_q}",
            xaxis_title="Financial Metrics",
            yaxis_title="Amount (Billions USD)",
            barmode="group",
            height=500,
            title_x=0.5
        )
        return fig

    except Exception as e:
        print(f"Error creating year-over-year chart: {str(e)}")
        return None

def create_simple_quarterly_summary(quarterly_data: dict, company_name: str):
    """
    Enkel sammanfattning av senaste 4 kvartal.
    Antagande: index=metrics, columns=quarters.
    """
    try:
        if "quarterly_financials" not in quarterly_data:
            return None

        qf_df = _ensure_metric_index_quarter_columns(quarterly_data["quarterly_financials"])

        def _q_key(q):
            s = str(q)
            m1 = re.search(r"Q([1-4]).*?(\d{4})", s)
            m2 = re.search(r"(\d{4}).*?Q([1-4])", s)
            if m1:
                return (int(m1.group(2)), int(m1.group(1)))
            if m2:
                return (int(m2.group(1)), int(m2.group(2)))
            return (0, 0)

        quarters_sorted = sorted(qf_df.columns, key=_q_key)
        latest_quarters = quarters_sorted[-4:]

        key_metrics = ["Total Revenue", "Net Income", "Gross Profit", "Operating Income"]

        summary_rows = []
        for metric in key_metrics:
            if metric in qf_df.index:
                row = {"Metric": metric.replace("Total ", "")}
                for q in latest_quarters:
                    val = pd.to_numeric(qf_df.loc[metric, q], errors="coerce")
                    row[str(q)] = f"${val/1e9:.2f}B" if pd.notna(val) else "N/A"
                summary_rows.append(row)

        if not summary_rows:
            return None

        return pd.DataFrame(summary_rows)

    except Exception as e:
        print(f"Error creating summary table: {str(e)}")
        return None
