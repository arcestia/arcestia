import json
import os
import re
import time
import urllib.parse
import urllib.request

# Retrieve Keys from Environment Variables
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
WHATPULSE_API_TOKEN = os.environ.get("WHATPULSE_API_TOKEN")


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
    """Fetch GitHub sponsors count using GraphQL API with fallback."""
    if not GITHUB_TOKEN:
        return 0

    url = "https://api.github.com/graphql"

    def fetch_sponsors(include_private=True):
        priv_str = "(includePrivate: true)" if include_private else ""
        query = """
        query {
          user(login: "%s") {
            sponsorshipsAsMaintainer%s {
              totalCount
            }
            sponsorshipsAsSponsor {
              totalCount
            }
          }
        }
        """ % (
            username,
            priv_str,
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
                res_content = response.read().decode()
                print(f"DEBUG: GraphQL Response: {res_content}")
                return json.loads(res_content)
        except Exception as e:
            print(f"GraphQL request error: {e}")
            if hasattr(e, "read"):
                print(f"DEBUG: Error body: {e.read().decode()}")
            return None

    # Try with private sponsors first
    res_data = fetch_sponsors(include_private=True)

    # If it failed or returned errors (common if token lacks scope for includePrivate)
    if not res_data or "errors" in res_data:
        if res_data and "errors" in res_data:
            print(
                f"DEBUG: Token likely missing 'read:user' scope or incorrect permissions."
            )
            print(f"GraphQL Error (Private): {res_data['errors'][0].get('message')}")

        print("Falling back to public-only sponsors...")
        res_data = fetch_sponsors(include_private=False)

    if not res_data or "errors" in res_data:
        if res_data and "errors" in res_data:
            print(f"GraphQL Error (Public): {res_data['errors'][0].get('message')}")
        return cache.get("sponsors", 0)

    user_data = res_data.get("data", {}).get("user", {})
    sponsors_count = user_data.get("sponsorshipsAsMaintainer", {}).get("totalCount", 0)
    sponsoring_count = user_data.get("sponsorshipsAsSponsor", {}).get("totalCount", 0)

    # Store counts in cache for reference
    cache["sponsors"] = sponsors_count
    cache["sponsoring"] = sponsoring_count

    return sponsors_count


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
        return cache.get("x", 0)

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
        return cache.get("soundcloud", 0)

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


def get_instagram_followers(username, cache, cache_key):
    """Fetch Instagram followers using a third-party RapidAPI service."""
    if not RAPIDAPI_KEY:
        return cache.get(cache_key, 0)

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


def format_bytes_mb(mb):
    """Format megabytes into human-readable size string (MB/GB/TB)."""
    try:
        val = float(mb)
        if val >= 1024 * 1024:
            return f"{val / (1024 * 1024):.2f}TB".replace(".00", "")
        elif val >= 1024:
            return f"{val / 1024:.2f}GB".replace(".00", "")
        elif val > 0:
            return f"{val:.1f}MB"
        return ""
    except (ValueError, TypeError):
        return str(mb) if mb else ""


def get_whatpulse_stats(username, cache):
    """Fetch WhatPulse keys, clicks, download, and upload via official API or public profile."""
    # 1. Try official API if token is provided
    if WHATPULSE_API_TOKEN:
        try:
            url = f"https://whatpulse.org/api/v1/users/{username}"
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {WHATPULSE_API_TOKEN}",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                totals = data.get("user", {}).get("totals", {})
                if totals.get("keys") is not None and totals.get("clicks") is not None:
                    down_str = format_bytes_mb(totals.get("download_mb", 0))
                    up_str = format_bytes_mb(totals.get("upload_mb", 0))
                    print(
                        f"Successfully fetched WhatPulse stats via official API for {username}: "
                        f"{totals.get('keys')} keys, {totals.get('clicks')} clicks, {down_str} down, {up_str} up"
                    )
                    return {
                        "keys": int(totals.get("keys", 0)),
                        "clicks": int(totals.get("clicks", 0)),
                        "download": down_str,
                        "upload": up_str,
                    }
        except Exception as e:
            print(f"WhatPulse API error: {e}. Falling back to public profile...")

    # 2. Fallback to public profile parsing
    try:
        url = f"https://whatpulse.org/u/{username}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
        clean = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL)
        clean = re.sub(r"<style.*?</style>", "", clean, flags=re.DOTALL)
        clean_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", clean))
        m = re.search(
            r"([\d,]+)\s+keys\s*·\s*([\d,]+)\s+clicks(?:\s+([\d.]+[KMGTP]?B)\s*↓\s*·\s*([\d.]+[KMGTP]?B)\s*↑)?",
            clean_text,
        )
        if m:
            down_str = m.group(3) if m.group(3) else ""
            up_str = m.group(4) if m.group(4) else ""
            print(
                f"Successfully parsed WhatPulse stats from public profile for {username}: "
                f"{m.group(1)} keys, {m.group(2)} clicks, {down_str} down, {up_str} up"
            )
            return {
                "keys": int(m.group(1).replace(",", "")),
                "clicks": int(m.group(2).replace(",", "")),
                "download": down_str,
                "upload": up_str,
            }
    except Exception as e:
        print(f"Error fetching WhatPulse public profile for {username}: {e}")

    return cache.get(
        "whatpulse", {"keys": 0, "clicks": 0, "download": "", "upload": ""}
    )


def update_readme(stats, whatpulse_stats=None):
    """Update README.md with content generated from stats and social.json config."""
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
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
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        # Update WhatPulse badge if stats available
        if whatpulse_stats:
            wp_config = config.get("whatpulse", {})
            wp_user = wp_config.get("username", "skiddle")
            wp_color = wp_config.get("color", "00ADD8")
            wp_label_color = wp_config.get("label_color", "333333")
            wp_style = wp_config.get("style", "flat-square")

            keys_str = format_count(whatpulse_stats.get("keys", 0))
            clicks_str = format_count(whatpulse_stats.get("clicks", 0))
            parts = [f"{keys_str} keys", f"{clicks_str} clicks"]
            if whatpulse_stats.get("download"):
                parts.append(f"{whatpulse_stats['download']} ↓")
            if whatpulse_stats.get("upload"):
                parts.append(f"{whatpulse_stats['upload']} ↑")

            badge_text = " · ".join(parts)
            encoded_val = urllib.parse.quote(badge_text)
            wp_badge_url = (
                f"https://img.shields.io/badge/WhatPulse-{encoded_val}-{wp_color}"
                f"?style={wp_style}&labelColor={wp_label_color}"
            )
            wp_badge_html = f'<a href="https://whatpulse.org/u/{wp_user}"><img alt="WhatPulse" src="{wp_badge_url}"/></a>'

            wp_pattern = r"<!-- WHATPULSE-STATS:START -->.*?<!-- WHATPULSE-STATS:END -->"
            wp_replacement = f"<!-- WHATPULSE-STATS:START -->\n    {wp_badge_html}\n    <!-- WHATPULSE-STATS:END -->"
            content = re.sub(wp_pattern, wp_replacement, content, flags=re.DOTALL)

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Successfully updated README.md")


if __name__ == "__main__":
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
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
        wp_config = config.get("whatpulse", {})
        wp_username = wp_config.get("username", "skiddle")
        stats = {}
        whatpulse_stats = cache_data.get("whatpulse", {})

        # Always fetch fresh GitHub stats (high rate limit, no cost)
        print("Fetching fresh GitHub followers...")
        stats["github"] = get_github_followers(
            platforms.get("github", {}).get("handle", "arcestia"), cache
        )

        print("Fetching fresh GitHub sponsors...")
        stats["sponsors"] = get_github_sponsors(
            platforms.get("sponsors", {}).get("handle", "arcestia"), cache
        )

        # For other platforms, use cache if not expired (stricter rate limits)
        if current_time - last_update > 86400 or not cache or not whatpulse_stats:
            print("Cache expired or empty. Fetching fresh stats...")

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

            print("Fetching SoundCloud followers...")
            stats["soundcloud"] = get_soundcloud_followers(
                platforms.get("soundcloud", {}).get(
                    "url", "https://soundcloud.com/arcestiaishere"
                ),
                cache,
            )

            print(f"Fetching WhatPulse stats ({wp_username})...")
            whatpulse_stats = get_whatpulse_stats(wp_username, cache_data)

            # Update cache with new timestamp
            save_json(
                cache_path,
                {
                    "last_updated_at": current_time,
                    "stats": stats,
                    "whatpulse": whatpulse_stats,
                },
            )
        else:
            print(
                f"Using cached stats for other platforms (Last updated {int((current_time - last_update) / 3600)}h ago)"
            )
            # Merge fresh GitHub stats with cached values for other platforms
            stats.update(
                {
                    k: v
                    for k, v in cache.items()
                    if k not in ["github", "sponsors", "sponsoring"]
                }
            )

        update_readme(stats, whatpulse_stats)
