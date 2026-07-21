# ============================================================
# ORZYN AI m2.0
# Notebook 07
# Developer Intelligence
# ============================================================

from __future__ import annotations

from pathlib import Path
import sys

BACKEND_DIR = Path.cwd().parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from collections import Counter
from dataclasses import dataclass

import pandas as pd

from orzyn import(
    client,
    get_active_repository,
)

repo_config = get_active_repository()

OWNER = repo_config.owner

REPOSITORY = repo_config.repository

print(f"Repository : {OWNER}/{REPOSITORY}")

CONTRIBUTORS_QUERY = """
query(
    $owner:String!,
    $name:String!
){

repository(

    owner:$owner,

    name:$name

){

mentionableUsers(

    first:100

){

nodes{

login

name

company

location

bio

url

avatarUrl

followers{

totalCount

}

repositories{

totalCount

}

}

}

}

}
"""

@dataclass(slots=True)
class DeveloperProfile:

    username: str

    name: str

    company: str | None

    location: str | None

    bio: str | None

    profile_url: str

    avatar_url: str

    followers: int

    repositories: int

def build_developer(node: dict) -> DeveloperProfile:

    return DeveloperProfile(

        username=node["login"],

        name=node["name"] or "",

        company=node["company"],

        location=node["location"],

        bio=node["bio"],

        profile_url=node["url"],

        avatar_url=node["avatarUrl"],

        followers=node["followers"]["totalCount"],

        repositories=node["repositories"]["totalCount"]

    )

result = client.execute(

    CONTRIBUTORS_QUERY,

    {

        "owner": OWNER,

        "name": REPOSITORY

    }

)

nodes = (

    result["repository"]

          ["mentionableUsers"]

          ["nodes"]

)

developers = [

    build_developer(node)

    for node in nodes

]

print(

    f"Downloaded {len(developers)} developer profiles."

)

if not developers:

    raise RuntimeError(

        "No developers found."

    )

print("Developer data validated.")

top_developers = sorted(

    developers,

    key=lambda developer:

        developer.followers,

    reverse=True

)

top_developer = top_developers[0]

developers_df = pd.DataFrame(

    [

        {

            "Username": developer.username,

            "Name": developer.name,

            "Followers": developer.followers,

            "Repositories": developer.repositories,

            "Company": developer.company,

            "Location": developer.location,

            "Profile": developer.profile_url

        }

        for developer in top_developers

    ]

)

developers_df.head(100)

print("=" * 60)

print("Developer Summary")

print("=" * 60)

print(f"Profiles          : {len(developers)}")

print(f"Most Followed     : {top_developer.username}")

print(f"Followers         : {top_developer.followers}")

print(f"Average Followers : {developers_df['Followers'].mean():.2f}")

print(f"Average Repos     : {developers_df['Repositories'].mean():.2f}")