from dotenv import load_dotenv, set_key
from pathlib import Path
import os
import base64
import requests
import re
from datetime import datetime


class SchwabClient:
    def __init__(self):
        # Define .env path
        self.env_path = Path(__file__).resolve().parent / ".env"

        # Load environment (if file exists)
        if self.env_path.exists():
            load_dotenv(dotenv_path=self.env_path)

        # Load core configuration (these exist always)
        self.client_id = os.getenv("APP_KEY")
        self.client_secret = os.getenv("APP_SECRET")
        self.redirect_uri = os.getenv("APP_CALLBACK_URL")
        self.base_url = os.getenv("BASE_URL")

        # Token endpoint
        self.token_endpoint = f"{self.base_url}/v1/oauth/token"

        # Tokens (may be None initially)
        self.auth_code_url = os.getenv("AUTH_CODE_URL")
        self.auth_code = os.getenv("AUTH_CODE")
        self.access_token = os.getenv("ACCESS_TOKEN")
        self.refresh_token = os.getenv("REFRESH_TOKEN")
        self.id_token = os.getenv("ID_TOKEN")

    # -----------------------------------------------------
    # 👇 Entry point for authentication handling
    # -----------------------------------------------------
    def handle_authentication(self, authenticate=True, expiry_days = 7):

        file_age = self._get_env_file_age_days()

        if file_age > expiry_days or authenticate:
            self._authorize_and_get_tokens()

        self._refresh_access_token()

    # -----------------------------------------------------
    # 👇 Refresh access token (Step 4)
    # -----------------------------------------------------
    def _refresh_access_token(self):
        """Use the stored refresh token to get new access + refresh tokens."""
        try:
            credentials = f"{self.client_id}:{self.client_secret}"
            b64_credentials = base64.b64encode(credentials.encode()).decode()

            headers = {
                "Authorization": f"Basic {b64_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            }

            response = requests.post(self.token_endpoint, headers=headers, data=data)
            token_data = response.json()

            # Handle invalid or expired refresh token
            if "access_token" not in token_data:
                print("❌ Failed to refresh tokens:", token_data)
                return False

            print("✅ Refreshed token successfully")#, token_data)

            # Save updated tokens
            set_key(self.env_path, "REFRESH_TOKEN", token_data.get("refresh_token", ""))
            set_key(self.env_path, "ACCESS_TOKEN", token_data.get("access_token", ""))
            set_key(self.env_path, "ID_TOKEN", token_data.get("id_token", ""))

            # Update class properties
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.id_token = token_data.get("id_token")

            print("💾 New tokens saved to .env.")
            return True

        except Exception as e:
            print(f"❌ Error refreshing token: {e}")
            return False

    # -----------------------------------------------------
    # 👇 Utility: check file age
    # -----------------------------------------------------
    def _get_env_file_age_days(self):
        """Return .env file age in days, or 0 if just created."""
        try:
            modified_time = datetime.fromtimestamp(self.env_path.stat().st_mtime)
            return (datetime.now() - modified_time).days
        except FileNotFoundError:
            return 9999  # treat as very old

    # -----------------------------------------------------
    # 👇 Core token retrieval logic
    # -----------------------------------------------------
    def _get_auth_code_url(self):
        """Prompt user to authenticate and paste redirect URL."""
        auth_url = f'https://api.schwabapi.com/v1/oauth/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}'
        print("\n🔗 Click this link to authenticate:\n")
        print(auth_url)
        print("\nAfter login, copy the full redirect URL (starting with https://127.0.0.1...)")
        return input("Paste it here: ").strip()

    def _extract_auth_code(self, auth_code_url):
        """Extract 'code' value from redirect URL."""
        return auth_code_url.split("code=")[1].split("&")[0].replace("%40", "@")

    def _authorize_and_get_tokens(self):
        """Request new tokens and save to .env."""
        auth_code_url = self._get_auth_code_url()
        auth_code = self._extract_auth_code(auth_code_url)

        credentials = f"{self.client_id}:{self.client_secret}"
        b64_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {b64_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri
        }

        print("\n📡 Requesting tokens from Schwab API...")
        response = requests.post(self.token_endpoint, headers=headers, data=data)
        token_data = response.json()
        print("✅ Token response received")#, token_data)

        # Ensure .env exists
        self.env_path.touch(exist_ok=True)

        # Save new tokens
        set_key(self.env_path, "AUTH_CODE_URL", auth_code_url)
        set_key(self.env_path, "AUTH_CODE", auth_code)
        set_key(self.env_path, "REFRESH_TOKEN", token_data.get("refresh_token", ""))
        set_key(self.env_path, "ACCESS_TOKEN", token_data.get("access_token", ""))
        set_key(self.env_path, "ID_TOKEN", token_data.get("id_token", ""))

        self.auth_code_url = auth_code_url
        self.auth_code = auth_code
        self.access_token = token_data.get("refresh_token", "")
        self.refresh_token = token_data.get("access_token", "")
        self.id_token = token_data.get("id_token", "")

        print("💾 Tokens saved to .env successfully.")

    def get_headers(self):
        """Return headers with Authorization: Bearer {access_token}"""
        if not self.access_token:
            raise ValueError("Access token not found. Run handle_authentication() first.")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
