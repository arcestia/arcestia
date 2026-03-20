import json
import os
import re
import urllib.request

# Retrieve Keys from Environment Variables
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def get_github_followers(username):
    """Fetch GitHub follower count using public API."""
    url = f"https://api.github.com/users/{username}"
    headers = {"User-Agent": "Mozilla/5.0"}

    # Use token if available to prevent GitHub API rate limits
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
        print("Note: GITHUB_TOKEN not found. Defaulting to 0 for GitHub Sponsors.")
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
        # POST request required for GraphQL
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
        print("Note: RAPIDAPI_KEY not found. Defaulting to 0 for X.")
        return 0

    # Updated to use twitter241.p.rapidapi.com as provided
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
            # Navigating the nested response: result -> data -> user -> result -> legacy -> followers_count
            user_data = (
                data.get("result", {})
                .get("data", {})
                .get("user", {})
                .get("result", {})
                .get("legacy", {})
            )
            return user_data.get("followers_count", 0)
    except Exception as e:
        print(f"Error fetching X followers via RapidAPI: {e}")
        return 0


def get_instagram_followers(username):
    """Fetch Instagram followers using a third-party RapidAPI service."""
    if not RAPIDAPI_KEY:
        print("Note: RAPIDAPI_KEY not found. Defaulting to 0 for Instagram.")
        return 0

    # Updated to use instagram120.p.rapidapi.com as provided
    url = "https://instagram120.p.rapidapi.com/api/instagram/profile"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "instagram120.p.rapidapi.com",
        "Content-Type": "application/json",
    }
    # This endpoint requires a POST request with the username in JSON format
    post_data = json.dumps({"username": username}).encode("utf-8")

    try:
        req = urllib.request.Request(
            url, data=post_data, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            # Navigating the response: result -> edge_followed_by -> count
            return data.get("result", {}).get("edge_followed_by", {}).get("count", 0)
    except Exception as e:
        print(f"Error fetching Instagram followers via RapidAPI: {e}")
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


def update_readme(
    gh_count, bsky_count, x_count, ig_count, ig_lab_count, gh_sponsors_count
):
    """Update README.md with individual follower counts and a total sum."""
    total = (
        gh_count + bsky_count + x_count + ig_count + ig_lab_count + gh_sponsors_count
    )

    # Determine README path
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")

    if not os.path.exists(readme_path):
        print(f"Error: Could not find {readme_path}")
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Create dynamic badges with current counts and usernames for consistency
    gh_badge = f"https://img.shields.io/github/followers/arcestia?label=GitHub&style=for-the-badge&logo=github&color=181717"
    bsky_badge = f"https://img.shields.io/bluesky/followers/skiddle.blue?label=%40skiddle.blue&style=for-the-badge&logo=bluesky&color=0285FF"
    x_badge = f"https://img.shields.io/badge/%40skiddleid-{format_count(x_count)}-000000?style=for-the-badge&logo=X&logoColor=white"
    ig_badge = f"https://img.shields.io/badge/%40skiddle.id-{format_count(ig_count)}-E4405F?style=for-the-badge&logo=Instagram&logoColor=white"
    ig_lab_badge = f"https://img.shields.io/badge/%40skiddleton-{format_count(ig_lab_count)}-E4405F?style=for-the-badge&logo=Instagram&logoColor=white"
    sponsors_badge = f"https://img.shields.io/badge/Sponsors-{format_count(gh_sponsors_count)}-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white"

    new_stats = (
        f'  <a href="https://skiddle.id"><img src="https://img.shields.io/badge/Website-121011?style=for-the-badge&logo=google-chrome&logoColor=white" alt="Website"></a>\n'
        f'  <a href="https://github.com/arcestia"><img src="{gh_badge}" alt="GitHub"></a>\n'
        f'  <a href="https://github.com/sponsors/arcestia"><img src="{sponsors_badge}" alt="GitHub Sponsors"></a>\n'
        f'  <a href="https://bsky.app/profile/skiddle.blue"><img src="{bsky_badge}" alt="Bluesky"></a>\n'
        f'  <a href="https://x.com/skiddleid"><img src="{x_badge}" alt="X"></a>\n'
        f'  <a href="https://instagram.com/skiddle.id"><img src="{ig_badge}" alt="Instagram"></a>\n'
        f'  <a href="https://instagram.com/skiddleton"><img src="{ig_lab_badge}" alt="Skiddleton"></a>\n'
        f"  <br>\n"
        f'  <img src="https://img.shields.io/badge/Total_Followers-{format_count(total)}-blue?style=for-the-badge" alt="Total Followers">'
    )

    # Use regex to replace content between the markers
    pattern = r"<!-- SOCIAL-STATS:START -->.*?<!-- SOCIAL-STATS:END -->"
    replacement = (
        f"<!-- SOCIAL-STATS:START -->\n{new_stats}\n  <!-- SOCIAL-STATS:END -->"
    )

    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print(
        f"Updated README.md. Stats: GH={gh_count}, Sponsors={gh_sponsors_count}, BS={bsky_count}, X={x_count}, IG={ig_count}, IG_Lab={ig_lab_count}, Total={total}"
    )


if __name__ == "__main__":
    # Fetch automated counts
    gh_followers = get_github_followers("arcestia")
    gh_sponsors = get_github_sponsors("arcestia")
    bsky_followers = get_bluesky_followers("skiddle.blue")

    # Fetch X and Instagram counts via RapidAPI
    x_followers = get_x_followers("skiddleid")
    ig_followers = get_instagram_followers("skiddle.id")
    ig_lab_followers = get_instagram_followers("skiddleton")

    update_readme(
        gh_followers,
        bsky_followers,
        x_followers,
        ig_followers,
        ig_lab_followers,
        gh_sponsors,
    )
