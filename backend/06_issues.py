# ============================================================
# ORZYN AI m2.0
# Notebook 06
# GitHub Issues Intelligence
# ============================================================

from pathlib import Path
import sys

BACKEND_DIR = Path.cwd().parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from statistics import mean

import pandas as pd

from orzyn import (
    client,
    parse_datetime,
    get_active_repository,
)

repo_config = get_active_repository()

OWNER = repo_config.owner

REPOSITORY = repo_config.repository

print(f"Repository : {OWNER}/{REPOSITORY}")

ISSUES_QUERY = """
query(
    $owner:String!,
    $name:String!
){

repository(

    owner:$owner,

    name:$name

){

issues(

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

closedAt

comments{

totalCount

}

author{

login

}

labels(

    first:20

){

nodes{

name

}

}

assignees(

    first:20

){

nodes{

login

}

}

}

}

}

}
"""

@dataclass(slots=True)
class IssueProfile:

    number: int

    title: str

    author: str

    state: str

    created_at: object

    closed_at: object | None

    comments: int

    labels: list[str]

    assignees: list[str]

def build_issue(node: dict) -> IssueProfile:

    author = node.get("author")

    return IssueProfile(

        number=node["number"],

        title=node["title"],

        author=author["login"] if author else "Unknown",

        state=node["state"],

        created_at=parse_datetime(
            node["createdAt"]
        ),

        closed_at=(

            parse_datetime(
                node["closedAt"]
            )

            if node["closedAt"]

            else None

        ),

        comments=node["comments"]["totalCount"],

        labels=[

            label["name"]

            for label in

            node["labels"]["nodes"]

        ],

        assignees=[

            person["login"]

            for person in

            node["assignees"]["nodes"]

        ]

    )

result = client.execute(

    ISSUES_QUERY,

    {

        "owner": OWNER,

        "name": REPOSITORY

    }

)

nodes = (

    result["repository"]

          ["issues"]

          ["nodes"]

)

issues = [

    build_issue(node)

    for node in nodes

]

print(

    f"Downloaded {len(issues)} issues."

)

if not issues:

    raise RuntimeError(

        "Repository contains no issues."

    )

print(

    "Issue history validated."

)

largest_issues = sorted(

    issues,

    key=lambda issue:

        issue.comments,

    reverse=True

)

largest_issue = largest_issues[0]

issues_df = pd.DataFrame(

    [

        {

            "Issue": issue.number,

            "Title": issue.title,

            "Author": issue.author,

            "State": issue.state,

            "Comments": issue.comments,

            "Labels": ", ".join(

                issue.labels

            ),

            "Assignees": ", ".join(

                issue.assignees

            ),

            "Created": issue.created_at,

            "Closed": issue.closed_at

        }

        for issue in largest_issues

    ]

)

issues_df.head(100)

state_counts = Counter(

    issue.state

    for issue in issues

)

author_counts = Counter(

    issue.author

    for issue in issues
)

label_counts = Counter(

    label

    for issue in issues

    for label in issue.labels

)

print("=" * 60)

print("Issue Summary")

print("=" * 60)

print(f"Repository      : {OWNER}/{REPOSITORY}")

print(f"Issues          : {len(issues)}")

print(f"Authors         : {len(author_counts)}")

print(f"Open            : {state_counts['OPEN']}")

print(f"Closed          : {state_counts['CLOSED']}")

print(f"Most Comments   : {largest_issue.comments}")

print(

    f"Average Comments: "

    f"{mean(issue.comments for issue in issues):.2f}"

)

print(

    f"Unique Labels   : "

    f"{len(label_counts)}"

)