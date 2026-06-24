# Uses the ServiceNow Rest API to deal with profile information

import os
import requests
from dotenv import load_dotenv

load_dotenv("env/.env.local.user")


class ProfilesApiService:

    def __init__(self):
        self.sn_instance = os.environ.get("SN_INSTANCE", "")
        self.sn_username = os.environ.get("SN_USERNAME", "")
        self.sn_password = os.environ.get("SN_PASSWORD", "")

    @property
    def _base_url(self) -> str:
        return f"https://{self.sn_instance}.service-now.com/api/now/table"

    @property
    def _auth(self) -> tuple:
        return (self.sn_username, self.sn_password)

    @property
    def _headers(self) -> dict:
        return {"Content-Type": "application/json"}

    def get_profile(self, email: str) -> list:
        """Fetch a user profile from ServiceNow by email."""
        response = requests.get(
            f"{self._base_url}/sys_user",
            params={
                "sysparm_limit": 10,
                "sysparm_query": f"email={email}",
            },
            auth=self._auth,
            headers=self._headers,
        )
        response.raise_for_status()
        result = response.json().get("result", [])
        print(f"Profile fetched successfully from ServiceNow: {result}")
        return result
