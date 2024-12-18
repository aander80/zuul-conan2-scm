#!/usr/bin/python3

import random
import string
import sys
from argparse import ArgumentParser
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from typing import List, Optional

import requests


# A note on gerrit. It always returns )]}' as the first characters in the response before actual
# JSON data. We need to remove them in the response text before parsing as JSON.
GERRIT_URL = "http://admin:secret@localhost:8080/a"


def parse_args(argv: Optional[List[str]] = None):
    parser = ArgumentParser(description="Create a new change in a Gerrit repository")
    parser.add_argument("repo_name", help="The name of the repository to create a change in")
    parser.add_argument("commit_message", help="The commit message for the change")
    parser.add_argument("--merge", action="store_true", help="Merge the change after creating it")
    return parser.parse_args(argv)


def create_change(repo_name, commit_message, merge=False):
    print(f"Creating a new change with commit message {commit_message}")
    with TemporaryDirectory() as temp_dir:
        print(f"Cloning repository {repo_name} to {temp_dir}")
        run(["git", "clone", f"{GERRIT_URL}/{repo_name}", temp_dir], check=True)

        # Set up change ID hooks
        resp = requests.get(f"{GERRIT_URL}/tools/hooks/commit-msg")
        resp.raise_for_status()
        commit_msg_hook = Path(temp_dir, ".git", "hooks", "commit-msg")
        with open(commit_msg_hook, "w") as f:
            f.write(resp.text)
        commit_msg_hook.chmod(0o755)

        # Create dummy file and commit
        random_file = f"{''.join(random.choice(string.ascii_lowercase) for _ in range(6))}.txt"
        Path(temp_dir, random_file).touch()
        run(["git", "add", random_file], cwd=temp_dir, check=True)
        run(["git", "commit", "-m", commit_message], cwd=temp_dir, check=True)
        run(["git", "push", "origin", "HEAD:refs/for/master"], cwd=temp_dir, check=True)

        if merge:
            print("Merging change")
            run(["git", "push", "origin", "master"], cwd=temp_dir, check=True)


def main(argv: Optional[List[str]] = None):
    args = parse_args(argv)
    create_change(args.repo_name, args.commit_message, args.merge)


if __name__ == "__main__":
    main(sys.argv[1:])
