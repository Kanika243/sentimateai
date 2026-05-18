"""
logic.py — SentimateAI Backend
================================
Handles all data fetching, sentiment scoring, and AI verdict generation.

Sentiment strategy:
  • Alpha Vantage  → pre-scored financial news  (for tickers/crypto)
  • NewsAPI        → headlines scored with VADER
  • Gemini API     → final analyst verdict + confidence reasoning

Install deps:
    pip install yfinance requests vaderSentiment google-generativeai
"""

import re
import requests
import yfinance as yf
import pandas as pd
import google.generativeai as genai  # Swapped Anthropic for Gemini
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ─────────────────────────────────────────────────────────
# 1.  DATA FETCHERS
# ─────────────────────────────────────────────────────────

def fetch_yahoo(ticker: str) -> dict:
    """
    Fetch 30-day price history + company metadata via yfinance.
    No API key required.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period="30d")[["Close"]].reset_index()
        hist.rename(columns={"Close": "Price"}, inplace=True)
        
        # Strip timezone so Altair renders cleanly
        hist["Date"] = pd.to_datetime(hist["Date"])
        if hist["Date"].dt.tz is not None:
            hist["Date"] = hist["Date"].dt.tz_convert(None)
            
        info = stock.info
        return {
            "price_df": hist,
            "current_price": (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or (hist["Price"].iloc[-1] if not hist.empty else None)
            ),
            "company_name": info.get("longName", ticker.upper()),
            "sector": info.get("sector", "N/A"),
            "market_cap": info.get("marketCap"),
            "error": None,
        }
    except Exception as e:
        return {
            "price_df": pd.DataFrame(),
            "current_price": None,
            "company_name": ticker.upper(),
            "sector": "N/A",
            "market_cap": None,
            "error": str(e),
        }

def fetch_alpha_vantage_sentiment(query: str, api_key: str) -> list[dict]:
    """
    Alpha Vantage NEWS_SENTIMENT endpoint.
    Returns articles with pre-computed relevance + sentiment scores.
    """
    url = (
        "https://www.alphavantage.co/query"
        f"?function=NEWS_SENTIMENT&tickers={query.upper()}"
        f"&limit=25&sort=LATEST&apikey={api_key}"
    )
    try:
        resp = requests.get(url, timeout=12)
        data = resp.json()

        if "feed" not in data:
            return []

        items = []
        for art in data["feed"]:
            raw_score = float(art.get("overall_sentiment_score", 0))
            raw_label = art.get("overall_sentiment_label", "Neutral")
            items.append({
                "source": "Alpha Vantage",
                "text": art.get("title", "No title"),
                "score": round(raw_score, 3),
                "sentiment": _normalize_av_label(raw_label),
                "url": art.get("url", ""),
            })
        return items

    except Exception:
        return []

def fetch_newsapi(query: str, api_key: str) -> list[dict]:
    """
    NewsAPI — fetch up to 20 recent articles, score each with VADER.
    """
    url = (
        "https://newsapi.org/v2/everything"
        f"?q={query}&pageSize=20&sortBy=publishedAt"
        f"&language=en&apiKey={api_key}"
    )
    try:
        data = requests.get(url, timeout=12).json()
        texts = []
        for art in data.get("articles", []):
            title = art.get("title") or ""
            desc = art.get("description") or ""
            if title:
                texts.append(title + ". " + desc)
        return _vader_score_list(texts, source="NewsAPI")
    except Exception:
        return []


# ─────────────────────────────────────────────────────────
# 2.  SENTIMENT HELPERS
# ─────────────────────────────────────────────────────────

_vader = SentimentIntensityAnalyzer()

def _vader_score_list(texts: list[str], source: str) -> list[dict]:
    """Score a list of text strings with VADER and return structured dicts."""
    results = []
    for t in texts:
        if not t.strip():
            continue
        score = _vader.polarity_scores(t)["compound"]
        results.append({
            "source": source,
            "text": t[:150],
            "score": round(score, 3),
            "sentiment": (
                "Positive" if score > 0.05
                else "Negative" if score < -0.05
                else "Neutral"
            ),
            "url": "",
        })
    return results

def _normalize_av_label(label: str) -> str:
    """Map Alpha Vantage verbose labels → Positive / Neutral / Negative."""
    label = label.lower()
    if "bull" in label:
        return "Positive"
    if "bear" in label:
        return "Negative"
    return "Neutral"

def aggregate_sentiment(items: list[dict]) -> dict:
    """
    Compute average score, overall label, and per-sentiment counts
    from a list of scored items.
    """
    if not items:
        return {
            "avg_score": 0.0,
            "label": "Neutral",
            "counts": {"Positive": 0, "Neutral": 0, "Negative": 0},
            "total": 0,
        }
    avg = sum(i["score"] for i in items) / len(items)
    counts: dict[str, int] = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for i in items:
        counts[i["sentiment"]] = counts.get(i["sentiment"], 0) + 1

    # Use financial language for the label
    if avg > 0.10:
        label = "Bullish"
    elif avg > 0.03:
        label = "Somewhat Bullish"
    elif avg < -0.10:
        label = "Bearish"
    elif avg < -0.03:
        label = "Somewhat Bearish"
    else:
        label = "Neutral"

    return {
        "avg_score": round(avg, 3),
        "label": label,
        "counts": counts,
        "total": len(items),
    }


# ─────────────────────────────────────────────────────────
# 3.  GEMINI AI VERDICT
# ─────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────
# 3.  GEMINI AI VERDICT
# ─────────────────────────────────────────────────────────

def get_ai_verdict(query: str, agg: dict, sources: list[dict], api_key: str) -> dict:
    """
    Send aggregated data to Gemini and get back a structured verdict.
    """
    if not api_key:
        return {
            "verdict": "Gemini API key is missing from secrets. Add it to enable AI analysis.",
            "confidence": 0,
            "signal": agg["label"].upper().replace(" ", "_"),
            "raw": ""
        }

    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # ── DYNAMIC MODEL SELECTION ──────────────────────────────────────────────
    try:
        working_model = None
        # 1. Ask the API for a list of all models this key can see
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # 2. Prefer standard 'flash' or 'pro' text models to avoid weird experimental ones
                if 'flash' in m.name or 'pro' in m.name:
                    working_model = m.name
                    break
        
        # 3. Fallback: If no flash/pro is found, just grab the very first valid model
        if not working_model:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    working_model = m.name
                    break
                    
        if not working_model:
            raise Exception("Your API key does not have access to any text-generation models.")
            
        model = genai.GenerativeModel(working_model)
        
    except Exception as e:
        return {
            "verdict": f"Model initialization failed. Error: {str(e)}",
            "confidence": 0,
            "signal": agg["label"].upper().replace(" ", "_"),
            "raw": ""
        }
    # ─────────────────────────────────────────────────────────────────────────

    # Take a representative sample of top headlines for the prompt
    top = sorted(sources, key=lambda x: abs(x["score"]), reverse=True)[:15]
    headline_block = "\n".join(
        f"  [{i+1}] ({s['source']}, score={s['score']:+.2f}) {s['text'][:120]}"
        for i, s in enumerate(top)
    )

    prompt = f"""You are a senior financial sentiment analyst. Analyse the aggregated social + news sentiment data below for "{query}" and produce a structured report.

=== DATA ===
Total sources analysed: {agg['total']}
Average sentiment score: {agg['avg_score']:+.3f}  (scale: -1.0 bearish → +1.0 bullish)
Breakdown: Positive={agg['counts']['Positive']}  Neutral={agg['counts']['Neutral']}  Negative={agg['counts']['Negative']}

Top headlines/posts (sorted by signal strength):
{headline_block}

=== INSTRUCTIONS ===
Respond in EXACTLY this format, no extra text:

VERDICT: <Write exactly 3 sentences of sharp analyst commentary. Mention specific themes you see in the data. Be direct and opinionated, not wishy-washy.>
CONFIDENCE: <integer 0-100 reflecting how strong/consistent the sentiment signal is>
SIGNAL: <BULLISH | SOMEWHAT_BULLISH | NEUTRAL | SOMEWHAT_BEARISH | BEARISH>"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        return _parse_verdict(raw)
    except Exception as e:
        return {
            "verdict": f"AI verdict unavailable. Error: {str(e)}",
            "confidence": 0,
            "signal": agg["label"].upper().replace(" ", "_"),
            "raw": str(e),
        }

def _parse_verdict(raw: str) -> dict:
    """Extract structured fields from Gemini's formatted response."""
    verdict, confidence, signal = "", 50, "NEUTRAL"

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("VERDICT:"):
            verdict = line[len("VERDICT:"):].strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                confidence = int(re.search(r"\d+", line).group())
            except Exception:
                confidence = 50
        elif line.startswith("SIGNAL:"):
            signal = line[len("SIGNAL:"):].strip().upper()

    return {"verdict": verdict, "confidence": confidence, "signal": signal, "raw": raw}


# ─────────────────────────────────────────────────────────
# 4.  MASTER ORCHESTRATOR
# ─────────────────────────────────────────────────────────

def run_analysis(query: str, search_type: str, api_keys: dict) -> dict:
    """
    Entry point called by app.py.
    """
    all_items: list[dict] = []

    # ── Alpha Vantage ────────────────────────────────────────────────────────
    if api_keys.get("alpha_vantage") and search_type != "General Topic":
        av = fetch_alpha_vantage_sentiment(query, api_keys["alpha_vantage"])
        all_items.extend(av)

    # ── NewsAPI ──────────────────────────────────────────────────────────────
    if api_keys.get("newsapi"):
        news = fetch_newsapi(query, api_keys["newsapi"])
        all_items.extend(news)

    # ── Aggregate ────────────────────────────────────────────────────────────
    agg = aggregate_sentiment(all_items)

    # ── Gemini AI Verdict ────────────────────────────────────────────────────
    gemini_key = api_keys.get("gemini", "")
    ai_verdict = get_ai_verdict(query, agg, all_items, gemini_key)

    # ── Yahoo Finance price data (stocks/crypto only) ────────────────────────
    yahoo_data: dict = {}
    if search_type != "General Topic":
        yahoo_data = fetch_yahoo(query)

    return {
        "sentiment": agg,
        "sources": all_items,
        "yahoo": yahoo_data,
        "ai_verdict": ai_verdict,
    }