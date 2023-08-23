import pandas as pd
from location import weatherloc
import pytz
import pickle
from weathercode import weatherCode
from aux_viz import arrow_pos, gauge, generate_wind_rose, get_forecast_fig
import plotly.graph_objects as go
import dash
from dash import dcc
import base64
from datetime import datetime
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html
from dash_bootstrap_components._components.Container import Container
import re
from clothes import clothesRecommender
from components import get_card, get_badge
from api_utils import api_call, convert_to_df, convert_to_local_time, process_data, add_desc, get_image_names
from config import OPENAI_API_KEY, TOMORROW_IO_API_KEY

# Style Specifications
external_stylesheets = [
    'https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css',  # Bootstrap
    'https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap'  # Lato font
]

color_palette: dict[str, str] = {
    "dark_blue": "#06283D",
    "medium_blue": "#1363DF",
    "light_blue": "#47B5FF",
    "off_white": "#DFF6FF"
}

card_style = {
    'padding': '10px',  # Reducing padding to make the card content more compact
    'backgroundColor': '#AEDFF7',  # Keeping the original background color
}

# Importing png files scraped from Github with scrape_icons.py
with open('data.pkl', 'rb') as f:
    loaded_data = pickle.load(f)
    png_files = loaded_data


def is_valid_zip(zip_code):
    # For US ZIP codes
    pattern = r'^\d{5}(?:-\d{4})?$'
    return bool(re.match(pattern, zip_code))


# Set values for API Call parameters
location_obj = weatherloc("08057")
unit_selected = "imperial"

try:
    now = api_call(time_period="now", time_step="1h", units=unit_selected, wlo=location_obj)
    forecast = api_call(time_period="forecast", time_step="1h", units=unit_selected, wlo=location_obj)
except:
    print("API call failed", "", {}, "", "")

# Extract hourly data from the the JSON
# historical_data = last_24_hours.json()
now_data = now.json()
forecast_data = forecast.json()

# Convert Realtime Weather to Dictionary
now_data_dict = now_data['data']['values']

# Convert Historical and Forecast Data to Pandas Df
# historical_data_df = convert_to_df(historical_data)
forecast_data_df = convert_to_df(forecast_data)
forecast_data_df["image_names"] = get_image_names(forecast_data_df)

# historical_data_df = process_data(historical_data_df, location_obj)
forecast_data_df = process_data(forecast_data_df, location_obj)

# historical_data_df = add_desc(historical_data_df)
forecast_data_df = add_desc(forecast_data_df)

# UV Index Dial
uvIndex = now_data_dict['uvIndex']
arrow_num = arrow_pos(uvIndex)

if arrow_num == 1:
    uv_desc = 'Minimal Danger'
elif arrow_num == 2:
    uv_desc = 'Low Risk'
elif arrow_num == 3:
    uv_desc = 'Moderate Risk'
elif arrow_num == 4:
    uv_desc = 'High Risk'
elif arrow_num == 5:
    uv_desc = 'Very High Risk'
else:
    uv_desc = ""

gauge_fig = dcc.Graph(id='gauge-plot',
                      figure={
                          'layout': {
                              'width': 150,
                              'height': 150,
                              'images': [{'source': gauge(labels=['0-2', '3-5', '6-7', '8-10', '11+'],
                                                          colors=['#299501', '#f7e401', '#f95901', '#d90011',
                                                                  '#6c49cb'],
                                                          arrow=arrow_num,
                                                          title=f'{uv_desc}')}],
                              'showlegend': False, }})

# formatting time
forecast_data_df['local_time'] = forecast_data_df.apply(lambda row: row["local_time"].strftime("%I:%M %p"), axis=1)

next_day = forecast_data_df[:24]

now_data_df = pd.DataFrame([now_data_dict])
now_data_df["time"] = datetime.now().strftime('%H:%M:%S')
now_data_df = process_data(now_data_df)

# Instantiate the clothesRecommender class
recommender = clothesRecommender(OPENAI_API_KEY)

recommendation = recommender.get_gpt4_response(
    temp=now_data_dict['temperature'],
    feels_like=now_data_dict['temperatureApparent'],
    rain=now_data_dict['precipitationProbability'],
    humid=now_data_dict['humidity'],
    uv=now_data_dict['uvIndex'],
    wind=now_data_dict['windSpeed'],
    description=weatherCode[str(now_data_df['weatherCode'][0])]
)

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.config.suppress_callback_exceptions = True

# Set the throttling delay in seconds (every hour)
throttle_delay = 3600
now = datetime.now()
current_time = now.strftime("%H:%M")
current_temperature = now_data_dict['temperature']

# fig.update_layout(showlegend=False)

initial_value = arrow_num  # Change this to the initial value you want
gauge_fig = gauge(arrow=initial_value)
wind_rose_uri = generate_wind_rose(forecast_data_df)

LOGO = "https://cdn-icons-png.flaticon.com/512/10127/10127236.png"

search_bar = dbc.Row(
    [
        dbc.Col(dcc.Input(id='zipcode-input', type='text', placeholder='Enter zipcode', value='08057')),
        dbc.Col(
            dbc.Button(
                "Search", color="primary", className="ms-2", n_clicks=0
            ),
            width="auto",
        ),
    ],
    className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=LOGO, height="30px")),
                        dbc.Col(dbc.NavbarBrand("ICA Weather Dashboard", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                search_bar,
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True
)

# uv_index_card_style = {
#     'height': '200%',  # Adjust as needed
#     'padding': '10px',
#     'backgroundColor': '#AEDFF7',
# }

app.layout = dbc.Container([
    navbar,

    html.Hr(),

    dbc.Row([
        dbc.Col([
            get_card([
                html.H2(id='current_temp', children=f"{location_obj.name}: {current_temperature}°F"),
                get_badge(id='current_desc', text=f"{weatherCode[str(now_data_df['weatherCode'][0])]}"),
            ], className="h-100"),
        ], width=6),
        dbc.Col([
            get_card([
                html.H4([
                    html.Img(
                        src='https://www.clipartmax.com/png/middle/433-4330520_operating-dry-clothes-comments-clothes-icon-png-free.png',
                        alt='Clothes Icon',
                        style={'width': '20px', 'height': '20px', 'vertical-align': 'middle',
                               'margin-right': '5px'}),
                    "What to Wear"
                ]),
                html.P(id='current_rec', children=recommendation),
            ], className="h-100")
        ], width=6)
    ], className='mb-4'),

    html.Hr(),
    html.H3("Current Conditions"),
    dbc.Row([
        dbc.Col([
            get_card([
                html.H4([
                    html.Img(src='https://cdn-icons-png.flaticon.com/512/263/263883.png ', alt='Rain Icon',
                             style={'width': '20px', 'height': '20px', 'vertical-align': 'middle',
                                    'margin-right': '5px'}),
                    "Precipitation"
                ]),
                html.P(id='current_precip', children=f"{now_data_dict['precipitationProbability']}%")
            ]),
            get_card([
                html.H4([
                    html.Img(src='https://static-00.iconduck.com/assets.00/temperature-feels-like-icon-495x512'
                                 '-ylzv705f.png', alt='Feels Like Icon',
                             style={'width': '20px', 'height': '20px', 'vertical-align': 'middle',
                                    'margin-right': '5px'}),
                    "Feels Like"
                ]),
                html.P(id='current_temp_app', children=f"{now_data_dict['temperatureApparent']}°F")
            ]),
            get_card([
                html.H4([
                    html.Img(src='https://cdn-icons-png.flaticon.com/512/6393/6393411.png', alt='Humidity Icon',
                             style={'width': '20px', 'height': '20px', 'vertical-align': 'middle',
                                    'margin-right': '5px'}),
                    "Humidity"
                ])
                ,
                html.P(id='current_humid', children=f"{now_data_dict['humidity']}%")
            ]),
            get_card([
                html.H4([
                    html.Img(id='gauge-plot', src=gauge_fig, alt='UV Index Icon',
                             style={'width': '30px', 'height': '30px', 'vertical-align': 'middle',
                                    'margin-right': '5px'}),
                    "UV Index"
                ]),
                html.P(id='current_uv', children=f"{now_data_dict['uvIndex']}")
            ]),
            get_card([
                html.H4([
                    html.Img(src='https://cdn-icons-png.flaticon.com/512/252/252035.png', alt='Cloud Cover Icon',
                             style={'width': '20px', 'height': '20px', 'vertical-align': 'middle',
                                    'margin-right': '5px'}),
                    "Cloud Cover"
                ]),
                html.P(id='current_cloudcover', children=f"{now_data_dict['cloudCover']} %")
            ])
        ]),
        dbc.Col([
            get_card([
                html.H4([
                    html.Img(src='https://cdn-icons-png.flaticon.com/512/54/54298.png', alt='Wind Gust Icon',
                             style={'width': '20px', 'height': '20px', 'vertical-align': 'middle',
                                    'margin-right': '5px'}),
                    "Wind Gust"
                ]),
                html.P(id='current_windGust', children=f"{now_data_dict['windGust']} mph")
            ]),
            get_card([
                html.H4([
                    html.Img(src='https://cdn-icons-png.flaticon.com/512/740/740832.png', alt='Wind Speed Icon',
                             style={'width': '20px', 'height': '20px', 'vertical-align': 'middle',
                                    'margin-right': '5px'}),
                    "Wind Speed"
                ]),
                html.P(id='current_windSpeed', children=f"{now_data_dict['windSpeed']} mph")
            ]),
            get_card([
                html.H4([
                    html.Img(src='https://cdn-icons-png.flaticon.com/512/4655/4655946.png', alt='Dew Point Icon',
                             style={'width': '20px', 'height': '20px', 'vertical-align': 'middle',
                                    'margin-right': '5px'}),
                    "Dew Point"
                ]),
                html.P(id='current_dewPoint', children=f"{now_data_dict['dewPoint']}°F")
            ]),
            get_card([
                html.H4([
                    html.Img(src='https://cdn-icons-png.flaticon.com/512/1839/1839341.png', alt='Pressure Icon',
                             style={'width': '20px', 'height': '20px', 'vertical-align': 'middle',
                                    'margin-right': '5px'}),
                    "Pressure"
                ]),
                html.P(id='current_pressure', children=f"{now_data_dict['pressureSurfaceLevel']} inHg")
            ]),
            get_card([
                html.H4([
                    html.Img(src='https://cdn-icons-png.flaticon.com/512/4005/4005908.png', alt='Visibility Icon',
                             style={'width': '20px', 'height': '20px', 'vertical-align': 'middle',
                                    'margin-right': '5px'}),
                    "Visibility"
                ]),
                html.P(id='current_visibility', children=f"{now_data_dict['visibility']} mi")
            ])
        ]),
    ], style={'fontFamily': 'Lato, sans-serif'}),

    html.Hr(),

    dbc.Row([
        dbc.Col([
            html.H3("24 Hour Forecast"),
            dcc.Graph(id='forecast-plot', figure=get_forecast_fig(next_day),
                      style={
                          'textAlign': 'center',  # Horizontal centering
                          'display': 'flex',
                          'justifyContent': 'center',  # Horizontal centering with flex
                          'alignItems': 'center'  # Vertical centering with flex
                      })
        ])
    ]),

    html.Hr(),

    dbc.Row([
        dbc.Col([
            get_card([
                html.H3("Wind Rose"),
                html.P("Shows the distribution of wind direction and speed in the next 24 hours"),
                html.Img(id='wind-rose-image', src=wind_rose_uri)
            ])
        ], width=6)

    ])
], style={
    'backgroundColor': color_palette['dark_blue'],
    'color': color_palette['off_white']
}, fluid=True)


# add callback for toggling the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    [
        Output('current_temp', 'children'),
        Output('current_desc', 'children'),
        Output('current_precip', 'children'),
        Output('current_temp_app', 'children'),
        Output('current_humid', 'children'),
        Output('current_uv', 'children'),
        Output('current_windGust', 'children'),
        Output('current_windSpeed', 'children'),
        Output('current_dewPoint', 'children'),
        Output('current_pressure', 'children'),
        Output('current_cloudcover', 'children'),
        Output('current_visibility', 'children'),
        Output('forecast-plot', 'figure'),
        Output('wind-rose-image', 'src'),
        Output('gauge-plot', 'src'),
        Output('current_rec', 'children')
    ],
    Input('zipcode-input', 'value'),
    prevent_initial_call=True
)
def update_based_on_zipcode(zipcode_value):
    if not is_valid_zip(zipcode_value):
        return dash.no_update
    else:
        location_obj = weatherloc(zipcode_value)

        # Make API calls using location_obj
        try:
            now = api_call(time_period="now", time_step="1h", units=unit_selected, wlo=location_obj)
            forecast = api_call(time_period="forecast", time_step="1h", units=unit_selected, wlo=location_obj)
        except:
            return "API call failed", "", {}, "", ""

        # Extract and process data
        now_data = now.json()
        forecast_data = forecast.json()

        now_data_dict = now_data['data']['values']
        forecast_data_df = convert_to_df(forecast_data)
        forecast_data_df["image_names"] = get_image_names(forecast_data_df)
        forecast_data_df = process_data(forecast_data_df, location_obj)
        forecast_data_df = add_desc(forecast_data_df)
        forecast_data_df['local_time'] = forecast_data_df.apply(lambda row: row["local_time"].strftime("%I:%M %p"),
                                                                axis=1)

        # Extract necessary values for components
        current_temp = f"{location_obj.name}: {now_data_dict['temperature']}°F"
        current_desc = f"{weatherCode[str(now_data_df['weatherCode'][0])]}"
        current_precip = f"{now_data_dict['precipitationProbability']}%"
        current_temp_app = f"{now_data_dict['temperatureApparent']}°F"
        current_humid = f"{now_data_dict['humidity']}%"
        current_uv = f"{now_data_dict['uvIndex']}"
        current_windGust = f"{now_data_dict['windGust']} mph"
        current_windSpeed = f"{now_data_dict['windSpeed']} mph"
        current_dewPoint = f"{now_data_dict['dewPoint']}°F"
        current_pressure = f"{now_data_dict['pressureSurfaceLevel']} inHg"
        current_cloudcover = f"{now_data_dict['cloudCover']} %"
        current_visibility = f"{now_data_dict['visibility']} mi"

        forecast_figure = get_forecast_fig(forecast_data_df[:24])
        wind_rose_uri = generate_wind_rose(forecast_data_df)
        uvIndex = now_data_dict['uvIndex']
        arrow_num = arrow_pos(uvIndex)
        gauge_fig = gauge(arrow=arrow_num)  # You might need to adjust this based on your gauge function

        recommendation = recommender.get_gpt4_response(
            temp=now_data_dict['temperature'],
            feels_like=now_data_dict['temperatureApparent'],
            rain=now_data_dict['precipitationProbability'],
            humid=now_data_dict['humidity'],
            uv=now_data_dict['uvIndex'],
            wind=now_data_dict['windSpeed'],
            description=weatherCode[str(now_data_df['weatherCode'][0])]
        )

        return (current_temp, current_desc, current_precip, current_temp_app, current_humid, current_uv,
                current_windGust, current_windSpeed, current_dewPoint, current_pressure, current_cloudcover,
                current_visibility, forecast_figure, wind_rose_uri, gauge_fig, recommendation)


if __name__ == '__main__':
    app.run_server(debug=True)
