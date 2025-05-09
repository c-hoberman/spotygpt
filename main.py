import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from spotipy import SpotifyOAuth, Spotify

app = FastAPI()

# Mount the 'public' folder to serve static files
app.mount("/static", StaticFiles(directory="public"), name="static")

# Serve the callback page directly
@app.get("/oauth/callback")
async def serve_callback():
    return FileResponse("public/oauth/callback.html")

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),
    scope="playlist-modify-public playlist-modify-private",
)

@app.get("/authorize")
def authorize():
    # This always generates a fresh auth URL
    return RedirectResponse(sp_oauth.get_authorize_url())

@app.get("/callback")
async def callback(request: Request):
    error = request.query_params.get("error")
    if error:
        # 1) clear Spotipy’s cache for this user
        sp_oauth.cache_handler.delete_cached_token()
        # 2) redirect straight back into the auth flow
        return RedirectResponse("/authorize")
    code = request.query_params.get("code")
    token_info = sp_oauth.get_access_token(code, as_dict=True)
    # store token_info and continue…
    return {"status": "authorized"}
