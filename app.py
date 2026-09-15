import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from ai_engine import understand_question, generate_insight

# ============================================================
# CONVERSATIONAL SESSION STATE
# ============================================================

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []


def build_contextual_question(current_question):
    """Add recent analysis context so follow-up questions can be understood."""
    history = st.session_state.get("conversation_history", [])

    if not history:
        return current_question

    recent = history[-3:]
    context_lines = [
        "You are answering a follow-up question in an ongoing data-analysis conversation.",
        "Use the previous analysis context when the current question is ambiguous.",
        "Keep using the same dataset and relevant grouping/filter context unless the user explicitly changes it.",
        "Previous conversation context:",
    ]

    for i, item in enumerate(recent, 1):
        context_lines.append(
            f"Turn {i}: User question: {item['question']} | "
            f"Analysis plan: {item.get('plan', {})} | "
            f"Insight: {item.get('insight', '')}"
        )

    context_lines.append(f"Current user question: {current_question}")
    return "\n".join(context_lines)


def add_conversation_turn(question, plan, insight, analysis_text):
    history = st.session_state.setdefault("conversation_history", [])
    history.append({
        "question": question,
        "plan": plan,
        "insight": insight,
        "analysis": analysis_text[:2500],
    })
    # Keep the session lightweight while preserving recent context.
    if len(history) > 8:
        del history[:-8]

# ============================================================
# PROFESSIONAL DASHBOARD STYLING
# ============================================================

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}
.hero {
    padding: 1.5rem 1.7rem;
    border-radius: 18px;
    border: 1px solid rgba(49,51,63,.14);
    margin-bottom: 1.3rem;
    background: linear-gradient(135deg, rgba(240,244,255,.95), rgba(248,250,252,.98));
    box-shadow: 0 4px 18px rgba(0,0,0,.04);
}
.hero h1 { margin: 0 0 .4rem 0; font-size: 2.35rem; letter-spacing: -.035em; }
.hero p { margin: 0; color: #5f6368; font-size: 1.02rem; line-height: 1.55; }
.section-card {
    padding: 1rem 1.15rem;
    border: 1px solid rgba(49,51,63,.12);
    border-radius: 14px;
    margin: .6rem 0 1.1rem 0;
    background: rgba(255,255,255,.5);
}
.small-muted { color: #6b7280; font-size: .88rem; }
.nav-title { font-size: 1.08rem; font-weight: 750; margin-bottom: .2rem; }
.nav-subtitle { font-size: .82rem; color: #8b92a3; margin-bottom: 1rem; }
.nav-item {
    display: block;
    padding: .5rem .68rem;
    margin: .2rem 0;
    border-radius: 9px;
    text-decoration: none !important;
    color: inherit !important;
    border: 1px solid transparent;
    transition: background .15s ease, border-color .15s ease;
}
.nav-item:hover {
    border-color: rgba(49,51,63,.14);
    background: rgba(49,51,63,.055);
}
.sidebar-status {
    padding: .75rem;
    border-radius: 10px;
    border: 1px solid rgba(49,51,63,.14);
    margin-top: 1rem;
    font-size: .85rem;
}
div[data-testid="stMetric"] {
    border: 1px solid rgba(49,51,63,.13);
    padding: 1rem 1.05rem;
    border-radius: 14px;
    min-height: 112px;
    background: rgba(255,255,255,.45);
    box-shadow: 0 2px 10px rgba(0,0,0,.035);
}
[data-testid="stMetricLabel"] { font-size: .82rem; font-weight: 650; }
[data-testid="stMetricValue"] { font-size: 1.55rem; font-weight: 750; }
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(49,51,63,.08);
}
div[data-testid="stPlotlyChart"] {
    border: 1px solid rgba(49,51,63,.09);
    border-radius: 14px;
    padding: .35rem;
    background: rgba(255,255,255,.25);
}
.stButton > button, .stDownloadButton > button {
    border-radius: 9px;
    font-weight: 650;
    min-height: 2.5rem;
}
.stTextInput input, .stTextArea textarea {
    border-radius: 9px;
}
[data-testid="stExpander"] {
    border-radius: 12px;
    border: 1px solid rgba(49,51,63,.13);
}
hr { margin: 1.25rem 0; }
</style>
""", unsafe_allow_html=True)



# ============================================================
# PHASE 6 — AI DASHBOARD INTELLIGENCE HELPERS
# ============================================================

def format_metric(value):
    """Format numeric dashboard values consistently."""
    if pd.isna(value):
        return "—"
    if isinstance(value, (int, float)):
        return f"{value:,.2f}"
    return str(value)


def add_phase6_kpis(dataframe):
    """Render the Phase 11 executive KPI dashboard from filtered data."""
    st.markdown('<div id="executive"></div>', unsafe_allow_html=True)
    st.subheader("📊 Executive Dashboard")
    st.caption("A real-time business snapshot based on the currently filtered dataset.")

    if dataframe is None or dataframe.empty:
        st.warning("No data is available for the executive dashboard.")
        return

    cards = []

    # Records
    cards.append(("Filtered Records", f"{len(dataframe):,}", None))

    # Sales
    sales_value = None
    if "Sales" in dataframe.columns and pd.api.types.is_numeric_dtype(dataframe["Sales"]):
        sales_value = pd.to_numeric(dataframe["Sales"], errors="coerce").sum()
        cards.append(("Total Sales", format_metric(sales_value), None))

    # Profit
    profit_value = None
    if "Profit" in dataframe.columns and pd.api.types.is_numeric_dtype(dataframe["Profit"]):
        profit_value = pd.to_numeric(dataframe["Profit"], errors="coerce").sum()
        cards.append(("Total Profit", format_metric(profit_value), None))

    # Margin
    if sales_value is not None and profit_value is not None and sales_value != 0:
        margin = profit_value / sales_value * 100
        cards.append(("Profit Margin", f"{margin:.2f}%", None))

    # Keep the dashboard useful for arbitrary CSVs without Sales/Profit.
    for numeric_col in dataframe.select_dtypes(include="number").columns:
        if len(cards) >= 5:
            break
        if numeric_col not in {"Sales", "Profit"}:
            value = pd.to_numeric(dataframe[numeric_col], errors="coerce").sum()
            cards.append((f"Total {numeric_col}", format_metric(value), None))

    cols = st.columns(min(5, len(cards)))
    for i, (label, value, delta) in enumerate(cards[:5]):
        with cols[i]:
            st.metric(label, value, delta)

    # Executive context row
    context_items = []

    date_candidates = [
        c for c in dataframe.columns
        if "date" in str(c).lower()
        or "time" in str(c).lower()
        or "timestamp" in str(c).lower()
    ]
    if date_candidates:
        dates = pd.to_datetime(dataframe[date_candidates[0]], errors="coerce").dropna()
        if not dates.empty:
            context_items.append(
                f"📅 **Period:** {dates.min().date()} → {dates.max().date()}"
            )

    if sales_value is not None:
        context_items.append(
            f"💰 **Average Sales / Record:** {sales_value / len(dataframe):,.2f}"
        )

    if "Category" in dataframe.columns and sales_value is not None:
        category_sales = (
            dataframe.assign(_sales=pd.to_numeric(dataframe["Sales"], errors="coerce"))
            .groupby("Category", dropna=False)["_sales"]
            .sum()
            .sort_values(ascending=False)
        )
        if not category_sales.empty:
            context_items.append(
                f"🏆 **Top Category:** {category_sales.index[0]}"
            )

    if "Country" in dataframe.columns and sales_value is not None:
        country_sales = (
            dataframe.assign(_sales=pd.to_numeric(dataframe["Sales"], errors="coerce"))
            .groupby("Country", dropna=False)["_sales"]
            .sum()
            .sort_values(ascending=False)
        )
        if not country_sales.empty:
            context_items.append(
                f"🌍 **Top Country:** {country_sales.index[0]}"
            )

    if context_items:
        st.info("  •  ".join(context_items))


def render_result_kpis(result, value_column, label_column=None, title="Result Summary"):
    """Automatically surface the strongest result values."""
    if result is None or result.empty or value_column not in result.columns:
        return
    numeric_values = pd.to_numeric(result[value_column], errors="coerce")
    if numeric_values.dropna().empty:
        return

    idx_max = numeric_values.idxmax()
    idx_min = numeric_values.idxmin()
    max_label = result.loc[idx_max, label_column] if label_column and label_column in result.columns else "Highest"
    min_label = result.loc[idx_min, label_column] if label_column and label_column in result.columns else "Lowest"

    st.caption(title)
    c1, c2 = st.columns(2)
    c1.metric("Highest", f"{max_label}: {numeric_values.loc[idx_max]:,.2f}")
    c2.metric("Lowest", f"{min_label}: {numeric_values.loc[idx_min]:,.2f}")


# ============================================================
# PHASE 6.2 — AUTOMATIC CHART SELECTION
# ============================================================

def select_chart_type(operation, question, result=None, x_column=None, y_column=None):
    """Choose a visualization from the question and analysis shape.
    The chart choice affects presentation only; numerical calculations
    remain deterministic Pandas operations.
    """
    q = (question or "").lower()

    if operation == "correlation":
        if any(word in q for word in ["relationship", "relation", "vs", "versus", "correlat"]):
            return "scatter"
        return "heatmap"

    if operation == "date_trend":
        return "line"

    if operation == "comparison":
        return "bar"

    if any(word in q for word in ["trend", "over time", "by month", "by week", "by year", "by quarter", "by date"]):
        if result is not None and x_column in result.columns:
            try:
                if pd.api.types.is_datetime64_any_dtype(result[x_column]):
                    return "line"
            except Exception:
                pass

    if any(word in q for word in ["share", "proportion", "percentage", "distribution", "breakdown"]):
        if result is not None and len(result) <= 8:
            return "pie"

    if operation in {"top_n", "bottom_n"}:
        return "horizontal_bar"

    if operation in {"group_by", "profit_margin"}:
        return "bar"

    return "kpi"


def render_auto_chart(result, chart_type, x_column=None, y_column=None, title=""):
    """Render the selected Plotly chart."""
    if result is None or result.empty:
        return None

    if chart_type == "pie":
        fig = px.pie(result, names=x_column, values=y_column, title=title, hole=0.35)
    elif chart_type == "line":
        plot_df = result.sort_values(by=x_column)
        fig = px.line(plot_df, x=x_column, y=y_column, markers=True, title=title)
    elif chart_type == "horizontal_bar":
        plot_df = result.sort_values(by=y_column, ascending=True)
        fig = px.bar(plot_df, x=y_column, y=x_column, orientation="h", title=title)
    else:
        fig = px.bar(result, x=x_column, y=y_column, title=title)

    st.plotly_chart(fig, use_container_width=True)
    return fig


def show_chart_choice(chart_type):
    labels = {
        "bar": "📊 Bar chart",
        "horizontal_bar": "📊 Horizontal bar chart",
        "line": "📈 Line chart",
        "pie": "🥧 Pie chart",
        "scatter": "🔵 Scatter plot",
        "heatmap": "🌡️ Correlation heatmap",
        "kpi": "🔢 KPI summary",
    }
    st.caption(f"🤖 Recommended visualization: **{labels.get(chart_type, chart_type)}**")


# ============================================================
# PHASE 11.7 — RESPONSIVE LAYOUT & FINAL UI POLISH
# ============================================================
st.markdown("""
<style>
/* Responsive dashboard container */
.block-container {
    max-width: 1500px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

/* Prevent long tables and charts from forcing horizontal overflow */
[data-testid="stDataFrame"], .stPlotlyChart {
    max-width: 100%;
    overflow-x: auto;
}

/* Touch-friendly controls */
.stButton > button, .stDownloadButton > button {
    min-height: 42px;
    border-radius: 10px;
}

/* Mobile/tablet layout */
@media (max-width: 900px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .hero {
        padding: 1.35rem !important;
    }
    .hero h1 {
        font-size: 2rem !important;
    }
    .hero p {
        font-size: 0.95rem !important;
    }
}

@media (max-width: 640px) {
    .block-container {
        padding-left: 0.65rem;
        padding-right: 0.65rem;
    }
    .hero {
        padding: 1rem !important;
        border-radius: 14px !important;
    }
    .hero h1 {
        font-size: 1.55rem !important;
    }
    .hero p {
        font-size: 0.88rem !important;
        line-height: 1.5 !important;
    }
    [data-testid="stMetric"] {
        min-height: 95px;
    }
    .section-card {
        padding: 0.9rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# PHASE 11.1 — PROFESSIONAL NAVIGATION
# ============================================================

st.sidebar.markdown(
    """
    <div class="nav-title">📊 AI Data Analyst</div>
    <div class="nav-subtitle">Professional analytics workspace</div>
    <a class="nav-item" href="#dashboard">🏠 Dashboard</a>
    <a class="nav-item" href="#executive">📊 Executive Dashboard</a>
    <a class="nav-item" href="#overview">📋 Dataset Overview</a>
    <a class="nav-item" href="#quality">🧪 Data Quality</a>
    <a class="nav-item" href="#cleaning">🧹 Data Cleaning</a>
    <a class="nav-item" href="#filters">🎯 Smart Filters</a>
    <a class="nav-item" href="#eda">📊 Automated EDA</a>
    <a class="nav-item" href="#advanced">🚀 Advanced Analytics</a>
    <a class="nav-item" href="#report">📄 Professional Report</a>
    <a class="nav-item" href="#report-center">🗂️ Report Center</a>
    <a class="nav-item" href="#ask">💬 Ask Your Data</a>
    """,
    unsafe_allow_html=True
)
st.sidebar.divider()
st.sidebar.caption("Phase 11.3 • Visual Design")

# ============================================================
# TITLE
# ============================================================

st.markdown('<div id="dashboard"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🤖 AI Data Analyst</h1>
    <p>Upload one or more CSV files, ask questions in natural language, and turn raw data into interactive analysis, automatic visualizations, and evidence-based business insights.</p>
</div>
""", unsafe_allow_html=True)


# ============================================================
# UPLOAD CSV
# ============================================================

uploaded_files = st.file_uploader(
    "Upload one or more CSV files",
    type=["csv"],
    accept_multiple_files=True,
    help="Upload multiple CSV files. They will be combined into one analysis dataset."
)


if uploaded_files:
    st.sidebar.markdown(
        f"""
        <div class="sidebar-status">
        <b>🟢 Dataset loaded</b><br>
        {len(uploaded_files)} file(s) uploaded
        </div>
        """,
        unsafe_allow_html=True
    )

    try:
        frames = []
        file_rows = []

        for uploaded_file in uploaded_files:
            current_df = pd.read_csv(uploaded_file)
            current_df["_Source_File"] = uploaded_file.name
            frames.append(current_df)
            file_rows.append({
                "File": uploaded_file.name,
                "Rows": len(current_df),
                "Columns": len(current_df.columns) - 1
            })

        df = pd.concat(frames, ignore_index=True, sort=False)
        st.session_state.uploaded_file_names = [f.name for f in uploaded_files]

        st.success(
            f"Loaded {len(uploaded_files)} file(s) with {len(df):,} combined rows."
        )

        with st.expander("📁 Uploaded Files", expanded=False):
            st.dataframe(pd.DataFrame(file_rows), use_container_width=True)

    except Exception as e:
        st.error(f"Unable to read the CSV file(s): {e}")
        st.stop()


    # ========================================================
    # DATASET OVERVIEW
    # ========================================================

    st.markdown('<div id="overview"></div>', unsafe_allow_html=True)
    st.subheader("📋 Dataset Overview")
    st.caption("A quick health check of the uploaded dataset.")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Rows",
        df.shape[0]
    )

    col2.metric(
        "Columns",
        df.shape[1]
    )

    col3.metric(
        "Missing Values",
        int(df.isnull().sum().sum())
    )

    col4.metric(
        "Duplicate Rows",
        int(df.duplicated().sum())
    )


    # ========================================================
    # AI DATA QUALITY & CLEANING ASSISTANT
    # ========================================================

    st.markdown('<div id="quality"></div>', unsafe_allow_html=True)
    st.subheader("🧹 AI Data Quality Assistant")
    st.caption("Automatically checks the uploaded data for common quality issues before analysis.")

    quality_rows = []
    for col in df.columns:
        missing = int(df[col].isna().sum())
        unique = int(df[col].nunique(dropna=True))
        empty = int(df[col].astype(str).str.strip().eq("").sum()) if df[col].dtype == "object" else 0
        quality_rows.append({
            "Column": col,
            "Missing": missing,
            "Empty Strings": empty,
            "Unique": unique,
            "Data Type": str(df[col].dtype),
        })

    quality_df = pd.DataFrame(quality_rows)
    duplicate_count = int(df.duplicated().sum())
    empty_columns = [c for c in df.columns if df[c].isna().all() or (df[c].dtype == "object" and df[c].astype(str).str.strip().eq("").all())]

    # Detect object columns that look like dates.
    date_candidates = []
    for col in df.select_dtypes(include=["object"]).columns:
        converted = pd.to_datetime(df[col], errors="coerce")
        if len(df) > 0 and converted.notna().mean() >= 0.80:
            date_candidates.append(col)

    # Detect numeric outliers using the IQR rule.
    outlier_info = []
    for col in df.select_dtypes(include="number").columns:
        series = df[col].dropna()
        if len(series) >= 4:
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                count = 0
            else:
                count = int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())
            if count:
                outlier_info.append((col, count))

    total_missing = int(df.isna().sum().sum())
    total_empty = int(sum(r["Empty Strings"] for r in quality_rows))

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Missing Cells", total_missing)
    q2.metric("Duplicate Rows", duplicate_count)
    q3.metric("Date-like Columns", len(date_candidates))
    q4.metric("Numeric Outlier Flags", sum(x[1] for x in outlier_info))

    issues = []
    if total_missing:
        issues.append(f"{total_missing} missing cell(s) detected.")
    if total_empty:
        issues.append(f"{total_empty} empty string value(s) detected.")
    if duplicate_count:
        issues.append(f"{duplicate_count} duplicate row(s) detected.")
    if empty_columns:
        issues.append(f"Completely empty column(s): {', '.join(empty_columns)}.")
    if date_candidates:
        issues.append(f"Date-like column(s) detected: {', '.join(date_candidates)}.")
    if outlier_info:
        issues.append("Potential numeric outliers detected in: " + ", ".join(f"{c} ({n})" for c, n in outlier_info) + ".")

    if not issues:
        st.success("✅ No common data-quality issues were detected.")
    else:
        st.warning("⚠️ Data-quality checks found items worth reviewing.")
        for issue in issues:
            st.write("• " + issue)

    with st.expander("View column quality details"):
        st.dataframe(quality_df, use_container_width=True)

    # ========================================================
    # PHASE 7.3 — AI DATA QUALITY EXPLANATION
    # ========================================================

    st.subheader("🤖 AI Data Quality Explanation")
    st.caption("AI explains the detected quality findings using only the measured dataset facts.")

    quality_facts = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_cells": total_missing,
        "empty_strings": total_empty,
        "duplicate_rows": duplicate_count,
        "empty_columns": empty_columns,
        "date_like_columns": date_candidates,
        "numeric_outliers": {col: count for col, count in outlier_info},
    }

    if st.button("🧠 Explain Data Quality", type="secondary", key="explain_quality"):
        with st.spinner("AI is reviewing the data-quality findings..."):
            try:
                quality_analysis = (
                    "DATA QUALITY FACTS\n"
                    f"Rows: {quality_facts['rows']}\n"
                    f"Columns: {quality_facts['columns']}\n"
                    f"Missing cells: {quality_facts['missing_cells']}\n"
                    f"Empty strings: {quality_facts['empty_strings']}\n"
                    f"Duplicate rows: {quality_facts['duplicate_rows']}\n"
                    f"Completely empty columns: {quality_facts['empty_columns']}\n"
                    f"Date-like columns: {quality_facts['date_like_columns']}\n"
                    f"Potential numeric outliers: {quality_facts['numeric_outliers']}\n\n"
                    "INSTRUCTIONS: Explain what these findings mean in plain English. "
                    "Separate confirmed facts from recommendations. Do not invent causes, "
                    "business impact, or claim that an outlier is erroneous. Mention that "
                    "date-like text can be converted to datetime when appropriate. Keep the "
                    "answer to 3-5 concise sentences. "
                )
                quality_insight = generate_insight(
                    "Explain the quality of this dataset",
                    quality_analysis
                )
                st.session_state["quality_ai_explanation"] = quality_insight
            except Exception as e:
                st.error(f"Unable to generate AI quality explanation: {e}")

    if st.session_state.get("quality_ai_explanation"):
        st.info(st.session_state["quality_ai_explanation"])

    # ========================================================
    # PHASE 11.5 — DATA QUALITY UI
    # ========================================================
    st.markdown("### 📊 Data Quality Score")
    st.caption("A transparent score based on measured quality findings. It is a review aid, not a guarantee of data correctness.")

    row_count = max(int(len(df)), 1)
    missing_rate = total_missing / max(row_count * max(len(df.columns), 1), 1)
    duplicate_rate = duplicate_count / row_count
    empty_rate = total_empty / max(row_count * max(len(df.columns), 1), 1)
    outlier_rate = sum(x[1] for x in outlier_info) / max(row_count * max(len(df.select_dtypes(include="number").columns), 1), 1)

    quality_penalty = min(100, missing_rate * 40 + duplicate_rate * 30 + empty_rate * 15 + outlier_rate * 15)
    quality_score = max(0, min(100, 100 - quality_penalty))

    if quality_score >= 95:
        quality_status = "Excellent"
    elif quality_score >= 85:
        quality_status = "Good"
    elif quality_score >= 70:
        quality_status = "Needs Review"
    else:
        quality_status = "Needs Cleaning"

    score_col, status_col, issues_col, coverage_col = st.columns(4)
    score_col.metric("Quality Score", f"{quality_score:.0f}/100")
    status_col.metric("Status", quality_status)
    issues_col.metric("Issue Types", int(bool(total_missing)) + int(bool(duplicate_count)) + int(bool(total_empty)) + int(bool(outlier_info)) + int(bool(empty_columns)))
    coverage_col.metric("Rows Checked", f"{len(df):,}")

    qtabs = st.tabs(["📌 Summary", "📋 Column Quality", "💡 Recommendations"])
    with qtabs[0]:
        quality_summary = pd.DataFrame({
            "Check": ["Missing cells", "Duplicate rows", "Empty strings", "Outlier flags", "Date-like columns"],
            "Count": [total_missing, duplicate_count, total_empty, sum(x[1] for x in outlier_info), len(date_candidates)],
            "Status": [
                "Review" if total_missing else "OK",
                "Review" if duplicate_count else "OK",
                "Review" if total_empty else "OK",
                "Review" if outlier_info else "OK",
                "Detected" if date_candidates else "None"
            ]
        })
        st.dataframe(quality_summary, use_container_width=True, hide_index=True)

    with qtabs[1]:
        column_quality = quality_df.copy()
        column_quality["Quality Flag"] = column_quality.apply(
            lambda r: "Review" if (r["Missing"] > 0 or r["Empty Strings"] > 0) else "OK", axis=1
        )
        st.dataframe(column_quality, use_container_width=True, hide_index=True)

    with qtabs[2]:
        recommendations = []
        if total_missing:
            recommendations.append("Review missing values and choose a field-appropriate imputation or removal strategy.")
        if duplicate_count:
            recommendations.append("Review duplicate rows before removing them, especially when repeated records may be legitimate.")
        if outlier_info:
            recommendations.append("Inspect flagged numeric outliers before deciding whether to cap, transform, or retain them.")
        if date_candidates:
            recommendations.append("Convert date-like text columns to datetime when they are intended for time-based analysis.")
        if total_empty:
            recommendations.append("Normalize empty strings before analysis so missing-value handling is consistent.")
        if not recommendations:
            recommendations.append("No immediate cleaning action was suggested by the measured quality checks.")
        for rec in recommendations:
            st.write("• " + rec)


    # ========================================================
    # PHASE 8 — AUTOMATED EXPLORATORY DATA ANALYSIS (EDA)
    # ========================================================

    st.markdown('<div id="eda"></div>', unsafe_allow_html=True)
    st.subheader("📊 Automated Exploratory Data Analysis")
    st.caption("Automatically profile the dataset, visualize important patterns, and surface useful observations before asking specific questions.")

    eda_numeric = df.select_dtypes(include="number").columns.tolist()
    eda_categorical = [
        c for c in df.columns
        if c not in eda_numeric and c != "_Source_File" and df[c].nunique(dropna=True) <= 30
    ]
    eda_date_columns = []
    for col in df.columns:
        if col == "_Source_File":
            continue
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            eda_date_columns.append(col)
        elif df[col].dtype == "object":
            converted = pd.to_datetime(df[col], errors="coerce")
            if len(df) and converted.notna().mean() >= 0.80:
                eda_date_columns.append(col)

    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Rows", f"{len(df):,}")
    e2.metric("Numeric Columns", len(eda_numeric))
    e3.metric("Categorical Columns", len(eda_categorical))
    e4.metric("Date Columns", len(eda_date_columns))

    with st.expander("📋 Automated Dataset Profile", expanded=True):
        profile_rows = []
        for col in df.columns:
            profile_rows.append({
                "Column": col,
                "Type": str(df[col].dtype),
                "Missing": int(df[col].isna().sum()),
                "Unique": int(df[col].nunique(dropna=True)),
            })
        st.dataframe(pd.DataFrame(profile_rows), use_container_width=True)

    # Numeric distributions
    if eda_numeric:
        st.markdown("### 📈 Numeric Distributions")
        selected_numeric = st.selectbox(
            "Choose a numeric column",
            eda_numeric,
            key="eda_numeric_column"
        )
        fig_hist = px.histogram(
            df,
            x=selected_numeric,
            nbins=min(20, max(5, df[selected_numeric].nunique())),
            title=f"Distribution of {selected_numeric}"
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        stats = df[eda_numeric].describe().T.reset_index().rename(columns={"index": "Column"})
        with st.expander("📊 Numeric Statistics"):
            st.dataframe(stats, use_container_width=True)

    # Categorical distributions
    if eda_categorical:
        st.markdown("### 🏷️ Categorical Overview")
        selected_cat = st.selectbox(
            "Choose a categorical column",
            eda_categorical,
            key="eda_categorical_column"
        )
        cat_counts = (
            df[selected_cat]
            .fillna("Missing")
            .astype(str)
            .value_counts()
            .head(10)
            .reset_index()
        )
        cat_counts.columns = [selected_cat, "Count"]
        fig_cat = px.bar(
            cat_counts,
            x=selected_cat,
            y="Count",
            title=f"Top Values in {selected_cat}"
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    # Correlation overview
    if len(eda_numeric) >= 2:
        st.markdown("### 🔗 Numeric Relationships")
        corr = df[eda_numeric].corr(numeric_only=True)
        fig_corr = px.imshow(
            corr,
            text_auto=".2f",
            aspect="auto",
            title="Correlation Matrix"
        )
        st.plotly_chart(fig_corr, use_container_width=True)

        pairs = []
        for i, c1 in enumerate(eda_numeric):
            for c2 in eda_numeric[i + 1:]:
                value = corr.loc[c1, c2]
                if pd.notna(value):
                    pairs.append((c1, c2, float(value)))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        if pairs:
            strongest = pairs[0]
            st.info(
                f"Strongest measured numeric relationship: **{strongest[0]} ↔ {strongest[1]}** "
                f"with correlation **{strongest[2]:.3f}**. Correlation describes association; it does not establish causation."
            )

    # Date overview
    if eda_date_columns and eda_numeric:
        st.markdown("### 📅 Time Overview")
        date_col = st.selectbox("Date column", eda_date_columns, key="eda_date_column")
        measure_col = st.selectbox("Measure", eda_numeric, key="eda_date_measure")
        date_series = pd.to_datetime(df[date_col], errors="coerce")
        time_df = pd.DataFrame({"Date": date_series, measure_col: df[measure_col]}).dropna()
        if not time_df.empty:
            time_df["Month"] = time_df["Date"].dt.to_period("M").dt.to_timestamp()
            monthly = time_df.groupby("Month", as_index=False)[measure_col].sum()
            fig_time = px.line(
                monthly,
                x="Month",
                y=measure_col,
                markers=True,
                title=f"Monthly {measure_col} Trend"
            )
            st.plotly_chart(fig_time, use_container_width=True)

    # Automatic EDA findings
    st.markdown("### 🧠 Automated EDA Findings")
    findings = []
    findings.append(f"The dataset contains {len(df):,} rows and {len(df.columns):,} columns.")
    if eda_numeric:
        findings.append(f"Numeric measures available for analysis: {', '.join(eda_numeric)}.")
    if eda_categorical:
        findings.append(f"Low-cardinality categorical columns available for grouping: {', '.join(eda_categorical)}.")
    if eda_date_columns:
        findings.append(f"Date-like columns detected: {', '.join(eda_date_columns)}.")
    if total_missing == 0 and duplicate_count == 0:
        findings.append("No missing cells or duplicate rows were detected by the quality checks.")
    elif total_missing or duplicate_count:
        findings.append(f"Quality checks found {total_missing} missing cell(s) and {duplicate_count} duplicate row(s).")
    if pairs:
        c1, c2, cv = pairs[0]
        findings.append(f"The strongest measured numeric correlation is between {c1} and {c2} at {cv:.3f}.")

    for finding in findings:
        st.write("• " + finding)


    # ========================================================
    # DATA CLEANING ASSISTANT
    # ========================================================

    st.markdown('<div id="cleaning"></div>', unsafe_allow_html=True)
    st.subheader("🧽 Data Cleaning Assistant")
    st.caption("Review detected issues and choose cleaning actions. Nothing changes until you click Apply Cleaning.")

    file_signature = tuple((f.name, getattr(f, "size", 0)) for f in uploaded_files)
    if st.session_state.get("cleaning_file_signature") != file_signature:
        st.session_state["cleaning_file_signature"] = file_signature
        st.session_state.pop("cleaned_df", None)
        st.session_state.pop("cleaning_report", None)

    with st.expander("🛠️ Choose cleaning actions", expanded=False):
        clean_duplicates = st.checkbox(
            "Remove duplicate rows",
            value=duplicate_count > 0,
            disabled=duplicate_count == 0,
            key="clean_remove_duplicates"
        )

        date_to_convert = st.multiselect(
            "Convert date-like columns to datetime",
            date_candidates,
            default=date_candidates,
            key="clean_date_columns"
        )

        missing_columns = [c for c in df.columns if int(df[c].isna().sum()) > 0]
        missing_action = st.selectbox(
            "Missing-value handling",
            ["Do nothing", "Drop rows with missing values", "Fill numeric with median and categorical with mode"],
            index=0 if not missing_columns else 1,
            key="clean_missing_action"
        )

        empty_string_columns = [
            c for c in df.columns
            if df[c].dtype == "object" and df[c].astype(str).str.strip().eq("").any()
        ]
        clean_empty_strings = st.checkbox(
            "Convert empty strings to missing values",
            value=bool(empty_string_columns),
            disabled=not bool(empty_string_columns),
            key="clean_empty_strings"
        )

        outlier_columns = [c for c, _ in outlier_info]
        cap_outliers = st.checkbox(
            "Cap numeric outliers using IQR limits",
            value=False,
            disabled=not bool(outlier_columns),
            key="clean_cap_outliers"
        )
        if outlier_columns:
            st.caption("Outliers are not removed by default. Capping changes extreme values, so review this choice carefully.")

        apply_cleaning = st.button("🧹 Apply Cleaning", type="primary", key="apply_cleaning")

        if apply_cleaning:
            before_rows = len(df)
            before_missing = int(df.isna().sum().sum())
            working = df.copy()
            actions = []

            if clean_empty_strings:
                for col in working.select_dtypes(include=["object"]).columns:
                    working[col] = working[col].replace(r"^\s*$", pd.NA, regex=True)
                actions.append("Converted empty strings to missing values")

            if clean_duplicates:
                removed = int(working.duplicated().sum())
                working = working.drop_duplicates().reset_index(drop=True)
                actions.append(f"Removed {removed} duplicate row(s)")

            if missing_action == "Drop rows with missing values":
                removed = int(working.isna().any(axis=1).sum())
                working = working.dropna().reset_index(drop=True)
                actions.append(f"Dropped {removed} row(s) containing missing values")
            elif missing_action == "Fill numeric with median and categorical with mode":
                filled = 0
                for col in working.columns:
                    missing_count = int(working[col].isna().sum())
                    if missing_count == 0:
                        continue
                    if pd.api.types.is_numeric_dtype(working[col]):
                        median = working[col].median()
                        if pd.notna(median):
                            working[col] = working[col].fillna(median)
                            filled += missing_count
                    else:
                        modes = working[col].mode(dropna=True)
                        if not modes.empty:
                            working[col] = working[col].fillna(modes.iloc[0])
                            filled += missing_count
                actions.append(f"Filled {filled} missing value(s) using median/mode where possible")

            for col in date_to_convert:
                if col in working.columns:
                    working[col] = pd.to_datetime(working[col], errors="coerce")
                    actions.append(f"Converted {col} to datetime")

            if cap_outliers:
                capped = 0
                for col in outlier_columns:
                    if col not in working.columns or not pd.api.types.is_numeric_dtype(working[col]):
                        continue
                    series = working[col].dropna()
                    if len(series) < 4:
                        continue
                    q1v = series.quantile(0.25)
                    q3v = series.quantile(0.75)
                    iqr_v = q3v - q1v
                    if iqr_v == 0:
                        continue
                    lower = q1v - 1.5 * iqr_v
                    upper = q3v + 1.5 * iqr_v
                    mask = (working[col] < lower) | (working[col] > upper)
                    capped += int(mask.sum())
                    working[col] = working[col].clip(lower=lower, upper=upper)
                actions.append(f"Capped {capped} numeric outlier value(s) using IQR limits")

            after_rows = len(working)
            after_missing = int(working.isna().sum().sum())
            st.session_state["cleaned_df"] = working
            st.session_state["cleaning_report"] = {
                "before_rows": before_rows,
                "after_rows": after_rows,
                "before_missing": before_missing,
                "after_missing": after_missing,
                "actions": actions or ["No cleaning action changed the dataset"]
            }
            st.rerun()

    if "cleaned_df" in st.session_state:
        df = st.session_state["cleaned_df"].copy()
        report = st.session_state.get("cleaning_report", {})
        st.success("🧽 Cleaned dataset is active for the analysis below.")
        r1, r2, r3, r4 = st.columns(4)
        before_rows = report.get("before_rows", len(df))
        before_missing = report.get("before_missing", int(df.isna().sum().sum()))
        r1.metric("Rows Before", before_rows)
        r2.metric("Rows After", len(df), delta=len(df) - before_rows)
        r3.metric("Missing Before", before_missing)
        r4.metric("Missing After", int(df.isna().sum().sum()), delta=int(df.isna().sum().sum()) - before_missing)
        with st.expander("View cleaning actions"):
            for action in report.get("actions", []):
                st.write("• " + action)
        st.download_button(
            "📥 Download Cleaned CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="cleaned_dataset.csv",
            mime="text/csv",
            key="download_cleaned_csv"
        )


    # ========================================================
    # DATA PREVIEW
    # ========================================================

    st.subheader("🔍 Data Preview")

    st.dataframe(
        df.head(10),
        use_container_width=True
    )


    # ========================================================
    # COLUMN INFORMATION
    # ========================================================

    st.subheader("📊 Column Information")

    column_info = pd.DataFrame({
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str).values,
        "Missing": df.isnull().sum().values,
        "Unique Values": df.nunique().values
    })

    st.dataframe(
        column_info,
        use_container_width=True
    )


    # ========================================================
    # COLUMN TYPES
    # ========================================================

    numeric_columns = (
        df
        .select_dtypes(include="number")
        .columns
        .tolist()
    )

    categorical_columns = (
        df
        .select_dtypes(
            include=["object", "category"]
        )
        .columns
        .tolist()
    )


    # ========================================================
    # DATE COLUMN DETECTION
    # ========================================================

    date_columns = []

    for col in df.columns:

        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_columns.append(col)
            continue

        if df[col].dtype == "object":

            converted = pd.to_datetime(
                df[col],
                errors="coerce"
            )

            valid_ratio = converted.notna().mean()

            if valid_ratio >= 0.80:
                date_columns.append(col)


    # Remove detected date columns from categorical filters.
    # Date fields should be handled by the date-range filter, not as
    # categorical values such as individual dates.
    categorical_columns = [
        col for col in categorical_columns
        if col not in date_columns
    ]


    # ========================================================
    # SMART DATA FILTERS
    # ========================================================

    st.markdown('<div id="filters"></div>', unsafe_allow_html=True)
    st.subheader("🎯 Smart Data Filters")
    st.caption(
        "Filter the dataset before running AI analysis or manual analysis."
    )

    filtered_df = df.copy()

    filter_col1, filter_col2 = st.columns(2)

    # Date range filter
    with filter_col1:

        if date_columns:

            global_date_col = st.selectbox(
                "Date filter column",
                date_columns,
                key="global_date_filter_column"
            )

            global_dates = pd.to_datetime(
                filtered_df[global_date_col],
                errors="coerce"
            )

            valid_global_dates = global_dates.dropna()

            if not valid_global_dates.empty:

                global_min_date = valid_global_dates.min().date()
                global_max_date = valid_global_dates.max().date()

                global_date_range = st.date_input(
                    "Date range",
                    value=(global_min_date, global_max_date),
                    min_value=global_min_date,
                    max_value=global_max_date,
                    format="YYYY-MM-DD",
                    key="global_date_range_filter"
                )

                if (
                    isinstance(global_date_range, tuple)
                    and len(global_date_range) == 2
                ):

                    start_date, end_date = global_date_range

                    date_mask = (
                        global_dates.dt.date >= start_date
                    ) & (
                        global_dates.dt.date <= end_date
                    )

                    filtered_df = filtered_df.loc[date_mask]

    # Categorical filters
    with filter_col2:

        filterable_columns = [
            col for col in categorical_columns
            if col != "_Source_File" and df[col].nunique(dropna=True) <= 100
        ]

        selected_filter_columns = st.multiselect(
            "Categorical filters",
            filterable_columns,
            default=[],
            key="selected_filter_columns"
        )

        for filter_column in selected_filter_columns:

            options = sorted(
                df[filter_column]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            selected_values = st.multiselect(
                f"{filter_column}",
                options,
                default=options,
                key=f"filter_values_{filter_column}"
            )

            if selected_values:

                filtered_df = filtered_df[
                    filtered_df[filter_column]
                    .astype(str)
                    .isin(selected_values)
                ]

            else:

                filtered_df = filtered_df.iloc[0:0]

    st.info(
        f"Showing {len(filtered_df):,} of {len(df):,} rows after filters."
    )

    if len(uploaded_files) > 1:
        source_summary = (
            filtered_df.groupby("_Source_File", dropna=False)
            .size()
            .reset_index(name="Rows")
        )
        with st.expander("📁 Rows by source file", expanded=False):
            st.dataframe(source_summary, use_container_width=True)

    if filtered_df.empty:
        st.warning(
            "No rows match the selected filters. Please adjust the filters."
        )
    else:
        # ====================================================
        # AUTOMATIC KPI SUMMARY
        # ====================================================

        add_phase6_kpis(filtered_df)


    # ========================================================
    # DATE/TIME ANALYSIS
    # ========================================================

    if date_columns:

        st.subheader("📅 Date & Time Analysis")

        st.write(
            "Date columns were detected automatically. "
            "Use this section to explore trends over time."
        )

        date_col = st.selectbox(
            "Select date column",
            date_columns,
            key="date_column_selector"
        )

        date_series = pd.to_datetime(
            df[date_col],
            errors="coerce"
        )

        valid_dates = date_series.dropna()

        if not valid_dates.empty:

            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()

            st.caption(
                f"Detected date range: {min_date} to {max_date}"
            )

            date_filter_enabled = st.checkbox(
                "Filter by date range",
                key="enable_date_filter"
            )

            filtered_date_df = filtered_df.copy()

            if date_filter_enabled:

                selected_range = st.date_input(
                    "Select date range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    format="YYYY-MM-DD",
                    key="date_range_filter"
                )

                if (
                    isinstance(selected_range, tuple)
                    and len(selected_range) == 2
                ):

                    start_date, end_date = selected_range

                    temp_dates = pd.to_datetime(
                        filtered_date_df[date_col],
                        errors="coerce"
                    )

                    mask = (
                        temp_dates.dt.date >= start_date
                    ) & (
                        temp_dates.dt.date <= end_date
                    )

                    filtered_date_df = filtered_date_df.loc[mask]

            if numeric_columns:

                date_col1, date_col2, date_col3 = st.columns(3)

                with date_col1:

                    date_measure = st.selectbox(
                        "Measure",
                        numeric_columns,
                        key="date_measure_selector"
                    )

                with date_col2:

                    date_granularity = st.selectbox(
                        "Time granularity",
                        [
                            "Day",
                            "Week",
                            "Month",
                            "Quarter",
                            "Year"
                        ],
                        key="date_granularity_selector"
                    )

                with date_col3:

                    date_aggregation = st.selectbox(
                        "Aggregation",
                        [
                            "Sum",
                            "Average",
                            "Minimum",
                            "Maximum"
                        ],
                        key="date_aggregation_selector"
                    )

                trend_df = filtered_date_df.copy()

                trend_df["_date_"] = pd.to_datetime(
                    trend_df[date_col],
                    errors="coerce"
                )

                trend_df = trend_df.dropna(
                    subset=["_date_"]
                )

                if not trend_df.empty:

                    if date_granularity == "Day":
                        trend_df["_period_"] = (
                            trend_df["_date_"].dt.floor("D")
                        )

                    elif date_granularity == "Week":
                        trend_df["_period_"] = (
                            trend_df["_date_"]
                            .dt.to_period("W")
                            .dt.start_time
                        )

                    elif date_granularity == "Month":
                        trend_df["_period_"] = (
                            trend_df["_date_"]
                            .dt.to_period("M")
                            .dt.start_time
                        )

                    elif date_granularity == "Quarter":
                        trend_df["_period_"] = (
                            trend_df["_date_"]
                            .dt.to_period("Q")
                            .dt.start_time
                        )

                    else:
                        trend_df["_period_"] = (
                            trend_df["_date_"]
                            .dt.to_period("Y")
                            .dt.start_time
                        )

                    aggregation_map = {
                        "Sum": "sum",
                        "Average": "mean",
                        "Minimum": "min",
                        "Maximum": "max"
                    }

                    agg_func = aggregation_map[
                        date_aggregation
                    ]

                    trend_result = (
                        trend_df
                        .groupby("_period_")[date_measure]
                        .agg(agg_func)
                        .reset_index()
                        .rename(
                            columns={
                                "_period_": "Date",
                                date_measure: date_measure
                            }
                        )
                    )

                    trend_result = trend_result.sort_values(
                        "Date"
                    )

                    st.markdown(
                        "### 📈 Time Trend"
                    )

                    st.dataframe(
                        trend_result,
                        use_container_width=True
                    )

                    fig = px.line(
                        trend_result,
                        x="Date",
                        y=date_measure,
                        markers=True,
                        title=(
                            f"{date_aggregation} "
                            f"{date_measure} by "
                            f"{date_granularity}"
                        )
                    )

                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title=date_measure
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                    if not trend_result.empty:

                        highest_row = trend_result.loc[
                            trend_result[date_measure].idxmax()
                        ]

                        lowest_row = trend_result.loc[
                            trend_result[date_measure].idxmin()
                        ]

                        insight_col1, insight_col2 = st.columns(2)

                        with insight_col1:

                            st.metric(
                                "Highest Period",
                                str(
                                    highest_row["Date"].date()
                                    if hasattr(
                                        highest_row["Date"],
                                        "date"
                                    )
                                    else highest_row["Date"]
                                ),
                                f"{highest_row[date_measure]:,.2f}"
                            )

                        with insight_col2:

                            st.metric(
                                "Lowest Period",
                                str(
                                    lowest_row["Date"].date()
                                    if hasattr(
                                        lowest_row["Date"],
                                        "date"
                                    )
                                    else lowest_row["Date"]
                                ),
                                f"{lowest_row[date_measure]:,.2f}"
                            )

            else:

                st.info(
                    "No numeric columns are available for "
                    "date trend analysis."
                )

        else:

            st.warning(
                f"Column '{date_col}' could not be converted "
                "to valid dates."
            )


    # ========================================================
    # PHASE 9 — ADVANCED AI ANALYTICS
    # ========================================================

    st.markdown('<div id="advanced"></div>', unsafe_allow_html=True)
    st.subheader("🚀 Advanced AI Analytics")
    st.caption("Explore growth, rankings, profit margins, anomalies, and an evidence-based executive summary.")

    adv_tabs = st.tabs([
        "📈 Growth Analysis",
        "🏆 Ranking",
        "💰 Profit Margin",
        "🔍 Anomalies",
        "🧠 Executive Summary",
    ])

    # ---------------- Growth Analysis ----------------
    with adv_tabs[0]:
        adv_dates = []
        for c in df.columns:
            if c == "_Source_File":
                continue
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                adv_dates.append(c)
            elif df[c].dtype == "object":
                parsed = pd.to_datetime(df[c], errors="coerce")
                if len(df) and parsed.notna().mean() >= 0.80:
                    adv_dates.append(c)

        adv_numeric = df.select_dtypes(include="number").columns.tolist()

        if adv_dates and adv_numeric:
            gc1, gc2, gc3 = st.columns(3)
            growth_date = gc1.selectbox("Date column", adv_dates, key="phase9_growth_date")
            growth_measure = gc2.selectbox("Measure", adv_numeric, key="phase9_growth_measure")
            growth_granularity = gc3.selectbox("Granularity", ["month", "quarter", "year"], key="phase9_growth_granularity")

            temp = df[[growth_date, growth_measure]].copy()
            temp[growth_date] = pd.to_datetime(temp[growth_date], errors="coerce")
            temp[growth_measure] = pd.to_numeric(temp[growth_measure], errors="coerce")
            temp = temp.dropna()

            if not temp.empty:
                if growth_granularity == "month":
                    temp["Period"] = temp[growth_date].dt.to_period("M").astype(str)
                elif growth_granularity == "quarter":
                    temp["Period"] = temp[growth_date].dt.to_period("Q").astype(str)
                else:
                    temp["Period"] = temp[growth_date].dt.year.astype(str)

                growth = temp.groupby("Period")[growth_measure].sum().reset_index()
                growth["Previous"] = growth[growth_measure].shift(1)
                growth["Change"] = growth[growth_measure] - growth["Previous"]
                growth["Change %"] = (growth["Change"] / growth["Previous"].replace(0, pd.NA)) * 100

                st.dataframe(growth, use_container_width=True)
                valid_growth = growth.dropna(subset=["Change %"])
                if not valid_growth.empty:
                    best = valid_growth.loc[valid_growth["Change %"].idxmax()]
                    worst = valid_growth.loc[valid_growth["Change %"].idxmin()]
                    a, b = st.columns(2)
                    a.metric("Largest Growth", f"{best['Period']}: {best['Change %']:.2f}%")
                    b.metric("Largest Decline", f"{worst['Period']}: {worst['Change %']:.2f}%")

                    fig_growth = px.bar(
                        valid_growth,
                        x="Period",
                        y="Change %",
                        title=f"Period-over-Period Growth — {growth_measure}"
                    )
                    st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info("Growth analysis requires at least one date-like column and one numeric column.")

    # ---------------- Ranking ----------------
    with adv_tabs[1]:
        rank_cats = [
            c for c in df.columns
            if c != "_Source_File" and c not in df.select_dtypes(include="number").columns
            and df[c].nunique(dropna=True) <= 50
        ]
        rank_nums = df.select_dtypes(include="number").columns.tolist()

        if rank_cats and rank_nums:
            rc1, rc2, rc3 = st.columns(3)
            rank_category = rc1.selectbox("Rank by", rank_cats, key="phase9_rank_category")
            rank_measure = rc2.selectbox("Measure", rank_nums, key="phase9_rank_measure")
            rank_n = rc3.number_input("Top N", min_value=3, max_value=20, value=5, step=1, key="phase9_rank_n")

            ranking = (
                df.groupby(rank_category, dropna=False)[rank_measure]
                .sum()
                .reset_index()
                .sort_values(rank_measure, ascending=False)
                .head(int(rank_n))
            )

            st.dataframe(ranking, use_container_width=True)
            fig_rank = px.bar(
                ranking.sort_values(rank_measure),
                x=rank_measure,
                y=rank_category,
                orientation="h",
                title=f"Top {int(rank_n)} {rank_category} by {rank_measure}"
            )
            st.plotly_chart(fig_rank, use_container_width=True)
        else:
            st.info("Ranking requires a categorical column and a numeric column.")

    # ---------------- Profit Margin ----------------
    with adv_tabs[2]:
        if "Sales" in df.columns and "Profit" in df.columns:
            margin_cats = [
                c for c in df.columns
                if c != "_Source_File" and c not in {"Sales", "Profit"}
                and df[c].nunique(dropna=True) <= 50
            ]
            if margin_cats:
                margin_category = st.selectbox("Analyze margin by", margin_cats, key="phase9_margin_category")
                margin_df = (
                    df.groupby(margin_category, dropna=False)[["Sales", "Profit"]]
                    .sum()
                    .reset_index()
                )
                margin_df["Profit Margin %"] = (
                    margin_df["Profit"] / margin_df["Sales"].replace(0, pd.NA) * 100
                )
                margin_df = margin_df.sort_values("Profit Margin %", ascending=False)

                st.dataframe(margin_df, use_container_width=True)
                fig_margin = px.bar(
                    margin_df,
                    x=margin_category,
                    y="Profit Margin %",
                    title=f"Profit Margin by {margin_category}"
                )
                st.plotly_chart(fig_margin, use_container_width=True)

                valid_margin = margin_df.dropna(subset=["Profit Margin %"])
                if not valid_margin.empty:
                    best_margin = valid_margin.iloc[0]
                    st.success(
                        f"Highest measured profit margin: **{best_margin[margin_category]} — {best_margin['Profit Margin %']:.2f}%**"
                    )
            else:
                st.info("No suitable categorical column was found for margin analysis.")
        else:
            st.info("Profit margin analysis requires numeric Sales and Profit columns.")

    # ---------------- Anomalies ----------------
    with adv_tabs[3]:
        anomaly_nums = df.select_dtypes(include="number").columns.tolist()
        if anomaly_nums:
            anomaly_col = st.selectbox("Check numeric column", anomaly_nums, key="phase9_anomaly_column")
            series = pd.to_numeric(df[anomaly_col], errors="coerce")
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if pd.notna(iqr) and iqr > 0:
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                anomaly_mask = (series < lower) | (series > upper)
                anomalies = df.loc[anomaly_mask].copy()
                st.write(f"Potential anomalies detected: **{len(anomalies)}**")
                st.caption("An anomaly is a statistical signal, not proof that a record is incorrect.")
                if not anomalies.empty:
                    st.dataframe(anomalies, use_container_width=True)
                else:
                    st.success("No potential IQR anomalies were detected in this column.")
            else:
                st.info("IQR anomaly detection is not informative when the interquartile range is zero.")
        else:
            st.info("No numeric columns are available for anomaly analysis.")

    # ---------------- Executive Summary ----------------
    with adv_tabs[4]:
        st.write("Generate a concise, evidence-based summary from the measured dataset statistics.")
        if st.button("🧠 Generate Executive Summary", key="phase9_exec_summary"):
            try:
                summary_facts = {
                    "rows": int(len(df)),
                    "columns": int(len(df.columns)),
                    "missing_cells": int(df.isna().sum().sum()),
                    "duplicate_rows": int(df.duplicated().sum()),
                    "numeric_columns": adv_numeric if 'adv_numeric' in locals() else df.select_dtypes(include="number").columns.tolist(),
                    "categorical_columns": eda_categorical if 'eda_categorical' in locals() else [],
                }

                if "Sales" in df.columns and pd.api.types.is_numeric_dtype(df["Sales"]):
                    summary_facts["total_sales"] = float(df["Sales"].sum())
                if "Profit" in df.columns and pd.api.types.is_numeric_dtype(df["Profit"]):
                    summary_facts["total_profit"] = float(df["Profit"].sum())
                if "Sales" in df.columns and "Profit" in df.columns and df["Sales"].sum() != 0:
                    summary_facts["profit_margin_pct"] = float(df["Profit"].sum() / df["Sales"].sum() * 100)

                prompt = (
                    "Create a concise executive summary using ONLY these measured dataset facts. "
                    "Mention important scale, quality, and measurable business patterns. "
                    "Do not invent causes, customer motivations, external market conditions, "
                    "recommendations, or future predictions. Correlation is association, not causation. "
                    "Use 4-6 bullet points.\n\nFACTS:\n" + str(summary_facts)
                )
                exec_summary = generate_insight("Generate an executive summary", prompt)
                st.session_state.latest_executive_summary = exec_summary
                st.info(exec_summary)
            except Exception as e:
                st.error(f"Unable to generate executive summary: {e}")

    # ========================================================
    # PHASE 10 — PROFESSIONAL AI REPORT
    # ========================================================

    st.markdown('<div id="report"></div>', unsafe_allow_html=True)
    st.subheader("📄 Professional AI Report")
    st.caption("Generate a consolidated PDF report from the currently filtered dataset.")

    def create_professional_report(df, source_files, quality_facts, eda_facts, executive_text):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        styles = getSampleStyleSheet()
        title = ParagraphStyle("PTitle", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=16)
        h1 = ParagraphStyle("PH1", parent=styles["Heading1"], spaceBefore=12, spaceAfter=8)
        h2 = ParagraphStyle("PH2", parent=styles["Heading2"], spaceBefore=10, spaceAfter=6)
        body = ParagraphStyle("PBody", parent=styles["BodyText"], leading=14, spaceAfter=6)

        def esc(value):
            return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")

        story = [
            Paragraph("AI Data Analyst — Professional Report", title),
            Paragraph("1. Dataset Overview", h1),
            Paragraph(f"Rows analyzed: <b>{len(df):,}</b>", body),
            Paragraph(f"Columns: <b>{len(df.columns):,}</b>", body),
            Paragraph(f"Source files: <b>{len(source_files):,}</b>", body),
        ]

        if source_files:
            story.append(Paragraph("Source files: " + ", ".join(esc(x) for x in source_files), body))

        story += [Paragraph("2. Data Quality", h1)]
        for label, value in quality_facts.items():
            story.append(Paragraph(f"{esc(label)}: <b>{esc(value)}</b>", body))

        story.append(Paragraph("3. Key KPIs", h1))
        kpi_rows = [["Metric", "Value"]]
        for col in ["Sales", "Profit", "Quantity"]:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                kpi_rows.append([col, f"{df[col].sum():,.2f}"])
        if "Sales" in df.columns and "Profit" in df.columns:
            sales_total = pd.to_numeric(df["Sales"], errors="coerce").sum()
            profit_total = pd.to_numeric(df["Profit"], errors="coerce").sum()
            if sales_total != 0:
                kpi_rows.append(["Profit Margin", f"{profit_total / sales_total * 100:.2f}%"])
        if len(kpi_rows) > 1:
            table = Table(kpi_rows, colWidths=[220, 220])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EAF2F8")),
                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
            ]))
            story += [table, Spacer(1, 10)]

        story.append(Paragraph("4. Automated EDA Findings", h1))
        if eda_facts:
            for fact in eda_facts:
                story.append(Paragraph("• " + esc(fact), body))
        else:
            story.append(Paragraph("No automated EDA findings were available.", body))

        story.append(Paragraph("5. Executive Summary", h1))
        story.append(Paragraph(esc(executive_text) if executive_text else "Generate the Executive Summary from the Advanced AI Analytics section to include it here.", body))

        story.append(Paragraph("6. Numeric Profile", h1))
        numeric = df.select_dtypes(include="number")
        if not numeric.empty:
            rows = [["Column", "Mean", "Min", "Max"]]
            for col in numeric.columns[:12]:
                rows.append([str(col), f"{numeric[col].mean():,.2f}", f"{numeric[col].min():,.2f}", f"{numeric[col].max():,.2f}"])
            table = Table(rows, colWidths=[140, 120, 120, 120], repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EAF2F8")),
                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No numeric columns available.", body))

        story += [Spacer(1, 14), Paragraph("Generated by AI Data Analyst", styles["Italic"])]
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    if st.button("📄 Generate Professional PDF Report", key="phase10_report"):
        try:
            quality_facts = {
                "Missing cells": int(df.isna().sum().sum()),
                "Duplicate rows": int(df.duplicated().sum()),
                "Columns": int(len(df.columns)),
            }
            eda_facts = [
                f"The analyzed dataset contains {len(df):,} rows and {len(df.columns):,} columns.",
            ]
            numeric_for_report = df.select_dtypes(include="number")
            if len(numeric_for_report.columns) >= 2:
                corr = numeric_for_report.corr()
                pairs = []
                for i, a in enumerate(corr.columns):
                    for b in corr.columns[i+1:]:
                        if pd.notna(corr.loc[a, b]):
                            pairs.append((abs(float(corr.loc[a, b])), a, b, float(corr.loc[a, b])))
                if pairs:
                    _, a, b, value = max(pairs)
                    eda_facts.append(f"Strongest measured numeric relationship: {a} and {b} with correlation {value:.3f}.")
            executive_text = st.session_state.get("latest_executive_summary", "")
            report_files = st.session_state.get("uploaded_file_names", [])
            pdf = create_professional_report(
                df,
                report_files,
                quality_facts,
                eda_facts,
                executive_text,
            )
            st.success("Professional PDF report generated successfully.")
            st.download_button(
                "⬇️ Download Professional PDF Report",
                data=pdf,
                file_name="ai_data_analyst_professional_report.pdf",
                mime="application/pdf",
                key="phase10_download_report",
            )
        except Exception as e:
            st.error(f"Unable to generate professional report: {e}")

    # ========================================================
    # ========================================================
    # PHASE 11.6 — REPORT CENTER
    # ========================================================
    st.markdown('<div id="report-center"></div>', unsafe_allow_html=True)
    st.subheader("🗂️ Report Center")
    st.caption("One place to review dataset status, analysis history, and generate the professional PDF report.")

    report_files = st.session_state.get("uploaded_file_names", [])
    report_history = st.session_state.get("conversation_history", [])
    rc1, rc2, rc3, rc4 = st.columns(4)
    rc1.metric("Files", len(report_files))
    rc2.metric("Rows", f"{len(df):,}")
    rc3.metric("Columns", len(df.columns))
    rc4.metric("AI Questions", len(report_history))

    center_tabs = st.tabs(["📄 Report Summary", "💬 AI Analysis History", "⬇️ Export Center"])
    with center_tabs[0]:
        report_summary = pd.DataFrame({
            "Report Component": ["Dataset Profile", "Data Quality", "Automated EDA", "Advanced Analytics", "AI Analyst"],
            "Status": ["Ready", "Ready", "Ready", "Ready", "Ready" if report_history else "Awaiting questions"]
        })
        st.dataframe(report_summary, use_container_width=True, hide_index=True)

    with center_tabs[1]:
        if report_history:
            for idx, item in enumerate(report_history[-10:], 1):
                with st.expander(f"Question {idx}: {item.get('question', 'Analysis')}", expanded=False):
                    st.write(item.get("insight", "No insight stored."))
        else:
            st.info("Ask questions in the AI Analyst section to build an analysis history.")

    with center_tabs[2]:
        st.info("Use the Professional AI Report section below to generate the consolidated PDF. Individual AI analysis notes can also be exported from the Ask Your Data workflow.")


    # ========================================================
    # ASK YOUR DATA — AI ANALYST EXPERIENCE
    # ========================================================

    st.markdown('<div id="ask"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-card" style="padding:1.25rem 1.35rem;">
        <div style="font-size:1.35rem;font-weight:760;margin-bottom:.25rem;">💬 Ask Your Data</div>
        <div class="small-muted">Talk to your dataset in natural language. The AI plans the analysis, Python computes it, and the dashboard explains the result.</div>
    </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # Suggested analyst questions
    # --------------------------------------------------------
    st.markdown("**✨ Suggested questions**")
    suggestion_col1, suggestion_col2, suggestion_col3, suggestion_col4 = st.columns(4)
    suggestions = [
        "Which category has the highest profit margin?",
        "What are the top 5 products by sales?",
        "Which country has the highest profit?",
        "Show sales trend over time",
    ]
    for col, suggestion in zip(
        [suggestion_col1, suggestion_col2, suggestion_col3, suggestion_col4],
        suggestions,
    ):
        with col:
            if st.button(suggestion, use_container_width=True, key=f"suggest_{suggestion[:18]}"):
                st.session_state["analysis_question"] = suggestion
                st.rerun()

    # --------------------------------------------------------
    # Conversation history as analyst chat cards
    # --------------------------------------------------------
    history = st.session_state.get("conversation_history", [])
    if history:
        st.markdown("### 🧠 Analyst Conversation")
        for idx, item in enumerate(history[-6:]):
            st.markdown(
                f"""
                <div style="margin:.65rem 0 1rem 0;">
                    <div style="padding:.8rem 1rem;border-radius:14px;border:1px solid rgba(49,51,63,.10);background:rgba(49,51,63,.035);">
                        <div style="font-size:.78rem;font-weight:700;color:#6b7280;margin-bottom:.25rem;">YOU</div>
                        <div style="font-size:1rem;font-weight:560;">{item.get('question','')}</div>
                    </div>
                    <div style="margin:.45rem 0 0 1.6rem;padding:1rem 1.1rem;border-radius:14px;border:1px solid rgba(49,51,63,.12);background:rgba(255,255,255,.65);box-shadow:0 2px 10px rgba(0,0,0,.025);">
                        <div style="font-size:.78rem;font-weight:700;color:#6b7280;margin-bottom:.35rem;">🤖 AI ANALYST</div>
                        <div style="line-height:1.55;">{item.get('insight','')}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # Question composer
    # --------------------------------------------------------
    composer_col1, composer_col2 = st.columns([5, 1])
    with composer_col1:
        question = st.text_input(
            "Ask a question about your dataset",
            placeholder="Try: Which category has the highest profit margin?",
            key="analysis_question",
            label_visibility="visible",
        )
    with composer_col2:
        st.write("")
        st.write("")
        if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_ai_chat"):
            st.session_state.conversation_history = []
            st.rerun()

    if history:
        st.caption("💡 Follow-up questions work too — for example: **What about profit?** or **Now compare India and USA.**")

    st.markdown(
        "<div class='small-muted' style='margin:.25rem 0 .9rem 0;'>"
        "AI Analyst workflow: <b>Question → Analysis Plan → Pandas Computation → Visualization → Insight</b>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ========================================================
    # ANALYZE
    # ========================================================

    # ANALYZE
    # ========================================================

    if st.button(
        "Analyze",
        type="primary"
    ):

        if not question:

            st.warning(
                "Please enter a question."
            )

        else:

            try:

                # ==============================================
                # AI PLAN
                # ==============================================

                with st.spinner(
                    "🤖 AI is understanding your question..."
                ):

                    planner_question = build_contextual_question(question)
                    plan = understand_question(
                        planner_question,
                        df.columns.tolist(),
                        numeric_columns,
                        categorical_columns
                    )


                with st.expander("🧠 View AI Analysis Plan", expanded=False):
                    st.json(plan)


                # ==============================================
                # EXTRACT PLAN
                # ==============================================

                operation = plan.get(
                    "operation"
                )

                column = plan.get(
                    "column"
                )

                group_by = plan.get(
                    "group_by"
                )

                aggregation = plan.get(
                    "aggregation"
                )

                n = plan.get(
                    "n"
                )

                date_column = plan.get(
                    "date_column"
                )

                granularity = plan.get(
                    "granularity"
                )


                # ==============================================
                # SMART DATE HANDLING
                # ==============================================

                # The AI planner currently supports the existing
                # operations. If it selects a detected date
                # column for grouping, automatically convert it
                # to datetime before analysis.

                working_df = filtered_df.copy()

                if group_by in date_columns:

                    working_df[group_by] = pd.to_datetime(
                        working_df[group_by],
                        errors="coerce"
                    )

                    # For questions mentioning month/year/
                    # quarter/week, derive the requested period.
                    question_lower = question.lower()

                    if "month" in question_lower:

                        working_df["_AI_DATE_GROUP_"] = (
                            working_df[group_by]
                            .dt.to_period("M")
                            .dt.start_time
                        )

                        group_by = "_AI_DATE_GROUP_"

                    elif "quarter" in question_lower:

                        working_df["_AI_DATE_GROUP_"] = (
                            working_df[group_by]
                            .dt.to_period("Q")
                            .dt.start_time
                        )

                        group_by = "_AI_DATE_GROUP_"

                    elif "year" in question_lower:

                        working_df["_AI_DATE_GROUP_"] = (
                            working_df[group_by]
                            .dt.to_period("Y")
                            .dt.start_time
                        )

                        group_by = "_AI_DATE_GROUP_"

                    elif "week" in question_lower:

                        working_df["_AI_DATE_GROUP_"] = (
                            working_df[group_by]
                            .dt.to_period("W")
                            .dt.start_time
                        )

                        group_by = "_AI_DATE_GROUP_"


                # ==============================================
                # VALIDATE
                # ==============================================

                if column and column not in working_df.columns:

                    st.error(
                        f"Column '{column}' does not exist."
                    )

                    st.stop()


                if (
                    group_by
                    and group_by not in working_df.columns
                ):

                    st.error(
                        f"Column '{group_by}' does not exist."
                    )

                    st.stop()


                if date_column and date_column not in df.columns:

                    st.error(
                        f"Date column '{date_column}' does not exist."
                    )

                    st.stop()


                # ==============================================
                # AI COMPARISON ANALYSIS
                # ==============================================

                import re

                comparison_values = None
                comparison_dimension = None

                # Detect natural-language comparisons such as:
                # "Compare India vs USA sales and profit"
                # "Compare Electronics and Furniture"
                question_lower = question.lower()
                comparison_match = re.search(
                    r"compare\s+(.+?)\s+(?:vs\.?|versus|and)\s+(.+?)(?:\s+(?:sales|profit|revenue|quantity|amount|average|mean)|$)",
                    question_lower,
                )

                if comparison_match:
                    candidate_a = comparison_match.group(1).strip(" ,.!?")
                    candidate_b = comparison_match.group(2).strip(" ,.!?")

                    # Find the categorical column containing both values.
                    for cat_col in categorical_columns:
                        values_map = {
                            str(v).strip().lower(): v
                            for v in working_df[cat_col].dropna().unique()
                        }
                        if candidate_a in values_map and candidate_b in values_map:
                            comparison_dimension = cat_col
                            comparison_values = [
                                values_map[candidate_a],
                                values_map[candidate_b],
                            ]
                            break

                if comparison_values:
                    operation = "comparison"
                    group_by = comparison_dimension

                    # Choose requested measures. For a business comparison,
                    # show both Sales and Profit when both are available.
                    comparison_measures = []
                    if "sales" in question_lower and "Sales" in numeric_columns:
                        comparison_measures.append("Sales")
                    if "profit" in question_lower and "Profit" in numeric_columns:
                        comparison_measures.append("Profit")
                    if "quantity" in question_lower and "Quantity" in numeric_columns:
                        comparison_measures.append("Quantity")

                    if not comparison_measures:
                        if "Sales" in numeric_columns:
                            comparison_measures.append("Sales")
                        elif numeric_columns:
                            comparison_measures.append(numeric_columns[0])

                    if "average" in question_lower or "mean" in question_lower:
                        comparison_aggregation = "mean"
                    elif "minimum" in question_lower or "lowest" in question_lower:
                        comparison_aggregation = "min"
                    elif "maximum" in question_lower or "highest" in question_lower:
                        comparison_aggregation = "max"
                    else:
                        comparison_aggregation = "sum"

                    comparison_df = working_df[
                        working_df[comparison_dimension].isin(comparison_values)
                    ].copy()

                    agg_result = (
                        comparison_df
                        .groupby(comparison_dimension)[comparison_measures]
                        .agg(comparison_aggregation)
                        .reindex(comparison_values)
                        .reset_index()
                    )

                    st.subheader("⚖️ Comparison Analysis")
                    st.caption(
                        f"Comparing {comparison_dimension}: "
                        f"{comparison_values[0]} vs {comparison_values[1]}"
                    )

                    st.dataframe(
                        agg_result,
                        use_container_width=True,
                        hide_index=True,
                    )

                    # Automatic visualization for a comparison.
                    comparison_chart_type = select_chart_type(
                        "comparison", question, agg_result, comparison_dimension, comparison_measures[0]
                    )
                    show_chart_choice(comparison_chart_type)

                    # Display metric cards with absolute and percentage differences.
                    for measure in comparison_measures:
                        if len(agg_result) == 2:
                            first = float(agg_result.iloc[0][measure])
                            second = float(agg_result.iloc[1][measure])
                            difference = first - second
                            pct = (difference / second * 100) if second != 0 else None

                            c1, c2, c3 = st.columns(3)
                            c1.metric(str(agg_result.iloc[0][comparison_dimension]), f"{first:,.2f}")
                            c2.metric(str(agg_result.iloc[1][comparison_dimension]), f"{second:,.2f}")
                            c3.metric(
                                "Difference",
                                f"{difference:,.2f}",
                                f"{pct:.1f}%" if pct is not None else None,
                            )

                        fig = px.bar(
                            agg_result,
                            x=comparison_dimension,
                            y=measure,
                            text_auto=True,
                            title=f"{measure}: {comparison_values[0]} vs {comparison_values[1]}",
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    analysis_text = agg_result.to_string(index=False)

                # ==============================================
                # DATE TREND
                # ==============================================

                elif operation == "date_trend":

                    if not date_column:

                        st.error(
                            "The AI did not identify a date column."
                        )

                        st.stop()

                    if not column:

                        st.error(
                            "The AI did not identify a numeric measure."
                        )

                        st.stop()

                    if column not in numeric_columns:

                        st.error(
                            f"'{column}' must be a numeric column "
                            "for date trend analysis."
                        )

                        st.stop()

                    if granularity not in [
                        "day",
                        "week",
                        "month",
                        "quarter",
                        "year"
                    ]:

                        st.error(
                            "Unsupported date granularity."
                        )

                        st.stop()


                    trend_df = working_df.copy()

                    trend_df["_AI_DATE_"] = pd.to_datetime(
                        trend_df[date_column],
                        errors="coerce"
                    )

                    trend_df = trend_df.dropna(
                        subset=["_AI_DATE_"]
                    )


                    if trend_df.empty:

                        st.error(
                            f"No valid dates were found in "
                            f"'{date_column}'."
                        )

                        st.stop()


                    # ------------------------------------------
                    # CREATE TIME PERIOD
                    # ------------------------------------------

                    if granularity == "day":

                        trend_df["_AI_PERIOD_"] = (
                            trend_df["_AI_DATE_"]
                            .dt.floor("D")
                        )

                    elif granularity == "week":

                        trend_df["_AI_PERIOD_"] = (
                            trend_df["_AI_DATE_"]
                            .dt.to_period("W")
                            .dt.start_time
                        )

                    elif granularity == "month":

                        trend_df["_AI_PERIOD_"] = (
                            trend_df["_AI_DATE_"]
                            .dt.to_period("M")
                            .dt.start_time
                        )

                    elif granularity == "quarter":

                        trend_df["_AI_PERIOD_"] = (
                            trend_df["_AI_DATE_"]
                            .dt.to_period("Q")
                            .dt.start_time
                        )

                    else:

                        trend_df["_AI_PERIOD_"] = (
                            trend_df["_AI_DATE_"]
                            .dt.to_period("Y")
                            .dt.start_time
                        )


                    # ------------------------------------------
                    # AGGREGATION
                    # ------------------------------------------

                    aggregation_map = {
                        "sum": "sum",
                        "mean": "mean",
                        "min": "min",
                        "max": "max",
                        "count": "count"
                    }

                    agg_func = aggregation_map.get(
                        aggregation or "sum"
                    )

                    if agg_func is None:

                        st.error(
                            f"Unsupported aggregation: {aggregation}"
                        )

                        st.stop()


                    result = (
                        trend_df
                        .groupby("_AI_PERIOD_")[column]
                        .agg(agg_func)
                        .reset_index()
                    )

                    result = result.rename(
                        columns={
                            "_AI_PERIOD_": "Date"
                        }
                    )

                    result = result.sort_values(
                        "Date"
                    )


                    # ------------------------------------------
                    # RESULT
                    # ------------------------------------------

                    st.subheader(
                        "📈 Date Trend Analysis"
                    )

                    st.caption(
                        f"{aggregation or 'sum'} of {column} "
                        f"by {granularity} using {date_column}"
                    )

                    st.dataframe(
                        result,
                        use_container_width=True
                    )


                    # ------------------------------------------
                    # CHART
                    # ------------------------------------------

                    fig = px.line(
                        result,
                        x="Date",
                        y=column,
                        markers=True,
                        title=(
                            f"{(aggregation or 'sum').title()} "
                            f"{column} by {granularity.title()}"
                        )
                    )

                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title=column
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )


                    # ------------------------------------------
                    # HIGHEST / LOWEST PERIOD
                    # ------------------------------------------

                    if not result.empty:

                        highest_row = result.loc[
                            result[column].idxmax()
                        ]

                        lowest_row = result.loc[
                            result[column].idxmin()
                        ]

                        metric1, metric2 = st.columns(2)

                        with metric1:

                            highest_date = highest_row["Date"]

                            if hasattr(
                                highest_date,
                                "strftime"
                            ):

                                highest_date = (
                                    highest_date.strftime(
                                        "%Y-%m-%d"
                                    )
                                )

                            st.metric(
                                "Highest Period",
                                str(highest_date),
                                f"{highest_row[column]:,.2f}"
                            )

                        with metric2:

                            lowest_date = lowest_row["Date"]

                            if hasattr(
                                lowest_date,
                                "strftime"
                            ):

                                lowest_date = (
                                    lowest_date.strftime(
                                        "%Y-%m-%d"
                                    )
                                )

                            st.metric(
                                "Lowest Period",
                                str(lowest_date),
                                f"{lowest_row[column]:,.2f}"
                            )


                    analysis_text = result.to_string(
                        index=False
                    )


                # ==============================================
                # TOTAL
                # ==============================================

                elif operation == "total":

                    value = working_df[column].sum()

                    st.subheader(
                        "📊 Analysis Result"
                    )

                    st.metric(
                        f"Total {column}",
                        f"{value:,.2f}"
                    )

                    analysis_text = (
                        f"Total {column}: {value:,.2f}"
                    )


                # ==============================================
                # AVERAGE
                # ==============================================

                elif operation == "average":

                    value = working_df[column].mean()

                    st.subheader(
                        "📊 Analysis Result"
                    )

                    st.metric(
                        f"Average {column}",
                        f"{value:,.2f}"
                    )

                    analysis_text = (
                        f"Average {column}: {value:,.2f}"
                    )


                # ==============================================
                # MINIMUM
                # ==============================================

                elif operation == "minimum":

                    value = working_df[column].min()

                    st.subheader(
                        "📊 Analysis Result"
                    )

                    st.metric(
                        f"Minimum {column}",
                        f"{value:,.2f}"
                    )

                    analysis_text = (
                        f"Minimum {column}: {value:,.2f}"
                    )


                # ==============================================
                # MAXIMUM
                # ==============================================

                elif operation == "maximum":

                    value = working_df[column].max()

                    st.subheader(
                        "📊 Analysis Result"
                    )

                    st.metric(
                        f"Maximum {column}",
                        f"{value:,.2f}"
                    )

                    analysis_text = (
                        f"Maximum {column}: {value:,.2f}"
                    )


                # ==============================================
                # COUNT
                # ==============================================

                elif operation == "count":

                    value = working_df[column].count()

                    st.subheader(
                        "📊 Analysis Result"
                    )

                    st.metric(
                        f"Count of {column}",
                        f"{value:,}"
                    )

                    analysis_text = (
                        f"Count of {column}: {value:,}"
                    )


                # ==============================================
                # UNIQUE COUNT
                # ==============================================

                elif operation == "unique_count":

                    value = working_df[column].nunique()

                    st.subheader(
                        "📊 Analysis Result"
                    )

                    st.metric(
                        f"Unique {column}",
                        f"{value:,}"
                    )

                    analysis_text = (
                        f"Unique {column}: {value:,}"
                    )


                # ==============================================
                # PROFIT MARGIN
                # ==============================================

                elif operation == "profit_margin":

                    profit_col = column if column in working_df.columns else None

                    if not profit_col:
                        profit_candidates = [
                            c for c in working_df.select_dtypes(include=np.number).columns
                            if "profit" in str(c).lower()
                        ]
                        profit_col = profit_candidates[0] if profit_candidates else None

                    sales_candidates = [
                        c for c in working_df.select_dtypes(include=np.number).columns
                        if any(
                            key in str(c).lower()
                            for key in ["sales", "revenue", "turnover", "amount"]
                        )
                    ]

                    sales_col = sales_candidates[0] if sales_candidates else None

                    if not profit_col or not sales_col:
                        st.error(
                            "Profit margin requires both a profit column and a sales/revenue column."
                        )
                        st.stop()

                    if group_by and group_by in working_df.columns:
                        margin_result = (
                            working_df
                            .groupby(group_by)[[profit_col, sales_col]]
                            .sum()
                            .reset_index()
                        )
                        margin_result["Profit Margin (%)"] = np.where(
                            margin_result[sales_col].abs() > 0,
                            (margin_result[profit_col] / margin_result[sales_col]) * 100,
                            np.nan
                        )
                        result = margin_result[
                            [group_by, "Profit Margin (%)"]
                        ].sort_values(
                            by="Profit Margin (%)",
                            ascending=False
                        )

                        st.subheader("📊 Profit Margin Analysis")
                        st.dataframe(result, use_container_width=True)

                        render_result_kpis(
                            result,
                            "Profit Margin (%)",
                            group_by,
                            "Profit margin highlights"
                        )

                        chart_type = select_chart_type(
                            operation,
                            question,
                            result,
                            group_by,
                            "Profit Margin (%)"
                        )
                        show_chart_choice(chart_type)
                        render_auto_chart(
                            result,
                            chart_type,
                            group_by,
                            "Profit Margin (%)",
                            f"Profit Margin by {group_by}"
                        )

                        analysis_text = result.to_string(index=False)

                    else:
                        total_sales = pd.to_numeric(
                            working_df[sales_col], errors="coerce"
                        ).sum()
                        total_profit = pd.to_numeric(
                            working_df[profit_col], errors="coerce"
                        ).sum()

                        margin = (
                            (total_profit / total_sales) * 100
                            if total_sales != 0
                            else np.nan
                        )

                        st.subheader("📊 Profit Margin Analysis")
                        st.metric("Overall Profit Margin", f"{margin:.2f}%")

                        analysis_text = (
                            f"Overall Profit Margin: {margin:.2f}% "
                            f"(Total Profit: {total_profit:,.2f}; "
                            f"Total Sales/Revenue: {total_sales:,.2f})"
                        )


                # ==============================================
                # GROUP BY
                # ==============================================

                elif operation == "group_by":

                    if aggregation == "sum":

                        result = (
                            working_df
                            .groupby(group_by)[column]
                            .sum()
                            .reset_index()
                        )

                    elif aggregation == "mean":

                        result = (
                            working_df
                            .groupby(group_by)[column]
                            .mean()
                            .reset_index()
                        )

                    elif aggregation == "min":

                        result = (
                            working_df
                            .groupby(group_by)[column]
                            .min()
                            .reset_index()
                        )

                    elif aggregation == "max":

                        result = (
                            working_df
                            .groupby(group_by)[column]
                            .max()
                            .reset_index()
                        )

                    elif aggregation == "count":

                        result = (
                            working_df
                            .groupby(group_by)[column]
                            .count()
                            .reset_index()
                        )

                    else:

                        st.error(
                            "Unsupported aggregation."
                        )

                        st.stop()


                    # Sort numeric result descending.
                    result = result.sort_values(
                        by=column,
                        ascending=False
                    )


                    # Rename temporary AI date column.
                    display_group = group_by

                    if group_by == "_AI_DATE_GROUP_":

                        result = result.rename(
                            columns={
                                "_AI_DATE_GROUP_": "Date"
                            }
                        )

                        display_group = "Date"


                    st.subheader(
                        "📊 Analysis Result"
                    )

                    st.dataframe(
                        result,
                        use_container_width=True
                    )

                    render_result_kpis(
                        result,
                        column,
                        display_group,
                        "Automatic result highlights"
                    )

                    # ==========================================
                    # AUTOMATIC CHART SELECTION
                    # ==========================================

                    chart_type = select_chart_type(
                        operation, question, result, display_group, column
                    )

                    # Datetime grouped results are always better represented
                    # as a time-series line chart.
                    if (
                        display_group == "Date"
                        or pd.api.types.is_datetime64_any_dtype(result[display_group])
                    ):
                        chart_type = "line"

                    show_chart_choice(chart_type)
                    render_auto_chart(
                        result,
                        chart_type,
                        display_group,
                        column,
                        f"{aggregation.title()} {column} by {display_group}"
                    )


                    analysis_text = result.to_string(
                        index=False
                    )


                # ==============================================
                # TOP N
                # ==============================================

                elif operation == "top_n":

                    n = int(n or 5)

                    # If group_by exists, aggregate first.
                    if group_by and group_by in working_df.columns:

                        top_result = (
                            working_df
                            .groupby(group_by)[column]
                            .sum()
                            .reset_index()
                            .sort_values(
                                by=column,
                                ascending=False
                            )
                            .head(n)
                        )

                        result = top_result

                        x_column = group_by

                    else:

                        result = (
                            working_df
                            .nlargest(
                                n,
                                column
                            )
                        )

                        x_column = (
                            group_by
                            if group_by
                            else result.columns[0]
                        )


                    st.subheader(
                        f"🏆 Top {n}"
                    )

                    st.dataframe(
                        result,
                        use_container_width=True
                    )

                    render_result_kpis(
                        result,
                        column,
                        x_column,
                        "Automatic result highlights"
                    )

                    chart_type = select_chart_type(
                        operation, question, result, x_column, column
                    )
                    show_chart_choice(chart_type)
                    render_auto_chart(
                        result, chart_type, x_column, column, f"Top {n} by {column}"
                    )


                    analysis_text = result.to_string(
                        index=False
                    )


                # ==============================================
                # BOTTOM N
                # ==============================================

                elif operation == "bottom_n":

                    n = int(n or 5)

                    # If group_by exists, aggregate first.
                    if group_by and group_by in working_df.columns:

                        bottom_result = (
                            working_df
                            .groupby(group_by)[column]
                            .sum()
                            .reset_index()
                            .sort_values(
                                by=column,
                                ascending=True
                            )
                            .head(n)
                        )

                        result = bottom_result

                        x_column = group_by

                    else:

                        result = (
                            working_df
                            .nsmallest(
                                n,
                                column
                            )
                        )

                        x_column = (
                            group_by
                            if group_by
                            else result.columns[0]
                        )


                    st.subheader(
                        f"📉 Bottom {n}"
                    )

                    st.dataframe(
                        result,
                        use_container_width=True
                    )

                    render_result_kpis(
                        result,
                        column,
                        x_column,
                        "Automatic result highlights"
                    )

                    chart_type = select_chart_type(
                        operation, question, result, x_column, column
                    )
                    show_chart_choice(chart_type)
                    render_auto_chart(
                        result, chart_type, x_column, column, f"Bottom {n} by {column}"
                    )


                    analysis_text = result.to_string(
                        index=False
                    )


                # ==============================================
                # CORRELATION
                # ==============================================

                elif operation == "correlation":

                    if len(numeric_columns) < 2:

                        st.error(
                            "At least two numeric columns "
                            "are required."
                        )

                        st.stop()


                    correlation = (
                        working_df[numeric_columns]
                        .corr()
                    )


                    st.subheader(
                        "📈 Correlation Matrix"
                    )

                    st.dataframe(
                        correlation,
                        use_container_width=True
                    )


                    chart_type = select_chart_type(
                        operation, question, correlation
                    )
                    show_chart_choice(chart_type)

                    fig = px.imshow(
                        correlation,
                        text_auto=True,
                        title="Correlation Matrix"
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )


                    # If AI identified two specific numeric
                    # columns, also show a scatter plot.
                    if (
                        column in numeric_columns
                        and group_by in numeric_columns
                        and column != group_by
                    ):

                        scatter_fig = px.scatter(
                            working_df,
                            x=column,
                            y=group_by,
                            title=(
                                f"{column} vs {group_by}"
                            )
                        )

                        st.plotly_chart(
                            scatter_fig,
                            use_container_width=True
                        )


                    analysis_text = correlation.to_string()


                # ==============================================
                # UNSUPPORTED
                # ==============================================

                else:

                    st.warning(
                        f"Operation '{operation}' "
                        "is not supported yet."
                    )

                    st.stop()


                # ==============================================
                # AI BUSINESS INSIGHT
                # ==============================================

                with st.spinner(
                    "💡 AI is generating business insights..."
                ):

                    insight = generate_insight(
                        question
                        + "\n\nStrict evidence rule: report only patterns directly supported by the supplied analysis result. Do not claim causes, motivations, external factors, recommendations, or future outcomes unless they are explicitly present in the analysis result.",
                        analysis_text
                    )


                st.subheader("💡 AI Business Insight")
                st.info(insight)

                # Save the completed analysis so the next question can
                # naturally refer to it. Streamlit Session State persists
                # this context across reruns in the current browser session.
                add_conversation_turn(
                    question,
                    plan,
                    insight,
                    analysis_text
                )

                # ==============================================
                # DOWNLOAD ANALYSIS NOTE AS PDF
                # ==============================================

                def create_analysis_pdf(question_text, plan, result_text, insight_text):
                    buffer = BytesIO()

                    doc = SimpleDocTemplate(
                        buffer,
                        pagesize=A4,
                        rightMargin=40,
                        leftMargin=40,
                        topMargin=40,
                        bottomMargin=40
                    )

                    styles = getSampleStyleSheet()
                    title_style = ParagraphStyle(
                        "ReportTitle",
                        parent=styles["Title"],
                        alignment=TA_CENTER,
                        spaceAfter=18
                    )
                    heading_style = ParagraphStyle(
                        "ReportHeading",
                        parent=styles["Heading2"],
                        spaceBefore=12,
                        spaceAfter=8
                    )
                    body_style = ParagraphStyle(
                        "ReportBody",
                        parent=styles["BodyText"],
                        leading=15,
                        spaceAfter=8
                    )

                    story = [
                        Paragraph("AI Data Analyst — Analysis Note", title_style),
                        Paragraph("Question", heading_style),
                        Paragraph(str(question_text).replace("&", "&amp;"), body_style),
                        Paragraph("AI Analysis Plan", heading_style),
                        Paragraph(str(plan).replace("&", "&amp;"), body_style),
                        Paragraph("Analysis Result", heading_style),
                        Paragraph(str(result_text).replace("\n", "<br/>").replace("&", "&amp;"), body_style),
                        Paragraph("AI Business Insight", heading_style),
                        Paragraph(str(insight_text).replace("\n", "<br/>").replace("&", "&amp;"), body_style),
                        Spacer(1, 12),
                        Paragraph("Generated by AI Data Analyst", styles["Italic"]),
                    ]

                    doc.build(story)
                    buffer.seek(0)
                    return buffer.getvalue()

                pdf_data = create_analysis_pdf(
                    question,
                    plan,
                    analysis_text,
                    insight
                )

                st.download_button(
                    "📄 Download Analysis Note (PDF)",
                    data=pdf_data,
                    file_name="ai_analysis_note.pdf",
                    mime="application/pdf"
                )


            except Exception as e:

                st.error(
                    f"Something went wrong: {e}"
                )


# ============================================================
# PHASE 11.7 — FOOTER
# ============================================================
if "df" in locals():
    st.markdown("---")
    st.caption("AI Data Analyst • Natural-language analytics • Pandas computation • Plotly visualization • Evidence-based AI insights")
