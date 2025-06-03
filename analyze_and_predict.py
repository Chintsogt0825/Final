import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import numpy as np
import sys

# Step 1: Load CSV
try:
    df = pd.read_csv("crypto_prices.csv")
except FileNotFoundError:
    print("[ERROR] crypto_prices.csv not found. Please run the publisher first.")
    sys.exit()

# Step 2: Convert timestamp to numerical value
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["timestamp_ordinal"] = df["timestamp"].apply(lambda x: x.toordinal())

# Step 3: Ask user which coin
available_coins = [col for col in df.columns if col not in ["timestamp", "timestamp_ordinal"]]
print("Available coins:", available_coins)
selected_coin = input("Enter coin to analyze (e.g., bitcoin_usd): ").strip()

if selected_coin not in df.columns:
    print("[ERROR] Invalid coin name.")
    sys.exit()

# Step 4: Plot historical trend
plt.figure(figsize=(10, 5))
plt.plot(df["timestamp"], df[selected_coin], label=selected_coin.upper(), color="blue", marker='o')
plt.title(f"{selected_coin.upper()} Price Trend")
plt.xlabel("Time")
plt.ylabel("Price ($)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# Step 5: Train a simple Linear Regression model
X = df[["timestamp_ordinal"]]
y = df[[selected_coin]]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)

# Step 6: Predict next 5 days
future_days = 5
last_day = df["timestamp"].max()
future_dates = pd.date_range(start=last_day + pd.Timedelta(days=1), periods=future_days)

future_ordinals = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
predictions = model.predict(future_ordinals)

# Step 7: Plot Predictions
plt.figure(figsize=(10, 5))
plt.plot(df["timestamp"], df[selected_coin], label="Historical", marker='o')
plt.plot(future_dates, predictions, label="Prediction", linestyle='--', marker='x', color='red')
plt.title(f"{selected_coin.upper()} Price Forecast (Next {future_days} Days)")
plt.xlabel("Time")
plt.ylabel("Price ($)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# Step 8: Print forecast table
forecast_df = pd.DataFrame({
    "Date": future_dates.strftime("%Y-%m-%d"),
    "Predicted Price ($)": predictions.flatten()
})
print("\n🔮 Predicted Prices:")
print(forecast_df.to_string(index=False))
