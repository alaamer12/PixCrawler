from package_a import hello
import requests

def world():
    hello()
    print("Hello from package-b!")
    try:
        response = requests.get("http://www.google.com")
        print(f"Successfully made a request to Google. Status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to make a request: {e}")
