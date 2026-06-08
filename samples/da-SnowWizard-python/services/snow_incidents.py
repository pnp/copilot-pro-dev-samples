# Uses the ServiceNow Rest API to deal with incidents

import os
import requests
from dotenv import load_dotenv

load_dotenv("env/.env.local.user")


class IncidentsApiService:

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

    def get_incident(self, incident_id: str) -> list:
        """Fetch a single incident from ServiceNow by number."""
        response = requests.get(
            f"{self._base_url}/incident",
            params={
                "sysparm_limit": 1,
                "sysparm_fields": "number,made_sla,short_description,description,priority,opened_at",
                "sysparm_query": f"number={incident_id}",
            },
            auth=self._auth,
            headers=self._headers,
        )
        response.raise_for_status()
        result = response.json().get("result", [])
        print(f"Incidents fetched successfully from ServiceNow: {result}")
        return result

    def get_incidents(self) -> list:
        """Fetch the latest 10 incidents from ServiceNow."""
        response = requests.get(
            f"{self._base_url}/incident",
            params={
                "sysparm_limit": 10,
                "sysparm_fields": "number,made_sla,short_description,description,priority,opened_at",
                "sysparm_query": "ORDERBYDESCsys_created_on",
            },
            auth=self._auth,
            headers=self._headers,
        )
        response.raise_for_status()
        result = response.json().get("result", [])
        print(f"Incidents fetched successfully from ServiceNow: {result}")
        return result

    def get_user_incidents(self, username: str) -> list:
        """Fetch the latest 10 incidents assigned to a user."""
        sys_id = self._get_user_sys_id(username)
        response = requests.get(
            f"{self._base_url}/incident",
            params={
                "sysparm_limit": 10,
                "sysparm_fields": "number,made_sla,short_description,description,priority,opened_at",
                "sysparm_query": f"ORDERBYDESCsys_created_on^assigned_to={sys_id}",
            },
            auth=self._auth,
            headers=self._headers,
        )
        response.raise_for_status()
        result = response.json().get("result", [])
        print(f"Incidents fetched successfully from ServiceNow: {result}")
        return result

    def create_incident(self, email: str, short_description: str, description: str) -> dict:
        """Create a new incident in ServiceNow."""
        sys_id = self._get_user_sys_id(email)
        response = requests.post(
            f"{self._base_url}/incident",
            json={
                "short_description": short_description,
                "description": description,
                "caller_id": sys_id,
            },
            auth=self._auth,
            headers=self._headers,
        )
        response.raise_for_status()
        result = response.json().get("result", {})
        print(f"Incident created successfully in ServiceNow: {result}")
        return result

    def _get_user_sys_id(self, username: str) -> str:
        """Get the sys_id of a user by email."""
        response = requests.get(
            f"{self._base_url}/sys_user",
            params={
                "sysparm_limit": 10,
                "sysparm_query": f"email={username}",
            },
            auth=self._auth,
            headers=self._headers,
        )
        response.raise_for_status()
        result = response.json().get("result", [])
        print(f"User fetched successfully from ServiceNow: {result}")
        return result[0]["sys_id"]
