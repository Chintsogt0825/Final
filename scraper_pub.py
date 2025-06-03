import requests
from bs4 import BeautifulSoup
import json
import re
import time
import zenoh


# --- Function: Scrape BTC & ETH from CoinMarketCap ---
def get_crypto_prices_bs_embedded_json():
    url = "https://coinmarketcap.com/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print("[SCRAPER] Failed to fetch data:", e)
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    script_tag = None
    for script in soup.find_all("script"):
        if script.string and "window.__INITIAL_STATE__" in script.string:
            script_tag = script
            break

    if not script_tag:
        print("[SCRAPER] No script tag with initial state found")
        return {}

    match = re.search(r"window\.__INITIAL_STATE__\s*=\s*({.*});", script_tag.string, re.DOTALL)
    if not match:
        print("[SCRAPER] No JSON data found in script")
        return {}

    try:
        json_text = match.group(1)
        data = json.loads(json_text)
    except Exception as e:
        print("[SCRAPER] Error parsing JSON:", e)
        return {}

    # Extract prices
    prices = {}
    try:
        listings = data["cryptocurrency"]["listingLatest"]["data"]
        for coin in listings:
            symbol = coin.get("symbol", "").lower()
            if symbol in ["btc", "eth"]:
                price = coin["quote"]["USD"]["price"]
                if symbol == "btc":
                    prices["bitcoin"] = round(price, 2)
                elif symbol == "eth":
                    prices["ethereum"] = round(price, 2)
    except Exception as e:
        print("[SCRAPER] Error extracting prices from JSON:", e)

    return prices

# --- Zenoh Publisher Setup ---
def start_publishing():
    try:
        z = zenoh.open(zenoh.Config())
        pub = z.declare_publisher("crypto/prices")
        print("[ZENOH] Publisher ready...")

        while True:
            prices = get_crypto_prices_bs_embedded_json()
            if prices:
                json_str = json.dumps(prices)
                pub.put(json_str.encode())
                print("[PUBLISH] Sent:", prices)
            else:
                print("[PUBLISH] No prices to send.")

            time.sleep(10)  # Scrape every 10 seconds

    except Exception as e:
        print("[ZENOH ERROR]", e)

if __name__ == "__main__":
    start_publishing()
