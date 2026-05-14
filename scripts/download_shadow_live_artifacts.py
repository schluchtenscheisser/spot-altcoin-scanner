#!/usr/bin/env python3
"""Download relevant GitHub Actions artifacts for Independence Shadow-Live runs.

Default behavior:
- repository: inferred from git remote, or pass --repo owner/name
- workflow: independence-shadow-live.yml
- artifacts: independence-shadow-live-*, shadow-live-reports, shadow-live-state
- output: data/shadow-live-zips

Authentication:
- uses GITHUB_TOKEN or GH_TOKEN if set
- otherwise tries `gh auth token`

Examples:
  python scripts/download_shadow_live_artifacts.py --repo schluchtenscheisser/spot-altcoin-scanner
  python scripts/download_shadow_live_artifacts.py --max-runs 20
  python scripts/download_shadow_live_artifacts.py --since 2026-05-03
  python scripts/download_shadow_live_artifacts.py --artifact-prefix independence-shadow-live-
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

API_ROOT = "https://api.github.com"
DEFAULT_WORKFLOW = "independence-shadow-live.yml"
DEFAULT_OUTPUT_DIR = Path("data/shadow-live-zips")
DEFAULT_ARTIFACT_PREFIXES = (
    "independence-shadow-live-",
    "shadow-live-reports",
    "shadow-live-state",
)


def _log(message: str) -> None:
    print(message, flush=True)


def _warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr, flush=True)


def _fatal(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr, flush=True)
    raise SystemExit(code)


def _run(cmd: list[str], cwd: Path | None = None) -> str | None:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        return result.stdout.strip()
    except Exception:
        return None


def _infer_repo(project_root: Path) -> str | None:
    remote = _run(["git", "remote", "get-url", "origin"], cwd=project_root)
    if not remote:
        return None

    # Supports:
    # git@github.com:owner/repo.git
    # https://github.com/owner/repo.git
    # https://github.com/owner/repo
    patterns = [
        r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$",
        r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, remote)
        if match:
            return f"{match.group('owner')}/{match.group('repo')}"
    return None


def _get_token() -> str | None:
    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        token = os.environ.get(key)
        if token:
            return token.strip()
    token = _run(["gh", "auth", "token"])
    return token.strip() if token else None


def _headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "independence-shadow-live-artifact-downloader",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers



class _NoRedirectHandler(HTTPRedirectHandler):
    """Prevent urllib from following GitHub artifact redirects automatically.

    GitHub's artifact archive endpoint returns a short-lived redirect to a
    signed blob-storage URL. Authorization headers are required for the GitHub
    API request, but must not be forwarded to the signed blob URL. Following the
    redirect manually keeps those two requests separate.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _artifact_redirect_url(url: str, token: str | None) -> str:
    """Resolve a GitHub artifact archive URL to its signed download URL."""
    request = Request(url, headers=_headers(token), method="GET")
    opener = build_opener(_NoRedirectHandler)
    try:
        with opener.open(request, timeout=60) as response:
            # In case GitHub ever serves the archive directly, return the final URL.
            return response.geturl()
    except HTTPError as exc:
        if exc.code in {301, 302, 303, 307, 308}:
            location = exc.headers.get("Location")
            if location:
                return location
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"artifact redirect request failed: {exc.code} {exc.reason}; {body}"
        ) from exc


def _parse_link_next(link_header: str | None) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        sections = part.split(";")
        if len(sections) < 2:
            continue
        url = sections[0].strip()
        rel = ";".join(sections[1:]).strip()
        if rel == 'rel="next"' and url.startswith("<") and url.endswith(">"):
            return url[1:-1]
    return None


def _api_json(url: str, token: str | None, retries: int = 3) -> tuple[Any, dict[str, str]]:
    for attempt in range(1, retries + 1):
        request = Request(url, headers=_headers(token), method="GET")
        try:
            with urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload, dict(response.headers.items())
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code in {403, 429, 500, 502, 503, 504} and attempt < retries:
                wait = min(30, 2**attempt)
                _warn(f"GitHub API {exc.code} for {url}; retrying in {wait}s")
                time.sleep(wait)
                continue
            _fatal(f"GitHub API request failed: {exc.code} {exc.reason}\nURL: {url}\n{body}")
        except URLError as exc:
            if attempt < retries:
                wait = min(30, 2**attempt)
                _warn(f"Network error for {url}: {exc}; retrying in {wait}s")
                time.sleep(wait)
                continue
            _fatal(f"Network error for {url}: {exc}")
    raise AssertionError("unreachable")


def _download_file(url: str, target: Path, token: str | None, overwrite: bool, retries: int = 3) -> bool:
    if target.exists() and target.stat().st_size > 0 and not overwrite:
        _log(f"SKIP existing: {target}")
        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()

    for attempt in range(1, retries + 1):
        try:
            # Step 1: ask the GitHub API for the short-lived archive redirect.
            # This request must include Authorization.
            signed_url = _artifact_redirect_url(url, token)

            # Step 2: download from the signed blob URL. Do NOT forward the
            # GitHub Authorization header to the redirected storage endpoint;
            # doing so can produce HTTP 401 in GitHub Actions.
            request = Request(
                signed_url,
                headers={"User-Agent": "independence-shadow-live-artifact-downloader"},
                method="GET",
            )
            with urlopen(request, timeout=180) as response:
                with tmp.open("wb") as fh:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        fh.write(chunk)
            if tmp.stat().st_size <= 0:
                raise RuntimeError("downloaded artifact is empty")
            tmp.replace(target)
            _log(f"DOWNLOADED: {target} ({target.stat().st_size:,} bytes)")
            return True
        except Exception as exc:
            if tmp.exists():
                tmp.unlink()
            if attempt < retries:
                wait = min(30, 2**attempt)
                _warn(f"Download failed for {target.name}: {exc}; retrying in {wait}s")
                time.sleep(wait)
                continue
            _fatal(f"Download failed for {target.name}: {exc}")
    raise AssertionError("unreachable")


def _list_workflow_runs(
    repo: str,
    workflow: str,
    token: str | None,
    *,
    branch: str | None,
    status: str,
    conclusion: str | None,
    max_runs: int,
) -> list[dict[str, Any]]:
    params: dict[str, str | int] = {"per_page": 100, "status": status}
    if branch:
        params["branch"] = branch
    if conclusion:
        # GitHub supports conclusion on list workflow runs.
        params["conclusion"] = conclusion
    url = f"{API_ROOT}/repos/{repo}/actions/workflows/{workflow}/runs?{urlencode(params)}"

    runs: list[dict[str, Any]] = []
    while url and len(runs) < max_runs:
        payload, headers = _api_json(url, token)
        page_runs = payload.get("workflow_runs", []) if isinstance(payload, dict) else []
        if not isinstance(page_runs, list):
            _fatal("Unexpected GitHub API response: workflow_runs is not a list")
        for run in page_runs:
            if isinstance(run, dict):
                runs.append(run)
                if len(runs) >= max_runs:
                    break
        url = _parse_link_next(headers.get("Link")) if len(runs) < max_runs else None
    return runs


def _list_run_artifacts(repo: str, run_id: int, token: str | None) -> list[dict[str, Any]]:
    url = f"{API_ROOT}/repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100"
    artifacts: list[dict[str, Any]] = []
    while url:
        payload, headers = _api_json(url, token)
        page_artifacts = payload.get("artifacts", []) if isinstance(payload, dict) else []
        if not isinstance(page_artifacts, list):
            _fatal("Unexpected GitHub API response: artifacts is not a list")
        artifacts.extend(a for a in page_artifacts if isinstance(a, dict))
        url = _parse_link_next(headers.get("Link"))
    return artifacts


def _safe_date(value: Any) -> str:
    if not isinstance(value, str) or not value:
        return "unknown-date"
    # 2026-05-13T06:50:38Z -> 20260513T065038Z
    return value.replace("-", "").replace(":", "").replace(".", "").replace("+", "").replace(" ", "T")


def _artifact_matches(name: str, prefixes: tuple[str, ...]) -> bool:
    return any(name == prefix or name.startswith(prefix) for prefix in prefixes)


def _parse_since(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return dt.datetime.fromisoformat(raw + "T00:00:00+00:00")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _run_created_at(run: dict[str, Any]) -> dt.datetime | None:
    raw = run.get("created_at")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return dt.datetime.fromisoformat(raw).astimezone(dt.timezone.utc)
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Download Shadow-Live GitHub Actions artifacts into data/shadow-live-zips.")
    parser.add_argument("--project-root", type=Path, default=Path("."), help="Repo root used for git remote inference and output paths.")
    parser.add_argument("--repo", default=None, help="GitHub repository in owner/name form. Defaults to git remote origin.")
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW, help="Workflow file name or workflow ID.")
    parser.add_argument("--branch", default="main", help="Workflow run branch filter. Use empty string to disable.")
    parser.add_argument("--status", default="completed", help="Workflow run status filter.")
    parser.add_argument("--conclusion", default="success", help="Workflow run conclusion filter. Use empty string to disable.")
    parser.add_argument("--max-runs", type=int, default=50, help="Maximum workflow runs to inspect.")
    parser.add_argument("--since", default=None, help="Only include runs created at/after this date or timestamp, e.g. 2026-05-03.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for downloaded ZIP files.")
    parser.add_argument(
        "--artifact-prefix",
        action="append",
        default=None,
        help="Artifact name or prefix to download. Can be repeated. Defaults to Shadow-Live main/reports/state artifacts.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Redownload and replace existing ZIP files.")
    parser.add_argument("--include-expired", action="store_true", help="List expired artifacts in manifest, but they cannot be downloaded.")
    parser.add_argument("--dry-run", action="store_true", help="List matching artifacts without downloading.")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    repo = args.repo or _infer_repo(project_root)
    if not repo:
        _fatal("Could not infer repo from git remote. Pass --repo owner/name.")
    if not re.fullmatch(r"[^/]+/[^/]+", repo):
        _fatal(f"Invalid --repo value: {repo!r}. Expected owner/name.")

    token = _get_token()
    if not token:
        _fatal("GitHub token not found. Set GITHUB_TOKEN/GH_TOKEN or run `gh auth login`.")

    prefixes = tuple(args.artifact_prefix or DEFAULT_ARTIFACT_PREFIXES)
    since_dt = _parse_since(args.since)
    output_dir = (project_root / args.output_dir).resolve() if not args.output_dir.is_absolute() else args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    branch = args.branch or None
    conclusion = args.conclusion or None

    _log(f"Repo: {repo}")
    _log(f"Workflow: {args.workflow}")
    _log(f"Output dir: {output_dir}")
    _log(f"Artifact prefixes: {', '.join(prefixes)}")

    runs = _list_workflow_runs(
        repo,
        args.workflow,
        token,
        branch=branch,
        status=args.status,
        conclusion=conclusion,
        max_runs=max(1, args.max_runs),
    )
    if since_dt:
        runs = [r for r in runs if (_run_created_at(r) and _run_created_at(r) >= since_dt)]

    _log(f"Runs inspected: {len(runs)}")

    manifest: dict[str, Any] = {
        "repo": repo,
        "workflow": args.workflow,
        "branch": branch,
        "status": args.status,
        "conclusion": conclusion,
        "since": args.since,
        "artifact_prefixes": list(prefixes),
        "downloaded_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "output_dir": str(output_dir),
        "runs": [],
    }

    total_matches = 0
    total_downloaded = 0
    total_skipped_existing = 0
    total_expired = 0

    for run in runs:
        run_id = int(run.get("id"))
        run_number = run.get("run_number")
        created_at = str(run.get("created_at") or "")
        display_title = str(run.get("display_title") or run.get("name") or "")
        artifacts = _list_run_artifacts(repo, run_id, token)
        matching = []
        for artifact in artifacts:
            name = str(artifact.get("name") or "")
            if not _artifact_matches(name, prefixes):
                continue
            expired = bool(artifact.get("expired"))
            if expired and not args.include_expired:
                total_expired += 1
                continue
            matching.append(artifact)

        run_entry = {
            "run_id": run_id,
            "run_number": run_number,
            "created_at": created_at,
            "display_title": display_title,
            "html_url": run.get("html_url"),
            "artifacts": [],
        }

        if not matching:
            manifest["runs"].append(run_entry)
            continue

        _log(f"Run {run_id} ({created_at}) matches: {len(matching)}")
        for artifact in matching:
            total_matches += 1
            name = str(artifact.get("name") or f"artifact-{artifact.get('id')}")
            artifact_id = int(artifact.get("id"))
            expired = bool(artifact.get("expired"))
            filename = f"{_safe_date(created_at)}__run-{run_id}__artifact-{artifact_id}__{name}.zip"
            target = output_dir / filename
            downloaded = False
            skipped_existing = False

            if expired:
                total_expired += 1
                _warn(f"Expired artifact cannot be downloaded: run={run_id} artifact={name}")
            elif args.dry_run:
                _log(f"DRY-RUN would download: {target}")
            else:
                existed_before = target.exists() and target.stat().st_size > 0
                downloaded = _download_file(
                    str(artifact.get("archive_download_url")),
                    target,
                    token,
                    overwrite=args.overwrite,
                )
                skipped_existing = existed_before and not downloaded and not args.overwrite
                if downloaded:
                    total_downloaded += 1
                if skipped_existing:
                    total_skipped_existing += 1

            run_entry["artifacts"].append(
                {
                    "artifact_id": artifact_id,
                    "name": name,
                    "expired": expired,
                    "size_in_bytes": artifact.get("size_in_bytes"),
                    "created_at": artifact.get("created_at"),
                    "updated_at": artifact.get("updated_at"),
                    "archive_download_url": artifact.get("archive_download_url"),
                    "local_path": str(target),
                    "downloaded": downloaded,
                    "skipped_existing": skipped_existing,
                }
            )
        manifest["runs"].append(run_entry)

    manifest["summary"] = {
        "runs_inspected": len(runs),
        "matching_artifacts": total_matches,
        "downloaded_artifacts": total_downloaded,
        "skipped_existing_artifacts": total_skipped_existing,
        "expired_artifacts": total_expired,
        "dry_run": bool(args.dry_run),
    }
    manifest_path = output_dir / "download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _log("Summary:")
    _log(json.dumps(manifest["summary"], indent=2, sort_keys=True))
    _log(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
