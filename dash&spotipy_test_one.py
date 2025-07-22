import dash
from dash import dcc, html, Input, Output, State
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import flask
import os
import json
from collections import defaultdict

# ----------------------- Spotify OAuth Configuration -----------------------
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = ''
SCOPE = 'user-read-recently-played user-top-read user-read-playback-position'

# ----------------------- Authentication Function (adjusted from script) -----------------------
def authenticate(scope):
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=scope,
        cache_path=".spotifycache",
        show_dialog=True
    ))

# Dash and Flask server
server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True)

# Try authentication at startup
try:
    sp = authenticate(SCOPE)
    token_valid = True
except Exception as e:
    sp = None
    token_valid = False

# ----------------------- Dash Layout -----------------------
app.layout = html.Div([
    html.H2("🎵 Spotify Track Insights Dashboard"),
    html.Div(id='auth-status'),
    html.Br(),

    html.Div([
        dcc.Input(id='track-search', type='text', placeholder='Search for a track...', debounce=True),
        html.Button('Search', id='search-button', n_clicks=0),
        html.Br(), html.Br(),
        dcc.Dropdown(id='track-dropdown', placeholder='Select a track...')
    ], style={'display': 'block' if token_valid else 'none'}, id='search-area'),

    html.Div(id='track-stats'),
    html.Br(),

    html.Div([
        html.H4("🎶 Display Top Tracks"),
        dcc.Input(id='top-n', type='number', placeholder='Enter number of top tracks...', min=1),
        html.Button('Show Top Tracks', id='show-top-button', n_clicks=0),
        html.Div(id='top-tracks-output')
    ]),

    html.Br(),

    html.Div([
        html.H4("🎤 Top Tracks by Artist"),
        dcc.Input(id='artist-name', type='text', placeholder='Enter artist name...'),
        html.Button('Find Artist Tracks in Top 50', id='artist-search-button', n_clicks=0),
        html.Div(id='artist-track-output')
    ]),

    html.Br(),

    html.Div([
        html.H4("🏆 Top Artists Range Selection (Short/Medium/Long):"),
        dcc.Dropdown(
            id='artist-range-dropdown',
            options=[
                {'label': 'Short Term (last 4 weeks)', 'value': 'short_term'},
                {'label': 'Medium Term (last 6 months)', 'value': 'medium_term'},
                {'label': 'Long Term (all time)', 'value': 'long_term'}
            ],
            value='long_term'
        ),
        html.Br(),
        html.Label("Number of Artists to Display:"),
        dcc.Input(id='artist-count-input', type='number', placeholder='Number of artists', min=1, max=50, value=20),
        html.Div(id='top-artists-output')
    ])
])

# ----------------------- Callbacks -----------------------
@app.callback(
    Output('auth-status', 'children'),
    Output('search-area', 'style'),
    Input('search-button', 'n_clicks'),
    prevent_initial_call=True
)
def display_login_status(n_clicks):
    if sp:
        return '✅ Successfully authenticated with Spotify.', {'display': 'block'}
    return '🔒 Authentication failed. Please check credentials or permissions.', {'display': 'none'}

@app.callback(
    Output('track-dropdown', 'options'),
    Input('search-button', 'n_clicks'),
    State('track-search', 'value'),
    prevent_initial_call=True
)
def search_tracks(n_clicks, search_term):
    return [] if not sp or not search_term else [
        {'label': f"{item['name']} - {item['artists'][0]['name']}", 'value': item['id']}
        for item in sp.search(q=search_term, type='track', limit=10)['tracks']['items']
    ]

@app.callback(
    Output('track-stats', 'children'),
    Input('track-dropdown', 'value')
)
def calculate_track_stats(track_id):
    if not sp or not track_id:
        return ''

    recent = sp.current_user_recently_played(limit=50)
    count = 0
    total_ms = 0
    for item in recent['items']:
        if item['track']['id'] == track_id:
            count += 1
            total_ms += item['track']['duration_ms']

    total_time_minutes = total_ms / 60000

    top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term')
    ranking = 'Not in top 50'
    for i, item in enumerate(top_tracks['items']):
        if item['id'] == track_id:
            ranking = f"#{i+1}"
            break

    return html.Div([
        html.H4("📊 Track Listening Stats"),
        html.P(f"Total listened time: {total_time_minutes:.2f} minutes"),
        html.P(f"Number of times listened (last 50 plays): {count}"),
        html.P(f"Top Track Ranking (all time): {ranking}")
    ])

@app.callback(
    Output('top-tracks-output', 'children'),
    Input('show-top-button', 'n_clicks'),
    State('top-n', 'value')
)
def display_top_tracks(n_clicks, n):
    if not sp or not n:
        return ''

    top_tracks = sp.current_user_top_tracks(limit=n, time_range='long_term')
    display = [html.H4("🎧 Your Top Tracks:")]
    for i, item in enumerate(top_tracks['items'], start=1):
        display.append(html.P(f"{i}. {item['name']} - {item['artists'][0]['name']}"))
    return display

@app.callback(
    Output('artist-track-output', 'children'),
    Input('artist-search-button', 'n_clicks'),
    State('artist-name', 'value')
)
def artist_top_count(n_clicks, artist_name):
    if not sp or not artist_name:
        return ''

    top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term')
    matching_tracks = [track for track in top_tracks['items'] if track['artists'][0]['name'].lower() == artist_name.lower()]
    count = len(matching_tracks)

    return html.P(f"❌ No top 50 tracks by artist '{artist_name}' found.") if count == 0 else [
        html.P(f"✅ {count} of your top 50 tracks are by '{artist_name}':")
    ] + [html.P(f"{i+1}. {track['name']}") for i, track in enumerate(matching_tracks)]

@app.callback(
    Output('top-artists-output', 'children'),
    Input('artist-range-dropdown', 'value'),
    State('artist-count-input', 'value')
)
def show_top_artists(selected_range, count):
    if not sp:
        return ''

    top_artists = sp.current_user_top_artists(limit=count, time_range=selected_range)
    output = [html.H4("🧠 Top Artists:")]
    for i, item in enumerate(top_artists['items'], start=1):
        output.append(html.P(f"{i}. {item['name']}"))

    return output

# ----------------------- Run Server -----------------------
if __name__ == '__main__':
    app.run(debug=True, port=8050)
    print("Visit http://127.0.0.1:8050 to open the dashboard")
