import time
import requests
import json
import zenoh
import csv
from datetime import datetime
from bs4 import BeautifulSoup
import os
# cd C:\Asia university\advanced computer programming\crypto_tracker
# python zenoh_sub_dash.py
# python zenoh_pub.py
# python analyze_and_predict.py
# ==== Configuration ====
CRYPTO_IDS = ["bitcoin", "ethereum", "dogecoin", "solana"]
VS_CURRENCY = "usd"
CSV_FILE = CSV_FILE = "C:\\Asia university\\advanced computer programming\\crypto_tracker\\crypto_prices.csv"
ZENOH_PRICE_KEY = "crypto/prices"
ZENOH_NEWS_KEY = "crypto/news"

# ==== Initialize Zenoh ====
session = zenoh.open(zenoh.Config())

# ==== Create CSV File (if not exists or empty) ====
def init_csv():
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            headers = ["timestamp"] + [f"{crypto}_{VS_CURRENCY}" for crypto in CRYPTO_IDS]
            writer.writerow(headers)
            print(f"[INIT] CSV created with headers: {headers}")
    else:
        print(f"[INIT] CSV already exists and is not empty.")

# ==== Append Prices to CSV ====
def append_to_csv(timestamp, prices):
    row = [timestamp] + [prices.get(crypto, "NA") for crypto in CRYPTO_IDS]
    try:
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        print(f"[CSV] Appended row: {row}")
    except PermissionError:
        print("[ERROR] Permission denied while writing to CSV. Close the file if it's open in Excel.")
    except Exception as e:
        print(f"[ERROR] CSV Write Error: {e}")

# ==== Fetch Crypto Prices ====
def fetch_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(CRYPTO_IDS),
        "vs_currencies": VS_CURRENCY
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        prices = {crypto: data.get(crypto, {}).get(VS_CURRENCY, 0) for crypto in CRYPTO_IDS}
        if all(price == 0 for price in prices.values()):
            print("[WARN] Skipping publish due to 0 prices.")
            return None
        return prices
    except Exception as e:
        print("[ERROR] Price Fetch Error:", e)
        return None

# ==== Fetch Crypto News (CryptoPanic RSS Alternative) ====
def fetch_crypto_news():
    try:
        url = "https://cryptopanic.com/news"
        headers = { "User-Agent": "Mozilla/5.0" }
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

# ==== Run Loop ====
init_csv()

while True:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    prices = fetch_prices()
    if prices:
        timestamp = datetime.now().isoformat()  # ISO format timestamp
        payload = {"timestamp": timestamp, "prices": prices}
        session.put(ZENOH_PRICE_KEY, json.dumps(payload))
        append_to_csv(timestamp, prices) 

    news = fetch_crypto_news()
    if news:
        session.put(ZENOH_NEWS_KEY, json.dumps(news))
        print(f"[PUB] Published {len(news)} news items.")

    time.sleep(10)
