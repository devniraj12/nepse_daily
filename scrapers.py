from datetime import datetime

import requests
from bs4 import BeautifulSoup
import re
import yfinance as yf

# 1. NEPSE Scraper (using ShareSansar)
def get_nepse_price(symbol):
    """
    Scrapes the last traded price for a given NEPSE symbol.
    """
    url = f"https://www.sharesansar.com/company/{symbol.upper()}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for the specific price span on ShareSansar
            price_element = soup.find("span", {"class": "comp-price"})
            if price_element:
                # Remove commas (e.g., 1,200 -> 1200) and convert to float
                return float(price_element.text.replace(',', ''))
        
        print(f"Warning: Could not fetch price for {symbol}")
        return 0.0
    except Exception as e:
        print(f"NEPSE Scrape Error for {symbol}: {e}")
        return 0.0

# 2. Silver Price Scraper (Silver in JPY per gram)
def get_silver_usd_per_gram():
    """
    Fetches the current silver price in JPY/gram using a commodities API or finance site.
    """
    try:
        # Using a reliable financial data source for commodities
        url = "https://query1.finance.yahoo.com/v8/finance/chart/SI=F" # Silver Futures
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = response.json()
        price_usd_ounce = data['chart']['result'][0]['meta']['regularMarketPrice']
        
        return round(price_usd_ounce, 2)
    except Exception as e:
        print(f"Silver Fetch Error: {e}")
        return 0.0

# 3. Crypto Scraper (using Binance Public API)
def get_crypto_price(symbol="BTCUSDT"):
    """
    Fetches live crypto price from Binance (No API key required for public ticker).
    """
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
        response = requests.get(url)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"Crypto Fetch Error: {e}")
        return 0.0

def get_global_price(symbol):
    """Fetches live price for global stocks (AAPL, TSLA, 7203.T, etc.)"""
    try:
        ticker = yf.Ticker(symbol)
        # 'fast_info' is the quickest way to get the last price in 2026
        price = ticker.fast_info['last_price']
        return round(price, 2)
    except Exception as e:
        print(f"Global Scraper Error ({symbol}): {e}")
        return 0.0
# 4. Pokémon Sealed Box Scraper (using PriceCharting)
def get_pokemon_price(slug):
    """
    Scrapes 'Ungraded' (Factory Sealed) price from PriceCharting.
    Example slug: 'pokemon-surging-sparks/booster-box'
    """
    try:
        url = f"https://www.pricecharting.com/game/{slug}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # PriceCharting stores the 'Ungraded' price in a specific table cell
        price_text = soup.find("td", {"id": "price_details"}).find("span", {"class": "price"}).text
        # Convert '$250.07' to float
        price_usd = float(re.sub(r'[^\d.]', '', price_text))
        
        # Convert to JPY (Approximate or fetch live rate)
        return round(price_usd, 2)
    except Exception as e:
        print(f"Pokemon Scrape Error for {slug}: {e}")
        return 0.0

def get_usd_npr_rate():
    """Fetches the official USD to NPR exchange rate from Nepal Rastra Bank."""
    today = datetime.now().strftime('%Y-%m-%d')
    # The API requires 'from' and 'to' parameters
    url = f"https://www.nrb.org.np/api/forex/v1/rates?page=1&per_page=1&from={today}&to={today}"
    try:
        # NRB Official API (v1)
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Check if the payload exists and has rates
        if data.get('data') and data['data'].get('payload'):
            rates = data['data']['payload'][0].get('rates', [])
            usd_rate = next((item for item in rates if item['currency']['iso3'] == 'USD'), None)
            
            if usd_rate:
                # Return the 'sell' rate
                return float(usd_rate['sell'])
        
        return 134.50  # Fallback if today's data isn't published yet
    except Exception as e:
        print(f"Exchange Rate Error: {e}")
        return 134.50  # Intelligent fallback based on recent trends