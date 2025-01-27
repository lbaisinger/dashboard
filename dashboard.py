import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from dash import Dash, dcc, html, Input, Output

# Initialize Dash app
app = Dash(__name__)

# Stock tickers to display
tickers = ["NVDA", "GOOG", "MSFT", "QQQ", "SPY", "TSM", "RKLB", "AMD", "INTC", "RIVN", "PL"]

# Fetch stock data
def fetch_data():
    data = {}
    for ticker in tickers:
        stock_data = yf.Ticker(ticker).history(period="1y")
        data[ticker] = stock_data["Close"]
    df = pd.DataFrame(data)
    df.index = pd.to_datetime(df.index)
    # Convert to percentage relative to the first value
    df = df.apply(lambda x: (x / x.iloc[0]) * 100)
    return df

stock_data = fetch_data()

# Function to generate label styles with background color
def get_label_style(ticker):
    color_map = {
        "NVDA": "#1E6B55", "GOOG": "#4285F4", "MSFT": "#00A4EF", "QQQ": "#FF8A00", "SPY": "#006F5F",
        "TSM": "#00C4B4", "RKLB": "#FF6159", "AMD": "#8C1515", "INTC": "#0071C5", "RIVN": "#00B8A9", "PL": "#1E2A47"
    }
    return color_map.get(ticker, "#808080")

# Create layout
app.layout = html.Div([
    html.H1("Stock Time Series Dashboard", style={"textAlign": "center"}),
    dcc.Dropdown(
        id="ticker-dropdown",
        options=[{"label": ticker, "value": ticker} for ticker in tickers],
        value=tickers,
        multi=True
    ),
    dcc.Graph(id="stock-plot", style={"height": "800px"}),
    html.Div(id="current-values", style={"textAlign": "center", "marginTop": "20px"}),
    html.Div("Data source: Yahoo Finance", style={"textAlign": "center", "marginTop": "20px"})
])

# Callback to update plot based on selected tickers
@app.callback(
    [Output("stock-plot", "figure"), Output("current-values", "children")],
    [Input("ticker-dropdown", "value")]
)
def update_plot(selected_tickers):
    # Sort tickers by their current value (last closing price)
    sorted_tickers = sorted(selected_tickers, key=lambda ticker: stock_data[ticker].iloc[-1], reverse=True)

    fig = go.Figure()
    current_values = []
    annotations = []

    # Initialize a variable to track the last y-position of annotations
    last_y_pos = None
    y_offset = 0

    for idx, ticker in enumerate(sorted_tickers):
        # Get the line color for this ticker
        line_color = get_label_style(ticker)

        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data[ticker], mode='lines', name=ticker, line=dict(color=line_color)))
        # Add current value for the ticker (as percentage)
        current_value = stock_data[ticker].iloc[-1]
        current_values.append(f"{ticker}: {current_value:.2f}%")

        # Adjust annotation y-position if too close to the previous one
        if last_y_pos is not None and abs(current_value - last_y_pos) < 1:  # If values are too close
            y_offset += 30  # Increment y_offset for separation

        # Alternate text position based on the index (odd/even)
        x_offset = 0
        ax = 0
        if idx % 2 == 0:  # Even index, position text to the right
            ax = -60
        else:  # Odd index, position text to the left
            ax = 60  # Move the text slightly left (adjust if necessary)

        # Add annotation for the latest value with background color style
        annotations.append(dict(
            x=stock_data.index[-1],
            y=current_value + y_offset,  # Apply y_offset to avoid overlap
            xref="x",
            yref="y",
            text=f"<b>{ticker}: {current_value:.2f}%</b>",  # Show percentage symbol
            showarrow=True,
            arrowhead=2,
            ax=ax,
            ay=0+y_offset,
            font=dict(color="white"),  # Text color remains white for contrast
            bgcolor=line_color,  # Set background color to match stock line color
            borderpad=5
        ))

        # Update last_y_pos for the next iteration
        last_y_pos = current_value + y_offset

    fig.update_layout(
        title="Stock Closing Prices Over Time (Relative to 1 Year Ago)",
        xaxis_title="Date",
        yaxis_title="Price (% of 1 Year Ago)",
        template="plotly_dark",
        legend_title="Stocks",
        hovermode="x unified",
        annotations=annotations
    )

    # Add the current value labels with respective background color
    current_values_text = html.Div([
        html.Span(value, style={"backgroundColor": get_label_style(ticker), "color": "white", "padding": "5px 10px", "borderRadius": "5px", "fontWeight": "bold"})
        for ticker, value in zip(sorted_tickers, current_values)
    ], style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center", "minWidth": "100px"})

    return fig, current_values_text

# Run app
if __name__ == "__main__":
    app.run_server(debug=True)
