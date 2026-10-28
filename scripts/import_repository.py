"""Import the verified private neocam bundle without replacing existing history."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.parse
import urllib.request

REPO = "edithatogo/neocam"
SOURCE_COMMIT = "7242e7f7e12d807c52e1d250a388541ada033c51"
SOURCE_TREE = "0ef76ee21360db34af07a281712ce2f75dc97bd8"
BUNDLE_SHA256 = "df495af954ce94f2acf1049cec7358bd348d12ca5d235c6b8b1f5948142737be"
BUNDLE_BYTES = 76718081
SOURCE_ENTRIES = 893


def git(*args: str, cwd: Path, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, env=env, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode("utf-8")


def entries(ref: str, cwd: Path) -> dict[str, str]:
    return {record.split("\t", 1)[1]: record.split("\t", 1)[0]
            for record in git("ls-tree", "-rz", ref, cwd=cwd).split("\0") if record}


def read_request() -> tuple[str, str]:
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    if event["repository"]["full_name"] != REPO or not event["repository"]["private"]:
        raise RuntimeError("Import requires the designated PRIVATE repository")
    owner = REPO.split("/")[0]
    if event["sender"]["login"] != owner or event["issue"]["user"]["login"] != owner:
        raise RuntimeError("Only the repository owner may trigger this import")
    request = json.loads(event["issue"]["body"])
    if request["sha256"] != BUNDLE_SHA256 or request["commit"] != SOURCE_COMMIT:
        raise RuntimeError("Unexpected archive or commit")
    url = request["download_url"]
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "https" or parsed.username or parsed.password
            or not (parsed.hostname or "").endswith(".oaiusercontent.com")
            or parsed.port not in (None, 443)):
        raise RuntimeError("Unapproved archive source")
    print("::add-mask::" + url, flush=True)
    return url, str(event["issue"]["number"])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Archive redirect refused; request a fresh direct file URL")


def download(url: str, destination: Path) -> None:
    digest = hashlib.sha256()
    count = 0
    opener = urllib.request.build_opener(NoRedirect)
    with opener.open(url, timeout=90) as response, destination.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            count += len(chunk)
            if count > BUNDLE_BYTES:
                raise RuntimeError("Archive exceeds its verified size")
            digest.update(chunk)
            output.write(chunk)
    if count != BUNDLE_BYTES or digest.hexdigest() != BUNDLE_SHA256:
        raise RuntimeError("Archive integrity verification failed")


def main() -> None:
    url, issue = read_request()
    token = os.environ["GH_TOKEN"]
    auth = base64.b64encode(("x-access-token:" + token).encode()).decode()
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_COUNT="1",
               GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
               GIT_CONFIG_VALUE_0="AUTHORIZATION: basic " + auth)
    with tempfile.TemporaryDirectory(prefix="neocam-import-") as folder:
        work = Path(folder)
        bundle = work / "project.bundle"
        download(url, bundle)
        git("init", "--bare", "verified.git", cwd=work)
        git("bundle", "verify", str(bundle), cwd=work / "verified.git")
        git("clone", "--branch", "conductor/neocam-v8-assurance-publish",
            str(bundle), "repo", cwd=work)
        repo = work / "repo"
        if git("rev-parse", "HEAD", cwd=repo).strip() != SOURCE_COMMIT:
            raise RuntimeError("Source commit mismatch")
        if git("rev-parse", "HEAD^{tree}", cwd=repo).strip() != SOURCE_TREE:
            raise RuntimeError("Source tree mismatch")
        original = entries("HEAD", repo)
        if len(original) != SOURCE_ENTRIES:
            raise RuntimeError("Source inventory mismatch")
        git("fsck", "--full", cwd=repo)
        git("remote", "set-url", "origin", "https://github.com/" + REPO + ".git", cwd=repo)
        git("fetch", "origin", "main", cwd=repo, env=env)
        previous = git("rev-parse", "origin/main", cwd=repo).strip()
        git("config", "user.name", "github-actions[bot]", cwd=repo)
        git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com", cwd=repo)
        git("push", "origin", "HEAD:refs/heads/recovery/v8-original", cwd=repo, env=env)
        git("merge", "--allow-unrelated-histories", "--no-commit", "-s", "ours",
            "origin/main", cwd=repo)
        for path, metadata in entries("origin/main", repo).items():
            if path not in original:
                git("checkout", "origin/main", "--", path, cwd=repo)
        old_readme = git("show", "origin/main:README.md", cwd=repo)
        handoff = repo / "handoff"
        handoff.mkdir(exist_ok=True)
        (handoff / "bootstrap-readme.md").write_text(old_readme)
        evidence = repo / "verification" / "imports"
        evidence.mkdir(parents=True, exist_ok=True)
        receipt = {"source_commit": SOURCE_COMMIT, "source_tree": SOURCE_TREE,
                   "bundle_sha256": BUNDLE_SHA256, "bundle_bytes": BUNDLE_BYTES,
                   "source_entries": SOURCE_ENTRIES, "previous_main": previous,
                   "trigger_issue": issue, "ci_status": "not certified by import"}
        (evidence / "v8-import.json").write_text(json.dumps(receipt, indent=2) + "\n")
        git("add", "handoff/bootstrap-readme.md", "verification/imports/v8-import.json", cwd=repo)
        git("commit", "-m", "Import complete verified v8 project and preserve both histories", cwd=repo)
        merged = entries("HEAD", repo)
        if any(merged.get(path) != metadata for path, metadata in original.items()):
            raise RuntimeError("A source file or gitlink changed during import")
        git("merge-base", "--is-ancestor", previous, "HEAD", cwd=repo)
        git("merge-base", "--is-ancestor", SOURCE_COMMIT, "HEAD", cwd=repo)
        git("push", "origin", "HEAD:refs/heads/main", cwd=repo, env=env)
        head = git("rev-parse", "HEAD", cwd=repo).strip()
        actual = git("ls-remote", "origin", "refs/heads/main", cwd=repo, env=env).split()[0]
        if head != actual:
            raise RuntimeError("Remote main did not match the imported commit")
        print(f"IMPORT VERIFIED: {SOURCE_ENTRIES} unchanged source entries; main={head}")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a") as out:
                out.write(f"## Complete repository import\n\nSource entries: {SOURCE_ENTRIES}\n\n"
                          f"Source commit: `{SOURCE_COMMIT}`\n\nRemote main: `{head}`\n\n"
                          "Every source blob/mode/gitlink retained. Both histories preserved. "
                          "This verifies transfer, not scientific validity or full CI.\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"IMPORT FAILED ({type(exc).__name__}); no credentials printed", flush=True)
        raise SystemExit(1) from None
