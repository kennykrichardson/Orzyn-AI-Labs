"""
============================================================
ORZYN AI m2.0
Notebook 03 : Repository Intelligence
============================================================

Purpose
-------
Transform GitHub repository data into structured intelligence.
"""



from pathlib import Path
import sys

BACKEND_DIR = Path.cwd().parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))



from orzyn import *

from dataclasses import dataclass, field



REPOSITORY_QUERY = """
query($owner:String!, $name:String!){

repository(owner:$owner,name:$name){

name

description

url

homepageUrl

createdAt

updatedAt

pushedAt

diskUsage

isArchived

isFork

isPrivate

forkCount

stargazerCount

watchers{

totalCount

}

defaultBranchRef{

name

}

licenseInfo{

name

}

repositoryTopics(first:100){

nodes{

topic{

name

}

}

}

languages(

first:20,

orderBy:{

field:SIZE,

direction:DESC

}

){

edges{

size

node{

name

}

}

}

}

}
"""



@dataclass(slots=True)
class RepositoryProfile:

    name:str

    description:str|None

    url:str

    homepage:str|None

    created_at:object

    updated_at:object

    pushed_at:object

    default_branch:str

    license:str|None

    stars:int

    forks:int

    watchers:int

    disk_usage_kb:int

    archived:bool

    private:bool

    fork:bool

    topics:list[str]=field(default_factory=list)

    languages:dict[str,float]=field(default_factory=dict)



def calculate_language_percentages(edges):

    total = sum(

        edge["size"]

        for edge in edges

    )

    if total == 0:

        return {}

    return {

        edge["node"]["name"]:

        round(

            edge["size"]/total*100,

            2

        )

        for edge in edges

    }



def build_repository_profile(data):

    repo = data["repository"]

    return RepositoryProfile(

        name=repo["name"],

        description=repo["description"],

        url=repo["url"],

        homepage=repo["homepageUrl"],

        created_at=parse_datetime(repo["createdAt"]),

        updated_at=parse_datetime(repo["updatedAt"]),

        pushed_at=parse_datetime(repo["pushedAt"]),

        default_branch=repo["defaultBranchRef"]["name"],

        license=repo["licenseInfo"]["name"]
        if repo["licenseInfo"]
        else None,

        stars=repo["stargazerCount"],

        forks=repo["forkCount"],

        watchers=repo["watchers"]["totalCount"],

        disk_usage_kb=repo["diskUsage"],

        archived=repo["isArchived"],

        private=repo["isPrivate"],

        fork=repo["isFork"],

        topics=[

            topic["topic"]["name"]

            for topic in repo["repositoryTopics"]["nodes"]

        ],

        languages=calculate_language_percentages(

            repo["languages"]["edges"]

        )

    )



repo_config = get_active_repository()

OWNER = repo_config.owner

REPOSITORY = repo_config.repository



repository_data = client.execute(

    REPOSITORY_QUERY,

    {

        "owner":OWNER,

        "name":REPOSITORY

    }

)



profile = build_repository_profile(

    repository_data

)

profile



profile.languages



profile.topics



profile.stars



profile.default_branch



profile.created_at


