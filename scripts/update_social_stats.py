import json
import os
import re
import urllib.request

# Retrieve Keys from Environment Variables
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def load_config(file_path):
    """Load JSON configuration file."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_github_followers(username):
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
    return 0


def get_github_sponsors(username):
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
        return 0


def get_bluesky_followers(handle):
    """Fetch Bluesky follower count using public API."""
    url = f"https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={handle}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("followersCount", 0)
    except Exception as e:
        print(f"Error fetching Bluesky followers for {handle}: {e}")
    return 0


def get_x_followers(username):
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
    return 0


def get_instagram_followers(username):
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
        print(f"Error fetching Instagram followers: {e}")
    return 0


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

    config = load_config(config_path)
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
    order = ["github", "sponsors", "bluesky", "x", "instagram", "instagram_lab"]
    for key in order:
        p = platforms.get(key)
        if not p:
            continue

        count = stats.get(key, 0)
        formatted = format_count(count)
        color = p.get("color", "grey")
        label_color = f"&labelColor={color}" if use_matching_labels else ""

        # GitHub uses a specific shields.io endpoint for followers, others use generic badges
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

    # Construct the final row
    # Website on its own line, others in a row
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
    config = load_config(config_path)

    if config:
        platforms = config.get("platforms", {})
        stats = {
            "github": get_github_followers(
                platforms.get("github", {}).get("handle", "arcestia")
            ),
            "sponsors": get_github_sponsors(
                platforms.get("sponsors", {}).get("handle", "arcestia")
            ),
            "bluesky": get_bluesky_followers(
                platforms.get("bluesky", {}).get("handle", "skiddle.blue")
            ),
            "x": get_x_followers(platforms.get("x", {}).get("handle", "skiddleid")),
            "instagram": get_instagram_followers(
                platforms.get("instagram", {}).get("handle", "skiddle.id")
            ),
            "instagram_lab": get_instagram_followers(
                platforms.get("instagram_lab", {}).get("handle", "skiddleton")
            ),
        }
        update_readme(stats)
