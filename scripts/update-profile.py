#!/usr/bin/env python3
"""
Automatically update open source contribution badges in README.md
by querying GitHub Search API for merged PRs authored by @gr8man.
"""

import os
import re
import sys
import json
import urllib.parse
import urllib.request
from collections import Counter

USERNAME = "gr8man"
README_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))

KNOWN_PRESETS = {
    "codeigniter4/CodeIgniter4": {
        "label": "codeigniter4",
        "color": "ee4623",
        "logo": "codeigniter",
        "query": "org%3Acodeigniter4%20is%3Apr%20is%3Amerged%20author%3Agr8man",
        "url": "https://github.com/pulls?q=is%3Apr+is%3Amerged+org%3Acodeigniter4+author%3Agr8man",
    },
    "laravel/framework": {
        "label": "laravel",
        "color": "f53003",
        "logo": "laravel",
        "query": "org%3Alaravel%20is%3Apr%20is%3Amerged%20author%3Agr8man",
        "url": "https://github.com/pulls?q=is%3Apr+is%3Amerged+org%3Alaravel+author%3Agr8man",
    },
    "mockery/mockery": {
        "label": "mockery",
        "color": "6f42c1",
        "logo": "php",
        "query": "repo%3Amockery%2Fmockery%20is%3Apr%20is%3Amerged%20author%3Agr8man",
        "url": "https://github.com/pulls?q=is%3Apr+is%3Amerged+repo%3Amockery%2Fmockery+author%3Agr8man",
    },
    "hestiacp/hestiacp": {
        "label": "hestiacp",
        "color": "0284c7",
        "logo": "linux",
        "query": "repo%3Ahestiacp%2Fhestiacp%20is%3Apr%20is%3Amerged%20author%3Agr8man",
        "url": "https://github.com/pulls?q=is%3Apr+is%3Amerged+repo%3Ahestiacp%2Fhestiacp+author%3Agr8man",
    },
    "phpstan/phpstan": {
        "label": "phpstan",
        "color": "2b2b2b",
        "logo": "phpstan",
        "query": "org%3Aphpstan%20is%3Apr%20is%3Amerged%20author%3Agr8man",
        "url": "https://github.com/pulls?q=is%3Apr+is%3Amerged+org%3Aphpstan+author%3Agr8man",
    },
    "rectorphp/rector": {
        "label": "rector",
        "color": "4f5b93",
        "logo": "rector",
        "query": "org%3Arectorphp%20is%3Apr%20is%3Amerged%20author%3Agr8man",
        "url": "https://github.com/pulls?q=is%3Apr+is%3Amerged+org%3Arectorphp+author%3Agr8man",
    },
    "symfony/symfony": {
        "label": "symfony",
        "color": "000000",
        "logo": "symfony",
        "query": "org%3Asymfony%20is%3Apr%20is%3Amerged%20author%3Agr8man",
        "url": "https://github.com/pulls?q=is%3Apr+is%3Amerged+org%3Asymfony+author%3Agr8man",
    },
}

def fetch_merged_prs(token=None):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "gr8man-profile-updater",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    page = 1
    items = []
    while True:
        url = f"https://api.github.com/search/issues?q=is:pr+is:merged+is:public+author:{USERNAME}&per_page=100&page={page}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            batch = data.get("items", [])
            items.extend(batch)
            if len(items) >= data.get("total_count", 0) or not batch:
                break
            page += 1
    return items

def generate_badges(prs):
    repo_counts = Counter()
    for pr in prs:
        repo_url = pr.get("repository_url", "")
        if "repos/" in repo_url:
            repo_name = repo_url.split("repos/")[1]
            repo_counts[repo_name] += 1

    lines = []
    # Global badge
    global_query = f"is%3Apr%20is%3Amerged%20is%3Apublic%20author%3A{USERNAME}"
    lines.append(
        f"[![open source PRs merged](https://img.shields.io/github/issues-search?query={global_query}&label=open%20source%20PRs%20merged&color=22c55e&style=flat&logo=github)](https://github.com/pulls?q=is%3Apr+is%3Amerged+is%3Apublic+author%3A{USERNAME})"
    )

    for repo, count in repo_counts.most_common():
        preset = KNOWN_PRESETS.get(repo)
        if preset:
            label = preset["label"]
            color = preset["color"]
            logo = preset["logo"]
            query = preset["query"]
            target_url = preset["url"]
        else:
            label = repo.split("/")[-1].lower()
            color = "0969da"
            logo = "github"
            query = f"repo%3A{urllib.parse.quote(repo)}%20is%3Apr%20is%3Amerged%20author%3A{USERNAME}"
            target_url = f"https://github.com/{repo}/pulls?q=is%3Apr+is%3Amerged+author%3A{USERNAME}"

        badge_url = f"https://img.shields.io/github/issues-search?query={query}&label={urllib.parse.quote(label)}%20PRs%20merged&color={color}&style=flat&logo={logo}"
        lines.append(f"[![{label}]({badge_url})]({target_url})")

    return "\n".join(lines)

def update_readme(badges_md):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    marker_start = "<!-- START_PR_BADGES -->"
    marker_end = "<!-- END_PR_BADGES -->"

    replacement = f"{marker_start}\n{badges_md}\n{marker_end}"

    if marker_start in content and marker_end in content:
        pattern = re.compile(f"{re.escape(marker_start)}.*?{re.escape(marker_end)}", re.DOTALL)
        new_content = pattern.sub(replacement, content)
    else:
        # If markers don't exist yet, insert under '## Open source contributions'
        target = "## Open source contributions"
        if target in content:
            # Replace existing badges under target up to the next heading
            parts = content.split(target, 1)
            rest = parts[1]
            next_heading_idx = rest.find("\n## ")
            if next_heading_idx != -1:
                after = rest[next_heading_idx:]
            else:
                after = ""
            new_content = f"{parts[0]}{target}\n\n{replacement}\n{after}"
        else:
            new_content = f"{content}\n\n## Open source contributions\n\n{replacement}\n"

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    print("Fetching merged PRs from GitHub API...")
    prs = fetch_merged_prs(token)
    print(f"Found {len(prs)} merged PRs.")
    badges_md = generate_badges(prs)
    print("Updating README.md...")
    update_readme(badges_md)
    print("Done!")

if __name__ == "__main__":
    main()
