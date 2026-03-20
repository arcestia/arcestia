import json
import os
import re
import time
import urllib.request

# Retrieve Keys from Environment Variables
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def load_json(file_path):
    """Load JSON file safely."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return {}


def save_json(file_path, data):
    """Save JSON file safely."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {file_path}: {e}")


def get_github_followers(username, cache):
    """Fetch GitHub follower count using public API."""
    url = f"https://api.github.com/users/{username}"
    headers = {"User-Agent": "Mozilla/5.0"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("followers", 0)
    except Exception as e:
        print(f"Error fetching GitHub followers for {username}: {e}")
    return cache.get("github", 0)


def get_github_sponsors(username, cache):
    """Fetch GitHub sponsors count using GraphQL API."""
    if not GITHUB_TOKEN:
        return 0

    url = "https://api.github.com/graphql"
    query = (
        """
    query {
      user(login: "%s") {
        sponsors {
          totalCount
        }
      }
    }
    """
        % username
    )

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    data = json.dumps({"query": query}).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            return (
                res_data.get("data", {})
                .get("user", {})
                .get("sponsors", {})
                .get("totalCount", 0)
            )
    except Exception as e:
        print(f"Error fetching GitHub sponsors for {username}: {e}")
        return cache.get("sponsors", 0)


def get_bluesky_followers(handle, cache):
    """Fetch Bluesky follower count using public API."""
    url = f"https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={handle}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("followersCount", 0)
    except Exception as e:
        print(f"Error fetching Bluesky followers for {handle}: {e}")
    return cache.get("bluesky", 0)


def get_x_followers(username, cache):
    """Fetch X followers using a third-party RapidAPI service."""
    if not RAPIDAPI_KEY:
        return 0

    url = f"https://twitter241.p.rapidapi.com/user?username={username}"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "twitter241.p.rapidapi.com",
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            user_data = (
                data.get("result", {})
                .get("data", {})
                .get("user", {})
                .get("result", {})
                .get("legacy", {})
            )
            return user_data.get("followers_count", 0)
    except Exception as e:
        print(f"Error fetching X followers: {e}")
    return cache.get("x", 0)


def get_soundcloud_followers(url, cache):
    """Fetch SoundCloud follower count using RapidAPI."""
    if not RAPIDAPI_KEY:
        return 0

    import urllib.parse

    encoded_url = urllib.parse.quote(url, safe="")
    api_url = (
        f"https://soundcloud-scraper.p.rapidapi.com/v1/user/profile?user={encoded_url}"
    )
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "soundcloud-scraper.p.rapidapi.com",
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("followerCount", 0)
    except Exception as e:
        print(f"Error fetching SoundCloud followers: {e}")
    return cache.get("soundcloud", 0)


def get_youtube_subscribers(handle, cache):
    """Fetch YouTube subscriber count using RapidAPI."""
    if not RAPIDAPI_KEY:
        return 0

    # Ensure handle starts with @ for the API
    if not handle.startswith("@"):
        handle = f"@{handle}"

    import urllib.parse

    encoded_handle = urllib.parse.quote(handle, safe="")
    api_url = f"https://youtube138.p.rapidapi.com/channel/details/?id={encoded_handle}&hl=en&gl=US"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "youtube138.p.rapidapi.com",
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("stats", {}).get("subscribers", 0)
    except Exception as e:
        print(f"Error fetching YouTube subscribers: {e}")
    return cache.get("youtube", 0)


def get_instagram_followers(username, cache, cache_key):
    """Fetch Instagram followers using a third-party RapidAPI service."""
    if not RAPIDAPI_KEY:
        return 0

    url = "https://instagram120.p.rapidapi.com/api/instagram/profile"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "instagram120.p.rapidapi.com",
        "Content-Type": "application/json",
    }
    post_data = json.dumps({"username": username}).encode("utf-8")

    try:
        req = urllib.request.Request(
            url, data=post_data, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("result", {}).get("edge_followed_by", {}).get("count", 0)
    except Exception as e:
        print(f"Error fetching Instagram followers for {username}: {e}")
    return cache.get(cache_key, 0)


def format_count(count):
    """Format large numbers for badges (e.g. 1500 -> 1.5k)."""
    try:
        num = int(count)
        if num >= 1000000:
            return f"{num / 1000000:.1f}M".replace(".0", "")
        if num >= 1000:
            return f"{num / 1000:.1f}k".replace(".0", "")
        return str(num)
    except (ValueError, TypeError):
        return str(count) if count else "0"


def update_readme(stats):
    """Update README.md with content generated from stats and social.json config."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(base_dir, "README.md")
    config_path = os.path.join(base_dir, ".github", "config", "social.json")

    config = load_json(config_path)
    if not config:
        print("Error: Could not load social.json config")
        return

    platforms = config.get("platforms", {})
    settings = config.get("settings", {})
    style = settings.get("style", "flat-square")
    use_matching_labels = settings.get("use_matching_labels", True)
    total_color = settings.get("total_color", "8A2BE2")

    total_followers = sum(stats.values())
    badges = []

    # Website badge (static, no count)
    web = platforms.get("website", {})
    web_color = web.get("color", "grey")
    web_label_color = f"&labelColor={web_color}" if use_matching_labels else ""
    badges.append(
        f'<a href="{web.get("url")}"><img src="https://img.shields.io/badge/{web.get("name")}-{web_color}?style={style}&logo={web.get("logo")}&logoColor=white{web_label_color}" alt="Website"></a>'
    )

    # Platform badges
    order = [
        "github",
        "sponsors",
        "bluesky",
        "x",
        "instagram",
        "instagram_lab",
        "youtube",
        "soundcloud",
    ]
    for key in order:
        p = platforms.get(key)
        if not p:
            continue

        count = stats.get(key, 0)
        formatted = format_count(count)
        color = p.get("color", "grey")
        label_color = f"&labelColor={color}" if use_matching_labels else ""

        if key == "github":
            img_url = f"https://img.shields.io/github/followers/{p.get('handle')}?label=GitHub&style={style}&logo=github&color={color}{label_color}"
        else:
            label = (
                f"@{p.get('handle')}"
                if "handle" in p and key not in ["sponsors"]
                else p.get("name")
            )
            img_url = f"https://img.shields.io/badge/{label.replace('-', '--')}-{formatted}-{color}?style={style}&logo={p.get('logo')}&logoColor=white{label_color}"

        badges.append(
            f'<a href="{p.get("url")}"><img src="{img_url}" alt="{p.get("name")}"></a>'
        )

    # Total badge
    total_label_color = f"&labelColor={total_color}" if use_matching_labels else ""
    badges.append(
        f'<img src="https://img.shields.io/badge/Total_Followers-{format_count(total_followers)}-{total_color}?style={style}{total_label_color}" alt="Total Followers">'
    )

    new_stats_html = f"{badges[0]}\n  {' '.join(badges[1:])}"

    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r"<!-- SOCIAL-STATS:START -->.*?<!-- SOCIAL-STATS:END -->"
        replacement = f"<!-- SOCIAL-STATS:START -->\n  {new_stats_html}\n  <!-- SOCIAL-STATS:END -->"

        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"Successfully updated social stats in README.md")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, ".github", "config", "social.json")
    cache_path = os.path.join(base_dir, ".github", "config", "stats_cache.json")

    config = load_json(config_path)
    cache_data = load_json(cache_path)

    # Cache expiration logic (24 hours = 86400 seconds)
    last_update = cache_data.get("last_updated_at", 0)
    current_time = time.time()
    cache = cache_data.get("stats", {})

    if config:
        platforms = config.get("platforms", {})
        stats = {}

        # Only fetch new stats if 24 hours have passed or cache is empty
        if current_time - last_update > 86400 or not cache:
            print("Cache expired or empty. Fetching fresh stats...")

            print("Fetching GitHub followers...")
            stats["github"] = get_github_followers(
                platforms.get("github", {}).get("handle", "arcestia"), cache
            )

            print("Fetching GitHub sponsors...")
            stats["sponsors"] = get_github_sponsors(
                platforms.get("sponsors", {}).get("handle", "arcestia"), cache
            )

            print("Fetching Bluesky followers...")
            stats["bluesky"] = get_bluesky_followers(
                platforms.get("bluesky", {}).get("handle", "skiddle.blue"), cache
            )

            print("Fetching X followers...")
            stats["x"] = get_x_followers(
                platforms.get("x", {}).get("handle", "skiddleid"), cache
            )

            print("Fetching Instagram followers (skiddle.id)...")
            stats["instagram"] = get_instagram_followers(
                platforms.get("instagram", {}).get("handle", "skiddle.id"),
                cache,
                "instagram",
            )

            print("Fetching Instagram followers (skiddleton)...")
            stats["instagram_lab"] = get_instagram_followers(
                platforms.get("instagram_lab", {}).get("handle", "skiddleton"),
                cache,
                "instagram_lab",
            )

            print("Fetching YouTube subscribers...")
            stats["youtube"] = get_youtube_subscribers(
                platforms.get("youtube", {}).get("handle", "SkiddleID"), cache
            )

            print("Fetching SoundCloud followers...")
            stats["soundcloud"] = get_soundcloud_followers(
                platforms.get("soundcloud", {}).get(
                    "url", "https://soundcloud.com/arcestiaishere"
                ),
                cache,
            )

            # Update cache with new timestamp
            save_json(cache_path, {"last_updated_at": current_time, "stats": stats})
        else:
            print(
                f"Using cached stats (Last updated {int((current_time - last_update) / 3600)}h ago)"
            )
            stats = cache

        update_readme(stats)
