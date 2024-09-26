import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
import requests
import pandas as pd
from datetime import date
from datetime import datetime 

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 获取合约Kline数据
def get_futures_klines(symbol, interval):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
    return df

# 获取现货Kline数据
def get_spot_klines(symbol, interval):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
    return df

# 获取合约Open Interest数据
def get_open_interest_hist(symbol, period):
    url = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol}&period={period}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=['timestamp', 'symbol', 'sumOpenInterest', 'sumOpenInterestValue'])
    return df

def get_symbols():
    exchange_info = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    symbols = [{'label':i['symbol'],'value':i['symbol']} for i in requests.get(exchange_info).json()['symbols'] if i['status']=='TRADING']
    return symbols 

symbols = get_symbols()

app.layout = dbc.Container([
    dcc.Tabs(id='tabs', children=[
        dcc.Tab(label='Spot and Futures Prices', value='tab-1'),
        dcc.Tab(label='Open Interest', value='tab-2'),
    ]),
    html.Div(id='tabs-content', style={'display': 'flex', 'justify-content': 'flex-start','width':'100%'})
])

@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            dcc.Dropdown(
                id='dropdown-symbols',
                options=symbols,
                value='BTCUSDT'
            ),
            dcc.DatePickerRange(
                id='date-picker-range'
            ),
            html.Button('Submit', id='submit-button'),
            dcc.Graph(id='price-graph', style={'width': '100%', 'height': '500px',}) # Set width to 48% and align to the left
        ], style={'width': '49%', 'display': 'inline-block'})  # Use inline-block for layout control
    elif tab == 'tab-2':
        return html.Div([
            dcc.Dropdown(
                id='dropdown-symbols-oi',
                options=symbols,
                multi=True,
                value=['BTCUSDT']
            ),
            dcc.DatePickerRange(
                id='date-picker-range-oi'
            ),
            html.Button('Submit', id='submit-button-oi'),
            dcc.Graph(id='oi-graph', style={'width': '100%', 'height': '500px'})  # Set width to 48% and align to the left
        ], style={'width': '49%', 'display': 'inline-block'})


@app.callback(
    Output('price-graph', 'figure'),
    Input('submit-button', 'n_clicks'),
    State('dropdown-symbols', 'value'),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date')
)
def update_graph(n_clicks, symbol, start_date, end_date):
    if n_clicks and start_date and end_date:
        df_spot = get_spot_klines(symbol, '1d')
        df_futures = get_futures_klines(symbol, '1d')

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=pd.to_datetime(df_spot['Open time'], unit='ms'), y=df_spot['Close'].astype(float), mode='lines', name='Spot Price'))
        fig.add_trace(go.Scatter(x=pd.to_datetime(df_futures['Open time'], unit='ms'), y=df_futures['Close'].astype(float), mode='lines', name='Futures Price'))
        fig.update_layout(hovermode='x unified')

        return fig
    return go.Figure()

@app.callback(
    Output('oi-graph', 'figure'),
    Input('submit-button-oi', 'n_clicks'),
    State('dropdown-symbols-oi', 'value'),
    State('date-picker-range-oi', 'start_date'),
    State('date-picker-range-oi', 'end_date')
)
# def update_open_interest_graph(n_clicks, symbols_list, start_date, end_date):
#     if n_clicks:
#         fig = go.Figure()
#         for symbol in symbols_list:
#             df = get_open_interest_hist(symbol, '1d')
#             fig.add_trace(go.Scatter(x=pd.to_datetime(df['timestamp'], unit='ms'), y=df['sumOpenInterestValue'].astype(float), mode='lines', name=f'{symbol} Open Interest'))
#             fig.update_layout(hovermode='x unified')

#         return fig
#     return go.Figure()

def update_open_interest_graph(n_clicks, symbols, start_date, end_date):
    if n_clicks:
        fig = go.Figure()
        for symbol in symbols:
            df = get_open_interest_hist(symbol, '1d')
            fig.add_trace(go.Scatter(x=pd.to_datetime(df['timestamp'], unit='ms'), y=df['sumOpenInterestValue'].astype(float).apply(lambda x:round(x,2)), mode='lines', name=f'{symbol} Open Interest'))
            fig.update_layout(hovermode='x unified')

        return fig
    return go.Figure()

if __name__ == '__main__':
    app.run_server(debug=True)
