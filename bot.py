import json
import os
import threading
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler
)
from ib_insync import IB, Stock

# ==== CONFIG ====
TELEGRAM_TOKEN = '7537301802:AAHNMUItC6y8PWEICOwt2JxlmvPVJVuOkbs'
TELEGRAM_CHAT_ID = '6251762088'
IBKR_HOST = '127.0.0.1'
IBKR_PORT = 7497
IBKR_CLIENT_ID = 1
CONFIG_FILE = 'presets.json'

# ==== INIT ====
app = Flask(__name__)
bot = Bot(TELEGRAM_TOKEN)
updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher
ib = IB()

# ==== PRESET STORAGE ====
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        presets = json.load(f)
else:
    presets = {}

def save_presets():
    with open(CONFIG_FILE, 'w') as f:
        json.dump(presets, f, indent=2)

# ==== TELEGRAM CONFIG CONVERSATION ====
TICKER, SIZE, PROFIT = range(3)

def start_set(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Enter the ticker symbol (e.g., AAPL):")
    return TICKER

def get_ticker(update: Update, context: CallbackContext) -> int:
    context.user_data['ticker'] = update.message.text.strip().upper()
    update.message.reply_text("Enter order size in USD (e.g., 500):")
    return SIZE

def get_size(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data['size'] = float(update.message.text.strip())
        update.message.reply_text("Enter minimum profit percentage (e.g., 3.5):")
        return PROFIT
    except ValueError:
        update.message.reply_text("Invalid size. Please enter a numeric value:")
        return SIZE

def get_profit(update: Update, context: CallbackContext) -> int:
    try:
        ticker = context.user_data['ticker']
        size = context.user_data['size']
        profit = float(update.message.text.strip())
        presets[ticker] = {
            "order_size": size,
            "min_profit_pct": profit
        }
        save_presets()
        update.message.reply_text(
            f"✅ Config saved for {ticker}:\nOrder Size: ${size}\nMin Profit: {profit}%"
        )
        return ConversationHandler.END
    except ValueError:
        update.message.reply_text("Invalid percentage. Enter a number:")
        return PROFIT

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Configuration cancelled.")
    return ConversationHandler.END

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('set', start_set)],
    states={
        TICKER: [MessageHandler(Filters.text & ~Filters.command, get_ticker)],
        SIZE: [MessageHandler(Filters.text & ~Filters.command, get_size)],
        PROFIT: [MessageHandler(Filters.text & ~Filters.command, get_profit)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
dispatcher.add_handler(conv_handler)

# ==== FLASK WEBHOOK ENDPOINT ====
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    action = data.get("action")
    ticker = data.get("ticker", "").upper()

    if ticker not in presets:
        return jsonify({"error": "Ticker not configured"}), 400

    try:
        ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)
    except Exception as e:
        return jsonify({"error": f"IBKR connection failed: {e}"}), 500

    stock = Stock(ticker, 'SMART', 'USD')
    ib.qualifyContracts(stock)

    if action == "buy":
        return handle_buy(ticker, stock)
    elif action == "sell":
        return handle_sell(ticker, stock)
    else:
        return jsonify({"error": "Unknown action"}), 400

def handle_buy(ticker, stock):
    preset = presets[ticker]
    order_size_usd = preset["order_size"]

    buying_power = float(ib.accountSummary().loc['NetLiquidation', 'value'])
    if buying_power < order_size_usd:
        notify(f"❌ Not enough buying power for {ticker}")
        return jsonify({"status": "insufficient funds"}), 200

    market_data = ib.reqMktData(stock, '', False, False)
    ib.sleep(2)
    price = market_data.last if market_data.last else market_data.close
    if not price:
        return jsonify({"error": "Price unavailable"}), 500

    quantity = round(order_size_usd / price)
    order = ib.limitOrder('BUY', quantity, price)
    order.tif = 'GTC'
    order.outsideRth = True
    ib.placeOrder(stock, order)

    notify(f"✅ Buy Order Placed: {ticker}, Qty: {quantity}, Limit: {price}")
    return jsonify({"status": "buy order placed"}), 200

def handle_sell(ticker, stock):
    preset = presets[ticker]
    min_profit = preset["min_profit_pct"]

    positions = [pos for pos in ib.positions() if pos.contract.symbol == ticker]
    if not positions:
        return jsonify({"status": "no position to sell"}), 200

    pos = positions[0]
    qty = pos.position
    avg_cost = pos.avgCost

    market_data = ib.reqMktData(stock, '', False, False)
    ib.sleep(2)
    price = market_data.last if market_data.last else market_data.close
    if not price:
        return jsonify({"error": "Price unavailable"}), 500

    unrealized_pct = ((price - avg_cost) / avg_cost) * 100
    if unrealized_pct >= min_profit:
        order = ib.limitOrder('SELL', qty, price)
        order.tif = 'GTC'
        order.outsideRth = True
        ib.placeOrder(stock, order)
        notify(f"✅ Sell Order Placed: {ticker}, Qty: {qty}, Limit: {price}")
        return jsonify({"status": "sell order placed"}), 200
    else:
        return jsonify({"status": "profit below threshold"}), 200

def notify(message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# ==== START ====
def start_telegram():
    updater.start_polling()

if __name__ == '__main__':
    threading.Thread(target=start_telegram).start()
    app.run(host='0.0.0.0', port=5000)
