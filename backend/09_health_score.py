from __future__ import annotations

from pathlib import Path
import sys

# Notebook directory
NOTEBOOK_DIR = Path.cwd().resolve()

# backend/
BACKEND_DIR = NOTEBOOK_DIR.parent.resolve()

# Common artifact directories
DATA_DIR = BACKEND_DIR / "data"
EXPORT_DIR = BACKEND_DIR / "exports"

# Ensure they exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from statistics import mean, median
from typing import Any, Iterable

from orzyn import (
    get_active_model,
    get_active_repository,
    load_json,
    parse_datetime,
)

REPOSITORY_KIND_KEYWORDS = {
    "student_portfolio": {
        "portfolio",
        "resume",
        "cv",
        "student",
        "personal",
        "showcase",
        "assignment",
        "homework",
        "coursework",
        "capstone",
    },
    "course_project": {
        "course",
        "class",
        "semester",
        "assignment",
        "homework",
        "lab",
        "project",
    },
    "hackathon": {
        "hackathon",
        "demo",
        "submission",
        "challenge",
        "winning",
    },
    "research_project": {
        "research",
        "paper",
        "experiment",
        "thesis",
        "benchmark",
    },
    "open_source_library": {
        "library",
        "package",
        "sdk",
        "toolkit",
        "module",
    },
    "framework": {
        "framework",
        "runtime",
        "platform",
        "engine",
    },
    "cli_tool": {
        "cli",
        "command line",
        "terminal",
        "shell",
    },
    "api_service": {
        "api",
        "backend",
        "server",
        "service",
        "microservice",
    },
    "desktop_app": {
        "desktop",
        "electron",
        "app",
        "gui",
    },
    "mobile_app": {
        "mobile",
        "android",
        "ios",
        "react native",
        "flutter",
    },
    "enterprise_internal": {
        "internal",
        "enterprise",
        "corporate",
        "company",
    },
}

GENERIC_TOPICS = {
    "github",
    "repository",
    "code",
    "project",
    "software",
    "application",
    "app",
}

GENERIC_MESSAGE_PATTERNS = {
    "update",
    "updates",
    "fix",
    "misc",
    "wip",
    "temp",
    "test",
    "typo",
    "changes",
    "stuff",
}

class RepositoryKind(str, Enum):
    STUDENT_PORTFOLIO = "student_portfolio"
    COURSE_PROJECT = "course_project"
    HACKATHON = "hackathon"
    RESEARCH_PROJECT = "research_project"
    OPEN_SOURCE_LIBRARY = "open_source_library"
    FRAMEWORK = "framework"
    CLI_TOOL = "cli_tool"
    API_SERVICE = "api_service"
    DESKTOP_APP = "desktop_app"
    MOBILE_APP = "mobile_app"
    ENTERPRISE_INTERNAL = "enterprise_internal"
    UNKNOWN = "unknown"


class MaturityLevel(str, Enum):
    EXPERIMENTAL = "experimental"
    EARLY = "early"
    GROWING = "growing"
    MATURE = "mature"
    LEGACY = "legacy"


class ScoreBand(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    WEAK = "weak"
    UNKNOWN = "unknown"

@dataclass(slots=True)
class RepositorySnapshot:
    owner: str
    repository: str
    url: str
    description: str | None = None
    homepage: str | None = None
    default_branch: str | None = None
    private: bool = False
    archived: bool = False
    fork: bool = False
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    topics: list[str] = field(default_factory=list)
    license: str | None = None
    language_breakdown: dict[str, float] = field(default_factory=dict)
    created_at: datetime | None = None
    pushed_at: datetime | None = None


@dataclass(slots=True)
class HealthInputs:
    repository: Any | None = None
    commits: list[Any] = field(default_factory=list)
    pull_requests: list[Any] = field(default_factory=list)
    issues: list[Any] = field(default_factory=list)
    developers: list[Any] = field(default_factory=list)
    releases: list[Any] = field(default_factory=list)
    files: Any | None = None
    readme_text: str | None = None
    ci: Any | None = None


@dataclass(slots=True)
class MetricResult:
    name: str
    score: float | None
    confidence: float
    available: bool
    weight: float
    value: Any = None
    explanation: str = ""
    evidence: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CategoryResult:
    name: str
    score: float | None
    weight: float
    confidence: float
    metrics: list[MetricResult] = field(default_factory=list)
    explanation: str = ""


@dataclass(slots=True)
class HealthReport:
    repository: RepositorySnapshot
    kind: RepositoryKind
    maturity: MaturityLevel
    overall_score: float
    overall_confidence: float
    categories: list[CategoryResult]
    strengths: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    missing_signals: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

@dataclass(slots=True)
class ScoringProfile:
    category_weights: dict[str, float]
    expected_signals: dict[str, float]
    maturity_thresholds: dict[str, float]

def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def pick(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def to_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            dt = parse_datetime(value)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                return None
    return None


def days_since(value: Any) -> int | None:
    dt = to_datetime(value)
    if dt is None:
        return None
    now = datetime.now(timezone.utc)
    return max(0, (now - dt.astimezone(timezone.utc)).days)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def tokenize_text(value: Any) -> set[str]:
    text = normalize_text(value).lower()
    return {token for token in re.split(r"[^a-z0-9]+", text) if token}


def score_linear(value: float, minimum: float, maximum: float) -> float:
    if value <= minimum:
        return 0.0
    if value >= maximum:
        return 100.0
    return 100.0 * safe_divide(value - minimum, maximum - minimum, 0.0)


def score_inverse_days(days_value: int | None, best: int, worst: int) -> float:
    if days_value is None:
        return 0.0
    if days_value <= best:
        return 100.0
    if days_value >= worst:
        return 0.0
    return 100.0 * safe_divide(worst - days_value, worst - best, 0.0)


def score_presence(value: Any, present_score: float = 100.0, missing_score: float = 35.0) -> float:
    return present_score if value not in (None, "", [], {}, ()) else missing_score


def score_count(value: int, good: int, excellent: int, low_score: float = 35.0) -> float:
    if value <= 0:
        return low_score
    if value >= excellent:
        return 100.0
    if value <= good:
        return 60.0 + 40.0 * safe_divide(value, good, 0.0)
    return 80.0 + 20.0 * safe_divide(value - good, excellent - good, 0.0)


def score_ratio(ratio: float | None, low: float, high: float) -> float:
    if ratio is None:
        return 0.0
    return clamp(score_linear(ratio, low, high))


def weighted_mean(values: Iterable[tuple[float, float]]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for score, weight in values:
        numerator += score * weight
        denominator += weight
    if denominator == 0:
        return None
    return numerator / denominator


def serialize_dataclass(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [serialize_dataclass(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_dataclass(item) for key, item in value.items()}
    return value

def find_artifact_path(kind: str, keyword_sets: list[tuple[str, ...]] | None = None) -> Path | None:
    search_roots = [DATA_DIR, EXPORT_DIR, BACKEND_DIR]
    keyword_sets = keyword_sets or [(kind.lower(),)]
    candidates: list[Path] = []

    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            lowered = path.name.lower()
            for keywords in keyword_sets:
                if all(keyword.lower() in lowered for keyword in keywords):
                    candidates.append(path)
                    break

    if not candidates:
        return None

    return max(candidates, key=lambda path: path.stat().st_mtime)


def load_json_artifact(kind: str, keyword_sets: list[tuple[str, ...]] | None = None, default: Any = None) -> Any:
    path = find_artifact_path(kind, keyword_sets)
    if path is None:
        return default
    try:
        return load_json(path)
    except Exception:
        return default


def pull_from_globals(*names: str, default: Any = None) -> Any:
    for name in names:
        if name in globals() and globals()[name] is not None:
            return globals()[name]
    return default


def load_health_inputs() -> HealthInputs:
    repository = pull_from_globals(
        "repository_profile",
        "repo_profile",
        "repository_data",
        "repository",
        default=None,
    )
    if repository is None:
        repository = load_json_artifact(
            "repository",
            keyword_sets=[
                ("repository", "profile"),
                ("repo", "profile"),
                ("repository",),
            ],
            default=None,
        )

    commits = pull_from_globals("commits", "commit_profiles", default=None)
    if commits is None:
        commits = load_json_artifact(
            "commits",
            keyword_sets=[("commit",), ("commits",)],
            default=[],
        ) or []

    pull_requests = pull_from_globals("pull_requests", "prs", default=None)
    if pull_requests is None:
        pull_requests = load_json_artifact(
            "pull_requests",
            keyword_sets=[("pull", "request"), ("pr",)],
            default=[],
        ) or []

    issues = pull_from_globals("issues", default=None)
    if issues is None:
        issues = load_json_artifact(
            "issues",
            keyword_sets=[("issue",), ("issues",)],
            default=[],
        ) or []

    developers = pull_from_globals("developers", "contributors", default=None)
    if developers is None:
        developers = load_json_artifact(
            "developers",
            keyword_sets=[("developer",), ("contributor",)],
            default=[],
        ) or []

    releases = pull_from_globals("releases", default=None)
    if releases is None:
        releases = load_json_artifact(
            "releases",
            keyword_sets=[("release",), ("releases",)],
            default=[],
        ) or []

    files = pull_from_globals("files", "file_tree", "tree", default=None)
    if files is None:
        files = load_json_artifact(
            "files",
            keyword_sets=[("file", "tree"), ("tree",), ("snapshot",)],
            default=None,
        )

    readme_text = pull_from_globals("readme_text", "readme", default=None)
    if readme_text is None:
        readme_text = load_json_artifact(
            "readme",
            keyword_sets=[("readme",)],
            default=None,
        )
        if isinstance(readme_text, dict):
            readme_text = readme_text.get("content") or readme_text.get("text")

    ci = pull_from_globals("ci", "ci_data", "workflow_data", default=None)
    if ci is None:
        ci = load_json_artifact(
            "ci",
            keyword_sets=[("workflow",), ("ci",), ("pipeline",)],
            default=None,
        )

    return HealthInputs(
        repository=repository,
        commits=as_list(commits),
        pull_requests=as_list(pull_requests),
        issues=as_list(issues),
        developers=as_list(developers),
        releases=as_list(releases),
        files=files,
        readme_text=readme_text if isinstance(readme_text, str) else None,
        ci=ci,
    )

def normalize_repository_snapshot(raw_repository: Any | None) -> RepositorySnapshot:
    active_repo = get_active_repository()
    raw_repository = raw_repository or {}

    repo = RepositorySnapshot(
        owner=normalize_text(pick(raw_repository, "owner", active_repo.owner)) or active_repo.owner,
        repository=normalize_text(pick(raw_repository, "name", active_repo.repository)) or active_repo.repository,
        url=normalize_text(pick(raw_repository, "url", active_repo.url)) or active_repo.url,
        description=pick(raw_repository, "description"),
        homepage=pick(raw_repository, "homepageUrl", pick(raw_repository, "homepage")),
        default_branch=pick(raw_repository, "defaultBranchRef"),
        private=bool(pick(raw_repository, "isPrivate", False)),
        archived=bool(pick(raw_repository, "isArchived", False)),
        fork=bool(pick(raw_repository, "isFork", False)),
        stars=int(pick(raw_repository, "stargazerCount", pick(raw_repository, "stars", 0)) or 0),
        forks=int(pick(raw_repository, "forkCount", pick(raw_repository, "forks", 0)) or 0),
        watchers=int(pick(raw_repository, "watchers", {}).get("totalCount", pick(raw_repository, "watchers", 0)) if isinstance(pick(raw_repository, "watchers", {}), dict) else pick(raw_repository, "watchers", 0) or 0),
        topics=[],
        license=pick(raw_repository, "licenseInfo", {}).get("name") if isinstance(pick(raw_repository, "licenseInfo", {}), dict) else pick(raw_repository, "license"),
        language_breakdown={},
        created_at=to_datetime(pick(raw_repository, "createdAt")),
        pushed_at=to_datetime(pick(raw_repository, "pushedAt")),
    )

    topics_value = pick(raw_repository, "repositoryTopics", None)
    if isinstance(topics_value, dict):
        nodes = topics_value.get("nodes", [])
        repo.topics = [
            normalize_text(pick(node, "topic", {}).get("name") if isinstance(pick(node, "topic", {}), dict) else pick(node, "name"))
            for node in nodes
            if normalize_text(pick(node, "topic", {}).get("name") if isinstance(pick(node, "topic", {}), dict) else pick(node, "name"))
        ]
    else:
        raw_topics = pick(raw_repository, "topics", [])
        repo.topics = [normalize_text(topic) for topic in as_list(raw_topics) if normalize_text(topic)]

    languages_value = pick(raw_repository, "languages", None)
    if isinstance(languages_value, dict):
        edges = languages_value.get("edges", [])
        total = sum((pick(edge, "size", 0) or 0) for edge in edges)
        breakdown: dict[str, float] = {}
        for edge in edges:
            node = pick(edge, "node", {})
            language = normalize_text(pick(node, "name"))
            size = float(pick(edge, "size", 0) or 0)
            if language and total > 0:
                breakdown[language] = round(100.0 * size / total, 2)
        repo.language_breakdown = breakdown
    elif isinstance(languages_value, dict):
        repo.language_breakdown = {normalize_text(k): float(v) for k, v in languages_value.items() if normalize_text(k)}
    elif isinstance(languages_value, list):
        breakdown = {}
        for item in languages_value:
            language = normalize_text(pick(item, "name"))
            pct = pick(item, "percentage", pick(item, "share", None))
            if language and pct is not None:
                breakdown[language] = float(pct)
        repo.language_breakdown = breakdown

    return repo


def current_context_snapshot() -> tuple[RepositorySnapshot, HealthInputs]:
    inputs = load_health_inputs()
    repository = normalize_repository_snapshot(inputs.repository)
    return repository, inputs

def repository_kind_signals(repository: RepositorySnapshot) -> set[str]:
    signals = set(tokenize_text(repository.repository))
    signals |= tokenize_text(repository.description)
    signals |= {topic.lower() for topic in repository.topics}
    return signals


def classify_repository_kind(repository: RepositorySnapshot) -> RepositoryKind:
    if repository.private:
        return RepositoryKind.ENTERPRISE_INTERNAL

    signals = repository_kind_signals(repository)

    if signals & REPOSITORY_KIND_KEYWORDS["student_portfolio"]:
        return RepositoryKind.STUDENT_PORTFOLIO
    if signals & REPOSITORY_KIND_KEYWORDS["course_project"]:
        return RepositoryKind.COURSE_PROJECT
    if signals & REPOSITORY_KIND_KEYWORDS["hackathon"]:
        return RepositoryKind.HACKATHON
    if signals & REPOSITORY_KIND_KEYWORDS["research_project"]:
        return RepositoryKind.RESEARCH_PROJECT
    if signals & REPOSITORY_KIND_KEYWORDS["desktop_app"]:
        return RepositoryKind.DESKTOP_APP
    if signals & REPOSITORY_KIND_KEYWORDS["mobile_app"]:
        return RepositoryKind.MOBILE_APP
    if signals & REPOSITORY_KIND_KEYWORDS["cli_tool"]:
        return RepositoryKind.CLI_TOOL
    if signals & REPOSITORY_KIND_KEYWORDS["api_service"]:
        return RepositoryKind.API_SERVICE
    if signals & REPOSITORY_KIND_KEYWORDS["framework"]:
        return RepositoryKind.FRAMEWORK
    if signals & REPOSITORY_KIND_KEYWORDS["open_source_library"]:
        return RepositoryKind.OPEN_SOURCE_LIBRARY

    if repository.stars >= 500 and repository.forks >= 50:
        return RepositoryKind.OPEN_SOURCE_LIBRARY

    return RepositoryKind.UNKNOWN


def infer_maturity_level(repository: RepositorySnapshot, inputs: HealthInputs) -> MaturityLevel:
    age_days = days_since(repository.created_at) or 0
    commit_count = len(inputs.commits)
    pr_count = len(inputs.pull_requests)
    issue_count = len(inputs.issues)
    release_count = len(inputs.releases)

    if age_days < 30 and commit_count < 10:
        return MaturityLevel.EXPERIMENTAL
    if age_days < 120 or commit_count < 40:
        return MaturityLevel.EARLY
    if age_days < 365 or (commit_count >= 40 and (pr_count + issue_count) >= 20):
        return MaturityLevel.GROWING
    if release_count >= 3 or (commit_count >= 100 and (pr_count + issue_count) >= 50):
        return MaturityLevel.MATURE
    return MaturityLevel.MATURE if age_days >= 365 else MaturityLevel.GROWING

WEIGHT_PROFILES: dict[RepositoryKind, dict[str, float]] = {
    RepositoryKind.STUDENT_PORTFOLIO: {
        "foundation": 25,
        "documentation": 25,
        "activity": 20,
        "maintenance": 15,
        "collaboration": 5,
        "release": 0,
        "code_surface": 10,
    },
    RepositoryKind.COURSE_PROJECT: {
        "foundation": 20,
        "documentation": 25,
        "activity": 15,
        "maintenance": 15,
        "collaboration": 5,
        "release": 0,
        "code_surface": 20,
    },
    RepositoryKind.HACKATHON: {
        "foundation": 20,
        "documentation": 20,
        "activity": 20,
        "maintenance": 10,
        "collaboration": 5,
        "release": 0,
        "code_surface": 25,
    },
    RepositoryKind.RESEARCH_PROJECT: {
        "foundation": 15,
        "documentation": 20,
        "activity": 10,
        "maintenance": 15,
        "collaboration": 10,
        "release": 5,
        "code_surface": 25,
    },
    RepositoryKind.OPEN_SOURCE_LIBRARY: {
        "foundation": 15,
        "documentation": 15,
        "activity": 15,
        "maintenance": 15,
        "collaboration": 10,
        "release": 15,
        "code_surface": 15,
    },
    RepositoryKind.FRAMEWORK: {
        "foundation": 10,
        "documentation": 15,
        "activity": 15,
        "maintenance": 15,
        "collaboration": 10,
        "release": 15,
        "code_surface": 20,
    },
    RepositoryKind.CLI_TOOL: {
        "foundation": 15,
        "documentation": 20,
        "activity": 15,
        "maintenance": 15,
        "collaboration": 5,
        "release": 10,
        "code_surface": 20,
    },
    RepositoryKind.API_SERVICE: {
        "foundation": 10,
        "documentation": 15,
        "activity": 15,
        "maintenance": 20,
        "collaboration": 10,
        "release": 10,
        "code_surface": 20,
    },
    RepositoryKind.DESKTOP_APP: {
        "foundation": 15,
        "documentation": 15,
        "activity": 15,
        "maintenance": 15,
        "collaboration": 5,
        "release": 10,
        "code_surface": 25,
    },
    RepositoryKind.MOBILE_APP: {
        "foundation": 15,
        "documentation": 15,
        "activity": 15,
        "maintenance": 15,
        "collaboration": 5,
        "release": 10,
        "code_surface": 25,
    },
    RepositoryKind.ENTERPRISE_INTERNAL: {
        "foundation": 10,
        "documentation": 10,
        "activity": 10,
        "maintenance": 25,
        "collaboration": 10,
        "release": 5,
        "code_surface": 30,
    },
    RepositoryKind.UNKNOWN: {
        "foundation": 20,
        "documentation": 20,
        "activity": 15,
        "maintenance": 15,
        "collaboration": 10,
        "release": 10,
        "code_surface": 10,
    },
}

def choose_weight_profile(kind: RepositoryKind) -> dict[str, float]:
    return dict(WEIGHT_PROFILES.get(kind, WEIGHT_PROFILES[RepositoryKind.UNKNOWN]))


def normalize_weight_profile(weights: dict[str, float], available_categories: set[str]) -> dict[str, float]:
    filtered = {name: weight for name, weight in weights.items() if name in available_categories and weight > 0}
    total = sum(filtered.values())
    if total == 0:
        return filtered
    return {name: (weight / total) * 100.0 for name, weight in filtered.items()}

def commit_timestamps(items: list[Any]) -> list[datetime]:
    timestamps: list[datetime] = []
    for item in items:
        timestamp = to_datetime(
            pick(item, "committed_at")
            or pick(item, "committedAt")
            or pick(item, "created_at")
            or pick(item, "createdAt")
            or pick(item, "date")
        )
        if timestamp is not None:
            timestamps.append(timestamp)
    return timestamps


def issue_timestamps(items: list[Any], field_name: str) -> list[datetime]:
    timestamps: list[datetime] = []
    for item in items:
        timestamp = to_datetime(pick(item, field_name))
        if timestamp is not None:
            timestamps.append(timestamp)
    return timestamps


def distinct_contributors(commits: list[Any], developers: list[Any]) -> int:
    authors = set()
    for commit in commits:
        author = normalize_text(pick(commit, "author") or pick(commit, "author_name") or pick(commit, "name"))
        if author:
            authors.add(author.lower())
        username = normalize_text(pick(commit, "username") or pick(commit, "login"))
        if username:
            authors.add(username.lower())
    for dev in developers:
        username = normalize_text(pick(dev, "username") or pick(dev, "login"))
        if username:
            authors.add(username.lower())
    return len(authors)


def count_generic_messages(commits: list[Any]) -> tuple[int, int]:
    total = 0
    specific = 0
    for commit in commits:
        message = normalize_text(
            pick(commit, "message")
            or pick(commit, "messageHeadline")
            or pick(commit, "message_headline")
            or pick(commit, "title")
        )
        if not message:
            continue
        total += 1
        words = tokenize_text(message)
        first_word = next(iter(words), "")
        if len(message) >= 12 and first_word not in GENERIC_MESSAGE_PATTERNS:
            specific += 1
    return specific, total


def has_readme_text(inputs: HealthInputs) -> bool:
    text = normalize_text(inputs.readme_text)
    return bool(text)


def readme_sections_score(readme_text: str | None) -> MetricResult:
    if not readme_text:
        return MetricResult(
            name="readme_sections",
            score=None,
            confidence=30.0,
            available=False,
            weight=1.0,
            value=None,
            explanation="No README text was provided, so section analysis is unavailable.",
            evidence=[],
        )

    text = readme_text.lower()
    indicators = {
        "installation": ["install", "setup", "getting started", "quickstart"],
        "usage": ["usage", "examples", "example", "how to use"],
        "contribution": ["contributing", "contribution", "pull request"],
        "license": ["license", "licence"],
    }
    matches = 0
    evidence: list[str] = []
    for section, phrases in indicators.items():
        if any(phrase in text for phrase in phrases):
            matches += 1
            evidence.append(section)

    score = 40.0 + 15.0 * matches
    return MetricResult(
        name="readme_sections",
        score=clamp(score),
        confidence=88.0,
        available=True,
        weight=1.0,
        value={"matched_sections": matches},
        explanation="README was checked for core project sections.",
        evidence=evidence,
    )

def score_foundation(repository: RepositorySnapshot, inputs: HealthInputs) -> CategoryResult:
    metrics: list[MetricResult] = []

    description = normalize_text(repository.description)
    homepage = normalize_text(repository.homepage)
    license_name = normalize_text(repository.license)
    topics = repository.topics

    metrics.append(
        MetricResult(
            name="description_presence",
            score=score_presence(description, 100.0, 25.0),
            confidence=100.0 if description else 45.0,
            available=True,
            weight=1.0,
            value=description,
            explanation="Repository description helps establish intent and scope.",
            evidence=[description] if description else [],
        )
    )
    metrics.append(
        MetricResult(
            name="homepage_presence",
            score=score_presence(homepage, 100.0, 35.0),
            confidence=100.0 if homepage else 40.0,
            available=True,
            weight=1.0,
            value=homepage,
            explanation="Homepage or project site improves discoverability.",
            evidence=[homepage] if homepage else [],
        )
    )
    metrics.append(
        MetricResult(
            name="license_presence",
            score=score_presence(license_name, 100.0, 40.0),
            confidence=100.0 if license_name else 40.0,
            available=True,
            weight=1.0,
            value=license_name,
            explanation="A license clarifies reuse, distribution, and contribution terms.",
            evidence=[license_name] if license_name else [],
        )
    )
    metrics.append(
        MetricResult(
            name="topic_clarity",
            score=score_count(len([topic for topic in topics if topic.lower() not in GENERIC_TOPICS]), good=1, excellent=4, low_score=40.0),
            confidence=100.0 if topics else 55.0,
            available=True,
            weight=1.0,
            value=topics,
            explanation="Meaningful topics improve repository discoverability and intent clarity.",
            evidence=topics[:5],
        )
    )

    branch = normalize_text(repository.default_branch)
    metrics.append(
        MetricResult(
            name="default_branch_presence",
            score=score_presence(branch, 100.0, 45.0),
            confidence=100.0 if branch else 50.0,
            available=True,
            weight=1.0,
            value=branch,
            explanation="A clearly defined default branch is part of repository hygiene.",
            evidence=[branch] if branch else [],
        )
    )

    score = weighted_mean((metric.score or 0.0, metric.weight) for metric in metrics if metric.available)
    confidence = weighted_mean((metric.confidence, metric.weight) for metric in metrics if metric.available) or 0.0
    return CategoryResult(
        name="foundation",
        score=score,
        weight=1.0,
        confidence=confidence,
        metrics=metrics,
        explanation="Metadata completeness and repository identity signals.",
    )

def score_activity(repository: RepositorySnapshot, inputs: HealthInputs) -> CategoryResult:
    metrics: list[MetricResult] = []
    commits = inputs.commits

    if commits:
        timestamps = commit_timestamps(commits)
        last_commit_days = days_since(max(timestamps)) if timestamps else None
        first_commit_days = days_since(min(timestamps)) if timestamps else None
        age_days = max(1, (days_since(repository.created_at) or 1))
        active_days = max(1, (first_commit_days or 1) - (last_commit_days or 0) + 1) if first_commit_days is not None and last_commit_days is not None else age_days
        commit_count = len(commits)
        commits_per_month = commit_count / max(1.0, age_days / 30.0)

        specific_messages, total_messages = count_generic_messages(commits)
        message_specificity = safe_divide(specific_messages, total_messages, 0.0) if total_messages else None

        metrics.append(
            MetricResult(
                name="commit_recency",
                score=score_inverse_days(last_commit_days, best=7, worst=180),
                confidence=100.0 if last_commit_days is not None else 40.0,
                available=last_commit_days is not None,
                weight=1.0,
                value=last_commit_days,
                explanation="Recent commits indicate active maintenance.",
                evidence=[f"days_since_last_commit={last_commit_days}"] if last_commit_days is not None else [],
            )
        )
        metrics.append(
            MetricResult(
                name="commit_cadence",
                score=score_count(int(commits_per_month), good=2, excellent=18, low_score=30.0),
                confidence=95.0 if commit_count >= 3 else 55.0,
                available=True,
                weight=1.0,
                value=round(commits_per_month, 2),
                explanation="Commit cadence shows whether the repository is moving at a healthy pace.",
                evidence=[f"commits_per_month={round(commits_per_month, 2)}"],
            )
        )
        metrics.append(
            MetricResult(
                name="commit_message_specificity",
                score=score_ratio(message_specificity, low=0.35, high=0.9),
                confidence=90.0 if total_messages else 45.0,
                available=total_messages > 0,
                weight=1.0,
                value=message_specificity,
                explanation="Specific commit messages make history easier to inspect and trust.",
                evidence=[f"specific_messages={specific_messages}/{total_messages}"] if total_messages else [],
            )
        )
    else:
        metrics.append(
            MetricResult(
                name="commit_recency",
                score=None,
                confidence=20.0,
                available=False,
                weight=1.0,
                value=None,
                explanation="No commit dataset was available.",
                evidence=[],
            )
        )
        metrics.append(
            MetricResult(
                name="commit_cadence",
                score=None,
                confidence=20.0,
                available=False,
                weight=1.0,
                value=None,
                explanation="No commit dataset was available.",
                evidence=[],
            )
        )
        metrics.append(
            MetricResult(
                name="commit_message_specificity",
                score=None,
                confidence=20.0,
                available=False,
                weight=1.0,
                value=None,
                explanation="No commit dataset was available.",
                evidence=[],
            )
        )

    score = weighted_mean((metric.score or 0.0, metric.weight) for metric in metrics if metric.available)
    confidence = weighted_mean((metric.confidence, metric.weight) for metric in metrics if metric.available) or 0.0
    return CategoryResult(
        name="activity",
        score=score,
        weight=1.0,
        confidence=confidence,
        metrics=metrics,
        explanation="Commit cadence, recency, and message quality.",
    )

def score_collaboration(repository: RepositorySnapshot, inputs: HealthInputs, kind: RepositoryKind) -> CategoryResult:
    metrics: list[MetricResult] = []
    pull_requests = inputs.pull_requests
    developers = inputs.developers
    issues = inputs.issues

    contributor_count = distinct_contributors(inputs.commits, developers)
    collaboration_expected = kind not in {
        RepositoryKind.STUDENT_PORTFOLIO,
        RepositoryKind.COURSE_PROJECT,
        RepositoryKind.HACKATHON,
    }

    if contributor_count > 0:
        contributor_score = score_count(contributor_count, good=2, excellent=6, low_score=45.0)
        if not collaboration_expected:
            contributor_score = max(contributor_score, 70.0)
        metrics.append(
            MetricResult(
                name="contributor_presence",
                score=contributor_score,
                confidence=95.0,
                available=True,
                weight=1.0,
                value=contributor_count,
                explanation="Contributor coverage helps reveal whether the repo has a maintainable bus factor.",
                evidence=[f"contributors={contributor_count}"],
            )
        )
    else:
        metrics.append(
            MetricResult(
                name="contributor_presence",
                score=None,
                confidence=30.0,
                available=False,
                weight=1.0,
                value=None,
                explanation="Contributor data was unavailable.",
                evidence=[],
            )
        )

    if pull_requests:
        review_counts = []
        merged_counts = 0
        for pr in pull_requests:
            review_count = int(pick(pr, "reviews", {}).get("totalCount", 0) if isinstance(pick(pr, "reviews", {}), dict) else pick(pr, "review_count", 0) or 0)
            review_counts.append(review_count)
            merged_at = to_datetime(pick(pr, "mergedAt") or pick(pr, "merged_at"))
            if merged_at is not None:
                merged_counts += 1
        review_coverage = safe_divide(sum(1 for count in review_counts if count > 0), len(review_counts), 0.0)
        merge_ratio = safe_divide(merged_counts, len(pull_requests), 0.0)
        metrics.append(
            MetricResult(
                name="pr_review_coverage",
                score=score_ratio(review_coverage, low=0.15, high=0.8),
                confidence=95.0,
                available=True,
                weight=1.0,
                value=review_coverage,
                explanation="Review coverage indicates how much human scrutiny pull requests receive.",
                evidence=[f"review_coverage={round(review_coverage * 100, 2)}%"],
            )
        )
        metrics.append(
            MetricResult(
                name="pr_merge_ratio",
                score=score_ratio(merge_ratio, low=0.35, high=0.9),
                confidence=90.0,
                available=True,
                weight=1.0,
                value=merge_ratio,
                explanation="A healthy merge ratio suggests pull requests are being handled rather than abandoned.",
                evidence=[f"merge_ratio={round(merge_ratio * 100, 2)}%"],
            )
        )
    else:
        if collaboration_expected:
            metrics.append(
                MetricResult(
                    name="pr_review_coverage",
                    score=None,
                    confidence=20.0,
                    available=False,
                    weight=1.0,
                    value=None,
                    explanation="No pull request dataset was available.",
                    evidence=[],
                )
            )
            metrics.append(
                MetricResult(
                    name="pr_merge_ratio",
                    score=None,
                    confidence=20.0,
                    available=False,
                    weight=1.0,
                    value=None,
                    explanation="No pull request dataset was available.",
                    evidence=[],
                )
            )
        else:
            metrics.append(
                MetricResult(
                    name="pr_review_coverage",
                    score=75.0,
                    confidence=35.0,
                    available=True,
                    weight=1.0,
                    value=None,
                    explanation="Small student or course repositories are not expected to have formal review pipelines.",
                    evidence=[],
                )
            )
            metrics.append(
                MetricResult(
                    name="pr_merge_ratio",
                    score=75.0,
                    confidence=35.0,
                    available=True,
                    weight=1.0,
                    value=None,
                    explanation="Small student or course repositories are not expected to have formal release-style pull request discipline.",
                    evidence=[],
                )
            )

    issue_assignment_ratio = None
    if issues:
        assigned = 0
        for issue in issues:
            assignees = pick(issue, "assignees", [])
            if isinstance(assignees, dict):
                nodes = assignees.get("nodes", [])
                assigned += 1 if nodes else 0
            else:
                assigned += 1 if as_list(assignees) else 0
        issue_assignment_ratio = safe_divide(assigned, len(issues), 0.0)
        metrics.append(
            MetricResult(
                name="issue_assignment_coverage",
                score=score_ratio(issue_assignment_ratio, low=0.15, high=0.8),
                confidence=90.0,
                available=True,
                weight=1.0,
                value=issue_assignment_ratio,
                explanation="Assigned issues are easier to triage and resolve.",
                evidence=[f"assigned_issues={assigned}/{len(issues)}"],
            )
        )
    else:
        if collaboration_expected:
            metrics.append(
                MetricResult(
                    name="issue_assignment_coverage",
                    score=None,
                    confidence=20.0,
                    available=False,
                    weight=1.0,
                    value=None,
                    explanation="No issue dataset was available.",
                    evidence=[],
                )
            )
        else:
            metrics.append(
                MetricResult(
                    name="issue_assignment_coverage",
                    score=70.0,
                    confidence=35.0,
                    available=True,
                    weight=1.0,
                    value=None,
                    explanation="Student or course repositories are not expected to maintain a heavy issue workflow.",
                    evidence=[],
                )
            )

    score = weighted_mean((metric.score or 0.0, metric.weight) for metric in metrics if metric.available)
    confidence = weighted_mean((metric.confidence, metric.weight) for metric in metrics if metric.available) or 0.0
    return CategoryResult(
        name="collaboration",
        score=score,
        weight=1.0,
        confidence=confidence,
        metrics=metrics,
        explanation="Pull request and contributor collaboration signals.",
    )

def score_maintenance(repository: RepositorySnapshot, inputs: HealthInputs) -> CategoryResult:
    metrics: list[MetricResult] = []

    pushed_days = days_since(repository.pushed_at)
    metrics.append(
        MetricResult(
            name="push_recency",
            score=score_inverse_days(pushed_days, best=7, worst=365),
            confidence=100.0 if pushed_days is not None else 45.0,
            available=pushed_days is not None,
            weight=1.0,
            value=pushed_days,
            explanation="Recent pushes are a general sign that the repository is still being maintained.",
            evidence=[f"days_since_last_push={pushed_days}"] if pushed_days is not None else [],
        )
    )

    issues = inputs.issues
    if issues:
        closed = 0
        stale_open = 0
        issue_dates = issue_timestamps(issues, "createdAt") + issue_timestamps(issues, "created_at")
        now = datetime.now(timezone.utc)
        for issue in issues:
            state = normalize_text(pick(issue, "state")).upper()
            if state == "CLOSED":
                closed += 1
            created = to_datetime(pick(issue, "createdAt") or pick(issue, "created_at"))
            closed_at = to_datetime(pick(issue, "closedAt") or pick(issue, "closed_at"))
            if created is not None and closed_at is None and (now - created.astimezone(timezone.utc)).days >= 90:
                stale_open += 1

        closure_rate = safe_divide(closed, len(issues), 0.0)
        stale_rate = safe_divide(stale_open, len(issues), 0.0)

        metrics.append(
            MetricResult(
                name="issue_closure_rate",
                score=score_ratio(closure_rate, low=0.3, high=0.9),
                confidence=95.0,
                available=True,
                weight=1.0,
                value=closure_rate,
                explanation="Closed issues indicate the project is resolving reported problems.",
                evidence=[f"closed={closed}/{len(issues)}"],
            )
        )
        metrics.append(
            MetricResult(
                name="stale_issue_rate",
                score=clamp(100.0 - (stale_rate * 120.0)),
                confidence=90.0,
                available=True,
                weight=1.0,
                value=stale_rate,
                explanation="Old open issues are a backlog pressure signal.",
                evidence=[f"stale_open={stale_open}/{len(issues)}"],
            )
        )
    else:
        metrics.append(
            MetricResult(
                name="issue_closure_rate",
                score=68.0 if kind_is_student_or_course(repository) else None,
                confidence=35.0 if kind_is_student_or_course(repository) else 20.0,
                available=kind_is_student_or_course(repository),
                weight=1.0,
                value=None,
                explanation="No issue dataset was available.",
                evidence=[],
            )
        )
        metrics.append(
            MetricResult(
                name="stale_issue_rate",
                score=68.0 if kind_is_student_or_course(repository) else None,
                confidence=35.0 if kind_is_student_or_course(repository) else 20.0,
                available=kind_is_student_or_course(repository),
                weight=1.0,
                value=None,
                explanation="No issue dataset was available.",
                evidence=[],
            )
        )

    score = weighted_mean((metric.score or 0.0, metric.weight) for metric in metrics if metric.available)
    confidence = weighted_mean((metric.confidence, metric.weight) for metric in metrics if metric.available) or 0.0
    return CategoryResult(
        name="maintenance",
        score=score,
        weight=1.0,
        confidence=confidence,
        metrics=metrics,
        explanation="Issue handling and freshness signals.",
    )

def kind_is_student_or_course(repository: RepositorySnapshot) -> bool:
    signals = repository_kind_signals(repository)
    if repository.private:
        return False
    return bool(signals & (REPOSITORY_KIND_KEYWORDS["student_portfolio"] | REPOSITORY_KIND_KEYWORDS["course_project"] | REPOSITORY_KIND_KEYWORDS["hackathon"]))

def score_documentation(repository: RepositorySnapshot, inputs: HealthInputs, kind: RepositoryKind) -> CategoryResult:
    metrics: list[MetricResult] = []

    readme_text = normalize_text(inputs.readme_text)
    readme_available = bool(readme_text)

    metrics.append(
        MetricResult(
            name="readme_presence",
            score=score_presence(readme_text, 100.0, 40.0),
            confidence=100.0 if readme_available else 30.0,
            available=True,
            weight=1.0,
            value=bool(readme_text),
            explanation="A README is the most basic entry point for a repository.",
            evidence=["README provided"] if readme_available else [],
        )
    )

    metrics.append(readme_sections_score(inputs.readme_text))

    description = normalize_text(repository.description)
    metrics.append(
        MetricResult(
            name="project_summary_quality",
            score=clamp(40.0 + min(60.0, len(description) * 1.5)) if description else 30.0,
            confidence=95.0 if description else 40.0,
            available=True,
            weight=1.0,
            value=len(description) if description else 0,
            explanation="A clear description helps users understand the project quickly.",
            evidence=[description] if description else [],
        )
    )

    homepage = normalize_text(repository.homepage)
    metrics.append(
        MetricResult(
            name="homepage_or_demo",
            score=score_presence(homepage, 100.0, 45.0),
            confidence=100.0 if homepage else 40.0,
            available=True,
            weight=1.0,
            value=homepage,
            explanation="A homepage or live demo improves project discoverability.",
            evidence=[homepage] if homepage else [],
        )
    )

    score = weighted_mean((metric.score or 0.0, metric.weight) for metric in metrics if metric.available)
    confidence = weighted_mean((metric.confidence, metric.weight) for metric in metrics if metric.available) or 0.0
    return CategoryResult(
        name="documentation",
        score=score,
        weight=1.0,
        confidence=confidence,
        metrics=metrics,
        explanation="README quality and entry-point clarity.",
    )

def score_release_discipline(repository: RepositorySnapshot, inputs: HealthInputs, kind: RepositoryKind) -> CategoryResult:
    metrics: list[MetricResult] = []
    releases = inputs.releases

    if releases:
        release_count = len(releases)
        metrics.append(
            MetricResult(
                name="release_presence",
                score=score_count(release_count, good=1, excellent=5, low_score=55.0),
                confidence=95.0,
                available=True,
                weight=1.0,
                value=release_count,
                explanation="Releases provide a stable public milestone structure.",
                evidence=[f"releases={release_count}"],
            )
        )

        release_dates = [to_datetime(pick(rel, "publishedAt") or pick(rel, "published_at") or pick(rel, "createdAt") or pick(rel, "created_at")) for rel in releases]
        release_dates = [dt for dt in release_dates if dt is not None]
        latest_release_days = days_since(max(release_dates)) if release_dates else None
        metrics.append(
            MetricResult(
                name="release_recency",
                score=score_inverse_days(latest_release_days, best=30, worst=730),
                confidence=90.0 if release_dates else 40.0,
                available=latest_release_days is not None,
                weight=1.0,
                value=latest_release_days,
                explanation="Recent releases help indicate versioned progress.",
                evidence=[f"days_since_last_release={latest_release_days}"] if latest_release_days is not None else [],
            )
        )
    else:
        if kind in {RepositoryKind.OPEN_SOURCE_LIBRARY, RepositoryKind.FRAMEWORK, RepositoryKind.API_SERVICE, RepositoryKind.CLI_TOOL, RepositoryKind.DESKTOP_APP, RepositoryKind.MOBILE_APP}:
            metrics.append(
                MetricResult(
                    name="release_presence",
                    score=55.0,
                    confidence=35.0,
                    available=True,
                    weight=1.0,
                    value=0,
                    explanation="No release dataset was available; public projects in this category usually benefit from release tags.",
                    evidence=[],
                )
            )
        else:
            metrics.append(
                MetricResult(
                    name="release_presence",
                    score=None,
                    confidence=20.0,
                    available=False,
                    weight=1.0,
                    value=None,
                    explanation="Release data was not available.",
                    evidence=[],
                )
            )

    score = weighted_mean((metric.score or 0.0, metric.weight) for metric in metrics if metric.available)
    confidence = weighted_mean((metric.confidence, metric.weight) for metric in metrics if metric.available) or 0.0
    return CategoryResult(
        name="release",
        score=score,
        weight=1.0,
        confidence=confidence,
        metrics=metrics,
        explanation="Release cadence and version milestone signals.",
    )

def score_code_surface(repository: RepositorySnapshot, inputs: HealthInputs) -> CategoryResult:
    metrics: list[MetricResult] = []
    files = inputs.files

    if files:
        if isinstance(files, dict):
            file_list = as_list(files.get("files") or files.get("items") or files.get("paths") or files.get("tree"))
        else:
            file_list = as_list(files)

        names = [normalize_text(pick(item, "path") or pick(item, "name") or item) for item in file_list]
        names = [name for name in names if name]
        lower_names = [name.lower() for name in names]

        has_tests = any("/test" in name or name.startswith("test") or "/tests" in name or name.endswith(".test.ts") or name.endswith(".test.js") for name in lower_names)
        has_src = any(name.startswith("src/") or "/src/" in name for name in lower_names)
        has_ci = any(".github/workflows" in name or "github/workflows" in name or "circleci" in name or "gitlab-ci" in name for name in lower_names)
        has_package = any(name in {"package.json", "pyproject.toml", "requirements.txt", "cargo.toml", "go.mod", "pom.xml", "build.gradle", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"} or name.endswith(("/package.json", "/pyproject.toml")) for name in lower_names)

        metrics.append(
            MetricResult(
                name="source_organization",
                score=95.0 if has_src else 65.0,
                confidence=85.0,
                available=True,
                weight=1.0,
                value=has_src,
                explanation="A clear source directory improves code organization.",
                evidence=["src directory"] if has_src else [],
            )
        )
        metrics.append(
            MetricResult(
                name="test_surface",
                score=95.0 if has_tests else 55.0,
                confidence=85.0,
                available=True,
                weight=1.0,
                value=has_tests,
                explanation="Tests are a strong signal of maintainability.",
                evidence=["test files"] if has_tests else [],
            )
        )
        metrics.append(
            MetricResult(
                name="ci_surface",
                score=95.0 if has_ci else 55.0,
                confidence=80.0,
                available=True,
                weight=1.0,
                value=has_ci,
                explanation="Automated CI strengthens repository reliability.",
                evidence=["ci config"] if has_ci else [],
            )
        )
        metrics.append(
            MetricResult(
                name="package_surface",
                score=95.0 if has_package else 60.0,
                confidence=80.0,
                available=True,
                weight=1.0,
                value=has_package,
                explanation="Package manifests help reproducibility and installation.",
                evidence=["package manifest"] if has_package else [],
            )
        )
    else:
        metrics.append(
            MetricResult(
                name="source_organization",
                score=None,
                confidence=10.0,
                available=False,
                weight=1.0,
                value=None,
                explanation="No file tree or code surface snapshot was provided.",
                evidence=[],
            )
        )
        metrics.append(
            MetricResult(
                name="test_surface",
                score=None,
                confidence=10.0,
                available=False,
                weight=1.0,
                value=None,
                explanation="No file tree or code surface snapshot was provided.",
                evidence=[],
            )
        )
        metrics.append(
            MetricResult(
                name="ci_surface",
                score=None,
                confidence=10.0,
                available=False,
                weight=1.0,
                value=None,
                explanation="No file tree or code surface snapshot was provided.",
                evidence=[],
            )
        )
        metrics.append(
            MetricResult(
                name="package_surface",
                score=None,
                confidence=10.0,
                available=False,
                weight=1.0,
                value=None,
                explanation="No file tree or code surface snapshot was provided.",
                evidence=[],
            )
        )

    score = weighted_mean((metric.score or 0.0, metric.weight) for metric in metrics if metric.available)
    confidence = weighted_mean((metric.confidence, metric.weight) for metric in metrics if metric.available) or 0.0
    return CategoryResult(
        name="code_surface",
        score=score,
        weight=1.0,
        confidence=confidence,
        metrics=metrics,
        explanation="Optional file tree, tests, package, and CI signals.",
    )

def build_category_results(repository: RepositorySnapshot, inputs: HealthInputs, kind: RepositoryKind) -> list[CategoryResult]:
    return [
        score_foundation(repository, inputs),
        score_activity(repository, inputs),
        score_collaboration(repository, inputs, kind),
        score_maintenance(repository, inputs),
        score_documentation(repository, inputs, kind),
        score_release_discipline(repository, inputs, kind),
        score_code_surface(repository, inputs),
    ]

def category_availability(category: CategoryResult) -> bool:
    return category.score is not None and any(metric.available for metric in category.metrics)


def calculate_overall_score(kind: RepositoryKind, categories: list[CategoryResult]) -> tuple[float, float]:
    weights = choose_weight_profile(kind)
    available_categories = {
        category.name for category in categories if category_availability(category)
    }
    normalized = normalize_weight_profile(weights, available_categories)

    weighted_scores = []
    weighted_confidences = []
    total_expected_weight = sum(weight for weight in weights.values() if weight > 0)

    observed_weight = 0.0
    for category in categories:
        if category.score is None:
            continue
        weight = normalized.get(category.name, 0.0)
        if weight > 0:
            observed_weight += weights.get(category.name, 0.0)
            weighted_scores.append((category.score, weight))
            weighted_confidences.append((category.confidence, weight))

    overall_score = weighted_mean(weighted_scores)
    overall_confidence = weighted_mean(weighted_confidences)

    coverage = safe_divide(observed_weight, total_expected_weight, 0.0) if total_expected_weight else 0.0
    if overall_confidence is None:
        overall_confidence = 0.0
    overall_confidence = clamp((overall_confidence * 0.7) + (coverage * 100.0 * 0.3))

    return (clamp(overall_score if overall_score is not None else 0.0), clamp(overall_confidence))


def category_band(score: float | None) -> ScoreBand:
    if score is None:
        return ScoreBand.UNKNOWN
    if score >= 85:
        return ScoreBand.EXCELLENT
    if score >= 70:
        return ScoreBand.GOOD
    if score >= 55:
        return ScoreBand.FAIR
    return ScoreBand.WEAK


def confidence_band(score: float | None) -> ScoreBand:
    return category_band(score)

def top_strengths(categories: list[CategoryResult], limit: int = 5) -> list[str]:
    strengths: list[str] = []
    ranked = sorted(
        [category for category in categories if category.score is not None],
        key=lambda category: category.score,
        reverse=True,
    )
    for category in ranked:
        if category.score is None or category.score < 70:
            continue
        strengths.append(f"{category.name.replace('_', ' ').title()} is strong ({round(category.score, 1)}/100).")
        if len(strengths) >= limit:
            break
    return strengths


def top_risks(categories: list[CategoryResult], limit: int = 5) -> list[str]:
    risks: list[str] = []
    ranked = sorted(
        [category for category in categories if category.score is not None],
        key=lambda category: category.score,
    )
    for category in ranked:
        if category.score is None or category.score >= 70:
            continue
        risks.append(f"{category.name.replace('_', ' ').title()} is under pressure ({round(category.score, 1)}/100).")
        if len(risks) >= limit:
            break
    return risks


def recommendation_for_category(category: CategoryResult, repository_kind: RepositoryKind) -> list[str]:
    name = category.name
    suggestions: list[str] = []

    if name == "foundation":
        if category.score is not None and category.score < 80:
            suggestions.append("Add or improve the README, homepage, license, and topic metadata so the repository explains itself clearly.")
    elif name == "activity":
        if category.score is not None and category.score < 75:
            suggestions.append("Establish a steadier commit cadence and use descriptive commit messages.")
    elif name == "collaboration":
        if repository_kind not in {RepositoryKind.STUDENT_PORTFOLIO, RepositoryKind.COURSE_PROJECT, RepositoryKind.HACKATHON} and (category.score is not None and category.score < 70):
            suggestions.append("Strengthen pull request review practices and contributor handoff patterns.")
        elif category.score is not None and category.score < 65:
            suggestions.append("If this is a solo project, document that explicitly so the low collaboration signal is interpreted fairly.")
    elif name == "maintenance":
        if category.score is not None and category.score < 75:
            suggestions.append("Triage stale issues, close resolved items promptly, and keep the repository actively maintained.")
    elif name == "documentation":
        if category.score is not None and category.score < 80:
            suggestions.append("Expand the README with installation, usage, examples, and contribution guidance.")
    elif name == "release":
        if repository_kind in {RepositoryKind.OPEN_SOURCE_LIBRARY, RepositoryKind.FRAMEWORK, RepositoryKind.API_SERVICE, RepositoryKind.CLI_TOOL} and (category.score is not None and category.score < 70):
            suggestions.append("Add tagged releases and release notes so users can understand version milestones.")
    elif name == "code_surface":
        if category.score is not None and category.score < 70:
            suggestions.append("Add tests, CI workflows, and a clearer source/package structure if they are part of the project goals.")

    return suggestions


def build_recommendations(categories: list[CategoryResult], repository_kind: RepositoryKind, limit: int = 8) -> list[str]:
    recs: list[str] = []
    for category in categories:
        recs.extend(recommendation_for_category(category, repository_kind))
    deduped: list[str] = []
    seen = set()
    for rec in recs:
        key = rec.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(rec)
    return deduped[:limit]

def build_missing_signals(repository: RepositorySnapshot, inputs: HealthInputs, kind: RepositoryKind) -> list[str]:
    missing: list[str] = []
    if not inputs.commits:
        missing.append("Commit dataset unavailable.")
    if not inputs.pull_requests:
        missing.append("Pull request dataset unavailable.")
    if not inputs.issues:
        missing.append("Issue dataset unavailable.")
    if not inputs.developers:
        missing.append("Developer dataset unavailable.")
    if not inputs.releases and kind in {
        RepositoryKind.OPEN_SOURCE_LIBRARY,
        RepositoryKind.FRAMEWORK,
        RepositoryKind.API_SERVICE,
        RepositoryKind.CLI_TOOL,
    }:
        missing.append("Release dataset unavailable for a repository type that usually benefits from releases.")
    if not inputs.readme_text:
        missing.append("README text was not provided for deeper documentation analysis.")
    if not inputs.files:
        missing.append("File-tree / code-surface snapshot was not provided.")
    return missing

def build_health_report(inputs: HealthInputs | None = None) -> HealthReport:
    inputs = inputs or load_health_inputs()
    repository = normalize_repository_snapshot(inputs.repository)
    repository_kind = classify_repository_kind(repository)
    maturity = infer_maturity_level(repository, inputs)
    categories = build_category_results(repository, inputs, repository_kind)
    overall_score, overall_confidence = calculate_overall_score(repository_kind, categories)

    strengths = top_strengths(categories)
    risks = top_risks(categories)
    recommendations = build_recommendations(categories, repository_kind)
    missing_signals = build_missing_signals(repository, inputs, repository_kind)

    return HealthReport(
        repository=repository,
        kind=repository_kind,
        maturity=maturity,
        overall_score=overall_score,
        overall_confidence=overall_confidence,
        categories=categories,
        strengths=strengths,
        risks=risks,
        recommendations=recommendations,
        missing_signals=missing_signals,
        notes=[
            "Health score is context-aware and intentionally fair to small repositories.",
            "Missing datasets lower confidence more than they lower the score.",
            "Student portfolios are not penalized for lacking open-source community scale.",
        ],
    )

def format_category(category: CategoryResult) -> str:
    lines = [
        f"{category.name.replace('_', ' ').title()}: {round(category.score, 1) if category.score is not None else 'n/a'}/100",
        f"  Confidence: {round(category.confidence, 1)}%",
        f"  Explanation: {category.explanation}",
    ]
    for metric in category.metrics:
        value = metric.value
        if isinstance(value, float):
            value = round(value, 3)
        lines.append(
            f"    - {metric.name}: {metric.score if metric.score is not None else 'n/a'} | confidence={round(metric.confidence, 1)}% | {'available' if metric.available else 'missing'} | value={value}"
        )
    return "\n".join(lines)


def format_health_report(report: HealthReport) -> str:
    lines = [
        "=" * 80,
        "ORZYN REPOSITORY HEALTH REPORT",
        "=" * 80,
        f"Repository : {report.repository.owner}/{report.repository.repository}",
        f"URL        : {report.repository.url}",
        f"Kind       : {report.kind.value.replace('_', ' ').title()}",
        f"Maturity   : {report.maturity.value.title()}",
        f"Overall    : {round(report.overall_score, 1)}/100",
        f"Confidence : {round(report.overall_confidence, 1)}%",
        "",
        "Category Breakdown",
        "-" * 80,
    ]
    for category in report.categories:
        lines.append(format_category(category))
        lines.append("")
    if report.strengths:
        lines.extend(["Strengths", "-" * 80] + [f"• {item}" for item in report.strengths] + [""])
    if report.risks:
        lines.extend(["Risks", "-" * 80] + [f"• {item}" for item in report.risks] + [""])
    if report.recommendations:
        lines.extend(["Recommendations", "-" * 80] + [f"• {item}" for item in report.recommendations] + [""])
    if report.missing_signals:
        lines.extend(["Missing Signals", "-" * 80] + [f"• {item}" for item in report.missing_signals] + [""])
    if report.notes:
        lines.extend(["Notes", "-" * 80] + [f"• {item}" for item in report.notes] + [""])
    return "\n".join(lines)


def report_to_dict(report: HealthReport) -> dict[str, Any]:
    return serialize_dataclass(report)

def build_health_prompt(report: HealthReport) -> str:
    report_json = json.dumps(report_to_dict(report), indent=2)
    return f'''You are helping explain a GitHub repository health assessment.

Your job is to produce a clear, fair, and concise analysis for the repository below.

Important rules:
- Do not confuse popularity with quality.
- Do not penalize student portfolios for lacking open-source community scale.
- Explain the score in plain language.
- Mention strengths, risks, and the most useful next improvements.
- If confidence is low, say so explicitly.
- If data is missing, explain how that affects confidence rather than inventing facts.

Repository health report JSON:
{report_json}
'''.strip()


def summarize_report(report: HealthReport) -> None:
    print(format_health_report(report))


def show_report_table(report: HealthReport) -> list[tuple[str, float | None, float]]:
    table: list[tuple[str, float | None, float]] = []
    for category in report.categories:
        table.append((category.name, category.score, category.confidence))
    return table

inputs = load_health_inputs()
report = build_health_report(inputs)

summarize_report(report)

print()
print("=" * 80)
print("AI PROMPT PREVIEW")
print("=" * 80)
preview = build_health_prompt(report)
print(preview[:2500] + ("\n...\n" if len(preview) > 2500 else ""))