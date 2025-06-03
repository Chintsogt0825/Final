import time
import requests
import json
import zenoh
import csv
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup

# ==== Configuration ====
CRYPTO_IDS = ["bitcoin", "ethereum", "dogecoin", "solana"]
VS_CURRENCY = "usd"
CSV_FILE = "crypto_prices.csv"
ZENOH_PRICE_KEY = "crypto/prices"
ZENOH_NEWS_KEY = "crypto/news"

# ==== Initialize Zenoh ====
session = zenoh.open(zenoh.Config())

# ==== Create CSV and Pandas DataFrame ====
def init_csv():
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            headers = ["timestamp"] + [f"{crypto}_{VS_CURRENCY}" for crypto in CRYPTO_IDS]
            writer.writerow(headers)

def append_to_csv(timestamp, prices):
    row = [timestamp] + [prices.get(crypto, "NA") for crypto in CRYPTO_IDS]
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(row)

# ==== Fetch Prices ====
def fetch_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(CRYPTO_IDS),
        "vs_currencies": VS_CURRENCY
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return {crypto: data.get(crypto, {}).get(VS_CURRENCY, 0) for crypto in CRYPTO_IDS}
    except Exception as e:
        print("[ERROR] Price Fetch Error:", e)
        return {}

# ==== Fetch News (from CryptoPanic) ====
def fetch_crypto_news():
    try:
        url = "https://cryptopanic.com/news"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, "html.parser")

        news = []
        for item in soup.select(".news__item-title"):
            title = item.get_text(strip=True)
            link = item.find("a")["href"] if item.find("a") else "#"
            news.append({"title": title, "url": link})

        return news[:5]
    except Exception as e:
        print("[ERROR] News Fetch Error:", e)
        return []

# ==== Main Loop ====
init_csv()

while True:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prices = fetch_prices()
    if prices:
        print(f"[PUB] {timestamp} | Prices:", prices)
        append_to_csv(timestamp, prices)
        session.put(ZENOH_PRICE_KEY, json.dumps(prices))

    news = fetch_crypto_news()
    if news:
        session.put(ZENOH_NEWS_KEY, json.dumps(news))
        print(f"[PUB] Published {len(news)} news items.")

    time.sleep(10)
