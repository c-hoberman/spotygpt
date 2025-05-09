import os, logging
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

logging.basicConfig(level=logging.DEBUG)
app = FastAPI()

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),
    scope="playlist-modify-public playlist-modify-private",
    cache_path=".cache-debug",
)

@app.get("/authorize")
def authorize():
    # clear stale cache
    sp_oauth.cache_handler.delete_cached_token()

    # debug print env
    logging.debug("SPOTIFY_CLIENT_ID=%r", os.getenv("SPOTIFY_CLIENT_ID"))
    logging.debug("REDIRECT_URI=%r", os.getenv("REDIRECT_URI"))

    # force the user prompt
    auth_url = sp_oauth.get_authorize_url(show_dialog=True)
    logging.debug("Auth URL: %s", auth_url)
    return {"auth_url": auth_url}

@app.get("/callback")
async def callback(request: Request):
    error = request.query_params.get("error")
    code  = request.query_params.get("code")
    logging.debug("Callback error=%r code=%r", error, code)

    if error:
        return RedirectResponse("/authorize")  # retry

    try:
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        logging.debug("Token info: %r", token_info)
    except Exception as e:
        logging.error("Token exchange failed: %s", e)
        return JSONResponse({"failed": str(e)}, status_code=400)

    # Store token_info in your DB/session…
    return {"status": "authorized"}
