import streamlit as st
import pandas as pd
import altair as alt
import time
from logic import run_analysis

# ─────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SentimateAI",
    page_icon="🧠",
    layout="wide",
)

# ─────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Base ─────────────────────────────────────── */
    .stApp { background-color: #0E1117; }

    /* ── Cards ────────────────────────────────────── */
    .result-card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }

    /* ── AI Verdict card ──────────────────────────── */
    .verdict-card {
        background: linear-gradient(135deg, #161b22 0%, #1a2332 100%);
        padding: 24px 28px;
        border-radius: 12px;
        border: 1px solid #2d4a6e;
        box-shadow: 0 4px 20px rgba(0, 100, 200, 0.15);
        margin-bottom: 20px;
    }
    .verdict-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #4d94ff;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .verdict-text {
        color: #c9d1d9;
        font-size: 15px;
        line-height: 1.7;
        margin-bottom: 16px;
    }
    .verdict-footer {
        display: flex;
        gap: 20px;
        align-items: center;
    }
    .confidence-pill {
        background: #1f2d3d;
        border: 1px solid #2d4a6e;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 12px;
        color: #4d94ff;
        font-weight: 600;
    }

    /* ── Search Button ────────────────────────────── */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background: linear-gradient(180deg, #00E676 0%, #00C853 100%) !important;
        color: #000000 !important;
        font-weight: 900;
        font-size: 17px;
        padding: 12px 0;
        border: 1px solid #00C853;
        margin-top: 28px;
        transition: transform 0.1s, box-shadow 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.01);
        background: linear-gradient(180deg, #69F0AE 0%, #00E676 100%) !important;
        box-shadow: 0 0 12px rgba(0, 200, 83, 0.5);
        color: #000000 !important;
    }
    .stButton>button:active { transform: scale(0.98); }

    /* ── Typography ───────────────────────────────── */
    h1, h2, h3 { color: #e6edf3 !important; font-family: 'Segoe UI', sans-serif; }
    p, label { color: #c9d1d9 !important; }
    [data-testid="stMetricValue"] { color: #e6edf3; font-size: 28px; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #8b949e; }

    /* ── Inputs ───────────────────────────────────── */
    .stTextInput>div>div>input {
        background-color: #0d1117;
        color: white;
        border: 1px solid #30363d;
    }
    .stSelectbox>div>div>div {
        background-color: #0d1117;
        color: white;
    }

    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# API KEYS
# ─────────────────────────────────────────────────────────
API_KEYS = {
    "alpha_vantage":  st.secrets.get("alpha_vantage", ""),
    "newsapi":        st.secrets.get("newsapi", ""),
    "gemini":         st.secrets.get("gemini", ""), # Changed to gemini
}

# ─────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown(
        "<h1 style='text-align:center;font-size:60px;margin:0;'>🧠</h1>",
        unsafe_allow_html=True,
    )
with col_title:
    st.markdown(
        "<h1 style='font-size:50px;margin-bottom:0;'>SentimateAI</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='font-size:18px;color:#8b949e;margin-top:-10px;'>"
        "Market Intelligence & Trend Sentinel</p>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ─────────────────────────────────────────────────────────
# SEARCH BAR
# ─────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([3, 1, 1])

with c1:
    search_query = st.text_input(
        "Search Ticker or Topic",
        value="AAPL",
        placeholder="e.g. TSLA, Bitcoin, AI",
    )
with c2:
    search_type = st.selectbox(
        "Data Source", ["Stocks (US)", "Crypto", "General Topic"]
    )
with c3:
    analyze_btn = st.button("🚀 SEARCH")

# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────
def _sentiment_color(label: str) -> str:
    label_lower = label.lower()
    if "bull" in label_lower or "positive" in label_lower:
        return "#00E676"
    if "bear" in label_lower or "negative" in label_lower:
        return "#FF5252"
    return "#FFD600"

def _signal_to_display(signal: str) -> str:
    return signal.replace("_", " ").title()

# ─────────────────────────────────────────────────────────
# MAIN LOGIC
# ─────────────────────────────────────────────────────────
if analyze_btn:
    is_financial = search_type != "General Topic"

    with st.status("Initializing Sentinel Engine...", expanded=True) as status:
        st.write("🔄 Fetching data from NewsAPI and Alpha Vantage...")
        result = run_analysis(search_query, search_type, API_KEYS)

        st.write("🧠 Running VADER + Alpha Vantage sentiment analysis...")
        time.sleep(0.4)

        st.write("🤖 Generating Gemini AI verdict...") # Changed Text
        time.sleep(0.3)

        st.write("📊 Aggregating metrics and building charts...")
        time.sleep(0.3)

        status.update(label="✅ Analysis Complete!", state="complete", expanded=False)

    # ── Unpack results ────────────────────────────────────────────────────────
    sentiment    = result["sentiment"]
    sources      = result["sources"]
    yahoo        = result["yahoo"]
    ai_verdict   = result["ai_verdict"]

    avg_score    = sentiment["avg_score"]
    label        = sentiment["label"]
    main_color   = _sentiment_color(label)
    social_df    = pd.DataFrame(sources) if sources else pd.DataFrame(
        columns=["source", "text", "score", "sentiment", "url"]
    )
    price_df     = yahoo.get("price_df", pd.DataFrame())
    current_price = yahoo.get("current_price")
    company_name  = yahoo.get("company_name", search_query)

    # ── KEY METRICS ROW ───────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(
            f'<div class="result-card" style="text-align:center;">'
            f'<h4>Sentiment Signal</h4>'
            f'<h2 style="color:{main_color}!important;">{label}</h2>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m2:
        score_color = main_color
        st.markdown(
            f'<div class="result-card" style="text-align:center;">'
            f'<h4>Avg Score</h4>'
            f'<h2 style="color:{score_color}!important;">{avg_score:+.3f}</h2>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="result-card" style="text-align:center;">'
            f'<h4>Sources Analysed</h4>'
            f'<h2>{sentiment["total"]}</h2>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m4:
        if is_financial and current_price:
            st.markdown(
                f'<div class="result-card" style="text-align:center;">'
                f'<h4>{company_name}</h4>'
                f'<h2>${current_price:,.2f}</h2>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            ai_signal = _signal_to_display(ai_verdict.get("signal", label.upper()))
            signal_color = _sentiment_color(ai_signal)
            st.markdown(
                f'<div class="result-card" style="text-align:center;">'
                f'<h4>AI Signal</h4>'
                f'<h2 style="color:{signal_color}!important;">{ai_signal}</h2>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── AI VERDICT CARD ───────────────────────────────────────────────────────
    verdict_text = ai_verdict.get("verdict", "No verdict generated.")
    confidence   = ai_verdict.get("confidence", 0)
    ai_signal    = _signal_to_display(ai_verdict.get("signal", label.upper()))
    sig_color    = _sentiment_color(ai_signal)

    st.markdown(
        f"""
        <div class="verdict-card">
            <div class="verdict-label">🤖 Gemini AI Analyst Verdict</div>
            <div class="verdict-text">{verdict_text}</div>
            <div class="verdict-footer">
                <span class="confidence-pill">Confidence: {confidence}%</span>
                <span style="color:{sig_color};font-weight:700;font-size:14px;">
                    ▶ {ai_signal}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── CHARTS ────────────────────────────────────────────────────────────────
    if is_financial and not price_df.empty:
        g1, g2 = st.columns([2, 1])

        with g1:
            st.markdown("### 📉 Price Trend (30 days)")
            chart = (
                alt.Chart(price_df)
                .mark_area(
                    line={"color": "#2962FF"},
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(color="#2962FF", offset=0),
                            alt.GradientStop(color="rgba(41,98,255,0)", offset=1),
                        ],
                        x1=1, x2=1, y1=1, y2=0,
                    ),
                )
                .encode(
                    x=alt.X("Date:T", axis=alt.Axis(format="%b %d")),
                    y=alt.Y("Price:Q", scale=alt.Scale(zero=False)),
                )
                .properties(height=300)
            )
            st.altair_chart(chart, use_container_width=True)

        with g2:
            st.markdown("### 📊 Sentiment Split")
            if not social_df.empty:
                donut = (
                    alt.Chart(social_df)
                    .mark_arc(innerRadius=60)
                    .encode(
                        theta=alt.Theta("count()", stack=True),
                        color=alt.Color(
                            "sentiment",
                            scale=alt.Scale(
                                domain=["Positive", "Neutral", "Negative"],
                                range=["#00E676", "#FFD600", "#FF5252"],
                            ),
                        ),
                    )
                    .properties(height=300)
                )
                st.altair_chart(donut, use_container_width=True)

    elif not is_financial and not social_df.empty:
        st.markdown("### 📊 Topic Sentiment Overview")
        bar = (
            alt.Chart(social_df)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                x=alt.X("count()", title="Article / Post Count"),
                y=alt.Y("sentiment", sort=["Positive", "Neutral", "Negative"], title=""),
                color=alt.Color(
                    "sentiment",
                    scale=alt.Scale(
                        domain=["Positive", "Neutral", "Negative"],
                        range=["#00E676", "#FFD600", "#FF5252"],
                    ),
                    legend=None,
                ),
            )
            .properties(height=200)
        )
        st.altair_chart(bar, use_container_width=True)

    # ── SOURCE BREAKDOWN TABLE ────────────────────────────────────────────────
    if not social_df.empty:
        st.markdown("### 📡 Source Breakdown")
        source_summary = (
            social_df.groupby("source")
            .agg(
                Articles=("text", "count"),
                Avg_Score=("score", lambda x: round(x.mean(), 3)),
                Positive=("sentiment", lambda x: (x == "Positive").sum()),
                Negative=("sentiment", lambda x: (x == "Negative").sum()),
            )
            .reset_index()
            .rename(columns={"source": "Source", "Avg_Score": "Avg Score"})
        )
        st.dataframe(source_summary, use_container_width=True, hide_index=True)

    # ── LIVE FEED ─────────────────────────────────────────────────────────────
    st.markdown("### 📰 Live Intelligence Feed")

    for _, row in social_df.iterrows():
        border_color = (
            "#00E676" if row["sentiment"] == "Positive"
            else "#FF5252" if row["sentiment"] == "Negative"
            else "#FFD600"
        )
        url_html = (
            f'<a href="{row["url"]}" target="_blank" '
            f'style="color:{border_color};font-size:0.85em;">↗ Read more</a>'
            if row.get("url") else ""
        )
        st.markdown(
            f"""
            <div class="result-card"
                 style="border-left:5px solid {border_color}; padding:15px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:{border_color}; font-weight:bold;">
                        {row['source']}
                    </span>
                    <span style="color:#8b949e; font-size:0.9em;">
                        Score: {row['score']:+.3f}
                    </span>
                </div>
                <p style="margin:6px 0 4px 0; font-size:1.05em;">{row['text']}</p>
                {url_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

else:
    # ── IDLE STATE ────────────────────────────────────────────────────────────
    st.info("👈 Enter a ticker symbol or topic above to begin real-time analysis.")

    st.markdown("#### How it works")
    col_a, col_b, col_c, col_d = st.columns(4)
    steps = [
        ("📡", "Fetch", "NewsAPI & Alpha Vantage pull fresh data"),
        ("🧮", "Score", "VADER + Alpha Vantage's NLP rate each article"),
        ("🤖", "Analyse", "Gemini AI synthesises a smart analyst verdict"),
        ("📊", "Display", "Charts, scores & a live intelligence feed"),
    ]
    for col, (icon, title, desc) in zip([col_a, col_b, col_c, col_d], steps):
        with col:
            st.markdown(
                f'<div class="result-card" style="text-align:center;">'
                f'<h2>{icon}</h2><h4>{title}</h4>'
                f'<p style="font-size:0.9em;color:#8b949e;">{desc}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )