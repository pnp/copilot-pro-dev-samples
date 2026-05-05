import shutil
import subprocess
import sys


def run_azure_functions():
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
