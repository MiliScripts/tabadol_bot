import requests
import time
import json
import io

TOKEN = "755633404:I7BVy6b168oMudJ1aT_R_8EIEw5T2uzNyFE"
CHAT_ID = "5976860939"
API_URL = "https://navasan.milaadfarzian.workers.dev/"

def get_price_data():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def send_to_bale_as_file(data):
    if data is None:
        return
    
    # Convert JSON to string
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    # Create file-like object
    file_bytes = io.BytesIO(json_str.encode('utf-8'))
    file_bytes.name = "prices.json"
    
    # Send as document
    url = f"https://tapi.bale.ai/bot{TOKEN}/sendDocument"
    files = {
        'document': (file_bytes.name, file_bytes, 'application/json')
    }
    payload = {
        'chat_id': CHAT_ID
    }
    
    try:
        r = requests.post(url, data=payload, files=files, timeout=10)
        if r.status_code != 200:
            print(f"Bale error: {r.text}")
        else:
            print(f"File sent successfully at {time.strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"Send error: {e}")

def main():
    print("Bot started. Sending JSON as file immediately...")
    
    # Send immediately on start
    data = get_price_data()
    send_to_bale_as_file(data)
    
    # Then every 5 minutes
    while True:
        time.sleep(300)
        data = get_price_data()
        send_to_bale_as_file(data)

if __name__ == "__main__":
    main()