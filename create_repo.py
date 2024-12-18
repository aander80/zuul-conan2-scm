#!/usr/bin/python3

import json
import sys
from argparse import ArgumentParser
from pathlib import Path
from shutil import copytree
from subprocess import run
from tempfile import TemporaryDirectory
from typing import List, Optional

import requests


# A note on gerrit. It always returns )]}' as the first characters in the response before actual
# JSON data. We need to remove them in the response text before parsing as JSON.
GERRIT_URL = "http://admin:secret@localhost:8080/a"


def get_projects():
    resp = requests.get(f"{GERRIT_URL}/projects")
    resp.raise_for_status()
    return json.loads(resp.text[4:])


def create_project(project_name):
    data = {
        "submit_type": "INHERIT",
        "state": "ACTIVE",
        "permissions_only": True,
    }
    resp = requests.put(f"{GERRIT_URL}/projects/{project_name}", json=data)
    resp.raise_for_status()

    with TemporaryDirectory() as temp_dir:
        run(["git", "init"], cwd=temp_dir, check=True)
        run(["git", "commit", "--allow-empty", "-m", "Initial commit"], cwd=temp_dir, check=True)
        run(["git", "remote", "add", "origin", f"{GERRIT_URL}/{project_name}"], cwd=temp_dir, check=True)
        run(["git", "push", "origin", "master"], cwd=temp_dir, check=True)

    resp = requests.put(f"{GERRIT_URL}/projects/{project_name}/HEAD", json={"ref": "refs/heads/master"})
    resp.raise_for_status()

    print(f"Project {project_name} created")


def populate_repo(project_name):
    local_repo_path = Path(__file__).parent / "repos" / project_name

    with TemporaryDirectory() as temp_dir:
        run(["git", "clone", f"{GERRIT_URL}/{project_name}", "."], cwd=temp_dir, check=True)
        copytree(local_repo_path, temp_dir, dirs_exist_ok=True)
        run(["git", "add", "."], cwd=temp_dir, check=True)
        run(["git", "commit", "--allow-empty", "-m", "Populated repo"], cwd=temp_dir, check=True)
        run(["git", "push", "origin", "master"], cwd=temp_dir, check=True)

    print(f"Project {project_name} populated")


def main(argv: Optional[List[str]] = None):
    parser = ArgumentParser()
    parser.add_argument("repo_name")
    args = parser.parse_args(argv)

    current_projects = get_projects()
    if args.repo_name in current_projects:
        print(f"Project {args.repo_name} already exists")
    else:
        create_project(args.repo_name)

    populate_repo(args.repo_name)


if __name__ == "__main__":
    main(sys.argv[1:])
