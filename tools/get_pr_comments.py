import argparse
import json
import shutil
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch GitHub PR review comments with filters",
    )
    parser.add_argument("--owner", default="quarion")
    parser.add_argument("--repo", default="poke-math")
    parser.add_argument("--pr", type=int, default=1)
    parser.add_argument("--author", default="quarion")
    return parser.parse_args()


def fetch_comments(owner: str, repo: str, pr: int) -> list[dict]:
    if not shutil.which("gh"):
        raise RuntimeError("GitHub CLI is required: https://cli.github.com/")

    endpoint = f"repos/{owner}/{repo}/pulls/{pr}/comments"
    try:
        result = subprocess.run(
            ["gh", "api", "--paginate", "--slurp", endpoint],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or "GitHub API request failed"
        raise RuntimeError(
            f"{message}\nAuthenticate once with: gh auth login",
        ) from exc

    pages = json.loads(result.stdout)
    return [comment for page in pages for comment in page]


def main() -> int:
    args = parse_args()
    try:
        comments = fetch_comments(args.owner, args.repo, args.pr)
    except (RuntimeError, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1

    filtered = [
        comment
        for comment in comments
        if not comment.get("resolved")
        and (not args.author or comment["user"]["login"].lower() == args.author.lower())
    ]
    author = f" by '@{args.author}'" if args.author else ""
    if not filtered:
        print(f"No unresolved comments{author} found in PR #{args.pr}")
        return 0

    print(f"Found {len(filtered)} unresolved comments{author}:\n")
    for comment in filtered:
        print("-----")
        print(f"File: {comment['path']}")
        print(f"Line: {comment.get('original_line', 'N/A')}")
        print(f"Author: @{comment['user']['login']}")
        print(f"Comment: {comment['body']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
