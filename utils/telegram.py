import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def send_telegram_report(data: dict):
    """
    Formats and sends a professional Markdown report to the user.
    'data' is the dictionary returned by get_dashboard_data() in main.py.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    
    if not token or not chat_id:
        print("Telegram Error: Credentials missing.")
        return False

    # 1. Header with Date
    rate_used = data.get('exchange_rate', 'Live')
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"🔔 *Daily Portfolio Update*\n📅 _{now} JST_\n\n"

    # 2. Summary Cards (Formatted for mobile readability)
    msg += f"💱 *USD/NPR Rate:* `{rate_used}`\n\n"
    msg += f"💰 *Total Valuation:* `NPR {data['total']:,.2f}`\n"
    msg += f"🏆 *Top Performer:* `{data['topAsset']}` ({data['topCategory']})\n"
    msg += "--- --- --- --- ---\n\n"

    # 3. Asset Breakdown Table
    # We use monospaced code blocks (`) to ensure columns align in Telegram
    msg += "*📈 Top Holdings Breakdown:*\n"
    msg += "```\n"
    msg += f"{'Asset':<7} | {'Qty':<4} | {'Value (JPY)':>9}\n"
    msg += "-" * 26 + "\n"
    
    # Show only top 8 assets to avoid hitting Telegram's message character limit
    for h in data['holdings'][:8]:
        symbol = h['symbol'][:7] # Truncate long symbols
        qty = h['qty']
        total = h['total']
        msg += f"{symbol:<7} | {qty:<4} | {total:>9,.0f}\n"
    
    msg += "```\n"

    # 4. Allocation Summary
    msg += "\n*📊 Sector Allocation:*\n"
    categories = ['NEPSE', 'Silver', 'Crypto', 'Pokémon', 'Global']
    for i, cat in enumerate(categories):
        val = data['allocation'][i]
        percent = (val / data['total'] * 100) if data['total'] > 0 else 0
        msg += f"• {cat}: `{percent:.1f}%`\n"

    # 5. Footer
    msg += "\n🔗 [View Full Dashboard](https://nepse-portfolio-phi.vercel.app/)"

    # Send Request
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Telegram API Error: {e}")
        return False