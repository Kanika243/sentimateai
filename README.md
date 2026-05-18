# SentimateAI

## What it is
SentimateAI is a Streamlit dashboard that analyzes news sentiment and financial data.
It uses:
- NewsAPI + VADER sentiment scoring
- Alpha Vantage news sentiment for tickers/crypto
- Yahoo Finance price history via `yfinance`
- Google Gemini API for a final analyst-style verdict

## Run locally
1. Activate the virtual environment:
   ```powershell
   & ".\.venv\Scripts\Activate.ps1"
   ```
2. Install requirements:
   ```powershell
   pip install -r requirements.txt
   ```
3. Add API keys in `.streamlit/secrets.toml`:
   ```toml
   alpha_vantage = "YOUR_ALPHA_VANTAGE_KEY"
   newsapi = "YOUR_NEWSAPI_KEY"
   gemini = "YOUR_GEMINI_API_KEY"
   ```
4. Run the app:
   ```powershell
   streamlit run SentimateAI/app.py
   ```
5. Open the browser at:
   ```text
   http://localhost:8501
   ```

## Deploy to Streamlit Cloud
1. Push this repository to GitHub.
2. Create a new app in Streamlit Cloud.
3. Set the repository and entrypoint to `SentimateAI/app.py`.
4. Add the secrets in the Streamlit Cloud app settings.
5. Deploy and open the public URL.
