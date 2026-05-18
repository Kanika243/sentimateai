# SentimateAI 🚀

AI-Powered Financial Sentiment Analysis Dashboard built using Streamlit, VADER Sentiment Analysis, Gemini AI, Yahoo Finance, Alpha Vantage, and NewsAPI.

## 🌐 Live Demo

https://kanika243-sentimateai-app-cvuiyk.streamlit.app/

---

# 📌 Project Overview

SentimateAI is an interactive web dashboard that analyzes financial news sentiment and generates AI-powered market insights.

The application combines:
- Real-time financial news
- NLP sentiment analysis
- Stock/crypto market data
- AI-generated analyst summaries

Users can search for:
- US Stocks
- Cryptocurrency symbols
- General market topics

The system then:
1. Fetches news and financial data
2. Performs sentiment analysis
3. Aggregates sentiment scores
4. Generates an AI analyst verdict
5. Visualizes results with charts and metrics

---

# ✨ Features

- 📈 Stock and Crypto sentiment analysis
- 📰 Real-time news fetching
- 🤖 AI-generated market verdicts using Gemini AI
- 📊 Interactive charts and sentiment visualizations
- 🌙 Modern dark-themed Streamlit UI
- 📉 Yahoo Finance price history integration
- 🔍 Source-level sentiment breakdown
- ⚡ Fast and interactive dashboard experience

---

# 🛠️ Tech Stack

## Frontend
- Streamlit
- Altair
- Pandas

## Backend & APIs
- Python
- Requests
- Yahoo Finance (`yfinance`)
- Alpha Vantage API
- NewsAPI
- Google Gemini AI

## NLP & AI
- VADER Sentiment Analysis
- Gemini Generative AI

---

# 🧠 How It Works

## 1. User Input
The user enters:
- a stock ticker,
- crypto symbol,
- or general topic.

---

## 2. Data Collection
The application fetches:
- financial news from Alpha Vantage,
- headlines from NewsAPI,
- historical market data from Yahoo Finance.

---

## 3. Sentiment Analysis
News headlines are analyzed using:
- VADER sentiment scoring
- Alpha Vantage sentiment labels

The scores are normalized and aggregated into:
- Positive
- Neutral
- Negative sentiment categories

---

## 4. AI Verdict Generation
Gemini AI generates:
- market outlook,
- confidence level,
- analyst-style summary,
- bullish/bearish interpretation.

---

## 5. Visualization
The app displays:
- price charts,
- sentiment charts,
- AI verdict cards,
- live news feed,
- source-level analysis.

---

# 📂 Project Structure

```bash
sentimateai/
│
├── app.py
├── logic.py
├── requirements.txt
├── README.md
└── .gitignore
