class HttpError(Exception):
    """Custom HTTP error exception."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def clean_up_parameter(name: str, value: str) -> str:
    """Clean up common issues with Copilot parameters."""
    val = value.lower()

    if "trey" in val or "research" in val:
        new_val = val.replace("trey", "").replace("research", "").strip()
        print(f"   ❗ Plugin name detected in the {name} parameter '{val}'; replacing with '{new_val}'.")
        val = new_val

    if val == "<user_name>":
        print(f"   ❗ Invalid name '{val}'; replacing with 'avery'.")
        val = "avery"

    if name == "role" and val == "consultant":
        print(f"   ❗ Invalid role name '{val}'; replacing with ''.")
        val = ""

    if val == "null":
        print(f"   ❗ Invalid value '{val}'; replacing with ''.")
        val = ""

    return val
