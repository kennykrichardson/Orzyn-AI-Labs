# ============================================================
# Orzyn AI
# Notebook 05 — Pull Request Intelligence
# ============================================================

from pathlib import Path
import sys

BACKEND_DIR = Path.cwd().parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from statistics import mean

import pandas as pd

from orzyn import (
    client,
    parse_datetime,
    pretty_json,
    save_json,
    load_json,
    get_active_repository,
)

repo_config = get_active_repository()

OWNER = repo_config.owner

REPOSITORY = repo_config.repository

print(f"Repository : {OWNER}/{REPOSITORY}")

PULL_REQUEST_QUERY = """
query(
    $owner:String!,
    $name:String!
){

repository(
    owner:$owner,
    name:$name
){

pullRequests(

    first:100,

    orderBy:{
        field:CREATED_AT,
        direction:DESC
    }

){

nodes{

number

title

state

createdAt

mergedAt

closedAt

isDraft

additions

deletions

changedFiles

commits{

totalCount

}

reviews{

totalCount

}

comments{

totalCount

}

author{

login

}

}

}

}

}
"""

@dataclass(slots=True)
class PullRequestProfile:

    number: int

    title: str

    author: str

    state: str

    created_at: datetime

    merged_at: datetime | None

    closed_at: datetime | None

    additions: int

    deletions: int

    changed_files: int

    commits: int

    reviews: int

    comments: int

    merged: bool

    draft: bool

def build_pull_request(node: dict) -> PullRequestProfile:

    author = node.get("author")

    return PullRequestProfile(

        number=node["number"],

        title=node["title"],

        author=author["login"] if author else "Unknown",

        state=node["state"],

        created_at=datetime.fromisoformat(
            node["createdAt"].replace("Z", "+00:00")
        ),

        merged_at=(
            datetime.fromisoformat(
                node["mergedAt"].replace("Z", "+00:00")
            )
            if node["mergedAt"]
            else None
        ),

        closed_at=(
            datetime.fromisoformat(
                node["closedAt"].replace("Z", "+00:00")
            )
            if node["closedAt"]
            else None
        ),

        additions=node["additions"],

        deletions=node["deletions"],

        changed_files=node["changedFiles"],

        commits=node["commits"]["totalCount"],

        reviews=node["reviews"]["totalCount"],

        comments=node["comments"]["totalCount"],

        merged=node["mergedAt"] is not None,

        draft=node["isDraft"]

    )

result = client.execute(

    PULL_REQUEST_QUERY,

    {

        "owner": OWNER,

        "name": REPOSITORY

    }

)

nodes = (

    result["repository"]

          ["pullRequests"]

          ["nodes"]

)

pull_requests = [

    build_pull_request(node)

    for node in nodes

]

print(

    f"Downloaded {len(pull_requests)} pull requests."

)

if not pull_requests:

    raise RuntimeError(
        "Repository contains no pull requests."
    )

print("Pull request history validated.")

largest_prs = sorted(

    pull_requests,

    key=lambda pr:

        pr.additions +

        pr.deletions,

    reverse=True

)

largest_pr = largest_prs[0]

pr_df = pd.DataFrame(

    [

        {

            "PR": pr.number,

            "Title": pr.title,

            "Author": pr.author,

            "State": pr.state,

            "Additions": pr.additions,

            "Deletions": pr.deletions,

            "Total Changes":

                pr.additions +

                pr.deletions,

            "Files":

                pr.changed_files,

            "Commits":

                pr.commits,

            "Reviews":

                pr.reviews,

            "Comments":

                pr.comments,

            "Draft":

                pr.draft

        }

        for pr in largest_prs

    ]

)

pr_df.head(100)

state_counts = Counter(

    pr.state

    for pr in pull_requests

)

author_counts = Counter(

    pr.author

    for pr in pull_requests

)

print("=" * 60)

print("Pull Request Summary")

print("=" * 60)

print(f"Repository        : {OWNER}/{REPOSITORY}")

print(f"Pull Requests     : {len(pull_requests)}")

print(f"Authors           : {len(author_counts)}")

print(f"Merged            : {sum(pr.merged for pr in pull_requests)}")

print(f"Open              : {state_counts['OPEN']}")

print(f"Closed            : {state_counts['CLOSED']}")

print(f"Draft             : {sum(pr.draft for pr in pull_requests)}")

print(
    f"Largest PR Change : "
    f"{largest_pr.additions + largest_pr.deletions}"
)

print(
    f"Average Changes   : "
    f"{mean(pr.additions + pr.deletions for pr in pull_requests):.2f}"
)