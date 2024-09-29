import aiohttp, time

web_endpoint = "https://api.spotify.com"
auth_endpoint = "https://accounts.spotify.com/api/token"

#API Req #1: Generate Token
async def generate_token(c_id, c_secret):
    global auth_endpoint
    #Set Parameters
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': c_id,
        'client_secret': c_secret
    }
    #Send token geneeration request
    try: 
        print(f"Requesting token from {auth_endpoint}...")
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_endpoint, headers = headers, data = data) as response:
                if response.status == 200:
                    r = await response.json()
                    token = r['access_token']
                    expiry = int(time.time()) + r['expires_in']
                    return token, expiry, response.status, None

                error = await response.text()
                print(f"API Request Failed. See Spotify API reference page for details.")
                return None, None, response.status, error
    except aiohttp.ClientError as clienterror:
        print(f"Encountered Client Side Error: {clienterror}")
        return None, None, 500, str(clienterror)
    
    except Exception as e:
        print(f"Encountered Unexpected Error: {e}")
        return None, None, response.status, str(e)

#API Req #2: Get Artist
async def request_artist_info(artisturi, token):
    global web_endpoint
    url = f"{web_endpoint}/v1/artists/{artisturi}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data, response.status
            return None, response.status

#API Req #3: Get Artist Top Track