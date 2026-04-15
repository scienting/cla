import json
import os
import sys
from pathlib import Path


def main() -> None:
    event_path_str = os.getenv("GITHUB_EVENT_PATH")
    if not event_path_str:
        print("Error: GITHUB_EVENT_PATH environment variable not set.")
        sys.exit(1)

    event_path = Path(event_path_str)
    if not event_path.exists():
        print(f"Error: Event payload file not found at {event_path}")
        sys.exit(1)

    with event_path.open("r") as f:
        event: dict[str, str | int] = json.load(f)

    try:
        user = event["comment"]["user"]
        pr_number = event["issue"]["number"]
        repo_id = event["repository"]["id"]
        comment_id = event["comment"]["id"]
        created_at = event["comment"]["created_at"]
    except KeyError as e:
        print(f"Error: Missing expected key in GitHub payload - {e}")
        sys.exit(1)

    new_entry = {
        "name": user["login"],
        "id": user["id"],
        "comment_id": comment_id,
        "created_at": created_at,
        "repoId": repo_id,
        "pullRequestNo": pr_number,
    }

    cla_file = Path("signatures/cla.json")
    if not cla_file.exists() or cla_file.stat().st_size == 0:
        cla_data = {"signedContributors": []}
    else:
        with cla_file.open("r") as f:
            try:
                cla_data = json.load(f)
            except json.JSONDecodeError:
                print("Error: cla.json is corrupted or contains invalid JSON.")
                sys.exit(1)

    if "signedContributors" not in cla_data:
        cla_data["signedContributors"] = []

    for signer in cla_data["signedContributors"]:
        if signer["id"] == user["id"]:
            print(
                f"User {user['login']} (ID: {user['id']}) has already signed the CLA."
            )
            sys.exit(0)

    cla_data["signedContributors"].append(new_entry)

    with cla_file.open("w") as f:
        json.dump(cla_data, f, indent=2)

    print(
        f"Successfully parsed payload and added signature for {user['login']} to cla.json"
    )


if __name__ == "__main__":
    main()
