# utils/price_fetcher.py
import requests

def fetch_crypto_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
        print(f"Making request to: {url}")  # Debug line
        
        response = requests.get(url)
        print(f"Response status: {response.status_code}")  # Debug line
        print(f"Raw response: {response.text}")  # Debug line
        
        response.raise_for_status()  # This will raise an exception for 4XX/5XX status codes
        data = response.json()
        
        # Verify the expected keys exist
        if "bitcoin" not in data or "ethereum" not in data:
            print(f"Unexpected response structure: {data}")
            return None
            
        return {
            "bitcoin": data["bitcoin"]["usd"],
            "ethereum": data["ethereum"]["usd"]
        }
    except Exception as e:
        print(f"Error fetching prices: {str(e)}")
        return None