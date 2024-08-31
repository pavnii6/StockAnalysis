import dash
from dash import dcc, html
import yfinance as yf
import requests
import plotly.graph_objects as go

# Replace with your NewsAPI key
NEWS_API_KEY = 'b6d3625a416a4eb5a70e46ecf0946c1f'

app = dash.Dash(__name__)

def fetch_stock_data(symbol):
    stock = yf.Ticker(symbol)
    df = stock.history(period="1y")  # Fetching 1 year of historical data
    return df

def fetch_current_price(symbol):
    stock = yf.Ticker(symbol)
    todays_data = stock.history(period='1d')
    return todays_data['Close'].iloc[0]

def calculate_moving_average(df, period=10):
    return df['Close'].rolling(window=period).mean()

def fetch_latest_news(symbol):
    url = f'https://newsapi.org/v2/everything?q={symbol}&apiKey={NEWS_API_KEY}&language=en&sortBy=publishedAt'
    response = requests.get(url)
    
    if response.status_code == 200:
        articles = response.json().get('articles')
        if articles:
            return [{
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'publishedAt': article['publishedAt']
            } for article in articles[:5]]  # Limit to 5 articles
        else:
            return []
    else:
        return f"Error fetching news: {response.status_code}"

app.layout = html.Div([
    # Blurred Background Image
    html.Div(style={
        'backgroundImage': 'url("https://cdn.pixabay.com/photo/2023/10/10/06/41/chart-8305514_1280.jpg")',
        'backgroundSize': 'cover',
        'backgroundPosition': 'center',
        'filter': 'blur(8px)',  # Blur the background image
        'position': 'absolute',
        'width': '100%',
        'height': '100%',
        'zIndex': '-1'  # Send background behind other content
    }),
    
    # Foreground Content with Semi-Transparent Overlay
    html.Div(style={
        'position': 'relative',
        'zIndex': '1',
        'padding': '20px',
        'backgroundColor': 'rgba(0, 0, 0, 0.7)',  # Semi-transparent black overlay
        'borderRadius': '10px',  # Optional: adds rounded corners
        'maxHeight': '90vh',  # Limit the height to 90% of the viewport
        'overflowY': 'auto'  # Allow vertical scrolling if content overflows
    }, children=[
        html.H1("Stock Market Analysis Tool", style={'color': 'white'}),
        dcc.Input(id='stock-symbol', type='text', value='AAPL', debounce=True, style={'margin': '10px'}),
        html.Div(id='error-message', style={'color': 'red'}),
        html.Div(id='current-price', style={'fontSize': 24, 'fontWeight': 'bold', 'margin': '20px 0', 'color': 'white'}),
        html.Div(id='highest-price', style={'fontSize': 20, 'fontWeight': 'bold', 'margin': '10px 0', 'color': 'yellow'}),
        html.Div(id='lowest-price', style={'fontSize': 20, 'fontWeight': 'bold', 'margin': '10px 0', 'color': 'lightcoral'}),
        dcc.Graph(id='stock-chart'),
        html.H2("Latest News", style={'color': 'white'}),
        html.Div(id='news-container', style={'color': 'white'}),
        dcc.Interval(
            id='interval-component',
            interval=60*1000,  # Refresh every 1 minute
            n_intervals=0
        )
    ])
])

@app.callback(
    [dash.dependencies.Output('stock-chart', 'figure'),
     dash.dependencies.Output('current-price', 'children'),
     dash.dependencies.Output('news-container', 'children'),
     dash.dependencies.Output('error-message', 'children'),
     dash.dependencies.Output('highest-price', 'children'),
     dash.dependencies.Output('lowest-price', 'children')],
    [dash.dependencies.Input('stock-symbol', 'value'),
     dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_graph_and_news(symbol, n_intervals):
    try:
        # Fetch stock data, current price, and moving average
        df = fetch_stock_data(symbol)
        current_price = fetch_current_price(symbol)
        moving_avg = calculate_moving_average(df)
        
        # Get highest and lowest prices
        highest_price = df['High'].max()
        lowest_price = df['Low'].min()
        
        # Generate the candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Candlestick',
            hoverinfo='x+y+text',  # Add tooltips to display data
            text=[
                f"Open: {o:.2f}<br>High: {h:.2f}<br>Low: {l:.2f}<br>Close: {c:.2f}"
                for o, h, l, c in zip(df['Open'], df['High'], df['Low'], df['Close'])
            ]
        )])
        
        # Add moving average line to the candlestick chart
        fig.add_trace(go.Scatter(
            x=df.index,
            y=moving_avg,
            mode='lines',
            name=f'{len(moving_avg)}-Day Moving Average',
            line=dict(color='red')
        ))

        fig.update_layout(
            title=f'Stock Price and Moving Average for {symbol}',
            xaxis_title='Date',
            yaxis_title='Price',
            template='plotly_dark'
        )
        
        # Fetch latest news
        news_articles = fetch_latest_news(symbol)
        
        if isinstance(news_articles, str):  # Check if there's an error
            return fig, f"Current Price: ${current_price:.2f}", [], news_articles, f"Highest Price: ${highest_price:.2f}", f"Lowest Price: ${lowest_price:.2f}"
        
        # Format the news articles into HTML
        news_elements = []
        for article in news_articles:
            news_elements.append(html.Div([
                html.H3(html.A(article['title'], href=article['url'], target='_blank', style={'color': '#FFFFFF'})),
                html.P(article['description'], style={'color': '#FFFFFF'}),
                html.Small(f"Published at: {article['publishedAt']}", style={'color': '#FFFFFF'}),
                html.Hr()
            ]))
        
        return fig, f"Current Price: ${current_price:.2f}", news_elements, "", f"Highest Price: ${highest_price:.2f}", f"Lowest Price: ${lowest_price:.2f}"

    except Exception as e:
        return go.Figure(), "", [], f"Error fetching data: {e}", "", ""  # Return error message if there's an issue

if __name__ == '__main__':
    app.run_server(debug=True)
