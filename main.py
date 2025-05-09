import os, logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
from spotipy import SpotifyOAuth

logging.basicConfig(level=logging.DEBUG)

# ← Only one FastAPI instance
app = FastAPI()

# Mount static files once
app.mount("/static", StaticFiles(directory="public"), name="static")

# If your REDIRECT_URI is ".../oauth/callback", serve that here:
@app.get("/oauth/callback")
async def serve_callback():
    return FileResponse("public/oauth/callback.html")

# Spotify OAuth helper
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),   # must exactly match /oauth/callback or /callback
    scope="playlist-modify-public playlist-modify-private",
    cache_path=".cache-debug",
)

# Step 2 goes here: force the dialog in your authorize route

@app.get("/authorize")
@app.get("/authorize")
def authorize():
    try:
        # delete old cache file…
        cache_path = sp_oauth.cache_handler.cache_path
        if cache_path and os.path.exists(cache_path):
            os.remove(cache_path)

        # build the URL (no show_dialog arg)
        auth_url = sp_oauth.get_authorize_url()
        # manually tack on the param
        if "?" in auth_url:
            auth_url += "&show_dialog=true"
        else:
            auth_url += "?show_dialog=true"

        logging.debug("Auth URL with show_dialog → %s", auth_url)
        return RedirectResponse(auth_url)

    except Exception as e:
        logging.exception("Error in /authorize")
        return JSONResponse({"error": "authorize_failed", "details": str(e)}, status_code=500)


# This must match your REDIRECT_URI path too!
@app.get("/callback")
async def callback(request: Request):
    error = request.query_params.get("error")
    code  = request.query_params.get("code")
    logging.debug("Callback error=%r code=%r", error, code)

    if error:
        return RedirectResponse("/authorize")

    try:
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        logging.debug("Token info: %r", token_info)
    except Exception as e:
        logging.error("Token exchange failed: %s", e)
        return JSONResponse({"failed": str(e)}, status_code=400)

    return {"status": "authorized"}
