import requests
import json
import os
from datetime import datetime

TOKEN_FILE = "token.json"
FOLLOWER_HISTORY_FILE = "follower_history.json"
BASE_URL = "https://open.tiktokapis.com/v2"

def load_token():
    """Load saved access token from file."""
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def get_headers():
    """Build authorization headers."""
    token_data = load_token()
    if not token_data:
        return None
    return {
        "Authorization": f"Bearer {token_data['access_token']}",
        "Content-Type": "application/json"
    }

def get_user_info():
    """Fetch basic user profile info with fallback for sandbox."""
    headers = get_headers()
    if not headers:
        return {"error": "No token found"}
    
    url = f"{BASE_URL}/user/info/"
    
    # Try full fields first
    full_fields = "open_id,union_id,avatar_url,display_name,bio_description,profile_deep_link,is_verified,follower_count,following_count,likes_count,video_count"
    # Minimal fields for sandbox
    minimal_fields = "open_id,avatar_url,display_name"
    
    response = requests.get(url, headers=headers, params={"fields": full_fields})
    result = response.json()
    
    # If scope error, try with minimal fields
    if "error" in result and result["error"].get("code") == "scope_not_authorized":
        print("Full user info not available, trying minimal fields...")
        response = requests.get(url, headers=headers, params={"fields": minimal_fields})
        result = response.json()
    
    return result

def get_video_list(cursor=0, max_count=20):
    """Fetch list of user's videos with metadata."""
    headers = get_headers()
    if not headers:
        return {"error": "No token found"}
    
    url = f"{BASE_URL}/video/list/"
    
    # Fields confirmed to work — favourite_count is NOT available in sandbox
    fields = "id,title,video_description,duration,cover_image_url,share_url,view_count,like_count,comment_count,share_count,create_time"
    
    body = {
        "max_count": max_count,
        "cursor": cursor
    }
    
    response = requests.post(url, headers=headers, params={"fields": fields}, json=body)
    return response.json()

def track_followers(current_count):
    """Record follower count with timestamp for growth tracking."""
    history = load_follower_history()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Only add one entry per hour to avoid excessive data
    if history:
        last_entry_time = history[-1].get("time", "")
        # If we already have an entry for this hour, update it instead
        current_hour = datetime.now().strftime("%Y-%m-%d %H")
        last_hour = last_entry_time[:13] if len(last_entry_time) >= 13 else ""
        if current_hour == last_hour:
            history[-1]["count"] = current_count
            history[-1]["time"] = now
        else:
            history.append({"time": now, "date": today, "count": current_count})
    else:
        history.append({"time": now, "date": today, "count": current_count})
    
    # Keep last 365 entries max
    if len(history) > 365:
        history = history[-365:]
    
    with open(FOLLOWER_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    
    return history

def load_follower_history():
    """Load follower growth history."""
    if not os.path.exists(FOLLOWER_HISTORY_FILE):
        return []
    with open(FOLLOWER_HISTORY_FILE, "r") as f:
        return json.load(f)

def get_follower_growth():
    """Calculate follower growth stats from history."""
    history = load_follower_history()
    if not history or len(history) < 2:
        return {
            "history": history,
            "growth_today": 0,
            "growth_week": 0,
            "growth_month": 0
        }
    
    current = history[-1]["count"]
    
    # Find entry from ~24h ago, ~7 days ago, ~30 days ago
    growth_today = 0
    growth_week = 0
    growth_month = 0
    
    for entry in reversed(history):
        entry_date = entry.get("date", "")
        days_ago = (datetime.now() - datetime.strptime(entry_date, "%Y-%m-%d")).days if entry_date else 0
        
        if days_ago >= 1 and growth_today == 0:
            growth_today = current - entry["count"]
        if days_ago >= 7 and growth_week == 0:
            growth_week = current - entry["count"]
        if days_ago >= 30 and growth_month == 0:
            growth_month = current - entry["count"]
    
    return {
        "history": history,
        "growth_today": growth_today,
        "growth_week": growth_week,
        "growth_month": growth_month
    }

def get_all_data():
    """Get combined user info + video list + follower growth for the dashboard."""
    user_info = get_user_info()
    video_list = get_video_list()
    
    # Track follower count if we got valid user data
    follower_growth = {}
    if user_info and "data" in user_info:
        user_data = user_info.get("data", {}).get("user", {})
        follower_count = user_data.get("follower_count", 0)
        if follower_count:
            track_followers(follower_count)
        follower_growth = get_follower_growth()
    
    return {
        "user": user_info,
        "videos": video_list,
        "follower_growth": follower_growth
    }

if __name__ == "__main__":
    # Quick test
    print("=== User Info ===")
    user = get_user_info()
    print(json.dumps(user, indent=2))
    
    print("\n=== Video List ===")
    videos = get_video_list()
    print(json.dumps(videos, indent=2))
