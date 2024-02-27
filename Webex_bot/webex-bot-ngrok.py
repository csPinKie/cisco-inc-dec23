# -*- coding: utf-8 -*-
"""
Webex Ngrok Bot code for automatically creating ngrok webhooks and responding with stock information and graphs.
"""

import os
import sys
import json
import requests
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify
from webexteamssdk import WebexTeamsAPI, ApiError
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name="dl5lbmrnk",
    api_key="532147621565562",
    api_secret="RefO8kSdPtz562Jj92p_rNMM-e0"
)

app = Flask(__name__)
webserver_port = 4111
webserver_debug = True

my_bot_token = os.getenv('MY_BOT_TOKEN',
                         "ZTRlNGEwM2MtMmNiYi00ZTBhLTg5NWItN2RkODVkOTc4N2Y2OGMxNmY4OGQtNjMz_PE93_642a94f5-2664-4eea-ba2e-f2a12f9efba5")
api = WebexTeamsAPI(access_token=my_bot_token)


def check_ngrok():
    pass

def check_webhooks(ngrok_url):
    pass


def find_stock_symbol(query):
    pass


def get_stock_info(symbol):
    pass

def check_ngrok():
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels")
        public_url = json.loads(response.text)['tunnels'][0]['public_url'].replace("http://", "https://")
        return public_url
    except Exception:
        return "**ERROR**: 'ngrok http 4111' must be running."


def check_webhooks(ngrok_url):
    try:
        webhooks = list(api.webhooks.list())
        for webhook in webhooks:
            if webhook.targetUrl != ngrok_url:
                api.webhooks.delete(webhook.id)
        if not any(wh.targetUrl == ngrok_url for wh in webhooks):
            api.webhooks.create(name="Ngrok Webhook", targetUrl=ngrok_url, resource="messages", event="created")
    except ApiError as e:
        sys.exit(f"Webhook Error: {e}")


def find_stock_symbol(query):
    api_key = 'TU0SH77LD2F9LKFS'
    response = requests.get(
        f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={api_key}")
    data = response.json().get('bestMatches', [])
    if data:
        return data[0]['1. symbol'], data[0]['2. name']
    return None, None


def get_stock_info(symbol):
    api_key = 'TU0SH77LD2F9LKFS'
    response = requests.get(
        f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}")
    data = response.json().get('Time Series (Daily)', {})
    dates = sorted(data.keys(), reverse=True)[:2]  # Get the last two days

    if len(dates) >= 2:
        closing_price_latest = float(data[dates[0]]['4. close'])
        closing_price_previous = float(data[dates[1]]['4. close'])
        daily_change = closing_price_latest - closing_price_previous
        daily_change_percent = (daily_change / closing_price_previous) * 100

        return f"**{symbol}**: ${closing_price_latest} (as of {dates[0]}). Daily change: {'+' if daily_change > 0 else ''}{daily_change:.2f} ({daily_change_percent:+.2f}%)"
    return "Data not found."


def generate_stock_graph(symbol):
    api_key = 'TU0SH77LD2F9LKFS'
    data = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}").json()
    price_date = data['Time Series (Daily)']
    dates = sorted(data['Time Series (Daily)'].keys())
    # prices = [data['Time Series (Daily)'][date]['4. close'] for date in dates]
    opens = [float(price_date[date]['1. open']) for date in dates]
    highs = [float(price_date[date]['2. high']) for date in dates]
    lows = [float(price_date[date]['3. low']) for date in dates]
    closes = [float(price_date[date]['4. close']) for date in dates]

    # Plotting
    plt.figure(figsize=(14, 7))
    plt.plot(dates, closes, label='Close Price', color='blue')
    plt.title(f'{symbol} Stock Price')
    plt.xlabel('Date')
    plt.ylabel('Price in USD')
    plt.xticks(dates[::3], rotation=45, ha='right', va='center')
    fig = plt.gcf()
    ax = fig.gca()
    labels = ax.get_xticklabels()
    plt.setp(labels, y=-0.06)
    plt.legend()
    plt.tight_layout()

    image_save_path = '/Image_Cache'
    if not os.path.exists(image_save_path):
        os.makedirs(image_save_path)
    image_path = os.path.join(image_save_path, f"{symbol}_stock_graph.png")
    plt.savefig(image_path)
    plt.close()


    response = cloudinary.uploader.upload(image_path)
    #os.remove(image_path)
    return response['secure_url']




@app.route('/', methods=['POST'])
def webhook_handler():
    json_data = request.json
    message_id = json_data['data']['id']
    message = api.messages.get(message_id)

    #if message.personEmail.endswith('@webex.bot'):
    #    return 'Ignoring bot messages'
    if not message.personEmail.endswith('@webex.bot'):
        process_message(message)

    return jsonify({"success": True})
    message_text = message.text.lower().strip()
    if "help" in message_text:
        help_text = """**Here's what you can ask me:**\n- `stock:<ticker>` to get the latest stock information. Example: `stock:apple`\n- `help` to display this help message."""
        api.messages.create(roomId=message.roomId, markdown=help_text)
    elif message_text.startswith("stock:"):
        query = message_text.split("stock:")[1].strip()
        symbol, _ = find_stock_symbol(query)
        if symbol:
            stock_info = get_stock_info(symbol)
            api.messages.create(roomId=message.roomId, markdown=stock_info)
        else:
            api.messages.create(roomId=message.roomId, text="Stock symbol not found.")
    else:
        api.messages.create(roomId=message.roomId, text="Unrecognized command. Type 'help' for assistance.")

    return jsonify({"success": True})

def process_message(message):
    message_text = message.text.lower().strip()
    if "help" in message_text:
        help_text = """**Here's what you can ask me:**\n- `stock:<ticker>` to get the latest stock information. Example: `stock:apple`\n- `help` to display this help message."""
        api.messages.create(roomId=message.roomId, markdown=help_text)
    elif message_text.startswith("stock:"):
        query = message_text.split("stock:")[1].strip()
        symbol, _ = find_stock_symbol(query)
        if symbol:
            stock_info = get_stock_info(symbol)
            graph_url = generate_stock_graph(symbol)  # Ensure this function returns the URL correctly
            response_text = f"{stock_info})"
            api.messages.create(roomId=message.roomId, markdown=response_text, files=[graph_url])
        else:
            api.messages.create(roomId=message.roomId, text="Stock symbol not found.")
    else:
        api.messages.create(roomId=message.roomId, text="Unrecognized command. Type 'help' for assistance.")

if __name__ == "__main__":
    ngrok_url = check_ngrok()
    if "**ERROR**" in ngrok_url:
        print(ngrok_url)
        sys.exit(-1)

    check_webhooks(ngrok_url)
    app.run(host='0.0.0.0', port=webserver_port, debug=webserver_debug)




