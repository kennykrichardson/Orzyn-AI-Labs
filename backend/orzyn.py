"""
============================================================
ORZYN AI m2.0
Core Engine
============================================================

Shared infrastructure for every notebook.

Contains
--------
• Configuration
• Environment
• GraphQL Client
• Exceptions
• Pagination
• Utilities

Author
------
Kenny Richardson
"""

from __future__ import annotations

import json
import os

from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from dataclasses import dataclass

# ==========================================================
# Project Configuration
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BACKEND_DIR = PROJECT_ROOT / "backend"

NOTEBOOK_DIR = BACKEND_DIR / "notebooks"

DATA_DIR = BACKEND_DIR / "data"

CACHE_DIR = BACKEND_DIR / "cache"

EXPORT_DIR = BACKEND_DIR / "exports"

MODEL_DIR = BACKEND_DIR / "models"

load_dotenv(PROJECT_ROOT / ".env")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HF_TOKEN = os.getenv("HF_TOKEN")

GRAPHQL_URL = "https://api.github.com/graphql"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/vnd.github+json",
}

# ==========================================================
# Exceptions
# ==========================================================


class GraphQLClientError(Exception):
    """Base GraphQL Exception."""


class AuthenticationError(GraphQLClientError):
    """Authentication Failure."""


class RateLimitError(GraphQLClientError):
    """GitHub Rate Limit."""


class QueryError(GraphQLClientError):
    """GraphQL Query Error."""


# ==========================================================
# Utilities
# ==========================================================

@dataclass(slots=True)
class RepositoryConfig:

    owner: str

    repository: str

    url: str

@dataclass(slots=True)
class AIModelConfig:

    provider: str

    model: str

    endpoint: str | None = None

def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def pretty_json(data: dict) -> None:
    print(json.dumps(data, indent=4))


def save_json(path: Path, data: dict):

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def load_json(path: Path):

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)
    
def parse_repository_url(
    repository: str,
) -> RepositoryConfig:

    repository = repository.strip()

    if repository.endswith("/"):

        repository = repository[:-1]

    if repository.startswith("https://github.com/"):

        repository = repository.replace(
            "https://github.com/",
            "",
            1,
        )

    elif repository.startswith("http://github.com/"):

        repository = repository.replace(
            "http://github.com/",
            "",
            1,
        )

    repository = repository.split("?")[0]

    repository = repository.split("#")[0]

    parts = repository.split("/")

    if len(parts) != 2:

        raise ValueError(
            "Expected owner/repository or GitHub URL."
        )

    owner, repo = parts

    return RepositoryConfig(

        owner=owner,

        repository=repo,

        url=f"https://github.com/{owner}/{repo}"

    )

ACTIVE_REPOSITORY = RepositoryConfig(

    owner="kennykrichardson",

    repository="kennykrichardson-portfolio",

    url="https://github.com/kennykrichardson/kennykrichardson-portfolio"

)

ACTIVE_MODEL = AIModelConfig(

    provider="huggingface",

    model="Qwen/Qwen2.5-7B-Instruct",

)

def set_active_repository(
    repository: str,
) -> RepositoryConfig:

    global ACTIVE_REPOSITORY

    ACTIVE_REPOSITORY = parse_repository_url(
        repository
    )

    return ACTIVE_REPOSITORY

def get_active_repository() -> RepositoryConfig:

    return ACTIVE_REPOSITORY

def set_active_model(
    provider: str,
    model: str,
    endpoint: str | None = None,
) -> AIModelConfig:

    global ACTIVE_MODEL

    ACTIVE_MODEL = AIModelConfig(
        provider=provider,
        model=model,
        endpoint=endpoint,
    )

    return ACTIVE_MODEL

def get_active_model() -> AIModelConfig:

    return ACTIVE_MODEL

# ==========================================================
# GraphQL Client
# ==========================================================


class GitHubGraphQLClient:

    def __init__(self):

        self.url = GRAPHQL_URL

        self.headers = HEADERS

    def execute(
        self,
        query: str,
        variables: dict | None = None,
    ) -> dict:

        payload = {
            "query": query,
            "variables": variables or {},
        }

        response = requests.post(
            self.url,
            headers=self.headers,
            json=payload,
            timeout=30,
        )

        if response.status_code == 401:
            raise AuthenticationError(
                "GitHub authentication failed."
            )

        if response.status_code == 403:
            raise RateLimitError(
                "GitHub rate limit exceeded."
            )

        if response.status_code != 200:
            raise GraphQLClientError(
                f"HTTP {response.status_code}"
            )

        data = response.json()

        if "errors" in data:
            raise QueryError(
                json.dumps(data["errors"], indent=4)
            )

        return data["data"]

    def paginate(
        self,
        query: str,
        variables: dict,
        connection_path: list[str],
    ):

        after = None

        while True:

            current = variables.copy()

            current["after"] = after

            result = self.execute(
                query,
                current,
            )

            connection = result

            for key in connection_path:
                connection = connection[key]

            for node in connection["nodes"]:
                yield node

            page = connection["pageInfo"]

            if not page["hasNextPage"]:
                break

            after = page["endCursor"]

    def get_rate_limit(self):

        query = """
        query{

            rateLimit{

                limit
                remaining
                cost
                resetAt

            }

        }
        """

        return self.execute(query)


# ==========================================================
# Shared Client
# ==========================================================

client = GitHubGraphQLClient()