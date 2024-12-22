import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Initialize the portfolio
portfolio = {}

# Function to get real-time stock data
def get_stock_price(symbol):
    try:
        # API key for Alpha Vantage
        api_key = "CK23ZB6U6BDUBMKQ"
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
        response = requests.get(url)
        data = response.json()
        if "Global Quote" in data:
            price = float(data["Global Quote"]["05. price"])
            return price
        else:
            return None
    except Exception as e:
        print("Error fetching stock data:", e)
        return None

# Flask routes
@app.route('/')
def index():
    total_value = 0
    portfolio_data = []
    for symbol, data in portfolio.items():
        current_price = get_stock_price(symbol)
        if current_price:
            stock_value = current_price * data['quantity']
            total_value += stock_value
            portfolio_data.append({
                'symbol': symbol,
                'quantity': data['quantity'],
                'price': current_price,
                'value': stock_value
            })
    return render_template('index.html', portfolio=portfolio_data, total_value=total_value)

@app.route('/add', methods=['POST'])
def add_stock():
    symbol = request.form['symbol'].upper()
    quantity = int(request.form['quantity'])
    price = get_stock_price(symbol)
    if price:
        if symbol in portfolio:
            portfolio[symbol]['quantity'] += quantity
        else:
            portfolio[symbol] = {'quantity': quantity, 'price': price}
    return redirect(url_for('index'))

@app.route('/remove', methods=['POST'])
def remove_stock():
    symbol = request.form['symbol'].upper()
    if symbol in portfolio:
        del portfolio[symbol]
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
