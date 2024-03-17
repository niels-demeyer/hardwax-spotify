import webbrowser
import requests
from flask import Flask, request
from dotenv import load_dotenv
import os

load_dotenv()

# You should replace these placeholders with your actual Spotify client values
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8090/callback"


app = Flask(__name__)


def authorize_app():
    scopes = "playlist-modify-private playlist-modify-public"
    auth_url = (
        f"https://accounts.spotify.com/authorize?client_id={CLIENT_ID}"
        f"&response_type=code&redirect_uri={REDIRECT_URI}&scope={scopes}"
    )
    webbrowser.open(auth_url)
    print(f"Please authorize the app by visiting this url: {auth_url}")


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if code:
        # Use the code to get tokens
        tokens = request_tokens(code)
        if tokens and "refresh_token" in tokens:
            return f"Success! Refresh token: {tokens['refresh_token']}"
        else:
            return "Failed to get access and refresh tokens."
    else:
        return "No code found."


def request_tokens(auth_code):
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Failed to fetch tokens. Status code: {response.status_code}, Message: {response.text}"
        )
        return None


if __name__ == "__main__":
    authorize_app()
    app.run(port=8090)
