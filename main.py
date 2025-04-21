from flask import Flask, request, Response
import instaloader
import json

app = Flask(__name__)

def fetch_instagram_profile(username):
    loader = instaloader.Instaloader()
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

@app.route('/')
def get_instagram_data():
    username = request.args.get('username')
    if not username:
        return Response(json.dumps({"error": "username parameter is required"}, indent=4), mimetype='application/json')

    data = fetch_instagram_profile(username)
    return Response(json.dumps(data, indent=4, ensure_ascii=False), mimetype='application/json')

if __name__ == '__main__':
    app.run(port=8000)