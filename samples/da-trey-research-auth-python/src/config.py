import os


class Config:
    entra_app_client_id: str = os.environ.get("ENTRA_APP_CLIENT_ID", "")
    entra_app_tenant_id: str = os.environ.get("ENTRA_APP_TENANT_ID", "")


config = Config()
