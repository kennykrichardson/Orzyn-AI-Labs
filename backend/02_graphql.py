"""
============================================================
ORZYN AI m2.0
Notebook 02 : GraphQL Validation
============================================================

Purpose
-------
Validate the shared GraphQL engine.

Responsibilities
----------------
• Authentication
• Query validation
• Pagination validation
• Rate limit validation
"""



from pathlib import Path
import sys

BACKEND_DIR = Path.cwd().parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))



from orzyn import *



RATE_LIMIT_QUERY = """
query {

    rateLimit {

        limit
        remaining
        cost
        resetAt

    }

}
"""



rate_limit = client.execute(RATE_LIMIT_QUERY)

pretty_json(rate_limit)



REPOSITORY_QUERY = """
query($owner:String!, $name:String!) {

    repository(owner:$owner, name:$name) {

        name

        description

        stargazerCount

        forkCount

        url

        isPrivate

    }

}
"""



repo_config = get_active_repository()

OWNER = repo_config.owner

REPOSITORY = repo_config.repository



repository = client.execute(

    REPOSITORY_QUERY,

    {

        "owner":OWNER,

        "name":REPOSITORY

    }

)

pretty_json(repository)



PAGINATION_QUERY = """
query(
    $owner:String!,
    $name:String!,
    $after:String
){

repository(owner:$owner,name:$name){

issues(

first:100,

after:$after

){

nodes{

number

title

}

pageInfo{

hasNextPage

endCursor

}

}

}

}
"""



issues = list(

client.paginate(

    PAGINATION_QUERY,

    {

        "owner":OWNER,

        "name":REPOSITORY

    },

    ["repository","issues"]

)

)

len(issues)



issues[:5]



pretty_json(

client.get_rate_limit()

)


