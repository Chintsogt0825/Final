import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import datetime
import numpy as np

CSV_FILE = "crypto_prices.csv"

def predict_next_price(crypto_name):
    try:
        # Load the CSV with known headers
        df = pd.read_csv(CSV_FILE, names=[
            'timestamp', 'bitcoin_usd', 'ethereum_usd', 'dogecoin_usd', 'solana_usd'
        ], skiprows=1)  # Skip the header row once manually

        # Drop completely empty rows
        df = df.dropna()

        # Fix timestamps — handle both formats
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', infer_datetime_format=True)
        df = df.dropna(subset=['timestamp'])

        # Fix column types (some rows have dogecoin/solana flipped)
        df = df[
            (df['bitcoin_usd'] > 1000) &  # Bitcoin price must be realistic
            (df['ethereum_usd'] > 100) &
            (df['solana_usd'] > 1) & 
            (df['dogecoin_usd'] < 1)  # Doge should be below 1
        ]

        # Check if crypto column exists
        if f"{crypto_name}_usd" not in df.columns:
            print(f"[PREDICT WARNING] {crypto_name}_usd column not found.")
            return None

        # Prepare data for training
        df['timestamp_ordinal'] = df['timestamp'].map(datetime.toordinal)
        X = df[['timestamp_ordinal']]
        y = df[f"{crypto_name}_usd"]

        if len(X) < 2:
            print(f"[PREDICT WARNING] Not enough clean data for {crypto_name}.")
            return None

        model = LinearRegression()
        model.fit(X, y)

        next_time = datetime.now().toordinal() + 1
        pred = model.predict([[next_time]])[0]

        return round(pred, 2)

    except Exception as e:
        print(f"[PREDICT ERROR] {e}")
        return None

if __name__ == "__main__":
    for crypto in ["bitcoin", "ethereum", "solana", "dogecoin"]:
        pred = predict_next_price(crypto)
        print(f"{crypto} predicted price: ${pred}")
