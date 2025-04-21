from flask import Flask, request, Response
import instaloader
import requests
import json
import random
import logging
import os
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variable for proxy service (optional, replace with your paid proxy provider)
PROXY_API_URL = os.getenv("PROXY_API_URL", None)  # e.g., "https://api.proxyprovider.com/get_proxy"
PROXY_LIST_URL = "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"

def get_proxy():
    """
    Fetch a new proxy for each request, prioritizing paid proxy service if configured,
    else fall back to free proxy list.
    """
    try:
        if PROXY_API_URL:
            # Fetch proxy from a paid service (replace with your provider's API)
            response = requests.get(PROXY_API_URL)
            if response.status_code == 200:
                proxy_data = response.json()
                proxy = proxy_data.get("proxy", None)
                if proxy:
                    logger.info(f"Using paid proxy: {proxy}")
                    return f"http://{proxy}"
        # Fallback to free proxy list
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))
        
        response = session.get(PROXY_LIST_URL, timeout=10)
        if response.status_code == 200:
            proxies = response.text.splitlines()
            if proxies:
                proxy = random.choice(proxies)
                logger.info(f"Using free proxy: {proxy}")
                return f"http://{proxy}"
    except Exception as e:
        logger.error(f"Error fetching proxy: {e}")
    return None

def fetch_instagram_profile(username):
    """
    Fetch Instagram profile data using instaloader with a new proxy for each request.
    No caching to ensure fresh proxy usage.
    """
    proxy = get_proxy()
    if not proxy:
        logger.error("No working proxy available.")
        return {"error": "Couldn't fetch a working proxy."}

    loader = instaloader.Instaloader(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        sleep=True,  # Add delays to mimic human behavior
        quiet=True
    )

    # Configure proxy
    loader.context._session.proxies = {
        'http': proxy,
        'https': proxy,
    }

    try:
        profile = instaloader.Profile.from_username(loader.context, username)
        return {
            "username": profile.username,
            "full_name": profile.full_name,
            "bio": profile.biography,
            "external_url": profile.external_url,
            "followers": profile.followers,
            "following": profile.followees,
            "posts": profile.mediacount,
            "igtv_videos": profile.igtvcount,
            "is_verified": profile.is_verified,
            "is_private": profile.is_private,
            "profile_pic": profile.profile_pic_url,
            "business_category": profile.business_category_name
        }
    except instaloader.exceptions.ProfileNotExistsException:
        logger.error(f"Profile {username} does not exist.")
        return {"error": f"Profile {username} does not exist."}
    except instaloader.exceptions.ConnectionException as e:
        logger.error(f"Connection error for {username}: {e}")
        return {"error": "Connection error, possibly blocked by Instagram."}
    except Exception as e:
        logger.error(f"Unexpected error for {username}: {e}")
        return {"error": str(e)}

@app.route('/', methods=['GET'])
def root_query():
    """
    Handle GET requests to fetch Instagram profile data with a new proxy on each request.
    """
    username = request.args.get('username')
    if not username:
        logger.warning("Request received without username parameter.")
        return Response(
            json.dumps({"error": "username parameter is required"}, indent=4),
            mimetype='application/json',
            status=400
        )

    data = fetch_instagram_profile(username)
    status = 200 if "error" not in data else 500
    return Response(
        json.dumps(data, indent=4, ensure_ascii=False),
        mimetype='application/json',
        status=status
    )

if __name__ == '__main__':
    # Bind to 0.0.0.0 and port from environment (required for Render)
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)