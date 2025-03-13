import argparse
import os

import requests
from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser(description='Fetch GitHub PR review comments with filters')
parser.add_argument('--owner', default='quarion', help='Repository owner (default: REPO_OWNER)')
parser.add_argument('--repo', default='poke-math', help='Repository name (default: REPO_NAME)')
parser.add_argument('--pr', type=int, default=1, help='Pull request number (default: 1)')
parser.add_argument('--author', default='quarion', help='Filter by GitHub username (default: any author)')
args = parser.parse_args()

token = os.getenv("GITHUB_TOKEN")
if not token:
    raise ValueError("Missing GITHUB_TOKEN in .env or environment variables")

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json"
}

url = f"https://api.github.com/repos/{args.owner}/{args.repo}/pulls/{args.pr}/comments"

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    all_comments = response.json()

    # Apply filters
    filtered_comments = [
        c for c in all_comments
        if not c.get('resolved')  # Unresolved only
           and (not args.author or c['user']['login'].lower() == args.author.lower())
    ]

except requests.exceptions.RequestException as e:
    print(f"API request failed: {e}")
    exit(1)

# Output formatting
if not filtered_comments:
    author_msg = f" by '@{args.author}'" if args.author else ''
    print(f"No unresolved comments{author_msg} found in PR #{args.pr}")
else:
    author_msg = f" by '@{args.author}'" if args.author else ''
    print(f"Found {len(filtered_comments)} unresolved comments{author_msg}:\n")

    for comment in filtered_comments:
        print("-----")
        print(f"File: {comment['path']}")
        print(f"Line: {comment.get('original_line', 'N/A')}")
        print(f"Author: @{comment['user']['login']}")
        print(f"Comment: {comment['body']}")
        #print(f"URL: {comment['html_url']}\n{'-' * 40}\n")
