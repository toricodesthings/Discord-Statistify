import os, json, time
import apiwrapper as spotifyapi
from datetime import datetime

#TERMINAL COLOR CODE
RED, GREEN, LIGHT_BLUE, RESET = "\033[91m", "\033[92m", "\033[94m", "\033[0m" 

def load_token():
    file_path = os.path.join(os.path.dirname(__file__), 'accesstoken.json')
    
    try:
        with open(file_path, 'r') as file:
            saved_token = json.load(file)
            
            # Check if token is previous generated
            if saved_token and saved_token["access_token"] is not None:
                current_time = int(time.time())
                # Check if token is expired and attempt to generate a new one if 30 seconds before expiration
                if current_time < (saved_token["expires_at"] - 30):
                    token = saved_token["access_token"]
                    expiry_time = datetime.fromtimestamp(saved_token["expires_at"]).strftime("%d-%m-%y %H:%M:%S")
                    return token, expiry_time
                
    except FileNotFoundError:
        pass
    return None, None
    
def store_token(token, expires_at):
    file_path = os.path.join(os.path.dirname(__file__), 'accesstoken.json')
    token_data = {
        'access_token': token,
        'expires_at': expires_at
    }
    try:
        with open(file_path, 'w') as file:
            json.dump(token_data, file)
    except Exception as exc:
        print(f"{RED}Error storing token: {exc}{RESET}")
    
async def request_token(c_id, c_secret):
    # Attempt to load previously generated token
    token, expiry = load_token()    
    
    if token and expiry:
        print(f"{LIGHT_BLUE}Passing on previously generated token\nThis token will expire at {expiry}{RESET}")
        return token, 200, None
    
    print("No token previously generated. Proceed to generation...")
    token, expiry, response_code, response_msg = await spotifyapi.generate_token(c_id, c_secret)
    if token and response_code == 200:
        store_token(token, expiry)
    return token, response_code, response_msg