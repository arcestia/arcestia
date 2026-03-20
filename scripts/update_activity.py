import json
import os
import re
import urllib.request
from datetime import datetime

# Configuration
GITHUB_USERNAME = "arcestia"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
MAX_EVENTS = 10


def fetch_github_activity(username):
    """Fetch recent public events for a GitHub user."""
    url = f"https://api.github.com/users/{username}/events/public"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching GitHub activity: {e}")
        return []


def format_event(event):
    """Format a GitHub event into a readable markdown string."""
    event_type = event.get("type")
    repo_name = event.get("repo", {}).get("name")
    repo_url = f"https://github.com/{repo_name}"

    payload = event.get("payload", {})

    if event_type == "PushEvent":
        commits = payload.get("commits", [])
        if not commits:
            return None
        count = len(commits)
        s = "s" if count > 1 else ""
        return f"📝 Pushed {count} commit{s} to [`{repo_name}`]({repo_url})"

    elif event_type == "PullRequestEvent":
        action = payload.get("action")
        number = payload.get("number")
        pr_url = payload.get("pull_request", {}).get("html_url")
        return f"🔀 {action.capitalize()} PR [#{number}]({pr_url}) in [`{repo_name}`]({repo_url})"

    elif event_type == "IssuesEvent":
        action = payload.get("action")
        number = payload.get("issue", {}).get("number")
        issue_url = payload.get("issue", {}).get("html_url")
        return f"ℹ️ {action.capitalize()} issue [#{number}]({issue_url}) in [`{repo_name}`]({repo_url})"

    elif event_type == "CreateEvent":
        ref_type = payload.get("ref_type")
        return f"🏗️ Created {ref_type} `{payload.get('ref') or repo_name}` in [`{repo_name}`]({repo_url})"

    elif event_type == "WatchEvent":
        return f"⭐ Starred [`{repo_name}`]({repo_url})"

    elif event_type == "ReleaseEvent":
        tag = payload.get("release", {}).get("tag_name")
        return f"🚀 Released `{tag}` in [`{repo_name}`]({repo_url})"

    return None


def update_readme(activity_markdown):
    """Update the README.md file between activity markers."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(base_dir, "README.md")

    if not os.path.exists(readme_path):
        print(f"README not found at {readme_path}")
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"<!-- RECENT-ACTIVITY:START -->.*?<!-- RECENT-ACTIVITY:END -->"
    replacement = f"<!-- RECENT-ACTIVITY:START -->\n{activity_markdown}\n<!-- RECENT-ACTIVITY:END -->"

    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated_content)


if __name__ == "__main__":
    print(f"Fetching activity for {GITHUB_USERNAME}...")
    events = fetch_github_activity(GITHUB_USERNAME)

    formatted_activities = []
    seen_actions = set()  # Avoid too much repetition for the same repo/action

    for event in events:
        if len(formatted_activities) >= MAX_EVENTS:
            break

        formatted = format_event(event)
        if formatted and formatted not in seen_actions:
            formatted_activities.append(f"- {formatted}")
            seen_actions.add(formatted)

    if formatted_activities:
        activity_md = "\n".join(formatted_activities)
        update_readme(activity_md)
        print("Successfully updated README with recent activity.")
    else:
        print("No recent activity found to update.")
