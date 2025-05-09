import os, logging
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
from urllib.parse import urlencode
from spotipy import SpotifyOAuth

logging.basicConfig(level=logging.DEBUG)
app = FastAPI()

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),   # https://your-app.onrender.com/callback
    scope="playlist-modify-public playlist-modify-private",
    cache_path=".cache-debug",
)

@app.get("/authorize")
def authorize():
    # clear cache file…
    cache = sp_oauth.cache_handler.cache_path
    if cache and os.path.exists(cache):
        os.remove(cache)

    params = {
      "client_id":     os.getenv("SPOTIFY_CLIENT_ID"),
      "response_type": "code",
      "redirect_uri":  os.getenv("REDIRECT_URI"),
      "scope":         "playlist-modify-public playlist-modify-private",
      "show_dialog":   "true"
    }
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    logging.debug("→ Redirecting to: %s", auth_url)
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request):
    logging.debug("▶️ Hit /callback URL: %s", request.url)
    logging.debug("   query params: %r", dict(request.query_params))

    if request.query_params.get("error"):
        return RedirectResponse("/authorize")

    code = request.query_params.get("code")
    try:
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        logging.debug("✅ Token info: %r", token_info)
    except Exception as e:
        logging.exception("🔥 Token exchange failed")
        return JSONResponse(
            status_code=400,
            content={"error":"token_exchange_failed","details":str(e)}
        )

    # once authorized, show your static HTML page
    return FileResponse("public/callback.html")
