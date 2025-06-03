import threading
import json
from collections import deque, defaultdict
from dash import Dash, html, dcc
from dash.dependencies import Output, Input, State
import plotly.graph_objs as go
import zenoh
import time
import requests
from bs4 import BeautifulSoup

# cd C:\Asia university\advanced computer programming\crypto_tracker
# python zenoh_sub_dash.py
# python zenoh_pub.py
# python analyze_and_predict.py

# Zenoh settings
ZENOH_KEY = "crypto/prices"

# Supported cryptocurrencies
SUPPORTED_CRYPTOS = ["bitcoin", "ethereum", "solana", "dogecoin"]

# Real-time data storage (default 20 points)
price_history = defaultdict(lambda: deque(maxlen=20))

# Latest prices
latest_prices = {}

# ========== Zenoh Subscriber Thread ==========
def zenoh_listener():
    def callback(sample):
        global latest_prices
        try:
            prices = json.loads(bytes(sample.payload).decode())
            print("[ZENOH] Received:", prices)
            for coin in prices:
                latest_prices[coin] = prices[coin]
                price_history[coin].append(prices[coin])
        except Exception as e:
            print(f"[ZENOH ERROR] {e}")

    z = zenoh.open(zenoh.Config())
    z.declare_subscriber(ZENOH_KEY, callback)
    print("[ZENOH] Subscriber running...")
    while True:
        time.sleep(1)

threading.Thread(target=zenoh_listener, daemon=True).start()

# ========== Dash App ==========
app = Dash(__name__, external_stylesheets=[
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"])
app.title = "Advanced Crypto Tracker"

app.layout = html.Div([
    html.H1("📈 Advanced Live Cryptocurrency Dashboard", className="text-center my-4 fw-bold"),

    html.Div([
        html.Div([
            html.Label("Select Cryptocurrency:"),
            dcc.Dropdown(
                id='crypto-select',
                options=[{'label': c.title(), 'value': c} for c in SUPPORTED_CRYPTOS],
                value='bitcoin'
            ),
            html.Label("Select History Length (Data Points):"),
            dcc.Slider(
                id='history-length',
                min=10, max=100, step=10,
                value=20,
                marks={i: str(i) for i in range(10, 110, 10)},
            ),
            html.Div(id='highlow-card', className="mt-3 alert alert-info"),
        ], className="col-md-4"),

        html.Div([
            dcc.Graph(id='crypto-graph'),
            html.Div(id="latest-prices", className="text-center mt-2 fs-5 fw-semibold text-primary"),
        ], className="col-md-8")
    ], className="row"),

    html.Hr(),
    html.Div([
        html.H4("📰 Latest Crypto News", className="mb-3"),
        html.Ul(id="news-section")
    ], className="mt-4"),

    dcc.Interval(id='interval', interval=5*1000, n_intervals=0)
], className="container")

# ========== Dash Callbacks ==========
@app.callback(
    [Output('crypto-graph', 'figure'),
     Output('latest-prices', 'children'),
     Output('highlow-card', 'children'),
     Output('news-section', 'children')],
    [Input('interval', 'n_intervals')],
    [State('crypto-select', 'value'),
     State('history-length', 'value')]
)
def update_dashboard(n, selected_crypto, history_len):
    if selected_crypto not in price_history:
        return go.Figure(), "No data yet", "", []

    # Update maxlen if changed
    # Resize deque safely if history_len changed
    if price_history[selected_crypto].maxlen != history_len:
        existing_data = list(price_history[selected_crypto])[-history_len:]
        price_history[selected_crypto] = deque(existing_data, maxlen=history_len)


    prices = list(price_history[selected_crypto])
    fig = go.Figure(go.Scatter(y=prices, mode='lines+markers', name=selected_crypto.upper()))
    fig.update_layout(title=f"{selected_crypto.title()} Price (USD)", yaxis_title="Price ($)", margin=dict(t=40, b=20))

    latest = latest_prices.get(selected_crypto, "N/A")
    latest_text = f"Latest {selected_crypto.title()}: ${latest}"

    if prices:
        high = max(prices)
        low = min(prices)
        hl_text = f"High: ${high:.2f} | Low: ${low:.2f}"
    else:
        hl_text = "No data available."

    news_items = fetch_crypto_news(selected_crypto)
    news_list = [html.Li(html.A(n['title'], href=n['url'], target="_blank")) for n in news_items]

    return fig, latest_text, hl_text, news_list

# ========== News Fetching Function ==========


# ========== News Fetching Function ==========
def fetch_crypto_news(crypto_name):
    query = f"{crypto_name} cryptocurrency"
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.findAll("item")
        news = [{"title": item.title.text, "url": item.link.text} for item in items[:5]]
        return news
    except Exception as e:
        print("[NEWS ERROR]", e)
        return []



if __name__ == '__main__':
    app.run(debug=True)