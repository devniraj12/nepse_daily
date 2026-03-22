# Create a temporary file: test_db.py
from fastapi import FastAPI


app = FastAPI(title="Nepse Portfolio Tracker")
from app . database import get_holdings

data = get_holdings()
print(f"Data from Supabase: {data}")