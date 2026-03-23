import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime
from fastapi import Request
import httpx 
from database import supabase

# Internal Imports
from database import get_holdings
from scrapers import get_nepse_price, get_silver_usd_per_gram, get_global_price, get_pokemon_price, get_usd_npr_rate
from utils.telegram import send_telegram_report

from pydantic import BaseModel

app = FastAPI(title="Nepse Portfolio Tracker")


class StockEntry(BaseModel):
    symbol: str
    qty: float
    cat: str
    buy_price: float = 0.0

TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
MY_CHAT_ID = int(os.getenv("CHAT_ID", 0))

@app.get("/")
async def serve_dashboard():
    """Serves the modern HTML dashboard at the root URL."""
    return FileResponse('static/index.html')

@app.get("/api/dashboard_data")
async def get_dashboard_data():
    """
    The 'Brain' of the dashboard. 
    Calculates live valuations for all 5 asset classes.
    """
    raw_holdings = get_holdings()
    processed_holdings = []
    total_portfolio_npr = 0

    usd_to_npr = get_usd_npr_rate()
    
    # Category indices for Chart.js: [NEPSE, Silver, Crypto, Pokémon, Global]
    cat_totals = {"nepse": 0, "silver": 0, "crypto": 0, "pokemon": 0, "global": 0}

    for item in raw_holdings:
        symbol = item['symbol']
        cat = item['category'].lower()
        qty = float(item['qty'])
        
        # Route to the correct scraper
        price = 0.0
        if cat == 'nepse':
            price = get_nepse_price(symbol)
        elif cat == 'silver':
            price = get_silver_usd_per_gram() * usd_to_npr
        elif cat in ['global', 'us', 'crypto']:
            # Assumes symbol is like 'BTCUSDT'
            price = get_global_price(symbol) * usd_to_npr # Convert USD to JPY
        elif cat == 'pokemon':
            # Assumes symbol is a PriceCharting slug
            price = get_pokemon_price(symbol) * usd_to_npr
            
        line_total = qty * price
        total_portfolio_npr += line_total
        cat_totals[cat] += line_total
        
        processed_holdings.append({
            "symbol": symbol,
            "cat": cat,
            "qty": qty,
            "price": round(price, 2),
            "total": round(line_total, 2)
        })

    # Sort by value (Highest first)
    processed_holdings.sort(key=lambda x: x['total'], reverse=True)

    return {
        "exchange_rate": usd_to_npr,
        "total": round(total_portfolio_npr, 2),
        "topAsset": processed_holdings[0]['symbol'] if processed_holdings else "N/A",
        "topCategory": processed_holdings[0]['cat'].upper() if processed_holdings else "N/A",
        "allocation": [
            cat_totals['nepse'], 
            cat_totals['silver'], 
            cat_totals['crypto'], 
            cat_totals['pokemon'], 
            cat_totals['global']
        ],
        "holdings": processed_holdings
    }

@app.get("/api/report")
async def trigger_report():
    """Endpoint for cron-job.org to trigger Telegram updates."""
    data = await get_dashboard_data()
    success = send_telegram_report(data)
    return {"status": "success" if success else "failed"}

@app.get("/health")
async def health_check():
    """Keep-alive endpoint to prevent Render from sleeping."""
    return {"status": "online", "timestamp": datetime.now().isoformat()}

@app.post("/api/add_stock")
async def add_stock(entry: StockEntry):
    try:
        data = {
            "symbol": entry.symbol.upper(),
            "qty": entry.qty,
            "category": entry.cat.lower(),
            "buy_price": entry.buy_price
        }
        # Insert into your Supabase table
        supabase.table("holdings").insert(data).execute()
        return {"status": "success", "message": f"Added {entry.symbol}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]

        # --- THE SECURITY GUARD ---
        if chat_id != MY_CHAT_ID:
            print(f"Unauthorized access attempt by ID: {chat_id}")
            return {"ok": True} # We return 'ok' so Telegram stops retrying, but we do nothing.
        # ---------------------------

        text = data["message"].get("text", "").lower()

        if "update" in text:
            data = await get_dashboard_data()
            success = send_telegram_report(data)
            return {"status": "success" if success else "failed"}

    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    # Use standard port 8000 for local testing
    uvicorn.run(app, host="0.0.0.0", port=8000)