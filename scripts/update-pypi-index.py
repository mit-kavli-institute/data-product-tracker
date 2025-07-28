#!/usr/bin/env python3
"""
Script to update PyPI index HTML files to properly link to wheel files.
This converts git URL references to proper wheel download links.
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import requests


def get_github_releases(
    repo_owner: str, repo_name: str, package_name: str
) -> List[Dict]:
    """Get all releases for a package from GitHub."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"

    try:
        response = requests.get(url)
        response.raise_for_status()
        releases = response.json()

        # Filter releases for this package
        package_releases = []
        for release in releases:
            if release["tag_name"].startswith(f"{package_name}-"):
                package_releases.append(release)

        return package_releases
    except Exception as e:
        print(f"Error fetching releases: {e}")
        return []


def generate_wheel_links(releases: List[Dict]) -> List[str]:
    """Generate HTML links for wheel and sdist files from releases."""
    links = []

    for release in releases:
        for asset in release.get("assets", []):
            name = asset["name"]
            if name.endswith(".whl") or name.endswith(".tar.gz"):
                download_url = asset["browser_download_url"]
                links.append(f'    <a href="{download_url}">{name}</a><br>')

    return links


def generate_index_html(
    package_name: str, wheel_links: List[str], git_url: Optional[str] = None
) -> str:
    """Generate the complete index.html content for a package."""

    # Include git URL as fallback if no wheels are available
    fallback_section = ""
    if not wheel_links and git_url:
        fallback_section = f"""
            <hr>
            <h6>Git installation (fallback)</h6>
            <pre><code>pip install {git_url}</code></pre>
        """

    wheel_section = (
        "\n".join(wheel_links)
        if wheel_links
        else "<p>No wheel files available yet.</p>"
    )

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <title>{package_name}</title>
  <link crossorigin="anonymous" href="https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css" rel="stylesheet" />
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&amp;display=swap" rel="stylesheet" type="text/css" />
  <link href="https://gist.githubusercontent.com/astariul/c09af596e802e945d3032774e10e1047/raw/f693a2e2b65966494da082887bc4be2917f615e4/random_icon.svg" rel="icon" />
  <link href="../static/package_styles.css" rel="stylesheet" />
</head>
<body>
  <div class="container">
    <section class="header">
      <h2 class="title">{package_name}</h2>
    </section>
    <div>
      <h6>Install</h6>
      <pre><code>pip install {package_name} --extra-index-url https://mit-kavli-institute.github.io/MIT-Kavli-PyPi/</code></pre>
    </div>
    <h6>Available versions</h6>
    <div class="package-links">
{wheel_section}
    </div>
    {fallback_section}
  </div>
</body>
</html>"""

    return html_content


def update_package_index(package_dir: Path, repo_owner: str, repo_name: str):
    """Update the index.html for a specific package."""
    package_name = package_dir.name
    index_file = package_dir / "index.html"

    print(f"Updating index for package: {package_name}")

    # Get existing git URL if present
    git_url = None
    if index_file.exists():
        content = index_file.read_text()
        # Try to extract git URL from existing content
        git_match = re.search(r'git\+https://[^\s<>"]+', content)
        if git_match:
            git_url = git_match.group(0)

    # Get releases from GitHub
    releases = get_github_releases(repo_owner, repo_name, package_name)

    # Generate wheel links
    wheel_links = generate_wheel_links(releases)

    # Generate new HTML
    html_content = generate_index_html(package_name, wheel_links, git_url)

    # Write the updated index
    index_file.write_text(html_content)
    print(f"  Updated with {len(wheel_links)} wheel/sdist links")


def main():
    parser = argparse.ArgumentParser(
        description="Update PyPI index HTML files to include wheel download links"
    )
    parser.add_argument(
        "--repo-owner",
        default="mit-kavli-institute",
        help="GitHub repository owner",
    )
    parser.add_argument(
        "--repo-name", default="MIT-Kavli-PyPi", help="GitHub repository name"
    )
    parser.add_argument(
        "--index-dir",
        default=".",
        help="Directory containing package directories",
    )
    parser.add_argument("--package", help="Update only a specific package")

    args = parser.parse_args()

    index_path = Path(args.index_dir)

    if args.package:
        # Update single package
        package_dir = index_path / args.package
        if package_dir.is_dir():
            update_package_index(package_dir, args.repo_owner, args.repo_name)
        else:
            print(f"Package directory not found: {package_dir}")
    else:
        # Update all packages
        for item in index_path.iterdir():
            if (
                item.is_dir()
                and not item.name.startswith(".")
                and item.name not in ["static", "_site"]
            ):
                update_package_index(item, args.repo_owner, args.repo_name)


if __name__ == "__main__":
    main()
