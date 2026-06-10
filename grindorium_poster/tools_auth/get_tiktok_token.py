"""
TikTok OAuth helper. Use after the app review is approved.

Steps:
1. In the TikTok developer portal add this redirect URI to your app:
   http://localhost:8086/
2. Make sure the video.publish scope is approved.
3. python get_tiktok_token.py CLIENT_KEY CLIENT_SECRET
4. Approve in the browser, the token prints here.
5. Put it into config.json under platforms.tiktok.access_token
Note: TikTok access tokens expire in 24 hours. The refresh token lasts longer.
For unattended use, store the refresh token in config and the poster can be
extended to auto refresh. Ask for that extension when you reach this stage.
"""
import http.server
import sys
import threading
import urllib.parse
import webbrowser

import requests

REDIRECT = "http://localhost:8086/"
SCOPES = "video.publish,video.upload"

code_holder = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(qs)
        code_holder["code"] = params.get("code", [""])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h2>Done. Return to the terminal.</h2>")

    def log_message(self, *args):
        pass


def main():
    if len(sys.argv) < 3:
        raise SystemExit("Usage: python get_tiktok_token.py CLIENT_KEY CLIENT_SECRET")
    client_key, client_secret = sys.argv[1], sys.argv[2]

    auth_url = ("https://www.tiktok.com/v2/auth/authorize/?response_type=code"
                f"&client_key={client_key}&redirect_uri={urllib.parse.quote(REDIRECT)}"
                f"&scope={urllib.parse.quote(SCOPES)}&state=grindorium")
    server = http.server.HTTPServer(("localhost", 8086), Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()
    print("Opening browser for approval...")
    webbrowser.open(auth_url)
    while "code" not in code_holder:
        pass
    server.server_close()

    resp = requests.post("https://open.tiktokapis.com/v2/oauth/token/", timeout=60,
                         headers={"Content-Type": "application/x-www-form-urlencoded"},
                         data={"client_key": client_key,
                               "client_secret": client_secret,
                               "code": code_holder["code"],
                               "grant_type": "authorization_code",
                               "redirect_uri": REDIRECT})
    resp.raise_for_status()
    data = resp.json()
    print("\nACCESS TOKEN (config.json -> platforms.tiktok.access_token):")
    print(data.get("access_token"))
    print("\nRefresh token (sakla):")
    print(data.get("refresh_token"))


if __name__ == "__main__":
    main()
