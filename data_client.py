import os
import certifi
import shutil
import pandas as pd
import numpy as np

# SSL Cert Fix: The user's virtual environment path contains a curly apostrophe ("Ashley's").
# This completely breaks curl/openssl certificate resolution in the requests library. 
# We dynamically copy the cert to a safe path and point the environment to it before importing yfinance.
try:
    clean_cert_path = r"C:\Users\ashle\cacert.pem"
    shutil.copy2(certifi.where(), clean_cert_path)
    os.environ["REQUESTS_CA_BUNDLE"] = clean_cert_path
except Exception as e:
    pass

import yfinance as yf
import numpy as np

def fetch_financial_data(ticker_symbol: str) -> dict:
    """
    Fetches fundamental data for DCF screening: FCF, shares outstanding, current price.
    Also retrieves Beta for the risk-adjustment layer.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        current_price = info.get("currentPrice", info.get("regularMarketPrice", None))
        beta = info.get("beta", 1.0)
        shares_outstanding = info.get("sharesOutstanding", None)
        
        try:
            cash_flow = ticker.cashflow
            if not cash_flow.empty and "Free Cash Flow" in cash_flow.index:
                fcf = cash_flow.loc["Free Cash Flow"].iloc[0]
            elif not cash_flow.empty and "Operating Cash Flow" in cash_flow.index and "Capital Expenditure" in cash_flow.index:
                fcf = cash_flow.loc["Operating Cash Flow"].iloc[0] + cash_flow.loc["Capital Expenditure"].iloc[0]
            else:
                fcf = None
        except Exception:
            fcf = None

        if shares_outstanding is None:
            shares_outstanding = info.get("impliedSharesOutstanding", None)

        if fcf is None or shares_outstanding is None or current_price is None:
            return None

        return {
            "ticker": ticker_symbol,
            "current_price": current_price,
            "beta": beta,
            "fcf": fcf,
            "shares_outstanding": shares_outstanding
        }
    except Exception as e:
        print(f"Error fetching fundamental data for {ticker_symbol}: {e}")
        return None

def fetch_historical_prices(tickers: list, period: str = "2y") -> pd.DataFrame:
    """
    Fetches historical closing prices for a list of tickers.
    """
    try:
        data = yf.download(tickers, period=period, progress=False)["Close"]
        if isinstance(data, pd.Series):
            data = data.to_frame(name=tickers[0])
            
        if data.empty:
            raise ValueError("yfinance returned an empty DataFrame.")
            
        return data
    except Exception as e:
        print(f"Error fetching historical prices: {e}")
        return pd.DataFrame()
