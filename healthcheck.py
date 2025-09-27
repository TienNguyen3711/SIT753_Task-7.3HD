import requests
import sys

def check_api():
    try:
        r = requests.get("http://localhost:8000/health", timeout=5)
        if r.status_code == 200:
            return True
        return False
    except Exception as e:
        print(f"API healthcheck failed: {e}")
        return False

if __name__ == "__main__":
    if check_api():
        print(" App is healthy")
        sys.exit(0)
    else:
        print(" App is unhealthy")
        sys.exit(1)
