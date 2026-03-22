import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve credentials
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL or SUPABASE_KEY is missing in environment variables.")

# Initialize the Supabase Client
# This instance will be used across the application to interact with your Postgres DB
supabase: Client = create_client(url, key)

def get_holdings():
    """
    Helper function to fetch all assets from the 'holdings' table.
    """
    try:
        response = supabase.table("holdings").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Database Error: {e}")
        return []

def update_asset_price(symbol: str, price: float):
    """
    Example helper to update a price if you decide to cache 
    prices in the DB instead of scraping on every request.
    """
    try:
        supabase.table("holdings").update({"last_price": price}).eq("symbol", symbol).execute()
    except Exception as e:
        print(f"Failed to update price for {symbol}: {e}")