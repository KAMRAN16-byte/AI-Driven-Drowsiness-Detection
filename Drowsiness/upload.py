import requests

def server(filename):
    url = "http://192.168.1.241:8001/api/upload" # Update with your server's IP and port
    data = {"driver_name": "Driver1"} # You can modify this to include more driver details if needed

    # Always close the file safely
    with open(filename, "rb") as f:
        files = {"image": f}
        response = requests.post(url, data=data, files=files)

    print(response.json())
