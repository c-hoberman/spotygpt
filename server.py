# File: server.py
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, RedirectResponse
import httpx
import os
import urllib.parse

app = FastAPI()

CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
REDIRECT_URI  = os.getenv("REDIRECT_URI")
SCOPES        = "user-read-private user-read-email playlist-modify-public playlist-modify-private"

@app.get("/oauth/login")
def oauth_login():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        # optional: send a random “state” string here and verify it in callback
    }
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)
    
app = FastAPI()
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "https://yourdomain.com/oauth/callback"


CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

@app.get("/oauth/callback")
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(400, "Missing code in callback")

    data = {
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://accounts.spotify.com/api/token",
            data=data, headers=headers
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, f"Token exchange failed: {resp.text}")

    tokens = resp.json()  
    # tokens contains: access_token, token_type, expires_in, refresh_token, scope

    # For now, stash them in memory (you can swap this for a DB or file)
    request.app.state.spotify_tokens = tokens

    return JSONResponse({"message": "Spotify authentication successful! You can close this tab."})

async def get_access_token():
    tokens = app.state.spotify_tokens
    if not tokens or "access_token" not in tokens:
        raise HTTPException(401, "Not authenticated with Spotify")
    return tokens["access_token"]

@app.get("/playlists")
async def get_playlists(key: str, access_token: str = Depends(get_access_token)):
    if key != "supersecret123":
        raise HTTPException(403, "Bad API key")
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.spotify.com/v1/me/playlists",
            headers=headers, params={"limit": 50}
        )
    return r.json()

@app.get("/")
def health_check():
    return {"status": "ok"}

app.mount(
    "/.well-known",
    StaticFiles(directory="static/.well-known"),
    name="well-known"
)

@app.get("/oauth/login")
def login():
    url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=user-read-private playlist-read-private user-read-playback-state"
    )
    return RedirectResponse(url)

@app.get("/oauth/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET
            }
        )
    data = resp.json()
    # Store tokens in user session/store
    return JSONResponse(data)

@app.get("/playlists")
async def get_playlists(request: Request):
    # Retrieve stored user access token
    access_token = "USER_ACCESS_TOKEN"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.spotify.com/v1/me/playlists", headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return JSONResponse(resp.json())
