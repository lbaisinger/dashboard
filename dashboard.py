import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import datetime

# Initialize Dash app
app = Dash(__name__)

# Stock tickers to display
tickers = ["NVDA", "GOOG", "MSFT", "QQQ", "SPY", "TSM", "RKLB", "AMD", "INTC", "RIVN", "PL"]

# Function to fetch stock data
def fetch_data(tickers, start_date=None, end_date=None):
    # Fetch data for all tickers at once
    df = yf.download(tickers, start=start_date, end=end_date)['Close']
    # Calculate a 50-day moving average
    df_ma = df.rolling(window=50).mean()
    # Convert to percentage relative to the first value
    df = df.apply(lambda x: (x / x.iloc[0]) * 100)
    df_ma = df_ma.apply(lambda x: (x / x.iloc[0]) * 100)
    return df, df_ma

# Function to generate label styles with background color
def get_label_style(ticker):
    color_map = {
        "NVDA": "#1E6B55", "GOOG": "#4285F4", "MSFT": "#00A4EF", "QQQ": "#FF8A00", "SPY": "#006F5F",
        "TSM": "#00C4B4", "RKLB": "#FF6159", "AMD": "#8C1515", "INTC": "#0071C5", "RIVN": "#00B8A9", "PL": "#1E2A47"
    }
    return color_map.get(ticker, "#808080")

# Create layout with date picker and interval for live updates
app.layout = html.Div([
    html.H1("Stock Time Series Dashboard", style={"textAlign": "center"}),
    dcc.Dropdown(
        id="ticker-dropdown",
        options=[{"label": ticker, "value": ticker} for ticker in tickers],
        value=tickers,
        multi=True
    ),
    dcc.DatePickerRange(
        id='date-picker-range',
        min_date_allowed=datetime.date(2000, 1, 1),
        max_date_allowed=datetime.date.today(),
        start_date=datetime.date.today() - datetime.timedelta(days=365),
        end_date=datetime.date.today(),
        display_format='Y-MM-DD',
        style={'marginTop': '20px'}
    ),
    dcc.Graph(id="stock-plot", style={"height": "600px"}),
    html.Div(id="current-values", style={"textAlign": "center", "marginTop": "20px"}),
    dcc.Graph(id="heatmap", style={"height": "400px"}),
    html.Div("Data source: Yahoo Finance", style={"textAlign": "center", "marginTop": "20px"}),
    dcc.Interval(
        id='interval-component',
        interval=5*60*1000,  # Refresh data every 5 minutes
        n_intervals=0
    )
])

# Callback to update plot based on selected tickers and date range
@app.callback(
    [
        Output("stock-plot", "figure"),
        Output("current-values", "children"),
        Output("heatmap", "figure")
    ],
    [
        Input("ticker-dropdown", "value"),
        Input('date-picker-range', 'start_date'),
        Input('date-picker-range', 'end_date'),
        Input('interval-component', 'n_intervals')
    ]
)
def update_plot(selected_tickers, start_date, end_date, n_intervals):
    stock_data, stock_data_ma = fetch_data(selected_tickers, start_date, end_date)

    # Sort tickers by their current value (last closing price)
    sorted_tickers = sorted(selected_tickers, key=lambda ticker: stock_data[ticker].iloc[-1], reverse=True)

    fig = go.Figure()
    current_values = []
    annotations = []

    for idx, ticker in enumerate(sorted_tickers):
        # Get the line color for this ticker
        line_color = get_label_style(ticker)

        # Plot the stock price
        fig.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data[ticker],
            mode='lines',
            name=ticker,
            line=dict(color=line_color)
        ))

        # Plot the moving average
        fig.add_trace(go.Scatter(
            x=stock_data_ma.index,
            y=stock_data_ma[ticker],
            mode='lines',
            name=f'{ticker} 50-day MA',
            line=dict(color=line_color, dash='dash')
        ))

        # Add current value for the ticker (as percentage)
        current_value = stock_data[ticker].iloc[-1]
        current_values.append(f"{ticker}: {current_value:.2f}%")

        # Alternate text position based on the index (odd/even)
        ax = -50 if idx % 2 == 0 else 50

        # Add annotation for the latest value with background color style
        annotations.append(dict(
            x=stock_data.index[-1],
            y=current_value,
            xref="x",
            yref="y",
            text=f"<b>{ticker}: {current_value:.2f}%</b>",
            showarrow=True,
            arrowhead=2,
            ax=ax,
            ay=-20 * idx,
            font=dict(color="white"),
            bgcolor=line_color,
            borderpad=5
        ))

    fig.update_layout(
        title="Stock Closing Prices Over Time (Relative to Start Date)",
        xaxis_title="Date",
        yaxis_title="Price (% of Start Date)",
        template="plotly_dark",
        legend_title="Stocks",
        hovermode="x unified",
        annotations=annotations
    )

    # Calculate correlation
    correlation = stock_data[selected_tickers].corr()
    heatmap = go.Figure(data=go.Heatmap(
        z=correlation.values,
        x=correlation.columns.tolist(),
        y=correlation.index.tolist(),
        colorscale='Viridis'
    ))
    heatmap.update_layout(
        title="Correlation Heatmap",
        xaxis_title="Stocks",
        yaxis_title="Stocks",
        template="plotly_dark"
    )

    # Add the current value labels with respective background color
    current_values_text = html.Div([
        html.Span(
            value,
            style={
                "backgroundColor": get_label_style(ticker),
                "color": "white",
                "padding": "5px 10px",
                "borderRadius": "5px",
                "fontWeight": "bold",
                "margin": "5px"
            }
        )
        for ticker, value in zip(sorted_tickers, current_values)
    ], style={
        "display": "flex",
        "flexWrap": "wrap",
        "justifyContent": "center"
    })

    return fig, current_values_text, heatmap

# Run app
if __name__ == "__main__":
    app.run_server(debug=True)
