"""
============================================================
ORZYN AI m2.0
Notebook 01 : Configuration
============================================================

Purpose
-------
Centralized project configuration.

Responsibilities
----------------
• Load environment variables
• Define project paths
• Configure GitHub GraphQL endpoint
• Configure HuggingFace endpoint
• Verify project directories
• Provide reusable configuration for every notebook

Author
------
Kenny Richardson

Project
-------
Orzyn AI m2.0
"""



from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv



# ---------------------------------------------------------
# Project Root
# ---------------------------------------------------------

PROJECT_ROOT: Final[Path] = Path.cwd().parent.parent.resolve()

BACKEND_DIR: Final[Path] = PROJECT_ROOT / "backend"

NOTEBOOK_DIR: Final[Path] = BACKEND_DIR / "notebooks"

DATA_DIR: Final[Path] = BACKEND_DIR / "data"

CACHE_DIR: Final[Path] = BACKEND_DIR / "cache"

EXPORT_DIR: Final[Path] = BACKEND_DIR / "exports"

MODEL_DIR: Final[Path] = BACKEND_DIR / "models"

ENV_FILE: Final[Path] = PROJECT_ROOT / ".env"



DIRECTORIES = (
    DATA_DIR,
    CACHE_DIR,
    EXPORT_DIR,
    MODEL_DIR,
)

for directory in DIRECTORIES:
    directory.mkdir(parents=True, exist_ok=True)



load_dotenv(ENV_FILE)



GITHUB_GRAPHQL_URL: Final = "https://api.github.com/graphql"

GITHUB_TOKEN: str | None = os.getenv("GITHUB_TOKEN")



HF_TOKEN: str | None = os.getenv("HF_TOKEN")



GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/vnd.github+json",
}

HF_HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}"
}



def validate_environment() -> bool:
    """
    Validate the Orzyn environment.

    Returns
    -------
    bool
        True if everything required exists.
    """

    success = True

    print("=" * 60)
    print("ORZYN AI m2.0")
    print("Environment Validation")
    print("=" * 60)

    if ENV_FILE.exists():
        print("✓ .env located")
    else:
        print("✗ .env missing")
        success = False

    if GITHUB_TOKEN:
        print("✓ GitHub Token Loaded")
    else:
        print("✗ GitHub Token Missing")
        success = False

    if HF_TOKEN:
        print("✓ HuggingFace Token Loaded")
    else:
        print("✗ HuggingFace Token Missing")
        success = False

    print()

    for directory in DIRECTORIES:
        if directory.exists():
            print(f"✓ {directory.name}")
        else:
            print(f"✗ {directory.name}")
            success = False

    print()

    print("Project Root")
    print(PROJECT_ROOT)

    print()

    if success:
        print("Environment Ready")
    else:
        print("Configuration Incomplete")

    return success



validate_environment()



CONFIG = {
    "project_root": PROJECT_ROOT,
    "backend": BACKEND_DIR,
    "notebooks": NOTEBOOK_DIR,
    "data": DATA_DIR,
    "cache": CACHE_DIR,
    "exports": EXPORT_DIR,
    "models": MODEL_DIR,
    "github_graphql": GITHUB_GRAPHQL_URL,
}



CONFIG






