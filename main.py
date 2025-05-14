import os, logging, base64, requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

logging.basicConfig(level=logging.INFO)
app = FastAPI()

print("→ SPOTIFY_REDIRECT_URI is:", os.getenv("SPOTIFY_REDIRECT_URI"))
# ─── Env vars ─────────────────────────────────────────────────────────────
CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI  = os.getenv("REDIRECT_URI")  # must match your Dashboard exactly

if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    raise RuntimeError(
        "Missing env-vars: SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, or SPOTIFY_REDIRECT_URI"
    )

# ─── /authorize endpoint ─────────────────────────────────────────────────
@app.get("/authorize")
def authorize():
    from urllib.parse import urlencode
    params = {
        "client_id":     CLIENT_ID,
        "response_type": "code",
        "redirect_uri":  REDIRECT_URI,
        "scope":         "playlist-modify-private playlist-modify-public",
        "show_dialog":   "true"
    }
    auth_url = "https://accounts.spotify.com/authorize?" + urlencode(params)
    logging.info("Redirecting to Spotify auth URL: %s", auth_url)
    return RedirectResponse(auth_url)

# ─── /callback endpoint ──────────────────────────────────────────────────
@app.get("/callback")
def callback(request: Request):
    code  = request.query_params.get("code")
    error = request.query_params.get("error")
    logging.info("Callback received; code=%s, error=%s", code, error)

    if error:
        raise HTTPException(400, f"Spotify error: {error}")
    if not code:
        raise HTTPException(400, "No authorization code in callback")

    # Exchange code for tokens
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    b64_auth = base64.b64encode(auth_str).decode()
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type":  "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type":   "authorization_code",
        "code":         code,
        "redirect_uri": REDIRECT_URI
    }
    resp = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    logging.info("Token exchange status: %s", resp.status_code)
    if not resp.ok:
        # print Spotify’s error JSON so we can debug it
        logging.error("Spotify token error: %s", resp.text)
        return JSONResponse(status_code=resp.status_code, content=resp.json())

    token_info = resp.json()
    return token_info  # contains access_token, refresh_token, etc.
