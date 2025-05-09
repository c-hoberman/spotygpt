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
@app.get("/callback")
async def serve_callback():
    return FileResponse("public/callback.html")

# Spotify OAuth helper
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),   # must exactly match /oauth/callback or /callback
    scope="playlist-modify-public playlist-modify-private",
    cache_path=".cache-debug",
)

# Hand-craft the authorize redirect to Spotify
@app.get("/authorize")
def authorize():
     # delete old cache file…
        cache_path = sp_oauth.cache_handler.cache_path
        if cache_path and os.path.exists(cache_path):
            os.remove(cache_path)
    client_id    = os.getenv("SPOTIFY_CLIENT_ID")
    redirect_uri = os.getenv("REDIRECT_URI")  # should be ".../callback"
    scope        = "playlist-modify-public playlist-modify-private"
    params = {
      "client_id":     client_id,
      "response_type": "code",
      "redirect_uri":  redirect_uri,
      "scope":         scope,
      "show_dialog":   "true"
    }
    from urllib.parse import urlencode
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    logging.debug("→ Redirecting to: %s", auth_url)
    return RedirectResponse(auth_url)

# Dynamic code-exchange handler at /callback
@app.get("/callback")
async def callback(request: Request):
    logging.debug("▶️ Hit /callback URL: %s", request.url)
    logging.debug("   query params: %r", dict(request.query_params))

    error = request.query_params.get("error")
    if error:
        logging.error("❌ Spotify returned error: %s", error)
        return RedirectResponse("/authorize")

    code = request.query_params.get("code")
    logging.debug("️⃣ Received code: %r", code)
    try:
        sp_oauth = SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("REDIRECT_URI"),
            cache_path=".cache-debug",
        )
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        logging.debug("✅ Token info: %r", token_info)
        return {"status": "authorized"}
    except Exception as e:
        logging.exception("🔥 Token exchange failed")
        return JSONResponse(
            status_code=400,
            content={"error": "token_exchange_failed", "details": str(e)}
        )
