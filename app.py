from flask import Flask, render_template, request, redirect, url_for, flash, Response
import yfinance as yf
import plotly.graph_objects as go
import csv
import io


app = Flask(__name__)
app.secret_key = "your_secret_key"

# Initialize the portfolio
portfolio = {}

# The password to authenticate actions
PASSWORD = 'AdminPass'

# Function to get real-time stock price using yfinance
def get_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        price = stock.history(period="1d")['Close'][0]
        return price
    except Exception as e:
        print("Error fetching stock data:", e)
        return None

# Function to get historical stock data using yfinance
def get_stock_history(symbol):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1y")  # 1 year of historical data
        return data
    except Exception as e:
        print("Error fetching stock history:", e)
        return None


@app.route('/export', methods=['GET'])
def export_csv():
    # Create a CSV in-memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers
    writer.writerow(['Stock Symbol', 'Quantity', 'Buying Price', 'Current Price', 'Value', 'Profit/Loss'])

    # Write portfolio data
    for symbol, data in portfolio.items():
        current_price = get_stock_price(symbol)
        if current_price:
            stock_value = current_price * data['quantity']
            profit_loss = (current_price - data['buying_price']) * data['quantity']
            writer.writerow([
                symbol,
                data['quantity'],
                data['buying_price'],
                current_price,
                stock_value,
                profit_loss
            ])

    output.seek(0)  # Reset the pointer to the start of the file
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=portfolio.csv"}
    )


# Route to display the portfolio and optionally a graph
@app.route('/')
def index():
    total_value = 0
    total_profit_loss = 0
    portfolio_data = []

    for symbol, data in portfolio.items():
        current_price = get_stock_price(symbol)
        if current_price:
            stock_value = current_price * data['quantity']
            profit_loss = (current_price - data['buying_price']) * data['quantity']
            total_value += stock_value
            total_profit_loss += profit_loss
            portfolio_data.append({
                'symbol': symbol,
                'quantity': data['quantity'],
                'buying_price': data['buying_price'],
                'current_price': current_price,
                'value': stock_value,
                'profit_loss': profit_loss
            })

    # Check if a symbol is passed for the graph
    symbol = request.args.get("symbol")
    graph_html = None
    if symbol:
        history = get_stock_history(symbol)
        if history is not None and not history.empty:
            dates = history.index.strftime('%Y-%m-%d').tolist()
            prices = history['Close'].tolist()

            # Create the Plotly graph
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines', name=symbol))
            fig.update_layout(
                title=f"{symbol} Stock Price History",
                xaxis_title="Date",
                yaxis_title="Closing Price ($)",
                template="plotly_dark"
            )

            # Convert the Plotly graph to HTML
            graph_html = fig.to_html(full_html=False)
        else:
            flash(f"Could not fetch historical data for {symbol}.", "danger")

    return render_template(
        'index.html',
        portfolio=portfolio_data,
        total_value=total_value,
        total_profit_loss=total_profit_loss,
        graph_html=graph_html
    )

# Route to add stock with password verification
@app.route('/add', methods=['POST'])
def add_stock():
    password = request.form.get('password')
    if password != PASSWORD:
        flash("Incorrect password.", "danger")
        return redirect(url_for('index'))

    symbol = request.form['symbol'].upper()
    quantity = int(request.form['quantity'])
    buying_price = float(request.form['buying_price'])

    price = get_stock_price(symbol)
    if price:
        if symbol in portfolio:
            portfolio[symbol]['quantity'] += quantity
            portfolio[symbol]['buying_price'] = (
                (portfolio[symbol]['buying_price'] * portfolio[symbol]['quantity']) + (buying_price * quantity)
            ) / (portfolio[symbol]['quantity'] + quantity)
        else:
            portfolio[symbol] = {'quantity': quantity, 'buying_price': buying_price}
        flash(f"Added {quantity} shares of {symbol} to your portfolio.", "success")
    else:
        flash(f"Invalid stock symbol: {symbol}", "danger")
    return redirect(url_for('index'))

# Route to remove stock with password verification
@app.route('/remove', methods=['POST'])
def remove_stock():
    password = request.form.get('password')
    if password != PASSWORD:
        flash("Incorrect password.", "danger")
        return redirect(url_for('index'))

    symbol = request.form['symbol'].upper()
    units = request.form.get('units')

    if symbol in portfolio:
        if units:
            units_to_remove = int(units)
            if portfolio[symbol]['quantity'] > units_to_remove:
                portfolio[symbol]['quantity'] -= units_to_remove
                flash(f"Removed {units_to_remove} units of {symbol} from your portfolio.", "success")
            elif portfolio[symbol]['quantity'] == units_to_remove:
                del portfolio[symbol]
                flash(f"Removed all units of {symbol} from your portfolio.", "success")
            else:
                flash(f"Cannot remove {units_to_remove} units of {symbol} as you only have {portfolio[symbol]['quantity']} units.", "danger")
        else:
            del portfolio[symbol]
            flash(f"Removed {symbol} from your portfolio.", "success")
    else:
        flash(f"Stock {symbol} not found in your portfolio.", "danger")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=1397, host='0.0.0.0')
