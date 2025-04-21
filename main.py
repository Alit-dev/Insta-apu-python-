from flask import Flask, request, Response
import instaloader
import requests
import json
import random

app = Flask(__name__)

def get_free_proxy():
    try:
        response = requests.get("https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt")
        if response.status_code == 200:
            proxies = response.text.splitlines()
            if proxies:
                proxy = random.choice(proxies)
                return f"http://{proxy}"
    except Exception as e:
        print("Error fetching proxy:", e)
    return None

def fetch_instagram_profile(username):
    proxy = get_free_proxy()
    if not proxy:
        return {"error": "Couldn't fetch a working proxy."}

    loader = instaloader.Instaloader()
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
    except Exception as e:
        return {"error": str(e)}

@app.route('/', methods=['GET'])
def root_query():
    username = request.args.get('username')
    if not username:
        return Response(json.dumps({"error": "username parameter is required"}, indent=4), mimetype='application/json')

    data = fetch_instagram_profile(username)
    return Response(json.dumps(data, indent=4, ensure_ascii=False), mimetype='application/json')

if __name__ == '__main__':
    app.run(port=8000)