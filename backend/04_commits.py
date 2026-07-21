"""
============================================================
ORZYN AI m2.0
Notebook 04
Commit Intelligence
============================================================

Purpose
-------
Extract and analyze commit history for any GitHub repository.

Produces
--------
CommitProfile objects
Repository commit metrics
Developer activity metrics
Timeline statistics
"""

from pathlib import Path 
import sys 

BACKEND_DIR = Path.cwd().parent.resolve() 
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from orzyn import *

repo_config = get_active_repository()

OWNER = repo_config.owner

REPOSITORY = repo_config.repository

COMMIT_HISTORY_QUERY = """
query(
    $owner:String!,
    $name:String!
){

repository(
    owner:$owner,
    name:$name
){

defaultBranchRef{

target{

... on Commit{

history(first:100){

nodes{

oid

messageHeadline

committedDate

additions

deletions

changedFilesIfAvailable

author{

name

email

user{

login

}

}

}

}

}

}

}

}

}
"""

@dataclass(slots=True)
class CommitProfile:

    sha: str

    message: str

    author: str

    username: str | None

    email: str | None

    committed_at: datetime

    additions: int

    deletions: int

    files_changed: int

def build_commit(node: dict) -> CommitProfile:

    author = node.get("author") or {}

    user = author.get("user")

    return CommitProfile(

        sha=node["oid"],

        message=node["messageHeadline"],

        author=author.get("name") or "Unknown",

        username=user.get("login") if user else None,

        email=author.get("email"),

        committed_at=parse_datetime(
            node["committedDate"]
        ),

        additions=node.get("additions", 0),

        deletions=node.get("deletions", 0),

        files_changed=node.get(
            "changedFilesIfAvailable"
        ) or 0

    )

repository = client.execute(

    """
    query(
        $owner:String!,
        $name:String!
    ){

        repository(
            owner:$owner,
            name:$name
        ){

            name

            defaultBranchRef{

                name

                target{

                    __typename

                }

            }

        }

    }
    """,

    {

        "owner": OWNER,

        "name": REPOSITORY

    }

)

repo = repository.get("repository")

if repo is None:

    raise ValueError(
        "Repository not found."
    )

branch = repo.get("defaultBranchRef")

if branch is None:

    raise ValueError(
        "Repository has no default branch."
    )

target = branch.get("target")

if target is None:

    raise ValueError(
        "Default branch contains no commits."
    )

if target["__typename"] != "Commit":

    raise ValueError(
        "Default branch target is not a Commit."
    )

print(f"Repository : {repo['name']}")
print(f"Branch     : {branch['name']}")

result = client.execute(

    COMMIT_HISTORY_QUERY,

    {
        "owner": OWNER,
        "name": REPOSITORY
    }

)

repository = result.get("repository")

if repository is None:
    raise RuntimeError("Repository not found.")

branch = repository.get("defaultBranchRef")

if branch is None:
    raise RuntimeError("Repository has no default branch.")

target = branch.get("target")

if target is None:
    raise RuntimeError("Default branch has no commits.")

history = target.get("history")

if history is None:
    raise RuntimeError("Unable to retrieve commit history.")

nodes = history.get("nodes", [])

commits = [
    build_commit(node)
    for node in nodes
]

print(f"Downloaded {len(commits)} commits.")

if not commits:

    raise RuntimeError(
        "Repository contains no commits."
    )

print("Commit history validated.")

commits[0]

commits[-1]

author_counts = Counter(

    commit.author

    for commit in commits

)

author_counts

author_counts.most_common(10)

sorted_commits = sorted(

    commits,

    key=lambda commit: (

        commit.additions +

        commit.deletions

    ),

    reverse=True

)

largest_commit = sorted_commits[0]

print(

    f"Ranked {len(sorted_commits)} commits "

    "by total lines changed."

)



print("=" * 120)

print(
    f"{'#':<4}"
    f"{'Message':<65}"
    f"{'+Adds':>8}"
    f"{'-Dels':>8}"
    f"{'Total':>10}"
)

print("=" * 120)

for index, commit in enumerate(

    sorted_commits[:100],

    start=1

):

    total = (

        commit.additions +

        commit.deletions

    )

    print(

        f"{index:<4}"

        f"{commit.message[:62]:<65}"

        f"{commit.additions:>8}"

        f"{commit.deletions:>8}"

        f"{total:>10}"

    )

average_changes = (

    sum(

        commit.additions +

        commit.deletions

        for commit in commits

    )

    / len(commits)

)

round(

    average_changes,

    2

)

weekday_counts = Counter(

    commit.committed_at.strftime("%A")

    for commit in commits

)

weekday_counts

hour_counts = Counter(

    commit.committed_at.hour

    for commit in commits

)

hour_counts

first_commit = min(

    commits,

    key=lambda commit:

        commit.committed_at

)

latest_commit = max(

    commits,

    key=lambda commit:

        commit.committed_at

)

print(first_commit.committed_at)

print(latest_commit.committed_at)

print("=" * 60)

print("Repository Commit Summary")

print("=" * 60)

print()

print(f"Repository      : {REPOSITORY}")

print(f"Total Commits   : {len(commits)}")

print(f"Contributors    : {len(author_counts)}")

print(
    f"Largest Commit  : "
    f"{largest_commit.message}"
)

print(
    f"Lines Changed   : "
    f"{largest_commit.additions + largest_commit.deletions}"
)

print(
    f"Author          : "
    f"{largest_commit.author}"
)
print(
    f"Average Change  : "
    f"{average_changes:.2f}"
)

print(
    f"First Commit    : "
    f"{first_commit.committed_at.date()}"
)

print(
    f"Latest Commit   : "
    f"{latest_commit.committed_at.date()}"
)

