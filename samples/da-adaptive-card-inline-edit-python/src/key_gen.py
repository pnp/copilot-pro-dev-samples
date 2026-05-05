import secrets
import base64

KEY_LENGTH = 12

key = base64.b64encode(secrets.token_bytes(KEY_LENGTH)).decode("utf-8")[:KEY_LENGTH]

print(f"Generated a new API Key: {key}")
