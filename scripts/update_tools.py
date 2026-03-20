import json
import os
import re


def load_config(file_path):
    """Load JSON configuration file."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def generate_tools_html(config):
    """Generate HTML snippet from tools configuration."""
    if not config:
        return ""

    settings = config.get("settings", {})
    style = settings.get("style", "for-the-badge")
    default_logo_color = settings.get("defaultLogoColor", "white")

    tools_html = []
    for category in config.get("categories", []):
        cat_name = category.get("name", "Other")
        cat_icon = category.get("icon", "")

        tools_html.append(f"\n  <h3>{cat_icon} {cat_name}</h3>\n  <p>")

        for tool in category.get("tools", []):
            name = tool.get("name")
            color = tool.get("color", "grey")
            logo = tool.get("logo", "")
            logo_color = tool.get("logoColor", default_logo_color)

            # Escape spaces for URL
            safe_name = name.replace(" ", "_")
            badge_url = f"https://img.shields.io/badge/{safe_name}-{color}?style={style}&logo={logo}&logoColor={logo_color}"

            tools_html.append(f'    <img alt="{name}" src="{badge_url}" />')

        tools_html.append("  </p>")

    return "".join(tools_html)


def update_readme():
    """Update the README.md file with the latest tools from config."""
    # Determine paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(base_dir, "README.md")
    config_path = os.path.join(base_dir, ".github", "config", "tools.json")

    if not os.path.exists(readme_path):
        print(f"Error: Could not find {readme_path}")
        return

    # Load configuration
    config = load_config(config_path)
    if not config:
        print(f"Error: Could not find or load {config_path}")
        return

    # Generate content
    new_tools_content = generate_tools_html(config)

    # Read current README
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Define the markers
    pattern = r"<!-- TOOLS:START -->.*?<!-- TOOLS:END -->"
    replacement = f"<!-- TOOLS:START -->{new_tools_content}\n  <!-- TOOLS:END -->"

    # Perform replacement
    if "<!-- TOOLS:START -->" not in content:
        print("Error: Could not find <!-- TOOLS:START --> marker in README.md")
        return

    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Save the file
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Successfully updated tools in {readme_path} using {config_path}")


if __name__ == "__main__":
    update_readme()
