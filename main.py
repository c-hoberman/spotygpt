import os
import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

logging.basicConfig(level=logging.INFO)
app = FastAPI()

# ————————————————
# 1) ENV VAR SETUP (in Render or GitHub)
# ————————————————
CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI  = os.getenv("REDIRECT_URI")  # must match Spotify Dashboard exactly
SCOPE         = "playlist-modify-public playlist-modify-private"

if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    raise RuntimeError("Missing one of SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET / SPOTIPY_REDIRECT_URI")

# ————————————————
# 2) SPOTIPY OAUTH MANAGER (no cache, fresh every time)
# ————————————————
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=None,     # never write a cache file
    show_dialog=True     # always force login prompt
)

# ————————————————
# 3) /authorize → Spotify login
# ————————————————
@app.get("/authorize")
def authorize(request: Request):
    auth_url = sp_oauth.get_authorize_url()
    logging.info(f"Redirecting user to Spotify auth: {auth_url}")
    return RedirectResponse(auth_url)

# ————————————————
# 4) /callback ← Spotify redirects back here
# ————————————————
@app.get("/callback")
def callback(code: str = None, error: str = None):
    if error:
        # User denied or something else went wrong
        raise HTTPException(status_code=400, detail=f"Spotify error: {error}")

    try:
        # Exchange code for fresh tokens
        token_info = sp_oauth.get_access_token(code)
    except Exception as e:
        logging.error("Token exchange failed", exc_info=e)
        return JSONResponse({"error": "token_exchange_failed", "details": str(e)}, status_code=400)

    access_token  = token_info["access_token"]
    refresh_token = token_info.get("refresh_token")

    # Optional: return or store the refresh_token for later server-side refreshes.
    sp = Spotify(auth=access_token)
    user = sp.current_user()

    return {
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "user":          {"id": user["id"], "display_name": user["display_name"]},
    }

# ————————————————
# 5) Example protected endpoint
# ————————————————
@app.get("/me")
def me(token: str):
    """Call this with ?token=<access_token> to fetch your Spotify profile."""
    sp = Spotify(auth=token)
    return sp.current_user()
