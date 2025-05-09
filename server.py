import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from spotipy import SpotifyOAuth, Spotify

app = FastAPI()

# Pull secrets from environment – never commit these to GitHub!
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),
    scope="playlist-modify-public playlist-modify-private"
)

@app.get("/authorize")
def authorize():
    # Redirect the user to Spotify’s login/consent screen
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    token_info = sp_oauth.get_access_token(code, as_dict=True)
    # TODO: securely store token_info in your user session or DB
    return {"status": "authorized"}
