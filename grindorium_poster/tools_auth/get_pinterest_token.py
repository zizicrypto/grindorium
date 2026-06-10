"""
Pinterest OAuth helper. Converts App ID and App Secret into an access token.
Works with trial access on your own account before standard access is granted.

Steps:
1. In the Pinterest developer portal add this redirect URI to your app:
   http://localhost:8085/
2. Fill APP_ID and APP_SECRET below or pass them as arguments:
   python get_pinterest_token.py APP_ID APP_SECRET
3. A browser opens, you approve, the token prints here.
4. Put the access token into config.json under platforms.pinterest.access_token
"""
import base64
import http.server
import sys
import threading
import urllib.parse
import webbrowser

import requests

APP_ID = ""
APP_SECRET = ""
REDIRECT = "http://localhost:8085/"
SCOPES = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"

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
    app_id = sys.argv[1] if len(sys.argv) > 1 else APP_ID
    secret = sys.argv[2] if len(sys.argv) > 2 else APP_SECRET
    if not app_id or not secret:
        raise SystemExit("Provide APP_ID and APP_SECRET")

    auth_url = ("https://www.pinterest.com/oauth/?response_type=code"
                f"&client_id={app_id}&redirect_uri={urllib.parse.quote(REDIRECT)}"
                f"&scope={urllib.parse.quote(SCOPES)}")
    server = http.server.HTTPServer(("localhost", 8085), Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()
    print("Opening browser for approval...")
    webbrowser.open(auth_url)
    while "code" not in code_holder:
        pass
    server.server_close()

    basic = base64.b64encode(f"{app_id}:{secret}".encode()).decode()
    resp = requests.post("https://api.pinterest.com/v5/oauth/token", timeout=60,
                         headers={"Authorization": f"Basic {basic}",
                                  "Content-Type": "application/x-www-form-urlencoded"},
                         data={"grant_type": "authorization_code",
                               "code": code_holder["code"],
                               "redirect_uri": REDIRECT})
    resp.raise_for_status()
    data = resp.json()
    print("\nACCESS TOKEN (config.json -> platforms.pinterest.access_token):")
    print(data.get("access_token"))
    print("\nRefresh token (sakla, access token suresi dolunca lazim olur):")
    print(data.get("refresh_token"))


if __name__ == "__main__":
    main()
