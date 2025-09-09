#!/usr/bin/env python3
"""
Script to manually trigger versioned documentation deployment for existing releases.
"""

import json
import os
import re
import subprocess
from urllib.parse import urlparse


def trigger_docs_workflow(version_tag):
    """Trigger the docs-versioned workflow for a specific version."""
    print(f"Triggering docs deployment for {version_tag}")

    # Get GitHub token from environment
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN environment variable not set")
        return False

    # Get repository from git remote
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        remote_url = result.stdout.strip()
        # Extract owner/repo from URL robustly
        repo_path = None
        # HTTPS or SSH "git@github.com:owner/repo.git" or "https://github.com/owner/repo.git"
        if remote_url.startswith("git@"):
            # SSH URL, git@github.com:owner/repo.git
            match = re.match(r"git@([^:]+):([^/]+/[^/]+)(\.git)?", remote_url)
            if match and match.group(1) == "github.com":
                repo_path = match.group(2)
        else:
            # Try parsing as a URL
            parsed = urlparse(remote_url)
            if parsed.hostname == "github.com":
                repo_path = parsed.path.lstrip("/")
                if repo_path.endswith(".git"):
                    repo_path = repo_path[:-4]
        if not repo_path:
            print("❌ Could not determine repository from git remote")
            return False
    except subprocess.CalledProcessError:
        print("❌ Could not get git remote information")
        return False

    # Use curl to trigger the workflow via repository dispatch
    payload = {
        "event_type": "release-triggered",
        "client_payload": {"tag": version_tag},
    }

    cmd = [
        "curl",
        "-X",
        "POST",
        "-H",
        f"Authorization: token {token}",
        "-H",
        "Accept: application/vnd.github.v3+json",
        f"https://api.github.com/repos/{repo_path}/dispatches",
        "-d",
        json.dumps(payload),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Successfully triggered docs deployment for {version_tag}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to trigger docs deployment for {version_tag}: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main():
    """Main function to trigger docs deployment for all v3.x versions."""
    versions = ["v3.0.0", "v3.0.1", "v3.0.2"]

    print("Triggering versioned documentation deployment for existing releases...")
    print("=" * 60)

    success_count = 0
    for version in versions:
        if trigger_docs_workflow(version):
            success_count += 1
        print()

    print(f"Summary: {success_count}/{len(versions)} versions triggered successfully")


if __name__ == "__main__":
    main()
