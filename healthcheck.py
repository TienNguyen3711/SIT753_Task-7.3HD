# healthcheck.py
import sys
import requests

def main():
    try:
        resp = requests.get("http://localhost:8086/health")
        if resp.status_code == 200:
            print("Healthcheck passed ")
            sys.exit(0)
        else:
            print(f"Healthcheck failed  (status {resp.status_code})")
            sys.exit(1)
    except Exception as e:
        print(f"Healthcheck error : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
