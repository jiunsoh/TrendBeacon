import http.server
import socketserver
import urllib.parse
import requests
import json
import os
import hashlib
import base64
import secrets
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")

PORT = 3000

# Store PKCE verifier server-side so it works across browser sessions
PKCE_STORE = {}

def generate_pkce():
    """Generate PKCE code_verifier and code_challenge server-side."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
    return verifier, challenge

class TikTokAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        # Step 1: Start login - generate PKCE and redirect to TikTok
        if parsed_path.path == "/login":
            verifier, challenge = generate_pkce()
            # Store verifier server-side with a state key
            state = secrets.token_urlsafe(16)
            PKCE_STORE[state] = verifier
            
            scopes = "user.info.basic,video.list"
            auth_url = (
                f"https://www.tiktok.com/v2/auth/authorize"
                f"?client_key={CLIENT_KEY}"
                f"&scope={scopes}"
                f"&response_type=code"
                f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
                f"&state={state}"
                f"&code_challenge={challenge}"
                f"&code_challenge_method=S256"
            )
            
            print(f"Redirecting to TikTok login...")
            self.send_response(302)
            self.send_header("Location", auth_url)
            self.end_headers()

        # Step 2: Handle the callback from TikTok - exchange code immediately
        elif parsed_path.path == "/callback":
            query = urllib.parse.parse_qs(parsed_path.query)
            code = query.get("code", [None])[0]
            state = query.get("state", [None])[0]
            error = query.get("error", [None])[0]
            
            if error:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                error_desc = query.get("error_description", ["Unknown error"])[0]
                self.wfile.write(f"<h1>Login Error</h1><p>{error}: {error_desc}</p>".encode())
                return
            
            if not code or not state:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Error</h1><p>Missing code or state from TikTok.</p>")
                return
            
            # Retrieve the stored verifier
            verifier = PKCE_STORE.pop(state, None)
            if not verifier:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Error</h1><p>Session expired. Please try logging in again.</p>")
                return
            
            # Exchange code for token immediately (server-side)
            token_url = "https://open.tiktokapis.com/v2/oauth/token/"
            data = {
                "client_key": CLIENT_KEY,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "code_verifier": verifier,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI
            }
            
            print(f"Exchanging code for access token via v2 API...")
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = requests.post(token_url, data=data, headers=headers)
            token_data = response.json()
            print(f"Token response: {json.dumps(token_data, indent=2)}")
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            if "access_token" in token_data:
                with open("token.json", "w") as f:
                    json.dump(token_data, f, indent=2)
                print("Token saved to token.json!")
                self.wfile.write(b"""
                <html><body style="background:#010101;color:#fff;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;flex-direction:column;">
                <h1 style="color:#4ade80;">&#10003; Connected!</h1>
                <p>TrendBeacon is now linked to your TikTok account.</p>
                <p style="color:#888;">Redirecting to dashboard...</p>
                <script>setTimeout(() => window.location.href = '/trendbeacon.html', 2000);</script>
                </body></html>
                """)
            elif "data" in token_data and "access_token" in token_data.get("data", {}):
                with open("token.json", "w") as f:
                    json.dump(token_data["data"], f, indent=2)
                print("Token saved to token.json!")
                self.wfile.write(b"""
                <html><body style="background:#010101;color:#fff;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;flex-direction:column;">
                <h1 style="color:#4ade80;">&#10003; Connected!</h1>
                <p>TrendBeacon is now linked to your TikTok account.</p>
                <p style="color:#888;">Redirecting to dashboard...</p>
                <script>setTimeout(() => window.location.href = '/trendbeacon.html', 2000);</script>
                </body></html>
                """)
            else:
                error_msg = token_data.get('error_description', token_data.get('message', json.dumps(token_data)))
                print(f"Token exchange failed: {error_msg}")
                self.wfile.write(f"<h1>Error</h1><p>{error_msg}</p><pre>{json.dumps(token_data, indent=2)}</pre>".encode())

        # API endpoints for the dashboard
        elif parsed_path.path == "/api/data":
            from tiktok_api import get_all_data
            data = get_all_data()
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        elif parsed_path.path == "/api/user":
            from tiktok_api import get_user_info
            data = get_user_info()
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        elif parsed_path.path == "/api/videos":
            from tiktok_api import get_video_list
            data = get_video_list()
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        else:
            # Serve regular files (html, css, js)
            return super().do_GET()

if __name__ == "__main__":
    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("Required library 'requests' not found. Installing...")
        import subprocess
        subprocess.check_call(["python", "-m", "pip", "install", "requests", "python-dotenv"])
        import requests

    print(f"Starting TrendBeacon local server at http://localhost:{PORT}")
    print(f"Login URL: {REDIRECT_URI.replace('/callback', '/login')}")
    with socketserver.TCPServer(("", PORT), TikTokAuthHandler) as httpd:
        httpd.serve_forever()
