from __future__ import annotations

import io
import json
import zipfile
from urllib import request


class GitHubApi:
    def __init__(self, *, repo: str, token: str, api_url: str = "https://api.github.com") -> None:
        self.repo = repo
        self.token = token
        self.api_url = api_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, payload: dict | None = None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(f"{self.api_url}{path}", data=body, method=method, headers=self._headers())
        with request.urlopen(req) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8")) if resp.headers.get_content_type() == "application/json" else resp.read()

    def list_issue_comments(self, issue_number: int) -> list[dict]:
        return self._request("GET", f"/repos/{self.repo}/issues/{issue_number}/comments")

    def post_issue_comment(self, issue_number: int, body: str) -> dict:
        return self._request("POST", f"/repos/{self.repo}/issues/{issue_number}/comments", {"body": body})

    def list_run_artifacts(self, run_id: int) -> list[dict]:
        payload = self._request("GET", f"/repos/{self.repo}/actions/runs/{run_id}/artifacts")
        return payload.get("artifacts", [])

    def download_artifact_zip(self, artifact_id: int) -> bytes:
        req = request.Request(
            f"{self.api_url}/repos/{self.repo}/actions/artifacts/{artifact_id}/zip",
            method="GET",
            headers=self._headers(),
        )
        with request.urlopen(req) as resp:  # noqa: S310
            return resp.read()


def extract_session_json(zip_bytes: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        with zf.open("session.json") as fh:
            return json.loads(fh.read().decode("utf-8"))


def extract_text_file(zip_bytes: bytes, path: str) -> str | None:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        try:
            with zf.open(path) as fh:
                return fh.read().decode("utf-8")
        except KeyError:
            return None
