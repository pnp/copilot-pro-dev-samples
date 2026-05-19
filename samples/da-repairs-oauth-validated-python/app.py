import os
import shutil
import subprocess
import sys
from pathlib import Path


def load_local_configs():
    """Load environment variables from .localConfigs file."""
    config_file = Path(__file__).parent / ".localConfigs"
    if config_file.exists():
        for line in config_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def run_azure_functions():
    load_local_configs()

    func_path = shutil.which("func")

    if func_path:
        try:
            subprocess.run(
                [func_path, "start", "--port", "7071", "--cors", "*"],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running Azure Functions: {e}")
            sys.exit(1)
    else:
        print("Azure Functions Core Tools not found. Install from: https://learn.microsoft.com/azure/azure-functions/functions-run-local")
        sys.exit(1)


if __name__ == "__main__":
    run_azure_functions()
