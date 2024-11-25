import os, json, time
from wrapper import apiwrapper as spotifyapi
from datetime import datetime

#TERMINAL COLOR CODE
RED, GREEN, LIGHT_BLUE, RESET = "\033[91m", "\033[92m", "\033[94m", "\033[0m" 

def load_token():
    """
    Loads the Spotify API access token from a file and checks its validity.

    Returns:
        tuple: (access_token, expiry_time) if the token is valid, otherwise (None, None).
    """
    file_path = os.path.join(os.path.dirname(__file__), 'accesstoken.json')
    
    try:
        with open(file_path, 'r') as file:
            saved_token = json.load(file)
            access_token = saved_token.get("access_token")
            expires_at = saved_token.get("expires_at")
            
            if access_token and expires_at:
                current_time = int(time.time())
                # Return token if it hasn't expired (30-second buffer)
                if current_time < (expires_at - 30):
                    expiry_time = datetime.fromtimestamp(expires_at).strftime("%d-%m-%y %H:%M:%S")
                    return access_token, expiry_time
    except FileNotFoundError:
        print(f"{RED}Token file not found. Generating a new token...{RESET}")
    except json.JSONDecodeError:
        print(f"{RED}Error decoding token file. Proceeding with token generation...{RESET}")
    except Exception as exc:
        print(f"{RED}Unexpected error while loading token: {exc}{RESET}")
    
    return None, None

def store_token(token, expires_at):
    """
    Stores the Spotify API access token in a file.

    Args:
        token (str): The access token to store.
        expires_at (int): The token expiration timestamp.
    """
    file_path = os.path.join(os.path.dirname(__file__), 'accesstoken.json')
    token_data = {
        'access_token': token,
        'expires_at': expires_at
    }
    try:
        with open(file_path, 'w') as file:
            json.dump(token_data, file)
        print(f"{GREEN}Token successfully stored. Expires at {datetime.fromtimestamp(expires_at).strftime('%d-%m-%y %H:%M:%S')}{RESET}")
    except Exception as exc:
        print(f"{RED}Error storing token: {exc}{RESET}")

async def request_token(c_id, c_secret):
    """
    Requests a new Spotify API token if no valid token exists.

    Args:
        c_id (str): The client ID for Spotify API.
        c_secret (str): The client secret for Spotify API.

    Returns:
        tuple: (access_token, response_code, response_message).
    """
    # Check for a previously stored token
    token, expiry = load_token()
    if token and expiry:
        print(f"{LIGHT_BLUE}Using previously generated token. Expires at: {expiry}{RESET}")
        return token, 200, None

    # Generate a new token
    print(f"{LIGHT_BLUE}No valid token found. Generating a new token...{RESET}")
    try:
        token, expiry, response_code, response_msg = await spotifyapi.generate_token(c_id, c_secret)
        if token and response_code == 200:
            store_token(token, expiry)
        return token, response_code, response_msg
    except Exception as exc:
        print(f"{RED}Unexpected error during token request: {exc}{RESET}")
        return None, 500, f"Error during token request: {exc}"
