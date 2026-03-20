import json
import os
import re
import urllib.request

# Retrieve Keys from Environment Variables
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# Badge Color Configuration (Hex or standard color names)
BADGE_COLORS = {
    "website": "FF5733",  # Sunset Orange
    "github": "6cc644",  # GitHub Green
    "sponsors": "EA4AAA",  # Pink
    "bluesky": "00acee",  # Sky Blue
    "x": "000000",  # Black
    "instagram": "C13584",  # Purple/Magenta
    "total": "8A2BE2",  # Violet
}


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
        print(f"Error fetching X followers via RapidAPI: {e}")
        return 0


def get_instagram_followers(username):
    """Fetch Instagram followers using a third-party RapidAPI service."""
    if not RAPIDAPI_KEY:
        print("Note: RAPIDAPI_KEY not found. Defaulting to 0 for Instagram.")
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

    # Create dynamic badges with matching label and value colors for a fully colorful look (using flat-square style)
    website_badge = f"https://img.shields.io/badge/Website-{BADGE_COLORS['website']}?style=flat-square&logo=google-chrome&logoColor=white&labelColor={BADGE_COLORS['website']}"
    gh_badge = f"https://img.shields.io/github/followers/arcestia?label=GitHub&style=flat-square&logo=github&color={BADGE_COLORS['github']}&labelColor={BADGE_COLORS['github']}"
    sponsors_badge = f"https://img.shields.io/badge/Sponsors-{format_count(gh_sponsors_count)}-{BADGE_COLORS['sponsors']}?style=flat-square&logo=githubsponsors&logoColor=white&labelColor={BADGE_COLORS['sponsors']}"
    bsky_badge = f"https://img.shields.io/bluesky/followers/skiddle.blue?label=%40skiddle.blue&style=flat-square&logo=bluesky&color={BADGE_COLORS['bluesky']}&labelColor={BADGE_COLORS['bluesky']}"
    x_badge = f"https://img.shields.io/badge/%40skiddleid-{format_count(x_count)}-{BADGE_COLORS['x']}?style=flat-square&logo=X&logoColor=white&labelColor={BADGE_COLORS['x']}"
    ig_badge = f"https://img.shields.io/badge/%40skiddle.id-{format_count(ig_count)}-{BADGE_COLORS['instagram']}?style=flat-square&logo=Instagram&logoColor=white&labelColor={BADGE_COLORS['instagram']}"
    ig_lab_badge = f"https://img.shields.io/badge/%40skiddleton-{format_count(ig_lab_count)}-{BADGE_COLORS['instagram']}?style=flat-square&logo=Instagram&logoColor=white&labelColor={BADGE_COLORS['instagram']}"
    total_badge = f"https://img.shields.io/badge/Total_Followers-{format_count(total)}-{BADGE_COLORS['total']}?style=flat-square&labelColor={BADGE_COLORS['total']}"

    new_stats = (
        f'  <a href="https://skiddle.id"><img src="{website_badge}" alt="Website"></a>\n'
        f'  <a href="https://github.com/arcestia"><img src="{gh_badge}" alt="GitHub"></a> '
        f'  <a href="https://github.com/sponsors/arcestia"><img src="{sponsors_badge}" alt="GitHub Sponsors"></a> '
        f'  <a href="https://bsky.app/profile/skiddle.blue"><img src="{bsky_badge}" alt="Bluesky"></a> '
        f'  <a href="https://x.com/skiddleid"><img src="{x_badge}" alt="X"></a> '
        f'  <a href="https://instagram.com/skiddle.id"><img src="{ig_badge}" alt="Instagram"></a> '
        f'  <a href="https://instagram.com/skiddleton"><img src="{ig_lab_badge}" alt="Skiddleton"></a> '
        f'  <img src="{total_badge}" alt="Total Followers">'
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
