import os, logging
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
from spotipy import SpotifyOAuth

logging.basicConfig(level=logging.DEBUG)
app = FastAPI()

SPOTIFY_AUTH_URL  = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

@app.get("/oauth2/authorize")
def proxy_authorize():
    # forward query string to Spotify’s authorize URL
    return RedirectResponse(f"{SPOTIFY_AUTH_URL}?{Request.scope['query_string'].decode()}")

@app.post("/oauth2/token")
async def proxy_token(
    grant_type: str = Form(...),
    code: str       = Form(None),
    refresh_token: str = Form(None),
    redirect_uri: str  = Form(...),
    client_id: str     = Form(...),
    client_secret: str = Form(...),
):
    # relay this POST to Spotify’s token endpoint
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type":    grant_type,
                "code":          code,
                "refresh_token": refresh_token,
                "redirect_uri":  redirect_uri,
            },
            auth=(client_id, client_secret),
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())
    
# Spotify helper
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),   # e.g. "https://your-app.onrender.com/callback"
    scope="playlist-modify-public playlist-modify-private",
    cache_path=".cache-debug",
)

@app.get("/authorize")
def authorize():
    # build the Spotify URL by hand
    from urllib.parse import urlencode
    params = {
      "client_id":     os.getenv("SPOTIFY_CLIENT_ID"),
      "response_type": "code",
      "redirect_uri":  os.getenv("REDIRECT_URI"),
      "scope":         "playlist-modify-public playlist-modify-private",
      "show_dialog":   "true"
    }
    auth_url = "https://accounts.spotify.com/authorize?" + urlencode(params)
    logging.debug("→ Redirecting to: %s", auth_url)
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request):
    logging.debug("▶️  Hit /callback: %s", request.url)
    logging.debug("   params: %r", dict(request.query_params))

    # If the user denied consent
    if request.query_params.get("error"):
        return RedirectResponse("/authorize")

    code = request.query_params.get("code")
    logging.debug("🔑 Received code: %r", code)

    try:
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        logging.debug("✅ Token info: %r", token_info)
    except Exception as e:
        # Log full traceback
        logging.exception("🔥 Token exchange exception")
        # If it’s an HTTPError from Spotipy, log the raw response
        if hasattr(e, "response"):
            logging.error("Spotify responded: %s", e.response.text)
        return JSONResponse(
            status_code=400,
            content={"error":"token_exchange_failed","details":str(e)}
        )

    # On success, show your HTML confirmation page
    return FileResponse("public/callback.html")
