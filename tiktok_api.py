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

def initialize_upload(video_size, chunk_size, total_chunk_count):
    """Step 1: Initialize the upload to TikTok Inbox."""
    headers = get_headers()
    if not headers:
        return {"error": "No token found"}
    
    url = f"{BASE_URL}/post/publish/inbox/video/init/"
    body = {
        "source": "FILE_UPLOAD",
        "video_size": video_size,
        "chunk_size": chunk_size,
        "total_chunk_count": total_chunk_count
    }
    
    response = requests.post(url, headers=headers, json=body)
    return response.json()

def upload_chunk(upload_url, chunk_data, upload_id, chunk_index, total_video_size):
    """Step 2: Upload a single chunk to the provided TikTok upload URL."""
    headers = {
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes {chunk_index * len(chunk_data)}-{chunk_index * len(chunk_data) + len(chunk_data) - 1}/{total_video_size}"
    }
    # Note: TikTok documentation says to use PUT for chunks and specific headers
    # Some docs say x-upload-id, others say Content-Range. Content-Range is standard for chunked.
    # Let's use the headers TikTok specifically asks for.
    headers = {
        "Content-Type": "video/mp4",
        "Content-Length": str(len(chunk_data)),
    }
    
    response = requests.put(upload_url, headers=headers, data=chunk_data)
    return response

def upload_video_file(file_path):
    """Complete workflow: Post a video to TikTok Inbox."""
    if not os.path.exists(file_path):
        return {"error": "File not found"}
        
    video_size = os.path.getsize(file_path)
    # 5MB chunks (5 * 1024 * 1024)
    chunk_size = 5242880 
    total_chunk_count = (video_size + chunk_size - 1) // chunk_size
    
    print(f"Initializing upload for {file_path} ({video_size} bytes)...")
    init_res = initialize_upload(video_size, chunk_size, total_chunk_count)
    
    if "error" in init_res and init_res["error"].get("code") != "ok":
        return init_res
        
    data = init_res.get("data", {})
    upload_url = data.get("upload_url")
    
    if not upload_url:
        return {"error": "No upload URL received", "response": init_res}
        
    print(f"Uploading {total_chunk_count} chunks...")
    with open(file_path, "rb") as f:
        for i in range(total_chunk_count):
            chunk = f.read(chunk_size)
            print(f"  Uploading chunk {i+1}/{total_chunk_count}...")
            res = upload_chunk(upload_url, chunk, None, i, video_size)
            if res.status_code not in [200, 201, 206]:
                return {"error": f"Chunk {i} failed", "status": res.status_code, "body": res.text}
                
    return {"status": "success", "message": "Video sent to TikTok Inbox! Check your app to finish posting."}

if __name__ == "__main__":
    # Quick test
    print("=== User Info ===")
    user = get_user_info()
    print(json.dumps(user, indent=2))
    
    print("\n=== Video List ===")
    videos = get_video_list()
    print(json.dumps(videos, indent=2))
