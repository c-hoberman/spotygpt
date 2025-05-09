# File: server.py
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
import httpx
import os

app = FastAPI()
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "https://yourdomain.com/oauth/callback"

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
